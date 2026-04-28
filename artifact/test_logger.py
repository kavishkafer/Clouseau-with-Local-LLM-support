"""
Comprehensive test logging system for tracking test execution across different environments.
Logs test metadata, performance metrics, and enables comparison across runs.
"""

import json
import csv
import os
import sys
from datetime import datetime
from pathlib import Path
import sqlite3
from typing import Optional, Dict, Any, List
import hashlib

class TestLogger:
    """Logs test execution details to both JSON and SQLite for comprehensive tracking."""
    
    def __init__(self, log_dir: str = "test_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Generate run ID based on timestamp
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.log_dir / self.run_id
        self.run_dir.mkdir(exist_ok=True)
        
        # Initialize database
        self.db_path = self.log_dir / "test_runs.db"
        self._init_database()
        
        # Run metadata
        self.run_metadata = {
            "run_id": self.run_id,
            "start_time": datetime.now().isoformat(),
            "model": os.getenv("LLM_MODEL", "unknown"),
            "base_url": os.getenv("BASE_URL", "unknown"),
            "environment": self._get_environment_info(),
            "scenarios": [],
            "end_time": None,
            "total_duration": None
        }
        
        # Test results tracking
        self.test_results: List[Dict[str, Any]] = []
        
        print(f"✓ Test logger initialized: {self.run_dir}")
    
    def _init_database(self):
        """Initialize SQLite database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Runs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                start_time TEXT,
                end_time TEXT,
                model TEXT,
                base_url TEXT,
                environment TEXT,
                total_duration_seconds REAL
            )
        """)
        
        # Test results table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT,
                scenario_name TEXT,
                test_name TEXT,
                start_time TEXT,
                end_time TEXT,
                duration_seconds REAL,
                tp INTEGER,
                tn INTEGER,
                fp INTEGER,
                fn INTEGER,
                precision REAL,
                recall REAL,
                fpr REAL,
                f1 REAL,
                total_tokens INTEGER,
                input_tokens INTEGER,
                output_tokens INTEGER,
                status TEXT,
                error_message TEXT,
                FOREIGN KEY (run_id) REFERENCES runs(run_id)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _get_environment_info(self) -> str:
        """Capture environment information."""
        import platform
        return json.dumps({
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor()
        })
    
    def log_test_start(self, scenario_name: str, test_name: str) -> Dict[str, Any]:
        """Log test start event."""
        test_info = {
            "scenario_name": scenario_name,
            "test_name": test_name,
            "start_time": datetime.now().isoformat()
        }
        return test_info
    
    def log_test_result(
        self,
        test_info: Dict[str, Any],
        tp: int, tn: int, fp: int, fn: int,
        total_tokens: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        status: str = "success",
        error_message: str = None
    ):
        """Log test completion with metrics."""
        end_time = datetime.now().isoformat()
        duration = (datetime.fromisoformat(end_time) - datetime.fromisoformat(test_info["start_time"])).total_seconds()
        
        # Calculate metrics
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        result = {
            **test_info,
            "end_time": end_time,
            "duration_seconds": duration,
            "tp": tp,
            "tn": tn,
            "fp": fp,
            "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "fpr": round(fpr, 4),
            "f1": round(f1, 4),
            "total_tokens": total_tokens,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "status": status,
            "error_message": error_message
        }
        
        self.test_results.append(result)
        
        # Log to database
        self._save_to_database(result)
        
        return result
    
    def _save_to_database(self, result: Dict[str, Any]):
        """Save test result to SQLite database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO test_results (
                run_id, scenario_name, test_name, start_time, end_time, 
                duration_seconds, tp, tn, fp, fn, precision, recall, fpr, f1,
                total_tokens, input_tokens, output_tokens, status, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            self.run_id,
            result["scenario_name"],
            result["test_name"],
            result["start_time"],
            result["end_time"],
            result["duration_seconds"],
            result["tp"],
            result["tn"],
            result["fp"],
            result["fn"],
            result["precision"],
            result["recall"],
            result["fpr"],
            result["f1"],
            result["total_tokens"],
            result["input_tokens"],
            result["output_tokens"],
            result["status"],
            result["error_message"]
        ))
        
        conn.commit()
        conn.close()
    
    def finalize_run(self):
        """Finalize the test run and save summary."""
        end_time = datetime.now().isoformat()
        start_time = datetime.fromisoformat(self.run_metadata["start_time"])
        end_time_dt = datetime.fromisoformat(end_time)
        total_duration = (end_time_dt - start_time).total_seconds()
        
        self.run_metadata["end_time"] = end_time
        self.run_metadata["total_duration"] = total_duration
        self.run_metadata["total_tests"] = len(self.test_results)
        
        # Calculate aggregates
        successful = sum(1 for r in self.test_results if r["status"] == "success")
        failed = sum(1 for r in self.test_results if r["status"] == "failed")
        
        self.run_metadata["successful_tests"] = successful
        self.run_metadata["failed_tests"] = failed
        self.run_metadata["average_precision"] = round(sum(r["precision"] for r in self.test_results) / self.run_metadata["total_tests"], 4) if self.test_results else 0
        self.run_metadata["average_recall"] = round(sum(r["recall"] for r in self.test_results) / self.run_metadata["total_tests"], 4) if self.test_results else 0
        self.run_metadata["average_f1"] = round(sum(r["f1"] for r in self.test_results) / self.run_metadata["total_tests"], 4) if self.test_results else 0
        
        # Save run metadata to file
        metadata_file = self.run_dir / "run_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(self.run_metadata, f, indent=2)
        
        # Save test results to CSV
        results_file = self.run_dir / "test_results.csv"
        if self.test_results:
            with open(results_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.test_results[0].keys())
                writer.writeheader()
                writer.writerows(self.test_results)
        
        # Update database with run summary
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO runs (run_id, start_time, end_time, model, base_url, environment, total_duration_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            self.run_id,
            self.run_metadata["start_time"],
            end_time,
            self.run_metadata["model"],
            self.run_metadata["base_url"],
            self.run_metadata["environment"],
            total_duration
        ))
        
        conn.commit()
        conn.close()
        
        print(f"\n{'='*60}")
        print(f"Run Summary: {self.run_id}")
        print(f"{'='*60}")
        print(f"Model: {self.run_metadata['model']}")
        print(f"Total Tests: {self.run_metadata['total_tests']}")
        print(f"Successful: {successful} | Failed: {failed}")
        print(f"Average F1: {self.run_metadata['average_f1']} | Precision: {self.run_metadata['average_precision']} | Recall: {self.run_metadata['average_recall']}")
        print(f"Total Duration: {total_duration:.2f}s ({total_duration/60:.2f}m)")
        print(f"Results saved to: {self.run_dir}")
        print(f"{'='*60}\n")
        
        return self.run_metadata
    
    def get_run_id(self) -> str:
        """Get the current run ID."""
        return self.run_id
