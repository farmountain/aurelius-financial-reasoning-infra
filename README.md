# AURELIUS Quant Reasoning Model Trading Platform

AURELIUS is a quantitative research and strategy-evaluation platform that combines:
- A deterministic Rust backtesting engine
- A Python orchestration layer for strategy lifecycle and validation
- A REST API and React dashboard for team workflows
- Reproducibility tooling for auditability and governance

It is designed for researchers, engineers, and decision makers who need transparent, testable, and production-oriented quant workflows.

---

## Table of Contents

- [Why AURELIUS](#why-aurelius)
- [Core Capabilities](#core-capabilities)
- [Architecture](#architecture)
- [Repository Layout](#repository-layout)
- [Quick Start](#quick-start)
- [Backtesting with Alpaca Data](#backtesting-with-alpaca-data)
- [API and Dashboard](#api-and-dashboard)
- [Validation and Governance](#validation-and-governance)
- [Performance and Reliability](#performance-and-reliability)
- [Roadmap and Documentation](#roadmap-and-documentation)
- [Contributing](#contributing)
- [License](#license)
- [Contributors](#contributors)

---

## Why AURELIUS

Most strategy pipelines fail because they are hard to reproduce, difficult to validate out-of-sample, and disconnected from operational controls.

AURELIUS addresses that with:
- Deterministic simulation primitives
- Structured strategy generation and evaluation
- Walk-forward validation and gate-based quality checks
- API-first workflows for integration into internal tooling

---

## Core Capabilities

### 1) Strategy Research and Backtesting
- Event-driven OHLCV backtesting in Rust
- Modular interfaces for data feeds, brokers, and cost models
- Strategy templates and extensible strategy definitions
- Trade logs, equity curves, and summary metrics output

### 2) Validation and Robustness
- Walk-forward validation for out-of-sample testing
- CRV verification for bias and metric sanity checks
- Policy constraints (drawdown, leverage, turnover)
- Evidence-driven pass/fail gates for deployment readiness

### 3) Advanced Quant Tooling
- Portfolio optimization (max Sharpe, min variance, risk parity)
- Efficient frontier calculations
- Risk analytics (VaR/CVaR, drawdowns, Sharpe/Sortino/Calmar)
- ML-based parameter optimization (Optuna-driven workflows)
- Position sizing and risk management modules

### 4) Product Surface
- REST API for strategy lifecycle and backtest operations
- React dashboard for monitoring and control
- WebSocket support for real-time updates with canonical envelope/events
- Reflexion iteration history and run endpoints
- Orchestrator persisted pipeline runs and stage transitions
- PostgreSQL persistence and Redis caching support

---

## Architecture

### Rust Workspace (Core Engine)
- `schema`: Core traits and canonical data structures
- `engine`: Deterministic backtest engine and portfolio accounting
- `broker_sim`: Simulated order execution
- `cost`: Commission/slippage cost models
- `cli`: Command-line workflows and sample strategies
- `crv_verifier`: Verification and policy rule engine
- `hipcortex`: Content-addressed artifact and reproducibility support

### Python Layer
- Orchestration workflows
- Walk-forward validation tooling
- Strategy generation helpers
- Task/gate automation

### Service Layer
- FastAPI-based backend in [api/README.md](api/README.md)
- React/Vite dashboard in [dashboard/README.md](dashboard/README.md)

---

## Repository Layout

- [crates](crates) — Rust crates (engine, simulation, verifier, CLI)
- [python](python) — Python orchestration and examples
- [api](api) — REST API service and backend integrations
- [dashboard](dashboard) — Web dashboard
- [examples](examples) — Sample scripts and data workflows
- [docs](docs) — Design and rollout documentation
- [data](data) — Data artifacts and samples
- [specs](specs) — Specifications

---

## Quick Start

### Prerequisites
- Rust 1.70+
- Python 3.9+
- Node.js 18+
- Docker (optional, for full stack)

### 1) Clone and build core

```bash
cargo build --workspace
cargo test --workspace
```

### 2) Python environment (optional but recommended)

```bash
cd python
pip install -e .
```

### 3) Run API (local)

See [api/README.md](api/README.md) for full setup.

### 4) Run Dashboard (local)

See [dashboard/README.md](dashboard/README.md) for local frontend setup.

### 5) One-command checks

```bash
make ci
```

---

## Backtesting with Alpaca Data

A practical script is available at [examples/backtest_sp500_weekly_5pct_alpaca.py](examples/backtest_sp500_weekly_5pct_alpaca.py).

It supports:
- S&P 500 universe proxy data collection via Alpaca
- Reusable local CSV/Parquet input mode
- Weekly threshold strategy variants (`trend_5`, `mr_ladder_5_10`)

Required environment variables:
- `APCA_API_KEY_ID`
- `APCA_API_SECRET_KEY`

Example:

```bash
python examples/backtest_sp500_weekly_5pct_alpaca.py \
  --symbols-limit 500 \
  --feed iex \
  --start 2025-02-15T00:00:00Z \
  --end 2026-02-15T00:00:00Z
```

---

## API and Dashboard

### Capability Maturity Labels (Release-Facing)

- `validated`: Strategy generation, backtests, validation, gates, Reflexion, Orchestrator, auth-protected workflow APIs, and canonical WebSocket contract.
- `experimental`: Advanced analytics surfaces whose operational readiness is environment-dependent.
- `historical snapshot`: Phase completion reports that describe milestone delivery but do not override current evidence-gated release status.

### Promotion Readiness Scorecard (Decision Contract)

Promotion readiness is represented as a canonical scorecard:

$S = w_1 D + w_2 R + w_3 P + w_4 O + w_5 U$

Expanded with default v1 weights:

$S = 0.25D + 0.20R + 0.25P + 0.15O + 0.15U$

Where each component is normalized to `[0,100]`:
- `D`: Determinism/Parity confidence
- `R`: Risk/Validation confidence
- `P`: Policy/Governance compliance
- `O`: Operational reliability
- `U`: User interpretability/decision clarity

Default weight profile (`v1`):
- `w1=0.25`, `w2=0.20`, `w3=0.25`, `w4=0.15`, `w5=0.15`

Decision bands:
- `Green`: `S >= 85` and no hard blockers
- `Amber`: `70 <= S < 85` and no hard blockers
- `Red`: `S < 70` or any hard blocker

Hard blockers are non-compensatory (for example missing run identity, parity failure, lineage/policy blockers): a strategy cannot be promoted even with a high weighted score.

### API Highlights
- Strategy generation and listing
- Backtest execution and status (with optional deterministic `seed` and `data_source` inputs)
- Validation and gate endpoints
- Reflexion and orchestrator workflow endpoints
- Authentication and authorization support

Reference: [api/README.md](api/README.md)

### Dashboard Highlights
- Strategy and backtest monitoring
- Gate status visibility
- Real-time updates via WebSocket
- Portfolio/risk tooling pages

Reference: [dashboard/README.md](dashboard/README.md)

---

## Validation and Governance

AURELIUS includes governance-oriented checks:
- Determinism checks for reproducible results
- CRV policy verification and violation reporting
- Walk-forward robustness checks before progression
- Artifact traceability for audits and post-mortem analysis

Relevant docs:
- [WALK_FORWARD_IMPLEMENTATION.md](WALK_FORWARD_IMPLEMENTATION.md)
- [LLM_STRATEGY_GENERATION.md](LLM_STRATEGY_GENERATION.md)
- [TASK_GENERATOR_IMPLEMENTATION.md](TASK_GENERATOR_IMPLEMENTATION.md)

---

## Performance and Reliability

Project includes documented efforts on:
- API caching and query optimization
- Indexing and data access performance
- Load and integration testing
- Containerized deployment and Kubernetes manifests

See:
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- [DATABASE_SETUP.md](DATABASE_SETUP.md)
- [docker-compose.yml](docker-compose.yml)
- [k8s/deployment.yml](k8s/deployment.yml)

---

## Roadmap and Documentation

For status and historical implementation details:
- [CURRENT_STATUS.md](CURRENT_STATUS.md)
- [DEVELOPMENT_ROADMAP.md](DEVELOPMENT_ROADMAP.md)
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- [FINAL_SUMMARY.md](FINAL_SUMMARY.md)

---

## Contributing

Contributions are welcome.

Please read:
- [CONTRIBUTING.md](CONTRIBUTING.md)

Recommended contributor workflow:
1. Create a branch
2. Add tests for behavior changes
3. Run `make ci`
4. Open a pull request with clear scope and validation evidence

---

## License

This repository is licensed under the terms in [LICENSE](LICENSE).

---

## Contributors

See the repository contributor history and activity in GitHub Insights.

If you are using AURELIUS internally, consider maintaining an internal changelog of strategy/policy decisions for governance traceability.
