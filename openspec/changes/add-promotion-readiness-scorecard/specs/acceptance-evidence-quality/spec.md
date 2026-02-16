## MODIFIED Requirements

### Requirement: Release-facing acceptance evidence SHALL be current and environment-explicit
Release-facing acceptance evidence artifacts SHALL include recent run timestamps, execution environment context, and a clear interpretation of outcome class.

#### Scenario: Acceptance evidence entry is recorded
- **WHEN** a live acceptance run is appended to the evidence artifact
- **THEN** the entry includes timestamp, environment fields, and endpoint outcome summary

#### Scenario: Stale evidence is detected
- **WHEN** release validation finds no recent acceptance entry for the current change window
- **THEN** release validation fails and requests a refreshed acceptance run

#### Scenario: Evidence freshness contributes to operational confidence
- **WHEN** readiness scoring consumes evidence quality inputs
- **THEN** stale or missing evidence reduces operational confidence component with explicit penalty reason

### Requirement: Gate-path outcomes SHALL be classified for trust interpretation
Acceptance evidence SHALL classify gate-path outcomes as contract-valid success, contract-valid failure, or contract-invalid failure.

#### Scenario: Gate endpoint returns contract-valid failure
- **WHEN** gate endpoints return valid HTTP responses with explicit failure semantics due to business data conditions
- **THEN** evidence marks the outcome as contract-valid failure and includes rationale context

#### Scenario: Gate endpoint returns contract-invalid failure
- **WHEN** gate endpoints return route-not-found or internal errors in the acceptance path
- **THEN** release validation marks evidence as blocking until corrected or superseded by a clean run

#### Scenario: Evidence interpretation is surfaced to operators
- **WHEN** users inspect promotion readiness details
- **THEN** the system exposes environment caveats and gate-path classification used in readiness interpretation
