## 1. Acceptance Evidence Quality Closure

- [x] 1.1 Re-run live acceptance flow in a known-good environment and capture environment metadata.
- [x] 1.2 Ensure dev/CRV/product gate endpoint outcomes are contract-valid in the refreshed evidence block.
- [x] 1.3 Annotate or supersede older failing evidence entries so release interpretation is unambiguous.

## 2. Documentation Executability and Maturity Alignment

- [x] 2.1 Fix malformed strategy generation response example in `api/README.md` and move policy prose outside JSON blocks.
- [x] 2.2 Update trust-critical wording in `CURRENT_STATUS.md` to prevent over-strong maturity interpretation.
- [x] 2.3 Update trust-critical wording in `PROJECT_COMPLETE.md` to preserve snapshot context with evidence-gated caveats.
- [x] 2.4 Extend docs checks to catch malformed API example payloads and trust-critical claim drift.

## 3. Orchestrator First-Run UX Integrity

- [x] 3.1 Remove `runs[0]?.strategy_id` fallback from Orchestrator start logic.
- [x] 3.2 Confirm empty-state start path works using only selected or generated strategies.
- [x] 3.3 Add/adjust regression coverage to prevent run-history coupling from reappearing.

## 4. Runtime Truth-Path and Release Guardrails

- [x] 4.1 Add/update checks asserting acceptance evidence reflects current gate-path behavior with explicit environment caveats.
- [x] 4.2 Run targeted contract/docs/UX tests after fixes and record output as implementation evidence.
- [x] 4.3 Verify OpenSpec change readiness with `openspec validate close-verified-trust-evidence-gaps --type change` before apply.
