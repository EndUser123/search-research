# __dev\iCHS\ichs\cli_config.py
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

_DEFAULT_FILENAMES = ("ichs.yml", "ichs.yaml", "ichs.json")


def _expand_path(p: Union[str, Path]) -> Path:
    if isinstance(p, Path):
        return p.expanduser().resolve()
    return Path(os.path.expandvars(p)).expanduser().resolve()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_json(text: str) -> Dict[str, Any]:
    data = json.loads(text or "{}")
    if isinstance(data, dict):
        return data
    logger.warning("Top-level JSON config is not an object; ignoring.")
    return {}


def _load_yaml(text: str) -> Dict[str, Any]:
    try:
        import yaml  # type: ignore
    except Exception:
        logger.warning("YAML support not available (PyYAML not installed). Falling back to empty config for YAML file.")
        return {}
    try:
        data = yaml.safe_load(text) or {}
        if not isinstance(data, dict):
            logger.warning("Top-level YAML config is not a mapping; ignoring.")
            return {}
        return data
    except Exception as e:
        logger.error("Failed to parse YAML config: %s", e)
        return {}


def _default_config() -> Dict[str, Any]:
    return {
        "checks": [],
        "output": {
            "report_file": None,
            "json_export": None,
        },
        "database": {
            "path": None,
        },
    }


def _normalize_check(item: Any, idx: int) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        logger.warning("Ignoring check at index %d: expected a mapping, got %r", idx, type(item).__name__)
        return None
    name = str(item.get("name") or "").strip()
    if not name:
        logger.warning("Ignoring check at index %d: missing 'name'", idx)
        return None
    enabled = item.get("enabled", True)
    try:
        enabled = bool(enabled)
    except Exception:
        enabled = True

    params = item.get("params") or {}
    if not isinstance(params, dict):
        logger.warning("Check '%s': 'params' must be a mapping; ignoring provided value.", name)
        params = {}

    command = item.get("command")
    if command is not None and not isinstance(command, str):
        logger.warning("Check '%s': 'command' must be a string; ignoring provided value.", name)
        command = None

    normalized = {
        "name": name,
        "enabled": enabled,
        "command": command,
        "params": params,
    }
    return normalized


def _normalize_config(data: Dict[str, Any]) -> Dict[str, Any]:
    norm = _default_config()

    # checks
    raw_checks = data.get("checks", [])
    checks_out: List[Dict[str, Any]] = []
    if isinstance(raw_checks, list):
        for i, item in enumerate(raw_checks):
            c = _normalize_check(item, i)
            if c:
                checks_out.append(c)
    else:
        logger.warning("'checks' should be a list; ignoring invalid value.")
    norm["checks"] = checks_out

    # output
    raw_output = data.get("output") or {}
    if not isinstance(raw_output, dict):
        raw_output = {}
    report_file = raw_output.get("report_file")
    if report_file is not None:
        try:
            report_file = str(report_file)
        except Exception:
            report_file = None
    json_export = raw_output.get("json_export")
    if json_export is not None:
        try:
            json_export = str(json_export)
        except Exception:
            json_export = None
    norm["output"] = {
        "report_file": report_file,
        "json_export": json_export,
    }

    # database
    raw_db = data.get("database") or {}
    if not isinstance(raw_db, dict):
        raw_db = {}
    db_path = raw_db.get("path")
    if db_path is not None:
        try:
            db_path = str(db_path)
        except Exception:
            db_path = None
    norm["database"] = {"path": db_path}

    return norm


def _find_default_config(start_dir: Optional[Path] = None) -> Optional[Path]:
    """
    Search for default config files in the current directory (non-recursive).
    """
    base = start_dir or Path.cwd()
    for name in _DEFAULT_FILENAMES:
        p = base / name
        if p.exists() and p.is_file():
            return p
    return None


def load_config_file(config_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
    """
    Load CLI configuration from YAML or JSON, normalize, and return a dict.

    Resolution order when config_path is not provided:
      1) Environment variable ICHS_CONFIG (if set)
      2) A default file in CWD: ichs.yml | ichs.yaml | ichs.json
      3) Fallback to default structure

    Returns a normalized dict with keys:
      - checks: List[ {name:str, enabled:bool, command:Optional[str], params:dict} ]
      - output: { report_file: Optional[str], json_export: Optional[str] }
      - database: { path: Optional[str] }
    """
    # Env override
    if not config_path:
        env_path = os.environ.get("ICHS_CONFIG")
        if env_path:
