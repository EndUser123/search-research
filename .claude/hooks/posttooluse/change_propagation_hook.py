#!/usr/bin/env python3
from __future__ import annotations

"""In-process wrapper for post_tool_use_change_propagation.

Absorbs the standalone subprocess into the PostToolUse router.
Detects structural file changes and tracks verification requirements.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

# Tools that modify files
_MODIFY_TOOLS = {"write_file", "str_replace_editor", "edit_file", "Write", "patch"}

_STRUCTURAL_PATTERNS = [
    (r"(?s)^-\s*(def|class|async def)\s+(\w+)", "function_removal"),
    (r"(?s)removed?\s+(function|class|method)\s+['\"]?(\w+)", "function_removal"),
    (r"^-\s*(from|import)\s+", "import_removal"),
    (r"removed?\s+import", "import_removal"),
    (r"\brm\s+(-rf?\s+)?['\"]?([^\s'\"]+\.py)", "file_deletion"),
    (r"\bmv\s+['\"]?([^\s'\"]+\.py)", "file_rename"),
    (r"git\s+rm", "file_deletion"),
    (r"deleted?\s+\d+\s+lines?", "large_deletion"),
    (r"removed?\s+\d+\s+lines?", "large_deletion"),
]

_VERIFICATION_REQUIREMENTS = {
    "function_removal": ["execution_test"],
    "import_removal": [],
    "file_deletion": ["grep_references"],
    "file_rename": ["import_update"],
    "large_deletion": ["execution_test"],
}

_STATE_FILE = (
    Path(os.environ.get("CSF_STATE_DIR", "P:/.claude/state"))
    / "propagation_state.json"
)


def _load_state() -> dict:
    if _STATE_FILE.exists():
        try:
            with open(_STATE_FILE) as f:
                state = json.load(f)
            if state.get("pending_verifications"):
                cutoff = datetime.now().timestamp() - 3600
                state["pending_verifications"] = [
                    p for p in state["pending_verifications"]
                    if p.get("timestamp", 0) > cutoff
                ]
            return state
        except (json.JSONDecodeError, KeyError, OSError, PermissionError):
            pass
    return {
        "pending_verifications": [],
        "completed_verifications": [],
        "structural_changes": [],
        "session_start": datetime.now().timestamp(),
    }


def _save_state(state: dict) -> None:
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except (OSError, PermissionError):
        # Fail open: state persistence issues should not surface as hook errors.
        return


class ChangePropagationHook(PostToolUseHook):
    """Track structural file changes and required verifications."""

    tool_matcher = {"Write", "Edit", "MultiEdit", "Bash"}
    env_var = "CSF_CHANGE_PROPAGATION"
    default_enabled = True

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any],
    ) -> dict[str, Any]:
        try:
            tool_response_str = (
                json.dumps(tool_response) if isinstance(tool_response, dict)
                else str(tool_response)
            )

            state = _load_state()
            # Check if this satisfies pending verifications
            self._record_verification(tool_name, tool_input, state)

            # Detect new structural changes
            if tool_name in _MODIFY_TOOLS or tool_name in {"Bash", "bash"}:
                change = self._detect_change(tool_name, tool_input, tool_response_str)
                if change:
                    reqs = _VERIFICATION_REQUIREMENTS.get(change["type"], ["cache_clear"])
                    state["pending_verifications"].append(
                        {**change, "remaining": list(reqs), "original_requirements": list(reqs)}
                    )
                    state["structural_changes"].append(change)
                    _save_state(state)
                    return {"passed": True, "injection": self._format_warning(change, reqs)}

            _save_state(state)

            # Report outstanding verifications
            outstanding = [
                f"  - {p['type']} ({p['affected']}): {', '.join(p['remaining'])}"
                for p in state["pending_verifications"]
                if p.get("remaining")
            ]
            if outstanding:
                return {
                    "passed": True,
                    "injection": (
                        "\U0001f4dd Outstanding verifications:\n"
                        + "\n".join(outstanding)
                        + "\n\nComplete these before claiming the change is successful."
                    ),
                }
            return {"passed": True}
        except Exception:
            # Fail open: should never surface as user-visible PostToolUse hook error.
            return {"passed": True}

    # -- private helpers --

    def _detect_change(self, tool_name: str, tool_input: dict, output: str) -> dict | None:
        filepath = tool_input.get("path") or tool_input.get("file_path")
        combined = f"{json.dumps(tool_input)} {output}"
        for pattern, change_type in _STRUCTURAL_PATTERNS:
            m = re.search(pattern, combined, re.MULTILINE)
            if m:
                affected = m.group(2) if len(m.groups()) >= 2 else m.group(1)
                return {
                    "type": change_type,
                    "affected": affected,
                    "filepath": filepath,
                    "timestamp": datetime.now().timestamp(),
                }
        # Large deletions heuristic
        if output:
            dels = len(re.findall(r"^-[^-]", output, re.MULTILINE))
            if dels > 10:
                return {
                    "type": "large_deletion",
                    "affected": f"{dels} lines",
                    "filepath": filepath,
                    "timestamp": datetime.now().timestamp(),
                }
        return None

    def _record_verification(self, tool_name: str, tool_input: dict, state: dict) -> None:
        if tool_name not in {"Bash", "bash"}:
            return
        cmd = tool_input.get("command", "")
        satisfied = []
        for pending in state["pending_verifications"]:
            reqs = pending.get("remaining", [])
            if "grep_references" in reqs and re.search(r"\b(grep|rg|ag|find)\b", cmd):
                if pending.get("affected", "") in cmd:
                    reqs.remove("grep_references")
            if "cache_clear" in reqs and re.search(r"(rm.*__pycache__|find.*-delete.*\.pyc|pyclean)", cmd):
                reqs.remove("cache_clear")
            if "execution_test" in reqs and re.search(r"(python|pytest|\.py)", cmd):
                reqs.remove("execution_test")
            if "registry_check" in reqs and re.search(r"grep.*(\.json|\.yaml|\.toml|config)", cmd):
                reqs.remove("registry_check")
            pending["remaining"] = reqs
            if not reqs:
                satisfied.append(pending)
        for s in satisfied:
            state["pending_verifications"].remove(s)
            state["completed_verifications"].append(
                {**s, "completed_at": datetime.now().isoformat()}
            )

    def _format_warning(self, change: dict, reqs: list[str]) -> str:
        req_str = "\n".join(f"  - {r}" for r in reqs)
        return (
            f"\U0001f4cb STRUCTURAL CHANGE DETECTED\n"
            f"Change type: {change['type']}\n"
            f"Affected: {change['affected']}\n"
            f"File: {change.get('filepath', '?')}\n"
            f"Required verifications:\n{req_str}"
        )
