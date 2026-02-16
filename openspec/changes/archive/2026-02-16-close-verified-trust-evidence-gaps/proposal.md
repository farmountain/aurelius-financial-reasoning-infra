## Why

Recent verification identified remaining trust gaps between implementation, acceptance evidence, and release-facing documentation. These gaps block confident production-readiness messaging and should be closed before further expansion.

## What Changes

- Refresh live acceptance evidence with a clean, current run where gate-path behavior is contract-valid and environment context is explicit.
- Fix API README executable example issues (malformed strategy generation response block and misplaced policy prose).
- Remove residual Orchestrator first-run fallback coupling to run history (`runs[0]?.strategy_id`) so first-run flow depends only on selected/generated strategies.
- Tighten trust-critical status wording in historical snapshot docs to avoid overstating current release maturity.
- Keep existing route-family auth and websocket contract behavior intact while adding regression checks for newly fixed gaps.

## Capabilities

### New Capabilities
- `acceptance-evidence-quality`: Define and enforce quality expectations for release-facing acceptance evidence (freshness, contract-valid outcomes, explicit environment classification).

### Modified Capabilities
- `documentation-reality-alignment`: Correct executable API examples and tighten maturity wording consistency in trust-critical docs.
- `product-surface-completeness`: Remove hidden first-run dependency on run history in Orchestrator launch logic.
- `runtime-truth-path`: Require acceptance evidence updates to reflect current gate-path behavior and environment caveats.

## Impact

- Affects release evidence artifact maintenance in `docs/ACCEPTANCE_EVIDENCE_CLOSE_PRODUCT_EXPERIENCE_GAPS.md`.
- Affects API documentation quality in `api/README.md`.
- Affects first-run Orchestrator UX logic in `dashboard/src/pages/Orchestrator.jsx`.
- Affects trust-critical messaging in `CURRENT_STATUS.md` and `PROJECT_COMPLETE.md`.
- Adds/updates tests and checks that guard against recurrence of these specific verification findings.
