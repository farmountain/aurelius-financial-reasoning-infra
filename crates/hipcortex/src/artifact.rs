use crv_verifier::CRVReport;
use schema::{BacktestStats, Bar, EquityPoint, Fill};
use serde::{Deserialize, Serialize};

/// Artifact types supported by HipCortex
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Artifact {
    Dataset(Dataset),
    StrategySpec(StrategySpec),
    BacktestConfig(BacktestConfig),
    BacktestResult(BacktestResult),
    CRVReport(CRVReportArtifact),
    Trace(Trace),
}

impl Artifact {
    /// Get the artifact type as a string
    pub fn artifact_type(&self) -> &'static str {
        match self {
            Artifact::Dataset(_) => "dataset",
            Artifact::StrategySpec(_) => "strategy_spec",
            Artifact::BacktestConfig(_) => "backtest_config",
            Artifact::BacktestResult(_) => "backtest_result",
            Artifact::CRVReport(_) => "crv_report",
            Artifact::Trace(_) => "trace",
        }
    }
}

/// Dataset artifact containing market data
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Dataset {
    pub name: String,
    pub description: String,
    pub bars: Vec<Bar>,
    pub metadata: DatasetMetadata,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct DatasetMetadata {
    pub symbols: Vec<String>,
    pub start_timestamp: i64,
    pub end_timestamp: i64,
    pub bar_count: usize,
}

/// Strategy specification artifact
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct StrategySpec {
    pub name: String,
    pub description: String,
    pub strategy_type: String,
    pub parameters: serde_json::Value,
    pub goal: String,
    pub regime_tags: Vec<String>,
}

/// Backtest configuration artifact
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct BacktestConfig {
    pub initial_cash: f64,
    pub seed: u64,
    pub strategy_hash: String,
    pub dataset_hash: String,
    pub cost_model: CostModelConfig,
    pub policy: PolicyConstraints,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CostModelConfig {
    pub model_type: String,
    pub parameters: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PolicyConstraints {
    pub max_drawdown: Option<f64>,
    pub max_leverage: Option<f64>,
    pub turnover_limit: Option<f64>,
}

/// Backtest result artifact
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestResult {
    pub config_hash: String,
    pub stats: BacktestStats,
    pub trades: Vec<Fill>,
    pub equity_curve: Vec<EquityPoint>,
    pub execution_timestamp: i64,
}

/// CRV report artifact
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CRVReportArtifact {
    pub result_hash: String,
    pub report: CRVReport,
}

/// Trace artifact for debugging and audit
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Trace {
    pub operation: String,
    pub inputs: Vec<String>,
    pub output: String,
    pub timestamp: i64,
    pub metadata: serde_json::Value,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_artifact_type_names() {
        let dataset = Artifact::Dataset(Dataset {
            name: "test".to_string(),
            description: "test".to_string(),
            bars: vec![],
            metadata: DatasetMetadata {
                symbols: vec![],
                start_timestamp: 0,
                end_timestamp: 0,
                bar_count: 0,
            },
        });
        assert_eq!(dataset.artifact_type(), "dataset");

        let strategy = Artifact::StrategySpec(StrategySpec {
            name: "test".to_string(),
            description: "test".to_string(),
            strategy_type: "ts_momentum".to_string(),
            parameters: serde_json::json!({}),
            goal: "momentum".to_string(),
            regime_tags: vec!["trending".to_string()],
        });
        assert_eq!(strategy.artifact_type(), "strategy_spec");
    }

    #[test]
    fn test_artifact_serialization() {
        let artifact = Artifact::StrategySpec(StrategySpec {
            name: "test_strategy".to_string(),
            description: "A test strategy".to_string(),
            strategy_type: "ts_momentum".to_string(),
            parameters: serde_json::json!({"lookback": 20}),
            goal: "momentum".to_string(),
            regime_tags: vec!["trending".to_string()],
        });

        let json = serde_json::to_string(&artifact).unwrap();
        let deserialized: Artifact = serde_json::from_str(&json).unwrap();
        // Just verify it serializes and deserializes without error
        assert_eq!(artifact.artifact_type(), deserialized.artifact_type());
    }
}
