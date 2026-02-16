use anyhow::Result;
use serde::{Deserialize, Serialize};

use crate::types::Bar;

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MarketEventType {
    Bar,
    Trade,
    Quote,
    OrderBookUpdate,
    OptionsChainSnapshot,
    FundamentalsSnapshot,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum FidelityTier {
    Tier1Bar,
    Tier2TickQuote,
    Tier3OrderBook,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum LatencyClass {
    Realtime,
    Delayed,
    EndOfDay,
    Unknown,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MarketAssetClass {
    Equity,
    Future,
    Option,
    Crypto,
    Fx,
    Commodity,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum QualityFlag {
    MissingSourceField,
    DerivedValue,
    LateSourceData,
    NormalizationWarning,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TradePayload {
    pub price: f64,
    pub quantity: f64,
    pub venue: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct QuotePayload {
    pub bid_price: f64,
    pub bid_size: f64,
    pub ask_price: f64,
    pub ask_size: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OrderBookLevel {
    pub price: f64,
    pub size: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OrderBookPayload {
    pub bids: Vec<OrderBookLevel>,
    pub asks: Vec<OrderBookLevel>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OptionContractSnapshot {
    pub symbol: String,
    pub strike: f64,
    pub expiry: i64,
    pub option_type: String,
    pub bid: Option<f64>,
    pub ask: Option<f64>,
    pub last: Option<f64>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct OptionsChainPayload {
    pub underlying: String,
    pub contracts: Vec<OptionContractSnapshot>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct FundamentalsPayload {
    pub metric_name: String,
    pub value: f64,
    pub period: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(tag = "payload_type", rename_all = "snake_case")]
pub enum MarketEventPayload {
    Bar(Bar),
    Trade(TradePayload),
    Quote(QuotePayload),
    OrderBookUpdate(OrderBookPayload),
    OptionsChainSnapshot(OptionsChainPayload),
    FundamentalsSnapshot(FundamentalsPayload),
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct EventEnvelope {
    pub event_type: MarketEventType,
    pub symbol: String,
    pub event_time: i64,
    pub ingest_time: i64,
    pub source_id: String,
    pub quality_flags: Vec<QualityFlag>,
    pub payload: MarketEventPayload,
}

impl EventEnvelope {
    pub fn validate_required_fields(&self) -> Result<()> {
        if self.symbol.trim().is_empty() {
            anyhow::bail!("missing required field: symbol");
        }
        if self.event_time <= 0 {
            anyhow::bail!("missing or invalid required field: event_time");
        }
        if self.ingest_time <= 0 {
            anyhow::bail!("missing or invalid required field: ingest_time");
        }
        if self.source_id.trim().is_empty() {
            anyhow::bail!("missing required field: source_id");
        }

        let payload_type = self.payload.event_type();
        if payload_type != self.event_type {
            anyhow::bail!(
                "event_type/payload mismatch: envelope={:?}, payload={:?}",
                self.event_type,
                payload_type
            );
        }

        Ok(())
    }
}

impl MarketEventPayload {
    pub fn event_type(&self) -> MarketEventType {
        match self {
            Self::Bar(_) => MarketEventType::Bar,
            Self::Trade(_) => MarketEventType::Trade,
            Self::Quote(_) => MarketEventType::Quote,
            Self::OrderBookUpdate(_) => MarketEventType::OrderBookUpdate,
            Self::OptionsChainSnapshot(_) => MarketEventType::OptionsChainSnapshot,
            Self::FundamentalsSnapshot(_) => MarketEventType::FundamentalsSnapshot,
        }
    }
}

pub fn sort_events_deterministically(events: &mut [EventEnvelope]) {
    events.sort_by(|a, b| {
        a.event_time
            .cmp(&b.event_time)
            .then(a.ingest_time.cmp(&b.ingest_time))
            .then(a.symbol.cmp(&b.symbol))
            .then(format!("{:?}", a.event_type).cmp(&format!("{:?}", b.event_type)))
    });
}

pub fn validate_events_for_tier(events: &[EventEnvelope], tier: FidelityTier) -> Result<()> {
    for event in events {
        event.validate_required_fields()?;
    }

    match tier {
        FidelityTier::Tier1Bar => {
            if !events
                .iter()
                .any(|e| matches!(e.payload, MarketEventPayload::Bar(_)))
            {
                anyhow::bail!("tier1 requires at least one bar event");
            }
        }
        FidelityTier::Tier2TickQuote => {
            let has_trade = events
                .iter()
                .any(|e| matches!(e.payload, MarketEventPayload::Trade(_)));
            let has_quote = events
                .iter()
                .any(|e| matches!(e.payload, MarketEventPayload::Quote(_)));
            if !(has_trade || has_quote) {
                anyhow::bail!("tier2 requires at least one trade or quote event");
            }
        }
        FidelityTier::Tier3OrderBook => {
            if !events
                .iter()
                .any(|e| matches!(e.payload, MarketEventPayload::OrderBookUpdate(_)))
            {
                anyhow::bail!("tier3 requires at least one order_book_update event");
            }
        }
    }

    Ok(())
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AdapterRequest {
    pub asset_class: MarketAssetClass,
    pub event_type: MarketEventType,
    pub fidelity_tier: FidelityTier,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProviderCapabilityDeclaration {
    pub provider_id: String,
    pub supported_asset_classes: Vec<MarketAssetClass>,
    pub supported_event_types: Vec<MarketEventType>,
    pub supported_fidelity_tiers: Vec<FidelityTier>,
}

impl ProviderCapabilityDeclaration {
    pub fn supports(&self, request: &AdapterRequest) -> Result<()> {
        if !self.supported_asset_classes.contains(&request.asset_class) {
            anyhow::bail!(
                "provider '{}' does not support asset class {:?}",
                self.provider_id,
                request.asset_class
            );
        }
        if !self.supported_event_types.contains(&request.event_type) {
            anyhow::bail!(
                "provider '{}' does not support event type {:?}",
                self.provider_id,
                request.event_type
            );
        }
        if !self
            .supported_fidelity_tiers
            .contains(&request.fidelity_tier)
        {
            anyhow::bail!(
                "provider '{}' does not support fidelity tier {:?}",
                self.provider_id,
                request.fidelity_tier
            );
        }

        Ok(())
    }
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ProviderRecord {
    pub symbol: String,
    pub event_time: i64,
    pub ingest_time: i64,
    pub raw_payload: serde_json::Value,
    pub quality_flags: Vec<QualityFlag>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct TransformationStep {
    pub step: String,
    pub details: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct NormalizedEventBatch {
    pub source_id: String,
    pub events: Vec<EventEnvelope>,
    pub lineage: Vec<TransformationStep>,
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_bar_event() -> EventEnvelope {
        EventEnvelope {
            event_type: MarketEventType::Bar,
            symbol: "AAPL".to_string(),
            event_time: 1_700_000_000,
            ingest_time: 1_700_000_001,
            source_id: "legacy-parquet".to_string(),
            quality_flags: vec![],
            payload: MarketEventPayload::Bar(Bar {
                timestamp: 1_700_000_000,
                symbol: "AAPL".to_string(),
                open: 100.0,
                high: 102.0,
                low: 99.0,
                close: 101.0,
                volume: 1_000.0,
            }),
        }
    }

    #[test]
    fn validates_required_fields() {
        let event = sample_bar_event();
        assert!(event.validate_required_fields().is_ok());
    }

    #[test]
    fn rejects_missing_symbol() {
        let mut event = sample_bar_event();
        event.symbol = String::new();
        assert!(event.validate_required_fields().is_err());
    }

    #[test]
    fn sorts_events_stably() {
        let mut events = vec![
            EventEnvelope {
                ingest_time: 20,
                ..sample_bar_event()
            },
            EventEnvelope {
                event_time: 1_699_999_999,
                ingest_time: 50,
                ..sample_bar_event()
            },
            EventEnvelope {
                ingest_time: 10,
                ..sample_bar_event()
            },
        ];

        sort_events_deterministically(&mut events);
        assert_eq!(events[0].event_time, 1_699_999_999);
        assert_eq!(events[1].ingest_time, 10);
        assert_eq!(events[2].ingest_time, 20);
    }

    #[test]
    fn tier_validation_checks() {
        let bar_events = vec![sample_bar_event()];
        assert!(validate_events_for_tier(&bar_events, FidelityTier::Tier1Bar).is_ok());
        assert!(validate_events_for_tier(&bar_events, FidelityTier::Tier2TickQuote).is_err());

        let trade_event = EventEnvelope {
            event_type: MarketEventType::Trade,
            symbol: "AAPL".to_string(),
            event_time: 1_700_000_100,
            ingest_time: 1_700_000_101,
            source_id: "provider-x".to_string(),
            quality_flags: vec![QualityFlag::DerivedValue],
            payload: MarketEventPayload::Trade(TradePayload {
                price: 101.1,
                quantity: 10.0,
                venue: Some("XNAS".to_string()),
            }),
        };

        assert!(validate_events_for_tier(&[trade_event], FidelityTier::Tier2TickQuote).is_ok());
    }

    #[test]
    fn provider_capability_check_reports_unsupported() {
        let capabilities = ProviderCapabilityDeclaration {
            provider_id: "example-provider".to_string(),
            supported_asset_classes: vec![MarketAssetClass::Equity],
            supported_event_types: vec![MarketEventType::Bar],
            supported_fidelity_tiers: vec![FidelityTier::Tier1Bar],
        };

        let unsupported = AdapterRequest {
            asset_class: MarketAssetClass::Fx,
            event_type: MarketEventType::Quote,
            fidelity_tier: FidelityTier::Tier2TickQuote,
        };

        assert!(capabilities.supports(&unsupported).is_err());
    }
}
