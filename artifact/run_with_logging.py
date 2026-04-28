"""
Test runner with integrated logging.
This script wraps the Clouseau app.py to capture all results with detailed metrics.
"""

import os
import sys
import subprocess
import pandas as pd
import json
from pathlib import Path
from test_logger import TestLogger
from typing import Tuple


class LoggingTestRunner:
    """Run tests with comprehensive logging."""
    
    def __init__(self):
        self.logger = TestLogger()
        self.test_results_dir = Path("../claims")
    
    def run_scenario_test(
        self,
        scenario_type: str,
        csv_file: str,
        claim_name: str
    ) -> bool:
        """
        Run a scenario test with logging.
        
        Args:
            scenario_type: Type of scenario (--scenarios-si, --scenarios-se, --scenarios-ss)
            csv_file: Path to CSV file with test scenarios
            claim_name: Name of the claim being tested
        
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"Running test: {claim_name} ({scenario_type})")
        print(f"CSV file: {csv_file}")
        print(f"{'='*70}\n")
        
        # Check if CSV file exists
        csv_path = Path(csv_file)
        if not csv_path.exists():
            print(f"❌ CSV file not found: {csv_file}")
            return False
        
        # Build command
        cmd = [
            sys.executable,
            "app.py",
            scenario_type,
            "--csv-file", csv_file,
            "--no-warn"
        ]
        
        print(f"Running command: {' '.join(cmd)}\n")
        
        try:
            # Run the test
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                print(f"⚠️  Test exited with code {result.returncode}")
                if result.stderr:
                    print(f"Error output:\n{result.stderr}")
            
            # Parse results from CSV
            results_csv_path = Path(csv_file).parent / "average.csv"
            if results_csv_path.exists():
                results_df = pd.read_csv(results_csv_path)
                
                # Log each result
                for idx, row in results_df.iterrows():
                    test_info = self.logger.log_test_start(claim_name, row["test_name"])
                    
                    self.logger.log_test_result(
                        test_info,
                        tp=int(row["tp"]),
                        tn=int(row["tn"]),
                        fp=int(row["fp"]),
                        fn=int(row["fn"]),
                        total_tokens=int(row["total_tokens"]) if "total_tokens" in row else 0,
                        input_tokens=int(row["input_tokens"]) if "input_tokens" in row else 0,
                        output_tokens=int(row["output_tokens"]) if "output_tokens" in row else 0,
                        status="success"
                    )
                
                print(f"✓ Logged {len(results_df)} test results from {results_csv_path}")
                return True
            else:
                print(f"⚠️  Results file not found: {results_csv_path}")
                return False
        
        except subprocess.TimeoutExpired:
            print(f"❌ Test timed out after 1 hour")
            return False
        except Exception as e:
            print(f"❌ Error running test: {e}")
            return False
    
    def run_all_claims(self):
        """Run all claims (claim 1, 2, 3)."""
        claims = [
            {
                "name": "Claim 1",
                "scenario_type": "--scenarios-si",
                "csv_file": "../claims/claim1/scenarios.csv"
            },
            {
                "name": "Claim 2",
                "scenario_type": "--scenarios-se",
                "csv_file": "../claims/claim2/scenarios.csv"
            },
            {
                "name": "Claim 3",
                "scenario_type": "--scenarios-ss",
                "csv_file": "../claims/claim3/scenarios.csv"
            }
        ]
        
        successful = 0
        failed = 0
        
        for claim in claims:
            success = self.run_scenario_test(
                scenario_type=claim["scenario_type"],
                csv_file=claim["csv_file"],
                claim_name=claim["name"]
            )
            
            if success:
                successful += 1
            else:
                failed += 1
        
        # Finalize and summarize
        metadata = self.logger.finalize_run()
        
        print(f"\n{'='*70}")
        print(f"TEST RUN SUMMARY")
        print(f"{'='*70}")
        print(f"Claims completed: {successful}/{len(claims)}")
        print(f"Run ID: {self.logger.get_run_id()}")
        print(f"Results directory: {self.logger.run_dir}")
        print(f"{'='*70}\n")
        
        return metadata


def main():
    """Main entry point."""
    runner = LoggingTestRunner()
    runner.run_all_claims()


if __name__ == "__main__":
    main()
