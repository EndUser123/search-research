#!/usr/bin/env python3
"""PostToolUse Hook: Artifact Validator for Grounded Artifact Validation.

Injects grounded artifact context when available and cleans up on success.
"""


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

import json
import os
import re
import sys
from pathlib import Path

from shared_utils import resolve_session_id as _resolve_session_id_from_utils

# Add hooks lib to path
hooks_lib = Path(__file__).resolve().parent / "__lib"
sys.path.insert(0, str(hooks_lib))

def _safe_id(value: str) -> str:
    """Sanitize a string for use in filenames."""
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)

def _resolve_session_id(data: dict) -> str:
    """Delegates to shared_utils.resolve_session_id()."""
    return _resolve_session_id_from_utils(data)

def _resolve_terminal_id(data: dict) -> str:
    """Resolve terminal id from hook payload first, then environment."""
    session_obj = data.get("session")
    if isinstance(session_obj, dict):
        for key in ("terminal_id", "terminalId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in ("terminal_id", "terminalId", "CLAUDE_TERMINAL_ID"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_TERMINAL_ID", "").strip()

def _artifact_candidates(data: dict) -> list[Path]:
    """Return candidate artifact paths in precedence order."""
    session_id = _resolve_session_id(data)
    if not session_id:
        return []

    hooks_dir = Path(__file__).resolve().parent
    safe_session = _safe_id(session_id)
    state_dir = hooks_dir / "state"
    terminal_id = _resolve_terminal_id(data)

    candidates: list[Path] = []
    if terminal_id:
        safe_terminal = _safe_id(terminal_id)
        candidates.append(state_dir / f"grounded_artifact_{safe_terminal}_{safe_session}.json")
    candidates.append(state_dir / f"grounded_artifact_{safe_session}.json")
    return candidates

def _artifact_path(data: dict) -> Path | None:
    """Get the artifact file path for this scope.

    Prefer the current terminal+session scoped file. Fall back to the legacy
    session-scoped artifact path for backward compatibility and tests.
    """
    candidates = _artifact_candidates(data)
    if not candidates:
        return None
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]

def _read_grounded_artifact(data: dict) -> dict | None:
    """Read grounded artifact from state file."""
    artifact_path = _artifact_path(data)
    if not artifact_path or not artifact_path.exists():
        return None

    try:
        content = artifact_path.read_text(encoding="utf-8")
        return json.loads(content)
    except Exception:
        return None

def _write_artifact(data: dict, artifact: dict) -> None:
    """Write artifact back to state file."""
    artifact_path = _artifact_path(data)
    if artifact_path:
        try:
            artifact_path.parent.mkdir(exist_ok=True)
            artifact_path.write_text(json.dumps(artifact), encoding="utf-8")
        except Exception:
            pass  # Write failure is non-critical

def check_and_inject_artifact(data: dict) -> dict | None:
    """If a grounded artifact exists, inject it as context for the LLM."""
    artifact = _read_grounded_artifact(data)
    if not artifact:
        return None

    # Check if already injected (skip to allow validation phase)
    if artifact.get("_injected"):
        return None

    schema = artifact.get("schema", "unknown")

    if schema == "blocked_command":
        tool_name = artifact.get("tool_name", "?")
        command = artifact.get("tool_input", {}).get("command", "?")
        hook = artifact.get("blocking_hook", "?")
        reason = artifact.get("raw_reason", "?")

        injection = (
            f"GROUNDED ARTIFACT (mechanical - not LLM generated):\n"
            f"  Tool: {tool_name}\n"
            f"  Command: {command}\n"
            f"  Blocked by: {hook}\n"
            f"  Reason: {reason}\n\n"
            f"When explaining this block, you MUST quote the exact command above. "
            f"Do not reference commands or hooks from elsewhere in your context."
        )

        # Mark as injected (write back to state) so validation can run on next call
        artifact["_injected"] = True
        _write_artifact(data, artifact)

        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": injection
            }
        }

    if schema == "git_safety_block":
        tool_name = artifact.get("tool_name", "?")
        command = artifact.get("tool_input", {}).get("command", "?")
        git_subcommand = artifact.get("git_subcommand", "?")
        hook = artifact.get("blocking_hook", "?")
        reason = artifact.get("raw_reason", "?")

        injection = (
            f"GROUNDED ARTIFACT (mechanical - not LLM generated):\n"
            f"  Tool: {tool_name}\n"
            f"  Git subcommand: {git_subcommand}\n"
            f"  Command: {command}\n"
            f"  Blocked by: {hook}\n"
            f"  Reason: {reason}\n\n"
            f"When explaining this block, you MUST quote the exact git subcommand and command above. "
            f"Do not reference commands or hooks from elsewhere in your context."
        )

        # Mark as injected (write back to state) so validation can run on next call
        artifact["_injected"] = True
        _write_artifact(data, artifact)

        return {
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": injection
            }
        }

    return None

def cleanup_stale_artifact(data: dict) -> None:
    """Delete grounded artifact when the LLM makes a successful tool call."""
    artifact_path = _artifact_path(data)
    if artifact_path and artifact_path.exists():
        try:
            artifact_path.unlink(missing_ok=True)
        except Exception:
            pass  # Cleanup failure is non-critical

def validate_rca_against_artifact(data: dict) -> dict | None:
    """Check if RCA output references the correct grounded artifact.

    Returns None if valid or no artifact. Returns injection message if drift detected.
    """
    try:
        artifact = _read_grounded_artifact(data)
        if not artifact:
            return None

        tool_result = str(data.get("tool_result", ""))
        if not tool_result or len(tool_result) < 50:
            return None

        # Only validate if this looks like an RCA/explanation
        # Use specific markers to avoid false positives on routine tool outputs
        rca_markers = ["root cause", "why this happened", "diagnosis", "the command was blocked"]
        result_lower = tool_result.lower()
        if not any(marker in result_lower for marker in rca_markers):
            return None

        # Check: does the RCA mention the actual command?
        actual_command = artifact.get("tool_input", {}).get("command", "")
        if not actual_command:
            return None

        # Extract a meaningful substring (first 60 chars)
        command_snippet = actual_command[:60]

        # Check for exact command match first (fast path)
        if command_snippet in tool_result:
            # Command is mentioned - no substring drift
            # But still check for tool-type drift below
            pass
        else:
            # DRIFT DETECTED: RCA doesn't mention the actual command
            # Check concept drift too via token overlap
            artifact_tokens = set(artifact.get("command_tokens", []))
            if artifact_tokens:
                result_words = set(result_lower.split())
                overlap = artifact_tokens & result_words
                overlap_ratio = len(overlap) / len(artifact_tokens) if artifact_tokens else 0

                if overlap_ratio < 0.3:
                    # Strong drift - the RCA is talking about something completely different
                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PostToolUse",
                            "additionalContext": (
                                f"WARNING: Your explanation may reference the wrong artifact.\n"
                                f"The ACTUAL blocked command was: {actual_command}\n"
                                f"The blocking hook was: {artifact.get('blocking_hook', '?')}\n"
                                f"Please verify your explanation matches this specific command."
                            )
                        }
                    }

        # Check tool-type drift heuristic (runs regardless of substring match)
        # This catches cases where RCA mentions git safety concepts for non-git commands
        tool_name = artifact.get("tool_name", "")
        if tool_name == "Bash":
            # Git safety phrases that indicate the RCA is about git
            git_safety_phrases = [
                "global git status",
                "git status without path limiter",
                "git safety gate",
                "git operations during merge",
                "git safety check"
            ]

            # Check if RCA has git safety phrases
            has_git_phrases = any(phrase in result_lower for phrase in git_safety_phrases)

            # Check if actual command is actually git-related
            command_lower = actual_command.lower()
            is_git_command = (
                command_lower.startswith("git ") or
                " git " in command_lower or
                any(word in command_lower for word in ["git-status", "git-diff", "git-log"])
            )

            # Tool-type drift: git safety phrases but not a git command
            if has_git_phrases and not is_git_command:
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": (
                            f"WARNING: Your explanation mentions git safety but the actual command was not git-related.\n"
                            f"The ACTUAL blocked command was: {actual_command}\n"
                            f"The blocking hook was: {artifact.get('blocking_hook', '?')}\n"
                            f"Please verify your explanation matches this specific command."
                        )
                    }
                }

        return None
    except Exception:
        # Best-effort: validation failures should not break the hook
        return None

def main():
    """Main entry point."""
    try:
        raw_data = sys.stdin.read()
        if not raw_data:
            sys.exit(0)
        data = json.loads(raw_data)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)
    try:
        # Try to inject artifact context (only once, marked with _injected flag)
        injection_result = check_and_inject_artifact(data)
        if injection_result:
            print(json.dumps(injection_result))
            # DON'T delete yet - keep artifact for validation phase
            sys.exit(0)

        # Validate RCA output for drift (after injection phase, before cleanup)
        drift_warning = validate_rca_against_artifact(data)
        if drift_warning:
            print(json.dumps(drift_warning))

        # Cleanup after validation has had a chance to run
        cleanup_stale_artifact(data)
    except Exception:
        # Artifact validation is advisory only. Never surface runtime failures
        # as PostToolUse hook errors.
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
