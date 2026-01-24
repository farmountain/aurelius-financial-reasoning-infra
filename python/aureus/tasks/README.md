# AURELIUS Task Generator and Benchmark Suite

This module provides tools for generating synthetic market regimes, creating benchmark tasks, and evaluating performance across different market conditions.

## Features

### 1. Synthetic Regime Generator

Generate deterministic OHLCV market data for different regimes:

- **Trend**: Market with directional drift (uptrend/downtrend)
- **Chop**: Range-bound market with mean reversion
- **Vol Spike**: Market with occasional volatility spikes

```python
from aureus.tasks import generate_regime_data, RegimeType

# Generate trending market data
trend_data = generate_regime_data(
    regime_type=RegimeType.TREND,
    num_days=252,
    seed=42,
    drift=0.001,  # Positive drift
    volatility=0.015
)

# Generate choppy market data
chop_data = generate_regime_data(
    regime_type=RegimeType.CHOP,
    num_days=252,
    seed=42,
    mean_reversion_strength=0.2
)

# Generate market with volatility spikes
vol_spike_data = generate_regime_data(
    regime_type=RegimeType.VOL_SPIKE,
    num_days=252,
    seed=42,
    spike_frequency=0.05,
    spike_multiplier=3.0
)
```

**Key Features:**
- Deterministic: Same seed always produces identical data
- OHLCV invariants: High ≥ max(Open, Close), Low ≤ min(Open, Close)
- Realistic price dynamics: Random walk with regime-specific characteristics

### 2. Task Generator

Generate benchmark tasks for different objectives:

```python
from aureus.tasks import TaskGenerator, RegimeType, TaskType

generator = TaskGenerator(seed=42)

# Design task: Create a new strategy
design_task = generator.generate_design_task(
    regime=RegimeType.TREND,
    max_drawdown=0.25,
    min_sharpe=1.5,
    num_days=252
)

# Debug task: Find and fix issues
debug_task = generator.generate_debug_task(
    regime=RegimeType.CHOP,
    issue="excessive drawdown",
    num_days=252
)

# Repair task: Fix CRV violations
repair_task = generator.generate_repair_task(
    regime=RegimeType.VOL_SPIKE,
    violation="max_drawdown_constraint",
    target_metric={"max_drawdown": 0.20},
    num_days=252
)

# Optimize task: Improve specific metrics
optimize_task = generator.generate_optimize_task(
    regime=RegimeType.TREND,
    objective="sharpe_ratio",
    target_value=2.0,
    num_days=252
)

# Generate complete suite across all regimes
task_suite = generator.generate_task_suite(
    regimes=[RegimeType.TREND, RegimeType.CHOP, RegimeType.VOL_SPIKE],
    num_days=252
)
```

**Task Types:**
- `DESIGN`: Create a strategy from scratch
- `DEBUG`: Diagnose and fix strategy issues
- `REPAIR`: Fix CRV violations
- `OPTIMIZE`: Improve strategy metrics

### 3. HipCortex Storage

Store tasks and gold trajectories as content-addressed artifacts:

```python
from aureus.tasks import HipCortexStorage, GoldTrajectory, store_task_suite

# Initialize storage
storage = HipCortexStorage(".hipcortex")

# Store a task
task_hash = storage.store_task(task, metadata={
    "author": "researcher",
    "version": "1.0"
})

# Store gold trajectory (expected solution)
gold_trajectory = GoldTrajectory(
    task_id=task.task_id,
    strategy_spec={
        "type": "ts_momentum",
        "lookback": 20,
        "vol_target": 0.15,
    },
    expected_metrics={
        "sharpe_ratio": 1.5,
        "max_drawdown": 0.18,
    }
)
trajectory_hash = storage.store_gold_trajectory(gold_trajectory)

# Retrieve artifacts
retrieved_task = storage.retrieve_task(task.task_id)
retrieved_trajectory = storage.retrieve_gold_trajectory(task.task_id)

# List all stored artifacts
task_ids = storage.list_tasks()
trajectory_ids = storage.list_trajectories()

# Bulk storage
task_hashes = store_task_suite(tasks, storage_dir=".hipcortex")
```

**Storage Features:**
- Content-addressed: SHA256 hashing ensures reproducibility
- Symlinks: Easy lookup by task_id
- JSON format: Human-readable and version-controllable
- Metadata support: Add custom metadata to artifacts

### 4. Benchmark Runner

Execute tasks and generate performance metrics:

```python
from aureus.tasks import BenchmarkRunner

# Initialize runner
runner = BenchmarkRunner(output_dir="./benchmark_output")

# Run single task
result = runner.run_task(task)
print(f"Passed: {result.passed}")
print(f"CRV Passed: {result.crv_passed}")
print(f"Metrics: {result.metrics}")

# Run complete suite
results = runner.run_suite(tasks)

print(f"Total tasks: {results.total_tasks}")
print(f"Pass rate: {results.pass_rate:.1%}")
print(f"CRV pass rate: {results.crv_pass_rate:.1%}")
print(f"Robustness score: {results.robustness_score:.1%}")

# Access individual results
for task_result in results.task_results:
    print(f"{task_result.task_id}: {task_result.passed}")
```

**Metrics:**
- **Pass rate**: Percentage of tasks that meet constraints
- **CRV pass rate**: Percentage passing CRV verification
- **Robustness score**: Combined metric (average of pass rates)

### 5. Task Schema Validation

All tasks are validated using Pydantic schemas:

```python
from aureus.tasks import Task, TaskType, RegimeConfig

# Tasks are automatically validated
task = Task(
    task_id="test_001",
    task_type=TaskType.DESIGN,
    goal="Design a trend strategy under DD < 25%",
    regime=RegimeType.TREND,
    constraints={"max_drawdown": 0.25},
    data_config=RegimeConfig(
        regime_type=RegimeType.TREND,
        num_days=252,
        seed=42
    )
)

# Serialize to dict
task_dict = task.to_dict()

# Deserialize from dict
task = Task.from_dict(task_dict)
```

## Example Usage

See `examples/task_benchmark_demo.py` for a complete demonstration:

```bash
cd python
python examples/task_benchmark_demo.py
```

This demo:
1. Generates synthetic data for all regimes
2. Creates a variety of tasks
3. Stores tasks in HipCortex
4. Stores gold trajectories
5. Runs benchmark suite
6. Reports comprehensive metrics

## Testing

The module includes comprehensive tests covering:

- **Synthetic generator determinism**: Same seed produces identical data
- **Task schema validation**: All task fields validated
- **Benchmark runner stability**: Multiple runs produce consistent results
- **Storage integrity**: Content-addressed hashing ensures reproducibility

Run tests:

```bash
pytest tests/test_synthetic_generator.py
pytest tests/test_task_generator.py
pytest tests/test_benchmark.py
pytest tests/test_storage.py
```

All tests pass with 100% coverage of critical functionality.

## Architecture

```
aureus/tasks/
├── __init__.py              # Public API
├── synthetic_generator.py   # Synthetic regime generation
├── task_generator.py        # Task creation
├── benchmark.py             # Benchmark runner
└── storage.py               # HipCortex integration

tests/
├── test_synthetic_generator.py  # Generator tests (13 tests)
├── test_task_generator.py       # Task tests (15 tests)
├── test_benchmark.py            # Benchmark tests (13 tests)
└── test_storage.py              # Storage tests (17 tests)
```

## Design Principles

1. **Determinism**: All randomness is seeded; reproducible results
2. **Type Safety**: Pydantic schemas for validation
3. **Content Addressing**: SHA256 hashing for artifacts
4. **Regime Diversity**: Test strategies across market conditions
5. **Comprehensive Testing**: 58 tests covering all functionality

## License

Apache License 2.0 - see [LICENSE](../../LICENSE) for details.
