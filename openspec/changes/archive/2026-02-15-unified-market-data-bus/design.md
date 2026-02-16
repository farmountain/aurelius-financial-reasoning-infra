## Context

AURELIUS currently processes market data primarily as OHLCV bars and runs deterministic backtests over parquet inputs. This is effective for baseline strategy research, but it limits realism for microstructure-sensitive strategies, option execution modeling, and cross-provider comparability. The project already has modular seams (`DataFeed`, broker abstraction, artifact storage), so the design should preserve determinism and testability while introducing richer data fidelity and provider normalization.

Constraints:
- Determinism and reproducibility remain mandatory.
- Existing bar-based workflows must continue to function during migration.
- Multiple providers with different schemas, calendars, and latency qualities must be normalized without hiding provenance.

Stakeholders:
- Quant researchers (fidelity and realism)
- Platform/backend engineers (maintainable abstraction boundaries)
- Risk/validation owners (CRV evidence and reproducibility)

## Goals / Non-Goals

**Goals:**
- Define a canonical market event model that supports bar, trade, quote, order-book, options chain, and fundamentals snapshots.
- Define provider adapter contracts for normalization into canonical events.
- Preserve source provenance and quality metadata at dataset and event-batch levels.
- Define tiered simulation fidelity levels so strategy evaluation expectations are explicit.
- Maintain backward compatibility for existing bar-based backtests while enabling phased adoption.

**Non-Goals:**
- Implementing full production connectors for every provider in this change.
- Replacing all existing strategy logic in one release.
- Building a low-latency live trading router in this phase.
- Solving all market-impact modeling details (only defining interfaces and required data).

## Decisions

### 1) Canonical event envelope with typed payloads
Decision: Use a canonical envelope (`event_type`, `symbol`, `event_time`, `ingest_time`, `source_id`, `quality_flags`, `payload`) and typed payload variants for bars/trades/quotes/book/options/fundamentals.

Rationale:
- Keeps one ingestion pipeline while preserving event-specific fields.
- Enables consistent ordering, validation, and replay across providers.

Alternatives considered:
- Separate independent pipelines per event type (rejected: high duplication and reconciliation complexity).
- Provider-specific models passed downstream (rejected: lock-in and inconsistent analytics behavior).

### 2) Adapter boundary per provider, not per asset class
Decision: Define one provider adapter interface with capability flags (supported asset classes/event types/fidelity levels), and let each provider implement only supported subsets.

Rationale:
- Mirrors real vendor constraints.
- Avoids fragmented adapter explosion while still expressing capability differences.

Alternatives considered:
- Asset-class-first adapters (rejected: duplicates auth/rate-limit/provenance concerns across classes).

### 3) Fidelity tiers as first-class dataset attributes
Decision: Define simulation/data fidelity tiers (Tier 1 bar, Tier 2 tick/quote, Tier 3 book depth) and require each dataset to declare its tier.

Rationale:
- Prevents false comparability across results from materially different data richness.
- Allows CRV/risk/reporting to enforce context-aware expectations.

Alternatives considered:
- Implicit fidelity inferred from fields (rejected: brittle and ambiguous).

### 4) Provenance-required artifacts
Decision: Extend dataset metadata requirements to include provider, venue, adjustment policy, timezone/calendar, latency class, and transform lineage.

Rationale:
- Reproducibility depends on knowing exactly what data was used and how it was transformed.
- Supports evidence-gated workflows and auditability.

Alternatives considered:
- Keep metadata optional (rejected: undermines reproducibility and governance).

### 5) Backward-compatible migration bridge
Decision: Keep bar-based ingestion and simulation paths valid while adding canonical-event paths in parallel behind explicit configuration.

Rationale:
- Reduces migration risk and avoids blocking existing users.
- Allows progressive hardening of advanced paths before deprecating legacy assumptions.

Alternatives considered:
- Big-bang replacement (rejected: high delivery and reliability risk).

## Risks / Trade-offs

- [Schema complexity growth] → Mitigation: strict versioning, canonical validation tests, and minimal required core fields per event type.
- [Provider normalization drift] → Mitigation: golden normalization fixtures per provider and cross-provider parity tests for overlapping symbols/time windows.
- [Determinism regressions from real-time ingestion] → Mitigation: persisted ordered event logs and replay-by-sequence semantics for testing.
- [Higher storage and compute costs at Tier 2/3] → Mitigation: tier-aware retention policies and selective downsampling.
- [User confusion across fidelity tiers] → Mitigation: explicit tier labeling in API outputs and reports; reject tier-incompatible analytics requests.

## Migration Plan

1. Define canonical schemas and fidelity-tier taxonomy.
2. Introduce adapter interfaces and capability declarations.
3. Add provenance metadata requirements and validation rules in artifact workflows.
4. Add bridge converters from existing bar/parquet inputs to canonical events.
5. Enable dual-run validation (legacy path vs canonical Tier 1 path) for parity checks.
6. Introduce Tier 2/3 simulation support incrementally with guarded rollout.
7. Deprecate bar-only equivalence assumptions after parity and governance checks pass.

Rollback strategy:
- Keep legacy bar pipeline and configuration toggle available until canonical path maturity is confirmed.
- On failure, revert to legacy execution path while preserving ingested artifacts for diagnostics.

## Open Questions

- Which provider(s) should be first-class in Phase 1 adapter rollout (Polygon vs Databento vs Alpaca bridge)?
- What is the minimum required set of quality flags for CRV acceptance per fidelity tier?
- Should options chain snapshots be represented as per-contract events or batched chain events for performance?
- What default retention policy is acceptable for Tier 3 order-book data in local/dev environments?
- Where should symbol mapping authority live (adapter-local vs central normalization service)?
