#![forbid(unsafe_code)]

pub mod types;
pub mod verifier;

pub use types::{CRVReport, CRVViolation, RuleId, Severity};
pub use verifier::{CRVVerifier, PolicyConstraints, UniverseMetadata};
