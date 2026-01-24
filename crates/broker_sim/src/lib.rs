#![forbid(unsafe_code)]

use anyhow::Result;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use schema::{Bar, BrokerSim, CostModel, Fill, Order, OrderType, Side};

/// Simple broker simulator that fills all market orders immediately
pub struct SimpleBroker<C: CostModel> {
    cost_model: C,
    #[allow(dead_code)]
    rng: ChaCha8Rng, // For future stochastic features, currently unused but seeded for determinism
}

impl<C: CostModel> SimpleBroker<C> {
    pub fn new(cost_model: C, seed: u64) -> Self {
        Self {
            cost_model,
            rng: ChaCha8Rng::seed_from_u64(seed),
        }
    }
}

impl<C: CostModel> BrokerSim for SimpleBroker<C> {
    fn process_orders(&mut self, orders: Vec<Order>, bar: &Bar) -> Result<Vec<Fill>> {
        let mut fills = Vec::new();

        for order in orders {
            // For now, only support market orders
            match order.order_type {
                OrderType::Market => {
                    // Fill at the close price of the bar
                    let fill_price = bar.close;

                    // Calculate commission
                    let commission = self
                        .cost_model
                        .calculate_commission(order.quantity, fill_price);

                    // Apply slippage (if any)
                    let slippage =
                        self.cost_model
                            .calculate_slippage(order.quantity, fill_price, order.side);
                    let adjusted_price = match order.side {
                        Side::Buy => fill_price + slippage,
                        Side::Sell => fill_price - slippage,
                    };

                    fills.push(Fill {
                        timestamp: bar.timestamp,
                        symbol: order.symbol.clone(),
                        side: order.side,
                        quantity: order.quantity,
                        price: adjusted_price,
                        commission,
                    });
                }
                OrderType::Limit => {
                    // Limit orders not implemented yet - would need more sophisticated logic
                    // For simplicity, skip them in this implementation
                }
            }
        }

        Ok(fills)
    }

    fn name(&self) -> &str {
        "SimpleBroker"
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    struct ZeroCost;
    impl CostModel for ZeroCost {
        fn calculate_commission(&self, _quantity: f64, _price: f64) -> f64 {
            0.0
        }
        fn calculate_slippage(&self, _quantity: f64, _price: f64, _side: Side) -> f64 {
            0.0
        }
    }

    #[test]
    fn test_market_order_execution() {
        let mut broker = SimpleBroker::new(ZeroCost, 42);

        let bar = Bar {
            timestamp: 1000,
            symbol: "AAPL".to_string(),
            open: 100.0,
            high: 102.0,
            low: 99.0,
            close: 101.0,
            volume: 10000.0,
        };

        let orders = vec![Order {
            symbol: "AAPL".to_string(),
            side: Side::Buy,
            quantity: 10.0,
            order_type: OrderType::Market,
            limit_price: None,
        }];

        let fills = broker.process_orders(orders, &bar).unwrap();

        assert_eq!(fills.len(), 1);
        assert_eq!(fills[0].symbol, "AAPL");
        assert_eq!(fills[0].quantity, 10.0);
        assert_eq!(fills[0].price, 101.0);
        assert_eq!(fills[0].commission, 0.0);
    }

    #[test]
    fn test_determinism() {
        let bar = Bar {
            timestamp: 1000,
            symbol: "AAPL".to_string(),
            open: 100.0,
            high: 102.0,
            low: 99.0,
            close: 101.0,
            volume: 10000.0,
        };

        let orders = vec![Order {
            symbol: "AAPL".to_string(),
            side: Side::Buy,
            quantity: 10.0,
            order_type: OrderType::Market,
            limit_price: None,
        }];

        // Run the same simulation twice with the same seed
        let mut broker1 = SimpleBroker::new(ZeroCost, 42);
        let fills1 = broker1.process_orders(orders.clone(), &bar).unwrap();

        let mut broker2 = SimpleBroker::new(ZeroCost, 42);
        let fills2 = broker2.process_orders(orders, &bar).unwrap();

        // Results should be identical
        assert_eq!(fills1.len(), fills2.len());
        for (f1, f2) in fills1.iter().zip(fills2.iter()) {
            assert_eq!(f1.price, f2.price);
            assert_eq!(f1.quantity, f2.quantity);
            assert_eq!(f1.commission, f2.commission);
        }
    }
}
