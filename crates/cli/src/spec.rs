use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestSpec {
    pub initial_cash: f64,
    pub seed: u64,
    pub strategy: StrategySpec,
    pub cost_model: CostModelSpec,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum StrategySpec {
    #[serde(rename = "ts_momentum")]
    TsMomentum {
        symbol: String,
        lookback: usize,
        vol_target: f64,
        vol_lookback: usize,
    },
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type")]
pub enum CostModelSpec {
    #[serde(rename = "fixed_per_share")]
    FixedPerShare {
        cost_per_share: f64,
        minimum_commission: f64,
    },
    #[serde(rename = "percentage")]
    Percentage {
        percentage: f64,
        minimum_commission: f64,
    },
    #[serde(rename = "zero")]
    Zero,
}
