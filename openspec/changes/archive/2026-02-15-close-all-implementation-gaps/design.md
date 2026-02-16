## Context

AURELIUS already has deterministic computation and CRV verification in the Rust CLI path, but several service-layer routes still generate mocked/randomized outputs. This creates claim-vs-runtime divergence, weakens dashboard trust, and blocks enterprise-grade validation workflows. The change must unify API, dashboard, and orchestrator onto one deterministic execution truth path while preserving backward compatibility and controlled rollout.

Key constraints:
- Deterministic behavior is mandatory for production-grade outputs.
- Existing users must not lose baseline functionality during migration.
- API contracts and dashboard client calls must remain compatible or migrate with explicit versioning.
- Governance artifacts must support replay and audit from a single run identity.

Stakeholders:
- Quant researchers (execution correctness)
- Platform engineering (maintainability and performance)
- Product management (feature truth and release confidence)
- Risk/compliance users (auditability)

## Goals / Non-Goals

**Goals:**
- Replace mocked/randomized production API execution paths with real engine-backed execution.
- Guarantee CLI/API/dashboard metric parity for equivalent run inputs.
- Introduce contract integrity controls to prevent frontend/backend drift.
- Establish reproducible lineage and policy evidence requirements for promoted results.
- Introduce capability maturity gates tied to measurable acceptance criteria.

**Non-Goals:**
- Building live execution routing or OMS features.
- Rewriting all strategy templates at once.
- Eliminating experimental modes for local development (only preventing them from masquerading as production outputs).
- Re-architecting storage engines outside lineage and parity requirements.

## Decisions

### 1) Single truth execution plane
Decision: Route all production backtest/validation/gate outcomes through deterministic engine-backed execution, with route-level mock paths removed or explicitly marked non-production.

Rationale:
- Prevents inconsistent metrics between interfaces.
- Preserves a single source of computational truth for governance.

Alternatives considered:
- Keep mixed mock/real route behavior with labels (rejected: high accidental misuse risk).

### 2) Canonical run identity for parity and replay
Decision: Define run identity as `{spec_hash, data_hash, seed, engine_version}` and require this identity on all persisted result artifacts.

Rationale:
- Makes parity checks objective and replayable.
- Enables audit workflows and deterministic regression checks.

Alternatives considered:
- Timestamp-only run IDs (rejected: insufficient for reproducibility).

### 3) Contract parity via schema-driven client generation
Decision: Treat backend OpenAPI as source of truth and enforce generated client parity plus CI contract checks.

Rationale:
- Eliminates endpoint drift between dashboard and API.
- Reduces integration defects caused by manual client updates.

Alternatives considered:
- Manual endpoint synchronization (rejected: recurring drift).

### 4) Governance-first promotion flow
Decision: Require lineage completeness and policy gate evidence before any run is marked production-ready.

Rationale:
- Aligns product claims with measurable controls.
- Supports internal and external audit requirements.

Alternatives considered:
- Optional lineage fields (rejected: weakens trust and compliance posture).

### 5) Capability maturity release model
Decision: Label capabilities as `experimental`, `validated`, or `production` based on objective quality thresholds.

Rationale:
- Prevents overclaiming.
- Helps PM and GTM align messaging with runtime truth.

Alternatives considered:
- Binary enabled/disabled labeling (rejected: lacks nuance for staged rollout).

## Risks / Trade-offs

- [Integration latency increase after truth-path routing] → Mitigation: cache immutable artifacts by canonical run identity.
- [Migration regressions in existing API consumers] → Mitigation: contract tests, compatibility shims, and staged rollout flags.
- [Data insufficiency for full walk-forward execution] → Mitigation: minimum data sufficiency checks and explicit rejection reasons.
- [Operational confusion around capability tiers] → Mitigation: expose maturity status in API metadata and release notes.
- [Performance cost for parity validation] → Mitigation: limit full parity checks to CI/nightly plus sampled production verification.

## Migration Plan

1. Define canonical run identity and parity acceptance thresholds.
2. Replace production mock execution with engine-backed service adapter paths.
3. Implement API contract generation and CI parity checks for dashboard client.
4. Enforce lineage and policy evidence persistence for promoted runs.
5. Roll out capability maturity labels and release gating checks.
6. Enable staged rollout flags for controlled transition and observability.

Rollback strategy:
- Keep previous route behavior behind controlled fallback flags during rollout.
- If severe regression appears, rollback to last validated version while preserving run artifacts for diagnosis.

## Open Questions

- What exact parity tolerances are acceptable per metric (absolute vs relative) across API/CLI/dashboard?
- Should non-production mock mode remain available in a separate namespace or behind explicit environment gates only?
- Which governance evidence fields are mandatory for first enterprise-facing release vs deferred?
- What CI budget is acceptable for full parity matrix checks across strategies/data tiers?
