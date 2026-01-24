use crate::portfolio::PortfolioManager;
use anyhow::Result;
use schema::{BrokerSim, DataFeed, Fill, Strategy};
use std::collections::HashMap;

/// Event-driven backtest engine
pub struct BacktestEngine<D: DataFeed, S: Strategy, B: BrokerSim> {
    data_feed: D,
    strategy: S,
    broker: B,
    portfolio_manager: PortfolioManager,
    fills: Vec<Fill>,
    current_prices: HashMap<String, f64>,
}

impl<D: DataFeed, S: Strategy, B: BrokerSim> BacktestEngine<D, S, B> {
    pub fn new(data_feed: D, strategy: S, broker: B, initial_cash: f64) -> Self {
        Self {
            data_feed,
            strategy,
            broker,
            portfolio_manager: PortfolioManager::new(initial_cash),
            fills: Vec::new(),
            current_prices: HashMap::new(),
        }
    }

    /// Run the backtest bar-by-bar
    pub fn run(&mut self) -> Result<()> {
        loop {
            // Get next bar
            let bar = match self.data_feed.next_bar() {
                Some(b) => b,
                None => break, // No more data
            };

            // Update current prices
            self.current_prices.insert(bar.symbol.clone(), bar.close);

            // Let strategy generate orders based on current bar and portfolio state
            let orders = self
                .strategy
                .on_bar(&bar, self.portfolio_manager.portfolio());

            // Process orders through broker
            if !orders.is_empty() {
                let new_fills = self.broker.process_orders(orders, &bar)?;

                // Apply fills to portfolio
                for fill in &new_fills {
                    self.portfolio_manager
                        .apply_fill(fill, &self.current_prices)?;
                }

                self.fills.extend(new_fills);
            }

            // Update equity at end of bar
            self.portfolio_manager.update_equity(&self.current_prices);
        }

        Ok(())
    }

    /// Get the fills (trades) from the backtest
    pub fn fills(&self) -> &[Fill] {
        &self.fills
    }

    /// Get the equity history
    pub fn equity_history(&self) -> &[(i64, f64)] {
        self.portfolio_manager.equity_history()
    }

    /// Get realized PnL
    pub fn realized_pnl(&self) -> f64 {
        self.portfolio_manager.realized_pnl()
    }

    /// Get unrealized PnL
    pub fn unrealized_pnl(&self) -> f64 {
        self.portfolio_manager.unrealized_pnl(&self.current_prices)
    }

    /// Get total commission
    pub fn total_commission(&self) -> f64 {
        self.portfolio_manager.total_commission()
    }

    /// Get number of trades
    pub fn num_trades(&self) -> usize {
        self.fills.len()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::data_feed::VecDataFeed;
    use broker_sim::SimpleBroker;
    use cost::ZeroCost;
    use schema::{Bar, Order, OrderType, Portfolio, Side};

    // Simple buy-and-hold strategy for testing
    struct BuyAndHoldStrategy {
        symbol: String,
        bought: bool,
    }

    impl BuyAndHoldStrategy {
        fn new(symbol: String) -> Self {
            Self {
                symbol,
                bought: false,
            }
        }
    }

    impl Strategy for BuyAndHoldStrategy {
        fn on_bar(&mut self, bar: &Bar, _portfolio: &Portfolio) -> Vec<Order> {
            if !self.bought && bar.symbol == self.symbol {
                self.bought = true;
                vec![Order {
                    symbol: self.symbol.clone(),
                    side: Side::Buy,
                    quantity: 10.0,
                    order_type: OrderType::Market,
                    limit_price: None,
                }]
            } else {
                vec![]
            }
        }

        fn name(&self) -> &str {
            "BuyAndHold"
        }
    }

    #[test]
    fn test_simple_backtest() {
        let bars = vec![
            Bar {
                timestamp: 1000,
                symbol: "AAPL".to_string(),
                open: 100.0,
                high: 102.0,
                low: 99.0,
                close: 101.0,
                volume: 10000.0,
            },
            Bar {
                timestamp: 2000,
                symbol: "AAPL".to_string(),
                open: 101.0,
                high: 103.0,
                low: 100.0,
                close: 102.0,
                volume: 11000.0,
            },
        ];

        let data_feed = VecDataFeed::new(bars);
        let strategy = BuyAndHoldStrategy::new("AAPL".to_string());
        let broker = SimpleBroker::new(ZeroCost, 42);

        let mut engine = BacktestEngine::new(data_feed, strategy, broker, 10000.0);
        engine.run().unwrap();

        // Should have one fill (the buy)
        assert_eq!(engine.num_trades(), 1);

        // Equity should be initial cash - purchase + current value
        let equity_history = engine.equity_history();
        assert!(equity_history.len() >= 2);
    }

    #[test]
    fn test_deterministic_backtest() {
        use sha2::{Digest, Sha256};

        let bars = vec![
            Bar {
                timestamp: 1000,
                symbol: "AAPL".to_string(),
                open: 100.0,
                high: 102.0,
                low: 99.0,
                close: 101.0,
                volume: 10000.0,
            },
            Bar {
                timestamp: 2000,
                symbol: "AAPL".to_string(),
                open: 101.0,
                high: 103.0,
                low: 100.0,
                close: 102.0,
                volume: 11000.0,
            },
        ];

        // Run backtest 3 times with same seed
        let mut hashes = Vec::new();

        for _ in 0..3 {
            let data_feed = VecDataFeed::new(bars.clone());
            let strategy = BuyAndHoldStrategy::new("AAPL".to_string());
            let broker = SimpleBroker::new(ZeroCost, 42); // Same seed

            let mut engine = BacktestEngine::new(data_feed, strategy, broker, 10000.0);
            engine.run().unwrap();

            // Create a hash of the results
            let mut hasher = Sha256::new();

            // Hash equity history
            for (timestamp, equity) in engine.equity_history() {
                hasher.update(timestamp.to_le_bytes());
                hasher.update(equity.to_le_bytes());
            }

            // Hash fills
            for fill in engine.fills() {
                hasher.update(fill.timestamp.to_le_bytes());
                hasher.update(fill.quantity.to_le_bytes());
                hasher.update(fill.price.to_le_bytes());
            }

            let hash = hasher.finalize();
            hashes.push(hash);
        }

        // All three hashes should be identical
        assert_eq!(hashes[0], hashes[1]);
        assert_eq!(hashes[1], hashes[2]);
    }

    #[test]
    fn test_empty_backtest() {
        let bars = vec![];
        let data_feed = VecDataFeed::new(bars);
        let strategy = BuyAndHoldStrategy::new("AAPL".to_string());
        let broker = SimpleBroker::new(ZeroCost, 42);

        let mut engine = BacktestEngine::new(data_feed, strategy, broker, 10000.0);
        engine.run().unwrap();

        assert_eq!(engine.num_trades(), 0);
    }
}
