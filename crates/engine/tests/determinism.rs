//! Sprint 1 Determinism Scaffold Tests
//!
//! These tests validate stable primitives for determinism verification.
//! They do NOT test backtest engine outputs (which will be added in Sprint 2).
//!
//! Test coverage:
//! 1. Canonical byte hashing (SHA-256) - ensures identical inputs produce identical hashes
//! 2. Seeded pseudo-random number generation - ensures seeded RNG produces reproducible sequences
//!
//! All tests are designed to be:
//! - Fast (< 1ms each)
//! - Stable across runs and machines
//! - Independent of unfinished backtest outputs

use engine::{canonical_json_hash, stable_hash_bytes};
use rand::Rng;
use rand::SeedableRng;
use rand_chacha::ChaCha8Rng;
use serde::Serialize;

// Test constants
const TEST_SEED_1: u64 = 42;
const TEST_SEED_2: u64 = 43;
const TEST_SEED_3: u64 = 123;
const TEST_SEED_4: u64 = 999;
const NUM_SAMPLES: usize = 100;
const NUM_SAMPLES_SMALL: usize = 50;
const NUM_RANDOM_BYTES: usize = 32;
const NUM_ITERATIONS: usize = 1000;
const NUM_RESET_TESTS: usize = 10;

/// Test that stable_hash_bytes produces deterministic hashes
#[test]
fn test_hash_determinism_basic() {
    let data = b"deterministic test data";

    // Hash the same data multiple times
    let hash1 = stable_hash_bytes(data);
    let hash2 = stable_hash_bytes(data);
    let hash3 = stable_hash_bytes(data);

    // All hashes must be identical
    assert_eq!(hash1, hash2);
    assert_eq!(hash2, hash3);
    assert_eq!(hash1, hash3);
}

/// Test that stable_hash_bytes produces different hashes for different inputs
#[test]
fn test_hash_uniqueness() {
    let data1 = b"input one";
    let data2 = b"input two";

    let hash1 = stable_hash_bytes(data1);
    let hash2 = stable_hash_bytes(data2);

    // Different inputs must produce different hashes
    assert_ne!(hash1, hash2);
}

/// Test canonical JSON hashing with a small struct
#[test]
fn test_canonical_json_hash_determinism() {
    #[derive(Serialize)]
    struct TestConfig {
        strategy: String,
        lookback: i32,
        threshold: f64,
    }

    let config = TestConfig {
        strategy: "momentum".to_string(),
        lookback: 20,
        threshold: 0.5,
    };

    // Hash the same struct multiple times
    let hash1 = canonical_json_hash(&config).expect("JSON serialization failed");
    let hash2 = canonical_json_hash(&config).expect("JSON serialization failed");
    let hash3 = canonical_json_hash(&config).expect("JSON serialization failed");

    // All hashes must be identical
    assert_eq!(hash1, hash2);
    assert_eq!(hash2, hash3);
}

/// Test that canonical JSON hashing is sensitive to field changes
#[test]
fn test_canonical_json_hash_sensitivity() {
    #[derive(Serialize)]
    struct Config {
        value: i32,
    }

    let config1 = Config { value: 42 };
    let config2 = Config { value: 43 };

    let hash1 = canonical_json_hash(&config1).expect("JSON serialization failed");
    let hash2 = canonical_json_hash(&config2).expect("JSON serialization failed");

    // Different field values must produce different hashes
    assert_ne!(hash1, hash2);
}

/// Test seeded PRNG produces reproducible sequences
#[test]
fn test_seeded_rng_determinism() {
    // Generate first sequence
    let mut rng1 = ChaCha8Rng::seed_from_u64(TEST_SEED_1);
    let sequence1: Vec<f64> = (0..NUM_SAMPLES).map(|_| rng1.gen::<f64>()).collect();

    // Generate second sequence with same seed
    let mut rng2 = ChaCha8Rng::seed_from_u64(TEST_SEED_1);
    let sequence2: Vec<f64> = (0..NUM_SAMPLES).map(|_| rng2.gen::<f64>()).collect();

    // Sequences must be identical
    assert_eq!(sequence1, sequence2);
}

/// Test seeded PRNG produces different sequences for different seeds
#[test]
fn test_seeded_rng_different_seeds() {
    // Generate sequence with seed 42
    let mut rng1 = ChaCha8Rng::seed_from_u64(TEST_SEED_1);
    let sequence1: Vec<f64> = (0..NUM_SAMPLES).map(|_| rng1.gen::<f64>()).collect();

    // Generate sequence with seed 43
    let mut rng2 = ChaCha8Rng::seed_from_u64(TEST_SEED_2);
    let sequence2: Vec<f64> = (0..NUM_SAMPLES).map(|_| rng2.gen::<f64>()).collect();

    // Sequences must be different
    assert_ne!(sequence1, sequence2);
}

/// Test combined determinism: hash of RNG-generated data
#[test]
fn test_combined_hash_and_rng_determinism() {
    // Run 1: Generate random data and hash it
    let mut rng1 = ChaCha8Rng::seed_from_u64(TEST_SEED_3);
    let data1: Vec<u8> = (0..NUM_RANDOM_BYTES).map(|_| rng1.gen::<u8>()).collect();
    let hash1 = stable_hash_bytes(&data1);

    // Run 2: Generate random data with same seed and hash it
    let mut rng2 = ChaCha8Rng::seed_from_u64(TEST_SEED_3);
    let data2: Vec<u8> = (0..NUM_RANDOM_BYTES).map(|_| rng2.gen::<u8>()).collect();
    let hash2 = stable_hash_bytes(&data2);

    // Data and hashes must be identical
    assert_eq!(data1, data2);
    assert_eq!(hash1, hash2);
}

/// Test that hashing is stable across multiple iterations in a loop
#[test]
fn test_hash_stability_in_loop() {
    let data = b"loop test data";
    let expected_hash = stable_hash_bytes(data);

    // Hash the same data many times and verify stability
    for _ in 0..NUM_ITERATIONS {
        let hash = stable_hash_bytes(data);
        assert_eq!(
            hash, expected_hash,
            "Hash should remain stable across iterations"
        );
    }
}

/// Test RNG stability across multiple resets
#[test]
fn test_rng_stability_across_resets() {
    // Generate reference sequence
    let mut rng_ref = ChaCha8Rng::seed_from_u64(TEST_SEED_4);
    let expected: Vec<f64> = (0..NUM_SAMPLES_SMALL)
        .map(|_| rng_ref.gen::<f64>())
        .collect();

    // Test multiple times that we get the same sequence after resetting
    for _ in 0..NUM_RESET_TESTS {
        let mut rng = ChaCha8Rng::seed_from_u64(TEST_SEED_4);
        let sequence: Vec<f64> = (0..NUM_SAMPLES_SMALL).map(|_| rng.gen::<f64>()).collect();
        assert_eq!(
            sequence, expected,
            "RNG sequence should be stable after reset"
        );
    }
}
