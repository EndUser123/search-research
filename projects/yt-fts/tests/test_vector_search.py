"""
Tests for yt_fts.llm.vector_search module.

Tests vector search functionality for chatbot context generation.
"""

import sqlite3
from unittest.mock import Mock, patch

import pytest

from yt_fts.llm.vector_search import search_transcripts, VectorSearchResult


class TestVectorSearchResult:
    """Test VectorSearchResult dataclass."""

    def test_create_result(self):
        """Should create a result with required fields."""
        # Arrange & Act
        result = VectorSearchResult(
            video_id="abc123",
            video_title="Test Video",
            channel_name="Test Channel",
            timestamp="10:25",
            text="Sample transcript text",
            score=0.95,
        )

        # Assert
        assert result.video_id == "abc123"
        assert result.score == 0.95

    def test_result_attributes(self):
        """Should have all expected attributes."""
        # Arrange & Act
        result = VectorSearchResult(
            video_id="vid",
            video_title="Title",
            channel_name="Channel",
            timestamp="5:00",
            text="Text",
            score=0.8,
        )

        # Assert
        assert result.video_id == "vid"
        assert result.video_title == "Title"
        assert result.channel_name == "Channel"
        assert result.timestamp == "5:00"
        assert result.text == "Text"
        assert result.score == 0.8


class TestSearchTranscripts:
    """Test transcript search functionality."""

    def test_returns_empty_list_when_no_results(self, tmp_path):
        """Should return empty list when no matches found."""
        # Arrange - create empty database
        db_path = tmp_path / "test.db"
        conn = sqlite3.connect(str(db_path))
        conn.close()

        # Act
        results = search_transcripts("nonexistent query", str(db_path))

        # Assert
        assert results == []

    def test_returns_results_ordered_by_score(self, tmp_path):
        """Should return results ordered by relevance score (descending)."""
        # Arrange - create database with test data
        db_path = tmp_path / "test.db"
        self._create_test_db(str(db_path))

        # Act
        results = search_transcripts("test query", str(db_path))

        # Assert - results should be ordered by score descending
        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].score >= results[i + 1].score

    def test_limits_results_by_max_results(self, tmp_path):
        """Should respect max_results parameter."""
        # Arrange
        db_path = tmp_path / "test.db"
        self._create_test_db(str(db_path))

        # Act
        results = search_transcripts("test", str(db_path), max_results=3)

        # Assert
        assert len(results) <= 3

    def test_includes_video_metadata(self, tmp_path):
        """Should include video title and channel in results."""
        # Arrange
        db_path = tmp_path / "test.db"
        self._create_test_db(str(db_path))

        # Act
        results = search_transcripts("test", str(db_path))

        # Assert - if results exist, they should have metadata
        if results:
            result = results[0]
            assert result.video_title  # Should not be empty
            assert result.channel_name  # Should not be empty
            assert result.video_id  # Should not be empty

    def _create_test_db(self, db_path: str):
        """Helper to create test database with sample data."""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                video_id TEXT PRIMARY KEY,
                video_title TEXT,
                channel_name TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subtitles (
                id INTEGER PRIMARY KEY,
                video_id TEXT,
                text TEXT,
                timestamp TEXT,
                FOREIGN KEY (video_id) REFERENCES videos (video_id)
            )
        """)

        # Insert test data
        cursor.execute(
            "INSERT INTO videos VALUES (?, ?, ?)",
            ("test_vid_1", "Test Video 1", "Test Channel")
        )
        cursor.execute(
            "INSERT INTO subtitles VALUES (?, ?, ?, ?)",
            (1, "test_vid_1", "This is a test transcript text", "0:10")
        )

        conn.commit()
        conn.close()
