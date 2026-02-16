## Purpose

Define the canonical market event envelope, typed payloads, and deterministic replay ordering semantics.

## Requirements

### Requirement: Canonical event envelope
The system SHALL represent all ingested market data using a canonical event envelope that includes event type, symbol, event time, source identifier, and payload.

#### Scenario: Envelope validation on ingest
- **WHEN** an adapter emits an event into the market data bus
- **THEN** the bus MUST reject events missing required envelope fields

### Requirement: Typed event payloads across fidelity tiers
The system SHALL support typed payload variants for bar, trade, quote, order-book update, options chain snapshot, and fundamentals/macro snapshot events.

#### Scenario: Tier-compatible event acceptance
- **WHEN** a dataset is declared as Tier 1 (bar-level)
- **THEN** only bar payloads SHALL be required and accepted as sufficient for Tier 1 validation

#### Scenario: Tier 3 data requirement
- **WHEN** a dataset is declared as Tier 3 (order-book-level)
- **THEN** order-book payloads MUST be present and validated against tier rules

### Requirement: Deterministic event ordering for replay
The system SHALL define deterministic ordering semantics for canonical events within a dataset replay.

#### Scenario: Reproducible replay sequence
- **WHEN** the same canonical dataset is replayed multiple times with the same seed and configuration
- **THEN** the emitted event sequence order MUST be identical across runs
