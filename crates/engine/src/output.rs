use anyhow::Result;
use schema::{BacktestStats, Fill};
use std::fs::File;
use std::path::Path;

/// Write trades to CSV
pub fn write_trades_csv(fills: &[Fill], output_path: &Path) -> Result<()> {
    let mut wtr = csv::Writer::from_writer(File::create(output_path)?);

    wtr.write_record(&[
        "timestamp",
        "symbol",
        "side",
        "quantity",
        "price",
        "commission",
    ])?;

    for fill in fills {
        wtr.write_record(&[
            fill.timestamp.to_string(),
            fill.symbol.clone(),
            format!("{:?}", fill.side),
            fill.quantity.to_string(),
            fill.price.to_string(),
            fill.commission.to_string(),
        ])?;
    }

    wtr.flush()?;
    Ok(())
}

/// Write equity curve to CSV
pub fn write_equity_curve_csv(equity_history: &[(i64, f64)], output_path: &Path) -> Result<()> {
    let mut wtr = csv::Writer::from_writer(File::create(output_path)?);

    wtr.write_record(&["timestamp", "equity"])?;

    for (timestamp, equity) in equity_history {
        wtr.write_record(&[timestamp.to_string(), equity.to_string()])?;
    }

    wtr.flush()?;
    Ok(())
}

/// Write backtest statistics to JSON
pub fn write_stats_json(stats: &BacktestStats, output_path: &Path) -> Result<()> {
    let file = File::create(output_path)?;
    serde_json::to_writer_pretty(file, stats)?;
    Ok(())
}

/// Calculate backtest statistics from equity history
pub fn calculate_stats(
    equity_history: &[(i64, f64)],
    num_trades: usize,
    total_commission: f64,
) -> BacktestStats {
    if equity_history.is_empty() {
        return BacktestStats {
            initial_equity: 0.0,
            final_equity: 0.0,
            total_return: 0.0,
            num_trades,
            total_commission,
            sharpe_ratio: 0.0,
            max_drawdown: 0.0,
        };
    }

    let initial_equity = equity_history[0].1;
    let final_equity = equity_history.last().unwrap().1;

    // Guard against division by zero
    if initial_equity <= 0.0 {
        return BacktestStats {
            initial_equity,
            final_equity,
            total_return: 0.0,
            num_trades,
            total_commission,
            sharpe_ratio: 0.0,
            max_drawdown: 0.0,
        };
    }

    let total_return = (final_equity - initial_equity) / initial_equity;

    // Calculate returns for Sharpe ratio
    let mut returns = Vec::new();
    for i in 1..equity_history.len() {
        let prev_equity = equity_history[i - 1].1;
        let curr_equity = equity_history[i].1;
        if prev_equity > 0.0 {
            returns.push((curr_equity - prev_equity) / prev_equity);
        }
    }

    let sharpe_ratio = if returns.len() > 1 {
        let mean = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance =
            returns.iter().map(|r| (r - mean).powi(2)).sum::<f64>() / returns.len() as f64;
        let std_dev = variance.sqrt();
        if std_dev > 0.0 {
            mean / std_dev * (252.0_f64).sqrt() // Annualized Sharpe
        } else {
            0.0
        }
    } else {
        0.0
    };

    // Calculate max drawdown
    let mut max_equity = initial_equity;
    let mut max_drawdown = 0.0;
    for (_, equity) in equity_history {
        if *equity > max_equity {
            max_equity = *equity;
        }
        // Guard against division by zero
        if max_equity > 0.0 {
            let drawdown = (max_equity - equity) / max_equity;
            if drawdown > max_drawdown {
                max_drawdown = drawdown;
            }
        }
    }

    BacktestStats {
        initial_equity,
        final_equity,
        total_return,
        num_trades,
        total_commission,
        sharpe_ratio,
        max_drawdown,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_calculate_stats_simple() {
        let equity_history = vec![(0, 10000.0), (1, 10500.0), (2, 11000.0)];

        let stats = calculate_stats(&equity_history, 2, 10.0);

        assert_eq!(stats.initial_equity, 10000.0);
        assert_eq!(stats.final_equity, 11000.0);
        assert!((stats.total_return - 0.1).abs() < 1e-6); // 10% return
        assert_eq!(stats.num_trades, 2);
        assert_eq!(stats.total_commission, 10.0);
    }

    #[test]
    fn test_calculate_stats_with_drawdown() {
        let equity_history = vec![
            (0, 10000.0),
            (1, 12000.0), // Peak
            (2, 9000.0),  // Drawdown of 25%
            (3, 11000.0),
        ];

        let stats = calculate_stats(&equity_history, 3, 10.0);

        assert!((stats.max_drawdown - 0.25).abs() < 1e-6); // 25% drawdown
    }
}
