## Purpose

Define documentation-to-implementation consistency and maturity-label visibility requirements.

## Requirements

### Requirement: Product documentation SHALL reflect implemented behavior
Public README/API/dashboard documentation SHALL accurately represent what is implemented, unavailable, or experimental.

#### Scenario: Feature status is changed in product surface
- **WHEN** a feature transitions between unsupported, experimental, validated, or production
- **THEN** relevant docs are updated in the same release scope

#### Scenario: CI doc consistency check runs
- **WHEN** release validation runs
- **THEN** claims that conflict with known implementation status are flagged for correction

### Requirement: Capability maturity labels SHALL be visible to users
User-facing product surfaces SHALL expose maturity labels consistent with release-gate evidence.

#### Scenario: User inspects feature status
- **WHEN** user views a feature or workflow status in dashboard/API metadata
- **THEN** maturity label shown matches current release-gate evidence
