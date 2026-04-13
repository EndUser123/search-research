use anyhow::{Context, Result};
use chrono::{DateTime, Utc};
use rusqlite::{Connection, OpenFlags, params};
use std::path::Path;
use tracing::{debug, info};

/// Search using SQLite FTS5 full-text search
pub async fn search_fts5(
    db_path: &Path,
    query: &str,
    project: Option<&str>,
    limit: usize,
) -> Result<Vec<super::cli::SearchResult>> {
    info!("Searching SQLite FTS5 index: query='{}', project={:?}, limit={}", query, project, limit);

    if !db_path.exists() {
        info!("Database not found at {}, returning empty results", db_path.display());
        return Ok(Vec::new());
    }

    let conn = Connection::open_with_flags(
        db_path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )
    .context("Failed to open database")?;

    // Note: WAL mode is a persistent setting enabled by init_database().
    // Read-only connections cannot enable WAL (requires write access for -wal/-shm files),
    // but they benefit from WAL if already enabled by the database initialization.

    // Detect which schema exists: new (chat_messages_fts) or existing (messages_fts)
    // The existing database uses 'messages' and 'messages_fts' tables
    let (fts_table, main_table) = {
        let chat_fts_exists: i64 = conn
            .query_row(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='chat_messages_fts'",
                [],
                |row| row.get(0),
            )
            .unwrap_or(0);

        if chat_fts_exists > 0 {
            ("chat_messages_fts".to_string(), "chat_messages".to_string())
        } else {
            // Check for existing schema (messages_fts)
            let msg_fts_exists: i64 = conn
                .query_row(
                    "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='messages_fts'",
                    [],
                    |row| row.get(0),
                )
                .unwrap_or(0);

            if msg_fts_exists > 0 {
                ("messages_fts".to_string(), "messages".to_string())
            } else {
                info!("No FTS5 table found (tried chat_messages_fts and messages_fts), returning empty results");
                return Ok(Vec::new());
            }
        }
    };

    let mut results = Vec::new();

    // Build FTS5 query with JOIN to main table
    // Note: messages_fts uses content_rowid to link to messages.id
    if let Some(proj) = project {
        let sql = format!(
            "SELECT m.message_id as session_id, m.role as message_type,
                    m.timestamp, m.content, p.path as project,
                    bm25({fts}) as score,
                    snippet({fts}, -1, '<b>', '</b>', '...', 30) as snippet
             FROM {fts}
             JOIN messages m ON m.id = {fts}.rowid
             LEFT JOIN projects p ON p.id = m.project_id
             WHERE {fts} MATCH ?1 AND p.path = ?2
             ORDER BY score
             LIMIT ?3",
            fts = fts_table
        );
        let mut stmt = conn.prepare(&sql)?;
        let rows = stmt.query_map(params![query, proj, limit as i64], |row| {
            let content: String = row.get(3)?;
            let timestamp_str = row.get::<_, i64>(2)?.to_string();
            Ok(super::cli::SearchResult {
                session_id: row.get(0)?,
                message_type: row.get(1)?,
                timestamp: DateTime::from_timestamp(timestamp_str.parse().unwrap_or(0), 0)
                    .unwrap_or_else(|| DateTime::from_timestamp(0, 0).unwrap()),
                content,
                project: row.get(4)?,
                score: row.get::<_, Option<f64>>(5)?,
                snippet: row.get::<_, Option<String>>(6)?,
            })
        })?;

        for row in rows {
            results.push(row?);
        }
    } else {
        let sql = format!(
            "SELECT m.message_id as session_id, m.role as message_type,
                    m.timestamp, m.content, p.path as project,
                    bm25({fts}) as score,
                    snippet({fts}, -1, '<b>', '</b>', '...', 30) as snippet
             FROM {fts}
             JOIN messages m ON m.id = {fts}.rowid
             LEFT JOIN projects p ON p.id = m.project_id
             WHERE {fts} MATCH ?1
             ORDER BY score
             LIMIT ?2",
            fts = fts_table
        );
        let mut stmt = conn.prepare(&sql)?;
        let rows = stmt.query_map(params![query, limit as i64], |row| {
            let content: String = row.get(3)?;
            let timestamp_str = row.get::<_, i64>(2)?.to_string();
            Ok(super::cli::SearchResult {
                session_id: row.get(0)?,
                message_type: row.get(1)?,
                timestamp: DateTime::from_timestamp(timestamp_str.parse().unwrap_or(0), 0)
                    .unwrap_or_else(|| DateTime::from_timestamp(0, 0).unwrap()),
                content,
                project: row.get(4)?,
                score: row.get::<_, Option<f64>>(5)?,
                snippet: row.get::<_, Option<String>>(6)?,
            })
        })?;

        for row in rows {
            results.push(row?);
        }
    }

    Ok(results)
}

/// Fallback LIKE search when no FTS5 table exists
fn search_like(
    conn: &Connection,
    main_table: &str,
    query: &str,
    project: Option<&str>,
    limit: usize,
) -> Result<Vec<super::cli::SearchResult>> {
        let mut results = Vec::new();
        let search_pattern = format!("%{}%", query);
        if let Some(proj) = project {
            let sql = format!(
                "SELECT session_id, message_type, timestamp, content, project, NULL as score
                 FROM {}
                 WHERE content LIKE ?1 AND project = ?2
                 ORDER BY timestamp DESC
                 LIMIT ?3",
                main_table
            );
            let mut stmt = conn.prepare(&sql)?;
            let rows = stmt.query_map(params![search_pattern, proj, limit as i64], |row| {
                let content: String = row.get(3)?;
                Ok(super::cli::SearchResult {
                    session_id: row.get(0)?,
                    message_type: row.get(1)?,
                    timestamp: parse_timestamp(row.get::<_, String>(2)?.as_str())
                        .unwrap_or_else(|_| DateTime::from_timestamp(0, 0).unwrap()),
                    content,
                    project: row.get(4)?,
                    score: None,
                    snippet: None,
                })
            })?;

            for row in rows {
                results.push(row?);
            }
        } else {
            let sql = format!(
                "SELECT session_id, message_type, timestamp, content, project, NULL as score
                 FROM {}
                 WHERE content LIKE ?1
                 ORDER BY timestamp DESC
                 LIMIT ?2",
                main_table
            );
            let mut stmt = conn.prepare(&sql)?;
            let rows = stmt.query_map(params![search_pattern, limit as i64], |row| {
                let content: String = row.get(3)?;
                Ok(super::cli::SearchResult {
                    session_id: row.get(0)?,
                    message_type: row.get(1)?,
                    timestamp: parse_timestamp(row.get::<_, String>(2)?.as_str())
                        .unwrap_or_else(|_| DateTime::from_timestamp(0, 0).unwrap()),
                    content,
                    project: row.get(4)?,
                    score: None,
                    snippet: None,
                })
            })?;

            for row in rows {
                results.push(row?);
            }
        }

    Ok(results)
}

/// Count total messages in database
pub async fn count_messages(db_path: &Path) -> Result<usize> {
    if !db_path.exists() {
        return Ok(0);
    }

    let conn = Connection::open_with_flags(
        db_path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_NO_MUTEX,
    )
    .context("Failed to open database")?;

    let count: i64 = conn
        .query_row("SELECT COUNT(*) FROM chat_messages", [], |row| row.get(0))
        .unwrap_or(0);

    Ok(count as usize)
}

/// Initialize database with FTS5 table
pub async fn init_database(db_path: &Path) -> Result<()> {
    info!("Initializing database at {}", db_path.display());

    // Create parent directory if it doesn't exist
    if let Some(parent) = db_path.parent() {
        std::fs::create_dir_all(parent).context("Failed to create database directory")?;
    }

    let conn = Connection::open(db_path).context("Failed to create database")?;

    // Enable WAL mode
    conn.execute("PRAGMA journal_mode=WAL", [])
        .context("Failed to enable WAL mode")?;

    // Create main table
    conn.execute(
        "CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            message_type TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            content TEXT NOT NULL,
            project TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )",
        [],
    )
    .context("Failed to create chat_messages table")?;

    // Create FTS5 virtual table with Porter stemmer
    conn.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS chat_messages_fts USING fts5(
            session_id, message_type, timestamp, content, project,
            content_rowid=rowid,
            tokenize='porter unicode61'
        )",
        [],
    )
    .context("Failed to create FTS5 table")?;

    // Create triggers to keep FTS5 in sync
    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS chat_messages_ai AFTER INSERT ON chat_messages BEGIN
            INSERT INTO chat_messages_fts(rowid, session_id, message_type, timestamp, content, project)
            VALUES (new.id, new.session_id, new.message_type, new.timestamp, new.content, new.project);
        END",
        [],
    )
    .context("Failed to create INSERT trigger")?;

    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS chat_messages_ad AFTER DELETE ON chat_messages BEGIN
            INSERT INTO chat_messages_fts(chat_messages_fts, rowid, session_id, message_type, timestamp, content, project)
            VALUES ('delete', old.id, old.session_id, old.message_type, old.timestamp, old.content, old.project);
        END",
        [],
    )
    .context("Failed to create DELETE trigger")?;

    conn.execute(
        "CREATE TRIGGER IF NOT EXISTS chat_messages_au AFTER UPDATE ON chat_messages BEGIN
            INSERT INTO chat_messages_fts(chat_messages_fts, rowid, session_id, message_type, timestamp, content, project)
            VALUES ('delete', old.id, old.session_id, old.message_type, old.timestamp, old.content, old.project);
            INSERT INTO chat_messages_fts(rowid, session_id, message_type, timestamp, content, project)
            VALUES (new.id, new.session_id, new.message_type, new.timestamp, new.content, new.project);
        END",
        [],
    )
    .context("Failed to create UPDATE trigger")?;

    // Create indexes for common queries
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_session_id ON chat_messages(session_id)",
        [],
    )
    .context("Failed to create session_id index")?;

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_timestamp ON chat_messages(timestamp)",
        [],
    )
    .context("Failed to create timestamp index")?;

    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_project ON chat_messages(project)",
        [],
    )
    .context("Failed to create project index")?;

    info!("Database initialized successfully");
    Ok(())
}

/// Insert a message into the database
pub async fn insert_message(
    db_path: &Path,
    session_id: &str,
    message_type: &str,
    timestamp: &str,
    content: &str,
    project: &str,
) -> Result<()> {
    let conn = Connection::open(db_path).context("Failed to open database")?;

    conn.execute(
        "INSERT INTO chat_messages (session_id, message_type, timestamp, content, project)
         VALUES (?1, ?2, ?3, ?4, ?5)",
        [session_id, message_type, timestamp, content, project],
    )
    .context("Failed to insert message")?;

    Ok(())
}

/// Parse an ISO 8601 timestamp string into DateTime<Utc>
///
/// # Arguments
/// * `s` - Timestamp string in ISO 8601 format (e.g., "2026-03-18T12:00:00Z")
///
/// # Returns
/// * `Ok(DateTime<Utc>)` - Parsed timestamp
/// * `Err` - If the timestamp is not in valid ISO 8601 format
pub fn parse_timestamp(s: &str) -> Result<DateTime<Utc>> {
    DateTime::parse_from_rfc3339(s)
        .map(|dt| dt.with_timezone(&Utc))
        .context("Failed to parse timestamp")
}
