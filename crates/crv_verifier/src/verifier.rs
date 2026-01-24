use crate::types::{CRVReport, CRVViolation, RuleId, Severity};
use anyhow::Result;
use schema::{BacktestStats, Fill};

/// Threshold for unrealistic Sharpe ratio (annualized)
const SHARPE_RATIO_UNREALISTIC_THRESHOLD: f64 = 10.0;

/// Threshold percentage for survivorship bias detection (delisted symbols)
const SURVIVORSHIP_BIAS_DELISTED_THRESHOLD_PCT: f64 = 5.0;

/// Threshold for cherry-picking detection (% of universe traded)
const SURVIVORSHIP_BIAS_CHERRY_PICKING_THRESHOLD_PCT: f64 = 10.0;

/// Minimum universe size for cherry-picking detection
const MIN_UNIVERSE_SIZE_FOR_CHERRY_PICKING: usize = 10;

/// Tolerance for max drawdown calculation validation
const MAX_DRAWDOWN_TOLERANCE: f64 = 0.01;

/// Policy constraints for verification
#[derive(Debug, Clone)]
pub struct PolicyConstraints {
    pub max_drawdown: Option<f64>,
    pub max_leverage: Option<f64>,
    pub max_turnover: Option<f64>,
}

impl Default for PolicyConstraints {
    fn default() -> Self {
        Self {
            max_drawdown: Some(0.25), // 25% default max drawdown
            max_leverage: Some(2.0),  // 2x default max leverage
            max_turnover: None,       // No default turnover limit
        }
    }
}

/// Main CRV verifier that checks backtest results for correctness
pub struct CRVVerifier {
    constraints: PolicyConstraints,
}

/// Optional metadata for survivorship bias detection
#[derive(Debug, Clone)]
pub struct UniverseMetadata {
    /// Total symbols in universe
    pub total_symbols: usize,
    /// Symbols that delisted during backtest period
    pub delisted_symbols: Vec<String>,
    /// Symbols actually traded
    pub traded_symbols: Vec<String>,
}

impl CRVVerifier {
    pub fn new(constraints: PolicyConstraints) -> Self {
        Self { constraints }
    }

    pub fn with_defaults() -> Self {
        Self::new(PolicyConstraints::default())
    }

    /// Verify backtest results and generate a CRV report
    pub fn verify(
        &self,
        stats: &BacktestStats,
        fills: &[Fill],
        equity_history: &[(i64, f64)],
    ) -> Result<CRVReport> {
        // Validate input
        if equity_history.is_empty() {
            anyhow::bail!("Equity history cannot be empty for CRV verification");
        }

        let mut report = CRVReport::new(equity_history.last().map(|(t, _)| *t).unwrap_or(0));

        // Run all checks
        self.check_metric_correctness(stats, equity_history, &mut report)?;
        self.check_lookahead_bias(fills, equity_history, &mut report)?;
        self.check_policy_constraints(stats, equity_history, &mut report)?;

        Ok(report)
    }

    /// Verify backtest with optional universe metadata for survivorship bias detection
    pub fn verify_with_universe(
        &self,
        stats: &BacktestStats,
        fills: &[Fill],
        equity_history: &[(i64, f64)],
        universe: &UniverseMetadata,
    ) -> Result<CRVReport> {
        let mut report = self.verify(stats, fills, equity_history)?;

        // Additional survivorship bias checks
        self.check_survivorship_bias(universe, &mut report)?;

        Ok(report)
    }

    /// Check for survivorship bias in universe composition
    fn check_survivorship_bias(
        &self,
        universe: &UniverseMetadata,
        report: &mut CRVReport,
    ) -> Result<()> {
        // Check if delisted symbols are missing from the universe
        if !universe.delisted_symbols.is_empty() {
            let delisted_count = universe.delisted_symbols.len();
            let total_count = universe.total_symbols;
            let delisted_pct = (delisted_count as f64 / total_count as f64) * 100.0;

            // If more than threshold % of symbols are delisted but not in the universe, flag it
            if delisted_pct > SURVIVORSHIP_BIAS_DELISTED_THRESHOLD_PCT {
                report.add_violation(CRVViolation {
                    rule_id: RuleId::SurvivorshipBias,
                    severity: Severity::High,
                    message: format!(
                        "Universe may have survivorship bias: {:.1}% of symbols ({}/{}) delisted during backtest period",
                        delisted_pct, delisted_count, total_count
                    ),
                    evidence: vec![
                        format!("Delisted symbols: {}", universe.delisted_symbols.join(", ")),
                        "Consider including delisted symbols to avoid survivorship bias".to_string(),
                    ],
                });
            }
        }

        // Check if traded symbols are a small subset of universe (might indicate cherry-picking)
        let traded_count = universe.traded_symbols.len();
        let total_count = universe.total_symbols;
        let traded_pct = (traded_count as f64 / total_count as f64) * 100.0;

        if traded_pct < SURVIVORSHIP_BIAS_CHERRY_PICKING_THRESHOLD_PCT
            && total_count > MIN_UNIVERSE_SIZE_FOR_CHERRY_PICKING
        {
            report.add_violation(CRVViolation {
                rule_id: RuleId::SurvivorshipBias,
                severity: Severity::Medium,
                message: format!(
                    "Strategy traded only {} out of {} symbols ({:.1}%)",
                    traded_count, total_count, traded_pct
                ),
                evidence: vec![
                    "Trading a small subset of universe may indicate cherry-picking".to_string(),
                    "Verify strategy logic applies consistently to all universe symbols"
                        .to_string(),
                ],
            });
        }

        Ok(())
    }

    /// Check metric calculations for correctness
    fn check_metric_correctness(
        &self,
        stats: &BacktestStats,
        equity_history: &[(i64, f64)],
        report: &mut CRVReport,
    ) -> Result<()> {
        // Validate Sharpe ratio annualization
        if stats.sharpe_ratio.is_finite() && stats.sharpe_ratio.abs() > 0.0 {
            // Sharpe should be annualized with sqrt(252)
            // We can't validate the exact calculation without the raw returns,
            // but we can check for unrealistic values
            if stats.sharpe_ratio.abs() > SHARPE_RATIO_UNREALISTIC_THRESHOLD {
                report.add_violation(CRVViolation {
                    rule_id: RuleId::SharpeRatioValidation,
                    severity: Severity::Medium,
                    message: format!(
                        "Sharpe ratio value is unrealistically high: {:.2}",
                        stats.sharpe_ratio
                    ),
                    evidence: vec![
                        format!(
                            "Sharpe ratios above {} are extremely rare in practice",
                            SHARPE_RATIO_UNREALISTIC_THRESHOLD
                        ),
                        "Verify annualization is correct (sqrt(252) for daily data)".to_string(),
                    ],
                });
            }
        }

        // Validate max drawdown is within reasonable bounds
        if stats.max_drawdown < 0.0 || stats.max_drawdown > 1.0 {
            report.add_violation(CRVViolation {
                rule_id: RuleId::MaxDrawdownValidation,
                severity: Severity::Critical,
                message: format!(
                    "Max drawdown is out of bounds [0, 1]: {:.4}",
                    stats.max_drawdown
                ),
                evidence: vec!["Max drawdown should be between 0 and 1 (0% to 100%)".to_string()],
            });
        }

        // Validate drawdown calculation by recomputing
        let computed_dd = self.compute_max_drawdown(equity_history);
        let dd_diff = (stats.max_drawdown - computed_dd).abs();
        if dd_diff > MAX_DRAWDOWN_TOLERANCE {
            report.add_violation(CRVViolation {
                rule_id: RuleId::MaxDrawdownValidation,
                severity: Severity::High,
                message: format!(
                    "Max drawdown calculation mismatch: reported {:.4} vs computed {:.4}",
                    stats.max_drawdown, computed_dd
                ),
                evidence: vec![format!("Difference: {:.4}", dd_diff)],
            });
        }

        Ok(())
    }

    /// Check for lookahead bias in the backtest
    fn check_lookahead_bias(
        &self,
        fills: &[Fill],
        equity_history: &[(i64, f64)],
        report: &mut CRVReport,
    ) -> Result<()> {
        // Check that all fills have valid timestamps
        for (i, fill) in fills.iter().enumerate() {
            if fill.timestamp <= 0 {
                report.add_violation(CRVViolation {
                    rule_id: RuleId::LookaheadBias,
                    severity: Severity::Critical,
                    message: "Fill has invalid timestamp".to_string(),
                    evidence: vec![format!("Fill #{}: timestamp = {}", i, fill.timestamp)],
                });
            }
        }

        // Check that fills are in chronological order
        for i in 1..fills.len() {
            if fills[i].timestamp < fills[i - 1].timestamp {
                report.add_violation(CRVViolation {
                    rule_id: RuleId::LookaheadBias,
                    severity: Severity::Critical,
                    message: "Fills are not in chronological order".to_string(),
                    evidence: vec![format!(
                        "Fill #{} (t={}) occurs before Fill #{} (t={})",
                        i,
                        fills[i].timestamp,
                        i - 1,
                        fills[i - 1].timestamp
                    )],
                });
            }
        }

        // Check that equity history is in chronological order
        for i in 1..equity_history.len() {
            if equity_history[i].0 < equity_history[i - 1].0 {
                report.add_violation(CRVViolation {
                    rule_id: RuleId::LookaheadBias,
                    severity: Severity::Critical,
                    message: "Equity history is not in chronological order".to_string(),
                    evidence: vec![format!(
                        "Point #{} (t={}) occurs before Point #{} (t={})",
                        i,
                        equity_history[i].0,
                        i - 1,
                        equity_history[i - 1].0
                    )],
                });
            }
        }

        Ok(())
    }

    /// Check policy constraints
    fn check_policy_constraints(
        &self,
        stats: &BacktestStats,
        equity_history: &[(i64, f64)],
        report: &mut CRVReport,
    ) -> Result<()> {
        // Check max drawdown constraint
        if let Some(max_dd) = self.constraints.max_drawdown {
            if stats.max_drawdown > max_dd {
                report.add_violation(CRVViolation {
                    rule_id: RuleId::MaxDrawdownConstraint,
                    severity: Severity::High,
                    message: format!(
                        "Max drawdown {:.2}% exceeds limit {:.2}%",
                        stats.max_drawdown * 100.0,
                        max_dd * 100.0
                    ),
                    evidence: vec![
                        format!("Observed: {:.4}", stats.max_drawdown),
                        format!("Limit: {:.4}", max_dd),
                    ],
                });
            }
        }

        // Check leverage constraint (simplified: check if any equity point goes negative)
        if let Some(max_leverage) = self.constraints.max_leverage {
            for (i, (timestamp, equity)) in equity_history.iter().enumerate() {
                if *equity < 0.0 {
                    report.add_violation(CRVViolation {
                        rule_id: RuleId::MaxLeverageConstraint,
                        severity: Severity::Critical,
                        message: "Negative equity detected (bankruptcy)".to_string(),
                        evidence: vec![
                            format!(
                                "Point #{}: timestamp={}, equity={:.2}",
                                i, timestamp, equity
                            ),
                            format!("Max leverage limit: {:.2}x", max_leverage),
                        ],
                    });
                    break; // Only report once
                }
            }
        }

        Ok(())
    }

    /// Helper: Compute max drawdown from equity history
    fn compute_max_drawdown(&self, equity_history: &[(i64, f64)]) -> f64 {
        if equity_history.is_empty() {
            return 0.0;
        }

        let mut max_equity = equity_history[0].1;
        let mut max_drawdown = 0.0;

        for (_, equity) in equity_history {
            if *equity > max_equity {
                max_equity = *equity;
            }
            if max_equity > 0.0 {
                let drawdown = (max_equity - equity) / max_equity;
                if drawdown > max_drawdown {
                    max_drawdown = drawdown;
                }
            }
        }

        max_drawdown
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_stats() -> BacktestStats {
        BacktestStats {
            initial_equity: 100000.0,
            final_equity: 110000.0,
            total_return: 0.1,
            num_trades: 10,
            total_commission: 50.0,
            sharpe_ratio: 1.5,
            max_drawdown: 0.15,
        }
    }

    #[test]
    fn test_verifier_passes_valid_backtest() {
        let verifier = CRVVerifier::with_defaults();

        // Create stats with actual drawdown in equity history
        let stats = BacktestStats {
            initial_equity: 100000.0,
            final_equity: 110000.0,
            total_return: 0.1,
            num_trades: 10,
            total_commission: 50.0,
            sharpe_ratio: 1.5,
            max_drawdown: 0.05, // 5% max drawdown
        };

        let fills = vec![];
        let equity_history = vec![
            (1000, 100000.0),
            (2000, 105000.0), // Peak
            (3000, 99750.0),  // 5% drawdown from peak
            (4000, 110000.0), // Recovery
        ];

        let report = verifier.verify(&stats, &fills, &equity_history).unwrap();

        // Debug output if test fails
        if !report.passed {
            eprintln!("Report violations:");
            for v in &report.violations {
                eprintln!("  {:?}: {}", v.rule_id, v.message);
            }
        }

        assert!(
            report.passed,
            "Expected report to pass but got {} violations",
            report.violation_count()
        );
        assert_eq!(report.violation_count(), 0);
    }

    #[test]
    fn test_verifier_detects_max_drawdown_violation() {
        let mut constraints = PolicyConstraints::default();
        constraints.max_drawdown = Some(0.10); // 10% limit

        let verifier = CRVVerifier::new(constraints);

        let stats = BacktestStats {
            max_drawdown: 0.15, // 15% drawdown exceeds limit
            ..create_test_stats()
        };

        let fills = vec![];
        let equity_history = vec![
            (1000, 100000.0),
            (2000, 85000.0), // 15% drawdown
            (3000, 110000.0),
        ];

        let report = verifier.verify(&stats, &fills, &equity_history).unwrap();
        assert!(!report.passed);
        assert!(report
            .violations
            .iter()
            .any(|v| v.rule_id == RuleId::MaxDrawdownConstraint));
    }

    #[test]
    fn test_verifier_detects_unrealistic_sharpe() {
        let verifier = CRVVerifier::with_defaults();

        let stats = BacktestStats {
            sharpe_ratio: 15.0, // Unrealistically high
            ..create_test_stats()
        };

        let fills = vec![];
        let equity_history = vec![(1000, 100000.0), (2000, 110000.0)];

        let report = verifier.verify(&stats, &fills, &equity_history).unwrap();
        assert!(!report.passed);
        assert!(report
            .violations
            .iter()
            .any(|v| v.rule_id == RuleId::SharpeRatioValidation));
    }

    #[test]
    fn test_verifier_detects_invalid_drawdown_bounds() {
        let verifier = CRVVerifier::with_defaults();

        let stats = BacktestStats {
            max_drawdown: 1.5, // > 1.0 is invalid
            ..create_test_stats()
        };

        let fills = vec![];
        let equity_history = vec![(1000, 100000.0), (2000, 110000.0)];

        let report = verifier.verify(&stats, &fills, &equity_history).unwrap();
        assert!(!report.passed);
        assert!(report.violations.iter().any(
            |v| v.rule_id == RuleId::MaxDrawdownValidation && v.severity == Severity::Critical
        ));
    }

    #[test]
    fn test_verifier_detects_out_of_order_fills() {
        let verifier = CRVVerifier::with_defaults();
        let stats = create_test_stats();

        let fills = vec![
            Fill {
                timestamp: 2000,
                symbol: "AAPL".to_string(),
                side: schema::Side::Buy,
                quantity: 10.0,
                price: 100.0,
                commission: 5.0,
            },
            Fill {
                timestamp: 1000, // Out of order!
                symbol: "AAPL".to_string(),
                side: schema::Side::Sell,
                quantity: 10.0,
                price: 105.0,
                commission: 5.0,
            },
        ];

        let equity_history = vec![(1000, 100000.0), (2000, 110000.0)];

        let report = verifier.verify(&stats, &fills, &equity_history).unwrap();
        assert!(!report.passed);
        assert!(report
            .violations
            .iter()
            .any(|v| v.rule_id == RuleId::LookaheadBias));
    }

    #[test]
    fn test_verifier_detects_negative_equity() {
        let verifier = CRVVerifier::with_defaults();
        let stats = create_test_stats();
        let fills = vec![];

        let equity_history = vec![
            (1000, 100000.0),
            (2000, -10000.0), // Bankruptcy!
            (3000, 110000.0),
        ];

        let report = verifier.verify(&stats, &fills, &equity_history).unwrap();
        assert!(!report.passed);
        assert!(report.violations.iter().any(
            |v| v.rule_id == RuleId::MaxLeverageConstraint && v.severity == Severity::Critical
        ));
    }

    #[test]
    fn test_verifier_detects_survivorship_bias_delisted() {
        let verifier = CRVVerifier::with_defaults();
        let stats = create_test_stats();
        let fills = vec![];
        let equity_history = vec![(1000, 100000.0), (2000, 105000.0), (3000, 110000.0)];

        let universe = UniverseMetadata {
            total_symbols: 100,
            delisted_symbols: vec![
                "XYZ".to_string(),
                "ABC".to_string(),
                "DEF".to_string(),
                "GHI".to_string(),
                "JKL".to_string(),
                "MNO".to_string(),
            ], // 6% delisted
            traded_symbols: vec!["AAPL".to_string()],
        };

        let report = verifier
            .verify_with_universe(&stats, &fills, &equity_history, &universe)
            .unwrap();
        assert!(!report.passed);
        assert!(report
            .violations
            .iter()
            .any(|v| v.rule_id == RuleId::SurvivorshipBias && v.severity == Severity::High));
    }

    #[test]
    fn test_verifier_detects_survivorship_bias_cherry_picking() {
        let verifier = CRVVerifier::with_defaults();
        let stats = create_test_stats();
        let fills = vec![];
        let equity_history = vec![(1000, 100000.0), (2000, 105000.0), (3000, 110000.0)];

        let universe = UniverseMetadata {
            total_symbols: 100,
            delisted_symbols: vec![],
            traded_symbols: vec!["AAPL".to_string()], // Only 1 out of 100
        };

        let report = verifier
            .verify_with_universe(&stats, &fills, &equity_history, &universe)
            .unwrap();
        assert!(!report.passed);
        assert!(report
            .violations
            .iter()
            .any(|v| v.rule_id == RuleId::SurvivorshipBias && v.severity == Severity::Medium));
    }

    #[test]
    fn test_verifier_rejects_empty_equity_history() {
        let verifier = CRVVerifier::with_defaults();
        let stats = create_test_stats();
        let fills = vec![];
        let equity_history: Vec<(i64, f64)> = vec![];

        let result = verifier.verify(&stats, &fills, &equity_history);
        assert!(result.is_err());
        assert!(result.unwrap_err().to_string().contains("cannot be empty"));
    }
}
