"""CRITICAL integration tests for CHS v2 - Data Safety Verification.

These tests verify CRITICAL data safety behaviors for:
- Log rotation: No data loss when JSONL files are truncated/rotated
- Embedding versioning: Reject queries with mismatched embedding dimensions

These are CHARACTERIZATION tests that document REQUIRED safety behaviors.
Run with: pytest P:\\\\\\__csf/src/knowledge/systems/chs/v2/tests/test_critical.py -v
"""

import json
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from .critical import CHSIndexer, CHSMigrator, CHSSearcher, CHSValidator


class TestLogRotationDataLoss:
    """Tests for log rotation data loss prevention.

    Chat history files (JSONL) may be rotated by logging systems.
    CHS v2 MUST:
    1. Track indexed messages via content hash + offset
    2. Detect when file is truncated (rotation)
    3. Preserve already-indexed data
    4. Continue indexing from new position
    5. Use checkpoint recovery for crash safety
    """

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def jsonl_file(self, temp_dir):
        """Create test JSONL file path."""
        return temp_dir / "chat_history.jsonl"

    @pytest.fixture
    def db_path(self, temp_dir):
        """Create test database path."""
        return temp_dir / "chat_history.db"

    @pytest.fixture
    def checkpoint_path(self, temp_dir):
        """Create test checkpoint file path."""
        return temp_dir / "chs_checkpoint.json"

    @pytest.fixture
    def sample_messages(self):
        """Generate 100 sample messages for testing."""
        messages = []
        for i in range(100):
            messages.append(
                {
                    "id": f"msg_{i:04d}",
                    "timestamp": datetime.now().isoformat(),
                    "role": "user" if i % 2 == 0 else "assistant",
                    "content": f"Test message number {i} with some content for indexing",
                }
            )
        return messages

    def test_log_rotation_no_data_loss(
        self, jsonl_file, db_path, checkpoint_path, sample_messages, temp_dir
    ):
        """Test that log rotation does NOT cause data loss.

        Given: 100 messages in JSONL file
        When: File is indexed, then truncated to 50 messages (rotation)
        Then: No duplicate or lost messages after re-indexing

        Test Steps:
        1. Create JSONL with 100 messages
        2. Index all 100 messages
        3. Verify count = 100 in database
        4. Truncate JSONL to 50 messages (simulate rotation)
        5. Run indexer again
        6. Verify:
           - Database still has 100 messages (no loss)
           - No duplicate entries
           - Checkpoint recovered correctly
        """
        with open(jsonl_file, "w") as f:
            for msg in sample_messages:
                f.write(json.dumps(msg) + "\n")
        indexer = CHSIndexer(
            jsonl_path=jsonl_file, db_path=db_path, checkpoint_path=checkpoint_path
        )
        result = indexer.index()
        assert result["indexed_count"] == 100
        assert result["status"] == "success"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chat_messages")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 100, f"Expected 100 messages, got {count}"
        with open(jsonl_file, "w") as f:
            for msg in sample_messages[:50]:
                f.write(json.dumps(msg) + "\n")
        indexer2 = CHSIndexer(
            jsonl_path=jsonl_file, db_path=db_path, checkpoint_path=checkpoint_path
        )
        _ = indexer2.index()
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chat_messages")
        count_after = cursor.fetchone()[0]
        cursor.execute("\n            SELECT COUNT(DISTINCT id) FROM chat_messages\n        ")
        unique_count = cursor.fetchone()[0]
        conn.close()
        assert count_after == 100, f"Data loss! Expected 100, got {count_after}"
        assert unique_count == 100, f"Duplicates found! {count_after} total, {unique_count} unique"

    def test_checkpoint_recovery_after_crash(
        self, jsonl_file, db_path, checkpoint_path, sample_messages
    ):
        """Test that checkpoint recovery works correctly.

        Given: Indexing crashes after processing 70 messages
        When: Indexing is resumed from checkpoint
        Then: Only remaining 30 messages are processed (no duplicates)
        """
        with open(jsonl_file, "w") as f:
            for msg in sample_messages:
                f.write(json.dumps(msg) + "\n")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "\n            CREATE TABLE IF NOT EXISTS chat_messages (\n                id TEXT PRIMARY KEY,\n                content TEXT,\n                embedding BLOB,\n                embedding_dim INTEGER\n            )\n        "
        )
        for i in range(70):
            msg = sample_messages[i]
            cursor.execute(
                "INSERT INTO chat_messages (id, content) VALUES (?, ?)",
                (msg["id"], msg.get("content", "")),
            )
        conn.commit()
        conn.close()
        partial_checkpoint = {
            "last_indexed_id": "msg_0069",
            "indexed_count": 70,
            "last_offset": 0,
            "timestamp": datetime.now().isoformat(),
        }
        with open(checkpoint_path, "w") as f:
            json.dump(partial_checkpoint, f)
        indexer = CHSIndexer(
            jsonl_path=jsonl_file, db_path=db_path, checkpoint_path=checkpoint_path
        )
        result = indexer.index()
        assert (
            result["indexed_count"] == 30
        ), f"Expected 30 new messages, got {result['indexed_count']}"
        assert result["resumed_from_checkpoint"] is True
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chat_messages")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 100, f"Expected 100 total messages, got {count}"

    def test_duplicate_detection_with_content_hash(
        self, jsonl_file, db_path, checkpoint_path, sample_messages
    ):
        """Test that duplicate messages are detected via content hash.

        Given: Same message appears twice in file
        When: File is indexed
        Then: Only one entry is created (deduplication)
        """
        duplicate_messages = sample_messages[:10]
        duplicate_messages.insert(5, sample_messages[5])
        with open(jsonl_file, "w") as f:
            for msg in duplicate_messages:
                f.write(json.dumps(msg) + "\n")
        indexer = CHSIndexer(
            jsonl_path=jsonl_file, db_path=db_path, checkpoint_path=checkpoint_path
        )
        result = indexer.index()
        assert result["indexed_count"] == 10
        assert result["skipped_duplicates"] == 1
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM chat_messages")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 10, f"Expected 10 unique messages, got {count}"


class TestEmbeddingVersionMismatch:
    """Tests for embedding version mismatch detection.

    CHS v2 MUST reject queries when embedding dimensions don't match.
    This prevents silent correctness issues when models are upgraded.

    Schema:
    - chat_messages table: embedding_dim column stores model dimension
    - embedding blob: actual vector data
    - validate_embedding_blob(): checks len(blob) == embedding_dim * sizeof(float)
    """

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def db_path(self, temp_dir):
        """Create test database path."""
        return temp_dir / "chat_history.db"

    @pytest.fixture
    def sample_embedding_768(self):
        """Generate sample embedding with dim 768 (old model)."""
        import struct

        return struct.pack(f"{768}f", *[0.1] * 768)

    @pytest.fixture
    def sample_embedding_1536(self):
        """Generate sample embedding with dim 1536 (new model)."""
        import struct

        return struct.pack(f"{1536}f", *[0.1] * 1536)

    def test_validate_embedding_blob_rejects_mismatch(
        self, db_path, sample_embedding_768, sample_embedding_1536
    ):
        """Test that validate_embedding_blob() rejects dimension mismatches.

        Given: Row has embedding_dim = 768
        When: validate_embedding_blob() is called with 1536-dim blob
        Then: ValueError is raised
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "\n            CREATE TABLE chat_messages (\n                id TEXT PRIMARY KEY,\n                content TEXT,\n                embedding BLOB,\n                embedding_dim INTEGER\n            )\n        "
        )
        cursor.execute(
            "\n            INSERT INTO chat_messages (id, content, embedding, embedding_dim)\n            VALUES (?, ?, ?, ?)\n        ",
            ("msg_001", "test content", sample_embedding_768, 768),
        )
        conn.commit()
        conn.close()
        validator = CHSValidator(db_path=db_path)
        with pytest.raises(ValueError, match="embedding dimension mismatch"):
            validator.validate_embedding_blob(
                embedding_blob=sample_embedding_1536, expected_dim=768
            )

    def test_query_rejects_mismatched_embeddings(self, db_path, sample_embedding_768):
        """Test that query rejects embeddings with wrong dimension.

        Given: Database configured for dim 1536
        When: Row has embedding_dim = 768
        Then: Query skips that row (doesn't return it)
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "\n            CREATE TABLE chat_messages (\n                id TEXT PRIMARY KEY,\n                content TEXT,\n                embedding BLOB,\n                embedding_dim INTEGER\n            )\n        "
        )
        cursor.execute(
            "\n            INSERT INTO chat_messages (id, content, embedding, embedding_dim)\n            VALUES (?, ?, ?, ?)\n        ",
            ("msg_001", "old model content", sample_embedding_768, 768),
        )
        conn.commit()
        conn.close()
        searcher = CHSSearcher(db_path=db_path, model_dim=1536)
        results = searcher.search("test query", limit=10)
        assert len(results) == 0, "Query should skip rows with mismatched embedding_dim"
        assert results.get("skipped_mismatched", 0) == 1

    def test_validate_embedding_blob_accepts_match(self, db_path, sample_embedding_768):
        """Test that validate_embedding_blob() accepts correct dimensions.

        Given: Row has embedding_dim = 768
        When: validate_embedding_blob() is called with 768-dim blob
        Then: No error is raised
        """
        validator = CHSValidator(db_path=db_path)
        try:
            validator.validate_embedding_blob(embedding_blob=sample_embedding_768, expected_dim=768)
        except ValueError:
            pytest.fail("validate_embedding_blob() should accept matching dimensions")

    def test_embedding_dim_migration_required(self, db_path, sample_embedding_768):
        """Test that system detects when migration is required.

        Given: Database has rows with old embedding_dim
        When: Model is upgraded to new dimension
        Then: System signals migration required
        """
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "\n            CREATE TABLE chat_messages (\n                id TEXT PRIMARY KEY,\n                content TEXT,\n                embedding BLOB,\n                embedding_dim INTEGER\n            )\n        "
        )
        for i in range(5):
            cursor.execute(
                "\n                INSERT INTO chat_messages (id, content, embedding, embedding_dim)\n                VALUES (?, ?, ?, ?)\n            ",
                (f"msg_{i:03d}", f"content {i}", sample_embedding_768, 768),
            )
        conn.commit()
        conn.close()
        migrator = CHSMigrator(db_path=db_path)
        migration_status = migrator.check_migration_required(current_model_dim=1536)
        assert migration_status["required"] is True
        assert migration_status["old_dim"] == 768
        assert migration_status["new_dim"] == 1536
        assert migration_status["affected_rows"] == 5
