## 1. Canonical Event Foundation

- [x] 1.1 Define canonical market event envelope fields and typed payload variants for bar/trade/quote/book/options/fundamentals.
- [x] 1.2 Add validation rules for required envelope fields and tier-specific payload requirements.
- [x] 1.3 Define deterministic event ordering and replay invariants for canonical datasets.
- [x] 1.4 Add test fixtures and replay tests proving identical event sequence ordering across repeated runs.

## 2. Provider Adapter Framework

- [x] 2.1 Define provider adapter interface and capability declaration schema (asset classes, event types, fidelity tiers).
- [x] 2.2 Implement adapter normalization pipeline contract from provider-native records to canonical events.
- [x] 2.3 Add capability error handling for unsupported requests.
- [x] 2.4 Implement quality flag propagation for missing/derived/late source fields.
- [x] 2.5 Add legacy OHLCV parquet bridge path to canonical Tier 1 events.

## 3. Dataset Provenance and Governance

- [x] 3.1 Extend dataset metadata schema with required provenance fields (provider, venue class, timezone/calendar, adjustment policy).
- [x] 3.2 Add required fidelity tier and latency class metadata to dataset artifacts.
- [x] 3.3 Implement transformation lineage capture from raw source through normalized dataset outputs.
- [x] 3.4 Add comparability guard checks for cross-tier or materially different provenance comparisons.

## 4. Integration, Migration, and Rollout

- [x] 4.1 Add dual-path execution support so legacy bar pipeline and canonical Tier 1 pipeline can run in parallel.
- [x] 4.2 Add parity tests comparing legacy vs canonical Tier 1 outputs for equivalent inputs.
- [x] 4.3 Add incremental Tier 2 and Tier 3 readiness tests (tick/quote and order-book datasets).
- [x] 4.4 Add documentation for fidelity tiers, provider capabilities, and provenance requirements.
- [x] 4.5 Define release toggle, rollback procedure, and deprecation criteria for bar-only equivalence assumptions.
