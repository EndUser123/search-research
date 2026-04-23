"""Test CHS v2 database schema and configuration.

These tests verify the CHS v2 database initialization, configuration loading,
and core database operations. Implementation files (schema.sql, config.py, db.py)
will be created in the GREEN phase.

Run with: pytest P:/__csf/src/knowledge/systems/chs/v2/tests/test_db.py -v
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from .config import Config
from .db import (
    get_connection,
    database_is_initialized,
    init_db,
    load_embeddings_config,
    set_embeddings_config,
)


class TestConfigClass:
    """Tests for Config class environment variable loading."""

    def test_config_loads_chs_db_path_from_env(self, monkeypatch):
        """Test Config loads CHS_DB_PATH from environment variable.

        Given: CHS_DB_PATH environment variable is set
        When: Config is instantiated
        Then: db_path attribute should match the environment value
        """
        monkeypatch.setenv("CHS_DB_PATH", "P:/__csf/data/chat_history.db")
        config = Config()
        assert config.db_path == Path("P:/__csf/data/chat_history.db")

    def test_config_uses_default_db_path_when_env_not_set(self, monkeypatch):
        """Test Config uses default path when CHS_DB_PATH is not set.

        Given: CHS_DB_PATH environment variable is not set
        When: Config is instantiated
        Then: db_path should default to standard location
        """
        monkeypatch.delenv("CHS_DB_PATH", raising=False)
        config = Config()
        assert config.db_path == Path("P:/__csf/data/chat_history.db")

    def test_config_loads_embedding_model_from_env(self, monkeypatch):
        """Test Config loads EMBEDDING_MODEL from environment variable.

        Given: EMBEDDING_MODEL environment variable is set
        When: Config is instantiated
        Then: embedding_model attribute should match the environment value
        """
        monkeypatch.setenv("EMBEDDING_MODEL", "sentence-transformers/all-mpnet-base-v2")
        config = Config()
        assert config.embedding_model == "sentence-transformers/all-mpnet-base-v2"

    def test_config_loads_embedding_dimensions_from_env(self, monkeypatch):
        """Test Config loads EMBEDDING_DIMENSIONS from environment variable.

        Given: EMBEDDING_DIMENSIONS environment variable is set
        When: Config is instantiated
        Then: embedding_dim attribute should match the environment value
        """
        monkeypatch.setenv("EMBEDDING_DIMENSIONS", "768")
        config = Config()
        assert config.embedding_dim == 768

    def test_config_loads_jsonl_directory_from_env(self, monkeypatch, tmp_path):
        """Test Config loads CHS_JSONL_DIR from environment variable.

        Given: CHS_JSONL_DIR environment variable is set
        When: Config is instantiated
        Then: jsonl_dir attribute should match the environment value
        """
        jsonl_dir = tmp_path / "chats"
        jsonl_dir.mkdir()
        monkeypatch.setenv("CHS_JSONL_DIR", str(jsonl_dir))
        config = Config()
        assert config.jsonl_dir == jsonl_dir

    def test_config_validates_embedding_dim_is_positive_int(self, monkeypatch):
        """Test Config validates embedding_dim is a positive integer.

        Given: EMBEDDING_DIMENSIONS is set to an invalid value
        When: Config is instantiated
        Then: Should raise ValueError with appropriate message
        """
        monkeypatch.setenv("EMBEDDING_DIMENSIONS", "invalid")
        with pytest.raises(ValueError, match="EMBEDDING_DIMENSIONS must be a positive integer"):
            Config()

    def test_config_validates_jsonl_dir_exists(self, monkeypatch):
        """Test Config validates jsonl_dir exists.

        Given: CHS_JSONL_DIR is set to a non-existent directory
        When: Config is instantiated
        Then: Should raise ValueError with appropriate message
        """
        non_existent = Path("P:/does/not/exist/chats")
        monkeypatch.setenv("CHS_JSONL_DIR", str(non_existent))
        with pytest.raises(ValueError, match="CHS_JSONL_DIR must exist"):
            Config()


class TestGetConnection:
    """Tests for get_connection() function."""

    def test_get_connection_returns_sqlite_connection(self, tmp_path):
        """Test get_connection returns a valid SQLite connection.

        Given: A valid database path
        When: get_connection is called
        Then: Should return a sqlite3.Connection object
        """
        db_path = tmp_path / "test.db"
        conn = get_connection(db_path)
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_get_connection_enables_wal_mode(self, tmp_path):
        """Test get_connection enables WAL mode.

        Given: A database path
        When: get_connection is called
        Then: Connection should have WAL mode enabled
        """
        db_path = tmp_path / "test.db"
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        result = cursor.fetchone()
        assert result[0] == "wal"
        conn.close()

    def test_get_connection_sets_cache_settings(self, tmp_path):
        """Test get_connection sets appropriate cache settings.

        Given: A database path
        When: get_connection is called
        Then: Connection should have optimized cache size
        """
        db_path = tmp_path / "test.db"
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA cache_size;")
        result = cursor.fetchone()
        assert result[0] < -1000
        conn.close()

    def test_get_connection_creates_parent_directories(self, tmp_path):
        """Test get_connection creates parent directories if needed.

        Given: A database path with non-existent parent directories
        When: get_connection is called
        Then: Parent directories should be created
        """
        db_path = tmp_path / "nested" / "dirs" / "test.db"
        get_connection(db_path)
        assert db_path.parent.exists()


class TestDatabaseInitialization:
    """Tests for schema readiness detection."""

    def test_database_is_initialized_returns_false_for_empty_file(self, tmp_path):
        """An empty SQLite file should not count as an initialized CHS database."""
        db_path = tmp_path / "empty.db"
        db_path.touch()
        assert database_is_initialized(db_path) is False

    def test_database_is_initialized_returns_true_after_init(self, tmp_path):
        """A schema-initialized database should be detected as ready."""
        db_path = tmp_path / "ready.db"
        init_db(db_path)
        assert database_is_initialized(db_path) is True


class TestInitDB:
    """Tests for init_db() function."""

    def test_init_db_creates_projects_table(self, tmp_path):
        """Test init_db creates projects table.

        Given: A database path
        When: init_db is called
        Then: projects table should exist with correct schema
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects';")
        result = cursor.fetchone()
        assert result is not None
        cursor.execute("PRAGMA table_info(projects);")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {"id", "path", "label", "created_at"}
        assert expected_columns.issubset(columns)
        conn.close()

    def test_init_db_creates_sessions_table(self, tmp_path):
        """Test init_db creates sessions table.

        Given: A database path
        When: init_db is called
        Then: sessions table should exist with correct schema
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions';")
        result = cursor.fetchone()
        assert result is not None
        cursor.execute("PRAGMA table_info(sessions);")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "id",
            "session_key",
            "project_id",
            "started_at",
            "ended_at",
            "is_closed",
            "message_count",
            "summary_short",
            "summary_long",
            "embedding",
            "embedding_model",
            "embedding_dim",
            "last_turn_built_message_id",
            "last_message_timestamp",
            "created_at",
            "updated_at",
        }
        assert expected_columns.issubset(columns)
        conn.close()

    def test_init_db_creates_messages_table(self, tmp_path):
        """Test init_db creates messages table.

        Given: A database path
        When: init_db is called
        Then: messages table should exist with correct schema
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages';")
        result = cursor.fetchone()
        assert result is not None
        cursor.execute("PRAGMA table_info(messages);")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "id",
            "message_id",
            "session_id",
            "project_id",
            "timestamp",
            "role",
            "content",
            "has_code",
            "has_error",
            "raw_json",
            "created_at",
        }
        assert expected_columns.issubset(columns)
        conn.close()

    def test_init_db_creates_turns_table(self, tmp_path):
        """Test init_db creates turns table.

        Given: A database path
        When: init_db is called
        Then: turns table should exist with correct schema
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='turns';")
        result = cursor.fetchone()
        assert result is not None
        cursor.execute("PRAGMA table_info(turns);")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "id",
            "session_id",
            "project_id",
            "start_message_id",
            "end_message_id",
            "timestamp_start",
            "timestamp_end",
            "content",
            "has_code",
            "has_error",
            "length_chars",
            "embedding",
            "embedding_model",
            "embedding_dim",
            "created_at",
        }
        assert expected_columns.issubset(columns)
        conn.close()

    def test_init_db_creates_turns_fts_virtual_table(self, tmp_path):
        """Test init_db creates turns_fts FTS5 virtual table.

        Given: A database path
        When: init_db is called
        Then: turns_fts virtual table should exist for full-text search
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='turns_fts';")
        result = cursor.fetchone()
        assert result is not None
        cursor.execute("SELECT sql FROM sqlite_master WHERE name='turns_fts';")
        sql = cursor.fetchone()[0]
        assert "VIRTUAL TABLE" in sql.upper()
        assert "USING FTS5" in sql.upper()
        conn.close()

    def test_init_db_creates_messages_fts_virtual_table(self, tmp_path):
        """Test init_db creates messages_fts FTS5 virtual table.

        Given: A database path
        When: init_db is called
        Then: messages_fts virtual table should exist for full-text search
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages_fts';")
        result = cursor.fetchone()
        assert result is not None
        cursor.execute("SELECT sql FROM sqlite_master WHERE name='messages_fts';")
        sql = cursor.fetchone()[0]
        assert "VIRTUAL TABLE" in sql.upper()
        assert "USING FTS5" in sql.upper()
        conn.close()

    def test_init_db_creates_topics_table(self, tmp_path):
        """Test init_db creates topics table.

        Given: A database path
        When: init_db is called
        Then: topics table should exist for topic management
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='topics';")
        result = cursor.fetchone()
        assert result is not None
        conn.close()

    def test_init_db_creates_session_topics_table(self, tmp_path):
        """Test init_db creates session_topics table.

        Given: A database path
        When: init_db is called
        Then: session_topics table should exist for session-topic relationships
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='session_topics';"
        )
        result = cursor.fetchone()
        assert result is not None
        conn.close()

    def test_init_db_creates_indexer_checkpoints_table(self, tmp_path):
        """Test init_db creates indexer_checkpoints table.

        Given: A database path
        When: init_db is called
        Then: indexer_checkpoints table should exist for incremental indexing
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='indexer_checkpoints';"
        )
        result = cursor.fetchone()
        assert result is not None
        cursor.execute("PRAGMA table_info(indexer_checkpoints);")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {
            "id",
            "file_path",
            "file_hash",
            "last_indexed_position",
            "last_indexed_at",
        }
        assert expected_columns.issubset(columns)
        conn.close()

    def test_init_db_creates_embeddings_config_table(self, tmp_path):
        """Test init_db creates embeddings_config table.

        Given: A database path
        When: init_db is called
        Then: embeddings_config table should exist for embedding version tracking
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings_config';"
        )
        result = cursor.fetchone()
        assert result is not None
        cursor.execute("PRAGMA table_info(embeddings_config);")
        columns = {row[1] for row in cursor.fetchall()}
        expected_columns = {"id", "model_name", "embedding_dim", "created_at", "is_active"}
        assert expected_columns.issubset(columns)
        conn.close()

    def test_init_db_creates_fts_triggers(self, tmp_path):
        """Test init_db creates triggers for FTS5 synchronization.

        Given: A database path
        When: init_db is called
        Then: Triggers should exist to sync content to FTS tables
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='turns';")
        triggers = {row[0] for row in cursor.fetchall()}
        assert len(triggers) > 0, "No FTS triggers found for turns table"
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name='messages';"
        )
        triggers = {row[0] for row in cursor.fetchall()}
        assert len(triggers) > 0, "No FTS triggers found for messages table"
        conn.close()

    def test_init_db_is_idempotent(self, tmp_path):
        """Test init_db can be called multiple times without errors.

        Given: A database that has already been initialized
        When: init_db is called again
        Then: Should complete without errors and not lose data
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO projects (path, label) VALUES (?, ?)", ("/test/path", "test-project")
        )
        conn.commit()
        conn.close()
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM projects;")
        count = cursor.fetchone()[0]
        assert count == 1
        conn.close()


class TestEmbeddingsConfig:
    """Tests for embeddings configuration functions."""

    def test_load_embeddings_config_returns_current_config(self, tmp_path):
        """Test load_embeddings_config returns the active configuration.

        Given: A database with embeddings configuration
        When: load_embeddings_config is called
        Then: Should return the active configuration dict
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO embeddings_config (model_name, embedding_dim, is_active)\n               VALUES (?, ?, ?)",
            ("test-model", 768, 1),
        )
        conn.commit()
        conn.close()
        config = load_embeddings_config(db_path)
        assert config["model_name"] == "test-model"
        assert config["embedding_dim"] == 768

    def test_load_embeddings_config_returns_none_when_no_config(self, tmp_path):
        """Test load_embeddings_config returns None when no config exists.

        Given: A database with no embeddings configuration
        When: load_embeddings_config is called
        Then: Should return None
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        config = load_embeddings_config(db_path)
        assert config is None

    def test_set_embeddings_config_updates_config(self, tmp_path):
        """Test set_embeddings_config updates the active configuration.

        Given: A database
        When: set_embeddings_config is called with model and dim
        Then: Should create new config and mark previous as inactive
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        set_embeddings_config(db_path, "old-model", 768)
        set_embeddings_config(db_path, "new-model", 1536)
        config = load_embeddings_config(db_path)
        assert config["model_name"] == "new-model"
        assert config["embedding_dim"] == 1536
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM embeddings_config\n               WHERE model_name = ? AND is_active = 1",
            ("old-model",),
        )
        count = cursor.fetchone()[0]
        assert count == 0
        conn.close()

    def test_set_embeddings_config_creates_first_config(self, tmp_path):
        """Test set_embeddings_config creates first configuration.

        Given: A database with no existing configuration
        When: set_embeddings_config is called
        Then: Should create active configuration
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        set_embeddings_config(db_path, "initial-model", 768)
        config = load_embeddings_config(db_path)
        assert config["model_name"] == "initial-model"
        assert config["embedding_dim"] == 768


class TestSchemaIntegration:
    """Integration tests for complete schema initialization."""

    def test_all_tables_created_on_init(self, tmp_path):
        """Test all expected tables are created during init_db.

        Given: A new database
        When: init_db is called
        Then: All expected tables should exist
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = {row[0] for row in cursor.fetchall()}
        expected_tables = {
            "projects",
            "sessions",
            "messages",
            "turns",
            "turns_fts",
            "messages_fts",
            "topics",
            "session_topics",
            "indexer_checkpoints",
            "embeddings_config",
        }
        assert expected_tables.issubset(tables)
        conn.close()

    def test_foreign_key_constraints_enabled(self, tmp_path):
        """Test foreign key constraints are enabled.

        Given: An initialized database
        When: Foreign keys are checked
        Then: Foreign key constraints should be enabled
        """
        db_path = tmp_path / "test.db"
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        result = cursor.fetchone()
        assert result[0] == 1
        conn.close()

    def test_schema_matches_design_spec(self, tmp_path):
        """Test schema matches the design specification from plan.

        Given: An initialized database
        When: Schema is inspected
        Then: All tables from the design spec should exist
        """
        db_path = tmp_path / "test.db"
        init_db(db_path)
        conn = get_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        assert "projects" in tables
        assert "sessions" in tables
        assert "messages" in tables
        assert "turns" in tables
        assert "turns_fts" in tables
        assert "messages_fts" in tables
        assert "topics" in tables
        assert "session_topics" in tables
        assert "indexer_checkpoints" in tables
        assert "embeddings_config" in tables
        conn.close()
