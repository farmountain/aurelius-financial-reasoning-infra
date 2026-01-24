#![forbid(unsafe_code)]

use schema::{CostModel, Side};
use serde::{Deserialize, Serialize};

/// Fixed commission per share with optional minimum
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FixedPerShareCost {
    pub cost_per_share: f64,
    pub minimum_commission: f64,
}

impl FixedPerShareCost {
    pub fn new(cost_per_share: f64, minimum_commission: f64) -> Self {
        Self {
            cost_per_share,
            minimum_commission,
        }
    }
}

impl Default for FixedPerShareCost {
    fn default() -> Self {
        Self {
            cost_per_share: 0.005,   // $0.005 per share
            minimum_commission: 1.0, // $1 minimum
        }
    }
}

impl CostModel for FixedPerShareCost {
    fn calculate_commission(&self, quantity: f64, _price: f64) -> f64 {
        let commission = quantity.abs() * self.cost_per_share;
        commission.max(self.minimum_commission)
    }

    fn calculate_slippage(&self, _quantity: f64, _price: f64, _side: Side) -> f64 {
        // No slippage in this simple model
        0.0
    }
}

/// Percentage-based commission
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PercentageCost {
    pub percentage: f64, // e.g., 0.001 for 0.1%
    pub minimum_commission: f64,
}

impl PercentageCost {
    pub fn new(percentage: f64, minimum_commission: f64) -> Self {
        Self {
            percentage,
            minimum_commission,
        }
    }
}

impl Default for PercentageCost {
    fn default() -> Self {
        Self {
            percentage: 0.001,       // 0.1%
            minimum_commission: 1.0, // $1 minimum
        }
    }
}

impl CostModel for PercentageCost {
    fn calculate_commission(&self, quantity: f64, price: f64) -> f64 {
        let notional = quantity.abs() * price;
        let commission = notional * self.percentage;
        commission.max(self.minimum_commission)
    }

    fn calculate_slippage(&self, _quantity: f64, _price: f64, _side: Side) -> f64 {
        // No slippage in this simple model
        0.0
    }
}

/// Zero cost model (for testing)
#[derive(Debug, Clone, Default, Serialize, Deserialize)]
pub struct ZeroCost;

impl CostModel for ZeroCost {
    fn calculate_commission(&self, _quantity: f64, _price: f64) -> f64 {
        0.0
    }

    fn calculate_slippage(&self, _quantity: f64, _price: f64, _side: Side) -> f64 {
        0.0
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fixed_per_share_commission() {
        let cost = FixedPerShareCost::new(0.01, 5.0);

        // Small trade - should use minimum
        assert_eq!(cost.calculate_commission(100.0, 50.0), 5.0);

        // Large trade - should exceed minimum
        assert_eq!(cost.calculate_commission(1000.0, 50.0), 10.0);
    }

    #[test]
    fn test_percentage_commission() {
        let cost = PercentageCost::new(0.001, 1.0);

        // $5000 notional at 0.1% = $5
        assert_eq!(cost.calculate_commission(100.0, 50.0), 5.0);

        // Small trade - should use minimum
        assert_eq!(cost.calculate_commission(10.0, 5.0), 1.0);
    }

    #[test]
    fn test_zero_cost() {
        let cost = ZeroCost;
        assert_eq!(cost.calculate_commission(100.0, 50.0), 0.0);
        assert_eq!(cost.calculate_slippage(100.0, 50.0, Side::Buy), 0.0);
    }

    #[test]
    fn test_commission_sanity() {
        let costs: Vec<Box<dyn CostModel>> = vec![
            Box::new(FixedPerShareCost::default()),
            Box::new(PercentageCost::default()),
            Box::new(ZeroCost),
        ];

        for cost_model in costs {
            // Commission should always be non-negative
            let comm1 = cost_model.calculate_commission(100.0, 50.0);
            assert!(comm1 >= 0.0, "Commission should be non-negative");

            // Commission should scale with quantity (or stay at minimum)
            let comm2 = cost_model.calculate_commission(1000.0, 50.0);
            assert!(
                comm2 >= comm1,
                "Commission should not decrease with quantity"
            );

            // Slippage should be zero or small
            let slippage = cost_model.calculate_slippage(100.0, 50.0, Side::Buy);
            assert!(slippage.abs() < 10.0, "Slippage should be reasonable");
        }
    }
}
