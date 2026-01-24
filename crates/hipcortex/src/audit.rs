use crate::storage::ContentHash;
use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

/// A commit entry in the audit log
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct CommitEntry {
    pub timestamp: i64,
    pub artifact_hash: String,
    pub artifact_type: String,
    pub message: String,
    pub parent_hashes: Vec<String>,
}

/// Append-only audit log for artifact commits
pub struct AuditLog {
    path: PathBuf,
}

impl AuditLog {
    /// Create a new audit log at the given path
    pub fn new<P: AsRef<Path>>(path: P) -> Result<Self> {
        let path = path.as_ref().to_path_buf();

        // Create parent directory if it doesn't exist
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).context("Failed to create audit log directory")?;
        }

        // Create file if it doesn't exist
        if !path.exists() {
            File::create(&path).context("Failed to create audit log file")?;
        }

        Ok(Self { path })
    }

    /// Append a commit entry to the log
    pub fn append(&self, entry: &CommitEntry) -> Result<()> {
        let mut file = OpenOptions::new()
            .append(true)
            .create(true)
            .open(&self.path)
            .context("Failed to open audit log for append")?;

        let json = serde_json::to_string(entry).context("Failed to serialize commit entry")?;

        writeln!(file, "{}", json).context("Failed to write to audit log")?;

        Ok(())
    }

    /// Get all commit entries from the log
    pub fn entries(&self) -> Result<Vec<CommitEntry>> {
        if !self.path.exists() {
            return Ok(Vec::new());
        }

        let file = File::open(&self.path).context("Failed to open audit log for reading")?;
        let reader = BufReader::new(file);

        let mut entries = Vec::new();
        for line in reader.lines() {
            let line = line.context("Failed to read line from audit log")?;
            if line.trim().is_empty() {
                continue;
            }
            let entry: CommitEntry =
                serde_json::from_str(&line).context("Failed to deserialize commit entry")?;
            entries.push(entry);
        }

        Ok(entries)
    }

    /// Get entries for a specific artifact hash
    pub fn entries_for_artifact(&self, hash: &ContentHash) -> Result<Vec<CommitEntry>> {
        let all_entries = self.entries()?;
        Ok(all_entries
            .into_iter()
            .filter(|e| e.artifact_hash == hash.as_hex())
            .collect())
    }

    /// Get the most recent commit entry
    pub fn latest(&self) -> Result<Option<CommitEntry>> {
        let entries = self.entries()?;
        Ok(entries.into_iter().last())
    }

    /// Get commits within a time range
    pub fn entries_in_range(&self, start: i64, end: i64) -> Result<Vec<CommitEntry>> {
        let all_entries = self.entries()?;
        Ok(all_entries
            .into_iter()
            .filter(|e| e.timestamp >= start && e.timestamp <= end)
            .collect())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_audit_log_append_and_read() {
        let temp_dir = TempDir::new().unwrap();
        let log_path = temp_dir.path().join("audit.log");
        let log = AuditLog::new(&log_path).unwrap();

        let entry1 = CommitEntry {
            timestamp: 1000,
            artifact_hash: "abc123".to_string(),
            artifact_type: "strategy_spec".to_string(),
            message: "Initial commit".to_string(),
            parent_hashes: vec![],
        };

        let entry2 = CommitEntry {
            timestamp: 2000,
            artifact_hash: "def456".to_string(),
            artifact_type: "backtest_result".to_string(),
            message: "Backtest run".to_string(),
            parent_hashes: vec!["abc123".to_string()],
        };

        log.append(&entry1).unwrap();
        log.append(&entry2).unwrap();

        let entries = log.entries().unwrap();
        assert_eq!(entries.len(), 2);
        assert_eq!(entries[0], entry1);
        assert_eq!(entries[1], entry2);
    }

    #[test]
    fn test_audit_log_latest() {
        let temp_dir = TempDir::new().unwrap();
        let log_path = temp_dir.path().join("audit.log");
        let log = AuditLog::new(&log_path).unwrap();

        // Empty log should return None
        assert!(log.latest().unwrap().is_none());

        let entry = CommitEntry {
            timestamp: 1000,
            artifact_hash: "abc123".to_string(),
            artifact_type: "strategy_spec".to_string(),
            message: "Initial commit".to_string(),
            parent_hashes: vec![],
        };

        log.append(&entry).unwrap();

        let latest = log.latest().unwrap();
        assert!(latest.is_some());
        assert_eq!(latest.unwrap(), entry);
    }

    #[test]
    fn test_audit_log_time_range() {
        let temp_dir = TempDir::new().unwrap();
        let log_path = temp_dir.path().join("audit.log");
        let log = AuditLog::new(&log_path).unwrap();

        let entry1 = CommitEntry {
            timestamp: 1000,
            artifact_hash: "abc123".to_string(),
            artifact_type: "strategy_spec".to_string(),
            message: "First commit".to_string(),
            parent_hashes: vec![],
        };

        let entry2 = CommitEntry {
            timestamp: 2000,
            artifact_hash: "def456".to_string(),
            artifact_type: "backtest_result".to_string(),
            message: "Second commit".to_string(),
            parent_hashes: vec![],
        };

        let entry3 = CommitEntry {
            timestamp: 3000,
            artifact_hash: "ghi789".to_string(),
            artifact_type: "crv_report".to_string(),
            message: "Third commit".to_string(),
            parent_hashes: vec![],
        };

        log.append(&entry1).unwrap();
        log.append(&entry2).unwrap();
        log.append(&entry3).unwrap();

        let entries = log.entries_in_range(1500, 2500).unwrap();
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0], entry2);
    }
}
