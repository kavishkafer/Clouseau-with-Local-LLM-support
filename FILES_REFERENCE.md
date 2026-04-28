# New Test Logging System - File Reference

Quick reference guide for all new files created for result logging and analysis.

## Overview

Complete system for tracking, analyzing, and comparing test results across different environments and models.

## New Files by Location

### In `Clouseau/artifact/`

#### Core Logging System

| File | Purpose | Usage |
|------|---------|-------|
| `test_logger.py` | Test execution logging | `from test_logger import TestLogger` |
| `results_analyzer.py` | Compare and analyze runs | `python results_analyzer.py` or `from results_analyzer import ResultsAnalyzer` |
| `results_visualizer.py` | Generate charts/visualizations | `python results_visualizer.py` |

#### Test Runners

| File | Purpose | Usage |
|------|---------|-------|
| `run_with_logging.py` | Run all tests with logging | `python run_with_logging.py` |
| `run_tests_with_logging.sh` | DGX wrapper script | `bash run_tests_with_logging.sh` |
| `compare.py` | Quick CLI comparison tool | `python compare.py list\|compare\|show <id>` |

#### Documentation

| File | Purpose | Usage |
|------|---------|-------|
| `TEST_LOGGING_GUIDE.md` | Comprehensive guide | Read for complete documentation |

### In `Clouseau/` (Root)

| File | Purpose | Usage |
|------|---------|-------|
| `RESULT_LOGGING_SETUP.md` | System architecture overview | Read for high-level understanding |
| `DGX_EXECUTION_CHECKLIST.md` | Step-by-step DGX instructions | Follow for running on DGX machine |

### Also Updated

| File | Purpose |
|------|---------|
| `.gitignore` | Excludes `test_logs/` from git |

## File Dependencies

```
run_with_logging.py
    └─ test_logger.py
       └─ (creates) test_logs/

compare.py
    └─ results_analyzer.py
       └─ (reads) test_logs/

results_visualizer.py
    └─ results_analyzer.py
       └─ (reads) test_logs/
       └─ (creates) test_logs/visualizations/
```

## Quick Start by Role

### I'm on the Current Machine (Local)

1. Read: `RESULT_LOGGING_SETUP.md`
2. Run: `cd artifact && python run_with_logging.py`
3. Check: `python compare.py latest`

### I'm Running on DGX

1. Read: `DGX_EXECUTION_CHECKLIST.md`
2. Copy: All files from `artifact/` to DGX
3. Run: `bash run_tests_with_logging.sh`
4. Analyze: `python compare.py compare`

### I Want to Understand the System

1. Read: `TEST_LOGGING_GUIDE.md`
2. Read: `RESULT_LOGGING_SETUP.md`
3. Browse: Source code in `artifact/*.py`

## Data Flow

```
Input
  ↓
run_with_logging.py
  ├─ Calls test_logger.py
  │  └─ Creates test_logs/TIMESTAMP/
  │     ├─ run_metadata.json
  │     ├─ test_results.csv
  │     └─ (appends to test_runs.db)
  ↓
Results Available
  ↓
results_analyzer.py
  └─ Reads from test_logs/
     └─ Generates comparison reports
        └─ Saves comparison_*.json
  ↓
results_visualizer.py
  └─ Reads from test_logs/
     └─ Generates charts
        └─ Saves test_logs/visualizations/*.png
  ↓
compare.py (CLI)
  └─ Reads from test_logs/
     └─ Displays formatted summaries
```

## Execution Workflows

### Workflow 1: Single Machine Baseline

```bash
cd artifact
python run_with_logging.py
# Saves run ID (e.g., 20260428_110000)
# Creates test_logs/20260428_110000/
```

### Workflow 2: Compare Two Runs

```bash
cd artifact
python compare.py compare 20260428_110000 20260428_150000
```

### Workflow 3: Full Analysis with Visualizations

```bash
cd artifact
python run_with_logging.py      # Run tests
python results_analyzer.py      # Generate comparison
python results_visualizer.py    # Create charts
```

### Workflow 4: DGX Execution (Recommended)

```bash
cd artifact
bash run_tests_with_logging.sh  # Does everything:
                                # - Checks vLLM
                                # - Runs tests
                                # - Analyzes results
                                # - Creates visualizations
```

## Output Files

### After `run_with_logging.py`

```
artifact/test_logs/
├── test_runs.db                     # Persistent SQLite database
├── 20260428_110000/                 # Run directory (timestamp format)
│   ├── run_metadata.json            # Metadata and aggregate stats
│   │   {
│   │     "run_id": "20260428_110000",
│   │     "model": "google/gemma-4-27b-it",
│   │     "total_tests": 42,
│   │     "average_f1": 0.8512,
│   │     ...
│   │   }
│   ├── test_results.csv             # Detailed per-test results
│   │   test_name,precision,recall,f1,fpr,duration_seconds,...
│   │   s1_IP,0.9234,0.8901,0.9065,0.0123,45.32,...
│   │   ...
└── 20260428_150000/
    └── ...
```

### After `results_analyzer.py`

```
artifact/test_logs/
├── comparison_20260428_11_vs_20260428_15.json
│   {
│     "run_1": {...},
│     "run_2": {...},
│     "deltas": {
│       "f1_delta": +0.0278,
│       "precision_delta": +0.0222,
│       ...
│     },
│     "detailed_changes": {
│       "biggest_improvements": [...],
│       "biggest_regressions": [...]
│     }
│   }
```

### After `results_visualizer.py`

```
artifact/test_logs/visualizations/
├── run_20260428_110000.png              # Single run metrics
├── scenario_types_20260428_110000.png   # By scenario type
├── comparison_11_vs_15.png              # Side-by-side comparison
└── ... (more runs and comparisons)
```

## Command Reference

### Test Execution

```bash
python run_with_logging.py           # Run all tests with logging
```

### Quick Analysis

```bash
python compare.py list               # List all runs
python compare.py latest             # Show latest run
python compare.py compare            # Compare latest two runs
python compare.py show <run_id>      # Show specific run
python compare.py compare <id1> <id2> # Compare two specific runs
```

### Full Analysis

```bash
python results_analyzer.py           # Generate comparison reports
python results_visualizer.py         # Create visualization charts
```

### DGX Execution

```bash
bash run_tests_with_logging.sh       # Do everything at once
```

## Key Metrics Explained

- **Precision**: Accuracy of positive predictions (TP / (TP+FP))
- **Recall**: Coverage of actual positives (TP / (TP+FN))
- **F1**: Harmonic mean of precision and recall
- **FPR**: False positive rate (FP / (FP+TN))
- **Duration**: Execution time in seconds

## Configuration

### Environment Variables

```bash
export LLM_MODEL="google/gemma-4-27b-it"  # Model to use
export BASE_URL="http://localhost:8000/v1"  # vLLM endpoint
export API_KEY="local"                      # API key
```

### Python Dependencies

```bash
pip install pandas matplotlib seaborn
```

## Database Schema

### `test_runs` table

```sql
CREATE TABLE runs (
    run_id TEXT PRIMARY KEY,
    start_time TEXT,
    end_time TEXT,
    model TEXT,
    base_url TEXT,
    environment TEXT,
    total_duration_seconds REAL
)
```

### `test_results` table

```sql
CREATE TABLE test_results (
    id INTEGER PRIMARY KEY,
    run_id TEXT,
    scenario_name TEXT,
    test_name TEXT,
    start_time TEXT,
    end_time TEXT,
    duration_seconds REAL,
    tp INTEGER, tn INTEGER, fp INTEGER, fn INTEGER,
    precision REAL, recall REAL, fpr REAL, f1 REAL,
    total_tokens INTEGER,
    input_tokens INTEGER,
    output_tokens INTEGER,
    status TEXT,
    error_message TEXT
)
```

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: pandas` | `pip install pandas matplotlib seaborn` |
| `No runs found` | Run `python run_with_logging.py` first |
| `vLLM not reachable` | Check vLLM server is running on port 8000 |
| `Database locked` | Delete `test_logs/test_runs.db` and restart |
| No visualizations created | Check `test_logs/visualizations/` exists and matplotlib installed |

## Example Outputs

### `compare.py list`

```
AVAILABLE RUNS (3 total)

Run ID           Model                   Tests    Avg F1    Duration
20260428_150045  google/gemma-4-27b-it   42       0.8512    1847s
20260428_143000  google/gemma-4-27b-it   42       0.8234    2145s
20260428_110000  gpt-4.1-mini            42       0.8156    3245s
```

### `compare.py compare`

```
Metric             Run 1              Run 2              Change
Model              gpt-4.1-mini       google/gemma-4-27b  
Avg F1             0.8234             0.8512             +0.0278
Precision          0.8456             0.8678             +0.0222
Recall             0.8012             0.8351             +0.0339
Duration           3245.1s            1847.2s            -43.1%

TOP IMPROVEMENTS:
  1. s2_domain     0.8234 → 0.9012 (+0.0778)
  2. s3_IP         0.7654 → 0.8234 (+0.0580)
```

## Success Checklist

- [ ] All Python files copied to `artifact/`
- [ ] `.gitignore` updated to exclude `test_logs/`
- [ ] Dependencies installed: `pandas`, `matplotlib`, `seaborn`
- [ ] `run_with_logging.py` runs without errors
- [ ] Results appear in `test_logs/` directory
- [ ] `compare.py` displays results correctly
- [ ] Visualizations generate successfully

---

**For detailed information, see `TEST_LOGGING_GUIDE.md`**
