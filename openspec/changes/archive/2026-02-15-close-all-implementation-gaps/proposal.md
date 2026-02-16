## Why

AURELIUS has a strong deterministic Rust core, but several user-facing API routes still rely on mocked/randomized outputs. This creates a trust gap between platform claims and runtime behavior, blocks enterprise adoption, and causes product contract drift between backend and dashboard.

## What Changes

- Replace mocked/randomized API execution paths with deterministic engine-backed execution for backtests, validation, gates, and optimization workflows.
- Introduce API-to-engine truth-parity guarantees so the same spec/data/seed produce consistent metrics across CLI, API, and dashboard.
- Establish strict contract parity between backend OpenAPI and frontend service calls with compatibility checks in CI.
- Add lineage and governance requirements so every promoted result is reproducible and auditable from a single run identity.
- Define commercial-readiness maturity gates (`experimental`, `validated`, `production`) tied to measurable acceptance criteria.

## Capabilities

### New Capabilities
- `runtime-truth-path`: Engine-backed execution requirements for all production backtest/validation/gate flows.
- `api-contract-parity`: Contract synchronization and compatibility guarantees between API schemas and dashboard clients.
- `decision-lineage-governance`: Required lineage, reproducibility, and policy evidence for promoted strategy decisions.
- `release-maturity-gates`: Capability maturity labels and release gating rules linked to objective quality metrics.

### Modified Capabilities
- None.

## Impact

- Affects API routers for backtests, validation, gates, and advanced optimization.
- Affects Python orchestration/gate behavior and artifact generation.
- Affects dashboard API client routes and response contract assumptions.
- Adds CI requirements for contract checks and parity validation.
- Strengthens governance outputs for audit, risk, and commercialization readiness.
