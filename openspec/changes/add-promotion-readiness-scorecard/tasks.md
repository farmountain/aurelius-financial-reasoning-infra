## 1. Scorecard Domain and Policy Definition

- [x] 1.1 Define scorecard domain model for components (`D`,`R`,`P`,`O`,`U`), weighted total `S`, decision band, and hard blockers.
- [x] 1.2 Implement configurable default weight profile and threshold policy (`Green/Amber/Red`) with versioned metadata.
- [x] 1.3 Implement penalty-first normalization rules with explicit data-quality warning fields.
- [x] 1.4 Implement hard-blocker override logic so blocker state supersedes weighted band outcomes.

## 2. Readiness Signal Integration

- [x] 2.1 Map parity/run-identity/determinism signals into scorecard `D` component inputs.
- [x] 2.2 Map validation/CRV/risk completeness signals into `R` component inputs.
- [x] 2.3 Map policy/lineage/governance block reasons into `P` component inputs.
- [x] 2.4 Map startup/dependency health and evidence freshness/environment-classification signals into `O` and `U` component inputs.

## 3. Canonical API Contract Alignment

- [x] 3.1 Add canonical readiness payload schema that includes component scores, total score, decision band, hard blockers, top blockers, and actions.
- [x] 3.2 Extend gate/release status APIs to return canonical readiness payload alongside compatibility fields.
- [x] 3.3 Add transition context fields indicating which components changed between evaluations.
- [x] 3.4 Add API contract tests to ensure readiness payload shape remains stable.

## 4. Dashboard Decision UX Unification

- [x] 4.1 Update gate/dashboard data adapters to consume canonical readiness payload without schema-shape inference.
- [x] 4.2 Add compact promotion-readiness panel (score, band, blockers, recommended actions) to primary decision surfaces.
- [x] 4.3 Display maturity label consistently with decision band and blocker explanations.
- [x] 4.4 Add UI regression tests for readiness rendering, blocker priority ordering, and fallback behavior.

## 5. Runtime Reliability and Evidence Interpretation

- [x] 5.1 Integrate startup/dependency degraded-state reasons into readiness operational confidence computation.
- [x] 5.2 Add evidence freshness checks and environment caveat interpretation used by readiness scoring.
- [x] 5.3 Ensure contract-valid vs contract-invalid gate-path outcomes are represented in operator-facing explanations.

## 6. Documentation, KPI Instrumentation, and Validation

- [x] 6.1 Update README/API/dashboard docs with score formula, default weights, threshold bands, and hard-blocker precedence.
- [x] 6.2 Add/extend docs-consistency checks to detect scorecard semantic drift against implementation.
- [x] 6.3 Define and emit KPI events for decision latency, false-promotion proxy, reproducibility pass rate, and onboarding reliability.
- [x] 6.4 Run targeted test suites (score logic, API contract, dashboard UX, docs consistency) and record evidence for apply verification.