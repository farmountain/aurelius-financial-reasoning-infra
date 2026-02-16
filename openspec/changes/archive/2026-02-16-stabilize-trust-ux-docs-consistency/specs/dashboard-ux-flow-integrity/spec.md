## ADDED Requirements

### Requirement: Empty-state orchestrator flow SHALL be executable
The Orchestrator page SHALL support first-run execution without requiring previously existing orchestration runs.

#### Scenario: User starts orchestrator with no prior runs
- **WHEN** a user opens Orchestrator and no runs exist
- **THEN** the UI provides a valid strategy selection or generation path and can create a new run without hidden prerequisites

### Requirement: Dashboard gate metrics SHALL reflect live data
Dashboard gate summary metrics SHALL be computed from persisted gate results instead of placeholders.

#### Scenario: Gate summary rendering
- **WHEN** the dashboard loads with historical gate outcomes
- **THEN** passed, failed, and total counts shown are derived from backend gate status data

### Requirement: Reflexion list metrics SHALL be strategy-specific
Reflexion list summaries SHALL display per-strategy iteration counts rather than reusing the currently selected strategy count for all rows.

#### Scenario: Reflexion list with multiple strategies
- **WHEN** the user views Reflexion strategy cards for multiple strategies
- **THEN** each row displays that strategy's own iteration count and latest status
