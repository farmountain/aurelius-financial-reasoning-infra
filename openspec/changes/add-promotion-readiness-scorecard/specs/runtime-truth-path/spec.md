## MODIFIED Requirements

### Requirement: Production API execution SHALL be engine-backed
All production backtest, validation, gate, and optimization API routes SHALL execute deterministic engine-backed computation and MUST NOT return mocked or randomized metrics.

#### Scenario: Backtest route uses real execution path
- **WHEN** a client submits a valid backtest request in production mode
- **THEN** the system runs deterministic engine-backed computation and returns persisted result artifacts

#### Scenario: Validation route enforces real window execution
- **WHEN** a client submits a validation request with sufficient data
- **THEN** the system computes validation metrics from actual window executions and stores evidence artifacts

#### Scenario: Strategy generation avoids static synthetic ranking behavior
- **WHEN** a client generates strategies from a goal
- **THEN** returned strategy candidates are derived from goal/risk inputs and MUST NOT rely solely on fixed static strategy lists with mock timing semantics

### Requirement: Result parity SHALL be measurable across interfaces
For the same canonical run identity (`spec_hash`, `data_hash`, `seed`, `engine_version`), CLI and API outputs SHALL match within configured metric tolerances and SHALL contribute to readiness score inputs.

#### Scenario: CLI/API parity check passes
- **WHEN** parity validation is executed for a canonical run identity
- **THEN** metric deltas remain within configured tolerances and the run is marked parity-compliant

#### Scenario: Parity check fails
- **WHEN** one or more core metrics exceed tolerance
- **THEN** the system records a parity violation and blocks production promotion for that run

#### Scenario: Deterministic seed and data inputs are explicitly controllable
- **WHEN** an authorized user or integration specifies run seed and data source inputs
- **THEN** the execution records those inputs in run identity/provenance while preserving deterministic replay behavior

#### Scenario: Acceptance evidence reflects current gate-path behavior
- **WHEN** release readiness is evaluated using acceptance evidence
- **THEN** gate-path outcomes in evidence are current and interpreted with explicit environment caveats before production claims are made

#### Scenario: Operational reliability contributes to readiness
- **WHEN** startup/dependency health is degraded during readiness evaluation
- **THEN** readiness operational component is penalized with explicit root-cause metadata
