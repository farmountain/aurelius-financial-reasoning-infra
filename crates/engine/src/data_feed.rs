use schema::{Bar, DataFeed};

/// Simple in-memory data feed from a vector of bars
pub struct VecDataFeed {
    bars: Vec<Bar>,
    index: usize,
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

#[cfg(test)]
mod tests {
    use super::*;

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
}
