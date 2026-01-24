# HipCortex - Content-Addressed Artifact Storage

HipCortex is a content-addressed artifact storage system designed for quantitative research reproducibility and provenance tracking.

## Features

### Content-Addressed Storage
- **SHA-256 hashing** over canonical JSON bytes
- Immutable artifact storage with deduplication
- Content integrity verification

### Artifact Types
- **Dataset**: Market data with metadata
- **StrategySpec**: Strategy definitions with goals and regime tags
- **BacktestConfig**: Backtest configuration with policy constraints
- **BacktestResult**: Backtest results with statistics and trades
- **CRVReport**: CRV verification reports
- **Trace**: Audit trails for debugging

### Append-Only Audit Log
- Immutable commit history
- Parent hash tracking for lineage
- Timestamp-based ordering

### Metadata Index (SQLite)
- Fast searching by:
  - Artifact type
  - Goal
  - Regime tags
  - Policy constraints
  - Timestamps
- Efficient queries with proper indexing

### CLI Tool

#### Commit Artifacts
```bash
hipcortex commit --artifact strategy.json --message "Add momentum strategy"
hipcortex commit --artifact config.json --message "Add config" --parent <hash>
```

#### Show Artifact Details
```bash
hipcortex show <hash>
hipcortex show <hash> --full  # Include full artifact data
```

#### Diff Artifacts
```bash
hipcortex diff <hash1> <hash2>
```

#### Replay Computation
```bash
hipcortex replay <result_hash> --data data.parquet
```

#### Search Artifacts
```bash
hipcortex search --goal momentum
hipcortex search --tag trending
hipcortex search --artifact-type strategy_spec --limit 5
```

## Usage

### As a Library

```rust
use hipcortex::{Repository, Artifact, StrategySpec};

// Open repository
let mut repo = Repository::open(".hipcortex")?;

// Create an artifact
let strategy = Artifact::StrategySpec(StrategySpec {
    name: "momentum".to_string(),
    description: "Momentum strategy".to_string(),
    strategy_type: "ts_momentum".to_string(),
    parameters: serde_json::json!({"lookback": 20}),
    goal: "momentum".to_string(),
    regime_tags: vec!["trending".to_string()],
});

// Commit artifact
let hash = repo.commit(&strategy, "Add strategy", vec![])?;

// Retrieve artifact
let retrieved = repo.get(&hash)?;

// Search artifacts
let results = repo.search(&SearchQuery {
    goal: Some("momentum".to_string()),
    ..Default::default()
})?;
```

### Example Workflow

```bash
# 1. Commit a strategy
hipcortex commit --artifact strategy.json --message "Add momentum strategy"
# Output: Committed artifact: abc123...

# 2. Commit a config referencing the strategy
hipcortex commit --artifact config.json --message "Add config" --parent abc123...
# Output: Committed artifact: def456...

# 3. Commit a backtest result referencing the config
hipcortex commit --artifact result.json --message "Add result" --parent def456...
# Output: Committed artifact: ghi789...

# 4. Replay the computation to verify reproducibility
hipcortex replay ghi789... --data data.parquet
# Output: ✓ Result hash verification PASSED

# 5. Search for all momentum strategies
hipcortex search --goal momentum
```

## Repository Structure

```
.hipcortex/
├── objects/          # Content-addressed artifact storage
│   ├── ab/           # Sharded by first 2 chars of hash
│   │   └── abc123...def.json
│   └── cd/
│       └── cde456...789.json
├── audit.log         # Append-only commit log
└── index.db          # SQLite metadata index
```

## Testing

Run all tests:
```bash
cargo test --package hipcortex
```

Test coverage includes:
- Round-trip serialization (17 unit tests)
- Hash stability tests
- Replay reproducibility tests (3 integration tests)
- Content store operations
- Audit log functionality
- Metadata indexing and search

## Design Principles

1. **Immutability**: All artifacts are immutable once committed
2. **Content-Addressing**: Hash-based addressing ensures integrity
3. **Lineage Tracking**: Parent hashes track computation dependencies
4. **Reproducibility**: Deterministic hashing enables replay verification
5. **Searchability**: Efficient metadata indexing for fast queries

## Future Enhancements

- DuckDB as alternative to SQLite for larger datasets
- Full replay integration with backtest engine
- Garbage collection for unused artifacts
- Remote repository synchronization
- Artifact signing and verification
