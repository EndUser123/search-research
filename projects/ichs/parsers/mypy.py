# __dev\iCHS\ichs\parsers\mypy.py
from __future__ import annotations

import json
import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# Text output patterns:
# Examples:
#   pkg/mod.py:12:8: error: Incompatible types in assignment [assignment]
#   pkg/mod.py:12: error: Name "x" is not defined
#   pkg/mod.py:12:8: note: Revealed type is "builtins.int"
_TEXT_WITH_COL = re.compile(
    r"^(?P<file>.*?):(?P<line>\d+):(?P<col>\d+):\s*(?P<sev>error|warning|note):\s*(?P<msg>.*?)(?:\s*\[(?P<code>[-\w\.]+)\])?\s*$",
    flags=re.IGNORECASE,
)
_TEXT_NO_COL = re.compile(
    r"^(?P<file>.*?):(?P<line>\d+):\s*(?P<sev>error|warning|note):\s*(?P<msg>.*?)(?:\s*\[(?P<code>[-\w\.]+)\])?\s*$",
    flags=re.IGNORECASE,
)


def _to_int(v: Any) -> int | None:
    try:
        if v is None or v == "":
            return None
        return int(v)
    except Exception:
        return None


def _norm_severity(sev: str | None) -> str:
    s = (sev or "").lower()
    if s == "error":
        return "error"
    if s == "warning":
        return "warning"
    # mypy "note" -> informational
    return "info"


def _from_json_obj(obj: dict[str, Any]) -> dict[str, Any] | None:
    """
    Convert a mypy JSON diagnostic object to normalized issue dict.

    Typical mypy JSON object (when using --error-format=json and --show-error-codes):
    {
      "column": 8,
      "endColumn": 15,
      "endLine": 15,
      "line": 12,
      "message": "Incompatible types in assignment",
      "path": "pkg/mod.py",
      "severity": "error",
      "code": "assignment"
    }
    Some versions may use "filename" instead of "path", or "type" instead of "severity".
    """
    path = obj.get("path") or obj.get("filename") or obj.get("file") or ""
    line = _to_int(obj.get("line"))
    col = _to_int(obj.get("column"))
    msg = str(obj.get("message") or "").strip()
    code = str(obj.get("code") or "").strip()
    sev = _norm_severity(obj.get("severity") or obj.get("type"))
    if not path and not msg and not code:
        return None
    return {
        "file": str(path),
        "line": line,
        "column": col,
        "rule_code": code,
        "message": msg,
        "severity": sev,
    }


def _parse_json_array(data: Any) -> list[dict[str, Any]]:
    """
    Handle both:
      - Top-level list of error objects
      - Top-level object with 'errors': [...]
    """
    if isinstance(data, list):
        arr = data
    elif isinstance(data, dict) and isinstance(data.get("errors"), list):
        arr = data["errors"]
    else:
        return []

    out: list[dict[str, Any]] = []
    for item in arr:
        if isinstance(item, dict):
            row = _from_json_obj(item)
            if row:
                out.append(row)
    return out


def _try_parse_json(output: str) -> list[dict[str, Any]]:
    """
    Try to parse JSON (single object or array). Fallback to JSONL if needed.
    """
    try:
        parsed = json.loads(output)
        issues = _parse_json_array(parsed)
        if issues:
            return issues
    except json.JSONDecodeError:
        # Try JSONL (each line is a JSON object)
        pass
    except Exception as e:
        logger.debug("mypy JSON parse error: %s", e)

    # JSONL path
    issues: list[dict[str, Any]] = []
    lines = output.splitlines()
    any_json = False
    for line in lines:
        text = line.strip()
        if not text:
            continue
        try:
            obj = json.loads(text)
            any_json = True
            row = _from_json_obj(obj) if isinstance(obj, dict) else None
            if row:
                issues.append(row)
        except json.JSONDecodeError:
            # Not JSONL, bail to text parser
            any_json = False
            issues = []
            break
        except Exception as e:
            logger.debug("mypy JSONL parse error: %s", e)
            any_json = False
            issues = []
            break

    return issues if any_json else []


def _parse_text(output: str) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for raw in output.splitlines():
        line = raw.strip()
        if not line:
            continue
        m = _TEXT_WITH_COL.match(line) or _TEXT_NO_COL.match(line)
        if not m:
            continue
        file = m.group("file")
        ln = _to_int(m.group("line"))
        col = _to_int(m.groupdict().get("col"))
        sev = _norm_severity(m.group("sev"))
        msg = (m.group("msg") or "").strip()
        code = (m.group("code") or "").strip()
        issues.append(
            {
                "file": file,
                "line": ln,
                "column": col,
                "rule_code": code,
                "message": msg,
                "severity": sev,
            }
        )
    return issues


def parse_output(output: str) -> list[dict[str, Any]]:
    """
    Parse mypy output (JSON/JSONL/Text) into normalized issue dicts.

    Returns list of dicts with keys:
      - file: str
      - line: Optional[int]
      - column: Optional[int]
      - rule_code: str (mypy error code when --show-error-codes is enabled)
      - message: str
      - severity: 'error' | 'warning' | 'info'
    """
    if not output or not output.strip():
        return []

    # Prefer JSON formats if available.
    try:
        issues = _try_parse_json(output)
        if issues:
            return issues
    except Exception as e:
        logger.debug("mypy JSON parsing failed: %s", e)

    # Fallback to text parsing.
    try:
        return _parse_text(output)
    except Exception as e:
        logger.debug("mypy text parsing failed: %s", e)
        return []
