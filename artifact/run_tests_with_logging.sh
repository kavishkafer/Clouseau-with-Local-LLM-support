#!/bin/bash
# Test execution script for NVIDIA DGX with result logging
# This script runs all Clouseau tests with comprehensive logging and analysis

set -e  # Exit on error

echo "======================================================================"
echo "Clouseau Test Suite - DGX Execution with Result Logging"
echo "======================================================================"
echo ""

# Configuration
VLLM_PORT=${VLLM_PORT:-8000}
VLLM_MODEL=${VLLM_MODEL:-"/home/dgx-spark-01/ai_data/models/gemma-4-26b-moe"}
BASE_URL="http://localhost:${VLLM_PORT}/v1"
API_KEY="local"

# Check if vLLM server is reachable
echo "[CHECK] Verifying vLLM endpoint..."
if ! curl -s "${BASE_URL}/../health" > /dev/null 2>&1; then
    echo "⚠️  WARNING: Could not reach vLLM server at ${BASE_URL}"
    echo "   Make sure vLLM is running with:"
    echo "   python -m vllm.entrypoints.openai.api_server --model ${VLLM_MODEL} --port ${VLLM_PORT}"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set environment variables for LLM configuration
export LLM_MODEL="${VLLM_MODEL}"
export BASE_URL="${BASE_URL}"
export API_KEY="${API_KEY}"

echo "[INFO] Environment configured:"
echo "  LLM_MODEL: ${LLM_MODEL}"
echo "  BASE_URL: ${BASE_URL}"
echo ""

# Run tests with logging
echo "[INFO] Starting test execution with logging..."
echo ""

python run_with_logging.py

# After tests complete, run analysis and visualization
echo ""
echo "[INFO] Running analysis and visualization..."
python results_analyzer.py
python results_visualizer.py

echo ""
echo "======================================================================"
echo "Test execution complete!"
echo "======================================================================"
echo ""
echo "Results saved in: test_logs/"
echo "View comparisons: test_logs/visualizations/"
echo ""
