#!/usr/bin/env python3
from __future__ import annotations

"""In-process wrapper for post_tool_use_change_propagation.

Absorbs the standalone subprocess into the PostToolUse router.
Detects structural file changes and tracks verification requirements.

State is SESSION-scoped via the canonical state contract (__lib/state_paths.py),
i.e. .claude/state/sessions/{session_id}/propagation_state.json. Session scoping
gives both properties this hook needs:
  - multi-terminal isolation: concurrent terminals are distinct CC sessions, so
    they never share a state file (the old CSF_STATE_DIR path resolved to ONE
    shared file across all terminals);
  - staleness immunity: a new session starts from a fresh directory, so records
    from a prior session (or a prior detector version) can never bleed in — the
    "stale false positive" class that bit this hook twice.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from posttooluse.base import PostToolUseHook

# Tools that modify files. Must include Edit/MultiEdit so the Edit-diff branch
# of _detect_change is actually reachable (the class tool_matcher already routes
# them here; this gate previously excluded them, making Edit detection dead).
_MODIFY_TOOLS = {"write_file", "str_replace_editor", "edit_file", "Write", "Edit", "MultiEdit", "patch"}
_BASH_TOOLS = {"Bash", "bash"}
_EDIT_TOOLS = {"Edit", "MultiEdit", "str_replace_editor", "edit_file", "patch"}
_AFFECTED_KINDS = ("path", "symbol", "magnitude")

# Single source of truth for change-type contracts. Each live type declares
# its `affected_kind` (the semantic shape of `affected`) and the requirement
# keys a producer of this type must verify. The producer registry
# (`_PRODUCERS`) and the consumer metadata (`_REQUIREMENT_META`) are kept in
# lock-step with this table by invariant tests — adding a type or requirement
# without matching producer/consumer coverage fails CI.
#
# Dead keys removed vs. the pre-hardening table (no detector emitted them):
#   - "import_removal": never produced; "file_rename": never produced.
#     "file_rename"'s requirement "import_update" had no consumer handler
#     either, so both halves of the pair were dead config.
_VERIFICATION_REQUIREMENTS = {
    "file_deletion": {
        "affected_kind": "path",
        "requirements": ["grep_references"],
    },
    "function_removal": {
        "affected_kind": "symbol",
        "requirements": ["execution_test"],
    },
    "large_deletion": {
        "affected_kind": "magnitude",
        "requirements": ["execution_test"],
    },
}

# Per-requirement consumer metadata. Drives `_record_verification` so the
# consumer has no independent if/elif branch set that can drift from the
# requirements table. Symmetric invariant (locked by tests):
#   union(requirements across _VERIFICATION_REQUIREMENTS) == _REQUIREMENT_META.keys()
#
# Dead consumer branches removed vs. pre-hardening (no type declared them):
#   - "cache_clear": only reached via the unknown-type fallback, never hit.
#   - "registry_check": never declared by any type.
_REQUIREMENT_META = {
    "grep_references": {
        # A deleted file has nothing left to grep — path absence legitimately
        # satisfies this requirement. Path-kind records only; gated by
        # affected_kind so symbol/magnitude records can never trip it.
        "path_absence_satisfies": True,
        "command_match": r"\b(grep|rg|ag|find)\b",
        "requires_affected_in_cmd": True,
    },
    "execution_test": {
        # Never auto-satisfied by path absence: a function removal or large
        # deletion needs a test run regardless of any path's existence.
        "path_absence_satisfies": False,
        "command_match": r"(python|pytest|\.py)",
        "requires_affected_in_cmd": False,
    },
}


# -- Producer registry -------------------------------------------------------
# Keys MUST equal `_VERIFICATION_REQUIREMENTS.keys()` (locked by invariant
# test). A producer cannot emit a type the requirements table doesn't know
# about, because the table is the only source of `affected_kind`.

def _extract_edit_diff(tool_input):
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        old = "\n".join(str(e.get("old_string", "")) for e in edits if isinstance(e, dict))
        new = "\n".join(str(e.get("new_string", "")) for e in edits if isinstance(e, dict))
    else:
        old = str(tool_input.get("old_string", "") or "")
        new = str(tool_input.get("new_string", "") or "")
    return old, new


def _detect_file_deletion(tool_name, tool_input):
    if tool_name not in _BASH_TOOLS:
        return None
    from __lib.structural_change import deletions_in_command
    paths = deletions_in_command(tool_input.get("command", ""))
    return paths[0] if paths else None


def _detect_function_removal(tool_name, tool_input):
    if tool_name not in _EDIT_TOOLS:
        return None
    from __lib.structural_change import removed_symbols
    old, new = _extract_edit_diff(tool_input)
    syms = removed_symbols(old, new)
    return syms[0][1] if syms else None


def _detect_large_deletion(tool_name, tool_input):
    if tool_name not in _EDIT_TOOLS:
        return None
    from __lib.structural_change import lines_removed
    old, new = _extract_edit_diff(tool_input)
    removed = lines_removed(old, new)
    return f"{removed} lines" if removed > 10 else None


_PRODUCERS = {
    "file_deletion": _detect_file_deletion,
    "function_removal": _detect_function_removal,
    "large_deletion": _detect_large_deletion,
}


def _resolve_session_id(data: dict) -> str:
    """Resolve the CC session id from a PostToolUse payload.

    Mirrors PostToolUse.py's resolution (nested `session.*` then flat keys) so
    the state file is scoped to the same session the rest of the router sees.
    Falls back to "unknown" — never to a shared global path.
    """
    session_obj = data.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            value = session_obj.get(key)
            if value:
                return str(value)
    for key in ("session_id", "sessionId"):
        value = data.get(key)
        if value:
            return str(value)
    return "unknown"


class ChangePropagationHook(PostToolUseHook):
    """Track structural file changes and required verifications."""

    tool_matcher = {"Write", "Edit", "MultiEdit", "Bash"}
    env_var = "CSF_CHANGE_PROPAGATION"
    default_enabled = True

    # Default for direct process() calls (e.g. unit tests) that bypass run().
    _session_id: str = "unknown"

    def run(self, data: dict[str, Any]) -> dict[str, Any]:
        # Capture the session id before the base class strips data down to
        # tool_name/tool_input/tool_response for process().
        self._session_id = _resolve_session_id(data if isinstance(data, dict) else {})
        return super().run(data)

    def _state_path(self) -> Path:
        from __lib.state_paths import get_session_state_path

        return get_session_state_path(self._session_id, "propagation_state.json")

    def _load_state(self) -> dict:
        state_file = self._state_path()
        if state_file.exists():
            try:
                with open(state_file) as f:
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

    def _save_state(self, state: dict) -> None:
        try:
            state_file = self._state_path()
            state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(state_file, "w") as f:
                json.dump(state, f, indent=2)
        except (OSError, PermissionError):
            # Fail open: state persistence issues should not surface as hook errors.
            return

    def process(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_response: dict[str, Any],  # noqa: ARG002 — not used; detection is source-only
    ) -> dict[str, Any]:
        try:
            state = self._load_state()
            # Check if this satisfies pending verifications
            self._record_verification(tool_name, tool_input, state)

            # Detect new structural changes
            if tool_name in _MODIFY_TOOLS or tool_name in _BASH_TOOLS:
                change = self._detect_change(tool_name, tool_input)
                if change:
                    meta = _VERIFICATION_REQUIREMENTS[change["type"]]
                    reqs = list(meta["requirements"])
                    state["pending_verifications"].append(
                        {**change, "remaining": reqs, "original_requirements": list(reqs)}
                    )
                    state["structural_changes"].append(change)
                    self._save_state(state)
                    return {"passed": True, "injection": self._format_warning(change, reqs)}

            self._save_state(state)

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
        """Detect a structural change via the producer registry.

        Returns a change dict stamped with `affected_kind` drawn from
        `_VERIFICATION_REQUIREMENTS` (single source of truth), or None.

        Source-aware by design: shell deletions come from the Bash *command*,
        symbol/line removals from the Edit *diff* (old_string vs new_string).
        File content and tool output are NEVER scanned as operations — that
        conflates string literals / test fixtures with real changes (the
        historical false-positive class, e.g. a test body containing "rm x.py").
        A Write creates new content; the prior file state is unknown, so no
        deletion is inferred from it.
        """
        filepath = tool_input.get("path") or tool_input.get("file_path")
        now = datetime.now().timestamp()
        for ctype, detector in _PRODUCERS.items():
            affected = detector(tool_name, tool_input)
            if affected is None:
                continue
            meta = _VERIFICATION_REQUIREMENTS[ctype]
            return {
                "type": ctype,
                "affected": affected,
                "affected_kind": meta["affected_kind"],
                "filepath": filepath,
                "timestamp": now,
            }
        return None

    def _record_verification(self, tool_name: str, tool_input: dict, state: dict) -> None:
        if tool_name not in _BASH_TOOLS:
            return
        cmd = tool_input.get("command", "")
        satisfied = []
        for pending in state["pending_verifications"]:
            reqs = pending.get("remaining", [])
            affected = pending.get("affected", "")
            kind = pending.get("affected_kind", "")

            # Fail safe: missing/malformed kind → no auto-satisfy. This also
            # covers stale records written by older hook versions (no
            # affected_kind field) — they will not auto-satisfy until the
            # run that created them re-stamps them.
            if kind not in _AFFECTED_KINDS:
                continue

            for req in list(reqs):
                meta = _REQUIREMENT_META.get(req)
                if meta is None:
                    continue  # undeclared requirement: no handler, never auto-satisfy

                # Path-absence auto-satisfy: path-kind + eligible requirement only.
                # Symbol/magnitude records can never trip this (kind != "path"),
                # and execution_test is never path-eligible regardless of kind.
                if (kind == "path" and affected
                        and meta.get("path_absence_satisfies")
                        and not Path(affected).exists()):
                    reqs.remove(req)
                    continue

                # Command-match auto-satisfy (metadata-driven).
                pattern = meta.get("command_match")
                if pattern and re.search(pattern, cmd):
                    if meta.get("requires_affected_in_cmd", False):
                        if affected and (affected in cmd or Path(affected).name in cmd):
                            reqs.remove(req)
                    else:
                        reqs.remove(req)
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
