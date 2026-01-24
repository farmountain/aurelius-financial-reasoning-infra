use crate::storage::ContentHash;
use anyhow::{Context, Result};
use rusqlite::{params, Connection};
use std::path::Path;

/// Metadata for an artifact
#[derive(Debug, Clone)]
pub struct ArtifactMetadata {
    pub hash: String,
    pub artifact_type: String,
    pub timestamp: i64,
    pub goal: Option<String>,
    pub regime_tags: Vec<String>,
    pub policy: Option<String>,
    pub description: Option<String>,
}

/// SQLite-based metadata index for fast artifact search
pub struct MetadataIndex {
    conn: Connection,
}

impl MetadataIndex {
    /// Create a new metadata index at the given database path
    pub fn new<P: AsRef<Path>>(db_path: P) -> Result<Self> {
        let conn = Connection::open(db_path)
            .context("Failed to open SQLite database")?;
        
        // Create tables
        conn.execute(
            "CREATE TABLE IF NOT EXISTS artifacts (
                hash TEXT PRIMARY KEY,
                artifact_type TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                goal TEXT,
                policy TEXT,
                description TEXT
            )",
            [],
        ).context("Failed to create artifacts table")?;

        conn.execute(
            "CREATE TABLE IF NOT EXISTS regime_tags (
                hash TEXT NOT NULL,
                tag TEXT NOT NULL,
                PRIMARY KEY (hash, tag),
                FOREIGN KEY (hash) REFERENCES artifacts(hash)
            )",
            [],
        ).context("Failed to create regime_tags table")?;

        // Create indices for fast searching
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_artifact_type ON artifacts(artifact_type)",
            [],
        ).context("Failed to create artifact_type index")?;

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_goal ON artifacts(goal)",
            [],
        ).context("Failed to create goal index")?;

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_timestamp ON artifacts(timestamp)",
            [],
        ).context("Failed to create timestamp index")?;

        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_regime_tag ON regime_tags(tag)",
            [],
        ).context("Failed to create regime_tag index")?;

        Ok(Self { conn })
    }

    /// Index an artifact's metadata
    pub fn index(&mut self, metadata: &ArtifactMetadata) -> Result<()> {
        let tx = self.conn.transaction()
            .context("Failed to start transaction")?;

        tx.execute(
            "INSERT OR REPLACE INTO artifacts (hash, artifact_type, timestamp, goal, policy, description)
             VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                &metadata.hash,
                &metadata.artifact_type,
                metadata.timestamp,
                &metadata.goal,
                &metadata.policy,
                &metadata.description,
            ],
        ).context("Failed to insert artifact metadata")?;

        // Delete old tags and insert new ones
        tx.execute(
            "DELETE FROM regime_tags WHERE hash = ?1",
            params![&metadata.hash],
        ).context("Failed to delete old regime tags")?;

        for tag in &metadata.regime_tags {
            tx.execute(
                "INSERT INTO regime_tags (hash, tag) VALUES (?1, ?2)",
                params![&metadata.hash, tag],
            ).context("Failed to insert regime tag")?;
        }

        tx.commit().context("Failed to commit transaction")?;
        Ok(())
    }

    /// Search artifacts by various criteria
    pub fn search(&self, query: &SearchQuery) -> Result<Vec<ArtifactMetadata>> {
        let mut sql = String::from(
            "SELECT DISTINCT a.hash, a.artifact_type, a.timestamp, a.goal, a.policy, a.description
             FROM artifacts a"
        );

        let mut conditions = Vec::new();
        let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();
        let mut param_idx = 1;

        if query.regime_tags.is_some() {
            sql.push_str(" LEFT JOIN regime_tags rt ON a.hash = rt.hash");
        }

        if let Some(artifact_type) = &query.artifact_type {
            conditions.push(format!("a.artifact_type = ?{}", param_idx));
            params_vec.push(Box::new(artifact_type.clone()));
            param_idx += 1;
        }

        if let Some(goal) = &query.goal {
            conditions.push(format!("a.goal = ?{}", param_idx));
            params_vec.push(Box::new(goal.clone()));
            param_idx += 1;
        }

        if let Some(policy) = &query.policy {
            conditions.push(format!("a.policy = ?{}", param_idx));
            params_vec.push(Box::new(policy.clone()));
            param_idx += 1;
        }

        if let Some(start) = query.timestamp_start {
            conditions.push(format!("a.timestamp >= ?{}", param_idx));
            params_vec.push(Box::new(start));
            param_idx += 1;
        }

        if let Some(end) = query.timestamp_end {
            conditions.push(format!("a.timestamp <= ?{}", param_idx));
            params_vec.push(Box::new(end));
            param_idx += 1;
        }

        if let Some(tags) = &query.regime_tags {
            let mut tag_conditions = Vec::new();
            for tag in tags {
                tag_conditions.push(format!("rt.tag = ?{}", param_idx));
                params_vec.push(Box::new(tag.clone()));
                param_idx += 1;
            }
            if !tag_conditions.is_empty() {
                conditions.push(format!("({})", tag_conditions.join(" OR ")));
            }
        }

        if !conditions.is_empty() {
            sql.push_str(" WHERE ");
            sql.push_str(&conditions.join(" AND "));
        }

        sql.push_str(" ORDER BY a.timestamp DESC");

        if let Some(limit) = query.limit {
            conditions.push(format!("1 = 1 LIMIT ?{}", param_idx));
            sql.push_str(&format!(" LIMIT ?{}", param_idx));
            params_vec.push(Box::new(limit as i64));
        }

        let params_refs: Vec<&dyn rusqlite::ToSql> = params_vec.iter().map(|p| p.as_ref()).collect();

        let mut stmt = self.conn.prepare(&sql)
            .context("Failed to prepare search query")?;

        let rows = stmt.query_map(params_refs.as_slice(), |row| {
            let hash: String = row.get(0)?;
            let artifact_type: String = row.get(1)?;
            let timestamp: i64 = row.get(2)?;
            let goal: Option<String> = row.get(3)?;
            let policy: Option<String> = row.get(4)?;
            let description: Option<String> = row.get(5)?;

            Ok((hash, artifact_type, timestamp, goal, policy, description))
        }).context("Failed to execute search query")?;

        let mut results = Vec::new();
        for row in rows {
            let (hash, artifact_type, timestamp, goal, policy, description) = row
                .context("Failed to read row")?;

            // Fetch regime tags for this artifact
            let regime_tags = self.get_regime_tags(&hash)?;

            results.push(ArtifactMetadata {
                hash,
                artifact_type,
                timestamp,
                goal,
                regime_tags,
                policy,
                description,
            });
        }

        Ok(results)
    }

    /// Get regime tags for a specific artifact
    fn get_regime_tags(&self, hash: &str) -> Result<Vec<String>> {
        let mut stmt = self.conn.prepare(
            "SELECT tag FROM regime_tags WHERE hash = ?1"
        ).context("Failed to prepare regime tags query")?;

        let tags = stmt.query_map(params![hash], |row| {
            row.get(0)
        }).context("Failed to execute regime tags query")?;

        let mut result = Vec::new();
        for tag in tags {
            result.push(tag.context("Failed to read tag")?);
        }

        Ok(result)
    }

    /// Get metadata for a specific artifact
    pub fn get(&self, hash: &ContentHash) -> Result<Option<ArtifactMetadata>> {
        let mut stmt = self.conn.prepare(
            "SELECT hash, artifact_type, timestamp, goal, policy, description
             FROM artifacts WHERE hash = ?1"
        ).context("Failed to prepare get query")?;

        let mut rows = stmt.query(params![hash.as_hex()])
            .context("Failed to execute get query")?;

        if let Some(row) = rows.next().context("Failed to read row")? {
            let hash: String = row.get(0)?;
            let artifact_type: String = row.get(1)?;
            let timestamp: i64 = row.get(2)?;
            let goal: Option<String> = row.get(3)?;
            let policy: Option<String> = row.get(4)?;
            let description: Option<String> = row.get(5)?;

            let regime_tags = self.get_regime_tags(&hash)?;

            Ok(Some(ArtifactMetadata {
                hash,
                artifact_type,
                timestamp,
                goal,
                regime_tags,
                policy,
                description,
            }))
        } else {
            Ok(None)
        }
    }
}

/// Search query for artifacts
#[derive(Debug, Clone, Default)]
pub struct SearchQuery {
    pub artifact_type: Option<String>,
    pub goal: Option<String>,
    pub regime_tags: Option<Vec<String>>,
    pub policy: Option<String>,
    pub timestamp_start: Option<i64>,
    pub timestamp_end: Option<i64>,
    pub limit: Option<usize>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_metadata_index_insert_and_get() {
        let temp_dir = TempDir::new().unwrap();
        let db_path = temp_dir.path().join("metadata.db");
        let mut index = MetadataIndex::new(&db_path).unwrap();

        let metadata = ArtifactMetadata {
            hash: "abc123".to_string(),
            artifact_type: "strategy_spec".to_string(),
            timestamp: 1000,
            goal: Some("momentum".to_string()),
            regime_tags: vec!["trending".to_string(), "volatile".to_string()],
            policy: Some("conservative".to_string()),
            description: Some("Test strategy".to_string()),
        };

        index.index(&metadata).unwrap();

        let hash = ContentHash::from_hex("abc123".to_string());
        let retrieved = index.get(&hash).unwrap();
        assert!(retrieved.is_some());

        let retrieved = retrieved.unwrap();
        assert_eq!(retrieved.hash, metadata.hash);
        assert_eq!(retrieved.artifact_type, metadata.artifact_type);
        assert_eq!(retrieved.regime_tags.len(), 2);
    }

    #[test]
    fn test_metadata_search_by_goal() {
        let temp_dir = TempDir::new().unwrap();
        let db_path = temp_dir.path().join("metadata.db");
        let mut index = MetadataIndex::new(&db_path).unwrap();

        let metadata1 = ArtifactMetadata {
            hash: "abc123".to_string(),
            artifact_type: "strategy_spec".to_string(),
            timestamp: 1000,
            goal: Some("momentum".to_string()),
            regime_tags: vec![],
            policy: None,
            description: None,
        };

        let metadata2 = ArtifactMetadata {
            hash: "def456".to_string(),
            artifact_type: "strategy_spec".to_string(),
            timestamp: 2000,
            goal: Some("mean_reversion".to_string()),
            regime_tags: vec![],
            policy: None,
            description: None,
        };

        index.index(&metadata1).unwrap();
        index.index(&metadata2).unwrap();

        let query = SearchQuery {
            goal: Some("momentum".to_string()),
            ..Default::default()
        };

        let results = index.search(&query).unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].hash, "abc123");
    }

    #[test]
    fn test_metadata_search_by_regime_tags() {
        let temp_dir = TempDir::new().unwrap();
        let db_path = temp_dir.path().join("metadata.db");
        let mut index = MetadataIndex::new(&db_path).unwrap();

        let metadata1 = ArtifactMetadata {
            hash: "abc123".to_string(),
            artifact_type: "strategy_spec".to_string(),
            timestamp: 1000,
            goal: None,
            regime_tags: vec!["trending".to_string()],
            policy: None,
            description: None,
        };

        let metadata2 = ArtifactMetadata {
            hash: "def456".to_string(),
            artifact_type: "strategy_spec".to_string(),
            timestamp: 2000,
            goal: None,
            regime_tags: vec!["mean_reverting".to_string()],
            policy: None,
            description: None,
        };

        index.index(&metadata1).unwrap();
        index.index(&metadata2).unwrap();

        let query = SearchQuery {
            regime_tags: Some(vec!["trending".to_string()]),
            ..Default::default()
        };

        let results = index.search(&query).unwrap();
        assert_eq!(results.len(), 1);
        assert_eq!(results[0].hash, "abc123");
    }

    #[test]
    fn test_metadata_search_time_range() {
        let temp_dir = TempDir::new().unwrap();
        let db_path = temp_dir.path().join("metadata.db");
        let mut index = MetadataIndex::new(&db_path).unwrap();

        for i in 0..5 {
            let metadata = ArtifactMetadata {
                hash: format!("hash{}", i),
                artifact_type: "dataset".to_string(),
                timestamp: (i + 1) * 1000,
                goal: None,
                regime_tags: vec![],
                policy: None,
                description: None,
            };
            index.index(&metadata).unwrap();
        }

        let query = SearchQuery {
            timestamp_start: Some(2000),
            timestamp_end: Some(4000),
            ..Default::default()
        };

        let results = index.search(&query).unwrap();
        assert_eq!(results.len(), 3); // Timestamps 2000, 3000, 4000
    }
}
