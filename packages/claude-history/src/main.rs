mod cli;
mod database;
mod ingest;
mod mcp;

use anyhow::Result;
use clap::Parser;
use cli::{CliCommand, Opts};
use tracing::Level;
use tracing_subscriber::FmtSubscriber;

#[tokio::main]
async fn main() -> Result<()> {
    // Parse command line arguments
    let opts = Opts::parse();

    // Initialize logging (to stderr, not stdout, for JSON compatibility)
    let subscriber = FmtSubscriber::builder()
        .with_max_level(if opts.verbose {
            Level::DEBUG
        } else {
            Level::INFO
        })
        .with_writer(std::io::stderr)
        .finish();

    tracing::subscriber::set_global_default(subscriber)
        .expect("Failed to set tracing subscriber");

    // Execute command
    match opts.command {
        CliCommand::Search {
            query,
            source,
            project,
            limit,
            format,
        } => {
            cli::handle_search(query, source, project, limit, format).await?;
        }
        CliCommand::List {
            project,
            sort,
            limit,
        } => {
            cli::handle_list(project, sort, limit).await?;
        }
        CliCommand::Get { session_id, format } => {
            cli::handle_get(session_id, format).await?;
        }
        CliCommand::Stats => {
            cli::handle_stats().await?;
        }
        CliCommand::McpServer => {
            mcp::run_server().await?;
        }
    }

    Ok(())
}
