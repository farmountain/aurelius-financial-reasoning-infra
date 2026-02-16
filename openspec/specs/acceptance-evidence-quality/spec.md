## Purpose

Define quality standards for release-facing acceptance evidence so outcomes are current, environment-explicit, and interpretable for trust decisions.

## Requirements

### Requirement: Release-facing acceptance evidence SHALL be current and environment-explicit
Release-facing acceptance evidence artifacts SHALL include recent run timestamps, execution environment context, and a clear interpretation of outcome class.

#### Scenario: Acceptance evidence entry is recorded
- **WHEN** a live acceptance run is appended to the evidence artifact
- **THEN** the entry includes timestamp, environment fields, and endpoint outcome summary

#### Scenario: Stale evidence is detected
- **WHEN** release validation finds no recent acceptance entry for the current change window
- **THEN** release validation fails and requests a refreshed acceptance run

### Requirement: Gate-path outcomes SHALL be classified for trust interpretation
Acceptance evidence SHALL classify gate-path outcomes as contract-valid success, contract-valid failure, or contract-invalid failure.

#### Scenario: Gate endpoint returns contract-valid failure
- **WHEN** gate endpoints return valid HTTP responses with explicit failure semantics due to business data conditions
- **THEN** evidence marks the outcome as contract-valid failure and includes rationale context

#### Scenario: Gate endpoint returns contract-invalid failure
- **WHEN** gate endpoints return route-not-found or internal errors in the acceptance path
- **THEN** release validation marks evidence as blocking until corrected or superseded by a clean run
