## Why

AURELIUS has strong optimization and risk analytics, but its core backtesting flow is still centered on offline OHLCV bars and simulated execution assumptions. To support institutional-grade research (microstructure, options realism, global multi-asset coverage), the platform needs a unified market data contract that can ingest and validate multiple providers without locking the system to a single source.

## What Changes

- Introduce a unified market data bus capability that defines canonical event contracts across bars, trades, quotes, order book updates, options chain snapshots, and fundamentals/macro snapshots.
- Add a provider adapter framework so multiple data vendors (e.g., Alpaca, Polygon, Databento, Tiingo, IBKR) can be normalized into shared canonical events.
- Define dataset provenance and quality metadata requirements (provider, venue, adjustment policy, timezone/calendar, latency class, quality flags) for reproducible validation and CRV evidence.
- Define tiered simulation/data fidelity requirements (bar-level, tick/quote-level, order-book-level) so backtest expectations are explicit and testable.
- **BREAKING**: Existing assumptions that all datasets are bar-only and equivalent in fidelity will no longer be sufficient for validation once canonical event tiers are introduced.

## Capabilities

### New Capabilities
- `canonical-market-events`: Canonical event schema and validation rules for market data across fidelity tiers.
- `market-data-adapters`: Provider adapter contract, lifecycle, and normalization requirements for external market data APIs.
- `dataset-provenance`: Dataset lineage, quality, and reproducibility metadata requirements for evidence-gated workflows.

### Modified Capabilities
- None.

## Impact

- Affects Rust data interfaces and ingestion flows currently centered on `DataFeed`, `Bar`, and parquet-only loading.
- Affects simulation assumptions in broker execution realism and risk analytics comparability.
- Affects API and orchestration layers that currently use mock/random optimization/backtest flows for advanced endpoints.
- Introduces dependency on explicit provider abstraction boundaries and validation rules for data quality/fidelity.
- Expands HipCortex artifact expectations to include richer data provenance for reproducibility and auditability.
