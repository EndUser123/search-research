use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use clap::{Parser, Subcommand, ValueEnum};
use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Claude History Search - Fast keyword search for Claude Code chat history
#[derive(Parser, Debug)]
#[command(name = "claude-history")]
#[command(author = "Claude Code")]
#[command(version = "0.1.0")]
#[command(about = "Fast keyword search for Claude Code chat history using SQLite FTS5", long_about = None)]
pub struct Opts {
    /// Enable verbose logging
    #[arg(short, long)]
    pub verbose: bool,

    #[command(subcommand)]
    pub command: CliCommand,
}

#[derive(Subcommand, Debug)]
pub enum CliCommand {
    /// Search chat history for matching messages
    Search {
        /// Search query string
        query: String,

        /// Data source to search
        #[arg(short, long, value_enum, default_value_t = DataSource::Jsonl)]
        source: DataSource,

        /// Filter by project path
        #[arg(short, long)]
        project: Option<String>,

        /// Maximum number of results to return
        #[arg(short, long, default_value_t = 10)]
        limit: usize,

        /// Output format
        #[arg(short, long, value_enum, default_value_t = OutputFormat::Text)]
        format: OutputFormat,
    },

    /// List recent sessions
    List {
        /// Filter by project path
        #[arg(short, long)]
        project: Option<String>,

        /// Sort order
        #[arg(short, long, value_enum, default_value_t = SortOrder::Recent)]
        sort: SortOrder,

        /// Maximum number of sessions to list
        #[arg(short, long, default_value_t = 20)]
        limit: usize,
    },

    /// Get full details of a session
    Get {
        /// Session ID to retrieve
        session_id: String,

        /// Output format
        #[arg(short, long, value_enum, default_value_t = OutputFormat::Json)]
        format: OutputFormat,
    },

    /// Show database and index statistics
    Stats,

    /// Start MCP server mode
    McpServer,
}

/// Data source for search
#[derive(Clone, Copy, Debug, ValueEnum)]
pub enum DataSource {
    /// Search SQLite FTS5 index (fast, indexed)
    Db,
    /// Search JSONL file directly (recent messages)
    Jsonl,
}

/// Output format
#[derive(Clone, Copy, Debug, ValueEnum)]
pub enum OutputFormat {
    /// Plain text output
    Text,
    /// JSON output
    Json,
}

/// Sort order for listing sessions
#[derive(Clone, Copy, Debug, ValueEnum)]
pub enum SortOrder {
    /// Most recent first
    Recent,
    /// Oldest first
    Oldest,
    /// By project name
    Project,
}

/// Search result
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SearchResult {
    pub session_id: String,
    pub message_type: String,
    pub timestamp: DateTime<Utc>,
    pub content: String,
    pub project: String,
    pub score: Option<f64>,
    pub snippet: Option<String>,
}

/// Session summary
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SessionSummary {
    pub session_id: String,
    pub start_time: DateTime<Utc>,
    pub end_time: Option<DateTime<Utc>>,
    pub project: String,
    pub message_count: usize,
    pub title: Option<String>,
}

/// Statistics
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Stats {
    pub total_sessions: usize,
    pub total_messages: usize,
    pub indexed_messages: usize,
    pub projects: Vec<String>,
    pub db_path: String,
    pub jsonl_path: String,
}

// Default paths
pub fn default_jsonl_path() -> PathBuf {
    // Try user home directory first
    if let Ok(home) = std::env::var("USERPROFILE") {
        return PathBuf::from(home).join(".claude").join("history.jsonl");
    }
    PathBuf::from("C:/Users/brsth/.claude/history.jsonl")
}

pub fn default_db_path() -> PathBuf {
    // Use __csf data directory
    PathBuf::from("P:/__csf/data/chat_history.db")
}

// Command handlers
pub async fn handle_search(
    query: String,
    source: DataSource,
    project: Option<String>,
    limit: usize,
    format: OutputFormat,
) -> Result<()> {
    let results = match source {
        DataSource::Db => {
            // Search SQLite FTS5 index
            let db_path = default_db_path();
            super::database::search_fts5(&db_path, &query, project.as_deref(), limit).await?
        }
        DataSource::Jsonl => {
            // Search JSONL file directly
            let jsonl_path = default_jsonl_path();
            super::ingest::search_jsonl(&jsonl_path, &query, project.as_deref(), limit).await?
        }
    };

    match format {
        OutputFormat::Text => {
            println!("Found {} results:\n", results.len());
            for (i, result) in results.iter().enumerate() {
                println!("{}. [{}] {} @ {}", i + 1, result.message_type, result.session_id, result.timestamp.format("%Y-%m-%d %H:%M"));
                if let Some(score) = result.score {
                    println!("   Score: {:.2}", score);
                }
                if let Some(ref snippet) = result.snippet {
                    println!("   Snippet: {}", snippet);
                } else {
                    let content_preview: String = result.content.chars().take(100).collect();
                    println!("   Content: {}...", content_preview);
                }
                println!("   Project: {}", result.project);
                println!();
            }
        }
        OutputFormat::Json => {
            println!("{}", serde_json::to_string_pretty(&results)?);
        }
    }

    Ok(())
}

pub async fn handle_list(project: Option<String>, sort: SortOrder, limit: usize) -> Result<()> {
    let jsonl_path = default_jsonl_path();
    let sessions = super::ingest::list_sessions(&jsonl_path, project.as_deref(), sort, limit).await?;

    println!("Recent sessions ({}):\n", sessions.len());
    for (i, session) in sessions.iter().enumerate() {
        println!("{}. {}", i + 1, session.session_id);
        println!("   Project: {}", session.project);
        println!("   Started: {}", session.start_time.format("%Y-%m-%d %H:%M"));
        if let Some(end) = session.end_time {
            println!("   Ended: {}", end.format("%Y-%m-%d %H:%M"));
        }
        println!("   Messages: {}", session.message_count);
        if let Some(ref title) = session.title {
            println!("   Title: {}", title);
        }
        println!();
    }

    Ok(())
}

pub async fn handle_get(session_id: String, format: OutputFormat) -> Result<()> {
    let jsonl_path = default_jsonl_path();
    let messages = super::ingest::get_session(&jsonl_path, &session_id).await?;

    match format {
        OutputFormat::Text => {
            println!("Session {} ({} messages):\n", session_id, messages.len());
            for msg in messages {
                println!("[{}] {} @ {}", msg.message_type, msg.session_id, msg.timestamp.format("%Y-%m-%d %H:%M:%S"));
                println!("{}\n", msg.content);
            }
        }
        OutputFormat::Json => {
            println!("{}", serde_json::to_string_pretty(&messages)?);
        }
    }

    Ok(())
}

pub async fn handle_stats() -> Result<()> {
    let jsonl_path = default_jsonl_path();
    let db_path = default_db_path();

    let stats = Stats {
        total_sessions: super::ingest::count_sessions(&jsonl_path).await?,
        total_messages: super::ingest::count_messages(&jsonl_path).await?,
        indexed_messages: if db_path.exists() {
            super::database::count_messages(&db_path).await.unwrap_or(0)
        } else {
            0
        },
        projects: super::ingest::list_projects(&jsonl_path).await?,
        db_path: db_path.to_string_lossy().to_string(),
        jsonl_path: jsonl_path.to_string_lossy().to_string(),
    };

    println!("Claude History Statistics:\n");
    println!("Total Sessions: {}", stats.total_sessions);
    println!("Total Messages: {}", stats.total_messages);
    println!("Indexed Messages: {}", stats.indexed_messages);
    println!("Projects: {}", stats.projects.join(", "));
    println!("\nData Sources:");
    println!("  JSONL: {}", stats.jsonl_path);
    println!("  Database: {}", stats.db_path);

    Ok(())
}
