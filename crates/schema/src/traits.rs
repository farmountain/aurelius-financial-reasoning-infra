use crate::types::{Bar, Fill, Order, Portfolio};
use anyhow::Result;

/// Trait for providing market data
pub trait DataFeed {
    /// Get the next bar. Returns None when data is exhausted.
    fn next_bar(&mut self) -> Option<Bar>;

    /// Reset the data feed to the beginning
    fn reset(&mut self);
}

/// Trait for trading strategies
pub trait Strategy {
    /// Called when a new bar arrives. Strategy can return orders to submit.
    fn on_bar(&mut self, bar: &Bar, portfolio: &Portfolio) -> Vec<Order>;

    /// Get strategy name
    fn name(&self) -> &str;
}

/// Trait for simulating broker execution
pub trait BrokerSim {
    /// Process orders and return fills
    fn process_orders(&mut self, orders: Vec<Order>, bar: &Bar) -> Result<Vec<Fill>>;

    /// Get broker name
    fn name(&self) -> &str;
}

/// Trait for calculating trading costs
pub trait CostModel {
    /// Calculate commission for a trade
    fn calculate_commission(&self, quantity: f64, price: f64) -> f64;

    /// Calculate slippage (price impact)
    fn calculate_slippage(&self, quantity: f64, price: f64, side: crate::types::Side) -> f64;
}

// Implement CostModel for Box<dyn CostModel> to allow dynamic dispatch
impl CostModel for Box<dyn CostModel> {
    fn calculate_commission(&self, quantity: f64, price: f64) -> f64 {
        (**self).calculate_commission(quantity, price)
    }

    fn calculate_slippage(&self, quantity: f64, price: f64, side: crate::types::Side) -> f64 {
        (**self).calculate_slippage(quantity, price, side)
    }
}
