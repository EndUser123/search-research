//! Tests for database module (FTS5 search)

use anyhow::Result;

#[test]
fn test_fts5_snippet_extraction() -> Result<()> {
    // This test verifies FTS5 snippet extraction works
    use rusqlite::Connection;

    // Create in-memory database with FTS5
    let conn = Connection::open_in_memory()?;

    // Create FTS5 virtual table
    conn.execute(
        "CREATE VIRTUAL TABLE test_fts USING fts5(content)",
        [],
    )?;

    // Insert test data
    conn.execute(
        "INSERT INTO test_fts(content) VALUES ('The quick brown fox jumps over the lazy dog')",
        [],
    )?;

    // Test snippet extraction
    let snippet: String = conn.query_row(
        "SELECT snippet(test_fts, -1, '<b>', '</b>', '...', 30) FROM test_fts WHERE test_fts MATCH 'quick fox'",
        [],
        |row| row.get(0),
    )?;

    // Verify snippet contains our markers
    assert!(snippet.contains("<b>"));
    assert!(snippet.contains("</b>"));

    Ok(())
}

#[test]
fn test_bm25_ranking() -> Result<()> {
    // Test BM25 ranking works correctly
    use rusqlite::Connection;

    let conn = Connection::open_in_memory()?;

    conn.execute(
        "CREATE VIRTUAL TABLE test_fts USING fts5(content)",
        [],
    )?;

    // Insert documents with different term frequencies
    conn.execute(
        "INSERT INTO test_fts(content) VALUES ('rust rust rust programming')",
        [],
    )?;
    conn.execute(
        "INSERT INTO test_fts(content) VALUES ('rust programming')",
        [],
    )?;

    // Query with BM25 scores
    let mut stmt = conn.prepare(
        "SELECT content, bm25(test_fts) as score FROM test_fts WHERE test_fts MATCH 'rust' ORDER BY score"
    )?;

    let results: Vec<(String, f64)> = stmt.query_map([], |row| {
        Ok((row.get::<_, String>(0)?, row.get::<_, f64>(1)?))
    })?.filter_map(|r| r.ok()).collect();

    // First result should have lower BM25 score (better match)
    assert!(!results.is_empty());
    assert!(results[0].0.contains("rust rust rust"));

    Ok(())
}

#[test]
fn test_timestamp_parsing() -> Result<()> {
    // Test timestamp parsing edge cases
    use claude_history::database::parse_timestamp;

    // Valid ISO 8601 timestamp
    let result = parse_timestamp("2026-03-18T12:00:00Z")?;
    // March 18, 2026 12:00:00 UTC = 1742587200 seconds since epoch
    assert!(result.timestamp() > 1740000000);

    // Invalid timestamp returns error
    let result = parse_timestamp("invalid");
    assert!(result.is_err());

    Ok(())
}

#[test]
fn test_wal_mode_enabled() -> Result<()> {
    // Test that WAL mode can be enabled on file-based databases
    use rusqlite::Connection;
    use tempfile::NamedTempFile;

    // Create a temporary file for the database
    let temp_file = NamedTempFile::new()?;

    let conn = Connection::open(temp_file.path())?;

    // Enable WAL mode and get the result
    let journal_mode: String = conn.query_row("PRAGMA journal_mode=WAL", [], |row| row.get(0))?;

    // WAL mode should be "wal" (case may vary)
    assert_eq!(journal_mode.to_lowercase(), "wal");

    Ok(())
}
