//! Claude History - Fast keyword search for Claude Code chat history
//!
//! This library provides SQLite FTS5-based full-text search for Claude Code
//! chat history stored in JSONL format.

pub mod cli;
pub mod database;
pub mod ingest;
pub mod mcp;
