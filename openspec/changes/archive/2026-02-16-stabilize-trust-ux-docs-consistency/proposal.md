## Why

AURELIUS has a strong deterministic core, but reliability signals, dashboard UX behavior, and documentation claims are still inconsistent in ways that reduce user trust. This change is needed now to align operational reality, user-visible workflows, and product messaging before further feature expansion.

## What Changes

- Eliminate trust-breaking reliability issues in API startup/health and database optimization boot paths.
- Close high-friction UX gaps in Orchestrator, Reflexion, Dashboard metrics, and WebSocket lifecycle behavior.
- Enforce one canonical realtime contract from backend emitters to frontend subscribers and remove orphaned/unconsumed realtime pathways.
- Align auth requirements across related execution/status routes where the current model is inconsistent.
- Remove documentation contradictions and stale guidance that conflict with current implementation and maturity state.
- Add dependency and UI stack consistency checks for dashboard runtime stability.

## Capabilities

### New Capabilities
- `startup-operational-reliability`: API startup, health checks, and DB optimization routines are schema-aware, resilient, and low-noise under expected deployment modes.
- `dashboard-ux-flow-integrity`: User flows are executable from clean-state UX without hidden prerequisites or misleading placeholders.

### Modified Capabilities
- `product-surface-completeness`: Add missing executable behavior for surfaced controls and remove empty-state dead ends.
- `websocket-contract-consistency`: Expand consistency to include canonical defaults, token lifecycle behavior, and active consumer usage.
- `documentation-reality-alignment`: Reconcile maturity/status claims and remove stale setup guidance that is no longer true.
- `api-contract-parity`: Align auth and endpoint behavior across related route families; prevent contract drift in examples and references.
- `runtime-truth-path`: Ensure live acceptance evidence and gate-path behavior are consistent with production-readiness claims.

## Impact

- API: startup lifecycle logging and health execution paths; database optimization/indexing module; auth dependencies on validation/gates route families.
- Dashboard: Orchestrator empty-state launch flow, Reflexion list accuracy, Dashboard gate metrics computation, WebSocket provider token lifecycle, realtime hook consumption.
- Docs: root status/summary documents, API README examples and deployment guidance, acceptance evidence interpretation notes.
- Tooling/CI: contract and docs consistency checks, dependency consistency checks for dashboard imports vs package manifests.
