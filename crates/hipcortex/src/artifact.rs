use crv_verifier::CRVReport;
use schema::{
    BacktestStats, Bar, EquityPoint, FidelityTier, Fill, LatencyClass, QualityFlag,
    TransformationStep,
};
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
    #[serde(default = "default_provider")]
    pub provider: String,
    #[serde(default = "default_venue_class")]
    pub venue_class: String,
    #[serde(default = "default_timezone_calendar")]
    pub timezone_calendar: String,
    #[serde(default = "default_adjustment_policy")]
    pub adjustment_policy: String,
    #[serde(default = "default_fidelity_tier")]
    pub fidelity_tier: FidelityTier,
    #[serde(default = "default_latency_class")]
    pub latency_class: LatencyClass,
    #[serde(default)]
    pub quality_flags: Vec<QualityFlag>,
    #[serde(default)]
    pub transform_lineage: Vec<TransformationStep>,
}

impl DatasetMetadata {
    pub fn validate_provenance(&self) -> anyhow::Result<()> {
        if self.provider.trim().is_empty() {
            anyhow::bail!("dataset metadata missing provider");
        }
        if self.venue_class.trim().is_empty() {
            anyhow::bail!("dataset metadata missing venue_class");
        }
        if self.timezone_calendar.trim().is_empty() {
            anyhow::bail!("dataset metadata missing timezone_calendar");
        }
        if self.adjustment_policy.trim().is_empty() {
            anyhow::bail!("dataset metadata missing adjustment_policy");
        }
        Ok(())
    }

    pub fn assert_comparable_with(&self, other: &Self) -> anyhow::Result<()> {
        if self.fidelity_tier != other.fidelity_tier {
            anyhow::bail!(
                "non-equivalent comparison: fidelity tier mismatch ({:?} vs {:?})",
                self.fidelity_tier,
                other.fidelity_tier
            );
        }
        if self.adjustment_policy != other.adjustment_policy {
            anyhow::bail!(
                "non-equivalent comparison: adjustment policy mismatch ({} vs {})",
                self.adjustment_policy,
                other.adjustment_policy
            );
        }
        if self.timezone_calendar != other.timezone_calendar {
            anyhow::bail!(
                "non-equivalent comparison: timezone/calendar mismatch ({} vs {})",
                self.timezone_calendar,
                other.timezone_calendar
            );
        }

        Ok(())
    }
}

fn default_provider() -> String {
    "unknown".to_string()
}

fn default_venue_class() -> String {
    "unknown".to_string()
}

fn default_timezone_calendar() -> String {
    "UTC/24x7".to_string()
}

fn default_adjustment_policy() -> String {
    "unadjusted".to_string()
}

fn default_fidelity_tier() -> FidelityTier {
    FidelityTier::Tier1Bar
}

fn default_latency_class() -> LatencyClass {
    LatencyClass::Unknown
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
                provider: "test-provider".to_string(),
                venue_class: "equities".to_string(),
                timezone_calendar: "UTC/XNYS".to_string(),
                adjustment_policy: "split_dividend_adjusted".to_string(),
                fidelity_tier: FidelityTier::Tier1Bar,
                latency_class: LatencyClass::EndOfDay,
                quality_flags: vec![],
                transform_lineage: vec![],
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

    #[test]
    fn test_dataset_provenance_validation_and_comparability() {
        let metadata_a = DatasetMetadata {
            symbols: vec!["AAPL".to_string()],
            start_timestamp: 1,
            end_timestamp: 2,
            bar_count: 1,
            provider: "polygon".to_string(),
            venue_class: "equities".to_string(),
            timezone_calendar: "UTC/XNYS".to_string(),
            adjustment_policy: "split_dividend_adjusted".to_string(),
            fidelity_tier: FidelityTier::Tier1Bar,
            latency_class: LatencyClass::Delayed,
            quality_flags: vec![QualityFlag::DerivedValue],
            transform_lineage: vec![TransformationStep {
                step: "normalize".to_string(),
                details: "legacy parquet bridge".to_string(),
            }],
        };

        let metadata_b = DatasetMetadata {
            provider: "alpaca".to_string(),
            ..metadata_a.clone()
        };

        assert!(metadata_a.validate_provenance().is_ok());
        assert!(metadata_a.assert_comparable_with(&metadata_b).is_ok());

        let metadata_c = DatasetMetadata {
            fidelity_tier: FidelityTier::Tier3OrderBook,
            ..metadata_a
        };
        assert!(metadata_b.assert_comparable_with(&metadata_c).is_err());
    }
}
