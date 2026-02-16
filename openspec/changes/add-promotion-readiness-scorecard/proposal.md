## Why

AURELIUS has strong execution and governance primitives, but promotion decisions are still hard for users to interpret quickly and confidently. We need a canonical promotion-readiness scorecard that converts raw gate/runtime/evidence signals into a decision-grade product surface.

## What Changes

- Introduce a weighted promotion-readiness scorecard (`S = w1D + w2R + w3P + w4O + w5U`) with configurable component weights and explicit hard-blocker rules.
- Define canonical scoring inputs from existing sources (gate status, parity/run identity, validation status, lineage/policy blocks, startup/dependency health, and evidence quality).
- Add decision band semantics (`Green`, `Amber`, `Red`) and “top blockers + next actions” output contract for operator UX.
- Align API and dashboard gate semantics to a single decision contract so UI does not infer incompatible response shapes.
- Add runtime-operability and evidence-freshness interpretation hooks so local/environment instability is represented explicitly in readiness output.
- Add KPI instrumentation definitions for decision latency, false-promotion rate, reproducibility pass rate, and onboarding reliability.

## Capabilities

### New Capabilities
- `promotion-readiness-scorecard`: Defines weighted decision scoring, hard blockers, decision bands, and operator-facing blocker/action narratives.

### Modified Capabilities
- `release-maturity-gates`: Extend release-gate semantics to consume scorecard outputs and maturity labels as first-class decision signals.
- `product-surface-completeness`: Align gate/status product surfaces to a canonical response contract used consistently by API and dashboard decision views.
- `runtime-truth-path`: Require operational dependency health and deterministic evidence signals to contribute to readiness scoring.
- `documentation-reality-alignment`: Require scorecard formulas, thresholds, and UX interpretation guidance to stay synchronized with implementation.
- `acceptance-evidence-quality`: Require evidence freshness and environment classification signals used by scorecard operational confidence.

## Impact

- API: gate/status and readiness-related schemas, scorecard computation surfaces, and readiness interpretation payloads.
- Dashboard: gate and summary panels to render readiness score, decision band, top blockers, and actionable next steps.
- Runtime/ops: startup/dependency health signals and evidence freshness interpretation integrated into promotion readiness.
- Documentation: product/readme and operational docs updated to reflect canonical scorecard semantics.
- Testing: contract tests, UX regression tests, score computation tests, and KPI/event instrumentation checks.