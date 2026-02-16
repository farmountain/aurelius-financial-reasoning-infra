## MODIFIED Requirements

### Requirement: Websocket message envelope SHALL be contract-consistent
Backend websocket messages and frontend websocket consumers SHALL use one canonical envelope shape and field names.

#### Scenario: Backend emits subscribed event
- **WHEN** backend broadcasts an event to websocket clients
- **THEN** message payload matches the documented envelope contract used by frontend listeners

#### Scenario: Frontend subscribes to event stream
- **WHEN** frontend subscribes to a supported event type
- **THEN** incoming events are routed to the correct listener without schema translation ambiguity

#### Scenario: Default event names are canonical
- **WHEN** backend connection manager emits fallback/default event names
- **THEN** those names MUST be part of the canonical supported event taxonomy

### Requirement: Event taxonomy SHALL be explicit and testable
Supported websocket event names SHALL be documented and validated in contract tests.

#### Scenario: Contract test validates websocket events
- **WHEN** CI runs websocket contract checks
- **THEN** mismatched event names or message fields fail the build

#### Scenario: Realtime hooks are actively consumed
- **WHEN** the dashboard claims realtime updates for a surface
- **THEN** at least one active UI path subscribes to and renders the corresponding canonical websocket events

### Requirement: Authentication lifecycle SHALL preserve websocket continuity
Websocket connectivity SHALL remain aligned with the current auth token state after login, logout, or token refresh.

#### Scenario: Token changes after app bootstrap
- **WHEN** auth token changes during an active browser session
- **THEN** websocket connection state updates to use the new token and reconnect behavior remains deterministic
