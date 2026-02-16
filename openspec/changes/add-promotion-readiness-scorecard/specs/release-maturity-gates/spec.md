## MODIFIED Requirements

### Requirement: Capability maturity labels SHALL be enforced
Each externally exposed capability SHALL be labeled as `experimental`, `validated`, or `production` based on objective acceptance criteria and SHALL be consistent with scorecard-derived release evidence.

#### Scenario: Capability promoted to production
- **WHEN** capability metrics meet all production thresholds and no hard blockers are active
- **THEN** the capability label is updated to `production` and release notes include scorecard evidence summary

#### Scenario: Capability below threshold
- **WHEN** quality thresholds are not met or hard blockers are active
- **THEN** capability remains `experimental` or `validated` and cannot be advertised as production-ready

### Requirement: Release gating SHALL use measurable quality checks
Release decisions SHALL reference measurable checks including truth parity, determinism pass rate, contract parity, lineage completeness, and scorecard component outcomes.

#### Scenario: Release gate evaluation
- **WHEN** a release candidate is evaluated
- **THEN** the gate decision is derived from defined metrics, scorecard thresholds, and blocker precedence and is recorded with pass/fail rationale

#### Scenario: Score band determination
- **WHEN** no hard blockers are present during evaluation
- **THEN** decision band SHALL be emitted as Green/Amber/Red according to configured threshold policy
