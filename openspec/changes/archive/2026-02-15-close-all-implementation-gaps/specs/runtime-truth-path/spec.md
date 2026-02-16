## ADDED Requirements

### Requirement: Production API execution SHALL be engine-backed
All production backtest, validation, gate, and optimization API routes SHALL execute deterministic engine-backed computation and MUST NOT return mocked or randomized metrics.

#### Scenario: Backtest route uses real execution path
- **WHEN** a client submits a valid backtest request in production mode
- **THEN** the system runs deterministic engine-backed computation and returns persisted result artifacts

#### Scenario: Validation route enforces real window execution
- **WHEN** a client submits a validation request with sufficient data
- **THEN** the system computes validation metrics from actual window executions and stores evidence artifacts

### Requirement: Result parity SHALL be measurable across interfaces
For the same canonical run identity (`spec_hash`, `data_hash`, `seed`, `engine_version`), CLI and API outputs SHALL match within configured metric tolerances.

#### Scenario: CLI/API parity check passes
- **WHEN** parity validation is executed for a canonical run identity
- **THEN** metric deltas remain within configured tolerances and the run is marked parity-compliant

#### Scenario: Parity check fails
- **WHEN** one or more core metrics exceed tolerance
- **THEN** the system records a parity violation and blocks production promotion for that run
