/// Golden file tests for CRV report JSON structure
use crv_verifier::{CRVVerifier, PolicyConstraints};
use schema::{BacktestStats, Fill};
use std::fs;
use std::path::PathBuf;

fn get_golden_file_path(filename: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests")
        .join("golden_files")
        .join(filename)
}

#[test]
fn test_golden_passing_backtest() {
    let verifier = CRVVerifier::with_defaults();

    let stats = BacktestStats {
        initial_equity: 100000.0,
        final_equity: 110000.0,
        total_return: 0.1,
        num_trades: 10,
        total_commission: 50.0,
        sharpe_ratio: 1.5,
        max_drawdown: 0.05,
    };

    let fills: Vec<Fill> = vec![];
    let equity_history = vec![
        (1000, 100000.0),
        (2000, 105000.0), // Peak
        (3000, 99750.0),  // 5% drawdown from peak
        (4000, 110000.0), // Recovery
    ];

    let report = verifier.verify(&stats, &fills, &equity_history).unwrap();

    // Serialize to JSON
    let json = serde_json::to_string_pretty(&report).unwrap();

    // Read golden file
    let golden_path = get_golden_file_path("passing_backtest.json");
    let golden_json = fs::read_to_string(&golden_path).expect("Failed to read golden file");

    // Parse both to compare structure
    let report_value: serde_json::Value = serde_json::from_str(&json).unwrap();
    let golden_value: serde_json::Value = serde_json::from_str(&golden_json).unwrap();

    // Check structure matches (passed and empty violations)
    assert_eq!(report_value["passed"], golden_value["passed"]);
    assert_eq!(report_value["violations"], golden_value["violations"]);

    // Verify it's a valid passing report
    assert!(report.passed);
    assert_eq!(report.violation_count(), 0);
}

#[test]
fn test_golden_excessive_drawdown() {
    let verifier = CRVVerifier::with_defaults();

    let stats = BacktestStats {
        initial_equity: 100000.0,
        final_equity: 90000.0,
        total_return: -0.1,
        num_trades: 50,
        total_commission: 250.0,
        sharpe_ratio: -0.5,
        max_drawdown: 0.35, // 35% drawdown - exceeds 25% limit
    };

    let fills: Vec<Fill> = vec![];
    let equity_history = vec![
        (1000, 100000.0),
        (2000, 120000.0), // Peak
        (3000, 78000.0),  // 35% drawdown from peak
    ];

    let report = verifier.verify(&stats, &fills, &equity_history).unwrap();

    // Serialize to JSON
    let json = serde_json::to_string_pretty(&report).unwrap();

    // Read golden file
    let golden_path = get_golden_file_path("excessive_drawdown.json");
    let golden_json = fs::read_to_string(&golden_path).expect("Failed to read golden file");

    // Parse both to compare structure
    let report_value: serde_json::Value = serde_json::from_str(&json).unwrap();
    let golden_value: serde_json::Value = serde_json::from_str(&golden_json).unwrap();

    // Check structure matches
    assert_eq!(report_value["passed"], golden_value["passed"]);
    assert!(!report.passed);

    // Verify violation structure
    let violations = report_value["violations"].as_array().unwrap();
    assert_eq!(violations.len(), 1);

    let violation = &violations[0];
    assert_eq!(violation["rule_id"], "max_drawdown_constraint");
    assert_eq!(violation["severity"], "high");
    assert!(violation["message"].as_str().unwrap().contains("35.00%"));
    assert!(violation["message"].as_str().unwrap().contains("25.00%"));

    // Verify evidence array exists
    let evidence = violation["evidence"].as_array().unwrap();
    assert_eq!(evidence.len(), 2);
}

#[test]
fn test_report_json_schema_structure() {
    // Test that all reports follow the expected JSON schema
    let verifier = CRVVerifier::with_defaults();

    let stats = BacktestStats {
        initial_equity: 100000.0,
        final_equity: 110000.0,
        total_return: 0.1,
        num_trades: 10,
        total_commission: 50.0,
        sharpe_ratio: 1.5,
        max_drawdown: 0.05,
    };

    let fills: Vec<Fill> = vec![];
    let equity_history = vec![
        (1000, 100000.0),
        (2000, 105000.0),
        (3000, 99750.0),
        (4000, 110000.0),
    ];

    let report = verifier.verify(&stats, &fills, &equity_history).unwrap();
    let json = serde_json::to_string_pretty(&report).unwrap();
    let value: serde_json::Value = serde_json::from_str(&json).unwrap();

    // Verify required top-level fields
    assert!(value.get("timestamp").is_some());
    assert!(value.get("violations").is_some());
    assert!(value.get("passed").is_some());

    // Verify types
    assert!(value["timestamp"].is_i64());
    assert!(value["violations"].is_array());
    assert!(value["passed"].is_boolean());
}
