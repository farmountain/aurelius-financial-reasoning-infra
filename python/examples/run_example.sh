#!/bin/bash
# Example: Run AURELIUS orchestrator with a trend strategy goal

set -e

echo "========================================"
echo "AURELIUS Orchestrator Example"
echo "========================================"
echo ""

# Check if data file exists
if [ ! -f "../examples/data.parquet" ]; then
    echo "Generating sample data..."
    cd ..
    python3 examples/generate_data.py
    cd python
fi

echo "Running goal: 'design a trend strategy under DD<10%'"
echo ""

# Run the orchestrator
aureus run \
    --goal "design a trend strategy under DD<10%" \
    --data ../examples/data.parquet \
    --max-drawdown 0.10 \
    --strict

echo ""
echo "Example completed!"
