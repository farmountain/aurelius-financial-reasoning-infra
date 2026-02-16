## Why

The platform’s deterministic backend is substantially improved, but user-facing product workflows still have trust-breaking gaps (unsupported UI flows, websocket contract mismatch, synthetic UI data paths, and documentation drift). This change is needed now to align runtime truth, UX behavior, and product claims so users can reliably complete end-to-end strategy workflows.

## What Changes

- Implement real backend support for Reflexion and Orchestrator flows currently exposed in the dashboard.
- Standardize websocket message/event contracts between backend and frontend and enforce contract tests.
- Replace synthetic/random advanced dashboard demo inputs with user-provided or artifact-backed data pathways.
- Improve strategy generation fidelity (remove static-list behavior and mock timing semantics).
- Add configurable run inputs for seed/data selection while preserving deterministic defaults and auditability.
- Align API/dashboard documentation with actual implementation status and capability maturity labels.

## Capabilities

### New Capabilities
- `product-surface-completeness`: Ensure exposed UI surfaces (Reflexion/Orchestrator/Advanced workflows) have real backend routes and usable end-to-end behavior.
- `websocket-contract-consistency`: Define and enforce a single websocket message schema and event taxonomy across API and dashboard clients.
- `documentation-reality-alignment`: Keep README/API/Dashboard docs synchronized with implemented behavior and maturity claims.

### Modified Capabilities
- `runtime-truth-path`: Extend deterministic execution controls with explicit seed/data input handling and observable execution metadata.
- `api-contract-parity`: Expand parity checks to include websocket/event contracts and advanced workflow endpoint completeness.

## Impact

- Affects API routers and service layer for reflexion/orchestrator/strategy generation/advanced workflows.
- Affects dashboard API services, websocket context, and pages that currently use placeholders or synthetic data.
- Introduces contract test coverage for websocket payload shape and event naming.
- Updates public docs and capability labeling to match shipping behavior.
- Improves user trust, onboarding clarity, and commercial-readiness of the product surface.
