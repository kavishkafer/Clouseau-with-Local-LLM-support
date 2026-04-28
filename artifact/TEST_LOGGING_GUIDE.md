# Clouseau Test Logging & Analysis System

Complete result tracking and analysis system for comparing Clouseau test runs across different environments and models.

## Overview

This system provides:

1. **Comprehensive Test Logging** - Records detailed metrics for every test
2. **Result Comparison** - Compare two test runs to identify improvements and regressions
3. **Visualization** - Generate charts showing performance differences
4. **Analysis** - Break down results by scenario type and identify key changes

## Components

### 1. `test_logger.py` - Test Execution Logger

Captures detailed metrics for each test:
- Test name and scenario
- Start/end times and duration
- Performance metrics (precision, recall, F1, FPR)
- Token usage (if tracked)
- Success/failure status

**Database schema:**
- `runs` - Summary of each test run
- `test_results` - Individual test results

### 2. `results_analyzer.py` - Results Analysis

Compares results across runs:
- Load any stored run results
- Compare two runs in detail
- Identify biggest improvements and regressions
- Analyze performance by scenario type

### 3. `results_visualizer.py` - Visualization Generator

Creates charts for:
- Single run metrics distribution
- Comparison between two runs
- Scenario type performance breakdown
- F1 score changes visualization

### 4. `run_with_logging.py` - Test Runner

Executes tests with integrated logging:
- Runs all claims (Claim 1, 2, 3)
- Logs results automatically
- Generates summary statistics

## Usage

### On the DGX Machine

#### 1. Start vLLM Server

```bash
python -m vllm.entrypoints.openai.api_server \
  --model google/gemma-4-27b-it \
  --dtype auto \
  --gpu-memory-utilization 0.9 \
  --port 8000
```

#### 2. Run Tests with Logging

```bash
cd Clouseau/artifact

# Option A: Run all claims with logging
python run_with_logging.py

# Option B: Use the shell script (includes automatic analysis)
bash run_tests_with_logging.sh
```

### After Tests Complete

#### View Results Structure

```
test_logs/
├── test_runs.db                          # SQLite database with all runs
├── 20260428_120530/                      # Run directory (timestamp)
│   ├── run_metadata.json                 # Run configuration & summary stats
│   └── test_results.csv                  # Detailed test results
└── visualizations/
    ├── run_20260428_120530.png           # Single run visualization
    ├── scenario_types_20260428_120530.png
    └── comparison_20260428_12_vs_20260428_13.png
```

#### Compare Two Runs

```bash
python results_analyzer.py
```

This automatically:
1. Finds all available runs
2. Compares the latest two runs
3. Prints detailed comparison report
4. Saves comparison JSON

Or programmatically:

```python
from results_analyzer import ResultsAnalyzer

analyzer = ResultsAnalyzer()
runs = analyzer.get_all_runs()  # Get list of all run IDs

# Compare specific runs
analyzer.generate_comparison_report(runs[0], runs[1])
```

#### Generate Visualizations

```bash
python results_visualizer.py
```

Creates PNG charts in `test_logs/visualizations/`:
- Distribution of metrics
- F1 score by test
- Precision vs Recall scatter
- Duration analysis
- Comparison before/after charts

Or programmatically:

```python
from results_visualizer import ResultsVisualizer

visualizer = ResultsVisualizer()
analyzer = ResultsAnalyzer()
runs = analyzer.get_all_runs()

# Visualize specific run
visualizer.visualize_run(runs[0])

# Compare two runs visually
visualizer.visualize_comparison(runs[0], runs[1])
```

## Example Output

### Comparison Report

```
================================================================================
RUN COMPARISON SUMMARY
================================================================================

RUN 1:                         20260428_115530
  Model:                      gpt-4.1-mini
  Avg F1:                     0.8234
  Avg Precision:              0.8456
  Avg Recall:                 0.8012
  Duration:                   3245.32s

RUN 2:                         20260428_143045
  Model:                      google/gemma-4-27b-it
  Avg F1:                     0.8512
  Avg Precision:              0.8678
  Avg Recall:                 0.8351
  Duration:                   1847.23s

CHANGES (Run2 - Run1):
  F1 Delta:                   +0.0278
  Precision Delta:            +0.0222
  Recall Delta:               +0.0339
  Duration Delta:             -1398.09s (-43.1%)

TOP 5 IMPROVEMENTS:
  1. s2_domain                0.8234 → 0.9012 (+0.0778)
  2. s3_IP                    0.7654 → 0.8234 (+0.0580)
  ...

TOP 5 REGRESSIONS:
  1. se1_domain               0.9234 → 0.8901 (-0.0333)
  ...
```

## Data Interpretation

### Metrics

- **Precision**: Proportion of identified relevant items that were relevant (TP / (TP+FP))
- **Recall**: Proportion of all relevant items that were identified (TP / (TP+FN))
- **F1**: Harmonic mean of precision and recall (2 * P*R / (P+R))
- **FPR**: False positive rate (FP / (FP+TN))

### Scenario Types

- **Single (S1-S4)**: Standard test scenarios
- **Single Extended (SE1-SE4)**: Extended test scenarios
- **Single Sensitivity (SS1-SS4)**: Sensitivity analysis scenarios

## Tips for Analysis

1. **Compare baseline results first** - Run on the current machine if not already done
2. **Check scenario-specific changes** - Use `visualize_scenario_types()` to see if changes are consistent
3. **Investigate regressions** - If a specific test regresses significantly, review the test case
4. **Track over time** - Keep running comparisons to see consistency and trends
5. **Consider latency** - Duration changes can indicate model complexity differences

## File Locations

- **Test logger**: `artifact/test_logger.py`
- **Results analyzer**: `artifact/results_analyzer.py`
- **Results visualizer**: `artifact/results_visualizer.py`
- **Test runner**: `artifact/run_with_logging.py`
- **Shell script**: `artifact/run_tests_with_logging.sh`
- **Results directory**: `artifact/test_logs/`
- **Visualizations**: `artifact/test_logs/visualizations/`

## Troubleshooting

### vLLM Connection Issues

```python
# Quick test
import requests
try:
    response = requests.get("http://localhost:8000/v1/models")
    print(response.json())
except Exception as e:
    print(f"Cannot connect: {e}")
```

### Missing Dependencies

```bash
pip install pandas matplotlib seaborn scikit-learn
```

### Database Issues

The SQLite database is self-healing. Delete `test_logs/test_runs.db` to reset it.

## Integration with Current Workflow

You can run this alongside the existing Clouseau workflow:

```bash
# Old way (no logging)
cd artifact
python app.py --scenarios-si --csv-file ../claims/claim1/scenarios.csv

# New way (with logging)
python run_with_logging.py

# Then analyze
python results_analyzer.py
python results_visualizer.py
```

## Notes

- Ensure `LLM_MODEL`, `BASE_URL`, and `API_KEY` environment variables are set correctly
- The database persists across runs, allowing historical comparison
- Visualizations use high DPI (300) for publication quality
- All timestamps are ISO 8601 format for consistency
