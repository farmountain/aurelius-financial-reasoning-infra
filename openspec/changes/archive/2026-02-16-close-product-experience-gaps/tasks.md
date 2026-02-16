## 1. Reflexion and Orchestrator Backend Closure

- [x] 1.1 Implement backend Reflexion routes and persistence-backed history retrieval used by dashboard.
- [x] 1.2 Implement backend Orchestrator routes for run creation, stage transitions, and status polling.
- [x] 1.3 Wire dashboard API service methods to real Reflexion/Orchestrator endpoints and remove unsupported placeholders.
- [x] 1.4 Add minimal integration tests for Reflexion and Orchestrator happy-path and failure-path responses.

## 2. Websocket Contract Consistency

- [x] 2.1 Define canonical websocket envelope fields and supported event names in shared contract docs.
- [x] 2.2 Align backend websocket emitter payload shape and event taxonomy to canonical contract.
- [x] 2.3 Align frontend websocket context/hooks parsing and subscription keys to canonical contract.
- [x] 2.4 Add CI websocket contract tests that fail on envelope/event drift.

## 3. Advanced UX Data Integrity

- [x] 3.1 Replace client-side random input generation in Advanced Features page with user-entered or artifact-selected inputs.
- [x] 3.2 Add validation UX for required advanced analytics inputs and clear empty/error states.
- [x] 3.3 Ensure advanced requests call backend endpoints with deterministic payload semantics.
- [x] 3.4 Add UI tests to verify advanced workflows no longer rely on random synthetic data in production mode.

## 4. Strategy Generation Fidelity

- [x] 4.1 Refactor strategy generation to avoid fixed static strategy list behavior as primary output path.
- [x] 4.2 Remove mock generation timing semantics and return measurable generation metadata.
- [x] 4.3 Add quality checks ensuring generated strategies vary with goal/risk inputs.
- [x] 4.4 Add regression tests for deterministic and explainable strategy-generation outputs.

## 5. Runtime Input and Governance Enhancements

- [x] 5.1 Add explicit optional seed and data-source input handling for engine-backed runs with safe defaults.
- [x] 5.2 Persist seed/data-source selections into run identity/provenance for replay and audit.
- [x] 5.3 Expose execution metadata in relevant status endpoints and dashboard views.
- [x] 5.4 Add parity/replay tests covering custom seed/data-source combinations.

## 6. Documentation and Product Claim Alignment

- [x] 6.1 Update root README capability claims to reflect actual supported, experimental, and unsupported surfaces.
- [x] 6.2 Update API and dashboard READMEs to remove stale implementation-status sections and align endpoint behavior.
- [x] 6.3 Add docs consistency check in CI for key capability/maturity claim files.
- [x] 6.4 Execute end-to-end acceptance run covering strategy -> backtest -> validation -> gates -> reflexion/orchestrator visibility and record evidence.
