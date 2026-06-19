#!/usr/bin/env python3
from __future__ import annotations

"""In-process wrapper for post_tool_use_change_propagation.

Absorbs the standalone subprocess into the PostToolUse router.
Detects structural file changes and tracks verification requirements.

State is terminal-scoped via CSF_STATE_DIR env var.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

# Tools that modify files. Must include Edit/MultiEdit so the Edit-diff branch
# of _detect_change is actually reachable (the class tool_matcher already routes
# them here; this gate previously excluded them, making Edit detection dead).
_MODIFY_TOOLS = {"write_file", "str_replace_editor", "edit_file", "Write", "Edit", "MultiEdit", "patch"}

_VERIFICATION_REQUIREMENTS = {
    "function_removal": ["execution_test"],
    "import_removal": [],
    "file_deletion": ["grep_references"],
    "file_rename": ["import_update"],
    "large_deletion": ["execution_test"],
}

def _get_state_file() -> Path:
    """Get terminal-scoped state file path."""
    if "CSF_STATE_DIR" in os.environ:
        return Path(os.environ["CSF_STATE_DIR"]) / "propagation_state.json"

    # Terminal-scoped default: .claude/state/{terminal_id}/propagation_state.json
    terminal_id = os.environ.get("TERMINAL_ID", "unknown")
    return Path("P:/.claude/state") / terminal_id / "propagation_state.json"

_STATE_FILE = _get_state_file()


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
        tool_response: dict[str, Any],  # noqa: ARG002 — not used; detection is source-only
    ) -> dict[str, Any]:
        try:
            state = _load_state()
            # Check if this satisfies pending verifications
            self._record_verification(tool_name, tool_input, state)

            # Detect new structural changes
            if tool_name in _MODIFY_TOOLS or tool_name in {"Bash", "bash"}:
                change = self._detect_change(tool_name, tool_input)
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

    def _detect_change(self, tool_name: str, tool_input: dict) -> dict | None:
        """Detect a structural change from the RIGHT field per tool.

        Source-aware by design: shell deletions come from the Bash *command*,
        symbol/line removals from the Edit *diff* (old_string vs new_string).
        File content and tool output are NEVER scanned as operations — that
        conflates string literals / test fixtures with real changes (the
        historical false-positive class, e.g. a test body containing "rm x.py").
        A Write creates new content; the prior file state is unknown, so no
        deletion is inferred from it.
        """
        from __lib.structural_change import deletions_in_command, lines_removed, removed_symbols

        filepath = tool_input.get("path") or tool_input.get("file_path")
        now = datetime.now().timestamp()

        if tool_name in {"Bash", "bash"}:
            paths = deletions_in_command(tool_input.get("command", ""))
            if paths:
                return {"type": "file_deletion", "affected": paths[0],
                        "filepath": filepath, "timestamp": now}
            return None

        if tool_name in {"Edit", "MultiEdit", "str_replace_editor", "edit_file", "patch"}:
            edits = tool_input.get("edits")
            if isinstance(edits, list):  # MultiEdit
                old = "\n".join(str(e.get("old_string", "")) for e in edits if isinstance(e, dict))
                new = "\n".join(str(e.get("new_string", "")) for e in edits if isinstance(e, dict))
            else:
                old = str(tool_input.get("old_string", "") or "")
                new = str(tool_input.get("new_string", "") or "")
            syms = removed_symbols(old, new)
            if syms:
                return {"type": "function_removal", "affected": syms[0][1],
                        "filepath": filepath, "timestamp": now}
            removed = lines_removed(old, new)
            if removed > 10:
                return {"type": "large_deletion", "affected": f"{removed} lines",
                        "filepath": filepath, "timestamp": now}
            return None

        # Write (new content; prior state unknown) and everything else: no deletion.
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
