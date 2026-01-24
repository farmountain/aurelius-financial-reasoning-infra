use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use hipcortex::{Artifact, ContentHash, Repository, SearchQuery};
use std::path::PathBuf;

#[derive(Parser)]
#[command(name = "hipcortex")]
#[command(about = "HipCortex - Content-Addressed Artifact Storage for Quant Research", long_about = None)]
struct Cli {
    /// Path to HipCortex repository
    #[arg(long, default_value = ".hipcortex")]
    repo: PathBuf,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Commit an artifact to the repository
    Commit {
        /// Path to artifact JSON file
        #[arg(long)]
        artifact: PathBuf,

        /// Commit message
        #[arg(long)]
        message: String,

        /// Parent artifact hashes (for lineage tracking)
        #[arg(long)]
        parent: Vec<String>,
    },

    /// Show artifact details
    Show {
        /// Artifact hash
        hash: String,

        /// Show full details (including data)
        #[arg(long)]
        full: bool,
    },

    /// Show differences between two artifacts
    Diff {
        /// First artifact hash
        hash1: String,

        /// Second artifact hash
        hash2: String,
    },

    /// Replay a computation to verify reproducibility
    Replay {
        /// Backtest result hash to replay
        hash: String,

        /// Path to data file for replay
        #[arg(long)]
        data: PathBuf,
    },

    /// Search artifacts
    Search {
        /// Artifact type filter
        #[arg(long)]
        artifact_type: Option<String>,

        /// Goal filter
        #[arg(long)]
        goal: Option<String>,

        /// Regime tag filter
        #[arg(long)]
        tag: Vec<String>,

        /// Policy filter
        #[arg(long)]
        policy: Option<String>,

        /// Maximum number of results
        #[arg(long, default_value = "10")]
        limit: usize,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Commit {
            artifact,
            message,
            parent,
        } => {
            let mut repo = Repository::open(&cli.repo)
                .context("Failed to open repository")?;

            // Validate artifact path
            let artifact = artifact.canonicalize()
                .context("Failed to resolve artifact path")?;
            
            // Read artifact from file
            let artifact_data = std::fs::read_to_string(&artifact)
                .context("Failed to read artifact file")?;
            let artifact: Artifact = serde_json::from_str(&artifact_data)
                .context("Failed to parse artifact JSON")?;

            // Commit artifact
            let hash = repo.commit(&artifact, &message, parent)
                .context("Failed to commit artifact")?;

            println!("Committed artifact: {}", hash);
        }

        Commands::Show { hash, full } => {
            let repo = Repository::open(&cli.repo)
                .context("Failed to open repository")?;

            let content_hash = ContentHash::from_hex(hash.clone());

            // Get metadata
            let metadata = repo.metadata(&content_hash)
                .context("Failed to get metadata")?;

            if let Some(metadata) = metadata {
                println!("Artifact: {}", hash);
                println!("Type: {}", metadata.artifact_type);
                println!("Timestamp: {}", metadata.timestamp);
                if let Some(goal) = metadata.goal {
                    println!("Goal: {}", goal);
                }
                if !metadata.regime_tags.is_empty() {
                    println!("Regime Tags: {}", metadata.regime_tags.join(", "));
                }
                if let Some(policy) = metadata.policy {
                    println!("Policy: {}", policy);
                }
                if let Some(desc) = metadata.description {
                    println!("Description: {}", desc);
                }

                // Show commit history
                let history = repo.history(&content_hash)
                    .context("Failed to get history")?;
                if !history.is_empty() {
                    println!("\nCommit History:");
                    for entry in history {
                        println!("  - {} at {}: {}", entry.artifact_hash, entry.timestamp, entry.message);
                    }
                }

                if full {
                    println!("\nFull Artifact:");
                    let artifact = repo.get(&content_hash)
                        .context("Failed to get artifact")?;
                    let json = serde_json::to_string_pretty(&artifact)
                        .context("Failed to serialize artifact")?;
                    println!("{}", json);
                }
            } else {
                println!("Artifact not found: {}", hash);
            }
        }

        Commands::Diff { hash1, hash2 } => {
            let repo = Repository::open(&cli.repo)
                .context("Failed to open repository")?;

            let content_hash1 = ContentHash::from_hex(hash1.clone());
            let content_hash2 = ContentHash::from_hex(hash2.clone());

            let artifact1 = repo.get(&content_hash1)
                .context("Failed to get first artifact")?;
            let artifact2 = repo.get(&content_hash2)
                .context("Failed to get second artifact")?;

            let json1 = serde_json::to_string_pretty(&artifact1)
                .context("Failed to serialize first artifact")?;
            let json2 = serde_json::to_string_pretty(&artifact2)
                .context("Failed to serialize second artifact")?;

            println!("Diff between {} and {}:\n", hash1, hash2);
            println!("Artifact 1 type: {}", artifact1.artifact_type());
            println!("Artifact 2 type: {}", artifact2.artifact_type());

            if artifact1.artifact_type() == artifact2.artifact_type() {
                println!("\nArtifact 1:");
                println!("{}", json1);
                println!("\nArtifact 2:");
                println!("{}", json2);
            } else {
                println!("\nArtifacts have different types, cannot compare directly.");
            }
        }

        Commands::Replay { hash, data: _ } => {
            let repo = Repository::open(&cli.repo)
                .context("Failed to open repository")?;

            let content_hash = ContentHash::from_hex(hash.clone());
            let artifact = repo.get(&content_hash)
                .context("Failed to get artifact")?;

            match artifact {
                Artifact::BacktestResult(result) => {
                    println!("Replaying backtest result: {}", hash);
                    println!("Original config hash: {}", result.config_hash);
                    println!("Original execution timestamp: {}", result.execution_timestamp);
                    println!("Original stats:");
                    println!("  Final equity: {:.2}", result.stats.final_equity);
                    println!("  Total return: {:.2}%", result.stats.total_return * 100.0);
                    println!("  Sharpe ratio: {:.4}", result.stats.sharpe_ratio);
                    println!("  Max drawdown: {:.2}%", result.stats.max_drawdown * 100.0);

                    // Get the config
                    let config_hash = ContentHash::from_hex(result.config_hash.clone());
                    let config_artifact = repo.get(&config_hash)
                        .context("Failed to get config artifact")?;

                    match config_artifact {
                        Artifact::BacktestConfig(config) => {
                            println!("\nReplay Configuration:");
                            println!("  Initial cash: {:.2}", config.initial_cash);
                            println!("  Seed: {}", config.seed);
                            println!("  Strategy hash: {}", config.strategy_hash);
                            println!("  Dataset hash: {}", config.dataset_hash);

                            // In a real implementation, we would:
                            // 1. Load the dataset from the hash
                            // 2. Load the strategy from the hash
                            // 3. Re-run the backtest with the same parameters
                            // 4. Compare the new result hash with the original

                            println!("\nReplay verification:");
                            println!("  ✓ Configuration retrieved successfully");
                            println!("  ✓ Strategy hash: {}", config.strategy_hash);
                            println!("  ✓ Dataset hash: {}", config.dataset_hash);
                            println!("\nNote: Full replay requires integration with backtest engine.");
                            println!("This command demonstrates hash-based reproducibility tracking.");

                            // Compute hash of the original result
                            let result_artifact = Artifact::BacktestResult(result.clone());
                            let computed_hash = hipcortex::ContentHash::compute(&result_artifact)
                                .context("Failed to compute hash")?;
                            
                            if computed_hash.as_hex() == hash {
                                println!("\n✓ Result hash verification PASSED");
                                println!("  Original hash matches recomputed hash");
                            } else {
                                println!("\n✗ Result hash verification FAILED");
                                println!("  Expected: {}", hash);
                                println!("  Got: {}", computed_hash.as_hex());
                            }
                        }
                        _ => {
                            println!("Config artifact is not a BacktestConfig");
                        }
                    }
                }
                _ => {
                    println!("Artifact is not a BacktestResult, cannot replay");
                }
            }
        }

        Commands::Search {
            artifact_type,
            goal,
            tag,
            policy,
            limit,
        } => {
            let repo = Repository::open(&cli.repo)
                .context("Failed to open repository")?;

            let query = SearchQuery {
                artifact_type,
                goal,
                regime_tags: if tag.is_empty() { None } else { Some(tag) },
                policy,
                timestamp_start: None,
                timestamp_end: None,
                limit: Some(limit),
            };

            let results = repo.search(&query)
                .context("Failed to search artifacts")?;

            if results.is_empty() {
                println!("No artifacts found matching the query");
            } else {
                println!("Found {} artifact(s):\n", results.len());
                for result in results {
                    println!("Hash: {}", result.hash);
                    println!("  Type: {}", result.artifact_type);
                    println!("  Timestamp: {}", result.timestamp);
                    if let Some(goal) = result.goal {
                        println!("  Goal: {}", goal);
                    }
                    if !result.regime_tags.is_empty() {
                        println!("  Tags: {}", result.regime_tags.join(", "));
                    }
                    if let Some(desc) = result.description {
                        println!("  Description: {}", desc);
                    }
                    println!();
                }
            }
        }
    }

    Ok(())
}
