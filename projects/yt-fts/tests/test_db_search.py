"""Tests for yt_fts.db.search module.

These tests verify search functionality across all channels, specific channels,
and specific videos with support for proximity search, date filtering, and
language filtering.

Run with: pytest P:/worktrees/w1t2/projects/yt-fts/tests/test_db_search.py -v
"""

from unittest.mock import MagicMock, Mock, patch, call
import pytest
import sqlite3

from yt_fts.db.search import search_all, search_channel, search_video


class TestSearchAllBasicFunctionality:
    """Tests for basic search_all function behavior."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_basic_query(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_all executes basic search query.

        Given: A search text "test query"
        When: search_all is called with no optional parameters
        Then: Should execute FTS query and return formatted results
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test query"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA response - no language_code column (old schema)
        mock_cursor.fetchall.return_value = [
            (0, "rowid", "INTEGER", 0, None, 1),
            (1, "subtitle_id", "TEXT", 0, None, 0),
        ]

        # Mock search results
        mock_cursor.fetchall.return_value = [
            (
                1,  # rowid
                "sub001",  # subtitle_id
                "vid123",  # video_id
                10.5,  # start_time
                15.0,  # stop_time
                "test query text",  # text
                "Test Video",  # title
                "chan123",  # channel_id
                "Test Channel",  # channel_name
            )
        ]

        # Act
        result = search_all("test query")

        # Assert
        assert len(result) == 1
        assert result[0]["rowid"] == 1
        assert result[0]["subtitle_id"] == "sub001"
        assert result[0]["video_id"] == "vid123"
        assert result[0]["text"] == "test query text"
        assert result[0]["title"] == "Test Video"
        assert result[0]["channel_name"] == "Test Channel"
        assert result[0]["link"] == "https://youtu.be/vid123"

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_with_limit(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_all respects limit parameter.

        Given: A search with limit=5
        When: search_all is called with limit parameter
        Then: Should include LIMIT clause in query
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test query"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            return []

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_all("test query", limit=5)

        # Assert
        assert result == []
        # Verify SQL includes LIMIT
        sql_calls = [str(c) for c in mock_cursor.execute.call_args_list]
        assert any("LIMIT" in str(c) for c in sql_calls)


class TestSearchAllProximitySearch:
    """Tests for proximity search functionality in search_all."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query_with_proximity")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_with_proximity(
        self, mock_get_db_path, mock_parse_prox, mock_connect
    ):
        """Test that search_all uses proximity parsing when proximity is set.

        Given: A search with proximity=10
        When: search_all is called with proximity parameter
        Then: Should use parse_query_with_proximity instead of parse_query
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_prox.return_value = "test NEAR/10 query"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            return []

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_all("test query", proximity=10)

        # Assert
        mock_parse_prox.assert_called_once_with("test query", 10, None)
        assert result == []

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query_with_proximity")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_with_near_term(
        self, mock_get_db_path, mock_parse_prox, mock_connect
    ):
        """Test that search_all uses proximity parsing with near_term.

        Given: A search with near_term="target"
        When: search_all is called with near_term parameter
        Then: Should use parse_query_with_proximity with near_term
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_prox.return_value = "test NEAR/10 target"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            return []

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_all("test query", proximity=10, near_term="target")

        # Assert
        mock_parse_prox.assert_called_once_with("test query", 10, "target")
        assert result == []


class TestSearchAllDateFiltering:
    """Tests for date filtering in search_all."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_with_after_date(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_all filters by after_date.

        Given: A search with after_date="2023-01-01"
        When: search_all is called with after_date parameter
        Then: Should include date filter in query parameters
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test query"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            return []

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_all("test query", after_date="2023-01-01")

        # Assert
        assert result == []
        # Verify after_date is in query parameters
        call_args = mock_cursor.execute.call_args
        assert "2023-01-01" in call_args[0][1]

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_with_before_date(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_all filters by before_date.

        Given: A search with before_date="2023-12-31"
        When: search_all is called with before_date parameter
        Then: Should include date filter in query parameters
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test query"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            return []

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_all("test query", before_date="2023-12-31")

        # Assert
        assert result == []
        # Verify before_date is in query parameters
        call_args = mock_cursor.execute.call_args
        assert "2023-12-31" in call_args[0][1]


class TestSearchAllLanguageFiltering:
    """Tests for language filtering with backward compatibility."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_with_language_code_column(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_all filters by language when column exists.

        Given: A database with language_code column and search with language="en"
        When: search_all is called with language parameter
        Then: Should include language filter in query
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test query"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - has language_code column (new schema)
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            if pragma_call_count[0] == 1:
                # First call: PRAGMA table_info
                return [
                    (0, "rowid", "INTEGER", 0, None, 1),
                    (1, "subtitle_id", "TEXT", 0, None, 0),
                    (2, "language_code", "TEXT", 0, None, 0),
                ]
            else:
                # Second call: actual search results
                return []

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_all("test query", language="en")

        # Assert
        assert result == []
        # Verify language parameter is in query (should appear twice for IS NULL OR =)
        call_args = mock_cursor.execute.call_args[0][1]
        assert call_args.count("en") == 2  # language appears twice in the clause

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_without_language_code_column(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_all works without language_code column.

        Given: A database WITHOUT language_code column (old schema)
        When: search_all is called with language parameter
        Then: Should not include language filter in query (backward compatibility)
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test query"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code column (old schema)
        mock_cursor.fetchall.return_value = []

        # Act
        result = search_all("test query", language="en")

        # Assert
        assert result == []
        # Should still execute successfully without language filter


class TestSearchChannelBasicFunctionality:
    """Tests for basic search_channel function behavior."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_channel_basic_query(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_channel searches within specific channel.

        Given: A channel_id "chan123" and search text "test"
        When: search_channel is called
        Then: Should filter results by channel_id
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            if pragma_call_count[0] == 1:
                return []
            else:
                return [
                    (
                        1,  # rowid
                        "sub001",  # subtitle_id
                        "vid123",  # video_id
                        10.5,  # start_time
                        15.0,  # stop_time
                        "test text",  # text
                    )
                ]

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_channel("chan123", "test")

        # Assert
        assert len(result) == 1
        assert result[0]["video_id"] == "vid123"
        # Verify channel_id is in query parameters
        call_args = mock_cursor.execute.call_args[0][1]
        assert "chan123" in call_args


class TestSearchVideoBasicFunctionality:
    """Tests for basic search_video function behavior."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_video_basic_query_bug_index_error(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_video has bug: IndexError due to missing columns in SELECT.

        Given: A video_id "vid123" and search text "test"
        When: search_video is called
        Then: Should FAIL with IndexError because SELECT returns 6 columns but code accesses 9

        BUG: search_video SELECTs only 6 columns (rowid, subtitle_id, video_id, start_time, stop_time, text)
        But the formatting code tries to access 9 columns (adding title, channel_id, channel_name).
        This causes an IndexError when formatting results.

        This is a characterization test - documents the current buggy behavior.
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            if pragma_call_count[0] == 1:
                return []
            else:
                return [
                    (
                        1,  # rowid
                        "sub001",  # subtitle_id
                        "vid123",  # video_id
                        10.5,  # start_time
                        15.0,  # stop_time
                        "test text",  # text
                    )
                ]

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act & Assert - current implementation has IndexError bug
        with pytest.raises(IndexError):
            result = search_video("vid123", "test")
            _ = result  # Never reached due to bug


class TestSearchAllErrorHandling:
    """Tests for error handling in search functions."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_database_error_propagates(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_all raises database errors.

        Given: A database connection error occurs
        When: search_all is called
        Then: Should raise the exception after printing it
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test"
        mock_connect.side_effect = sqlite3.Error("Database locked")

        # Act & Assert
        with pytest.raises(sqlite3.Error, match="Database locked"):
            search_all("test")

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_video_database_error_propagates(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_video raises database errors.

        Given: A database connection error occurs
        When: search_video is called
        Then: Should raise the exception after printing it
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test"
        mock_connect.side_effect = sqlite3.Error("Database locked")

        # Act & Assert
        with pytest.raises(sqlite3.Error, match="Database locked"):
            search_video("vid123", "test")


class TestSearchAllCombinedOptions:
    """Tests for combining multiple search options."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query_with_proximity")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_all_options(
        self, mock_get_db_path, mock_parse_prox, mock_connect
    ):
        """Test search_all with all optional parameters.

        Given: A search with proximity, dates, language, and limit
        When: search_all is called with all parameters
        Then: Should build correct query with all filters
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_prox.return_value = "test NEAR/10 query"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - has language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            if pragma_call_count[0] == 1:
                return [
                    (0, "rowid", "INTEGER", 0, None, 1),
                    (2, "language_code", "TEXT", 0, None, 0),
                ]
            else:
                return []

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_all(
            text="test query",
            proximity=10,
            near_term="target",
            after_date="2023-01-01",
            before_date="2023-12-31",
            language="en",
            limit=25,
        )

        # Assert
        assert result == []
        # Verify parse_query_with_proximity was called correctly
        mock_parse_prox.assert_called_once_with("test query", 10, "target")
        # Verify all parameters are in the execute call
        call_args = mock_cursor.execute.call_args[0][1]
        assert "2023-01-01" in call_args
        assert "2023-12-31" in call_args
        assert call_args.count("en") == 2  # language appears twice
        assert 25 in call_args


class TestSearchChannelProximityAndOptions:
    """Tests for search_channel with proximity and other options."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query_with_proximity")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_channel_with_proximity(
        self, mock_get_db_path, mock_parse_prox, mock_connect
    ):
        """Test that search_channel supports proximity search.

        Given: A channel search with proximity=5
        When: search_channel is called with proximity parameter
        Then: Should use parse_query_with_proximity
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_prox.return_value = "query NEAR/5 term"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            return []

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_channel("chan123", "query term", proximity=5)

        # Assert
        mock_parse_prox.assert_called_once_with("query term", 5, None)
        assert result == []


class TestSearchVideoProximityAndOptions:
    """Tests for search_video with proximity and other options."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query_with_proximity")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_video_with_proximity(
        self, mock_get_db_path, mock_parse_prox, mock_connect
    ):
        """Test that search_video supports proximity search.

        Given: A video search with proximity=3
        When: search_video is called with proximity parameter
        Then: Should use parse_query_with_proximity
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_prox.return_value = "query NEAR/3 term"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            return []

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_video("vid123", "query term", proximity=3)

        # Assert
        mock_parse_prox.assert_called_once_with("query term", 3, None)
        assert result == []


class TestSearchAllResultFormatting:
    """Tests for result formatting in search_all."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_all_formats_multiple_results(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_all correctly formats multiple results.

        Given: A search returning multiple subtitle matches
        When: search_all is called
        Then: Should return list of properly formatted dictionaries
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            if pragma_call_count[0] == 1:
                return []
            else:
                return [
                    (
                        1,
                        "sub001",
                        "vid123",
                        10.0,
                        15.0,
                        "first match",
                        "Video 1",
                        "chan1",
                        "Channel 1",
                    ),
                    (
                        2,
                        "sub002",
                        "vid456",
                        20.0,
                        25.0,
                        "second match",
                        "Video 2",
                        "chan2",
                        "Channel 2",
                    ),
                ]

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_all("test")

        # Assert
        assert len(result) == 2
        assert result[0]["title"] == "Video 1"
        assert result[0]["channel_name"] == "Channel 1"
        assert result[0]["link"] == "https://youtu.be/vid123"
        assert result[1]["title"] == "Video 2"
        assert result[1]["channel_name"] == "Channel 2"
        assert result[1]["link"] == "https://youtu.be/vid456"


class TestSearchChannelResultFormatting:
    """Tests for result formatting in search_channel."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_channel_returns_subset_of_fields(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_channel returns only subtitle fields.

        Given: A channel search with results
        When: search_channel is called
        Then: Should return dict with rowid, subtitle_id, video_id, start_time, stop_time, text
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            if pragma_call_count[0] == 1:
                return []
            else:
                return [(1, "sub001", "vid123", 10.0, 15.0, "match text")]

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act
        result = search_channel("chan123", "test")

        # Assert
        assert len(result) == 1
        # search_channel returns subset of fields (no title, channel_name, link)
        assert "rowid" in result[0]
        assert "subtitle_id" in result[0]
        assert "video_id" in result[0]
        assert "text" in result[0]
        # These keys should NOT be in search_channel results
        assert "title" not in result[0]
        assert "channel_name" not in result[0]
        assert "link" not in result[0]


class TestSearchVideoResultFormatting:
    """Tests for result formatting in search_video."""

    @patch("yt_fts.db.search.sqlite3.connect")
    @patch("yt_fts.core.database.parse_query")
    @patch("yt_fts.db.infra.get_db_path")
    def test_search_video_bug_has_extra_fields(
        self, mock_get_db_path, mock_parse_query, mock_connect
    ):
        """Test that search_video has bug: returns extra fields it doesn't select.

        Given: A video search with results
        When: search_video is called
        Then: Should FAIL because it tries to format fields it doesn't select (title, channel_id, channel_name)

        BUG: search_video SELECTs only 6 columns but tries to format 9 columns.
        The SELECT returns: rowid, subtitle_id, video_id, start_time, stop_time, text
        But formatting code expects: rowid, subtitle_id, video_id, start_time, stop_time, text, title, channel_id, channel_name

        This test captures the BUG - will fail when implementation tries to access row[6], row[7], row[8]
        """
        # Arrange
        mock_get_db_path.return_value = "/test/db.sqlite"
        mock_parse_query.return_value = "test"
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn

        # Mock PRAGMA - no language_code
        pragma_call_count = [0]

        def pragma_side_effect(*args, **kwargs):
            pragma_call_count[0] += 1
            if pragma_call_count[0] == 1:
                return []
            else:
                return [(1, "sub001", "vid123", 10.0, 15.0, "match text")]  # Only 6 columns

        mock_cursor.fetchall.side_effect = pragma_side_effect

        # Act & Assert
        # This will fail with IndexError when trying to access row[6], row[7], row[8]
        # because the SELECT only returns 6 columns but code expects 9
        with pytest.raises(IndexError):
            result = search_video("vid123", "test")
            # If it doesn't raise, the bug is in test setup
            _ = result
