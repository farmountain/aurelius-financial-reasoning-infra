## MODIFIED Requirements

### Requirement: Product documentation SHALL reflect implemented behavior
Public README/API/dashboard documentation SHALL accurately represent what is implemented, unavailable, or experimental.

#### Scenario: Feature status is changed in product surface
- **WHEN** a feature transitions between unsupported, experimental, validated, or production
- **THEN** relevant docs are updated in the same release scope

#### Scenario: CI doc consistency check runs
- **WHEN** release validation runs
- **THEN** claims that conflict with known implementation status are flagged for correction

#### Scenario: Contradictory maturity summaries exist
- **WHEN** project status documents contain conflicting maturity or completion claims
- **THEN** release validation flags the conflict and requires aligned wording before promotion

### Requirement: Capability maturity labels SHALL be visible to users
User-facing product surfaces SHALL expose maturity labels consistent with release-gate evidence.

#### Scenario: User inspects feature status
- **WHEN** user views a feature or workflow status in dashboard/API metadata
- **THEN** maturity label shown matches current release-gate evidence

### Requirement: Setup and API examples SHALL remain executable
Published setup guidance and code examples SHALL reflect currently supported architecture and parameter contracts.

#### Scenario: API README guidance is validated
- **WHEN** documentation checks run for API examples
- **THEN** deprecated guidance and invalid field mappings are flagged and corrected before release
