## ADDED Requirements

### Requirement: Websocket message envelope SHALL be contract-consistent
Backend websocket messages and frontend websocket consumers SHALL use one canonical envelope shape and field names.

#### Scenario: Backend emits subscribed event
- **WHEN** backend broadcasts an event to websocket clients
- **THEN** message payload matches the documented envelope contract used by frontend listeners

#### Scenario: Frontend subscribes to event stream
- **WHEN** frontend subscribes to a supported event type
- **THEN** incoming events are routed to the correct listener without schema translation ambiguity

### Requirement: Event taxonomy SHALL be explicit and testable
Supported websocket event names SHALL be documented and validated in contract tests.

#### Scenario: Contract test validates websocket events
- **WHEN** CI runs websocket contract checks
- **THEN** mismatched event names or message fields fail the build
