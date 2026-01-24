use schema::{Bar, Order, OrderType, Portfolio, Side, Strategy};
use std::collections::VecDeque;

/// Time-series momentum strategy with volatility targeting
pub struct TsMomentumStrategy {
    symbol: String,
    lookback: usize,
    vol_target: f64,
    vol_lookback: usize,
    price_history: VecDeque<f64>,
    return_history: VecDeque<f64>,
}

impl TsMomentumStrategy {
    pub fn new(symbol: String, lookback: usize, vol_target: f64, vol_lookback: usize) -> Self {
        Self {
            symbol,
            lookback,
            vol_target,
            vol_lookback,
            price_history: VecDeque::new(),
            return_history: VecDeque::new(),
        }
    }

    fn calculate_momentum(&self) -> Option<f64> {
        if self.price_history.len() < self.lookback {
            return None;
        }
        let start_price = self.price_history[self.price_history.len() - self.lookback];
        let end_price = self.price_history[self.price_history.len() - 1];
        Some((end_price - start_price) / start_price)
    }

    fn calculate_volatility(&self) -> Option<f64> {
        if self.return_history.len() < self.vol_lookback {
            return None;
        }
        let recent_returns: Vec<f64> = self
            .return_history
            .iter()
            .rev()
            .take(self.vol_lookback)
            .copied()
            .collect();

        let mean = recent_returns.iter().sum::<f64>() / recent_returns.len() as f64;
        let variance = recent_returns
            .iter()
            .map(|r| (r - mean).powi(2))
            .sum::<f64>()
            / recent_returns.len() as f64;
        Some(variance.sqrt())
    }

    fn calculate_target_position(&self, current_price: f64, portfolio: &Portfolio) -> Option<f64> {
        let momentum = self.calculate_momentum()?;
        let volatility = self.calculate_volatility()?;

        if volatility < 1e-8 {
            return Some(0.0);
        }

        // Calculate position size based on volatility targeting
        // target_notional = equity * vol_target / volatility
        // position_size = target_notional / price
        let target_notional = portfolio.equity * self.vol_target / volatility;
        let target_shares = target_notional / current_price;

        // Apply momentum signal: positive momentum = long, negative = short
        let signal = if momentum > 0.01 {
            1.0
        } else if momentum < -0.01 {
            -1.0
        } else {
            0.0
        };

        Some(target_shares * signal)
    }
}

impl Strategy for TsMomentumStrategy {
    fn on_bar(&mut self, bar: &Bar, portfolio: &Portfolio) -> Vec<Order> {
        if bar.symbol != self.symbol {
            return vec![];
        }

        // Update price history
        self.price_history.push_back(bar.close);
        if self.price_history.len() > self.lookback + self.vol_lookback {
            self.price_history.pop_front();
        }

        // Calculate return
        if self.price_history.len() >= 2 {
            let prev_price = self.price_history[self.price_history.len() - 2];
            let curr_price = bar.close;
            let ret = (curr_price - prev_price) / prev_price;
            self.return_history.push_back(ret);
            if self.return_history.len() > self.vol_lookback {
                self.return_history.pop_front();
            }
        }

        // Get current position
        let current_position = portfolio
            .get_position(&self.symbol)
            .map(|p| p.quantity)
            .unwrap_or(0.0);

        // Calculate target position
        let target_position = match self.calculate_target_position(bar.close, portfolio) {
            Some(pos) => pos,
            None => return vec![], // Not enough data yet
        };

        // Generate order if position needs adjustment
        let position_delta = target_position - current_position;
        if position_delta.abs() > 0.1 {
            // Only trade if delta is significant
            let (side, quantity) = if position_delta > 0.0 {
                (Side::Buy, position_delta)
            } else {
                (Side::Sell, -position_delta)
            };

            vec![Order {
                symbol: self.symbol.clone(),
                side,
                quantity,
                order_type: OrderType::Market,
                limit_price: None,
            }]
        } else {
            vec![]
        }
    }

    fn name(&self) -> &str {
        "TsMomentum"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ts_momentum_basic() {
        let mut strategy = TsMomentumStrategy::new("AAPL".to_string(), 5, 0.1, 5);
        let portfolio = Portfolio::new(10000.0);

        // Feed some bars
        for i in 0..10 {
            let bar = Bar {
                timestamp: i * 1000,
                symbol: "AAPL".to_string(),
                open: 100.0 + i as f64,
                high: 102.0 + i as f64,
                low: 99.0 + i as f64,
                close: 101.0 + i as f64,
                volume: 10000.0,
            };

            let orders = strategy.on_bar(&bar, &portfolio);
            // Orders may or may not be generated depending on the signal
            if !orders.is_empty() {
                assert!(orders[0].quantity > 0.0);
            }
        }
    }

    #[test]
    fn test_strategy_determinism() {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let bars: Vec<Bar> = (0..20)
            .map(|i| Bar {
                timestamp: i * 1000,
                symbol: "AAPL".to_string(),
                open: 100.0 + i as f64 * 0.5,
                high: 102.0 + i as f64 * 0.5,
                low: 99.0 + i as f64 * 0.5,
                close: 101.0 + i as f64 * 0.5,
                volume: 10000.0,
            })
            .collect();

        let mut hashes = Vec::new();

        for _ in 0..3 {
            let mut strategy = TsMomentumStrategy::new("AAPL".to_string(), 5, 0.1, 5);
            let portfolio = Portfolio::new(10000.0);

            let mut hasher = DefaultHasher::new();
            for bar in &bars {
                let orders = strategy.on_bar(bar, &portfolio);
                orders.len().hash(&mut hasher);
                for order in orders {
                    order.quantity.to_bits().hash(&mut hasher);
                }
            }

            hashes.push(hasher.finish());
        }

        // All runs should produce the same hash
        assert_eq!(hashes[0], hashes[1]);
        assert_eq!(hashes[1], hashes[2]);
    }
}
