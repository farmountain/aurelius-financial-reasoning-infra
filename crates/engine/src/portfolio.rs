use anyhow::Result;
use schema::{Fill, Portfolio, Side};
use std::collections::HashMap;

/// Manages portfolio state and accounting
pub struct PortfolioManager {
    portfolio: Portfolio,
    realized_pnl: f64,
    total_commission: f64,
    equity_history: Vec<(i64, f64)>,
}

impl PortfolioManager {
    pub fn new(initial_cash: f64) -> Self {
        Self {
            portfolio: Portfolio::new(initial_cash),
            realized_pnl: 0.0,
            total_commission: 0.0,
            equity_history: vec![(0, initial_cash)],
        }
    }

    /// Apply a fill to the portfolio
    pub fn apply_fill(&mut self, fill: &Fill, current_prices: &HashMap<String, f64>) -> Result<()> {
        // Update timestamp
        self.portfolio.timestamp = fill.timestamp;

        // Get or create position
        let position = self.portfolio.get_position_mut(&fill.symbol);

        let old_quantity = position.quantity;
        let old_avg_price = position.avg_price;

        // Calculate new position
        let quantity_delta = match fill.side {
            Side::Buy => fill.quantity,
            Side::Sell => -fill.quantity,
        };

        let new_quantity = old_quantity + quantity_delta;

        // Handle realized PnL when closing or reducing a position
        if old_quantity.abs() > 1e-8 {
            // Check if we're closing or reducing the position (different direction)
            let is_closing = (old_quantity > 0.0 && quantity_delta < 0.0)
                || (old_quantity < 0.0 && quantity_delta > 0.0);

            if is_closing {
                // Position is being closed or reduced
                let closed_quantity = quantity_delta.abs().min(old_quantity.abs());

                let exit_price = fill.price;
                let entry_price = old_avg_price;

                let pnl = if old_quantity > 0.0 {
                    // Closing long position
                    closed_quantity * (exit_price - entry_price)
                } else {
                    // Closing short position
                    closed_quantity * (entry_price - exit_price)
                };

                self.realized_pnl += pnl;
            }
        }

        // Update position
        if new_quantity.abs() < 1e-8 {
            // Position is flat
            position.quantity = 0.0;
            position.avg_price = 0.0;
        } else {
            // Update average price for the new quantity
            if (old_quantity >= 0.0 && new_quantity > old_quantity)
                || (old_quantity <= 0.0 && new_quantity < old_quantity)
            {
                // Adding to position - update average price
                let old_value = old_quantity * old_avg_price;
                let new_value = quantity_delta * fill.price;
                position.avg_price = (old_value + new_value) / new_quantity;
            }
            // If reducing position but not flipping, keep the same avg price
            position.quantity = new_quantity;
        }

        // Update cash: pay for buys, receive for sells, always pay commission
        let cash_flow = match fill.side {
            Side::Buy => -(fill.quantity * fill.price + fill.commission),
            Side::Sell => fill.quantity * fill.price - fill.commission,
        };
        self.portfolio.cash += cash_flow;
        self.total_commission += fill.commission;

        // Update equity
        self.update_equity(current_prices);

        Ok(())
    }

    /// Update equity based on current market prices
    pub fn update_equity(&mut self, current_prices: &HashMap<String, f64>) {
        let mut positions_value = 0.0;
        for position in self.portfolio.positions.values() {
            if let Some(&price) = current_prices.get(&position.symbol) {
                positions_value += position.market_value(price);
            }
        }
        self.portfolio.equity = self.portfolio.cash + positions_value;
        self.equity_history
            .push((self.portfolio.timestamp, self.portfolio.equity));
    }

    pub fn portfolio(&self) -> &Portfolio {
        &self.portfolio
    }

    pub fn realized_pnl(&self) -> f64 {
        self.realized_pnl
    }

    pub fn total_commission(&self) -> f64 {
        self.total_commission
    }

    pub fn equity_history(&self) -> &[(i64, f64)] {
        &self.equity_history
    }

    pub fn unrealized_pnl(&self, current_prices: &HashMap<String, f64>) -> f64 {
        let mut unrealized = 0.0;
        for position in self.portfolio.positions.values() {
            if let Some(&price) = current_prices.get(&position.symbol) {
                unrealized += position.unrealized_pnl(price);
            }
        }
        unrealized
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_buy_and_hold() {
        let mut pm = PortfolioManager::new(10000.0);
        let mut prices = HashMap::new();
        prices.insert("AAPL".to_string(), 100.0);

        // Buy 10 shares at $100
        let fill = Fill {
            timestamp: 1000,
            symbol: "AAPL".to_string(),
            side: Side::Buy,
            quantity: 10.0,
            price: 100.0,
            commission: 5.0,
        };

        pm.apply_fill(&fill, &prices).unwrap();

        let portfolio = pm.portfolio();
        assert_eq!(portfolio.cash, 10000.0 - 1000.0 - 5.0);

        let position = portfolio.get_position("AAPL").unwrap();
        assert_eq!(position.quantity, 10.0);
        assert_eq!(position.avg_price, 100.0);

        // Check equity
        assert_eq!(portfolio.equity, 10000.0 - 5.0); // Still worth the same, just paid commission
    }

    #[test]
    fn test_buy_and_sell() {
        let mut pm = PortfolioManager::new(10000.0);
        let mut prices = HashMap::new();
        prices.insert("AAPL".to_string(), 100.0);

        // Buy 10 shares at $100
        let buy_fill = Fill {
            timestamp: 1000,
            symbol: "AAPL".to_string(),
            side: Side::Buy,
            quantity: 10.0,
            price: 100.0,
            commission: 5.0,
        };
        pm.apply_fill(&buy_fill, &prices).unwrap();

        // Sell 10 shares at $110
        prices.insert("AAPL".to_string(), 110.0);
        let sell_fill = Fill {
            timestamp: 2000,
            symbol: "AAPL".to_string(),
            side: Side::Sell,
            quantity: 10.0,
            price: 110.0,
            commission: 5.0,
        };
        pm.apply_fill(&sell_fill, &prices).unwrap();

        // Should have realized profit of $100 (10 shares * $10 gain)
        assert_eq!(pm.realized_pnl(), 100.0);

        // Total commission should be $10
        assert_eq!(pm.total_commission(), 10.0);

        // Cash should be initial + profit - commission
        let portfolio = pm.portfolio();
        assert_eq!(portfolio.cash, 10000.0 + 100.0 - 10.0);

        // Position should be flat
        let position = portfolio.get_position("AAPL").unwrap();
        assert!(position.is_flat());
    }

    #[test]
    fn test_accounting_invariant() {
        // Test: Initial equity = cash + positions value at all times (minus commissions)
        let mut pm = PortfolioManager::new(10000.0);
        let initial_equity = 10000.0;

        let mut prices = HashMap::new();
        prices.insert("AAPL".to_string(), 100.0);

        // Buy 10 shares
        let buy_fill = Fill {
            timestamp: 1000,
            symbol: "AAPL".to_string(),
            side: Side::Buy,
            quantity: 10.0,
            price: 100.0,
            commission: 5.0,
        };
        pm.apply_fill(&buy_fill, &prices).unwrap();

        // Check invariant: equity = initial - commissions (at same price)
        let portfolio = pm.portfolio();
        assert!((portfolio.equity - (initial_equity - 5.0)).abs() < 0.01);
        let cash = portfolio.cash;

        // Price goes up
        prices.insert("AAPL".to_string(), 110.0);
        pm.update_equity(&prices);

        // Equity should reflect unrealized gain
        let expected_equity = cash + 10.0 * 110.0;
        assert!((pm.portfolio().equity - expected_equity).abs() < 0.01);
    }

    #[test]
    fn test_partial_close() {
        let mut pm = PortfolioManager::new(10000.0);
        let mut prices = HashMap::new();
        prices.insert("AAPL".to_string(), 100.0);

        // Buy 10 shares at $100
        let buy_fill = Fill {
            timestamp: 1000,
            symbol: "AAPL".to_string(),
            side: Side::Buy,
            quantity: 10.0,
            price: 100.0,
            commission: 5.0,
        };
        pm.apply_fill(&buy_fill, &prices).unwrap();

        // Sell 5 shares at $110
        prices.insert("AAPL".to_string(), 110.0);
        let sell_fill = Fill {
            timestamp: 2000,
            symbol: "AAPL".to_string(),
            side: Side::Sell,
            quantity: 5.0,
            price: 110.0,
            commission: 5.0,
        };
        pm.apply_fill(&sell_fill, &prices).unwrap();

        // Should have realized profit of $50 (5 shares * $10 gain)
        assert_eq!(pm.realized_pnl(), 50.0);

        // Should still hold 5 shares
        let position = pm.portfolio().get_position("AAPL").unwrap();
        assert_eq!(position.quantity, 5.0);
        assert_eq!(position.avg_price, 100.0); // Average price unchanged
    }
}
