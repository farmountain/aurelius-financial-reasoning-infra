## ADDED Requirements

### Requirement: Provider adapter contract
The system SHALL define a provider adapter contract that normalizes provider-native market data into canonical market events.

#### Scenario: Adapter normalization output
- **WHEN** a provider adapter receives provider-native data
- **THEN** it MUST emit canonical events compliant with canonical event envelope requirements

### Requirement: Declared provider capabilities
Each provider adapter SHALL declare supported asset classes, event types, and fidelity tiers.

#### Scenario: Unsupported capability request
- **WHEN** a consumer requests a fidelity tier or event type not supported by the selected adapter
- **THEN** the system MUST return a capability error indicating unsupported provider features

### Requirement: Adapter-level quality signaling
Provider adapters SHALL attach normalization warnings or quality flags when source data is incomplete, delayed, or transformed.

#### Scenario: Missing source fields
- **WHEN** required source fields are absent and a fallback transformation is applied
- **THEN** the emitted canonical event MUST include a quality flag describing the fallback condition

### Requirement: Backward-compatible bar bridge
The system SHALL provide a bridge path that allows existing bar-only datasets to be treated as canonical Tier 1 datasets.

#### Scenario: Legacy dataset ingestion
- **WHEN** a legacy parquet OHLCV dataset is ingested through the bridge
- **THEN** the system MUST produce canonical bar events without requiring Tier 2 or Tier 3 payloads
