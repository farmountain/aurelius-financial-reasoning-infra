## Purpose

Define API schema-to-client contract guarantees, drift detection, and compatibility requirements.

## Requirements

### Requirement: API schema SHALL be source of truth for clients
The backend API schema SHALL be the authoritative contract for client integrations, and dashboard client bindings SHALL be generated or validated against that schema.

#### Scenario: Client contract generation succeeds
- **WHEN** the API schema is updated
- **THEN** the client contract artifacts are regenerated or validated before merge

#### Scenario: Contract drift is detected
- **WHEN** dashboard route or payload expectations differ from API schema
- **THEN** CI fails and blocks release until parity is restored

#### Scenario: Websocket contract drift is detected
- **WHEN** frontend websocket envelope/event expectations differ from backend websocket contract
- **THEN** CI fails and blocks release until websocket parity is restored

### Requirement: Backward compatibility policy SHALL be explicit
Breaking API contract changes SHALL include explicit migration notes and versioning strategy before release.

#### Scenario: Breaking change introduced
- **WHEN** a route path, response field, or request schema changes incompatibly
- **THEN** the release process requires migration documentation and versioned rollout decision

#### Scenario: Feature surface is exposed without backend support
- **WHEN** a dashboard feature is shipped with actionable controls but missing backend contract support
- **THEN** release gating marks the feature as unsupported and blocks production maturity claims for that surface
