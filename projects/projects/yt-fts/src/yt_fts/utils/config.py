import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def find_and_load_env(start_dir: Path | None = None) -> str | None:
    """Search for and load .env file from standard locations.

    Searches in priority order:
    1. Project root (start_dir)
    2. Parent directory (for monorepo setups)
    3. Grandparent directory (for P:\\.env scenario)

    Args:
        start_dir: Starting directory for search. Defaults to cwd().

    Returns:
        Path to .env file if found and loaded, None otherwise.
    """
    # Skip .env loading for help commands
    if "--help" in sys.argv or "-h" in sys.argv:
        return None
    if start_dir is None:
        start_dir = Path.cwd()
    possible_paths = [start_dir, start_dir.parent, start_dir.parent.parent]
    for location in possible_paths:
        env_path = location / ".env"
        if env_path.exists():
            try:
                from dotenv import load_dotenv

                load_dotenv(env_path)
                logger.info("Loaded .env from %s", env_path)
                return str(env_path)
            except ImportError:
                logger.warning("python-dotenv not installed, skipping .env load")
                return None
            except Exception as e:
                logger.exception("Error loading .env from %s: %s", env_path, e)
                return None
    return None


def get_config_path() -> str | None:
    """
    Get the path to the application configuration directory.

    Returns:
        Path to config directory or None if not found.
    """
    platform = sys.platform
    if platform == "win32":
        config_path = Path(os.getenv("APPDATA", "")) / "yt-fts"
        if not config_path.exists():
            return None
        return str(config_path)
    if platform in {"darwin", "linux"}:
        config_path = Path.home() / ".config" / "yt-fts"
        if not config_path.exists():
            return None
        return str(config_path)
    return None


def make_config_dir() -> str | None:
    """
    Create the configuration directory if it doesn't exist.

    Returns:
        Path to created config directory or None on failure.
    """
    platform = sys.platform
    try:
        if platform == "win32":
            config_path = Path(os.getenv("APPDATA", "")) / "yt-fts"
            if not config_path.exists():
                config_path.mkdir()
                return str(config_path)
        if platform in {"darwin", "linux"}:
            config_path = Path.home() / ".config" / "yt-fts"
            if not config_path.exists():
                config_path.mkdir()
                return str(config_path)
    except Exception as e:
        logger.exception("Error creating config directory: %s", e)
        return None


def get_db_path() -> str:
    """Get database path, with support for custom location via environment variable.

    Checks YT_FTS_DB_PATH environment variable first, then uses default locations.
    This allows users to specify a custom database location for testing or portability.
    """
    from yt_fts.db.maintenance import make_db

    custom_db_path = os.getenv("YT_FTS_DB_PATH")
    if custom_db_path:
        db_path = Path(custom_db_path)
        if db_path.parent and (not db_path.parent.exists()):
            db_path.parent.mkdir(parents=True, exist_ok=True)
        if not db_path.exists():
            logger.info("Creating database at custom path: %s", db_path)
            make_db(str(db_path))
        return str(db_path)
    config_path = get_config_path()
    if config_path is None:
        config_path = make_config_dir()
        if config_path is None:
            logger.warning("unable to make config path, using current directory")
            return "subtitles.db"
    db_path = Path(config_path) / "subtitles.db"
    if not db_path.exists():
        logger.info("db path not found at %s, making new db", db_path)
        make_db(str(db_path))
    return str(db_path)
