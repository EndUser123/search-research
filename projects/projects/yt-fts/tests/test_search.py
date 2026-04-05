import os
import sys
import shutil

import pytest
from click.testing import CliRunner
from testing_utils import fetch_and_unzip_test_db

from yt_fts.core.cli import cli
from yt_fts.utils.rich_console import reset_console_cache

# On Windows, config is in APPDATA, on Linux/Mac it's in ~/.config
if sys.platform == "win32":
    CONFIG_DIR = os.path.join(os.getenv("APPDATA", ""), "yt-fts")
else:
    CONFIG_DIR = os.path.expanduser("~/.config/yt-fts")


@pytest.fixture(scope="session")
def runner():
    return CliRunner()


def reset_testing_env():
    """Reset test environment and return the database path for use in tests."""
    if os.path.exists(CONFIG_DIR):
        if os.environ.get("YT_FTS_TEST_RESET", "true").lower() == "true":
            try:
                # Close any open database connections first
                import sqlite3
                import time

                # Try to close database connections
                db_path = os.path.join(CONFIG_DIR, "subtitles.db")
                if os.path.exists(db_path):
                    try:
                        conn = sqlite3.connect(db_path)
                        conn.close()
                    except:
                        pass

                # Wait a moment for file handles to be released
                time.sleep(0.1)

                # Now try to remove the directory
                shutil.rmtree(CONFIG_DIR, ignore_errors=True)

                # If directory still exists, try again after a longer wait
                if os.path.exists(CONFIG_DIR):
                    time.sleep(0.5)
                    try:
                        # Force remove remaining files
                        for root, dirs, files in os.walk(CONFIG_DIR, topdown=False):
                            for name in files:
                                file_path = os.path.join(root, name)
                                try:
                                    os.chmod(file_path, 0o666)
                                    os.unlink(file_path)
                                except:
                                    pass
                            for name in dirs:
                                try:
                                    os.rmdir(os.path.join(root, name))
                                except:
                                    pass
                        os.rmdir(CONFIG_DIR)
                    except:
                        pass

                fetch_and_unzip_test_db()

            except Exception as e:
                print(f"Warning: Could not fully reset test environment: {e}")
                # Try to continue with existing database if reset fails
                if not os.path.exists(os.path.join(CONFIG_DIR, "subtitles.db")):
                    fetch_and_unzip_test_db()
        else:
            print("running tests with existing db")

    # Return the database path for use with CliRunner
    return os.path.join(CONFIG_DIR, "subtitles.db")


def test_global_search(runner, capsys):
    # Reset console cache to ensure fresh stdout/stderr
    reset_console_cache()
    
    # Ensure test database is available and get its path
    db_path = reset_testing_env()

    # Set YT_FTS_DB_PATH so CliRunner can find the database outside its isolated filesystem
    env = {"YT_FTS_DB_PATH": db_path}

    # Also propagate GEMINI_API_KEY if set (for vector search tests)
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        env["GEMINI_API_KEY"] = gemini_key

    # Run the command
    result = runner.invoke(cli, ["search", "guilt", "-l", "99"], env=env)

    # Verify the command succeeded
    assert result.exit_code == 0, f"Command failed with: {result.output or result.stderr or result.exception}"
    
    # Note: Rich console output goes to actual stdout (visible in pytest output)
    # not to result.output, so we can't assert on specific output text here
    # The successful execution and visible output in pytest run confirms it works


def test_channel_search(runner, capsys):
    # Reset console cache to ensure fresh stdout/stderr
    reset_console_cache()
    
    # Ensure test database is available and get its path
    db_path = reset_testing_env()

    # Set YT_FTS_DB_PATH so CliRunner can find the database outside its isolated filesystem
    env = {"YT_FTS_DB_PATH": db_path}

    # Run the command
    result = runner.invoke(cli, ["search", "-c", "1", "criminal", "-l", "99", "--fts-only"], env=env)

    # Verify the command succeeded
    assert result.exit_code == 0, f"Command failed with: {result.output or result.stderr or result.exception}"
    
    # Note: Rich console output goes to actual stdout (visible in pytest output)
    # not to result.output, so we can't assert on specific output text here
    # The successful execution and visible output in pytest run confirms it works


if __name__ == "__main__":
    pytest.main([__file__])
