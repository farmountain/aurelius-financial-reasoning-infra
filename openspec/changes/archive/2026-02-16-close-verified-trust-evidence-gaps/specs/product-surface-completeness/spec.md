## MODIFIED Requirements

### Requirement: Exposed product surfaces SHALL have executable backend workflows
Any feature surfaced as actionable in the dashboard SHALL have corresponding backend APIs that execute real workflows, not placeholders.

#### Scenario: Reflexion workflow is invoked from dashboard
- **WHEN** a user starts or inspects Reflexion for a strategy
- **THEN** backend endpoints return real iteration records and status for that strategy.

#### Scenario: Orchestrator run is started from dashboard
- **WHEN** a user starts a pipeline run from the Orchestrator page
- **THEN** backend creates a persisted run record and exposes stage-by-stage status transitions.

#### Scenario: Orchestrator is started from clean state
- **WHEN** no prior orchestrator runs exist for the user session
- **THEN** the launch flow uses selected or generated strategy context and MUST NOT depend on run-list derived strategy identifiers.

### Requirement: Advanced UI pathways SHALL use real or user-provided data
Advanced analytics flows in the dashboard SHALL use artifact-backed or user-provided input data and MUST NOT rely on random synthetic data in production mode.

#### Scenario: Advanced analytics operation is executed
- **WHEN** a user runs portfolio or risk analysis from the Advanced Features page
- **THEN** the request payload comes from user/artifact inputs and the response reflects backend computation without client-side random data generation.
