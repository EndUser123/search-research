#!/usr/bin/env python3
from __future__ import annotations

"""In-process wrapper for error_attribution_validator.

Commitment pattern: forces explicit self-check before blaming external causes.
"""

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

_hooks_dir = Path(__file__).resolve().parent.parent
_COMMITMENT_FLAG = _hooks_dir / "session_data" / "commitment_pending.json"

# Add hooks dir to path for tool_sequence_manager
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

try:
    from tool_sequence_manager import ToolSequenceManager
    _TSM_OK = True
except ImportError:
    _TSM_OK = False

_ERROR_PATTERNS = [
    (r"(?i)404\s*(not\s*found)?", "http_404"),
    (r"(?i)403\s*(forbidden)?", "http_403"),
    (r"(?i)500\s*(internal\s*server)?", "http_500"),
    (r"(?i)connection\s*(refused|reset|timeout)", "connection_error"),
    (r"(?i)no\s*such\s*file\s*or\s*directory", "file_not_found"),
    (r"(?i)permission\s*denied", "permission_error"),
    (r"(?i)traceback\s*\(most\s*recent", "python_exception"),
    (r"(?i)(type|attribute|name|key|value|syntax)error:\s*", "python_error"),
    (r"(?i)modulenotfounderror", "import_error"),
    (r"(?i)importerror", "import_error"),
    (r"(?i)fatal:\s*", "git_fatal"),
    (r"(?i)FAILED\s+[\w/]+\.py", "test_failed"),
    (r"(?i)AssertionError", "assertion_error"),
]


class ErrorAttributionHook(PostToolUseHook):
    """Inject commitment checkpoint on tool failures."""

    tool_matcher = {"Bash"}
    env_var = "ERROR_ATTRIBUTION_ENABLED"
    default_enabled = True

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any],
    ) -> dict[str, Any]:
        output = str(tool_response)
        if len(output) < 10:
            return {"passed": True}

        # Detect hard errors
        errors = [(p, t) for p, t in _ERROR_PATTERNS if re.search(p, output)]
        if not errors:
            return {"passed": True}

        # Get recent modifications
        recent_mods = self._get_recent_mods()
        error_files = self._extract_error_files(output)
        related = self._find_related(error_files, recent_mods)

        injection = self._create_injection(recent_mods, related)

        # Set commitment flag
        files = [m.get("file", "") for m in (related or recent_mods)[:3]]
        self._set_flag("related_modification" if related else "recent_modification", files)

        return {"passed": True, "injection": injection}

    def _get_recent_mods(self) -> list[dict]:
        if not _TSM_OK:
            return []
        try:
            tools = ToolSequenceManager.get_recent(count=10)
            return [
                {"tool": t.get("name"), "file": t.get("file_path", ""),
                 "timestamp": t.get("timestamp", "")}
                for t in tools
                if t.get("name") in ("Write", "Edit", "MultiEdit") and t.get("file_path")
            ]
        except Exception:
            return []

    @staticmethod
    def _extract_error_files(output: str) -> list[str]:
        files = re.findall(r'File "([^"]+)"', output)
        files += re.findall(r'([\w/.\-_]+\.py):\d+', output)
        seen: set[str] = set()
        unique: list[str] = []
        for f in files:
            key = f.replace("\\", "/").lower()
            if key not in seen:
                seen.add(key)
                unique.append(f)
        return unique

    @staticmethod
    def _find_related(error_files: list[str], mods: list[dict]) -> list[dict]:
        related = []
        for mod in mods:
            mf = mod.get("file", "").replace("\\", "/").lower()
            mb = Path(mf).name.lower()
            for ef in error_files:
                en = ef.replace("\\", "/").lower()
                if mf in en or en in mf or mb == Path(en).name.lower():
                    related.append(mod)
                    break
        return related

    def _create_injection(self, recent: list[dict], related: list[dict]) -> str:
        if related:
            names = ", ".join(Path(m["file"]).name for m in related[:3])
            return f"\u26a0\ufe0f COMMITMENT CHECK: Did YOUR change to {names} cause this error? Answer YES/NO with evidence before diagnosing."
        if recent:
            names = ", ".join(Path(m["file"]).name for m in recent[-3:])
            return f"\u26a0\ufe0f COMMITMENT CHECK: You recently modified {names}. Could YOUR changes have caused this? Answer YES/NO with evidence before diagnosing."
        return "\u26a0\ufe0f COMMITMENT CHECK: Have you verified this isn't caused by your own recent changes? Answer YES/NO with evidence."

    @staticmethod
    def _set_flag(error_type: str, files: list[str]) -> None:
        try:
            _COMMITMENT_FLAG.parent.mkdir(parents=True, exist_ok=True)
            _COMMITMENT_FLAG.write_text(json.dumps({
                "pending": True, "error_type": error_type,
                "files": files, "timestamp": datetime.now(UTC).isoformat(),
            }), encoding="utf-8")
        except OSError:
            pass
