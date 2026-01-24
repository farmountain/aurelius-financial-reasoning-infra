use hipcortex::{
    Artifact, BacktestConfig, BacktestResult, ContentHash, CostModelConfig, PolicyConstraints,
    Repository, StrategySpec,
};
use schema::{BacktestStats, EquityPoint};
use tempfile::TempDir;

#[test]
fn test_replay_reproducibility() {
    let temp_dir = TempDir::new().unwrap();
    let mut repo = Repository::open(temp_dir.path()).unwrap();

    // Create a strategy artifact
    let strategy = Artifact::StrategySpec(StrategySpec {
        name: "test_strategy".to_string(),
        description: "Test strategy for replay".to_string(),
        strategy_type: "ts_momentum".to_string(),
        parameters: serde_json::json!({"lookback": 20, "vol_target": 0.15}),
        goal: "momentum".to_string(),
        regime_tags: vec!["trending".to_string()],
    });

    let strategy_hash = repo.commit(&strategy, "Add test strategy", vec![]).unwrap();

    // Create a backtest config artifact
    let config = Artifact::BacktestConfig(BacktestConfig {
        initial_cash: 100000.0,
        seed: 42,
        strategy_hash: strategy_hash.as_hex().to_string(),
        dataset_hash: "fake_dataset_hash".to_string(),
        cost_model: CostModelConfig {
            model_type: "fixed_per_share".to_string(),
            parameters: serde_json::json!({"cost_per_share": 0.005}),
        },
        policy: PolicyConstraints {
            max_drawdown: Some(0.25),
            max_leverage: Some(2.0),
            turnover_limit: Some(5.0),
        },
    });

    let config_hash = repo
        .commit(
            &config,
            "Add backtest config",
            vec![strategy_hash.as_hex().to_string()],
        )
        .unwrap();

    // Create a backtest result artifact
    let result = Artifact::BacktestResult(BacktestResult {
        config_hash: config_hash.as_hex().to_string(),
        stats: BacktestStats {
            initial_equity: 100000.0,
            final_equity: 125000.0,
            total_return: 0.25,
            num_trades: 10,
            total_commission: 50.0,
            sharpe_ratio: 1.5,
            max_drawdown: 0.15,
        },
        trades: vec![],
        equity_curve: vec![
            EquityPoint {
                timestamp: 0,
                equity: 100000.0,
                cash: 100000.0,
                positions_value: 0.0,
            },
            EquityPoint {
                timestamp: 1000,
                equity: 125000.0,
                cash: 50000.0,
                positions_value: 75000.0,
            },
        ],
        execution_timestamp: 1234567890,
    });

    // Commit the result
    let result_hash = repo
        .commit(
            &result,
            "Add backtest result",
            vec![config_hash.as_hex().to_string()],
        )
        .unwrap();

    // Retrieve the result and verify it's the same
    let retrieved = repo.get(&result_hash).unwrap();

    // Verify hash stability
    let recomputed_hash = ContentHash::compute(&retrieved).unwrap();
    assert_eq!(
        result_hash.as_hex(),
        recomputed_hash.as_hex(),
        "Hash should be stable across storage and retrieval"
    );

    // Verify lineage tracking
    let history = repo.history(&result_hash).unwrap();
    assert_eq!(history.len(), 1);
    assert_eq!(history[0].parent_hashes, vec![config_hash.as_hex()]);

    // Verify we can retrieve the config from the result
    match retrieved {
        Artifact::BacktestResult(res) => {
            let retrieved_config_hash = ContentHash::from_hex(res.config_hash.clone());
            let retrieved_config = repo.get(&retrieved_config_hash).unwrap();

            match retrieved_config {
                Artifact::BacktestConfig(cfg) => {
                    assert_eq!(cfg.seed, 42);
                    assert_eq!(cfg.initial_cash, 100000.0);
                    assert_eq!(cfg.strategy_hash, strategy_hash.as_hex());
                }
                _ => panic!("Expected BacktestConfig"),
            }
        }
        _ => panic!("Expected BacktestResult"),
    }
}

#[test]
fn test_hash_stability_across_runs() {
    // Create the same artifact twice and verify hashes match
    let strategy1 = Artifact::StrategySpec(StrategySpec {
        name: "stable_strategy".to_string(),
        description: "Strategy for hash stability test".to_string(),
        strategy_type: "ts_momentum".to_string(),
        parameters: serde_json::json!({"lookback": 20}),
        goal: "momentum".to_string(),
        regime_tags: vec!["trending".to_string()],
    });

    let strategy2 = Artifact::StrategySpec(StrategySpec {
        name: "stable_strategy".to_string(),
        description: "Strategy for hash stability test".to_string(),
        strategy_type: "ts_momentum".to_string(),
        parameters: serde_json::json!({"lookback": 20}),
        goal: "momentum".to_string(),
        regime_tags: vec!["trending".to_string()],
    });

    let hash1 = ContentHash::compute(&strategy1).unwrap();
    let hash2 = ContentHash::compute(&strategy2).unwrap();

    assert_eq!(
        hash1.as_hex(),
        hash2.as_hex(),
        "Identical artifacts should have identical hashes"
    );

    // Verify hash changes when content changes
    let strategy3 = Artifact::StrategySpec(StrategySpec {
        name: "stable_strategy".to_string(),
        description: "Strategy for hash stability test".to_string(),
        strategy_type: "ts_momentum".to_string(),
        parameters: serde_json::json!({"lookback": 30}), // Different parameter
        goal: "momentum".to_string(),
        regime_tags: vec!["trending".to_string()],
    });

    let hash3 = ContentHash::compute(&strategy3).unwrap();

    assert_ne!(
        hash1.as_hex(),
        hash3.as_hex(),
        "Different artifacts should have different hashes"
    );
}

#[test]
fn test_full_replay_simulation() {
    let temp_dir = TempDir::new().unwrap();
    let mut repo = Repository::open(temp_dir.path()).unwrap();

    // Simulate a complete workflow:
    // 1. Create and commit a dataset
    // 2. Create and commit a strategy
    // 3. Create and commit a config
    // 4. Create and commit a result
    // 5. Verify we can reconstruct the entire computation graph

    let dataset = Artifact::Dataset(hipcortex::Dataset {
        name: "test_data".to_string(),
        description: "Test dataset for replay".to_string(),
        bars: vec![],
        metadata: hipcortex::artifact::DatasetMetadata {
            symbols: vec!["AAPL".to_string()],
            start_timestamp: 0,
            end_timestamp: 1000000,
            bar_count: 252,
        },
    });

    let dataset_hash = repo.commit(&dataset, "Add dataset", vec![]).unwrap();

    let strategy = Artifact::StrategySpec(StrategySpec {
        name: "momentum_strat".to_string(),
        description: "Momentum strategy".to_string(),
        strategy_type: "ts_momentum".to_string(),
        parameters: serde_json::json!({"lookback": 20}),
        goal: "momentum".to_string(),
        regime_tags: vec!["trending".to_string()],
    });

    let strategy_hash = repo.commit(&strategy, "Add strategy", vec![]).unwrap();

    let config = Artifact::BacktestConfig(BacktestConfig {
        initial_cash: 100000.0,
        seed: 42,
        strategy_hash: strategy_hash.as_hex().to_string(),
        dataset_hash: dataset_hash.as_hex().to_string(),
        cost_model: CostModelConfig {
            model_type: "zero".to_string(),
            parameters: serde_json::json!({}),
        },
        policy: PolicyConstraints {
            max_drawdown: Some(0.20),
            max_leverage: None,
            turnover_limit: None,
        },
    });

    let config_hash = repo
        .commit(
            &config,
            "Add config",
            vec![
                strategy_hash.as_hex().to_string(),
                dataset_hash.as_hex().to_string(),
            ],
        )
        .unwrap();

    let result = Artifact::BacktestResult(BacktestResult {
        config_hash: config_hash.as_hex().to_string(),
        stats: BacktestStats {
            initial_equity: 100000.0,
            final_equity: 110000.0,
            total_return: 0.10,
            num_trades: 5,
            total_commission: 0.0,
            sharpe_ratio: 1.2,
            max_drawdown: 0.08,
        },
        trades: vec![],
        equity_curve: vec![],
        execution_timestamp: 1234567890,
    });

    let result_hash = repo
        .commit(
            &result,
            "Add result",
            vec![config_hash.as_hex().to_string()],
        )
        .unwrap();

    // Now verify we can replay: walk backwards from result to reconstruct inputs
    let retrieved_result = repo.get(&result_hash).unwrap();

    match retrieved_result {
        Artifact::BacktestResult(res) => {
            // Get config
            let cfg_hash = ContentHash::from_hex(res.config_hash.clone());
            let cfg = repo.get(&cfg_hash).unwrap();

            match cfg {
                Artifact::BacktestConfig(config) => {
                    // Get strategy
                    let strat_hash = ContentHash::from_hex(config.strategy_hash.clone());
                    let strat = repo.get(&strat_hash).unwrap();
                    assert_eq!(strat.artifact_type(), "strategy_spec");

                    // Get dataset
                    let data_hash = ContentHash::from_hex(config.dataset_hash.clone());
                    let data = repo.get(&data_hash).unwrap();
                    assert_eq!(data.artifact_type(), "dataset");

                    // Verify the result hash is stable
                    let result_artifact = Artifact::BacktestResult(res);
                    let recomputed = ContentHash::compute(&result_artifact).unwrap();
                    assert_eq!(recomputed.as_hex(), result_hash.as_hex());
                }
                _ => panic!("Expected BacktestConfig"),
            }
        }
        _ => panic!("Expected BacktestResult"),
    }
}
