use crate::types::{Bar, Fill, Order, Portfolio};
use crate::{
    AdapterRequest, EventEnvelope, NormalizedEventBatch, ProviderCapabilityDeclaration,
    ProviderRecord,
};
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

/// Trait for canonical event feeds
pub trait CanonicalEventFeed {
    /// Get the next market event. Returns None when data is exhausted.
    fn next_event(&mut self) -> Option<EventEnvelope>;

    /// Reset the event feed to the beginning.
    fn reset_events(&mut self);
}

/// Trait for market data provider adapters that normalize provider-native records
/// into canonical market event envelopes.
pub trait MarketDataAdapter {
    /// Unique provider identifier.
    fn provider_id(&self) -> &str;

    /// Supported capabilities for this provider adapter.
    fn capabilities(&self) -> ProviderCapabilityDeclaration;

    /// Normalize one provider-native record into a canonical event.
    fn normalize_record(&self, record: ProviderRecord) -> Result<EventEnvelope>;

    /// Normalize a batch while preserving transformation lineage.
    fn normalize_batch(
        &self,
        records: Vec<ProviderRecord>,
        lineage_step: Option<&str>,
    ) -> Result<NormalizedEventBatch> {
        let mut events = Vec::with_capacity(records.len());
        for record in records {
            events.push(self.normalize_record(record)?);
        }

        Ok(NormalizedEventBatch {
            source_id: self.provider_id().to_string(),
            events,
            lineage: lineage_step
                .map(|step| {
                    vec![crate::TransformationStep {
                        step: "normalize_batch".to_string(),
                        details: step.to_string(),
                    }]
                })
                .unwrap_or_default(),
        })
    }

    /// Validate whether this adapter supports a requested capability.
    fn supports_request(&self, request: &AdapterRequest) -> Result<()> {
        self.capabilities().supports(request)
    }
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
