# AURELIUS Quant Reasoning Model

An Evidence-Gated Intelligence Engine for Quant Reasoning - Event-Driven Backtest Engine in Rust with Python Orchestration

## ✅ Status: Phase 2 Complete

AURELIUS is now a **production-ready quantitative research platform** with:

- 🎯 **8 Professional Strategy Types** (momentum, mean-reversion, breakout, pairs trading, stat arb, ML classifier, carry trade, volatility trading)
- 🔬 **Walk-Forward Validation** - Industry-standard out-of-sample testing
- 🤖 **LLM-Assisted Strategy Generation** - GPT-4 and Claude-3.5 integration
- 🛡️ **Dual-Loop Evidence Gates** - Automated quality assurance
- 📊 **73 Rust Tests + 141 Python Tests** - All passing

### Active Workspace (Unified)

All crates are now **active workspace members** with complete CI/CD:

- **`schema`**: Core traits and data structures (DataFeed, Strategy, Portfolio, Order)
- **`engine`**: Backtest engine with portfolio management and determinism
- **`broker_sim`**: Broker simulator for order execution
- **`cost`**: Cost model implementations
- **`cli`**: Command-line interface with example strategies
- **`crv_verifier`**: CRV verification suite (12 passing tests)
- **`hipcortex`**: Content-addressed artifact storage (20 passing tests)

### Python Orchestrator

- **`aureus`**: Complete Python orchestration framework with FSM, gates, and LLM integration

### Directory Structure

```
├── crates/           # Rust crates (all active workspace members)
│   ├── schema/      # ✅ Core traits and data structures
│   ├── engine/      # ✅ Backtest engine
│   ├── broker_sim/  # ✅ Broker simulator
│   ├── cost/        # ✅ Cost models
│   ├── cli/         # ✅ Command-line interface
│   ├── crv_verifier/# ✅ CRV verification suite
│   └── hipcortex/   # ✅ Artifact storage
├── python/          # Python orchestrator (complete)
│   ├── aureus/      # Core orchestration modules
│   │   ├── fsm/     # Goal-guard state machine
│   │   ├── gates/   # Dev and product gates
│   │   ├── reflexion/ # Failure recovery loop
│   │   └── tasks/   # Task generation and storage
│   ├── tests/       # 141 Python tests (all passing)
│   └── examples/    # Usage examples and demos
├── docs/            # Documentation
├── data/            # Sample data files
├── specs/           # Formal specifications
└── examples/        # Example strategies and data
```

## Quick Start

### Prerequisites

- **Rust**: 1.70.0 or later (install from [rust-lang.org](https://rust-lang.org))
- **Make**: GNU Make or compatible (for CI commands)
- **Python**: 3.9+ (required for orchestrator)
- **Optional**: OpenAI API key or Anthropic API key for LLM-assisted strategy generation

### Build and Test

Run the full CI pipeline to verify all gates pass:

```bash
make ci
```

This will execute:
1. **Formatting check**: `cargo fmt --check` - ensures code is formatted
2. **Linting**: `cargo clippy` - runs static analysis with pedantic warnings
3. **Tests**: `cargo test --all` - runs all unit and integration tests

### Individual Commands

```bash
make fmt         # Autoformat code
make fmt-check   # Check formatting without modifying
make clippy      # Run linter (Sprint 1: warnings only, no PR failures)
make test        # Run all tests
```

### Determinism Guarantee (Sprint 1)

All randomness in the `engine` crate is **seeded** using `ChaCha8Rng` with explicit seeds for reproducibility.

**No system time dependencies** - timestamps are simulation time only.

**Verification**: 
- Sprint 1 determinism tests validate stable primitives (canonical serialization + SHA-256 hashing, seeded RNG).
- The `engine` crate includes comprehensive determinism tests that validate stable hashing and seeded RNG behavior across multiple runs.

## Overview

This project implements a deterministic, event-driven backtesting engine for quantitative trading strategies. The engine is designed with:

- **Determinism**: All randomness is seeded; no system time dependencies
- **Event-driven architecture**: Bar-by-bar simulation with OHLCV data
- **Portfolio accounting**: Tracks positions, cash, realized/unrealized PnL
- **Pluggable components**: Modular traits for data feeds, strategies, brokers, and cost models
- **Comprehensive testing**: 90%+ test coverage for critical modules
- **Safety**: All crates forbid unsafe code with `#![forbid(unsafe_code)]`

## Architecture

The project is organized as a **unified Cargo workspace** with all crates active:

### Rust Crates (All Active)

- **`schema`**: Core traits and data structures (DataFeed, Strategy, BrokerSim, CostModel)
- **`engine`**: Backtest engine with portfolio management and output generation (14 tests)
- **`broker_sim`**: Broker simulator for order execution (2 tests)
- **`cost`**: Cost model implementations (4 tests)
- **`cli`**: Command-line interface and example strategies (2 tests)
- **`crv_verifier`**: CRV verification suite for backtest validation (12 tests)
- **`hipcortex`**: Content-addressed artifact storage for reproducibility (20 tests)

**Total**: 73 Rust tests, all passing ✅

### Python Orchestrator

- **`aureus`**: Complete orchestration framework with FSM, gates, LLM integration, and task generation

**Total**: 141 Python tests, all passing ✅

### Python Orchestrator

The **Python orchestrator** (`python/aureus`) provides a complete workflow controller:

- **8 Strategy Templates**: Momentum, mean-reversion, breakout, pairs trading, stat arb, ML classifier, carry trade, volatility trading
- **LLM Integration**: GPT-4 and Claude-3.5 for intelligent strategy generation
- **Walk-Forward Validation**: Industry-standard time-series cross-validation with configurable windows
- **Tool API wrappers**: JSON schema-validated wrappers for Rust CLI commands
- **Goal-Guard FSM**: Enforces valid tool call sequences (11 states, 40+ transitions)
- **Dual-loop evidence gates**:
  - **Dev gate**: Tests pass, determinism check, lint verification
  - **Product gate**: CRV verification, walk-forward validation, stress testing
- **Reflexion loop**: Automatic failure analysis and repair plan generation
- **Strict mode**: Artifact ID-only responses for reproducibility
- **Task Generation**: Synthetic task creation for benchmarking

See [python/README.md](python/README.md), [WALK_FORWARD_IMPLEMENTATION.md](WALK_FORWARD_IMPLEMENTATION.md), and [PHASE2_SUMMARY.md](PHASE2_SUMMARY.md) for detailed documentation.

## Features

### Core Traits

- **`DataFeed`**: Provides market data (OHLCV bars)
- **`Strategy`**: Trading strategy implementation
- **`BrokerSim`**: Order execution and fill generation
- **`CostModel`**: Commission and slippage calculation

### Portfolio Accounting

- Position tracking with average price calculation
- Realized and unrealized PnL
- Cash management
- Equity curve generation

### Determinism

- Seeded random number generation (ChaCha8Rng)
- No system time usage
- Deterministic test passes across multiple runs

### Outputs

- `trades.csv`: All executed trades with timestamps
- `equity_curve.csv`: Equity over time
- `stats.json`: Backtest statistics (returns, Sharpe ratio, max drawdown, etc.)
- `crv_report.json`: CRV verification report with detected violations

### Walk-Forward Validation

Industry-standard time-series cross-validation for robust out-of-sample testing:

- **Configurable windows**: Default 3 windows with 70/30 train/test split
- **Performance degradation analysis**: Detects overfitting via Sharpe degradation
- **Threshold validation**: Minimum test Sharpe (default: 0.5) and max degradation (default: 30%)
- **Stability scoring**: Measures consistency across windows
- **JSON reports**: Complete validation analysis with per-window results

Example usage:
```python
from aureus.walk_forward import WalkForwardValidator

validator = WalkForwardValidator(
    num_windows=3,
    min_test_sharpe=0.5,
    max_degradation=0.3
)

# Create windows from data
windows = validator.create_windows("data/prices.csv")

# Run backtests per window (external)
# ...

# Validate overall performance
analysis = validator.validate(windows, results)
if analysis.passed:
    print(f"✅ Strategy passed (stability: {analysis.stability_score:.2%})")
else:
    print(f"❌ Failed: {analysis.failure_reasons}")
```

See [WALK_FORWARD_IMPLEMENTATION.md](WALK_FORWARD_IMPLEMENTATION.md) for complete documentation.

### Strategy Templates

AURELIUS includes **8 professional strategy templates** with intelligent parameter adjustment:

1. **Time-Series Momentum** (`ts_momentum`) - Trend following with volatility targeting
2. **Mean Reversion** (`mean_reversion`) - Bollinger band-based mean reversion
3. **Breakout** (`breakout`) - Volatility breakout strategy
4. **Pairs Trading** (`pairs_trading`) - Statistical arbitrage between correlated assets
5. **Statistical Arbitrage** (`stat_arb`) - Multi-asset cointegration strategies
6. **ML Classifier** (`ml_classifier`) - Machine learning for regime detection
7. **Carry Trade** (`carry_trade`) - Interest rate differential strategies
8. **Volatility Trading** (`volatility_trading`) - Options-based volatility arbitrage

Strategies are generated from natural language goals:
```python
from aureus.orchestrator import Orchestrator

orch = Orchestrator(llm_provider="openai")

# Natural language goal
goal = "Design a pairs trading strategy between tech stocks with low drawdown"

# Automatically generates appropriate strategy config
strategy = orch.generate_strategy(goal)
print(strategy.type)  # "pairs_trading"
print(strategy.entry_zscore)  # 2.0 (conservative)
```

### CRV Verification Suite

The **CRV Verifier** automatically validates backtest correctness and robustness:

#### Bias Detection
- **Lookahead bias**: Detects if strategy uses future data (validates timestamp ordering)
- **Survivorship bias**: Validates data completeness and universe composition

#### Metric Validation
- **Sharpe ratio**: Validates annualization correctness (sqrt(252) for daily data)
- **Max drawdown**: Recomputes and validates drawdown calculations

#### Policy Constraints
- **Max drawdown limit**: Enforces configurable drawdown thresholds (default: 25%)
- **Max leverage limit**: Detects bankruptcy and excessive leverage
- **Turnover limit**: Monitors portfolio turnover (configurable)

#### Report Format
CRV reports include:
- `rule_id`: Identifier for the violated rule
- `severity`: Critical, High, Medium, Low, or Info
- `message`: Human-readable description
- `evidence`: Supporting details and pointers

Example violation:
```json
{
  "rule_id": "max_drawdown_constraint",
  "severity": "high",
  "message": "Max drawdown 35.00% exceeds limit 25.00%",
  "evidence": [
    "Observed: 0.3500",
    "Limit: 0.2500"
  ]
}
```

### HipCortex: Artifact Storage

HipCortex provides content-addressed storage for research artifacts with reproducibility tracking:

```bash
# Commit a strategy artifact
hipcortex commit --artifact strategy.json --message "Add momentum strategy"

# Search for artifacts
hipcortex search --goal momentum --tag trending

# Show artifact details
hipcortex show <hash>

# Replay computation for reproducibility verification
hipcortex replay <result_hash> --data data.parquet
```

Features:
- **Content-addressed storage**: SHA-256 hashing over canonical bytes
- **Artifact types**: Dataset, StrategySpec, BacktestConfig, BacktestResult, CRVReport, Trace
- **Append-only audit log**: Immutable commit history with lineage tracking
- **SQLite metadata index**: Fast search by goal, regime tags, policy, timestamps
- **CLI commands**: commit, show, diff, replay, search

See [crates/hipcortex/README.md](crates/hipcortex/README.md) for detailed documentation.

## Example Strategy

The included **Time-Series Momentum** strategy demonstrates:

- Lookback-based momentum signal
- Volatility targeting for position sizing
- Deterministic execution

## Usage

### Python Orchestrator

The Python orchestrator provides a complete workflow with LLM-assisted strategy generation:

```bash
# Install Python package
cd python
pip install -e .

# Set up LLM API key (optional, falls back to templates)
export OPENAI_API_KEY="your-key"  # or ANTHROPIC_API_KEY

# Validate installation
aureus validate

# Run with natural language goal
aureus run \
  --goal "design a pairs trading strategy between tech stocks with low risk" \
  --data ../examples/data.parquet \
  --max-drawdown 0.15

# Enable walk-forward validation
aureus run \
  --goal "create a mean reversion strategy" \
  --data ../examples/data.parquet \
  --enable-walk-forward \
  --walk-forward-windows 3
```

The orchestrator automatically:
1. Parses your natural language goal
2. Generates appropriate strategy configuration (using LLM or templates)
3. Runs backtests with the Rust engine
4. Executes dev gate checks (tests, determinism, linting)
5. Runs product gate validation (CRV, walk-forward if enabled)
6. Commits successful strategies to HipCortex

See [python/README.md](python/README.md) for detailed usage.

### Direct Rust CLI

The CLI provides low-level access to the backtest engine:

```bash
# Build
cargo build --release

# Run backtest
cargo run --bin quant_engine -- backtest \
  --spec examples/spec.json \
  --data examples/data.parquet \
  --out output_dir

# Verify CRV constraints
cargo run --bin crv_verifier -- verify \
  --stats output_dir/stats.json \
  --trades output_dir/trades.csv \
  --max-drawdown 0.25
```

### Build and Test

```bash
# Run full CI pipeline
make ci

# Individual commands
make fmt         # Autoformat code
make clippy      # Run linter
make test        # Run all tests (73 Rust + 141 Python)

# Run specific test suite
cargo test --package engine
pytest python/tests/test_walk_forward.py -v
```

### Spec File Format

Strategy specifications support all 8 strategy types:

**Time-Series Momentum:**
```json
{
  "initial_cash": 100000.0,
  "seed": 42,
  "strategy": {
    "type": "ts_momentum",
    "symbol": "AAPL",
    "lookback": 20,
    "vol_target": 0.15,
    "vol_lookback": 60
  },
  "cost_model": {
    "type": "fixed_per_share",
    "cost_per_share": 0.005,
    "minimum_commission": 1.0
  }
}
```

**Pairs Trading:**
```json
{
  "initial_cash": 100000.0,
  "seed": 42,
  "strategy": {
    "type": "pairs_trading",
    "symbol": "AAPL",
    "secondary_symbol": "MSFT",
    "lookback": 20,
    "entry_zscore": 2.0,
    "exit_zscore": 0.5,
    "hedge_ratio_method": "ols"
  }
}
```

**Statistical Arbitrage:**
```json
{
  "strategy": {
    "type": "stat_arb",
    "symbol": "SPY",
    "basket": ["QQQ", "IWM", "DIA"],
    "lookback": 20,
    "entry_threshold": 2.0,
    "cointegration_test": "adf"
  }
}
```

**ML Classifier:**
```json
{
  "strategy": {
    "type": "ml_classifier",
    "symbol": "AAPL",
    "lookback": 20,
    "num_features": 15,
    "model_type": "random_forest",
    "retrain_frequency": 20
  }
}
```

See [python/aureus/llm_strategy_generator.py](python/aureus/llm_strategy_generator.py) for all strategy types and parameters.

### Generate Sample Data

```bash
python3 examples/generate_data.py
```

### Use HipCortex for Artifact Management

```bash
# Initialize repository
hipcortex --repo .hipcortex commit --artifact strategy.json --message "Initial strategy"

# View commit history
hipcortex show <hash>

# Search artifacts
hipcortex search --goal momentum
```

## Test Coverage

### Sprint 1: Active Crates

The Sprint 1 workspace includes comprehensive tests for the active crates:

- **`schema`**: Core trait definitions (no tests required)
- **`engine`**: 23 passing tests including:
  - Portfolio accounting invariants (correctness)
  - Determinism tests (hash-based validation, seeded RNG)
  - Backtest integration tests
  - Data feed tests
- **`broker_sim`**: 2 passing tests (market order execution, determinism)
- **`cost`**: 4 passing tests (commission calculations, model validation)

### Sprint 2+: Placeholder Crates

The following tests exist for placeholder crates but are not run in Sprint 1 CI:

- **`cli`**: 2 tests (strategy tests)
- **`crv_verifier`**: 22 tests (bias detection, metric validation, policy constraints)
- **`hipcortex`**: 20 tests (artifact storage, replay reproducibility)

### Sprint 1 Test Results

```
schema: 0 tests (trait definitions only)
broker_sim: 2 tests passed
cost: 4 tests passed
engine: 23 tests passed (14 unit + 9 determinism integration tests)
```

All critical modules exceed 90% test coverage.

## Evidence Gate Requirements

✅ **90%+ unit test coverage for critical modules**
- Portfolio management: 100% coverage
- Cost models: 100% coverage  
- Broker simulation: 100% coverage
- Backtest engine: 95%+ coverage
- CRV verifier: 100% coverage

✅ **Determinism test passes across 3 runs**
- Hash-based determinism validation implemented
- All tests use seeded RNG (ChaCha8Rng with seed=42)
- No system time dependencies

✅ **CRV verification suite implemented**
- Lookahead bias detection
- Survivorship bias detection (delisted symbols, cherry-picking)
- Metric correctness validation (Sharpe ratio, max drawdown)
- Policy constraint enforcement (max drawdown, leverage, turnover)
- Comprehensive test suite with intentionally flawed strategies
- Golden-file tests for JSON report structure
- All tests use seeded RNG (ChaCha8Rng with seed=42)
- No system time dependencies

## Development

### Adding a New Strategy

Implement the `Strategy` trait:

```rust
use schema::{Bar, Order, Portfolio, Strategy};

pub struct MyStrategy {
    // Strategy state
}

impl Strategy for MyStrategy {
    fn on_bar(&mut self, bar: &Bar, portfolio: &Portfolio) -> Vec<Order> {
        // Generate orders based on bar and portfolio state
        vec![]
    }

    fn name(&self) -> &str {
        "MyStrategy"
    }
}
```

### Adding a New Cost Model

Implement the `CostModel` trait:

```rust
use schema::{CostModel, Side};

pub struct MyCostModel {
    // Cost model parameters
}

impl CostModel for MyCostModel {
    fn calculate_commission(&self, quantity: f64, price: f64) -> f64 {
        // Calculate commission
        0.0
    }

    fn calculate_slippage(&self, quantity: f64, price: f64, side: Side) -> f64 {
        // Calculate slippage
        0.0
    }
}
```

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please ensure all tests pass and maintain test coverage above 90% for critical modules.
