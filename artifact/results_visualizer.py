"""
Visualization tool for comparing test results across different runs.
Creates charts showing performance metrics, duration, and changes.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from typing import Optional
from results_analyzer import ResultsAnalyzer


class ResultsVisualizer:
    """Generate comprehensive visualization of test results and comparisons."""
    
    def __init__(self, log_dir: str = "test_logs", output_dir: Optional[str] = None):
        self.log_dir = Path(log_dir)
        self.analyzer = ResultsAnalyzer(log_dir)
        
        # Create output directory for visualizations
        self.output_dir = Path(output_dir) if output_dir else self.log_dir / "visualizations"
        self.output_dir.mkdir(exist_ok=True)
        
        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (14, 8)
    
    def visualize_run(self, run_id: str):
        """Create visualizations for a single run."""
        results = self.analyzer.load_run_results(run_id)
        metadata = self.analyzer.load_run_metadata(run_id)
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f"Test Results - Run {run_id}\nModel: {metadata['model']}", fontsize=16, fontweight='bold')
        
        # 1. Metrics distribution
        metrics = ["precision", "recall", "f1", "fpr"]
        ax = axes[0, 0]
        results[metrics].boxplot(ax=ax)
        ax.set_title("Metrics Distribution")
        ax.set_ylabel("Score")
        ax.grid(True, alpha=0.3)
        
        # 2. F1 scores by test
        ax = axes[0, 1]
        results_sorted = results.sort_values("f1", ascending=True).tail(15)
        ax.barh(results_sorted["test_name"], results_sorted["f1"], color="steelblue")
        ax.set_xlabel("F1 Score")
        ax.set_title("Top 15 Test F1 Scores")
        ax.grid(True, alpha=0.3, axis='x')
        
        # 3. Precision vs Recall
        ax = axes[1, 0]
        scatter = ax.scatter(results["recall"], results["precision"], 
                           c=results["f1"], cmap="viridis", s=100, alpha=0.6)
        ax.set_xlabel("Recall")
        ax.set_ylabel("Precision")
        ax.set_title("Precision vs Recall (colored by F1)")
        ax.grid(True, alpha=0.3)
        plt.colorbar(scatter, ax=ax, label="F1 Score")
        
        # 4. Duration analysis
        ax = axes[1, 1]
        ax.bar(range(len(results)), results["duration_seconds"].sort_values(ascending=False).values, color="coral")
        ax.set_xlabel("Test Index (sorted by duration)")
        ax.set_ylabel("Duration (seconds)")
        ax.set_title("Test Duration Distribution")
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_file = self.output_dir / f"run_{run_id}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Visualization saved: {output_file}")
        plt.close()
    
    def visualize_comparison(self, run_id_1: str, run_id_2: str):
        """Create comparison visualizations between two runs."""
        comparison = self.analyzer.compare_two_runs(run_id_1, run_id_2)
        changes = comparison["detailed_changes"]["all_test_changes"]
        
        changes_df = pd.DataFrame(changes)
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle(f"Comparison: {run_id_2} vs {run_id_1}\n{comparison['run_2']['model']} vs {comparison['run_1']['model']}", 
                    fontsize=16, fontweight='bold')
        
        # 1. F1 changes
        ax = axes[0, 0]
        changes_sorted = changes_df.sort_values("f1_change")
        colors = ["red" if x < 0 else "green" for x in changes_sorted["f1_change"]]
        ax.barh(range(len(changes_sorted)), changes_sorted["f1_change"].values, color=colors)
        ax.set_yticks(range(len(changes_sorted)))
        ax.set_yticklabels(changes_sorted["test_name"].values, fontsize=8)
        ax.set_xlabel("F1 Change (Run2 - Run1)")
        ax.set_title("F1 Score Changes by Test")
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.8)
        ax.grid(True, alpha=0.3, axis='x')
        
        # 2. Metric deltas summary
        ax = axes[0, 1]
        metrics = ["precision_delta", "recall_delta", "f1_delta"]
        values = [comparison["deltas"].get(m, 0) for m in metrics]
        colors_delta = ["green" if v >= 0 else "red" for v in values]
        bars = ax.bar(["Precision", "Recall", "F1"], values, color=colors_delta, alpha=0.7, edgecolor='black')
        ax.set_ylabel("Change")
        ax.set_title("Overall Metric Changes")
        ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{val:+.4f}',
                   ha='center', va='bottom' if height > 0 else 'top', fontweight='bold')
        
        # 3. Scatter: Old F1 vs New F1
        ax = axes[1, 0]
        results1 = self.analyzer.load_run_results(run_id_1)
        results2 = self.analyzer.load_run_results(run_id_2)
        merged = pd.merge(results1[["test_name", "f1"]], results2[["test_name", "f1"]], 
                         on="test_name", suffixes=("_old", "_new"))
        
        ax.scatter(merged["f1_old"], merged["f1_new"], s=100, alpha=0.6, edgecolors='black')
        
        # Add diagonal line (no change)
        min_val = min(merged["f1_old"].min(), merged["f1_new"].min())
        max_val = max(merged["f1_old"].max(), merged["f1_new"].max())
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='No Change')
        
        ax.set_xlabel(f"F1 Score - Run1 ({run_id_1[:8]})")
        ax.set_ylabel(f"F1 Score - Run2 ({run_id_2[:8]})")
        ax.set_title("F1 Score Comparison")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # 4. Performance summary table
        ax = axes[1, 1]
        ax.axis('off')
        
        # Create summary text
        summary_text = f"""
SUMMARY STATISTICS

Run 1: {comparison['run_1']['id'][:16]}
  Model: {comparison['run_1']['model']}
  Avg F1: {comparison['run_1']['avg_f1']:.4f}
  Avg Precision: {comparison['run_1']['avg_precision']:.4f}
  Avg Recall: {comparison['run_1']['avg_recall']:.4f}
  Duration: {comparison['run_1']['total_duration']:.2f}s

Run 2: {comparison['run_2']['id'][:16]}
  Model: {comparison['run_2']['model']}
  Avg F1: {comparison['run_2']['avg_f1']:.4f}
  Avg Precision: {comparison['run_2']['avg_precision']:.4f}
  Avg Recall: {comparison['run_2']['avg_recall']:.4f}
  Duration: {comparison['run_2']['total_duration']:.2f}s

DELTAS:
  F1 Delta: {comparison['deltas']['f1_delta']:+.4f}
  Precision Delta: {comparison['deltas']['precision_delta']:+.4f}
  Recall Delta: {comparison['deltas']['recall_delta']:+.4f}
  Duration Delta: {comparison['deltas']['duration_delta']:+.2f}s ({comparison['deltas']['duration_delta_percent']:+.1f}%)
        """
        
        ax.text(0.1, 0.95, summary_text, transform=ax.transAxes, 
               fontsize=10, verticalalignment='top', fontfamily='monospace',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        plt.tight_layout()
        output_file = self.output_dir / f"comparison_{run_id_1[:8]}_vs_{run_id_2[:8]}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Comparison visualization saved: {output_file}")
        plt.close()
    
    def visualize_scenario_types(self, run_id: str):
        """Visualize performance by scenario type."""
        summary = self.analyzer.analyze_by_scenario_type(run_id)
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(f"Performance by Scenario Type - Run {run_id}", fontsize=14, fontweight='bold')
        
        # 1. Average metrics by type
        ax = axes[0, 0]
        metrics_cols = ["avg_precision", "avg_recall", "avg_f1"]
        summary[metrics_cols].plot(kind="bar", ax=ax, color=["skyblue", "lightcoral", "lightgreen"])
        ax.set_title("Average Metrics by Scenario Type")
        ax.set_ylabel("Score")
        ax.set_xlabel("Scenario Type")
        ax.legend(["Precision", "Recall", "F1"])
        ax.grid(True, alpha=0.3, axis='y')
        
        # 2. Test count by type
        ax = axes[0, 1]
        summary["test_count"].plot(kind="bar", ax=ax, color="steelblue")
        ax.set_title("Test Count by Scenario Type")
        ax.set_ylabel("Count")
        ax.set_xlabel("Scenario Type")
        ax.grid(True, alpha=0.3, axis='y')
        
        # 3. Average duration by type
        ax = axes[1, 0]
        summary["avg_duration"].plot(kind="bar", ax=ax, color="coral")
        ax.set_title("Average Duration by Scenario Type")
        ax.set_ylabel("Duration (seconds)")
        ax.set_xlabel("Scenario Type")
        ax.grid(True, alpha=0.3, axis='y')
        
        # 4. FPR by type
        ax = axes[1, 1]
        summary["avg_fpr"].plot(kind="bar", ax=ax, color="lightblue")
        ax.set_title("Average False Positive Rate by Scenario Type")
        ax.set_ylabel("FPR")
        ax.set_xlabel("Scenario Type")
        ax.grid(True, alpha=0.3, axis='y')
        
        plt.tight_layout()
        output_file = self.output_dir / f"scenario_types_{run_id}.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Scenario type visualization saved: {output_file}")
        plt.close()


def main():
    """Create visualizations for all runs."""
    visualizer = ResultsVisualizer()
    analyzer = ResultsAnalyzer()
    
    runs = analyzer.get_all_runs()
    print(f"Found {len(runs)} runs\n")
    
    # Filter runs that have results
    runs_with_results = []
    for run_id in runs:
        results_file = Path("test_logs") / run_id / "test_results.csv"
        if results_file.exists():
            try:
                df = pd.read_csv(results_file)
                if len(df) > 0:
                    runs_with_results.append(run_id)
            except Exception as e:
                print(f"Skipping {run_id}: {e}")
    
    print(f"Runs with results: {len(runs_with_results)}\n")
    
    # Visualize each run with results
    for run_id in runs_with_results:
        print(f"Visualizing run: {run_id}")
        try:
            visualizer.visualize_run(run_id)
            visualizer.visualize_scenario_types(run_id)
        except Exception as e:
            print(f"Could not visualize {run_id}: {e}")
    
    # Compare consecutive runs with results
    if len(runs_with_results) >= 2:
        print(f"\nCreating comparison: {runs_with_results[0]} vs {runs_with_results[1]}")
        try:
            visualizer.visualize_comparison(runs_with_results[1], runs_with_results[0])
        except Exception as e:
            print(f"Could not create comparison: {e}")


if __name__ == "__main__":
    main()
