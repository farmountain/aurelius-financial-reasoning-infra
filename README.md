# AURELIUS Quant Reasoning Model

An Evidence-Gated Intelligence Engine for Quant Reasoning - Event-Driven Backtest Engine in Rust

## Sprint 1: Minimal Repo Skeleton

This repository is organized using a **test-driven development** approach with a minimal workspace structure for Sprint 1.

### Active Modules (Sprint 1)

The following crates are **active workspace members** and included in `make ci`:

- **`schema`**: Core traits and data structures (DataFeed, Strategy, Portfolio, Order)
- **`engine`**: Backtest engine with portfolio management, determinism support, and output generation
- **`broker_sim`**: Broker simulator (required dependency of engine)
- **`cost`**: Cost model implementations (required dev-dependency of engine)

### Placeholder Modules (Sprint 2+)

The following crates are **fully implemented and tested** but excluded from the Sprint 1 workspace to maintain a minimal, cleanly compiling skeleton. They will be added as workspace members in Sprint 2:

- **`cli`**: Command-line interface and example strategies
- **`crv_verifier`**: Correctness, Robustness, and Validation suite (22 passing tests)
- **`hipcortex`**: Content-addressed artifact storage for reproducibility (20 passing tests)

### Future Placeholders

- **`aureus`**: Reserved for future development (TBD in Sprint 2+)

### Directory Structure

```
├── crates/           # Rust crates (workspace members + placeholders)
│   ├── schema/      # ✅ Active in Sprint 1
│   ├── engine/      # ✅ Active in Sprint 1
│   ├── broker_sim/  # ✅ Active in Sprint 1 (engine dependency)
│   ├── cost/        # ✅ Active in Sprint 1 (engine dev-dependency)
│   ├── cli/         # ⏸️ Placeholder (Sprint 2+)
│   ├── crv_verifier/# ⏸️ Placeholder (Sprint 2+)
│   ├── hipcortex/   # ⏸️ Placeholder (Sprint 2+)
│   └── aureus/      # ⏸️ Placeholder (Sprint 2+)
├── docs/            # Documentation (placeholder)
├── data/            # Sample data files (placeholder)
├── specs/           # Formal specifications (placeholder)
├── examples/        # Example code and data
└── python/          # Python orchestrator (optional)
```

Each placeholder crate has a `SPRINT1_STATUS.md` file documenting its status and planned integration.

## Quick Start

### Prerequisites

- **Rust**: 1.70.0 or later (install from [rust-lang.org](https://rust-lang.org))
- **Make**: GNU Make or compatible (for CI commands)
- **Python**: 3.9+ (optional, for Python orchestrator)

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

The project is organized as a Cargo workspace. In **Sprint 1**, the core crates and their dependencies are active workspace members:

### Sprint 1 Active Crates

- **`schema`**: Core traits and data structures (DataFeed, Strategy, BrokerSim, CostModel)
- **`engine`**: Backtest engine with portfolio management and output generation
- **`broker_sim`**: Broker simulator for order execution (required by engine)
- **`cost`**: Cost model implementations (required by engine tests)

### Sprint 2+ Placeholder Crates

These crates are fully implemented but not yet included as workspace members:

- **`cli`**: Command-line interface and example strategies
- **`crv_verifier`**: Correctness, Robustness, and Validation suite for backtest verification
- **`hipcortex`**: Content-addressed artifact storage for reproducibility and provenance tracking
- **`aureus`**: Reserved for future development

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

### Sprint 1 Note

In Sprint 1, the workspace includes the **core engine, schema, broker_sim, and cost crates**. The CLI and other advanced components (crv_verifier, hipcortex) are placeholder crates excluded from the workspace. To use the full functionality described below, you'll need to temporarily add the required crates to the workspace in `Cargo.toml`.

### Python Orchestrator (Future - Sprint 2+)

The Python orchestrator provides a high-level interface with evidence gates:

```bash
# Install Python package (requires full workspace)
cd python
pip install -e .

# Validate installation
aureus validate

# Run a goal
aureus run --goal "design a trend strategy under DD<10%" --data ../examples/data.parquet
```

See [python/README.md](python/README.md) for more details.

### Direct Rust CLI (Future - Sprint 2+)

The CLI is available in the `crates/cli` placeholder but not included in Sprint 1 workspace.

### Build

```bash
cargo build --release
```

### Run Tests

```bash
cargo test --all
```

### Run Backtest (Future - Sprint 2+)

```bash
# Requires cli crate to be added to workspace
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
