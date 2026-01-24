#![forbid(unsafe_code)]

use anyhow::{Context, Result};
use clap::{Parser, Subcommand};
use std::path::PathBuf;

mod backtest_cmd;
mod spec;
mod strategies;

#[derive(Parser)]
#[command(name = "quant_engine")]
#[command(about = "AURELIUS Quant Reasoning Model - Event-Driven Backtest Engine", long_about = None)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Run a backtest
    Backtest {
        /// Path to spec JSON file
        #[arg(long)]
        spec: PathBuf,

        /// Path to data parquet file
        #[arg(long)]
        data: PathBuf,

        /// Output directory
        #[arg(long)]
        out: PathBuf,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Backtest { spec, data, out } => {
            backtest_cmd::run_backtest(&spec, &data, &out).context("Failed to run backtest")?;
        }
    }

    Ok(())
}
