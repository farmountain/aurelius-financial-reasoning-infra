# Unified Market Data Bus Rollout Guide

## Fidelity Tiers

- **Tier 1 (`tier1_bar`)**: OHLCV bar events only. Suitable for baseline backtests and compatibility with the legacy pipeline.
- **Tier 2 (`tier2_tick_quote`)**: Trade and/or quote events. Suitable for intraday microstructure-aware analytics.
- **Tier 3 (`tier3_order_book`)**: Order book updates. Suitable for depth-aware execution and impact research.

## Provider Capabilities

Each adapter declares capabilities:

- Supported asset classes (equity, future, option, crypto, fx, commodity)
- Supported event types (bar/trade/quote/order_book/options_chain/fundamentals)
- Supported fidelity tiers

Unsupported requests are rejected with a capability error.

## Provenance Requirements

Dataset metadata MUST include:

- `provider`
- `venue_class`
- `timezone_calendar`
- `adjustment_policy`
- `fidelity_tier`
- `latency_class`
- `quality_flags`
- `transform_lineage`

These fields are required for reproducibility and comparability checks.

## Data Pipeline Modes

Backtest spec supports two data modes:

- `legacy` (default): existing parquet->bars path
- `canonical_tier1`: legacy parquet bridged to canonical events then projected back to bars

## Release Toggle

Use `data_pipeline` in backtest spec to control rollout per run:

```json
{
  "data_pipeline": "legacy"
}
```

or

```json
{
  "data_pipeline": "canonical_tier1"
}
```

## Rollback Procedure

1. Set `data_pipeline` back to `legacy` for all execution paths.
2. Keep canonical artifacts for diagnostics and parity analysis.
3. Disable Tier 2/Tier 3 validation gates if they block critical workflows.

## Deprecation Criteria for Bar-only Equivalence

Deprecate the assumption that all bar datasets are equivalent only when:

1. Tier 1 canonical parity tests pass consistently.
2. Provenance metadata is present and validated in dataset artifacts.
3. Comparability guards are active for cross-tier comparisons.
4. Operational rollback to legacy mode is documented and validated.
