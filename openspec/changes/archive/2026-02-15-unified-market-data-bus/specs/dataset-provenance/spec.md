## ADDED Requirements

### Requirement: Required dataset provenance metadata
The system SHALL require dataset provenance metadata including provider, venue or venue class, timezone/calendar basis, and adjustment policy.

#### Scenario: Provenance completeness check
- **WHEN** a dataset artifact is created for backtest or validation use
- **THEN** artifact creation MUST fail if any required provenance fields are missing

### Requirement: Fidelity tier and latency classification
The system SHALL require each dataset to declare fidelity tier and latency class as part of reproducibility metadata.

#### Scenario: Missing fidelity declaration
- **WHEN** a dataset is submitted without fidelity tier metadata
- **THEN** the system MUST reject the dataset for evidence-gated workflows

### Requirement: Transformation lineage tracking
The system SHALL record transformation lineage for normalized datasets, including source identifier and transformation steps.

#### Scenario: Auditable transform history
- **WHEN** an operator inspects a dataset artifact used by a backtest result
- **THEN** the system MUST expose source and transformation lineage sufficient to reproduce the dataset

### Requirement: Provenance-aware comparability checks
The system SHALL enforce comparability checks so evaluation results are not treated as equivalent when provenance or fidelity materially differs.

#### Scenario: Cross-tier comparison guard
- **WHEN** two results are compared and their datasets have different fidelity tiers
- **THEN** the system MUST flag the comparison as non-equivalent unless an explicit compatibility rule is provided
