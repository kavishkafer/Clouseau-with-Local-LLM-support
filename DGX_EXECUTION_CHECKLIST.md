# DGX Execution Checklist

Quick step-by-step guide for running tests on NVIDIA DGX Spark with proper logging.

## Pre-Execution Checklist

- [ ] DGX machine has internet access to pull models
- [ ] Python 3.10+ installed
- [ ] vLLM installed: `pip install vllm`
- [ ] Clouseau repository copied to DGX
- [ ] Dependencies installed: `pip install -r artifact/requirements.txt`
- [ ] Sufficient GPU memory (~48GB for Gemma 4 26B)

## DGX Setup

### Phase 1: Environment Preparation (Do Once)

```bash
# SSH into DGX
ssh user@dgx-spark

# Clone/copy Clouseau if not already present
git clone <repo> Clouseau
# OR copy from local
cd Clouseau

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r artifact/requirements.txt
pip install matplotlib seaborn      # Required for visualization

# Verify installation
python artifact/test_logger.py
```

### Phase 2: Model Download (Pre-warm)

```bash
cd Clouseau

# Pre-download Gemma 4 model (one-time)
python -c "from vllm.model_executor.model_loader import get_model; \
           get_model(model_name='google/gemma-4-27b-it')"
```

Or use HuggingFace CLI:
```bash
huggingface-cli download google/gemma-4-27b-it
```

## Test Execution

### Step 1: Start vLLM Server

**Terminal 1: vLLM Server**

```bash
cd Clouseau

# Activate venv if needed
# source venv/bin/activate

# Start vLLM with Gemma 4
python -m vllm.entrypoints.openai.api_server \
  --model google/gemma-4-27b-it \
  --dtype auto \
  --gpu-memory-utilization 0.9 \
  --port 8000 \
  --tensor-parallel-size 1

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# Served model: google/gemma-4-27b-it
```

**⏱️ Time to first token:** ~2-5 minutes (model loading)

### Step 2: Run Tests with Logging

**Terminal 2: Test Runner**

```bash
cd Clouseau/artifact

# Activate venv if needed
# source venv/bin/activate

# Run with logging (includes analysis)
bash run_tests_with_logging.sh

# OR run just tests (faster)
python run_with_logging.py

# Expected output:
# [INFO] Environment configured:
#   LLM_MODEL: google/gemma-4-27b-it
#   BASE_URL: http://localhost:8000/v1
# ✓ Test logger initialized: test_logs/20260428_120530
# Running test: Claim 1 (--scenarios-si)
```

**⏱️ Estimated Time:**
- Claim 1 (Standard): 30-45 minutes
- Claim 2 (Extended): 45-60 minutes
- Claim 3 (Sensitivity): 60-90 minutes
- **Total: 2.5-3.5 hours** (vs 4-8 hours with GPT-4)

### Step 3: Monitor Progress

**Terminal 3: Monitoring (Optional)**

```bash
cd Clouseau/artifact

# Watch logs
tail -f test_logs/*/test_results.csv

# Check vLLM utilization
nvidia-smi -l 2  # GPU memory every 2 seconds

# Or monitor via vLLM metrics endpoint
watch -n 5 'curl -s http://localhost:8000/metrics | grep vllm'
```

## Results Analysis

### After Tests Complete

```bash
cd Clouseau/artifact

# Quick summary (requires tabulate)
pip install tabulate

# View latest results
python compare.py latest

# Compare with previous run
python compare.py compare

# List all runs
python compare.py list

# Generate visualizations (requires matplotlib)
python results_visualizer.py

# Full analysis
python results_analyzer.py
```

### View Results

Results will be in `Clouseau/artifact/test_logs/`:

```
test_logs/
├── run_metadata.json          # Configuration
├── test_results.csv           # Detailed results
└── visualizations/
    ├── run_TIMESTAMP.png              # Metrics distribution
    ├── scenario_types_TIMESTAMP.png   # By scenario type
    └── comparison_*.png               # Comparisons with previous runs
```

## Troubleshooting

### vLLM Won't Start

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Check GPU memory
nvidia-smi

# If OOM, reduce batch size
python -m vllm.entrypoints.openai.api_server \
  --model google/gemma-4-27b-it \
  --gpu-memory-utilization 0.8

# Or use smaller model
--model meta-llama/Llama-2-7b-hf
```

### Connection Issues

```bash
# Test API is running
curl http://localhost:8000/v1/models

# Check firewall
netstat -tlnp | grep 8000
```

### Out of Memory

```bash
# Reduce memory utilization
--gpu-memory-utilization 0.85  # Default 0.9

# Enable quantization
--quantization awq  # Or bitsandbytes, gptq

# Use distributed inference
--tensor-parallel-size 2  # If multiple GPUs
```

### Tests Not Running

```bash
# Check environment variables
echo $LLM_MODEL
echo $BASE_URL

# Set manually if needed
export LLM_MODEL="google/gemma-4-27b-it"
export BASE_URL="http://localhost:8000/v1"
export API_KEY="local"

# Test connection
python -c "import openai; openai.api_base='http://localhost:8000/v1'; print(openai.Model.list())"
```

## Performance Tips

1. **Warm GPU before tests**: Let vLLM run a dummy request first
2. **Disable debug logging**: `--no-log-requests` in vLLM
3. **Use tensor parallelism**: If multiple GPUs available
4. **Monitor memory**: `nvidia-smi` in separate terminal
5. **Background processes**: Close unnecessary apps to free memory

## Result Comparison Example

After DGX run completes:

```bash
python compare.py compare

# Output:
# ========================================================================
# QUICK COMPARISON
# ========================================================================
#
# Metric             Run 1              Run 2              Change
# Model              gpt-4.1-mini       google/gemma-4-   
# Avg F1             0.8234             0.8512             +0.0278
# Avg Precision      0.8456             0.8678             +0.0222
# Avg Recall         0.8012             0.8351             +0.0339
# Duration           3245.1s            1847.2s            -1397.9s (-43.1%)
#
# TOP 5 IMPROVEMENTS:
#   1. s2_domain                0.8234 → 0.9012 (+0.0778)
#   2. s3_IP                    0.7654 → 0.8234 (+0.0580)
```

## Cleanup (After Tests)

```bash
# Keep results but stop services
kill %1  # Stop vLLM server from background

# Archive results for later comparison
tar -czf clouseau_results_20260428.tar.gz Clouseau/artifact/test_logs/

# Transfer to local machine if needed
scp -r user@dgx-spark:~/Clouseau/artifact/test_logs ~/clouseau_dgx_results/
```

## Key Files to Monitor

- `artifact/run_with_logging.py` - Main test runner
- `artifact/test_logs/test_runs.db` - SQLite database with all results
- `artifact/test_logs/TIMESTAMP/run_metadata.json` - Run configuration
- `artifact/test_logs/TIMESTAMP/test_results.csv` - Detailed metrics

## Success Criteria

✅ vLLM server starts and serves models
✅ First test executes without errors
✅ Results logged to `test_logs/` directory
✅ All metrics calculated (precision, recall, F1, etc.)
✅ Comparison report generated successfully
✅ Visualizations created in `visualizations/` folder

## Contact Points

If tests fail:

1. Check GPU memory: `nvidia-smi`
2. Check vLLM logs: Look for errors on Terminal 1
3. Check API connectivity: `curl http://localhost:8000/v1/models`
4. Review error in `test_logs/` directory
5. Check model download: `huggingface-cli scan-cache`

## Time Estimates

| Phase | Duration | Notes |
|-------|----------|-------|
| Env setup | 10 min | One-time only |
| Model download | 5-10 min | First run only |
| vLLM startup | 2-5 min | Includes model loading |
| Claim 1 tests | 30-45 min | Standard scenarios |
| Claim 2 tests | 45-60 min | Extended scenarios |
| Claim 3 tests | 60-90 min | Sensitivity scenarios |
| Analysis/Viz | 1-2 min | Automatic after tests |
| **Total** | **2.5-3.5 hours** | Parallel vLLM = real time |

---

**Need help?** Check `TEST_LOGGING_GUIDE.md` for detailed documentation.
