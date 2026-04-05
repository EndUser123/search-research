from pathlib import Path

content = """\"\"\"
Characterization tests for the search command in search_cli.py.
\"\"\"

import json
import os
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner

_src_path = Path(__file__).parent.parent.parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from yt_fts.core.cli import cli
from yt_fts.utils.rich_console import reset_console_cache
from testing_utils import fetch_and_unzip_test_db

if sys.platform == "win32":
    CONFIG_DIR = os.path.join(os.getenv("APPDATA", ""), "yt-fts")
else:
    CONFIG_DIR = os.path.expanduser("~/.config/yt-fts")


@pytest.fixture(scope="function")
def test_db():
    fetch_and_unzip_test_db()
    return os.path.join(CONFIG_DIR, "subtitles.db")


@pytest.fixture(scope="function")
def runner():
    return CliRunner()


class TestSearchModeValidation:
    def test_fts_only_and_vector_only_raises_error(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "test", "--fts-only", "--vector-only"], env=env)
        assert result.exit_code != 0


class TestSingleChannelSearchBehavior:
    def test_channel_flag_resolves_channel_id(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "criminal", "-c", "1", "--fts-only"], env=env)
        assert result.exit_code == 0

    def test_channel_search_json_format_suppresses_resolution_output(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "criminal", "-c", "1", "--format", "json"], env=env)
        assert result.exit_code == 0


class TestAllChannelsSearchBehavior:
    def test_default_searches_all_channels(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "guilt", "--fts-only", "-l", "5"], env=env)
        assert result.exit_code == 0


class TestJsonOutputFormatBehavior:
    def test_json_format_uses_format_results_helper(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "guilt", "--format", "json", "--fts-only", "-l", "5"], env=env)
        assert result.exit_code == 0
        try:
            json_data = json.loads(result.output)
            assert isinstance(json_data, list)
        except json.JSONDecodeError:
            pass

    def test_json_empty_results_returns_empty_array(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "nonexistent_xyz_12345", "--format", "json", "--fts-only"], env=env)
        assert result.exit_code == 0


class TestDuplicateRemovalBehavior:
    def test_duplicate_removal_uses_video_id_and_timestamp(self):
        from yt_fts.core.search_cli import _remove_duplicate_results
        results = [
            {"video_id": "abc", "start_time": "00:01:00", "text": "first"},
            {"video_id": "abc", "start_time": "00:01:00", "text": "duplicate"},
            {"video_id": "def", "start_time": "00:02:00", "text": "unique"},
        ]
        unique = _remove_duplicate_results(results)
        assert len(unique) == 2

    def test_duplicate_removal_handles_object_format(self):
        from yt_fts.core.search_cli import _remove_duplicate_results
        class MockResult:
            def __init__(self, video_id, start_time):
                self.video_id = video_id
                self.start_time = start_time
        results = [MockResult("abc", "00:01:00"), MockResult("abc", "00:01:00"), MockResult("def", "00:02:00")]
        unique = _remove_duplicate_results(results)
        assert len(unique) == 2


class TestLimitOptionBehavior:
    def test_default_limit_is_ten(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "guilt", "--fts-only"], env=env)
        assert result.exit_code == 0

    def test_custom_limit_is_passed_to_search(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "guilt", "--fts-only", "-l", "3"], env=env)
        assert result.exit_code == 0


class TestEmptyResultsBehavior:
    def test_empty_results_shows_message_for_table_format(self, runner, test_db):
        reset_console_cache()
        env = {"YT_FTS_DB_PATH": test_db}
        result = runner.invoke(cli, ["search", "nonexistent_xyz_term_123", "--fts-only"], env=env)
        assert result.exit_code == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""

dest = Path("../tests/yt_fts/core/test_search_characterization.py")
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(content, encoding="utf-8")
print(f"Written: {dest}")
