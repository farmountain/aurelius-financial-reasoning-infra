## ADDED Requirements

### Requirement: API startup SHALL report deterministic operational readiness
The API SHALL perform startup checks that accurately distinguish healthy, degraded, and unavailable dependencies without producing misleading success signals.

#### Scenario: Database unavailable at startup
- **WHEN** the API process starts and the configured database cannot be authenticated or reached
- **THEN** startup logs and health metadata MUST record degraded dependency status with actionable reason codes

#### Scenario: Optional subsystems unavailable at startup
- **WHEN** optional subsystems such as cache are unavailable
- **THEN** the API MUST continue serving supported routes while surfacing explicit degraded component status

### Requirement: Health checks SHALL use executable SQLAlchemy patterns
Health endpoints SHALL use SQL execution patterns compatible with the active SQLAlchemy runtime and MUST NOT raise non-executable-object errors.

#### Scenario: Health check query execution
- **WHEN** a health probe executes database liveness validation
- **THEN** the endpoint returns structured health status without runtime query-construction exceptions

### Requirement: DB optimization routines SHALL be schema-aware
Database optimization and index-management routines SHALL validate table and column existence for the active schema before applying statements.

#### Scenario: Startup index verification against current schema
- **WHEN** index verification runs during startup
- **THEN** nonexistent tables or columns are skipped deterministically with precise diagnostics and without transaction poisoning
