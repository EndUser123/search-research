-- CHS v2 Database Schema
-- Chat History Search v2 with FTS5, embeddings, and topic tracking

-- Core Tables

-- Projects: one per repository/workspace root
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    label TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

-- Sessions: logical conversation threads
-- provider: which history provider owns this session
--   ('claude_code_raw', 'codex_desktop', 'claude_log', 'grok_sessions')
CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY,
    session_key TEXT NOT NULL,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    provider TEXT NOT NULL DEFAULT 'unknown',
    started_at INTEGER NOT NULL,
    ended_at INTEGER,
    is_closed INTEGER NOT NULL DEFAULT 0,
    message_count INTEGER NOT NULL DEFAULT 0,
    first_prompt TEXT,
    summary_short TEXT,
    summary_long TEXT,
    embedding BLOB,
    embedding_model TEXT,
    embedding_dim INTEGER,
    embedding_run_id TEXT,
    last_turn_built_message_id INTEGER,
    last_message_timestamp INTEGER,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_project_session_key
ON sessions(project_id, session_key);

-- Messages: atomic conversation units
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    message_id TEXT NOT NULL UNIQUE,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    timestamp INTEGER NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'tool', 'system')),
    provider TEXT NOT NULL DEFAULT 'unknown',
    content TEXT NOT NULL,
    has_code INTEGER NOT NULL DEFAULT 0,
    has_error INTEGER NOT NULL DEFAULT 0,
    raw_json TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

CREATE INDEX IF NOT EXISTS idx_messages_session_time
ON messages(session_id, timestamp);

-- Turns: conversational retrieval units
CREATE TABLE IF NOT EXISTS turns (
    id INTEGER PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    start_message_id INTEGER NOT NULL REFERENCES messages(id),
    end_message_id INTEGER NOT NULL REFERENCES messages(id),
    timestamp_start INTEGER NOT NULL,
    timestamp_end INTEGER NOT NULL,
    content TEXT NOT NULL,
    has_code INTEGER NOT NULL DEFAULT 0,
    has_error INTEGER NOT NULL DEFAULT 0,
    length_chars INTEGER,
    embedding BLOB,
    embedding_model TEXT,
    embedding_dim INTEGER,
    embedding_run_id TEXT,
    created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')),
    UNIQUE(session_id, start_message_id, end_message_id)
);

CREATE INDEX IF NOT EXISTS idx_turns_session_time
ON turns(session_id, timestamp_start);

-- Checkpoint tracking for incremental indexing
CREATE TABLE IF NOT EXISTS indexer_checkpoint (
    file_identity TEXT PRIMARY KEY,
    file_position INTEGER NOT NULL,
    last_processed_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))
);

-- FTS5 Virtual Tables for full-text search

CREATE VIRTUAL TABLE IF NOT EXISTS turns_fts USING fts5(
    content,
    content=turns,
    content_rowid=rowid
);

CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
    message_id,
    role,
    content,
    content=messages,
    content_rowid=rowid
);

-- Topic Tables

-- Topics: Discovered topics across sessions
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_name TEXT UNIQUE NOT NULL,
    topic_type TEXT DEFAULT 'general',
    first_seen_at TEXT DEFAULT (datetime('now')),
    last_seen_at TEXT DEFAULT (datetime('now')),
    occurrence_count INTEGER DEFAULT 1,
    metadata TEXT
);

-- Session Topics: Many-to-many relationship
CREATE TABLE IF NOT EXISTS session_topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    weight REAL DEFAULT 1.0,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(session_id, topic_id)
);

-- Operational Tables

-- Indexer Checkpoints: Track incremental indexing progress
CREATE TABLE IF NOT EXISTS indexer_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT UNIQUE NOT NULL,
    file_hash TEXT NOT NULL,
    last_indexed_position INTEGER DEFAULT 0,
    last_indexed_at TEXT DEFAULT (datetime('now')),
    metadata TEXT
);

-- Embeddings Config: Track embedding model versions
CREATE TABLE IF NOT EXISTS embeddings_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_name TEXT NOT NULL,
    embedding_dim INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    is_active INTEGER DEFAULT 1
);

-- Embedding Runs: run-level provenance for every (re-)embedding pass.
-- Rows in sessions/turns reference embedding_run_id, so mixed states are
-- detectable and any embedding batch can be traced to model + source digest.
CREATE TABLE IF NOT EXISTS embedding_runs (
    run_id TEXT PRIMARY KEY,
    model_name TEXT NOT NULL,
    embedding_dim INTEGER NOT NULL,
    distance TEXT NOT NULL DEFAULT 'cosine',
    target_table TEXT NOT NULL,
    source_digest TEXT NOT NULL,
    params_json TEXT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    row_count INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running'
        CHECK(status IN ('running', 'complete', 'failed'))
);

-- Triggers for FTS5 synchronization

-- Turns FTS triggers
CREATE TRIGGER IF NOT EXISTS turns_fts_insert AFTER INSERT ON turns BEGIN
    INSERT INTO turns_fts(rowid, content)
    VALUES (NEW.id, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS turns_fts_update AFTER UPDATE ON turns BEGIN
    UPDATE turns_fts
    SET content = NEW.content
    WHERE rowid = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS turns_fts_delete AFTER DELETE ON turns BEGIN
    DELETE FROM turns_fts WHERE rowid = OLD.id;
END;

-- Messages FTS triggers
CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, message_id, role, content)
    VALUES (NEW.id, NEW.message_id, NEW.role, NEW.content);
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_update AFTER UPDATE ON messages BEGIN
    UPDATE messages_fts
    SET message_id = NEW.message_id,
        role = NEW.role,
        content = NEW.content
    WHERE rowid = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS messages_fts_delete AFTER DELETE ON messages BEGIN
    DELETE FROM messages_fts WHERE rowid = OLD.id;
END;

-- Indexes for performance

CREATE INDEX IF NOT EXISTS idx_sessions_project_id ON sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_provider ON messages(provider);
CREATE INDEX IF NOT EXISTS idx_turns_session_id ON turns(session_id);
CREATE INDEX IF NOT EXISTS idx_session_topics_session_id ON session_topics(session_id);
CREATE INDEX IF NOT EXISTS idx_session_topics_topic_id ON session_topics(topic_id);
CREATE INDEX IF NOT EXISTS idx_indexer_checkpoints_file_path ON indexer_checkpoints(file_path);
CREATE INDEX IF NOT EXISTS idx_embeddings_config_is_active ON embeddings_config(is_active);

-- Normalized events from all providers
-- PK is (provider_id, source_id, content_hash) per D4
CREATE TABLE IF NOT EXISTS events (
    provider_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    event_id TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    conversation_id TEXT,
    session_id TEXT,
    terminal_id TEXT,
    turn_id TEXT,
    occurred_at TEXT NOT NULL,
    raw_payload_path TEXT NOT NULL,
    cached_at TEXT NOT NULL,  -- when we ingested it (for freshness signal)
    metadata_json TEXT,
    PRIMARY KEY (provider_id, source_id, content_hash)
);

CREATE INDEX IF NOT EXISTS idx_events_provider_id ON events(provider_id);
CREATE INDEX IF NOT EXISTS idx_events_provider_occurred ON events(provider_id, occurred_at);

-- Task events from hooks: task_opened, task_updated, task_resolved, task_reopened, opportunity_detected
CREATE TABLE IF NOT EXISTS event_log (
    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    raw_event_path TEXT,
    UNIQUE(task_id, event_type, occurred_at, content_hash)
);

CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    provider_id TEXT NOT NULL,
    session_id TEXT,
    terminal_id TEXT,
    opened_at TEXT,
    updated_at TEXT,
    resolved_at TEXT,
    status TEXT,
    raw_event_path TEXT
);
