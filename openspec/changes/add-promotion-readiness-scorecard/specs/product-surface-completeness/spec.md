## MODIFIED Requirements

### Requirement: Exposed product surfaces SHALL have executable backend workflows
Any feature surfaced as actionable in the dashboard SHALL have corresponding backend APIs that execute real workflows, not placeholders, and readiness decision views SHALL consume a canonical API contract.

#### Scenario: Reflexion workflow is invoked from dashboard
- **WHEN** a user starts or inspects Reflexion for a strategy
- **THEN** backend endpoints return real iteration records and status for that strategy

#### Scenario: Orchestrator run is started from dashboard
- **WHEN** a user starts a pipeline run from the Orchestrator page
- **THEN** backend creates a persisted run record and exposes stage-by-stage status transitions

#### Scenario: Orchestrator is started from clean state
- **WHEN** no prior orchestrator runs exist for the user session
- **THEN** the launch flow uses selected or generated strategy context and MUST NOT depend on run-list derived strategy identifiers

#### Scenario: Gate/readiness surface consumes canonical contract
- **WHEN** dashboard fetches gate or readiness status
- **THEN** displayed decision fields are sourced from a canonical readiness payload without schema-shape inference hacks

### Requirement: Advanced UI pathways SHALL use real or user-provided data
Advanced analytics flows in the dashboard SHALL use artifact-backed or user-provided input data and MUST NOT rely on random synthetic data in production mode.

#### Scenario: Advanced analytics operation is executed
- **WHEN** a user runs portfolio or risk analysis from the Advanced Features page
- **THEN** the request payload comes from user/artifact inputs and the response reflects backend computation without client-side random data generation

#### Scenario: Operator views promotion readiness panel
- **WHEN** a user opens dashboard summary or gates views
- **THEN** UI SHALL render score, band, blockers, and actions with consistent semantics across pages
