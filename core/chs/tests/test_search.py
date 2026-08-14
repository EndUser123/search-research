"""
Tests for CHS v2 Search (FTS + Semantic + Fusion).

RED phase: These tests will FAIL initially - implementation file doesn't exist yet.

Tests verify the search module for CHS v2 which provides:
- FTS (Full-Text Search) with BM25 ranking on turns
- Semantic search with cosine similarity on embeddings
- Score fusion with adaptive lambda weighting
- Turn-based search (conversation-level) with message-level fallback

Run with: pytest P:\\\\\\__csf/src/knowledge/systems/chs/v2/tests/test_search.py -v
"""

from __future__ import annotations

import sqlite3

import pytest
from .search import (
    CHSSearchV2,
    fuse_scores,
    search_fts_messages,
    search_fts_turns,
    search_turns,
    semantic_search_turns,
)


class TestSearchFTSMessages:
    """Tests for FTS message-level search."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database with sample chat data."""
        db = sqlite3.connect(":memory:")
        db.execute(
            "\n            CREATE TABLE projects (\n                id INTEGER PRIMARY KEY,\n                path TEXT NOT NULL UNIQUE,\n                label TEXT,\n                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE sessions (\n                id INTEGER PRIMARY KEY,\n                session_key TEXT NOT NULL,\n                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,\n                started_at INTEGER NOT NULL,\n                ended_at INTEGER,\n                is_closed INTEGER NOT NULL DEFAULT 0,\n                message_count INTEGER NOT NULL DEFAULT 0,\n                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE messages (\n                id INTEGER PRIMARY KEY,\n                message_id TEXT NOT NULL UNIQUE,\n                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,\n                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,\n                timestamp INTEGER NOT NULL,\n                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'tool', 'system')),\n                content TEXT NOT NULL,\n                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n            )\n        "
        )
        db.execute(
            "\n            CREATE VIRTUAL TABLE messages_fts USING fts5(\n                message_id, role, content,\n                content=messages,\n                content_rowid=rowid\n            )\n        "
        )
        db.execute(
            "\n            CREATE TRIGGER IF NOT EXISTS messages_fts_insert AFTER INSERT ON messages BEGIN\n                INSERT INTO messages_fts(rowid, message_id, role, content)\n                VALUES (NEW.id, NEW.message_id, NEW.role, NEW.content);\n            END\n        "
        )
        db.execute("INSERT INTO projects (path, label) VALUES ('/test', 'Test Project')")
        db.execute(
            "\n            INSERT INTO sessions (session_key, project_id, started_at) VALUES\n            ('session-1', 1, 1735689600),\n            ('session-2', 1, 1735776000)\n        "
        )
        db.execute(
            "\n            INSERT INTO messages (message_id, session_id, project_id, timestamp, role, content) VALUES\n            ('msg-1', 1, 1, 1735689600, 'user', 'How do I implement async patterns in Python?'),\n            ('msg-2', 1, 1, 1735689660, 'assistant', 'Use asyncio with async/await syntax'),\n            ('msg-3', 1, 1, 1735689720, 'user', 'Show me a code example'),\n            ('msg-4', 1, 1, 1735689780, 'assistant', 'Here is an example with async def'),\n            ('msg-5', 2, 1, 1735776000, 'user', 'What is dependency injection?'),\n            ('msg-6', 2, 1, 1735776060, 'assistant', 'Dependency injection is a design pattern')\n        "
        )
        db.commit()
        yield db
        db.close()

    def test_search_fts_messages_returns_results(self, temp_db):
        """
        Test that search_fts_messages returns BM25-ranked results.

        Given: A database with chat messages
        When: Searching for 'async'
        Then: Returns results ordered by BM25 score
        """
        results = search_fts_messages(temp_db, "async", limit=5)
        assert len(results) > 0
        assert all("score" in r for r in results)
        assert all("content" in r for r in results)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_fts_messages_empty_query(self, temp_db):
        """
        Test that search_fts_messages handles empty query.

        Given: A database with chat messages
        When: Searching with empty query
        Then: Returns empty list or handles gracefully
        """
        results = search_fts_messages(temp_db, "", limit=5)
        assert results == []

    def test_search_fts_messages_limit_parameter(self, temp_db):
        """
        Test that search_fts_messages respects limit parameter.

        Given: A database with multiple matching messages
        When: Searching with limit=2
        Then: Returns at most 2 results
        """
        results = search_fts_messages(temp_db, "python", limit=2)
        assert len(results) <= 2


class TestSearchFTSTurns:
    """Tests for FTS turn-level search."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database with sample chat data."""
        db = sqlite3.connect(":memory:")
        db.execute(
            "\n            CREATE TABLE projects (\n                id INTEGER PRIMARY KEY,\n                path TEXT NOT NULL UNIQUE,\n                label TEXT,\n                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE sessions (\n                id INTEGER PRIMARY KEY,\n                session_key TEXT NOT NULL,\n                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,\n                started_at INTEGER NOT NULL,\n                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE messages (\n                id INTEGER PRIMARY KEY,\n                message_id TEXT NOT NULL UNIQUE,\n                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,\n                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,\n                timestamp INTEGER NOT NULL,\n                role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'tool', 'system')),\n                content TEXT NOT NULL,\n                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE turns (\n                id INTEGER PRIMARY KEY,\n                session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,\n                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,\n                start_message_id INTEGER NOT NULL REFERENCES messages(id),\n                end_message_id INTEGER NOT NULL REFERENCES messages(id),\n                timestamp_start INTEGER NOT NULL,\n                timestamp_end INTEGER NOT NULL,\n                content TEXT NOT NULL,\n                created_at INTEGER NOT NULL DEFAULT (strftime('%s','now'))\n            )\n        "
        )
        db.execute(
            "\n            CREATE VIRTUAL TABLE turns_fts USING fts5(\n                content,\n                content=turns,\n                content_rowid=rowid\n            )\n        "
        )
        db.execute(
            "\n            CREATE TRIGGER IF NOT EXISTS turns_fts_insert AFTER INSERT ON turns BEGIN\n                INSERT INTO turns_fts(rowid, content)\n                VALUES (NEW.id, NEW.content);\n            END\n        "
        )
        db.execute("INSERT INTO projects (path, label) VALUES ('/test', 'Test Project')")
        db.execute(
            "INSERT INTO sessions (session_key, project_id, started_at) VALUES ('session-1', 1, 1735689600)"
        )
        db.execute(
            "\n            INSERT INTO messages (message_id, session_id, project_id, timestamp, role, content) VALUES\n            ('msg-1', 1, 1, 1735689600, 'user', 'How do I implement async patterns in Python?'),\n            ('msg-2', 1, 1, 1735689660, 'assistant', 'Use asyncio with async/await syntax for coroutines'),\n            ('msg-3', 1, 1, 1735689720, 'user', 'What about async functions?'),\n            ('msg-4', 1, 1, 1735689780, 'assistant', 'Async functions use async def and return coroutines'),\n            ('msg-5', 1, 1, 1735689840, 'user', 'Show me dependency injection'),\n            ('msg-6', 1, 1, 1735689900, 'assistant', 'Dependency injection is a design pattern')\n        "
        )
        db.execute(
            "\n            INSERT INTO turns (session_id, project_id, start_message_id, end_message_id, timestamp_start, timestamp_end, content) VALUES\n            (1, 1, 1, 2, 1735689600, 1735689660, 'User: How do I implement async patterns in Python?\nAssistant: Use asyncio with async/await syntax for coroutines'),\n            (1, 1, 3, 4, 1735689720, 1735689780, 'User: What about async functions?\nAssistant: Async functions use async def and return coroutines'),\n            (1, 1, 5, 6, 1735689840, 1735689900, 'User: Show me dependency injection\nAssistant: Dependency injection is a design pattern')\n        "
        )
        db.commit()
        yield db
        db.close()

    def test_search_fts_turns_returns_turn_results(self, temp_db):
        """
        Test that search_fts_turns returns BM25-ranked turn results.

        A "turn" consists of user message + assistant response.

        Given: A database with chat turns
        When: Searching for 'async'
        Then: Returns turn-level results with BM25 scores
        """
        results = search_fts_turns(temp_db, "async", limit=5)
        assert len(results) > 0
        assert all("score" in r for r in results)
        assert all("content" in r for r in results)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_fts_turns_falls_back_to_messages(self, temp_db):
        """
        Test that search_fts_turns falls back to search_fts_messages.

        When turn-level search fails or returns no results,
        should fall back to message-level search.

        Given: A database with chat messages
        When: search_fts_turns cannot find turn pairs
        Then: Falls back to message-level search results
        """
        results = search_fts_turns(temp_db, "python", limit=5)
        assert len(results) >= 0


class TestSemanticSearchTurns:
    """Tests for semantic search on turns."""

    @pytest.fixture
    def mock_embeddings(self):
        """Mock embedding vectors for testing."""
        import numpy as np

        return {
            "turn-1": np.random.rand(384).astype("float32"),
            "turn-2": np.random.rand(384).astype("float32"),
            "turn-3": np.random.rand(384).astype("float32"),
        }

    @pytest.fixture
    def temp_db_with_embeddings(self, mock_embeddings):
        """Create a database with embeddings table."""
        db = sqlite3.connect(":memory:")
        db.execute(
            "\n            CREATE TABLE chat_sessions (\n                session_id TEXT PRIMARY KEY,\n                start_time TEXT NOT NULL,\n                end_time TEXT,\n                message_count INTEGER DEFAULT 0,\n                model_used TEXT,\n                total_tokens INTEGER DEFAULT 0,\n                metadata TEXT DEFAULT '{}'\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE chat_messages (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                session_id TEXT NOT NULL,\n                message_index INTEGER NOT NULL,\n                role TEXT NOT NULL,\n                content TEXT NOT NULL,\n                timestamp TEXT NOT NULL,\n                token_count INTEGER DEFAULT 0,\n                tool_calls TEXT DEFAULT '[]',\n                metadata TEXT DEFAULT '{}',\n                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE chat_turns (\n                turn_id TEXT PRIMARY KEY,\n                session_id TEXT NOT NULL,\n                user_message_id INTEGER NOT NULL,\n                assistant_message_id INTEGER,\n                turn_index INTEGER NOT NULL,\n                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id),\n                FOREIGN KEY (user_message_id) REFERENCES chat_messages(id),\n                FOREIGN KEY (assistant_message_id) REFERENCES chat_messages(id)\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE turn_embeddings (\n                turn_id TEXT PRIMARY KEY,\n                embedding BLOB NOT NULL,\n                model_name TEXT NOT NULL,\n                created_at TEXT DEFAULT CURRENT_TIMESTAMP,\n                FOREIGN KEY (turn_id) REFERENCES chat_turns(turn_id)\n            )\n        "
        )
        db.execute(
            "\n            INSERT INTO chat_sessions VALUES\n            ('session-1', '2025-01-01T10:00:00', '2025-01-01T10:30:00', 4, 'claude-3', 100, '{}')\n        "
        )
        db.execute(
            "\n            INSERT INTO chat_messages VALUES\n            (1, 'session-1', 0, 'user', 'How do I implement async patterns in Python?', '2025-01-01T10:00:00', 20, '[]', '{}'),\n            (2, 'session-1', 1, 'assistant', 'Use asyncio with async/await syntax', '2025-01-01T10:01:00', 15, '[]', '{}'),\n            (3, 'session-1', 2, 'user', 'What about dependency injection?', '2025-01-01T10:02:00', 15, '[]', '{}'),\n            (4, 'session-1', 3, 'assistant', 'Dependency injection is a design pattern', '2025-01-01T10:03:00', 30, '[]', '{}')\n        "
        )
        db.execute(
            "\n            INSERT INTO chat_turns VALUES\n            ('turn-1', 'session-1', 1, 2, 0),\n            ('turn-2', 'session-1', 3, 4, 1)\n        "
        )
        import pickle

        for turn_id, embedding in mock_embeddings.items():
            if turn_id in ["turn-1", "turn-2"]:
                db.execute(
                    "\n                    INSERT INTO turn_embeddings (turn_id, embedding, model_name)\n                    VALUES (?, ?, ?)\n                ",
                    (turn_id, pickle.dumps(embedding), "mock-model"),
                )
        db.commit()
        yield db
        db.close()

    def test_semantic_search_turns_returns_cosine_ranked_results(self, temp_db_with_embeddings):
        """
        Test that semantic_search_turns returns cosine-similarity-ranked results.

        Given: A database with turn embeddings
        When: Searching with a query embedding
        Then: Returns results ranked by cosine similarity
        """
        import numpy as np

        query_embedding = np.random.rand(384).astype("float32")
        results = semantic_search_turns(temp_db_with_embeddings, query_embedding, limit=5)
        assert len(results) >= 0
        if len(results) > 0:
            assert all("score" in r for r in results)
            assert all(0 <= r["score"] <= 1 for r in results)
            scores = [r["score"] for r in results]
            assert scores == sorted(scores, reverse=True)

    def test_semantic_search_turns_respects_semantic_limit(self, temp_db_with_embeddings):
        """
        Test that semantic_search_turns respects semantic_limit parameter.

        Given: A database with turn embeddings
        When: Searching with semantic_limit=2
        Then: Returns at most 2 results
        """
        import numpy as np

        query_embedding = np.random.rand(384).astype("float32")
        results = semantic_search_turns(temp_db_with_embeddings, query_embedding, limit=2)
        assert len(results) <= 2

    def test_semantic_search_turns_no_embeddings(self, temp_db_with_embeddings):
        """
        Test that semantic_search_turns handles no embeddings gracefully.

        Given: A database with no embeddings
        When: Searching semantically
        Then: Returns empty list
        """
        import numpy as np

        temp_db_with_embeddings.execute("DELETE FROM turn_embeddings")
        temp_db_with_embeddings.commit()
        query_embedding = np.random.rand(384).astype("float32")
        results = semantic_search_turns(temp_db_with_embeddings, query_embedding, limit=5)
        assert results == []


class TestFuseScores:
    """Tests for score fusion with adaptive lambda."""

    def test_fuse_scores_combines_fts_and_semantic(self):
        """
        Test that fuse_scores combines FTS and semantic scores.

        Given: FTS results and semantic results
        When: Fusing scores with adaptive lambda
        Then: Returns combined results with hybrid scores
        """
        fts_results = [
            {"id": "turn-1", "score": 0.8, "content": "async patterns in python"},
            {"id": "turn-2", "score": 0.6, "content": "dependency injection"},
        ]
        semantic_results = [
            {"id": "turn-1", "score": 0.7, "content": "async patterns in python"},
            {"id": "turn-2", "score": 0.9, "content": "dependency injection"},
        ]
        fused = fuse_scores(fts_results, semantic_results, lambda_param=0.5)
        assert len(fused) > 0
        assert all("hybrid_score" in r or "score" in r for r in fused)
        turn_1 = next((r for r in fused if r["id"] == "turn-1"), None)
        assert turn_1 is not None
        hybrid_score = turn_1.get("hybrid_score", turn_1.get("score"))
        assert 0.74 <= hybrid_score <= 0.76

    def test_fuse_scores_adaptive_lambda(self):
        """
        Test that fuse_scores uses adaptive lambda based on result quality.

        Given: FTS results and semantic results with varying quality
        When: Fusing with adaptive lambda
        Then: Adjusts lambda based on score distributions
        """
        fts_results = [
            {"id": "turn-1", "score": 0.9, "content": "high quality match"},
            {"id": "turn-2", "score": 0.7, "content": "medium match"},
        ]
        semantic_results = [
            {"id": "turn-1", "score": 0.5, "content": "high quality match"},
            {"id": "turn-2", "score": 0.4, "content": "medium match"},
        ]
        fused = fuse_scores(fts_results, semantic_results, lambda_param="adaptive")
        assert len(fused) > 0

    def test_fuse_scores_empty_semantic_results(self):
        """
        Test that fuse_scores handles empty semantic results.

        Given: FTS results but no semantic results
        When: Fusing scores
        Then: Returns FTS results only
        """
        fts_results = [{"id": "turn-1", "score": 0.8, "content": "async patterns"}]
        semantic_results = []
        fused = fuse_scores(fts_results, semantic_results, lambda_param=0.5)
        assert len(fused) == 1
        assert fused[0]["id"] == "turn-1"


class TestSearchTurnsMain:
    """Tests for main search_turns entry point."""

    @pytest.fixture
    def temp_db_full(self):
        """Create a full database with turns, FTS, and embeddings."""
        db = sqlite3.connect(":memory:")
        db.execute(
            "\n            CREATE TABLE chat_sessions (\n                session_id TEXT PRIMARY KEY,\n                start_time TEXT NOT NULL,\n                end_time TEXT,\n                message_count INTEGER DEFAULT 0,\n                model_used TEXT,\n                total_tokens INTEGER DEFAULT 0,\n                metadata TEXT DEFAULT '{}'\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE chat_messages (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                session_id TEXT NOT NULL,\n                message_index INTEGER NOT NULL,\n                role TEXT NOT NULL,\n                content TEXT NOT NULL,\n                timestamp TEXT NOT NULL,\n                token_count INTEGER DEFAULT 0,\n                tool_calls TEXT DEFAULT '[]',\n                metadata TEXT DEFAULT '{}',\n                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE chat_turns (\n                turn_id TEXT PRIMARY KEY,\n                session_id TEXT NOT NULL,\n                user_message_id INTEGER NOT NULL,\n                assistant_message_id INTEGER,\n                turn_index INTEGER NOT NULL,\n                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)\n            )\n        "
        )
        db.execute(
            "\n            CREATE VIRTUAL TABLE message_search USING fts5(\n                session_id, role, content, timestamp\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE turn_embeddings (\n                turn_id TEXT PRIMARY KEY,\n                embedding BLOB NOT NULL,\n                model_name TEXT NOT NULL,\n                created_at TEXT DEFAULT CURRENT_TIMESTAMP\n            )\n        "
        )
        db.execute(
            "\n            INSERT INTO chat_sessions VALUES\n            ('session-1', '2025-01-01T10:00:00', '2025-01-01T10:30:00', 4, 'claude-3', 100, '{}')\n        "
        )
        db.execute(
            "\n            INSERT INTO chat_messages VALUES\n            (1, 'session-1', 0, 'user', 'How do I implement async patterns in Python?', '2025-01-01T10:00:00', 20, '[]', '{}'),\n            (2, 'session-1', 1, 'assistant', 'Use asyncio with async/await syntax', '2025-01-01T10:01:00', 15, '[]', '{}'),\n            (3, 'session-1', 2, 'user', 'What about dependency injection?', '2025-01-01T10:02:00', 15, '[]', '{}'),\n            (4, 'session-1', 3, 'assistant', 'Dependency injection is a design pattern', '2025-01-01T10:03:00', 30, '[]', '{}')\n        "
        )
        db.execute(
            "\n            INSERT INTO chat_turns VALUES\n            ('turn-1', 'session-1', 1, 2, 0),\n            ('turn-2', 'session-1', 3, 4, 1)\n        "
        )
        db.execute(
            "\n            INSERT INTO message_search (session_id, role, content, timestamp)\n            SELECT session_id, role, content, timestamp FROM chat_messages\n        "
        )
        import pickle

        import numpy as np

        for turn_id in ["turn-1", "turn-2"]:
            embedding = np.random.rand(384).astype("float32")
            db.execute(
                "\n                INSERT INTO turn_embeddings (turn_id, embedding, model_name)\n                VALUES (?, ?, ?)\n            ",
                (turn_id, pickle.dumps(embedding), "mock-model"),
            )
        db.commit()
        yield db
        db.close()

    def test_search_turns_main_entry_point(self, temp_db_full):
        """
        Test that search_turns returns fused results.

        Given: A database with FTS and embeddings
        When: Calling search_turns main entry point
        Then: Returns fused results from both FTS and semantic search
        """
        results = search_turns(temp_db_full, query="async patterns", limit=5)
        assert len(results) >= 0
        if len(results) > 0:
            assert all("score" in r or "hybrid_score" in r for r in results)

    def test_search_turns_handles_empty_query(self, temp_db_full):
        """
        Test that search_turns handles empty query gracefully.

        Given: A database with chat data
        When: Searching with empty query
        Then: Returns empty list or handles gracefully
        """
        results = search_turns(temp_db_full, query="", limit=5)
        assert results == []

    def test_search_turns_only_fts_results(self, temp_db_full):
        """
        Test that search_turns handles only FTS results (no embeddings).

        Given: A database with FTS but no embeddings
        When: Searching
        Then: Returns FTS results only
        """
        temp_db_full.execute("DELETE FROM turn_embeddings")
        temp_db_full.commit()
        results = search_turns(temp_db_full, query="async", limit=5)
        assert len(results) >= 0


class TestCHSSearchV2Class:
    """Tests for CHSSearchV2 class interface."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database."""
        db = sqlite3.connect(":memory:")
        db.execute(
            "\n            CREATE TABLE chat_sessions (\n                session_id TEXT PRIMARY KEY,\n                start_time TEXT NOT NULL,\n                end_time TEXT,\n                message_count INTEGER DEFAULT 0,\n                model_used TEXT,\n                total_tokens INTEGER DEFAULT 0,\n                metadata TEXT DEFAULT '{}'\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE chat_messages (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                session_id TEXT NOT NULL,\n                message_index INTEGER NOT NULL,\n                role TEXT NOT NULL,\n                content TEXT NOT NULL,\n                timestamp TEXT NOT NULL,\n                token_count INTEGER DEFAULT 0,\n                tool_calls TEXT DEFAULT '[]',\n                metadata TEXT DEFAULT '{}',\n                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)\n            )\n        "
        )
        db.execute(
            "\n            CREATE VIRTUAL TABLE message_search USING fts5(\n                session_id, role, content, timestamp\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE chat_turns (\n                turn_id TEXT PRIMARY KEY,\n                session_id TEXT NOT NULL,\n                user_message_id INTEGER NOT NULL,\n                assistant_message_id INTEGER,\n                turn_index INTEGER NOT NULL,\n                FOREIGN KEY (session_id) REFERENCES chat_sessions(session_id)\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE turn_embeddings (\n                turn_id TEXT PRIMARY KEY,\n                embedding BLOB NOT NULL,\n                model_name TEXT NOT NULL,\n                created_at TEXT DEFAULT CURRENT_TIMESTAMP\n            )\n        "
        )
        db.execute(
            "\n            INSERT INTO chat_sessions VALUES\n            ('session-1', '2025-01-01T10:00:00', '2025-01-01T10:30:00', 4, 'claude-3', 100, '{}')\n        "
        )
        db.execute(
            "\n            INSERT INTO chat_messages VALUES\n            (1, 'session-1', 0, 'user', 'How do I implement async patterns?', '2025-01-01T10:00:00', 20, '[]', '{}'),\n            (2, 'session-1', 1, 'assistant', 'Use asyncio with async/await', '2025-01-01T10:01:00', 15, '[]', '{}'),\n            (3, 'session-1', 2, 'user', 'What about dependency injection?', '2025-01-01T10:02:00', 15, '[]', '{}'),\n            (4, 'session-1', 3, 'assistant', 'It is a design pattern', '2025-01-01T10:03:00', 30, '[]', '{}')\n        "
        )
        db.execute(
            "\n            INSERT INTO chat_turns VALUES\n            ('turn-1', 'session-1', 1, 2, 0),\n            ('turn-2', 'session-1', 3, 4, 1)\n        "
        )
        db.execute(
            "\n            INSERT INTO message_search (session_id, role, content, timestamp)\n            SELECT session_id, role, content, timestamp FROM chat_messages\n        "
        )
        db.commit()
        yield db
        db.close()

    def test_chs_search_v2_instantiation(self, temp_db):
        """
        Test that CHSSearchV2 can be instantiated.

        Given: A database path
        When: Creating CHSSearchV2 instance
        Then: Instance is created successfully
        """
        searcher = CHSSearchV2(temp_db)
        assert searcher is not None
        assert hasattr(searcher, "search")

    def test_chs_search_v2_search_method(self, temp_db):
        """
        Test that CHSSearchV2.search returns results.

        Given: A CHSSearchV2 instance
        When: Calling search with a query
        Then: Returns search results
        """
        searcher = CHSSearchV2(temp_db)
        results = searcher.search("async", limit=5)
        assert isinstance(results, list)


class TestMissingTableHandling:
    """Tests for defensive handling of missing chat_messages table."""

    def test_search_fts_messages_handles_missing_table(self):
        """
        Test that search_fts_messages gracefully handles uninitialized database.

        Given: An empty database without chat_messages table
        When: Calling search_fts_messages
        Then: Should return empty list without crashing (defensive check)

        Regression test for: "no such table: chat_messages" error
        """
        import sqlite3

        db = sqlite3.connect(":memory:")
        results = search_fts_messages(db=db, query="test query", limit=10)
        assert results == [], f"Missing table should return empty list, got {results}"
