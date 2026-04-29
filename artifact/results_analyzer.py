"""
Comprehensive results analyzer for comparing test runs across different environments/models.
Generates detailed comparison reports and identifies performance changes.
"""

import pandas as pd
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class ResultsAnalyzer:
    """Analyze and compare test results across multiple runs."""
    
    def __init__(self, log_dir: str = "test_logs"):
        self.log_dir = Path(log_dir)
        self.db_path = self.log_dir / "test_runs.db"
    
    def load_run_metadata(self, run_id: str) -> Dict:
        """Load metadata for a specific run."""
        metadata_file = self.log_dir / run_id / "run_metadata.json"
        with open(metadata_file, 'r') as f:
            return json.load(f)
    
    def load_run_results(self, run_id: str) -> pd.DataFrame:
        """Load test results for a specific run."""
        results_file = self.log_dir / run_id / "test_results.csv"
        return pd.read_csv(results_file)
    
    def get_all_runs(self) -> List[str]:
        """Get list of all run IDs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT run_id FROM runs ORDER BY start_time DESC")
        runs = [row[0] for row in cursor.fetchall()]
        conn.close()
        return runs
    
    def compare_two_runs(self, run_id_1: str, run_id_2: str) -> Dict:
        """Compare two test runs in detail."""
        print(f"\nComparing runs: {run_id_1} vs {run_id_2}\n")
        
        # Load metadata
        meta1 = self.load_run_metadata(run_id_1)
        meta2 = self.load_run_metadata(run_id_2)
        
        # Load results
        results1 = self.load_run_results(run_id_1)
        results2 = self.load_run_results(run_id_2)
        
        comparison = {
            "run_1": {
                "id": run_id_1,
                "model": meta1["model"],
                "start_time": meta1["start_time"],
                "total_duration": meta1["total_duration"],
                "total_tests": meta1["total_tests"],
                "avg_precision": meta1["average_precision"],
                "avg_recall": meta1["average_recall"],
                "avg_f1": meta1["average_f1"]
            },
            "run_2": {
                "id": run_id_2,
                "model": meta2["model"],
                "start_time": meta2["start_time"],
                "total_duration": meta2["total_duration"],
                "total_tests": meta2["total_tests"],
                "avg_precision": meta2["average_precision"],
                "avg_recall": meta2["average_recall"],
                "avg_f1": meta2["average_f1"]
            },
            "deltas": {}
        }
        
        # Calculate deltas
        comparison["deltas"]["precision_delta"] = round(meta2["average_precision"] - meta1["average_precision"], 4)
        comparison["deltas"]["recall_delta"] = round(meta2["average_recall"] - meta1["average_recall"], 4)
        comparison["deltas"]["f1_delta"] = round(meta2["average_f1"] - meta1["average_f1"], 4)
        comparison["deltas"]["duration_delta"] = meta2["total_duration"] - meta1["total_duration"]
        comparison["deltas"]["duration_delta_percent"] = round((comparison["deltas"]["duration_delta"] / meta1["total_duration"]) * 100, 2)
        
        # Test-by-test comparison
        merged = pd.merge(
            results1[["test_name", "precision", "recall", "f1"]],
            results2[["test_name", "precision", "recall", "f1"]],
            on="test_name",
            suffixes=("_run1", "_run2")
        )
        
        merged["precision_change"] = (merged["precision_run2"] - merged["precision_run1"]).round(4)
        merged["recall_change"] = (merged["recall_run2"] - merged["recall_run1"]).round(4)
        merged["f1_change"] = (merged["f1_run2"] - merged["f1_run1"]).round(4)
        
        # Identify biggest changes
        merged["abs_f1_change"] = merged["f1_change"].abs()
        biggest_improvements = merged.nlargest(5, "f1_change")
        biggest_regressions = merged.nsmallest(5, "f1_change")
        
        comparison["detailed_changes"] = {
            "biggest_improvements": biggest_improvements[["test_name", "f1_run1", "f1_run2", "f1_change"]].to_dict("records"),
            "biggest_regressions": biggest_regressions[["test_name", "f1_run1", "f1_run2", "f1_change"]].to_dict("records"),
            "all_test_changes": merged[["test_name", "precision_change", "recall_change", "f1_change"]].to_dict("records")
        }
        
        return comparison
    
    def generate_comparison_report(self, run_id_1: str, run_id_2: str, output_file: str = None):
        """Generate detailed comparison report."""
        comparison = self.compare_two_runs(run_id_1, run_id_2)
        
        if output_file is None:
            output_file = self.log_dir / f"comparison_{run_id_1}_vs_{run_id_2}.json"
        
        with open(output_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        # Print summary
        self._print_comparison_summary(comparison)
        
        return comparison
    
    def _print_comparison_summary(self, comparison: Dict):
        """Print formatted comparison summary."""
        print("\n" + "="*80)
        print("RUN COMPARISON SUMMARY")
        print("="*80)
        
        run1 = comparison["run_1"]
        run2 = comparison["run_2"]
        deltas = comparison["deltas"]
        
        print(f"\n{'RUN 1:':<30} {run1['id']}")
        print(f"{'  Model:':<28} {run1['model']}")
        print(f"{'  Avg F1:':<28} {run1['avg_f1']:.4f}")
        print(f"{'  Avg Precision:':<28} {run1['avg_precision']:.4f}")
        print(f"{'  Avg Recall:':<28} {run1['avg_recall']:.4f}")
        print(f"{'  Duration:':<28} {run1['total_duration']:.2f}s")
        
        print(f"\n{'RUN 2:':<30} {run2['id']}")
        print(f"{'  Model:':<28} {run2['model']}")
        print(f"{'  Avg F1:':<28} {run2['avg_f1']:.4f}")
        print(f"{'  Avg Precision:':<28} {run2['avg_precision']:.4f}")
        print(f"{'  Avg Recall:':<28} {run2['avg_recall']:.4f}")
        print(f"{'  Duration:':<28} {run2['total_duration']:.2f}s")
        
        print(f"\n{'CHANGES (Run2 - Run1):':<30}")
        print(f"{'  F1 Delta:':<28} {deltas['f1_delta']:+.4f}")
        print(f"{'  Precision Delta:':<28} {deltas['precision_delta']:+.4f}")
        print(f"{'  Recall Delta:':<28} {deltas['recall_delta']:+.4f}")
        print(f"{'  Duration Delta:':<28} {deltas['duration_delta']:+.2f}s ({deltas['duration_delta_percent']:+.1f}%)")
        
        print(f"\n{'TOP 5 IMPROVEMENTS:':<30}")
        for i, test in enumerate(comparison["detailed_changes"]["biggest_improvements"], 1):
            print(f"  {i}. {test['test_name']:<25} {test['f1_run1']:.4f} → {test['f1_run2']:.4f} ({test['f1_change']:+.4f})")
        
        print(f"\n{'TOP 5 REGRESSIONS:':<30}")
        for i, test in enumerate(comparison["detailed_changes"]["biggest_regressions"], 1):
            print(f"  {i}. {test['test_name']:<25} {test['f1_run1']:.4f} → {test['f1_run2']:.4f} ({test['f1_change']:+.4f})")
        
        print("\n" + "="*80 + "\n")
    
    def analyze_by_scenario_type(self, run_id: str) -> pd.DataFrame:
        """Analyze performance by scenario type."""
        results = self.load_run_results(run_id)
        
        # Extract scenario type from test_name
        results["scenario_type"] = results["test_name"].apply(self._extract_scenario_type)
        
        summary = results.groupby("scenario_type").agg({
            "precision": "mean",
            "recall": "mean",
            "f1": "mean",
            "fpr": "mean",
            "duration_seconds": ["mean", "sum"],
            "test_name": "count"
        }).round(4)
        
        summary.columns = ["avg_precision", "avg_recall", "avg_f1", "avg_fpr", "avg_duration", "total_duration", "test_count"]
        
        return summary
    
    @staticmethod
    def _extract_scenario_type(test_name: str) -> str:
        """Extract scenario type from test name."""
        if test_name.startswith("se"):
            return "Single Extended"
        elif test_name.startswith("ss"):
            return "Single Sensitivity"
        elif test_name.startswith("s"):
            return "Single"
        elif test_name.startswith("m"):
            return "Multi"
        else:
            return "Unknown"


def main():
    """Example usage."""
    analyzer = ResultsAnalyzer()
    
    # Get all runs
    runs = analyzer.get_all_runs()
    print(f"Available runs: {runs}\n")
    
    # Find first pair of runs with actual results
    runs_with_results = []
    for run_id in runs:
        results_file = Path("test_logs") / run_id / "test_results.csv"
        if results_file.exists():
            try:
                df = pd.read_csv(results_file)
                if len(df) > 0:
                    runs_with_results.append(run_id)
            except Exception as e:
                print(f"Could not read {results_file}: {e}")
    
    print(f"Runs with results: {runs_with_results}\n")
    
    # Compare latest two runs with results if available
    if len(runs_with_results) >= 2:
        analyzer.generate_comparison_report(runs_with_results[1], runs_with_results[0])
    else:
        if len(runs_with_results) == 1:
            print(f"Only 1 run has results. Need at least 2 runs to compare.")
        else:
            print("No runs with results yet. Run tests first.")


if __name__ == "__main__":
    main()
