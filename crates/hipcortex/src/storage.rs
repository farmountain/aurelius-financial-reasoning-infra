use crate::artifact::Artifact;
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::{Path, PathBuf};

/// Content hash for artifacts (SHA-256)
#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct ContentHash(String);

impl ContentHash {
    /// Create a new content hash from a hex string
    pub fn from_hex(hex: String) -> Self {
        Self(hex)
    }

    /// Get the hex representation of the hash
    pub fn as_hex(&self) -> &str {
        &self.0
    }

    /// Compute hash from artifact
    pub fn compute(artifact: &Artifact) -> Result<Self> {
        // Serialize to canonical JSON (sorted keys)
        let json = serde_json::to_vec(artifact)
            .context("Failed to serialize artifact")?;
        
        // Compute SHA-256 hash
        let mut hasher = Sha256::new();
        hasher.update(&json);
        let hash = hasher.finalize();
        
        Ok(Self(hex::encode(hash)))
    }
}

impl std::fmt::Display for ContentHash {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.0)
    }
}

/// Content-addressed store for artifacts
pub struct ContentStore {
    root: PathBuf,
}

impl ContentStore {
    /// Create a new content store at the given path
    pub fn new<P: AsRef<Path>>(root: P) -> Result<Self> {
        let root = root.as_ref().to_path_buf();
        fs::create_dir_all(&root)
            .context("Failed to create content store directory")?;
        Ok(Self { root })
    }

    /// Store an artifact and return its content hash
    pub fn store(&self, artifact: &Artifact) -> Result<ContentHash> {
        let hash = ContentHash::compute(artifact)?;
        let path = self.artifact_path(&hash);
        
        // Create subdirectory based on first two characters of hash
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .context("Failed to create artifact subdirectory")?;
        }
        
        // Write artifact to file
        let json = serde_json::to_vec_pretty(artifact)
            .context("Failed to serialize artifact")?;
        fs::write(&path, json)
            .context("Failed to write artifact to store")?;
        
        Ok(hash)
    }

    /// Retrieve an artifact by its content hash
    pub fn retrieve(&self, hash: &ContentHash) -> Result<Artifact> {
        let path = self.artifact_path(hash);
        let data = fs::read(&path)
            .with_context(|| format!("Failed to read artifact {}", hash))?;
        let artifact = serde_json::from_slice(&data)
            .context("Failed to deserialize artifact")?;
        Ok(artifact)
    }

    /// Check if an artifact exists in the store
    pub fn exists(&self, hash: &ContentHash) -> bool {
        self.artifact_path(hash).exists()
    }

    /// Get the file path for an artifact
    fn artifact_path(&self, hash: &ContentHash) -> PathBuf {
        let hex = hash.as_hex();
        // Ensure hash is long enough
        if hex.len() < 2 {
            panic!("Hash too short: {}", hex);
        }
        // Use first 2 characters as subdirectory for better filesystem performance
        let prefix = &hex[..2];
        self.root.join(prefix).join(format!("{}.json", hex))
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::artifact::{Dataset, DatasetMetadata, StrategySpec};
    use tempfile::TempDir;

    #[test]
    fn test_content_hash_stability() {
        // Create identical artifacts
        let artifact1 = Artifact::StrategySpec(StrategySpec {
            name: "test".to_string(),
            description: "test strategy".to_string(),
            strategy_type: "ts_momentum".to_string(),
            parameters: serde_json::json!({"lookback": 20}),
            goal: "momentum".to_string(),
            regime_tags: vec!["trending".to_string()],
        });

        let artifact2 = Artifact::StrategySpec(StrategySpec {
            name: "test".to_string(),
            description: "test strategy".to_string(),
            strategy_type: "ts_momentum".to_string(),
            parameters: serde_json::json!({"lookback": 20}),
            goal: "momentum".to_string(),
            regime_tags: vec!["trending".to_string()],
        });

        let hash1 = ContentHash::compute(&artifact1).unwrap();
        let hash2 = ContentHash::compute(&artifact2).unwrap();

        // Hashes should be identical for identical artifacts
        assert_eq!(hash1, hash2);

        // Hash should be deterministic across multiple invocations
        let hash3 = ContentHash::compute(&artifact1).unwrap();
        assert_eq!(hash1, hash3);
    }

    #[test]
    fn test_content_hash_changes_with_content() {
        let artifact1 = Artifact::StrategySpec(StrategySpec {
            name: "test".to_string(),
            description: "test strategy".to_string(),
            strategy_type: "ts_momentum".to_string(),
            parameters: serde_json::json!({"lookback": 20}),
            goal: "momentum".to_string(),
            regime_tags: vec!["trending".to_string()],
        });

        let artifact2 = Artifact::StrategySpec(StrategySpec {
            name: "test".to_string(),
            description: "test strategy".to_string(),
            strategy_type: "ts_momentum".to_string(),
            parameters: serde_json::json!({"lookback": 30}), // Different parameter
            goal: "momentum".to_string(),
            regime_tags: vec!["trending".to_string()],
        });

        let hash1 = ContentHash::compute(&artifact1).unwrap();
        let hash2 = ContentHash::compute(&artifact2).unwrap();

        // Hashes should be different for different artifacts
        assert_ne!(hash1, hash2);
    }

    #[test]
    fn test_content_store_round_trip() {
        let temp_dir = TempDir::new().unwrap();
        let store = ContentStore::new(temp_dir.path()).unwrap();

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

        // Store artifact
        let hash = store.store(&artifact).unwrap();

        // Retrieve artifact
        let retrieved = store.retrieve(&hash).unwrap();

        // Verify properties match
        match (&artifact, &retrieved) {
            (Artifact::Dataset(a), Artifact::Dataset(b)) => {
                assert_eq!(a.name, b.name);
                assert_eq!(a.description, b.description);
                assert_eq!(a.metadata.symbols, b.metadata.symbols);
            }
            _ => panic!("Artifact types don't match"),
        }
    }

    #[test]
    fn test_content_store_exists() {
        let temp_dir = TempDir::new().unwrap();
        let store = ContentStore::new(temp_dir.path()).unwrap();

        let artifact = Artifact::StrategySpec(StrategySpec {
            name: "test".to_string(),
            description: "test".to_string(),
            strategy_type: "ts_momentum".to_string(),
            parameters: serde_json::json!({}),
            goal: "momentum".to_string(),
            regime_tags: vec![],
        });

        let hash = store.store(&artifact).unwrap();

        // Should exist after storing
        assert!(store.exists(&hash));

        // Non-existent hash should not exist
        let fake_hash = ContentHash::from_hex("0000000000000000000000000000000000000000000000000000000000000000".to_string());
        assert!(!store.exists(&fake_hash));
    }
}
