use anyhow::{Context, Result};
use broker_sim::SimpleBroker;
use cost::{FixedPerShareCost, PercentageCost, ZeroCost};
use crv_verifier::{CRVVerifier, PolicyConstraints};
use engine::{BacktestEngine, VecDataFeed};
use polars::prelude::*;
use schema::{
    sort_events_deterministically, validate_events_for_tier, Bar, CostModel, EventEnvelope,
    FidelityTier, MarketEventPayload, MarketEventType, QualityFlag,
};
use std::fs;
use std::path::Path;

use crate::spec::{BacktestSpec, CostModelSpec, DataPipelineSpec, StrategySpec};
use crate::strategies::TsMomentumStrategy;

pub fn run_backtest(spec_path: &Path, data_path: &Path, out_dir: &Path) -> Result<()> {
    // Read spec
    let spec_str = fs::read_to_string(spec_path).context("Failed to read spec file")?;
    let spec: BacktestSpec =
        serde_json::from_str(&spec_str).context("Failed to parse spec JSON")?;

    // Create output directory
    fs::create_dir_all(out_dir).context("Failed to create output directory")?;

    // Load data from parquet (legacy bar path or canonical Tier 1 bridge path)
    let bars = match spec.data_pipeline {
        DataPipelineSpec::Legacy => load_bars_from_parquet_legacy(data_path)?,
        DataPipelineSpec::CanonicalTier1 => load_bars_from_parquet_canonical_tier1(data_path)?,
    };

    println!("Loaded {} bars", bars.len());
    println!("Running backtest with {} strategy", spec.strategy_name());
    println!("Initial cash: ${:.2}", spec.initial_cash);
    println!("Seed: {}", spec.seed);
    println!(
        "Data pipeline: {}",
        match spec.data_pipeline {
            DataPipelineSpec::Legacy => "legacy",
            DataPipelineSpec::CanonicalTier1 => "canonical_tier1",
        }
    );

    // Create data feed
    let data_feed = VecDataFeed::new(bars);

    // Run backtest based on strategy type
    match &spec.strategy {
        StrategySpec::TsMomentum {
            symbol,
            lookback,
            vol_target,
            vol_lookback,
        } => {
            let strategy =
                TsMomentumStrategy::new(symbol.clone(), *lookback, *vol_target, *vol_lookback);

            run_backtest_with_strategy(data_feed, strategy, &spec, out_dir)?;
        }
    }

    println!("Backtest completed. Results written to {:?}", out_dir);
    Ok(())
}

fn run_backtest_with_strategy<S: schema::Strategy>(
    data_feed: VecDataFeed,
    strategy: S,
    spec: &BacktestSpec,
    out_dir: &Path,
) -> Result<()> {
    // Create cost model
    let cost_model: Box<dyn CostModel> = match &spec.cost_model {
        CostModelSpec::FixedPerShare {
            cost_per_share,
            minimum_commission,
        } => Box::new(FixedPerShareCost::new(*cost_per_share, *minimum_commission)),
        CostModelSpec::Percentage {
            percentage,
            minimum_commission,
        } => Box::new(PercentageCost::new(*percentage, *minimum_commission)),
        CostModelSpec::Zero => Box::new(ZeroCost),
    };

    // Create broker with deterministic seed
    let broker = SimpleBroker::new(cost_model, spec.seed);

    // Create and run engine
    let mut engine = BacktestEngine::new(data_feed, strategy, broker, spec.initial_cash);

    engine.run()?;

    // Write outputs
    let trades_path = out_dir.join("trades.csv");
    engine::output::write_trades_csv(engine.fills(), &trades_path)?;
    println!("Wrote trades to {:?}", trades_path);

    let equity_path = out_dir.join("equity_curve.csv");
    engine::output::write_equity_curve_csv(engine.equity_history(), &equity_path)?;
    println!("Wrote equity curve to {:?}", equity_path);

    let stats = engine::output::calculate_stats(
        engine.equity_history(),
        engine.num_trades(),
        engine.total_commission(),
    );

    let stats_path = out_dir.join("stats.json");
    engine::output::write_stats_json(&stats, &stats_path)?;
    println!("Wrote statistics to {:?}", stats_path);

    // Run CRV verification
    println!("\n=== Running CRV Verification ===");
    let constraints = PolicyConstraints::default();
    let verifier = CRVVerifier::new(constraints);

    let crv_report = verifier.verify(&stats, engine.fills(), engine.equity_history())?;

    let crv_path = out_dir.join("crv_report.json");
    let crv_file = fs::File::create(&crv_path)?;
    serde_json::to_writer_pretty(crv_file, &crv_report)?;
    println!("Wrote CRV report to {:?}", crv_path);

    if crv_report.passed {
        println!("✓ CRV verification passed");
    } else {
        println!(
            "✗ CRV verification failed with {} violation(s)",
            crv_report.violation_count()
        );
        for (i, violation) in crv_report.violations.iter().enumerate() {
            println!("\n  Violation #{}:", i + 1);
            println!("    Rule: {:?}", violation.rule_id);
            println!("    Severity: {:?}", violation.severity);
            println!("    Message: {}", violation.message);
            if !violation.evidence.is_empty() {
                println!("    Evidence:");
                for evidence in &violation.evidence {
                    println!("      - {}", evidence);
                }
            }
        }
    }

    // Print summary
    println!("\n=== Backtest Summary ===");
    println!("Initial equity: ${:.2}", stats.initial_equity);
    println!("Final equity: ${:.2}", stats.final_equity);
    println!("Total return: {:.2}%", stats.total_return * 100.0);
    println!("Number of trades: {}", stats.num_trades);
    println!("Total commission: ${:.2}", stats.total_commission);
    println!("Sharpe ratio: {:.4}", stats.sharpe_ratio);
    println!("Max drawdown: {:.2}%", stats.max_drawdown * 100.0);

    Ok(())
}

fn load_bars_from_parquet_legacy(path: &Path) -> Result<Vec<Bar>> {
    let df = LazyFrame::scan_parquet(path, Default::default())?.collect()?;

    let timestamps = df
        .column("timestamp")?
        .i64()?
        .into_no_null_iter()
        .collect::<Vec<_>>();
    let symbols = df.column("symbol")?.str()?.into_iter().collect::<Vec<_>>();
    let opens = df
        .column("open")?
        .f64()?
        .into_no_null_iter()
        .collect::<Vec<_>>();
    let highs = df
        .column("high")?
        .f64()?
        .into_no_null_iter()
        .collect::<Vec<_>>();
    let lows = df
        .column("low")?
        .f64()?
        .into_no_null_iter()
        .collect::<Vec<_>>();
    let closes = df
        .column("close")?
        .f64()?
        .into_no_null_iter()
        .collect::<Vec<_>>();
    let volumes = df
        .column("volume")?
        .f64()?
        .into_no_null_iter()
        .collect::<Vec<_>>();

    let bars = timestamps
        .iter()
        .zip(symbols.iter())
        .zip(opens.iter())
        .zip(highs.iter())
        .zip(lows.iter())
        .zip(closes.iter())
        .zip(volumes.iter())
        .map(|((((((t, s), o), h), l), c), v)| Bar {
            timestamp: *t,
            symbol: s.unwrap_or("UNKNOWN").to_string(),
            open: *o,
            high: *h,
            low: *l,
            close: *c,
            volume: *v,
        })
        .collect();

    Ok(bars)
}

fn load_bars_from_parquet_canonical_tier1(path: &Path) -> Result<Vec<Bar>> {
    let legacy_bars = load_bars_from_parquet_legacy(path)?;
    let mut events = bars_to_canonical_tier1_events(&legacy_bars, "legacy-parquet");

    sort_events_deterministically(&mut events);
    validate_events_for_tier(&events, FidelityTier::Tier1Bar)
        .context("Canonical Tier 1 validation failed")?;

    canonical_tier1_events_to_bars(&events)
}

fn bars_to_canonical_tier1_events(bars: &[Bar], source_id: &str) -> Vec<EventEnvelope> {
    bars.iter()
        .map(|bar| EventEnvelope {
            event_type: MarketEventType::Bar,
            symbol: bar.symbol.clone(),
            event_time: bar.timestamp,
            ingest_time: bar.timestamp,
            source_id: source_id.to_string(),
            quality_flags: vec![QualityFlag::DerivedValue],
            payload: MarketEventPayload::Bar(bar.clone()),
        })
        .collect()
}

fn canonical_tier1_events_to_bars(events: &[EventEnvelope]) -> Result<Vec<Bar>> {
    let mut bars = Vec::new();

    for event in events {
        event
            .validate_required_fields()
            .context("Invalid canonical event encountered")?;

        if let MarketEventPayload::Bar(bar) = &event.payload {
            bars.push(bar.clone());
        }
    }

    Ok(bars)
}

impl BacktestSpec {
    fn strategy_name(&self) -> &str {
        match &self.strategy {
            StrategySpec::TsMomentum { .. } => "TsMomentum",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_tier1_bridge_preserves_legacy_bars() {
        let legacy = vec![
            Bar {
                timestamp: 1000,
                symbol: "AAPL".to_string(),
                open: 100.0,
                high: 102.0,
                low: 99.0,
                close: 101.0,
                volume: 10000.0,
            },
            Bar {
                timestamp: 2000,
                symbol: "AAPL".to_string(),
                open: 101.0,
                high: 103.0,
                low: 100.0,
                close: 102.0,
                volume: 11000.0,
            },
        ];

        let events = bars_to_canonical_tier1_events(&legacy, "legacy-parquet");
        let recovered = canonical_tier1_events_to_bars(&events).unwrap();

        assert_eq!(legacy, recovered);
    }

    #[test]
    fn tier_readiness_requires_trade_or_quote_for_tier2() {
        let events = bars_to_canonical_tier1_events(
            &[Bar {
                timestamp: 1000,
                symbol: "AAPL".to_string(),
                open: 100.0,
                high: 102.0,
                low: 99.0,
                close: 101.0,
                volume: 10000.0,
            }],
            "legacy-parquet",
        );

        assert!(validate_events_for_tier(&events, FidelityTier::Tier2TickQuote).is_err());
    }

    #[test]
    fn tier_readiness_requires_book_for_tier3() {
        let events = bars_to_canonical_tier1_events(
            &[Bar {
                timestamp: 1000,
                symbol: "AAPL".to_string(),
                open: 100.0,
                high: 102.0,
                low: 99.0,
                close: 101.0,
                volume: 10000.0,
            }],
            "legacy-parquet",
        );

        assert!(validate_events_for_tier(&events, FidelityTier::Tier3OrderBook).is_err());
    }
}
