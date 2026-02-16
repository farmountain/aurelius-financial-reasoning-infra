## MODIFIED Requirements

### Requirement: Product documentation SHALL reflect implemented behavior
Public README/API/dashboard documentation SHALL accurately represent what is implemented, unavailable, or experimental and SHALL document scorecard formulas, thresholds, and blocker precedence used in product decisions.

#### Scenario: Feature status is changed in product surface
- **WHEN** a feature transitions between unsupported, experimental, validated, or production
- **THEN** relevant docs are updated in the same release scope

#### Scenario: CI doc consistency check runs
- **WHEN** release validation runs
- **THEN** claims that conflict with known implementation status are flagged for correction

#### Scenario: API examples are malformed or non-executable
- **WHEN** documentation checks parse API README request/response examples
- **THEN** malformed JSON blocks or prose embedded inside example payloads are flagged and corrected before release

#### Scenario: Scorecard semantics drift from implementation
- **WHEN** scorecard weights, thresholds, or blocker rules change
- **THEN** docs updates are required in the same release scope and drift checks fail if omitted

### Requirement: Capability maturity labels SHALL be visible to users
User-facing product surfaces SHALL expose maturity labels consistent with release-gate evidence.

#### Scenario: User inspects feature status
- **WHEN** user views a feature or workflow status in dashboard/API metadata
- **THEN** maturity label shown matches current release-gate evidence

#### Scenario: User inspects promotion readiness details
- **WHEN** user views readiness output for a strategy
- **THEN** maturity label and decision band are shown together with blocker/action explanations
