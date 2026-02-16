## 1. Startup and Operational Reliability Hardening

- [x] 1.1 Update API health check DB liveness execution to SQLAlchemy-compatible query patterns and structured degraded reporting.
- [x] 1.2 Remove startup logging/health behaviors that emit misleading success signals during dependency failure.
- [x] 1.3 Refactor database optimization index statements to match current schema objects and skip missing objects safely.
- [x] 1.4 Add tests for startup degraded-mode behavior, health endpoint correctness, and schema-aware index verification.

## 2. Product UX Flow Integrity Fixes

- [x] 2.1 Refactor Orchestrator empty-state flow to support first-run launch without depending on existing runs list strategy IDs.
- [x] 2.2 Add strategy selection/generation affordance for Orchestrator start action when run history is empty.
- [x] 2.3 Correct Reflexion list metrics to show per-strategy iteration counts instead of selected-strategy count reuse.
- [x] 2.4 Replace Dashboard gate metric placeholders with computed values sourced from backend gate status data.

## 3. WebSocket Contract and Realtime Consumption Alignment

- [x] 3.1 Align backend WebSocket manager default/fallback event names to canonical supported event taxonomy.
- [x] 3.2 Update frontend realtime subscriptions and message routing to consume canonical event names only.
- [x] 3.3 Make WebSocket provider token lifecycle reactive to login/logout/token refresh changes.
- [x] 3.4 Ensure claimed realtime features are actually consumed in active UI surfaces and add regression coverage.

## 4. API Contract and Auth Consistency

- [x] 4.1 Define and implement explicit auth policy alignment for related run/status/gate endpoint families.
- [x] 4.2 Update validation and gate routes (and associated dependencies) to match selected auth policy consistently.
- [x] 4.3 Add API contract checks preventing route-family auth drift and invalid doc example fields.
- [x] 4.4 Add/update integration tests for consistent auth behavior across backtest, validation, and gate workflows.

## 5. Documentation Reality Alignment

- [x] 5.1 Reconcile contradictory project maturity/completion claims across trust-critical status documents.
- [x] 5.2 Correct stale API README guidance that implies missing PostgreSQL/JWT features and invalid strategy_id example mapping.
- [x] 5.3 Add docs consistency checks for trust-critical files and maturity claims tied to release evidence.
- [x] 5.4 Update release-facing messaging to classify implemented vs experimental surfaces consistently.

## 6. Dependency and Acceptance Evidence Integrity

- [x] 6.1 Reconcile dashboard dependency manifest with imported UI stack modules and enforce dependency consistency checks.
- [x] 6.2 Re-run live acceptance flow for strategy -> backtest -> validation -> gates -> reflexion -> orchestrator after fixes.
- [x] 6.3 Record refreshed acceptance evidence with explicit gate endpoint outcomes and environment context.
- [x] 6.4 Validate change readiness by running targeted tests and contract/doc checks before apply execution.
