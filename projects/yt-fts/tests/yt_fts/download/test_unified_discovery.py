"""
Unit tests for unified_discovery.py.

Tests cover:
- YtdlpSilentLogger - Logger suppression
- with_timeout - Timeout protection
- UnifiedChannelDiscoveryInitialization - Constructor
- Discover - Main discovery entry point
- GetFromDatabase - Database lookup
- DiscoverViaYtdlp - yt-dlp fallback
- IsValidChannel - Validation
- EnsureChannelInDb - Database persistence
- CacheManagement - Cache operations
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from yt_fts.download.unified_discovery import (
    DiscoveryResult,
    TimeoutError,
    UnifiedChannelDiscovery,
    YtdlpSilentLogger,
    with_timeout,
)


class TestYtdlpSilentLogger:
    """Tests for YtdlpSilentLogger logger suppression."""

    def test_debug_logs_in_debug_mode(self):
        """
        Test that debug messages are logged when debug mode is enabled.

        Given: Debug mode is enabled via environment variable
        When: debug() is called on YtdlpSilentLogger
        Then: debug_print is called with the prefixed message
        """
        logger = YtdlpSilentLogger()
        with patch("yt_fts.download.unified_discovery.debug_print") as mock_debug:
            logger.debug("test debug message")
            mock_debug.assert_called_once_with("YTDLP DEBUG: test debug message")

    def test_warning_suppressed(self):
        """
        Test that warning messages are suppressed.

        Given: A YtdlpSilentLogger instance
        When: warning() is called
        Then: debug_print is called with prefixed warning (suppresses spam)
        """
        logger = YtdlpSilentLogger()
        with patch("yt_fts.download.unified_discovery.debug_print") as mock_debug:
            logger.warning("test warning message")
            mock_debug.assert_called_once_with("YTDLP WARNING: test warning message")

    def test_error_suppressed(self):
        """
        Test that error messages are suppressed.

        Given: A YtdlpSilentLogger instance
        When: error() is called
        Then: debug_print is called with prefixed error (suppresses spam)
        """
        logger = YtdlpSilentLogger()
        with patch("yt_fts.download.unified_discovery.debug_print") as mock_debug:
            logger.error("test error message")
            mock_debug.assert_called_once_with("YTDLP ERROR: test error message")


class TestWithTimeout:
    """Tests for with_timeout timeout protection."""

    def test_function_completes_within_timeout(self):
        """
        Test that function completes successfully within timeout.

        Given: A function that completes quickly
        When: with_timeout is called with sufficient timeout
        Then: The function result is returned
        """
        def quick_func():
            return "success"

        result = with_timeout(quick_func, timeout_seconds=5)
        assert result == "success"

    def test_function_exceeds_timeout_raises_timeout_error(self):
        """
        Test that function exceeding timeout raises TimeoutError.

        Given: A function that never completes
        When: with_timeout is called with short timeout
        Then: TimeoutError is raised
        """
        def slow_func():
            import time
            time.sleep(10)

        with pytest.raises(TimeoutError) as exc_info:
            with_timeout(slow_func, timeout_seconds=0.1)
        assert "timed out after 0.1 seconds" in str(exc_info.value)

    def test_nested_thread_pool_executor_skips_wrapping(self):
        """
        Test that nested ThreadPoolExecutor detection skips wrapping.

        Given: Current thread is already in a ThreadPoolExecutor
        When: with_timeout is called
        Then: Function is executed directly without nested executor
        """
        with patch("threading.current_thread") as mock_thread:
            mock_thread_obj = Mock()
            mock_thread_obj.name = "ThreadPoolExecutor-0_1"
            mock_thread.return_value = mock_thread_obj

            def test_func():
                return "direct_result"

            result = with_timeout(test_func, timeout_seconds=5)
            assert result == "direct_result"

    def test_nested_thread_pool_executor_logs_debug(self):
        """
        Test that nested ThreadPoolExecutor logs debug message.

        Given: Current thread is in a ThreadPoolExecutor
        When: with_timeout is called with a logger
        Then: Debug message is logged about skipping nested timeout wrapper
        """
        mock_logger = MagicMock()

        with patch("threading.current_thread") as mock_thread:
            mock_thread_obj = Mock()
            mock_thread_obj.name = "ThreadPoolExecutor-0_1"
            mock_thread.return_value = mock_thread_obj

            def test_func():
                return "result"

            with_timeout(test_func, timeout_seconds=5, _logger=mock_logger)
            mock_logger.debug.assert_called_once_with(
                "[UNIFIED DISCOVERY] Skipping nested timeout wrapper"
            )


class TestUnifiedChannelDiscoveryInitialization:
    """Tests for UnifiedChannelDiscovery constructor."""

    def test_default_initialization(self):
        """
        Test default initialization values.

        Given: No arguments provided
        When: UnifiedChannelDiscovery is instantiated
        Then: cookies_from_browser is None and cache is empty dict
        """
        discovery = UnifiedChannelDiscovery()
        assert discovery.cookies_from_browser is None
        assert discovery._cache == {}
        assert discovery._user_agents  # USER_AGENTS list should be populated

    def test_with_cookies_from_browser(self):
        """
        Test initialization with cookies_from_browser.

        Given: cookies_from_browser is provided
        When: UnifiedChannelDiscovery is instantiated
        Then: cookies_from_browser is stored correctly
        """
        discovery = UnifiedChannelDiscovery(cookies_from_browser="chrome")
        assert discovery.cookies_from_browser == "chrome"

    def test_cache_initialized(self):
        """
        Test that cache is initialized as empty dict.

        Given: UnifiedChannelDiscovery instance
        When: Checking _cache attribute
        Then: _cache is an empty dictionary
        """
        discovery = UnifiedChannelDiscovery()
        assert isinstance(discovery._cache, dict)
        assert len(discovery._cache) == 0

    def test_user_agents_initialized(self):
        """
        Test that user_agents list is initialized from url_utils.

        Given: UnifiedChannelDiscovery instance
        When: Checking _user_agents attribute
        Then: _user_agents is a list of user agent strings
        """
        discovery = UnifiedChannelDiscovery()
        assert isinstance(discovery._user_agents, list)
        assert len(discovery._user_agents) > 0
        assert any("Mozilla" in ua for ua in discovery._user_agents)


class TestDiscover:
    """Tests for main discovery entry point."""

    def test_memory_cache_hit(self):
        """
        Test that memory cache returns cached result.

        Given: A previously cached discovery result
        When: discover is called with same input_str
        Then: Cached result is returned without database lookup
        """
        discovery = UnifiedChannelDiscovery()
        cached_result = DiscoveryResult(
            channel_id="UC123",
            channel_name="Test Channel",
            channel_url="@test",
            total_videos=100,
            with_subs=100,
            without_subs=0,
            scheduled=0,
            members_only=0,
            unavailable=0,
            source="cache",
        )
        discovery._cache["@test"] = cached_result

        with patch.object(discovery, "_get_from_database") as mock_db:
            result = discovery.discover("@test")
            mock_db.assert_not_called()
            assert result == cached_result

    def test_database_cache_hit(self):
        """
        Test that database cache returns result when memory cache misses.

        Given: Database contains channel info
        When: discover is called with matching input
        Then: Database result is returned and cached in memory
        """
        discovery = UnifiedChannelDiscovery()
        db_result = DiscoveryResult(
            channel_id="UC123",
            channel_name="Test Channel",
            channel_url="@test",
            total_videos=50,
            with_subs=50,
            without_subs=0,
            scheduled=0,
            members_only=0,
            unavailable=0,
            source="database",
        )

        with patch.object(discovery, "_get_from_database", return_value=db_result):
            result = discovery.discover("@test")
            assert result == db_result
            assert "@test" in discovery._cache
            assert discovery._cache["@test"] == db_result

    def test_force_refresh_skips_cache(self):
        """
        Test that force_refresh skips both memory and database cache.

        Given: Cached results exist
        When: discover is called with force_refresh=True
        Then: yt-dlp is called directly, caches are bypassed
        """
        discovery = UnifiedChannelDiscovery()
        cached_result = DiscoveryResult(
            channel_id="UC123",
            channel_name="Test Channel",
            channel_url="@test",
            total_videos=100,
            with_subs=100,
            without_subs=0,
            scheduled=0,
            members_only=0,
            unavailable=0,
            source="cache",
        )
        discovery._cache["@test"] = cached_result

        ytdlp_result = DiscoveryResult(
            channel_id="UC456",
            channel_name="Updated Channel",
            channel_url="@test",
            total_videos=150,
            with_subs=150,
            without_subs=0,
            scheduled=0,
            members_only=0,
            unavailable=0,
            source="ytdlp",
        )

        with patch.object(discovery, "_get_from_database", return_value=cached_result):
            with patch.object(discovery, "_discover_via_ytdlp", return_value=ytdlp_result):
                result = discovery.discover("@test", force_refresh=True)
                assert result == ytdlp_result
                assert result["channel_id"] == "UC456"

    def test_ytdlp_fallback_when_cache_miss(self):
        """
        Test that yt-dlp fallback is used when all caches miss.

        Given: No memory or database cache hit
        When: discover is called
        Then: _discover_via_ytdlp is called
        """
        discovery = UnifiedChannelDiscovery()
        ytdlp_result = DiscoveryResult(
            channel_id="UC789",
            channel_name="New Channel",
            channel_url="@newchannel",
            total_videos=10,
            with_subs=10,
            without_subs=0,
            scheduled=0,
            members_only=0,
            unavailable=0,
            source="ytdlp",
        )

        with patch.object(discovery, "_get_from_database", return_value=None):
            with patch.object(discovery, "_discover_via_ytdlp", return_value=ytdlp_result) as mock_ytdlp:
                result = discovery.discover("@newchannel")
                mock_ytdlp.assert_called_once_with("@newchannel", timeout_seconds=120)
                assert result == ytdlp_result

    def test_result_cached_in_memory_after_discovery(self):
        """
        Test that discovery result is cached in memory.

        Given: A successful yt-dlp discovery
        When: discover completes
        Then: Result is stored in _cache for future calls
        """
        discovery = UnifiedChannelDiscovery()
        ytdlp_result = DiscoveryResult(
            channel_id="UC" + "x" * 22,
            channel_name="Cached Channel",
            channel_url="@cached",
            total_videos=75,
            with_subs=75,
            without_subs=0,
            scheduled=0,
            members_only=0,
            unavailable=0,
            source="ytdlp",
        )

        def mock_discover(input_str, timeout_seconds=30):
            discovery._cache[input_str] = ytdlp_result
            return ytdlp_result

        with patch.object(discovery, "_get_from_database", return_value=None):
            with patch.object(discovery, "_discover_via_ytdlp", side_effect=mock_discover):
                discovery.discover("@cached")
                assert "@cached" in discovery._cache
                assert discovery._cache["@cached"] == ytdlp_result


class TestGetFromDatabase:
    """Tests for database lookup method."""

    def test_exact_url_match(self):
        """
        Test database lookup with exact URL match.

        Given: Database contains channel with exact URL
        When: _get_from_database is called with matching URL
        Then: DiscoveryResult is returned with database source
        """
        discovery = UnifiedChannelDiscovery()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_execute_result = MagicMock()
        mock_execute_result.fetchone.return_value = ("UC" + "x" * 22, "Test Channel")
        mock_cursor.execute.return_value = mock_execute_result

        with patch("yt_fts.download.unified_discovery.get_db_connection", return_value=mock_conn):
            with patch("yt_fts.download.unified_discovery.get_num_vids", return_value=100):
                result = discovery._get_from_database("https://youtube.com/@testchannel/videos")
                assert result is not None
                assert result["channel_id"] == "UC" + "x" * 22
                assert result["channel_name"] == "Test Channel"
                assert result["source"] == "database"
                assert result["total_videos"] == 100

    def test_url_with_videos_suffix_normalization(self):
        """
        Test URL normalization removes /videos suffix.

        Given: Input URL has /videos suffix
        When: _get_from_database is called
        Then: /videos suffix is stripped for lookup
        """
        discovery = UnifiedChannelDiscovery()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_execute_result1 = MagicMock()
        mock_execute_result1.fetchone.return_value = None
        mock_execute_result2 = MagicMock()
        mock_execute_result2.fetchone.return_value = ("UC" + "x" * 22, "Test Channel")
        mock_cursor.execute.side_effect = [mock_execute_result1, mock_execute_result2]

        with patch("yt_fts.download.unified_discovery.get_db_connection", return_value=mock_conn):
            with patch("yt_fts.download.unified_discovery.get_num_vids", return_value=50):
                result = discovery._get_from_database("https://youtube.com/@testchannel/videos")
                assert result is not None
                assert result["channel_id"] == "UC" + "x" * 22

    def test_handle_pattern_matching(self):
        """
        Test @handle pattern matching in database.

        Given: Input contains @handle
        When: _get_from_database is called
        Then: SQL LIKE pattern is used for flexible matching
        """
        discovery = UnifiedChannelDiscovery()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_execute_result = MagicMock()
        mock_execute_result.fetchone.return_value = ("UC" + "y" * 22, "Handle Channel")
        mock_cursor.execute.return_value = mock_execute_result

        with patch("yt_fts.download.unified_discovery.get_db_connection", return_value=mock_conn):
            with patch("yt_fts.download.unified_discovery.get_num_vids", return_value=25):
                result = discovery._get_from_database("@testhandle")
                assert result is not None
                assert result["channel_id"] == "UC" + "y" * 22

    def test_not_found_returns_none(self):
        """
        Test that None is returned when channel not found.

        Given: Database does not contain the channel
        When: _get_from_database is called
        Then: None is returned
        """
        discovery = UnifiedChannelDiscovery()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None

        with patch("yt_fts.download.unified_discovery.get_db_connection", return_value=mock_conn):
            result = discovery._get_from_database("@nonexistent")
            assert result is None

    def test_database_exception_returns_none(self):
        """
        Test that database exceptions are handled gracefully.

        Given: Database connection raises exception
        When: _get_from_database is called
        Then: None is returned without raising
        """
        discovery = UnifiedChannelDiscovery()

        with patch("yt_fts.download.unified_discovery.get_db_connection", side_effect=Exception("DB Error")):
            result = discovery._get_from_database("@test")
            assert result is None

    def test_returns_none_when_zero_videos(self):
        """
        Test that None is returned when channel has zero videos.

        Given: Database contains channel but get_num_vids returns 0
        When: _get_from_database is called
        Then: None is returned (channel has no content)
        """
        discovery = UnifiedChannelDiscovery()

        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = ("UC123", "Empty Channel")

        with patch("yt_fts.download.unified_discovery.get_db_connection", return_value=mock_conn):
            with patch("yt_fts.download.unified_discovery.get_num_vids", return_value=0):
                result = discovery._get_from_database("@emptychannel")
                assert result is None


class TestDiscoverViaYtdlp:
    """Tests for yt-dlp fallback discovery."""

    def test_successful_extraction(self):
        """Test successful yt-dlp extraction."""
        discovery = UnifiedChannelDiscovery()
        mock_info = {
            "channel_id": "UC1234567890",
            "channel": "Test Channel",
            "webpage_url": "https://youtube.com/@testchannel",
            "entry_count": 150,
            "channel_follower_count": 10000,
            "channel_is_verified": True,
            "description": "Test description",
            "thumbnail": "https://example.com/thumb.jpg",
        }

        with patch("yt_fts.download.unified_discovery.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
            mock_ydl_instance.extract_info.return_value = mock_info

            with patch("yt_fts.download.unified_discovery.with_timeout", side_effect=lambda f, **kw: f()):
                with patch("yt_fts.download.unified_discovery.StderrCapture"):
                    result = discovery._discover_via_ytdlp("@testchannel")
                    assert result["channel_id"] == "UC1234567890"
                    assert result["channel_name"] == "Test Channel"
                    assert result["total_videos"] == 150
                    assert result["source"] == "ytdlp"
                    assert result["subscriber_count"] == 10000
                    assert result["is_verified"] is True

    def test_timeout_handling_returns_none_source(self):
        """Test timeout handling sets source to none."""
        discovery = UnifiedChannelDiscovery()
        with patch("yt_fts.download.unified_discovery.with_timeout", side_effect=TimeoutError("Timeout")):
            result = discovery._discover_via_ytdlp("@timeoutchannel", timeout_seconds=30)
            assert result["source"] == "none"
            assert result["channel_id"] is None

    def test_generic_exception_handling(self):
        """Test generic exception handling sets source to none."""
        discovery = UnifiedChannelDiscovery()
        with patch("yt_fts.download.unified_discovery.with_timeout", side_effect=RuntimeError("Network error")):
            result = discovery._discover_via_ytdlp("@errorchannel")
            assert result["source"] == "none"
            assert result["channel_id"] is None


    def test_metadata_extraction_subscriber_count(self):
        """Test subscriber_count metadata extraction."""
        discovery = UnifiedChannelDiscovery()
        mock_info = {"channel_id": "UC123", "channel": "Test", "webpage_url": "https://youtube.com/@test", "entry_count": 50, "channel_follower_count": 5000000}

        with patch("yt_fts.download.unified_discovery.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
            mock_ydl_instance.extract_info.return_value = mock_info

            with patch("yt_fts.download.unified_discovery.with_timeout", side_effect=lambda f, **kw: f()):
                with patch("yt_fts.download.unified_discovery.StderrCapture"):
                    result = discovery._discover_via_ytdlp("@test")
                    assert result["subscriber_count"] == 5000000

    def test_metadata_extraction_is_verified(self):
        """Test is_verified metadata extraction."""
        discovery = UnifiedChannelDiscovery()
        mock_info = {"channel_id": "UC123", "channel": "Test", "webpage_url": "https://youtube.com/@test", "entry_count": 50, "channel_is_verified": False}

        with patch("yt_fts.download.unified_discovery.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
            mock_ydl_instance.extract_info.return_value = mock_info

            with patch("yt_fts.download.unified_discovery.with_timeout", side_effect=lambda f, **kw: f()):
                with patch("yt_fts.download.unified_discovery.StderrCapture"):
                    result = discovery._discover_via_ytdlp("@test")
                    assert result["is_verified"] is False

    def test_metadata_extraction_description(self):
        """Test description metadata extraction."""
        discovery = UnifiedChannelDiscovery()
        mock_info = {"channel_id": "UC123", "channel": "Test", "webpage_url": "https://youtube.com/@test", "entry_count": 50, "description": "This is a test channel description"}

        with patch("yt_fts.download.unified_discovery.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
            mock_ydl_instance.extract_info.return_value = mock_info

            with patch("yt_fts.download.unified_discovery.with_timeout", side_effect=lambda f, **kw: f()):
                with patch("yt_fts.download.unified_discovery.StderrCapture"):
                    result = discovery._discover_via_ytdlp("@test")
                    assert result["description"] == "This is a test channel description"

    def test_metadata_extraction_thumbnail(self):
        """Test thumbnail_url metadata extraction."""
        discovery = UnifiedChannelDiscovery()
        mock_info = {"channel_id": "UC123", "channel": "Test", "webpage_url": "https://youtube.com/@test", "entry_count": 50, "thumbnail": "https://i.ytimg.com/img/hqdefault.jpg"}

        with patch("yt_fts.download.unified_discovery.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
            mock_ydl_instance.extract_info.return_value = mock_info

            with patch("yt_fts.download.unified_discovery.with_timeout", side_effect=lambda f, **kw: f()):
                with patch("yt_fts.download.unified_discovery.StderrCapture"):
                    result = discovery._discover_via_ytdlp("@test")
                    assert result["thumbnail_url"] == "https://i.ytimg.com/img/hqdefault.jpg"

    def test_uploader_fallback_for_channel_name(self):
        """Test uploader field used as fallback for channel_name."""
        discovery = UnifiedChannelDiscovery()
        mock_info = {"channel_id": "UC123", "uploader": "Uploader Name", "webpage_url": "https://youtube.com/@test", "entry_count": 50}

        with patch("yt_fts.download.unified_discovery.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
            mock_ydl_instance.extract_info.return_value = mock_info

            with patch("yt_fts.download.unified_discovery.with_timeout", side_effect=lambda f, **kw: f()):
                with patch("yt_fts.download.unified_discovery.StderrCapture"):
                    result = discovery._discover_via_ytdlp("@test")
                    assert result["channel_name"] == "Uploader Name"

    def test_result_cached_after_ytdlp_discovery(self):
        """Test that result is cached in memory after yt-dlp discovery."""
        discovery = UnifiedChannelDiscovery()
        mock_info = {"channel_id": "UC123", "channel": "Test", "webpage_url": "https://youtube.com/@test", "entry_count": 50}

        with patch("yt_fts.download.unified_discovery.yt_dlp.YoutubeDL") as mock_ydl:
            mock_ydl_instance = MagicMock()
            mock_ydl.return_value.__enter__.return_value = mock_ydl_instance
            mock_ydl_instance.extract_info.return_value = mock_info

            with patch("yt_fts.download.unified_discovery.with_timeout", side_effect=lambda f, **kw: f()):
                with patch("yt_fts.download.unified_discovery.StderrCapture"):
                    result = discovery._discover_via_ytdlp("@test")
                    assert "@test" in discovery._cache
                    assert discovery._cache["@test"] == result


class TestIsValidChannel:
    """Tests for channel validation method."""

    def test_valid_channel_id(self):
        """Test validation with valid channel_id."""
        discovery = UnifiedChannelDiscovery()
        result = DiscoveryResult(channel_id="UC" + "x" * 22, channel_name="Test", channel_url="@test", total_videos=10, with_subs=10, without_subs=0, scheduled=0, members_only=0, unavailable=0, source="ytdlp")
        assert discovery._is_valid_channel(result) is True

    def test_none_channel_id_returns_false(self):
        """Test validation with None channel_id."""
        discovery = UnifiedChannelDiscovery()
        result = DiscoveryResult(channel_id=None, channel_name="Test", channel_url="@test", total_videos=0, with_subs=0, without_subs=0, scheduled=0, members_only=0, unavailable=0, source="ytdlp")
        assert discovery._is_valid_channel(result) is False

    def test_invalid_channel_id_too_short(self):
        """Test validation with channel_id shorter than 10 characters."""
        discovery = UnifiedChannelDiscovery()
        result = DiscoveryResult(channel_id="UC123", channel_name="Test", channel_url="@test", total_videos=0, with_subs=0, without_subs=0, scheduled=0, members_only=0, unavailable=0, source="ytdlp")
        assert discovery._is_valid_channel(result) is False

    def test_invalid_channel_id_too_long(self):
        """Test validation with channel_id longer than 100 characters."""
        discovery = UnifiedChannelDiscovery()
        result = DiscoveryResult(channel_id="UC" + "x" * 150, channel_name="Test", channel_url="@test", total_videos=0, with_subs=0, without_subs=0, scheduled=0, members_only=0, unavailable=0, source="ytdlp")
        assert discovery._is_valid_channel(result) is False

    def test_source_none_returns_false(self):
        """Test validation with source=none."""
        discovery = UnifiedChannelDiscovery()
        result = DiscoveryResult(channel_id="UC" + "x" * 22, channel_name="Test", channel_url="@test", total_videos=0, with_subs=0, without_subs=0, scheduled=0, members_only=0, unavailable=0, source="none")
        assert discovery._is_valid_channel(result) is False

    def test_non_string_channel_id_returns_false(self):
        """Test validation with non-string channel_id."""
        discovery = UnifiedChannelDiscovery()
        result = DiscoveryResult(channel_id=12345, channel_name="Test", channel_url="@test", total_videos=0, with_subs=0, without_subs=0, scheduled=0, members_only=0, unavailable=0, source="ytdlp")
        assert discovery._is_valid_channel(result) is False

    def test_exactly_10_characters_valid(self):
        """Test that channel_id with exactly 10 characters is valid."""
        discovery = UnifiedChannelDiscovery()
        result = DiscoveryResult(channel_id="0123456789", channel_name="Test", channel_url="@test", total_videos=10, with_subs=10, without_subs=0, scheduled=0, members_only=0, unavailable=0, source="ytdlp")
        assert discovery._is_valid_channel(result) is True

    def test_exactly_100_characters_valid(self):
        """Test that channel_id with exactly 100 characters is valid."""
        discovery = UnifiedChannelDiscovery()
        result = DiscoveryResult(channel_id="0" * 100, channel_name="Test", channel_url="@test", total_videos=10, with_subs=10, without_subs=0, scheduled=0, members_only=0, unavailable=0, source="ytdlp")
        assert discovery._is_valid_channel(result) is True


class TestEnsureChannelInDb:
    """Tests for database persistence method."""

    def test_valid_channel_gets_added_to_db(self):
        """Test that valid channel is added to database."""
        discovery = UnifiedChannelDiscovery()
        valid_channel_id = "UC" + "a" * 22
        result = DiscoveryResult(
            channel_id=valid_channel_id,
            channel_name="Test Channel",
            channel_url="https://youtube.com/@test",
            total_videos=50,
            with_subs=50,
            without_subs=0,
            scheduled=0,
            members_only=0,
            unavailable=0,
            source="ytdlp",
            subscriber_count=10000,
            is_verified=True,
            description="Test description",
            thumbnail_url="https://example.com/thumb.jpg",
            playlist_count=25,
        )

        with patch("yt_fts.download.unified_discovery.add_channel_info") as mock_add:
            discovery._ensure_channel_in_db(result, "@test")
            mock_add.assert_called_once()
            call_args = mock_add.call_args
            assert call_args[0][0] == valid_channel_id
            assert call_args[0][1] == "Test Channel"
            assert call_args[0][2] == "https://youtube.com/@test"
            assert call_args[1]["subscriber_count"] == 10000
            assert call_args[1]["is_verified"] is True
            assert call_args[1]["description"] == "Test description"
            assert call_args[1]["thumbnail_url"] == "https://example.com/thumb.jpg"
            assert call_args[1]["playlist_count"] == 25

    def test_invalid_channel_skipped(self):
        """Test that invalid channel is not added to database."""
        discovery = UnifiedChannelDiscovery()
        result = DiscoveryResult(channel_id=None, channel_name="Test", channel_url="@test", total_videos=0, with_subs=0, without_subs=0, scheduled=0, members_only=0, unavailable=0, source="none")
        with patch("yt_fts.download.unified_discovery.add_channel_info") as mock_add:
            discovery._ensure_channel_in_db(result, "@test")
            mock_add.assert_not_called()

    def test_missing_channel_name_uses_channel_id(self):
        """Test that missing channel_name uses channel_id as fallback."""
        discovery = UnifiedChannelDiscovery()
        valid_channel_id = "UC" + "b" * 22
        result = DiscoveryResult(
            channel_id=valid_channel_id,
            channel_name=None,
            channel_url="https://youtube.com/@test",
            total_videos=10,
            with_subs=10,
            without_subs=0,
            scheduled=0,
            members_only=0,
            unavailable=0,
            source="ytdlp",
        )
        with patch("yt_fts.download.unified_discovery.add_channel_info") as mock_add:
            discovery._ensure_channel_in_db(result, "@test")
            mock_add.assert_called_once()
            call_args = mock_add.call_args
            assert call_args[0][1] == valid_channel_id

    def test_missing_channel_url_uses_input_str(self):
        """Test that missing channel_url uses input_str as fallback."""
        discovery = UnifiedChannelDiscovery()
        valid_channel_id = "UC" + "c" * 22
        result = DiscoveryResult(
            channel_id=valid_channel_id,
            channel_name="Test",
            channel_url=None,
            total_videos=10,
            with_subs=10,
            without_subs=0,
            scheduled=0,
            members_only=0,
            unavailable=0,
            source="ytdlp",
        )
        with patch("yt_fts.download.unified_discovery.add_channel_info") as mock_add:
            discovery._ensure_channel_in_db(result, "@fallbackurl")
            mock_add.assert_called_once()
            call_args = mock_add.call_args
            assert call_args[0][2] == "@fallbackurl"

    def test_exception_during_add_channel_info_is_caught(self):
        """Test that exceptions during add_channel_info are caught and logged."""
        discovery = UnifiedChannelDiscovery()
        valid_channel_id = "UC" + "d" * 22
        result = DiscoveryResult(
            channel_id=valid_channel_id,
            channel_name="Test",
            channel_url="@test",
            total_videos=10,
            with_subs=10,
            without_subs=0,
            scheduled=0,
            members_only=0,
            unavailable=0,
            source="ytdlp",
        )
        with patch("yt_fts.download.unified_discovery.add_channel_info", side_effect=Exception("DB Error")):
            with patch("yt_fts.download.unified_discovery.logger.debug") as mock_debug:
                discovery._ensure_channel_in_db(result, "@test")
                mock_debug.assert_called()
                call_args = mock_debug.call_args
                assert "DB insert note" in str(call_args)


class TestCacheManagement:
    """Tests for cache management methods."""

    def test_clear_cache_empties_cache(self):
        """Test that clear_cache empties the in-memory cache."""
        discovery = UnifiedChannelDiscovery()
        discovery._cache["@test1"] = MagicMock()
        discovery._cache["@test2"] = MagicMock()
        assert len(discovery._cache) == 2
        discovery.clear_cache()
        assert len(discovery._cache) == 0

    def test_get_cache_size_returns_count(self):
        """Test that get_cache_size returns number of cached results."""
        discovery = UnifiedChannelDiscovery()
        assert discovery.get_cache_size() == 0
        discovery._cache["@test1"] = MagicMock()
        discovery._cache["@test2"] = MagicMock()
        discovery._cache["@test3"] = MagicMock()
        assert discovery.get_cache_size() == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
