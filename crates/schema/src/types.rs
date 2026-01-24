use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// A single OHLCV bar
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Bar {
    pub timestamp: i64, // Unix timestamp in seconds (deterministic)
    pub symbol: String,
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: f64,
}

/// Order side
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Side {
    Buy,
    Sell,
}

/// Order type
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum OrderType {
    Market,
    Limit,
}

/// An order to be submitted
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Order {
    pub symbol: String,
    pub side: Side,
    pub quantity: f64,
    pub order_type: OrderType,
    pub limit_price: Option<f64>,
}

/// A filled order (trade)
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Fill {
    pub timestamp: i64,
    pub symbol: String,
    pub side: Side,
    pub quantity: f64,
    pub price: f64,
    pub commission: f64,
}

/// Current position for a symbol
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Position {
    pub symbol: String,
    pub quantity: f64, // positive for long, negative for short
    pub avg_price: f64,
}

impl Position {
    pub fn new(symbol: String) -> Self {
        Self {
            symbol,
            quantity: 0.0,
            avg_price: 0.0,
        }
    }

    pub fn is_flat(&self) -> bool {
        self.quantity.abs() < 1e-8
    }

    pub fn market_value(&self, current_price: f64) -> f64 {
        self.quantity * current_price
    }

    pub fn unrealized_pnl(&self, current_price: f64) -> f64 {
        self.quantity * (current_price - self.avg_price)
    }
}

/// Portfolio state at a point in time
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Portfolio {
    pub timestamp: i64,
    pub cash: f64,
    pub positions: HashMap<String, Position>,
    pub equity: f64, // cash + sum of position market values
}

impl Portfolio {
    pub fn new(initial_cash: f64) -> Self {
        Self {
            timestamp: 0,
            cash: initial_cash,
            positions: HashMap::new(),
            equity: initial_cash,
        }
    }

    pub fn get_position(&self, symbol: &str) -> Option<&Position> {
        self.positions.get(symbol)
    }

    pub fn get_position_mut(&mut self, symbol: &str) -> &mut Position {
        self.positions
            .entry(symbol.to_string())
            .or_insert_with(|| Position::new(symbol.to_string()))
    }
}

/// Equity curve point
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EquityPoint {
    pub timestamp: i64,
    pub equity: f64,
    pub cash: f64,
    pub positions_value: f64,
}

/// Backtest statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BacktestStats {
    pub initial_equity: f64,
    pub final_equity: f64,
    pub total_return: f64,
    pub num_trades: usize,
    pub total_commission: f64,
    pub sharpe_ratio: f64,
    pub max_drawdown: f64,
}
