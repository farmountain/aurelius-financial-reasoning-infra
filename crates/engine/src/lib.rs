#![forbid(unsafe_code)]

pub mod backtest;
pub mod data_feed;
pub mod determinism;
pub mod output;
pub mod portfolio;

pub use backtest::BacktestEngine;
pub use data_feed::{VecCanonicalEventFeed, VecDataFeed};
pub use determinism::{canonical_json_hash, stable_hash_bytes};
pub use portfolio::PortfolioManager;
