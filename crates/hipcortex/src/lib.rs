#![forbid(unsafe_code)]

pub mod artifact;
pub mod audit;
pub mod index;
pub mod repository;
pub mod storage;

pub use artifact::{
    Artifact, BacktestConfig, BacktestResult, CRVReportArtifact, CostModelConfig, Dataset,
    DatasetMetadata, PolicyConstraints, StrategySpec, Trace,
};
pub use audit::{AuditLog, CommitEntry};
pub use index::{ArtifactMetadata, MetadataIndex, SearchQuery};
pub use repository::Repository;
pub use storage::{ContentHash, ContentStore};
