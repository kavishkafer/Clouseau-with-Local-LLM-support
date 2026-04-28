#!/usr/bin/env python3
"""
Quick comparison utility for viewing test results.
Run this script to quickly compare recent test runs or get a summary.
"""

import sys
import json
from pathlib import Path
from tabulate import tabulate
from results_analyzer import ResultsAnalyzer


def print_run_summary(analyzer: ResultsAnalyzer, run_id: str):
    """Print a formatted summary of a single run."""
    try:
        metadata = analyzer.load_run_metadata(run_id)
        results = analyzer.load_run_results(run_id)
        
        print(f"\n{'='*70}")
        print(f"Run: {run_id}")
        print(f"{'='*70}")
        
        summary_data = [
            ["Model", metadata["model"]],
            ["Start Time", metadata["start_time"][:16]],
            ["Total Duration", f"{metadata['total_duration']:.2f}s ({metadata['total_duration']/60:.1f}m)"],
            ["Total Tests", metadata["total_tests"]],
            ["Successful", metadata["successful_tests"]],
            ["Failed", metadata["failed_tests"]],
            ["", ""],
            ["Avg Precision", f"{metadata['average_precision']:.4f}"],
            ["Avg Recall", f"{metadata['average_recall']:.4f}"],
            ["Avg F1", f"{metadata['average_f1']:.4f}"],
        ]
        
        print(tabulate(summary_data, tablefmt="simple"))
        print()
        
    except FileNotFoundError:
        print(f"❌ Run not found: {run_id}")


def print_quick_comparison(analyzer: ResultsAnalyzer, run_id_1: str = None, run_id_2: str = None):
    """Print a quick comparison between two runs."""
    runs = analyzer.get_all_runs()
    
    if not runs:
        print("❌ No runs found. Run tests first.")
        return
    
    # Use latest two runs if not specified
    if run_id_1 is None or run_id_2 is None:
        if len(runs) < 2:
            print("❌ Need at least 2 runs to compare.")
            return
        run_id_2 = runs[0]
        run_id_1 = runs[1]
    
    try:
        comparison = analyzer.compare_two_runs(run_id_1, run_id_2)
        
        print(f"\n{'='*70}")
        print(f"QUICK COMPARISON")
        print(f"{'='*70}\n")
        
        # Summary table
        comparison_data = [
            ["Metric", "Run 1", "Run 2", "Change"],
            ["Model", comparison["run_1"]["model"][:20], comparison["run_2"]["model"][:20], ""],
            ["Avg F1", f"{comparison['run_1']['avg_f1']:.4f}", f"{comparison['run_2']['avg_f1']:.4f}", 
             f"{comparison['deltas']['f1_delta']:+.4f}"],
            ["Avg Precision", f"{comparison['run_1']['avg_precision']:.4f}", f"{comparison['run_2']['avg_precision']:.4f}",
             f"{comparison['deltas']['precision_delta']:+.4f}"],
            ["Avg Recall", f"{comparison['run_1']['avg_recall']:.4f}", f"{comparison['run_2']['avg_recall']:.4f}",
             f"{comparison['deltas']['recall_delta']:+.4f}"],
            ["Duration", f"{comparison['run_1']['total_duration']:.1f}s", f"{comparison['run_2']['total_duration']:.1f}s",
             f"{comparison['deltas']['duration_delta']:+.1f}s ({comparison['deltas']['duration_delta_percent']:+.1f}%)"],
        ]
        
        print(tabulate(comparison_data, tablefmt="grid"))
        
        # Top changes
        print(f"\n{'TOP 5 IMPROVEMENTS:':<30}")
        for i, test in enumerate(comparison["detailed_changes"]["biggest_improvements"][:5], 1):
            print(f"  {i}. {test['test_name']:<25} {test['f1_run1']:.4f} → {test['f1_run2']:.4f} ({test['f1_change']:+.4f})")
        
        print(f"\n{'TOP 5 REGRESSIONS:':<30}")
        for i, test in enumerate(comparison["detailed_changes"]["biggest_regressions"][:5], 1):
            print(f"  {i}. {test['test_name']:<25} {test['f1_run1']:.4f} → {test['f1_run2']:.4f} ({test['f1_change']:+.4f})")
        
        print()
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")


def list_all_runs(analyzer: ResultsAnalyzer):
    """List all available runs."""
    runs = analyzer.get_all_runs()
    
    if not runs:
        print("❌ No runs found.")
        return
    
    print(f"\n{'='*70}")
    print(f"AVAILABLE RUNS ({len(runs)} total)")
    print(f"{'='*70}\n")
    
    runs_data = []
    for run_id in runs:
        try:
            metadata = analyzer.load_run_metadata(run_id)
            runs_data.append([
                run_id[:16],
                metadata["model"][:25],
                metadata["total_tests"],
                f"{metadata['average_f1']:.4f}",
                f"{metadata['total_duration']:.0f}s"
            ])
        except:
            pass
    
    print(tabulate(
        runs_data,
        headers=["Run ID", "Model", "Tests", "Avg F1", "Duration"],
        tablefmt="grid"
    ))
    print()


def main():
    """Main CLI interface."""
    analyzer = ResultsAnalyzer()
    
    if len(sys.argv) < 2:
        command = "list"
    else:
        command = sys.argv[1].lower()
    
    if command == "list" or command == "ls":
        list_all_runs(analyzer)
    
    elif command == "compare" or command == "comp":
        if len(sys.argv) == 4:
            print_quick_comparison(analyzer, sys.argv[2], sys.argv[3])
        else:
            print_quick_comparison(analyzer)
    
    elif command == "show" or command == "view":
        if len(sys.argv) < 3:
            print("Usage: python compare.py show <run_id>")
            sys.exit(1)
        print_run_summary(analyzer, sys.argv[2])
    
    elif command == "latest":
        runs = analyzer.get_all_runs()
        if runs:
            print_run_summary(analyzer, runs[0])
        else:
            print("❌ No runs found.")
    
    elif command == "help" or command == "-h":
        print("""
Clouseau Test Results Comparison Tool

Usage:
  python compare.py list              - List all runs
  python compare.py compare           - Compare latest two runs
  python compare.py compare <id1> <id2> - Compare specific runs
  python compare.py show <run_id>     - Show single run summary
  python compare.py latest            - Show latest run

Examples:
  python compare.py list
  python compare.py show 20260428_120530
  python compare.py compare 20260428_115530 20260428_143045
        """)
    
    else:
        print(f"Unknown command: {command}")
        print("Use 'python compare.py help' for usage information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
