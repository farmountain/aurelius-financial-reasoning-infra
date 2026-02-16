## Context

AURELIUS now includes deterministic runtime execution and expanded product surfaces, but production trust is reduced by cross-layer inconsistency: startup reliability noise, acceptance evidence gaps, UX dead-ends, websocket contract drift in defaults and consumers, and contradictory maturity claims in documentation. The requested scope is cross-cutting across API lifecycle, dashboard UX, auth semantics, docs governance, and CI guardrails.

Constraints:
- Preserve deterministic and lineage-backed execution guarantees.
- Minimize API breaking changes while fixing route-family consistency.
- Keep websocket schema canonical and backwards-safe during migration.
- Deliver measurable evidence improvements, not only static policy updates.

Stakeholders:
- Quant users who rely on reproducible, executable end-to-end workflows.
- Platform engineering responsible for uptime and operational diagnostics.
- PM/release owners who need claim-to-runtime alignment.
- Governance/compliance stakeholders using evidence artifacts for promotion trust.

## Goals / Non-Goals

**Goals:**
- Harden startup/health/indexing behavior so operational state is accurate and low-noise.
- Remove first-run and list-level UX defects in Orchestrator, Reflexion, and Dashboard gate summaries.
- Align websocket default events, consumer subscriptions, and token lifecycle behavior with canonical contract.
- Normalize auth expectations in related run/status/gate route families.
- Align major status docs and API examples with current implementation and release maturity.
- Add CI checks that prevent recurrence of drift in docs, contracts, and dependencies.

**Non-Goals:**
- Introduce new trading or execution algorithms.
- Re-architect websocket transport protocol.
- Redesign full dashboard information architecture.
- Perform broad historical documentation rewrite beyond trust-critical files.

## Decisions

### Decision 1: Treat reliability, UX, and documentation as one release quality surface
Decision: Implement one integrated change rather than separate isolated fixes.

Rationale:
- Trust breaks when any one surface contradicts another.
- A single quality gate can validate startup health, UX executability, contract coherence, and docs claims together.

Alternatives considered:
- Split into multiple small changes (rejected due to likely sequencing gaps and prolonged inconsistency windows).

### Decision 2: Make startup lifecycle schema-aware and dependency-explicit
Decision: Health and index routines validate runtime schema/dependency context before executing optional checks.

Rationale:
- Prevents false positives and transaction-poisoning startup behavior.
- Enables deterministic degraded-mode reporting.

Alternatives considered:
- Keep best-effort execution with warning logs only (rejected: repeatedly noisy and ambiguous for operators).

### Decision 3: Enforce canonical websocket behavior end-to-end
Decision: Canonical event list governs manager defaults, frontend subscriptions, and consumer usage checks.

Rationale:
- Eliminates silent drift where defaults use non-canonical event names.
- Ensures realtime claims correspond to active UI consumers.

Alternatives considered:
- Keep compatibility aliases indefinitely (rejected: perpetuates hidden divergence).

### Decision 4: Align route-family auth policy explicitly
Decision: Run/status/gate endpoints in one workflow family must share explicit auth policy, documented and test-validated.

Rationale:
- Reduces security ambiguity and integration surprises.
- Supports predictable dashboard behavior and contract parity.

Alternatives considered:
- Leave mixed auth based on historical implementation (rejected: high support and security review friction).

### Decision 5: Use evidence-driven docs governance
Decision: Promote docs from informational artifacts to release-gated assertions for trust-critical files.

Rationale:
- Prevents “production-ready” overclaims when acceptance artifacts indicate failures.
- Keeps README examples executable against current schemas.

Alternatives considered:
- Manual periodic docs cleanup (rejected: prone to drift recurrence).

## Risks / Trade-offs

- [Auth policy tightening may impact existing consumers] → Mitigation: clearly documented migration notice and compatibility grace period where needed.
- [Websocket event normalization may break hidden listeners] → Mitigation: add temporary compatibility mapping with deprecation timeline and contract tests.
- [Operational checks may be perceived as stricter/failing more often initially] → Mitigation: distinguish degraded vs failed states with structured reason codes.
- [Cross-cutting scope increases implementation complexity] → Mitigation: phase work by risk order (reliability, then UX, then contract/docs guardrails).
- [Docs gate false positives] → Mitigation: limit strict checks to trust-critical files and known claim markers.

## Migration Plan

1. Reliability baseline
   - Fix health execution patterns and startup dependency reporting.
   - Make DB optimization/index routines schema-aware and transaction-safe.
2. UX flow integrity
   - Remove Orchestrator clean-state dependency on existing runs.
   - Correct Reflexion per-strategy counters and Dashboard gate summary computation.
3. Realtime contract integrity
   - Align manager defaults and hook subscriptions to canonical websocket events.
   - Ensure token lifecycle updates websocket session continuity.
4. Auth consistency
   - Apply and test explicit route-family auth policy across run/status/gate endpoints.
5. Documentation and CI guardrails
   - Resolve maturity/status contradictions and stale API examples.
   - Add CI checks for docs-contract-dependency consistency.
6. Acceptance evidence refresh
   - Re-run end-to-end acceptance and update evidence artifact for release gating.

Rollback strategy:
- Feature flag or compatibility shim for websocket event normalization.
- Revert auth enforcement changes behind explicit route-family toggles if emergency client breakage appears.
- Keep prior docs snapshots and restore if CI-gate logic requires recalibration.

## Open Questions

- Should route-family auth consistency enforce strict auth on all validation/gate status paths, or allow specific read-only exceptions?
- Should websocket compatibility aliases remain for one release or two?
- Which trust-critical docs should be hard-gated vs advisory in CI?
- Should acceptance evidence require a passing CRV/product gate in all environments, or allow environment-classified exceptions?
