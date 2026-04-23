"""Tests for CHS v2 Topic Extraction.

RED phase: These tests will FAIL initially - implementation file doesn't exist yet.

Tests verify the topics module for CHS v2 which provides:
- extract_topics(): Find matches from TOPIC_PATTERNS
- TF-based weighting for topic relevance
- update_session_topics(): Insert new topics
- update_session_topics(): Update existing topic scores

Run with: pytest P:/__csf/src/knowledge/systems/chs/v2/tests/test_topics.py -v
"""

from __future__ import annotations

import sqlite3

import pytest
from .topics import TOPIC_PATTERNS, extract_topics, update_session_topics


class TestExtractTopicsPatternMatching:
    """Tests for extract_topics() pattern matching from TOPIC_PATTERNS."""

    @pytest.fixture
    def sample_text_with_python(self) -> str:
        """Return sample text containing Python-related content."""
        return "\n        We need to implement async patterns in Python using asyncio.\n        The python code should handle concurrent requests properly.\n        "

    @pytest.fixture
    def sample_text_with_multiple_topics(self) -> str:
        """Return sample text with multiple topic matches."""
        return "\n        The React frontend connects to the FastAPI backend.\n        We are using TypeScript for type safety and pytest for testing.\n        Database queries are written in raw SQL.\n        "

    def test_extract_topics_finds_python_topic(self, sample_text_with_python: str) -> None:
        """
        Test that extract_topics() finds Python-related topics.

        Given: Text containing 'python' keyword
        When: extract_topics() is called
        Then: Should return topics with 'python' or 'python-dev'
        """
        result = extract_topics(sample_text_with_python)
        assert isinstance(result, dict)
        assert len(result) > 0
        topic_names = [name.lower() for name in result.keys()]
        assert any("python" in name for name in topic_names)

    def test_extract_topics_finds_multiple_topics(
        self, sample_text_with_multiple_topics: str
    ) -> None:
        """
        Test that extract_topics() finds multiple distinct topics.

        Given: Text containing React, FastAPI, TypeScript, pytest, SQL
        When: extract_topics() is called
        Then: Should return multiple topic matches
        """
        result = extract_topics(sample_text_with_multiple_topics)
        assert isinstance(result, dict)
        assert len(result) >= 2
        topic_names_lower = [name.lower() for name in result.keys()]
        expected_hints = ["react", "fastapi", "typescript", "pytest", "sql"]
        found_any = any(hint in " ".join(topic_names_lower) for hint in expected_hints)
        assert found_any, "Should find at least one of the expected topics"

    def test_extract_topics_returns_empty_dict_for_no_match(self) -> None:
        """
        Test that extract_topics() returns empty dict when no topics match.

        Given: Text with no recognizable topic keywords
        When: extract_topics() is called
        Then: Should return empty dictionary
        """
        text = "This is some random text without technical topics."
        result = extract_topics(text)
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_extract_topics_case_insensitive(self) -> None:
        """
        Test that extract_topics() matches topics case-insensitively.

        Given: Text with 'PYTHON' in uppercase
        When: extract_topics() is called
        Then: Should still find Python topic
        """
        text = "We are writing PYTHON code for the backend."
        result = extract_topics(text)
        assert len(result) > 0
        topic_names = [name.lower() for name in result.keys()]
        assert any("python" in name for name in topic_names)


class TestExtractTopicsTFWeighting:
    """Tests for extract_topics() term frequency weighting."""

    def test_extract_topics_uses_tf_weighting(self) -> None:
        """
        Test that extract_topics() uses TF-based weighting.

        Given: Text with 'python' appearing 3 times and 'django' once
        When: extract_topics() is called
        Then: Python should have higher weight than django
        """
        text = "\n        Python is great. Python has async support. Python is used everywhere.\n        We also use Django for web framework.\n        "
        result = extract_topics(text)
        python_weight = None
        django_weight = None
        for topic_name, weight in result.items():
            if "python" in topic_name.lower():
                python_weight = weight
            elif "django" in topic_name.lower():
                django_weight = weight
        assert python_weight is not None, "Should find python topic"
        if django_weight is not None:
            assert python_weight > django_weight

    def test_extract_topics_normalizes_weights(self) -> None:
        """
        Test that extract_topics() normalizes weights.

        Given: Text with multiple topic mentions
        When: extract_topics() is called
        Then: Weights should be reasonable floats
        """
        text = "python python django fastapi"
        result = extract_topics(text)
        for weight in result.values():
            assert isinstance(weight, (int, float))
            assert weight >= 0


class TestExtractTopicsMaxLimit:
    """Tests for extract_topics() max_topics limiting."""

    def test_extract_topics_limits_to_max_topics(self) -> None:
        """
        Test that extract_topics() limits results to max_topics.

        Given: Text with many potential topic matches
        When: extract_topics() is called with max_topics=3
        Then: Should return at most 3 topics
        """
        text = "\n        python javascript java golang rust csharp ruby php swift kotlin typescript\n        All these programming languages are mentioned.\n        "
        result = extract_topics(text, max_topics=3)
        assert len(result) <= 3, f"Should limit to max_topics=3, got {len(result)}"

    def test_extract_topics_default_max_topics(self) -> None:
        """
        Test that extract_topics() has a reasonable default max_topics.

        Given: Text with many potential topic matches
        When: extract_topics() is called without max_topics
        Then: Should return reasonable number of topics
        """
        text = "python javascript java golang rust"
        result = extract_topics(text)
        assert len(result) <= 10, "Default max_topics should be reasonable"


class TestUpdateSessionTopicsInsertNew:
    """Tests for update_session_topics() inserting new topics."""

    @pytest.fixture
    def temp_db_with_schema(self) -> sqlite3.Connection:
        """Create temporary database with CHS v2 schema."""
        db = sqlite3.connect(":memory:")
        db.execute(
            "\n            CREATE TABLE projects (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                path TEXT NOT NULL UNIQUE,\n                created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE sessions (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                project_id INTEGER NOT NULL REFERENCES projects(id),\n                started_at INTEGER NOT NULL,\n                message_count INTEGER NOT NULL DEFAULT 0,\n                is_closed INTEGER NOT NULL DEFAULT 0,\n                last_indexed_at INTEGER,\n                UNIQUE(project_id, started_at)\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE topics (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                name TEXT NOT NULL UNIQUE,\n                pattern TEXT,\n                description TEXT\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE session_topics (\n                session_id INTEGER NOT NULL REFERENCES sessions(id),\n                topic_id INTEGER NOT NULL REFERENCES topics(id),\n                weight REAL NOT NULL,\n                PRIMARY KEY (session_id, topic_id)\n            )\n        "
        )
        db.execute("INSERT INTO projects (path) VALUES ('/test/project')")
        db.execute("INSERT INTO sessions (project_id, started_at) VALUES (1, 1704067200)")
        db.commit()
        return db

    def test_update_session_topics_inserts_new_topic(
        self, temp_db_with_schema: sqlite3.Connection
    ) -> None:
        """
        Test that update_session_topics() inserts new topics.

        Given: Database with a session
        When: update_session_topics() is called with new topic
        Then: Topic should be inserted into topics table
        """
        topics = {"python": 0.8, "async": 0.5}
        update_session_topics(temp_db_with_schema, session_id=1, topics=topics)
        cursor = temp_db_with_schema.execute("SELECT name FROM topics")
        topic_names = [row[0] for row in cursor.fetchall()]
        assert "python" in topic_names
        assert "async" in topic_names

    def test_update_session_topics_creates_session_topic_mapping(
        self, temp_db_with_schema: sqlite3.Connection
    ) -> None:
        """
        Test that update_session_topics() creates session_topics entries.

        Given: Database with a session
        When: update_session_topics() is called
        Then: session_topics should have mappings with weights
        """
        topics = {"python": 0.8}
        update_session_topics(temp_db_with_schema, session_id=1, topics=topics)
        cursor = temp_db_with_schema.execute(
            "\n            SELECT st.weight, t.name\n            FROM session_topics st\n            JOIN topics t ON st.topic_id = t.id\n            WHERE st.session_id = 1\n        "
        )
        results = cursor.fetchall()
        assert len(results) == 1
        weight, name = results[0]
        assert name == "python"
        assert weight == 0.8


class TestUpdateSessionTopicsUpdateExisting:
    """Tests for update_session_topics() updating existing topic scores."""

    @pytest.fixture
    def temp_db_with_existing_topics(self) -> sqlite3.Connection:
        """Create database with existing topics and session_topics."""
        db = sqlite3.connect(":memory:")
        db.execute(
            "\n            CREATE TABLE projects (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                path TEXT NOT NULL UNIQUE,\n                created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE sessions (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                project_id INTEGER NOT NULL REFERENCES projects(id),\n                started_at INTEGER NOT NULL,\n                message_count INTEGER NOT NULL DEFAULT 0,\n                is_closed INTEGER NOT NULL DEFAULT 0,\n                last_indexed_at INTEGER,\n                UNIQUE(project_id, started_at)\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE topics (\n                id INTEGER PRIMARY KEY AUTOINCREMENT,\n                name TEXT NOT NULL UNIQUE,\n                pattern TEXT,\n                description TEXT\n            )\n        "
        )
        db.execute(
            "\n            CREATE TABLE session_topics (\n                session_id INTEGER NOT NULL REFERENCES sessions(id),\n                topic_id INTEGER NOT NULL REFERENCES topics(id),\n                weight REAL NOT NULL,\n                PRIMARY KEY (session_id, topic_id)\n            )\n        "
        )
        db.execute("INSERT INTO projects (path) VALUES ('/test/project')")
        db.execute("INSERT INTO sessions (project_id, started_at) VALUES (1, 1704067200)")
        db.execute("INSERT INTO topics (name) VALUES ('python')")
        db.execute("INSERT INTO session_topics (session_id, topic_id, weight) VALUES (1, 1, 0.5)")
        db.commit()
        return db

    def test_update_session_topics_updates_existing_weight(
        self, temp_db_with_existing_topics: sqlite3.Connection
    ) -> None:
        """
        Test that update_session_topics() updates existing topic scores.

        Given: Database with python topic at weight 0.5
        When: update_session_topics() is called with python at 0.9
        Then: Weight should be updated to 0.9
        """
        topics = {"python": 0.9}
        update_session_topics(temp_db_with_existing_topics, session_id=1, topics=topics)
        cursor = temp_db_with_existing_topics.execute(
            "\n            SELECT st.weight\n            FROM session_topics st\n            JOIN topics t ON st.topic_id = t.id\n            WHERE st.session_id = 1 AND t.name = 'python'\n        "
        )
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == 0.9

    def test_update_session_topics_merges_new_and_existing(
        self, temp_db_with_existing_topics: sqlite3.Connection
    ) -> None:
        """
        Test that update_session_topics() handles both new and existing topics.

        Given: Database with existing 'python' topic
        When: update_session_topics() is called with python and new 'django'
        Then: Both should exist with correct weights
        """
        topics = {"python": 0.7, "django": 0.6}
        update_session_topics(temp_db_with_existing_topics, session_id=1, topics=topics)
        cursor = temp_db_with_existing_topics.execute(
            "\n            SELECT t.name, st.weight\n            FROM session_topics st\n            JOIN topics t ON st.topic_id = t.id\n            WHERE st.session_id = 1\n            ORDER BY t.name\n        "
        )
        results = cursor.fetchall()
        assert len(results) == 2
        topic_dict = dict(results)
        assert topic_dict.get("django") == 0.6
        assert topic_dict.get("python") == 0.7


class TestTopicPatternsConstant:
    """Tests for TOPIC_PATTERNS constant."""

    def test_topic_patterns_is_defined(self) -> None:
        """
        Test that TOPIC_PATTERNS is defined.

        Given: topics module is imported
        When: TOPIC_PATTERNS is accessed
        Then: Should return a dictionary
        """
        assert isinstance(TOPIC_PATTERNS, dict)
        assert len(TOPIC_PATTERNS) > 0

    def test_topic_patterns_has_valid_structure(self) -> None:
        """
        Test that TOPIC_PATTERNS has valid structure.

        Given: TOPIC_PATTERNS dictionary
        When: Examining entries
        Then: Each should have name, pattern, and description
        """
        for _topic_name, topic_info in TOPIC_PATTERNS.items():
            assert isinstance(topic_info, dict)
            assert "pattern" in topic_info
            assert "description" in topic_info
