use crate::artifact::Artifact;
use crate::audit::{AuditLog, CommitEntry};
use crate::index::{ArtifactMetadata, MetadataIndex, SearchQuery};
use crate::storage::{ContentHash, ContentStore};
use anyhow::{Context, Result};
use std::path::{Path, PathBuf};

/// HipCortex repository for managing artifacts
pub struct Repository {
    #[allow(dead_code)]
    root: PathBuf,
    store: ContentStore,
    audit_log: AuditLog,
    index: MetadataIndex,
}

impl Repository {
    /// Create or open a HipCortex repository at the given path
    pub fn open<P: AsRef<Path>>(root: P) -> Result<Self> {
        let root = root.as_ref().to_path_buf();
        std::fs::create_dir_all(&root).context("Failed to create repository directory")?;

        let store = ContentStore::new(root.join("objects"))
            .context("Failed to initialize content store")?;

        let audit_log =
            AuditLog::new(root.join("audit.log")).context("Failed to initialize audit log")?;

        let index = MetadataIndex::new(root.join("index.db"))
            .context("Failed to initialize metadata index")?;

        Ok(Self {
            root,
            store,
            audit_log,
            index,
        })
    }

    /// Commit an artifact to the repository
    pub fn commit(
        &mut self,
        artifact: &Artifact,
        message: &str,
        parent_hashes: Vec<String>,
    ) -> Result<ContentHash> {
        // Store artifact
        let hash = self
            .store
            .store(artifact)
            .context("Failed to store artifact")?;

        // Get current timestamp
        let timestamp = chrono::Utc::now().timestamp();

        // Create commit entry
        let entry = CommitEntry {
            timestamp,
            artifact_hash: hash.as_hex().to_string(),
            artifact_type: artifact.artifact_type().to_string(),
            message: message.to_string(),
            parent_hashes,
        };

        // Append to audit log
        self.audit_log
            .append(&entry)
            .context("Failed to append to audit log")?;

        // Extract and index metadata
        let metadata = self.extract_metadata(artifact, &hash, timestamp);
        self.index
            .index(&metadata)
            .context("Failed to index artifact metadata")?;

        Ok(hash)
    }

    /// Retrieve an artifact by its hash
    pub fn get(&self, hash: &ContentHash) -> Result<Artifact> {
        self.store.retrieve(hash)
    }

    /// Check if an artifact exists
    pub fn exists(&self, hash: &ContentHash) -> bool {
        self.store.exists(hash)
    }

    /// Get commit history for an artifact
    pub fn history(&self, hash: &ContentHash) -> Result<Vec<CommitEntry>> {
        self.audit_log.entries_for_artifact(hash)
    }

    /// Get all commit entries
    pub fn all_commits(&self) -> Result<Vec<CommitEntry>> {
        self.audit_log.entries()
    }

    /// Search artifacts
    pub fn search(&self, query: &SearchQuery) -> Result<Vec<ArtifactMetadata>> {
        self.index.search(query)
    }

    /// Get metadata for an artifact
    pub fn metadata(&self, hash: &ContentHash) -> Result<Option<ArtifactMetadata>> {
        self.index.get(hash)
    }

    /// Extract metadata from an artifact for indexing
    fn extract_metadata(
        &self,
        artifact: &Artifact,
        hash: &ContentHash,
        timestamp: i64,
    ) -> ArtifactMetadata {
        match artifact {
            Artifact::StrategySpec(spec) => ArtifactMetadata {
                hash: hash.as_hex().to_string(),
                artifact_type: "strategy_spec".to_string(),
                timestamp,
                goal: Some(spec.goal.clone()),
                regime_tags: spec.regime_tags.clone(),
                policy: None,
                description: Some(spec.description.clone()),
            },
            Artifact::BacktestConfig(config) => {
                let policy_str = serde_json::to_string(&config.policy).ok();
                ArtifactMetadata {
                    hash: hash.as_hex().to_string(),
                    artifact_type: "backtest_config".to_string(),
                    timestamp,
                    goal: None,
                    regime_tags: vec![],
                    policy: policy_str,
                    description: None,
                }
            }
            Artifact::Dataset(dataset) => ArtifactMetadata {
                hash: hash.as_hex().to_string(),
                artifact_type: "dataset".to_string(),
                timestamp,
                goal: None,
                regime_tags: vec![],
                policy: None,
                description: Some(dataset.description.clone()),
            },
            Artifact::BacktestResult(_) => ArtifactMetadata {
                hash: hash.as_hex().to_string(),
                artifact_type: "backtest_result".to_string(),
                timestamp,
                goal: None,
                regime_tags: vec![],
                policy: None,
                description: None,
            },
            Artifact::CRVReport(_) => ArtifactMetadata {
                hash: hash.as_hex().to_string(),
                artifact_type: "crv_report".to_string(),
                timestamp,
                goal: None,
                regime_tags: vec![],
                policy: None,
                description: None,
            },
            Artifact::Trace(trace) => ArtifactMetadata {
                hash: hash.as_hex().to_string(),
                artifact_type: "trace".to_string(),
                timestamp,
                goal: None,
                regime_tags: vec![],
                policy: None,
                description: Some(trace.operation.clone()),
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::artifact::{Dataset, DatasetMetadata, StrategySpec};
    use tempfile::TempDir;

    #[test]
    fn test_repository_commit_and_get() {
        let temp_dir = TempDir::new().unwrap();
        let mut repo = Repository::open(temp_dir.path()).unwrap();

        let artifact = Artifact::StrategySpec(StrategySpec {
            name: "test_strategy".to_string(),
            description: "A test strategy".to_string(),
            strategy_type: "ts_momentum".to_string(),
            parameters: serde_json::json!({"lookback": 20}),
            goal: "momentum".to_string(),
            regime_tags: vec!["trending".to_string()],
        });

        let hash = repo.commit(&artifact, "Initial commit", vec![]).unwrap();

        let retrieved = repo.get(&hash).unwrap();

        // Verify properties match
        match (&artifact, &retrieved) {
            (Artifact::StrategySpec(a), Artifact::StrategySpec(b)) => {
                assert_eq!(a.name, b.name);
                assert_eq!(a.goal, b.goal);
            }
            _ => panic!("Artifact types don't match"),
        }
    }

    #[test]
    fn test_repository_history() {
        let temp_dir = TempDir::new().unwrap();
        let mut repo = Repository::open(temp_dir.path()).unwrap();

        let artifact = Artifact::Dataset(Dataset {
            name: "test_data".to_string(),
            description: "Test dataset".to_string(),
            bars: vec![],
            metadata: DatasetMetadata {
                symbols: vec!["AAPL".to_string()],
                start_timestamp: 0,
                end_timestamp: 1000,
                bar_count: 10,
            },
        });

        let hash = repo.commit(&artifact, "Add dataset", vec![]).unwrap();

        let history = repo.history(&hash).unwrap();
        assert_eq!(history.len(), 1);
        assert_eq!(history[0].message, "Add dataset");
    }

    #[test]
    fn test_repository_search() {
        let temp_dir = TempDir::new().unwrap();
        let mut repo = Repository::open(temp_dir.path()).unwrap();

        let artifact1 = Artifact::StrategySpec(StrategySpec {
            name: "momentum_strategy".to_string(),
            description: "Momentum strategy".to_string(),
            strategy_type: "ts_momentum".to_string(),
            parameters: serde_json::json!({"lookback": 20}),
            goal: "momentum".to_string(),
            regime_tags: vec!["trending".to_string()],
        });

        let artifact2 = Artifact::StrategySpec(StrategySpec {
            name: "mean_reversion".to_string(),
            description: "Mean reversion strategy".to_string(),
            strategy_type: "mean_reversion".to_string(),
            parameters: serde_json::json!({"lookback": 10}),
            goal: "mean_reversion".to_string(),
            regime_tags: vec!["ranging".to_string()],
        });

        repo.commit(&artifact1, "Add momentum strategy", vec![])
            .unwrap();
        repo.commit(&artifact2, "Add mean reversion strategy", vec![])
            .unwrap();

        let query = SearchQuery {
            goal: Some("momentum".to_string()),
            ..Default::default()
        };

        let results = repo.search(&query).unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].goal, Some("momentum".to_string()));
    }

    #[test]
    fn test_repository_metadata() {
        let temp_dir = TempDir::new().unwrap();
        let mut repo = Repository::open(temp_dir.path()).unwrap();

        let artifact = Artifact::StrategySpec(StrategySpec {
            name: "test".to_string(),
            description: "Test strategy".to_string(),
            strategy_type: "ts_momentum".to_string(),
            parameters: serde_json::json!({}),
            goal: "momentum".to_string(),
            regime_tags: vec!["trending".to_string()],
        });

        let hash = repo.commit(&artifact, "Commit test", vec![]).unwrap();

        let metadata = repo.metadata(&hash).unwrap();
        assert!(metadata.is_some());

        let metadata = metadata.unwrap();
        assert_eq!(metadata.goal, Some("momentum".to_string()));
        assert_eq!(metadata.regime_tags, vec!["trending".to_string()]);
    }
}
