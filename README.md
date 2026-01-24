# AURELIUS Quant Reasoning Model

An Evidence-Gated Intelligence Engine for Quant Reasoning - Event-Driven Backtest Engine in Rust

## Overview

This project implements a deterministic, event-driven backtesting engine for quantitative trading strategies. The engine is designed with:

- **Determinism**: All randomness is seeded; no system time dependencies
- **Event-driven architecture**: Bar-by-bar simulation with OHLCV data
- **Portfolio accounting**: Tracks positions, cash, realized/unrealized PnL
- **Pluggable components**: Modular traits for data feeds, strategies, brokers, and cost models
- **Comprehensive testing**: 90%+ test coverage for critical modules

## Architecture

The project is organized as a Cargo workspace with the following crates:

- **`schema`**: Core traits and data structures (DataFeed, Strategy, BrokerSim, CostModel)
- **`cost`**: Cost model implementations (fixed per share, percentage-based, zero cost)
- **`broker_sim`**: Broker simulator for order execution
- **`engine`**: Backtest engine with portfolio management and output generation
- **`crv_verifier`**: Correctness, Robustness, and Validation suite for backtest verification
- **`cli`**: Command-line interface and example strategies
- **`hipcortex`**: Content-addressed artifact storage for reproducibility and provenance tracking

### Python Orchestrator

The **Python orchestrator** (`python/aureus`) provides a high-level workflow controller:

- **Tool API wrappers**: JSON schema-validated wrappers for Rust CLI commands
- **Goal-Guard FSM**: Enforces valid tool call sequences (e.g., cannot run CRV before dev gate)
- **Dual-loop evidence gates**:
  - Dev gate: Tests pass, determinism check, lint
  - Product gate: CRV pass, walk-forward validation, stress testing
- **Reflexion loop**: Automatic failure analysis and repair plan generation
- **Strict mode**: Artifact ID-only responses for reproducibility

See [python/README.md](python/README.md) for detailed documentation.

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

### Python Orchestrator (Recommended)

The Python orchestrator provides a high-level interface with evidence gates:

```bash
# Install Python package
cd python
pip install -e .

# Validate installation
aureus validate

# Run a goal
aureus run --goal "design a trend strategy under DD<10%" --data ../examples/data.parquet
```

See [python/README.md](python/README.md) for more details.

### Direct Rust CLI

### Build

```bash
cargo build --release
```

### Run Tests

```bash
cargo test --all
```

### Run Backtest

```bash
cargo run --bin quant_engine -- backtest \
  --spec examples/spec.json \
  --data examples/data.parquet \
  --out output_dir
```

### Spec File Format

```json
{
  "initial_cash": 100000.0,
  "seed": 42,
  "strategy": {
    "type": "ts_momentum",
    "symbol": "AAPL",
    "lookback": 20,
    "vol_target": 0.15,
    "vol_lookback": 20
  },
  "cost_model": {
    "type": "fixed_per_share",
    "cost_per_share": 0.005,
    "minimum_commission": 1.0
  }
}
```

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

The project includes comprehensive tests:

- **Accounting invariants**: Ensures portfolio accounting correctness
- **Determinism tests**: Verifies reproducibility across runs (hash-based validation)
- **Cost model sanity tests**: Validates commission calculations
- **Strategy tests**: Tests strategy logic and determinism
- **Integration tests**: End-to-end backtest validation
- **CRV verification tests**: Tests bias detection, metric validation, and policy constraints
  - 12 unit tests for core verification logic
  - 7 flawed strategy tests (lookahead bias, excessive drawdown, bankruptcy, survivorship bias, etc.)
  - 3 golden-file tests for JSON report structure
- **HipCortex tests**: Artifact storage and reproducibility
  - 17 unit tests for storage, audit, and indexing
  - 3 integration tests for replay reproducibility

### Test Results

```
broker_sim: 2 tests passed
cost: 4 tests passed
engine: 11 tests passed
cli: 2 tests passed
crv_verifier: 22 tests passed (12 unit + 7 integration + 3 golden)
hipcortex: 20 tests passed (17 unit + 3 integration)
```
```
broker_sim: 2 tests passed
cost: 4 tests passed
engine: 11 tests passed
cli: 2 tests passed
crv_verifier: 22 tests passed (12 unit + 7 integration + 3 golden)
hipcortex: 20 tests passed (17 unit + 3 integration)
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
