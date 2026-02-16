## 1. Runtime Truth Path Integration

- [x] 1.1 Replace mocked/randomized execution in backtests API route with deterministic engine-backed execution.
- [x] 1.2 Replace mocked/randomized execution in validation API route with real window-based execution results.
- [x] 1.3 Replace mocked gate checks with artifact-derived gate decisions from real run outputs.
- [x] 1.4 Replace advanced optimization mock backtest callback with real backtest execution adapter.
- [x] 1.5 Add canonical run identity (`spec_hash`, `data_hash`, `seed`, `engine_version`) to all persisted run outputs.

## 2. Parity and Verification Controls

- [x] 2.1 Define metric parity tolerances for CLI vs API outputs and codify in test configuration.
- [x] 2.2 Implement parity validation tests for equivalent run identity across CLI and API.
- [x] 2.3 Block production promotion when parity checks fail and record violation evidence.
- [x] 2.4 Add deterministic replay checks for promoted runs using canonical run identity.

## 3. API Contract Parity

- [x] 3.1 Generate or validate dashboard API client bindings from backend OpenAPI schema.
- [x] 3.2 Resolve known route and payload mismatches between dashboard services and backend routers.
- [x] 3.3 Add CI contract drift checks that fail on incompatible route/schema divergence.
- [x] 3.4 Define and document backward compatibility policy for breaking API changes.

## 4. Decision Lineage and Governance

- [x] 4.1 Define required lineage fields for promotion (run identity, provenance, transforms, policy outcomes, artifact links).
- [x] 4.2 Enforce lineage completeness checks before promotion is allowed.
- [x] 4.3 Implement audit replay endpoint/workflow that reconstructs decision evidence from a single run identity.
- [x] 4.4 Add governance report artifact summarizing policy pass/fail rationale for promoted runs.

## 5. Capability Maturity and Release Gating

- [x] 5.1 Define objective thresholds for `experimental`, `validated`, and `production` capability labels.
- [x] 5.2 Add release gate evaluation step based on truth parity, determinism, contract parity, and lineage completeness.
- [x] 5.3 Persist release gate decisions with measurable pass/fail evidence.
- [x] 5.4 Update release documentation to ensure external claims align with achieved capability maturity.

## 6. Rollout and Safety Controls

- [x] 6.1 Add staged rollout flags to enable controlled migration from mock paths to truth paths.
- [x] 6.2 Define rollback procedure and trigger conditions for regressions in parity or latency.
- [x] 6.3 Add observability for route execution mode, parity status, and promotion-block reasons.
- [x] 6.4 Execute end-to-end acceptance run (`generate -> backtest -> validation -> gates -> promotion`) before declaring apply-ready.
