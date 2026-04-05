# __dev\iCHS\ichs\config.py
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Python 3.11+ has tomllib in stdlib; otherwise fall back to 'toml' if present.
try:  # pragma: no cover
    import tomllib as _toml  # type: ignore[attr-defined]

    def _loads_toml(b: bytes) -> dict[str, Any]:
        return _toml.loads(b.decode("utf-8"))
except Exception:  # pragma: no cover
    try:
        import toml as _toml  # type: ignore

        def _loads_toml(b: bytes) -> dict[str, Any]:
            return _toml.loads(b.decode("utf-8"))
    except Exception:
        _toml = None  # type: ignore

        def _loads_toml(b: bytes) -> dict[str, Any]:
            raise RuntimeError(
                "No TOML parser available (requires Python 3.11+ or 'toml' package)."
            )


def _expand_path_str(p: str | None) -> str | None:
    if not p:
        return p
    return str(Path(os.path.expandvars(p)).expanduser().resolve())


@dataclass
class _Overrides:
    # Ad-hoc attribute override used by some consumers (e.g., Database)
    database_path: str | None = None


class EnhancedConfig:
    """
    Lightweight TOML-backed configuration with:
      - get(section, key, default) access pattern
      - environment overrides for a few common keys
      - ad-hoc attribute override support (e.g., .database_path)

    Example ichs.toml:
        [database]
        path = ".ichs/ichs.sqlite3"

        [logging]
        level = "INFO"
        format = "%(levelname)s: %(message)s"
        file = ".ichs/ichs.log"

        [parallel]
        max_workers = 4
    """

    def __init__(self, toml_path: str | None = "ichs.toml") -> None:
        self._overrides = _Overrides()
        self._path = Path(toml_path) if toml_path else None
        self._cfg: dict[str, Any] = {}
        if self._path:
            try:
                self._load()
            except FileNotFoundError:
                # It's acceptable if no system config exists; operate with defaults
                logger.debug(
                    "System config not found at %s; using defaults", self._path
                )
            except Exception as e:
                logger.warning("Failed to load system config %s: %s", self._path, e)

        # Apply environment overrides
        self._apply_env()

    # ---------------- Public API ----------------

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Retrieve a value from the loaded TOML by section/key with default.

        Example:
            cfg.get("database", "path", None)
        """
        try:
            value = self._cfg.get(section, {}).get(key, default)
        except Exception:
            value = default
        return value

    def get_section(self, section: str) -> dict[str, Any]:
        """
        Return a copy of the entire section mapping (or empty if not present).
        """
        try:
            s = self._cfg.get(section, {})
            return dict(s) if isinstance(s, dict) else {}
        except Exception:
            return {}

    def reload(self) -> None:
        """
        Reload the TOML from disk and re-apply env overrides.
        """
        if self._path:
            self._load()
            self._apply_env()

    # Explicit attribute used by Database._resolve_db_path (may be set by CLI)
    @property
    def database_path(self) -> str | None:
        return self._overrides.database_path

    @database_path.setter
    def database_path(self, value: str | None) -> None:
        self._overrides.database_path = _expand_path_str(value)

    # ---------------- Internals ----------------

    def _load(self) -> None:
        assert self._path is not None
        raw = self._path.read_bytes()
        parsed = _loads_toml(raw)
        if not isinstance(parsed, dict):
            raise ValueError("Top-level TOML config must be a table/object")
        self._cfg = parsed

        # Normalize a couple of path-like settings
        db_path = self._cfg.get("database", {}).get("path")
        if isinstance(db_path, str):
            self._cfg.setdefault("database", {})["path"] = _expand_path_str(db_path)

        log_file = self._cfg.get("logging", {}).get("file")
        if isinstance(log_file, str):
            self._cfg.setdefault("logging", {})["file"] = _expand_path_str(log_file)

    def _apply_env(self) -> None:
        """
        Apply environment overrides for common keys.
        """
        # Database path override
        env_db = os.environ.get("ICHS_DB_PATH") or os.environ.get("ICHS_DATABASE_PATH")
        if env_db:
            self._cfg.setdefault("database", {})["path"] = _expand_path_str(env_db)

        # Logging overrides
        env_level = os.environ.get("ICHS_LOG_LEVEL")
        if env_level:
            self._cfg.setdefault("logging", {})["level"] = str(env_level)

        env_logfile = os.environ.get("ICHS_LOG_FILE")
        if env_logfile:
            self._cfg.setdefault("logging", {})["file"] = _expand_path_str(env_logfile)

        env_fmt = os.environ.get("ICHS_LOG_FMT") or os.environ.get("ICHS_LOG_FORMAT")
        if env_fmt:
            self._cfg.setdefault("logging", {})["format"] = str(env_fmt)

        # Parallelism override
        env_workers = os.environ.get("ICHS_MAX_WORKERS")
        if env_workers:
            try:
                self._cfg.setdefault("parallel", {})["max_workers"] = int(env_workers)
            except ValueError:
                logger.warning("Invalid ICHS_MAX_WORKERS value: %r", env_workers)


__all__ = ["EnhancedConfig"]
