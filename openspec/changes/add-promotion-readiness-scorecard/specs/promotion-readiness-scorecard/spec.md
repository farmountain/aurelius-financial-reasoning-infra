## ADDED Requirements

### Requirement: Promotion readiness SHALL be computed as a weighted scorecard
The system SHALL compute a promotion readiness score `S` as a weighted combination of normalized components (`D`, `R`, `P`, `O`, `U`) where each component is constrained to `[0,100]` and default weights are explicitly versioned.

#### Scenario: Score computed with default weights
- **WHEN** readiness is evaluated without tenant overrides
- **THEN** the system computes `S` using the default weight profile and returns component-level contributions

#### Scenario: Component normalization fails
- **WHEN** one or more component inputs are missing or out of bounds
- **THEN** the system clamps invalid values, records data-quality warnings, and returns a score with explicit uncertainty flags

### Requirement: Hard blockers SHALL override weighted score bands
The system SHALL enforce non-compensatory hard blockers (including `missing_run_identity`, parity failure, and lineage/policy blockers) such that a blocked decision cannot be promoted regardless of weighted score.

#### Scenario: High score with hard blocker
- **WHEN** weighted score is in Green range but one or more hard blockers are present
- **THEN** final readiness decision is blocked and the response includes blocker rationale and remediation actions

#### Scenario: No hard blockers
- **WHEN** no hard blockers are present
- **THEN** final decision band is derived from configured score thresholds

### Requirement: Readiness output SHALL be operator-actionable
The readiness payload SHALL include decision band, top blocker list, and prioritized next actions for operators.

#### Scenario: Operator inspects readiness panel
- **WHEN** API or dashboard renders readiness output
- **THEN** the user sees score, band, top blockers, and concrete next actions in a stable canonical format

#### Scenario: Decision state changes between evaluations
- **WHEN** readiness inputs change between evaluations
- **THEN** the payload includes transition-aware context indicating which components drove the state change
