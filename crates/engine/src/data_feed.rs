use schema::{sort_events_deterministically, Bar, CanonicalEventFeed, DataFeed, EventEnvelope};

/// Simple in-memory data feed from a vector of bars
pub struct VecDataFeed {
    bars: Vec<Bar>,
    index: usize,
}

/// In-memory canonical event feed with deterministic ordering
pub struct VecCanonicalEventFeed {
    events: Vec<EventEnvelope>,
    index: usize,
}

impl VecCanonicalEventFeed {
    pub fn new(mut events: Vec<EventEnvelope>) -> Self {
        sort_events_deterministically(&mut events);
        Self { events, index: 0 }
    }
}

impl VecDataFeed {
    pub fn new(mut bars: Vec<Bar>) -> Self {
        // Sort bars by timestamp to ensure deterministic ordering
        bars.sort_by_key(|b| b.timestamp);
        Self { bars, index: 0 }
    }
}

impl DataFeed for VecDataFeed {
    fn next_bar(&mut self) -> Option<Bar> {
        if self.index < self.bars.len() {
            let bar = self.bars[self.index].clone();
            self.index += 1;
            Some(bar)
        } else {
            None
        }
    }

    fn reset(&mut self) {
        self.index = 0;
    }
}

impl CanonicalEventFeed for VecCanonicalEventFeed {
    fn next_event(&mut self) -> Option<EventEnvelope> {
        if self.index < self.events.len() {
            let event = self.events[self.index].clone();
            self.index += 1;
            Some(event)
        } else {
            None
        }
    }

    fn reset_events(&mut self) {
        self.index = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use schema::{MarketEventPayload, MarketEventType, QualityFlag};
    use sha2::{Digest, Sha256};

    #[test]
    fn test_vec_data_feed() {
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

        let mut feed = VecDataFeed::new(bars);

        let bar1 = feed.next_bar().unwrap();
        assert_eq!(bar1.timestamp, 1000);

        let bar2 = feed.next_bar().unwrap();
        assert_eq!(bar2.timestamp, 2000);

        assert!(feed.next_bar().is_none());

        // Test reset
        feed.reset();
        let bar1_again = feed.next_bar().unwrap();
        assert_eq!(bar1_again.timestamp, 1000);
    }

    #[test]
    fn test_data_feed_sorts_by_timestamp() {
        let bars = vec![
            Bar {
                timestamp: 2000,
                symbol: "AAPL".to_string(),
                open: 101.0,
                high: 103.0,
                low: 100.0,
                close: 102.0,
                volume: 11000.0,
            },
            Bar {
                timestamp: 1000,
                symbol: "AAPL".to_string(),
                open: 100.0,
                high: 102.0,
                low: 99.0,
                close: 101.0,
                volume: 10000.0,
            },
        ];

        let mut feed = VecDataFeed::new(bars);

        // Should get bars in sorted order
        let bar1 = feed.next_bar().unwrap();
        assert_eq!(bar1.timestamp, 1000);

        let bar2 = feed.next_bar().unwrap();
        assert_eq!(bar2.timestamp, 2000);
    }

    #[test]
    fn test_canonical_event_feed_deterministic_replay() {
        let events = vec![
            EventEnvelope {
                event_type: MarketEventType::Bar,
                symbol: "AAPL".to_string(),
                event_time: 2000,
                ingest_time: 2001,
                source_id: "test".to_string(),
                quality_flags: vec![QualityFlag::DerivedValue],
                payload: MarketEventPayload::Bar(Bar {
                    timestamp: 2000,
                    symbol: "AAPL".to_string(),
                    open: 101.0,
                    high: 103.0,
                    low: 100.0,
                    close: 102.0,
                    volume: 11000.0,
                }),
            },
            EventEnvelope {
                event_type: MarketEventType::Bar,
                symbol: "AAPL".to_string(),
                event_time: 1000,
                ingest_time: 1001,
                source_id: "test".to_string(),
                quality_flags: vec![],
                payload: MarketEventPayload::Bar(Bar {
                    timestamp: 1000,
                    symbol: "AAPL".to_string(),
                    open: 100.0,
                    high: 102.0,
                    low: 99.0,
                    close: 101.0,
                    volume: 10000.0,
                }),
            },
        ];

        let mut hashes = Vec::new();
        for _ in 0..3 {
            let mut feed = VecCanonicalEventFeed::new(events.clone());
            let mut hasher = Sha256::new();

            while let Some(event) = feed.next_event() {
                hasher.update(event.event_time.to_le_bytes());
                hasher.update(event.ingest_time.to_le_bytes());
                hasher.update(event.symbol.as_bytes());
            }

            hashes.push(hasher.finalize());
        }

        assert_eq!(hashes[0], hashes[1]);
        assert_eq!(hashes[1], hashes[2]);
    }
}
