## Context

AURELIUS currently exposes strong execution, validation, and gate primitives, but promotion readiness is not represented as a canonical decision object across API and dashboard. Users can access raw gate outcomes and evidence artifacts, yet decision interpretation remains fragmented due to schema/UI mismatch and environment-dependent runtime signals.

This design introduces a promotion-readiness scorecard that unifies deterministic/parity, validation/risk, governance/policy, operational reliability, and UX interpretability signals into one operator-facing decision model. The design must preserve existing governance safeguards (hard blockers) while adding weighted score semantics and a stable contract for API and dashboard consumption.

## Goals / Non-Goals

**Goals:**
- Define a canonical score model `S = w1D + w2R + w3P + w4O + w5U` with component normalization to `[0,100]`.
- Preserve hard-blocker precedence so critical governance failures override weighted score bands.
- Define score component data contracts sourced from existing gate, runtime, and evidence pathways.
- Align API response schemas and dashboard rendering to a single readiness contract.
- Provide actionable UX output: score, decision band, top blockers, and recommended next actions.
- Establish KPI instrumentation definitions for decision quality and operating efficiency.

**Non-Goals:**
- Replacing existing gate computations (dev/CRV/product) with an entirely new gate engine.
- Introducing trading strategy algorithm changes.
- Reworking websocket protocol versions in this change.
- Solving all deployment environment variability across every host profile.

## Decisions

### Decision 1: Add scorecard as a compositional layer over existing controls
- The scorecard consumes existing outputs (gate status, parity/lineage/policy signals, runtime health, evidence freshness) rather than replacing upstream checks.
- Rationale: minimizes migration risk and preserves trust in proven components.
- Alternative considered: rewrite gate outputs into a single monolithic promotion endpoint (rejected due to high regression risk and reduced transparency).

### Decision 2: Hard blockers override weighted score bands
- Weighted score determines Green/Amber/Red only when no hard blockers are present.
- Hard blockers include missing run identity, parity failure, lineage incompleteness, and explicit policy block reasons.
- Rationale: governance safety should remain non-compensatory.
- Alternative considered: pure weighted model where strong signals can offset critical failures (rejected as unsafe for promotion decisions).

### Decision 3: Normalize all component scores to `[0,100]` with penalty-first v1
- Initial component scoring uses deterministic penalties from known failure conditions, then can evolve to statistical calibration later.
- Rationale: fast, explainable, and testable starting point.
- Alternative considered: direct ML or probabilistic readiness estimation in v1 (rejected due to explainability and validation burden).

### Decision 4: Publish a canonical readiness payload contract for product surfaces
- API provides a structured readiness payload including: component scores, weighted score, decision band, hard blockers, top blockers, and actions.
- Dashboard consumes the same payload without inferring nested/flattened compatibility workarounds.
- Rationale: removes current UI/API semantic drift.
- Alternative considered: dashboard-only transformation logic (rejected because it duplicates rules and causes contract drift).

### Decision 5: Operational reliability and evidence quality become first-class score inputs
- Runtime startup/dependency health and evidence freshness/environment classification contribute to `O` and `U` components.
- Rationale: promotion readiness should reflect real operating conditions, not only offline analytics.
- Alternative considered: keep ops/evidence signals as external notes (rejected because users need integrated decision clarity).

## Risks / Trade-offs

- [Score semantics may be perceived as arbitrary initially] → Mitigation: publish explicit formula, penalty rationale, and blocker precedence in docs + API metadata.
- [Contract migration could temporarily break dashboard compatibility] → Mitigation: support compatibility window and contract tests across API + dashboard.
- [Operational inputs may be noisy across environments] → Mitigation: classify environment context explicitly and document interpretation boundaries.
- [Too many blockers may produce persistent Red states] → Mitigation: rank blockers and provide concrete remediation actions to maintain operator momentum.
- [KPI instrumentation may add overhead] → Mitigation: phase instrumentation with lightweight event hooks first, then expand granularity.

## Migration Plan

1. Define canonical scorecard schema and component mapping.
2. Implement score computation over existing gate/runtime/evidence outputs.
3. Add API payload fields for weighted score, decision band, blockers, and actions.
4. Update dashboard summary/gate surfaces to consume canonical payload.
5. Update docs for formulas, thresholds, and interpretation rules.
6. Add regression/contract tests (score math, hard blocker override, API/UI compatibility).
7. Roll out with feature-flag or compatibility path where needed.
8. Validate KPI event emission for decision latency and false-promotion proxies.

Rollback strategy:
- Keep legacy `production_ready` and gate status behavior available during rollout.
- Revert scorecard presentation layer while preserving upstream gate logic if regressions occur.

## Open Questions

- Should component weights be globally fixed in v1 or tenant-configurable with policy constraints?
- What exact freshness window should define stale acceptance evidence for `O`/`U` penalties?
- Should maturity label be emitted only in readiness payload or also in dedicated metadata endpoints?
- How should local-dev degraded mode influence production decision views in multi-environment setups?
- What minimum KPI instrumentation set is required for meaningful commercial feedback in first release?