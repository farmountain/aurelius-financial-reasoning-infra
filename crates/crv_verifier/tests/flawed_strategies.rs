/// Integration tests for CRV verifier with intentionally flawed strategies
use crv_verifier::{CRVVerifier, PolicyConstraints, RuleId, Severity};
use schema::{BacktestStats, Fill, Side};

#[test]
fn test_flawed_strategy_with_lookahead_bias() {
    // Simulate a strategy that somehow traded before data arrived
    // (fills out of chronological order)
    let verifier = CRVVerifier::with_defaults();

    let stats = BacktestStats {
        initial_equity: 100000.0,
        final_equity: 150000.0,
        total_return: 0.5,
        num_trades: 3,
        total_commission: 15.0,
        sharpe_ratio: 2.5,
        max_drawdown: 0.08,
    };

    // Fills are intentionally out of order - evidence of lookahead bias
    let fills = vec![
        Fill {
            timestamp: 3000,
            symbol: "AAPL".to_string(),
            side: Side::Buy,
            quantity: 100.0,
            price: 150.0,
            commission: 5.0,
        },
        Fill {
            timestamp: 1000, // This is earlier! Lookahead bias detected
            symbol: "AAPL".to_string(),
            side: Side::Sell,
            quantity: 100.0,
            price: 145.0,
            commission: 5.0,
        },
    ];

    let equity_history = vec![(1000, 100000.0), (2000, 108000.0), (3000, 150000.0)];

    let report = verifier.verify(&stats, &fills, &equity_history).unwrap();

    assert!(!report.passed);
    assert!(report
        .violations
        .iter()
        .any(|v| v.rule_id == RuleId::LookaheadBias && v.severity == Severity::Critical));
}

#[test]
fn test_flawed_strategy_with_excessive_drawdown() {
    // Strategy exceeds max drawdown policy
    let mut constraints = PolicyConstraints::default();
    constraints.max_drawdown = Some(0.20); // 20% limit

    let verifier = CRVVerifier::new(constraints);

    let stats = BacktestStats {
        initial_equity: 100000.0,
        final_equity: 90000.0,
        total_return: -0.1,
        num_trades: 50,
        total_commission: 250.0,
        sharpe_ratio: -0.5,
        max_drawdown: 0.35, // 35% drawdown - exceeds policy!
    };

    let fills = vec![];
    let equity_history = vec![
        (1000, 100000.0),
        (2000, 120000.0), // Peak
        (3000, 78000.0),  // 35% drawdown from peak
        (4000, 90000.0),  // Partial recovery
    ];

    let report = verifier.verify(&stats, &fills, &equity_history).unwrap();

    assert!(!report.passed);
    assert!(report
        .violations
        .iter()
        .any(|v| v.rule_id == RuleId::MaxDrawdownConstraint && v.severity == Severity::High));
}

#[test]
fn test_flawed_strategy_with_bankruptcy() {
    // Strategy goes bankrupt (negative equity) - leverage too high
    let verifier = CRVVerifier::with_defaults();

    let stats = BacktestStats {
        initial_equity: 100000.0,
        final_equity: -50000.0, // Bankrupt!
        total_return: -1.5,
        num_trades: 20,
        total_commission: 100.0,
        sharpe_ratio: -5.0,
        max_drawdown: 1.5,
    };

    let fills = vec![];
    let equity_history = vec![
        (1000, 100000.0),
        (2000, 50000.0),
        (3000, -50000.0), // Bankruptcy!
    ];

    let report = verifier.verify(&stats, &fills, &equity_history).unwrap();

    assert!(!report.passed);
    assert!(report
        .violations
        .iter()
        .any(|v| v.rule_id == RuleId::MaxLeverageConstraint && v.severity == Severity::Critical));
}

#[test]
fn test_flawed_strategy_with_bad_sharpe_calculation() {
    // Strategy reports unrealistically high Sharpe ratio
    let verifier = CRVVerifier::with_defaults();

    let stats = BacktestStats {
        initial_equity: 100000.0,
        final_equity: 120000.0,
        total_return: 0.2,
        num_trades: 10,
        total_commission: 50.0,
        sharpe_ratio: 25.0, // Impossibly high!
        max_drawdown: 0.05,
    };

    let fills = vec![];
    let equity_history = vec![(1000, 100000.0), (2000, 110000.0), (3000, 120000.0)];

    let report = verifier.verify(&stats, &fills, &equity_history).unwrap();

    assert!(!report.passed);
    assert!(report
        .violations
        .iter()
        .any(|v| v.rule_id == RuleId::SharpeRatioValidation && v.severity == Severity::Medium));
}

#[test]
fn test_flawed_strategy_with_invalid_drawdown_calculation() {
    // Strategy reports max drawdown > 1.0 (impossible)
    let verifier = CRVVerifier::with_defaults();

    let stats = BacktestStats {
        initial_equity: 100000.0,
        final_equity: 50000.0,
        total_return: -0.5,
        num_trades: 5,
        total_commission: 25.0,
        sharpe_ratio: -1.0,
        max_drawdown: 2.5, // > 1.0 is invalid!
    };

    let fills = vec![];
    let equity_history = vec![(1000, 100000.0), (2000, 75000.0), (3000, 50000.0)];

    let report = verifier.verify(&stats, &fills, &equity_history).unwrap();

    assert!(!report.passed);
    assert!(report
        .violations
        .iter()
        .any(|v| v.rule_id == RuleId::MaxDrawdownValidation && v.severity == Severity::Critical));
}

#[test]
fn test_multiple_violations_detected() {
    // Strategy with multiple issues
    let verifier = CRVVerifier::with_defaults();

    let stats = BacktestStats {
        initial_equity: 100000.0,
        final_equity: 80000.0,
        total_return: -0.2,
        num_trades: 10,
        total_commission: 50.0,
        sharpe_ratio: 15.0, // Unrealistic
        max_drawdown: 0.30, // Exceeds default 25% limit
    };

    let fills = vec![];
    let equity_history = vec![
        (1000, 100000.0),
        (2000, 120000.0), // Peak
        (3000, 84000.0),  // 30% drawdown
        (4000, 80000.0),
    ];

    let report = verifier.verify(&stats, &fills, &equity_history).unwrap();

    assert!(!report.passed);
    assert!(report.violation_count() >= 2);

    // Should have both Sharpe ratio and max drawdown violations
    assert!(report
        .violations
        .iter()
        .any(|v| v.rule_id == RuleId::SharpeRatioValidation));
    assert!(report
        .violations
        .iter()
        .any(|v| v.rule_id == RuleId::MaxDrawdownConstraint));
}

#[test]
fn test_flawed_strategy_with_survivorship_bias() {
    // Strategy tested on a universe that excludes delisted stocks
    let verifier = CRVVerifier::with_defaults();

    let stats = BacktestStats {
        initial_equity: 100000.0,
        final_equity: 150000.0,
        total_return: 0.5,
        num_trades: 30,
        total_commission: 150.0,
        sharpe_ratio: 2.0,
        max_drawdown: 0.10,
    };

    let fills = vec![];
    let equity_history = vec![(1000, 100000.0), (2000, 125000.0), (3000, 150000.0)];

    // Universe had 50 stocks, 10 delisted (20%), but they were excluded
    let universe = crv_verifier::UniverseMetadata {
        total_symbols: 50,
        delisted_symbols: vec![
            "FAIL1".to_string(),
            "FAIL2".to_string(),
            "FAIL3".to_string(),
            "FAIL4".to_string(),
            "FAIL5".to_string(),
            "FAIL6".to_string(),
            "FAIL7".to_string(),
            "FAIL8".to_string(),
            "FAIL9".to_string(),
            "FAIL10".to_string(),
        ],
        traded_symbols: vec!["AAPL".to_string(), "MSFT".to_string(), "GOOGL".to_string()],
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
