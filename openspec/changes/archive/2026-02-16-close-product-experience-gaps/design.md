## Context

AURELIUS now has strong deterministic backend truth-path controls for backtests/validation/gates, but user-facing product surfaces still contain prototype behavior (unsupported APIs for Reflexion/Orchestrator, synthetic/random dashboard inputs, websocket envelope/event mismatch, and stale docs). This creates a product trust gap: users can complete some workflows with high confidence while adjacent workflows behave as placeholders.

Constraints:
- Preserve deterministic behavior and audit lineage guarantees.
- Avoid regressing existing API contracts while introducing missing workflow endpoints.
- Ensure dashboard/backends/websocket contracts remain synchronized and CI-enforced.
- Keep rollout safe via maturity labels and explicit unsupported states where needed.

Stakeholders:
- Quant users (workflow continuity and realistic analytics)
- Product/PM (feature claim integrity)
- Platform engineering (contract stability and maintainability)
- Governance/compliance (traceability and replay integrity)

## Goals / Non-Goals

**Goals:**
- Close end-to-end gaps for Reflexion and Orchestrator product surfaces.
- Unify websocket envelope and event taxonomy between backend and frontend.
- Replace synthetic advanced-page data generation with user/artifact-backed inputs.
- Improve strategy generation behavior to avoid static synthetic ranking/mocked semantics.
- Enforce docs and capability labels to match actual implementation/maturity.

**Non-Goals:**
- Building full autonomous strategy discovery research stack in this change.
- Replacing the deterministic core engine architecture.
- Delivering full multi-tenant permissions model.
- Expanding to live broker execution/OMS in this phase.

## Decisions

### 1) Product-surface closure before new feature expansion
Decision: Prioritize making currently exposed surfaces executable (Reflexion/Orchestrator/Advanced) before adding new visible surfaces.

Rationale:
- Reduces expectation mismatch and user distrust faster than adding breadth.
- Improves commercial readiness by stabilizing the existing journey.

Alternatives considered:
- Hide unsupported pages (rejected as partial fix; avoids but does not resolve capability debt).

### 2) Single websocket contract and taxonomy
Decision: Define one canonical websocket message envelope and event dictionary consumed by both backend and dashboard, with CI contract tests.

Rationale:
- Removes silent runtime failures caused by shape/name drift.
- Enables deterministic integration behavior under realtime updates.

Alternatives considered:
- Adapter translations in frontend only (rejected: shifts complexity and masks backend drift).

### 3) Artifact-backed analytics inputs
Decision: Advanced dashboard actions must send user-provided or stored artifact inputs; random client-side data generation is limited to explicit demo/dev mode.

Rationale:
- Preserves analytical integrity and repeatability.
- Prevents misleading outputs that look authoritative but are synthetic.

Alternatives considered:
- Keep random fallback in production (rejected: undermines trust and governance positioning).

### 4) Strategy generation fidelity hardening
Decision: Replace static-list strategy generation behavior with goal/risk-conditioned generation semantics and measurable generation metadata.

Rationale:
- Aligns feature claims with user expectations of intelligent generation.
- Improves output relevance and reduces perception of hardcoded behavior.

Alternatives considered:
- Keep static templates and relabel as examples (rejected for primary path; can remain as explicit fallback mode).

### 5) Documentation as release-gated artifact
Decision: Treat key docs (root README, API README, dashboard README) as release artifacts validated against implementation status/maturity labels.

Rationale:
- Prevents commercial and onboarding friction from stale claims.
- Tightens PM/engineering alignment for externally visible statements.

Alternatives considered:
- Manual docs updates without checks (rejected: repeatedly regresses).

## Risks / Trade-offs

- [Integration complexity across UI/API/websocket] → Mitigation: staged rollout and contract tests at each layer.
- [Temporary velocity slowdown due to closure work] → Mitigation: prioritize by high user-impact surfaces first.
- [Backward compatibility concerns for websocket consumers] → Mitigation: temporary compatibility shim + deprecation window.
- [Overfitting strategy generation to narrow templates] → Mitigation: explicit evaluation criteria and configurable generation backends.
- [Docs check false positives] → Mitigation: maintain allowlist/annotations for known experimental surfaces.

## Migration Plan

1. Define canonical websocket contract (envelope + event list) and add CI validation.
2. Implement backend endpoints/services for Reflexion and Orchestrator minimal executable workflows.
3. Update dashboard services/pages to use real endpoints and explicit unsupported badges only where intentionally scoped.
4. Replace advanced-page random data paths with user/artifact input forms and backend-coupled execution.
5. Harden strategy generation path and remove mock timing semantics from primary response.
6. Update README/API/dashboard documentation and add doc-consistency checks.
7. Run end-to-end acceptance across strategy -> backtest -> validation -> gate -> orchestrator/reflexion visibility.

Rollback strategy:
- Feature-flag new product-surface routes and websocket schema versioning.
- Revert dashboard to stable contract adapters while preserving persisted artifacts and run records.

## Open Questions

- Should websocket envelope migration be versioned (`v1`/`v2`) or in-place with compatibility shim?
- What minimal Reflexion/Orchestrator semantics are required for first production maturity label?
- Should strategy generation expose confidence calibration diagnostics to users?
- Which docs should be strict-gated in CI vs advisory-only in early rollout?