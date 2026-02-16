## Purpose

Define capability maturity labels and measurable release-gate evidence criteria.

## Requirements

### Requirement: Capability maturity labels SHALL be enforced
Each externally exposed capability SHALL be labeled as `experimental`, `validated`, or `production` based on objective acceptance criteria.

#### Scenario: Capability promoted to production
- **WHEN** capability metrics meet all production thresholds
- **THEN** the capability label is updated to `production` and release notes include evidence summary

#### Scenario: Capability below threshold
- **WHEN** quality thresholds are not met
- **THEN** capability remains `experimental` or `validated` and cannot be advertised as production-ready

### Requirement: Release gating SHALL use measurable quality checks
Release decisions SHALL reference measurable checks including truth parity, determinism pass rate, contract parity, and lineage completeness.

#### Scenario: Release gate evaluation
- **WHEN** a release candidate is evaluated
- **THEN** the gate decision is derived from defined metrics and recorded with pass/fail rationale
