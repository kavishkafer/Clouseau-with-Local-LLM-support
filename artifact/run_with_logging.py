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
        output_csv: str,
        claim_name: str
    ) -> bool:
        """
        Run a scenario test with logging.
        
        Args:
            scenario_type: Type of scenario (--scenarios-si, --scenarios-se, --scenarios-ss)
            output_csv: Path where app.py will save results
            claim_name: Name of the claim being tested
        
        Returns:
            bool: True if successful, False otherwise
        """
        print(f"\n{'='*70}")
        print(f"Running test: {claim_name} ({scenario_type})")
        print(f"Output CSV: {output_csv}")
        print(f"{'='*70}\n")
        
        # Build command - app.py handles scenario selection, --csv-file is for output
        cmd = [
            sys.executable,
            "app.py",
            scenario_type,
            "--csv-file", output_csv,
            "--no-warn"
        ]
        
        print(f"Running command: {' '.join(cmd)}\n")
        
        try:
            # Run the test with environment variables
            env = os.environ.copy()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=21600,  # 6 hour timeout
                env=env
            )
            
            if result.returncode != 0:
                print(f"⚠️  Test exited with code {result.returncode}")
                if result.stdout:
                    print(f"Output:\n{result.stdout}")
                if result.stderr:
                    print(f"Error output:\n{result.stderr}")
            
            # Parse results from the output CSV that app.py created
            results_csv_path = Path(output_csv)
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
            print(f"❌ Test timed out after 6 hours")
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
                "output_csv": "claim1_results.csv"
            },
            {
                "name": "Claim 2",
                "scenario_type": "--scenarios-se",
                "output_csv": "claim2_results.csv"
            },
            {
                "name": "Claim 3",
                "scenario_type": "--scenarios-ss",
                "output_csv": "claim3_results.csv"
            }
        ]
        
        successful = 0
        failed = 0
        
        for claim in claims:
            output_path = str(self.logger.run_dir / claim["output_csv"])
            success = self.run_scenario_test(
                scenario_type=claim["scenario_type"],
                output_csv=output_path,
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
