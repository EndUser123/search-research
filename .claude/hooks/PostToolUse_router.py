#!/usr/bin/env python3
from __future__ import annotations

"""
PostToolUse Router - In-Process Hook Execution
==============================================

This router consolidates 4 PostToolUse hooks into a single in-process execution:
- FixValidator: Validates code fixes for syntax/undefined methods
- ChangeVerification: Tracks file changes (silent)
- FalsificationAssessor: Assesses outcomes against expectations
- SemanticCompress: Compresses large outputs asynchronously

Previous approach (subprocess): ~184ms per tool use
New approach (in-process): ~5-10ms per tool use (~95% reduction)

The hooks are imported as Python modules and executed directly
instead of spawning subprocess.run() for each hook.

Author: CSF NIP
Version: 2.1.1 (Fix auto-commit stdout pollution causing invalid JSON)
"""

import json
import logging
import os
import re
import sys
import time
from pathlib import Path

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

hooks_lib = HOOKS_DIR / "__lib"
if str(hooks_lib) not in sys.path:
    sys.path.insert(0, str(hooks_lib))

try:
    from __lib.hook_base import hook_main
except ImportError:
    from hook_base import hook_main  # type: ignore

# Import the consolidated hook package
from posttooluse import create_registry, is_block_result

# Import tool sequence tracking and terminal detection
try:
    from tool_sequence_manager import ToolSequenceManager

    LEGACY_TRACKING_AVAILABLE = True
except ImportError:
    LEGACY_TRACKING_AVAILABLE = False

try:
    from __lib.terminal_detection import detect_terminal_id
except ImportError:
    try:
        from terminal_detection import detect_terminal_id  # type: ignore
    except ImportError:

        def detect_terminal_id() -> str:
            return ""


try:
    from __lib.runtime_env import ledger_available as _ledger_available
except ImportError:

    def _ledger_available() -> bool:
        return False


LEDGER_AVAILABLE = _ledger_available()

# Import ledger functions with fallback
try:
    from __lib.hook_ledger import (
        append_event as append_ledger_event,
    )
    from __lib.hook_ledger import (
        detect_terminal_id_from_payload,
        get_active_turn,
    )
except (ImportError, AttributeError):

    def append_ledger_event(*args, **kwargs) -> bool:
        return False

    def detect_terminal_id_from_payload(data: dict | None = None) -> str:
        return ""

    def get_active_turn(terminal_id: str) -> str | None:
        return None


try:
    from evidence_store import (
        append_tool_event,
        get_active_turn as get_active_evidence_turn,
        resolve_session_id,
    )

    EVIDENCE_AVAILABLE = True
except ImportError:
    EVIDENCE_AVAILABLE = False

    def append_tool_event(*args, **kwargs) -> bool:
        return False

    def get_active_evidence_turn(session_id: str, terminal_id: str) -> str | None:
        return None

    def resolve_session_id(explicit: str = "") -> str:
        return ""


# Buffered logger for router orchestration logging
try:
    from buffered_logger import DEBUG, create_router_entry, get_hook_invocation_logger
except ImportError:
    get_hook_invocation_logger = None
    create_router_entry = None
    DEBUG = False

# Optional debug mode
ROUTER_DEBUG = os.environ.get("ROUTER_DEBUG", "0") == "1"

# Error cache to track unique errors per session and avoid spam
ERROR_CACHE: dict[
    str, dict
] = {}  # {error_key: {"count": int, "first_seen": str, "last_seen": str}}

# Logging setup with NullHandler (prevents stderr output)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
log_dir = HOOKS_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "hook_errors.jsonl"


def log(msg: str) -> None:
    """Log debug messages to stdout (not stderr - only real errors go to stderr)."""
    if ROUTER_DEBUG:
        _logger.warning(f"Router: {msg}")


def _resolve_session_from_payload(data: dict[str, object]) -> str:
    """Resolve session id from payload/env/persisted context."""
    explicit_session_id = (
        str(
            data.get("session_id")
            or data.get("sessionId")
            or data.get("conversation_id")
            or data.get("conversationId")
            or ""
        )
        .strip()
        .lower()
    )
    session_id = explicit_session_id

    tool_input = data.get("tool_input")
    if (not session_id) and isinstance(tool_input, dict):
        explicit_session_id = (
            str(
                tool_input.get("session_id")
                or tool_input.get("sessionId")
                or tool_input.get("conversation_id")
                or tool_input.get("conversationId")
                or ""
            )
            .strip()
            .lower()
        )
        session_id = explicit_session_id

    if explicit_session_id and not re.fullmatch(r"[a-f0-9\-]{36}", explicit_session_id):
        return ""

    if not re.fullmatch(r"[a-f0-9\-]{36}", session_id):
        session_id = resolve_session_id("")
    return session_id


def _set_session_terminal_context(data: dict[str, object]) -> str:
    """Pin session identity for PostToolUse + Stop ledger consistency."""
    session_id = _resolve_session_from_payload(data)
    if not session_id:
        os.environ.pop("CLAUDE_SESSION_ID", None)
        os.environ.pop("CLAUDE_TERMINAL_ID", None)
        return ""

    os.environ["CLAUDE_SESSION_ID"] = session_id
    terminal_id = detect_terminal_id_from_payload(data) or detect_terminal_id()
    if not terminal_id:
        terminal_id = f"session_{session_id}"
    if terminal_id:
        os.environ["CLAUDE_TERMINAL_ID"] = terminal_id
        data.setdefault("terminal_id", terminal_id)
    return session_id


def _handle_tracking_error(error: Exception, tool_name: str, command: str) -> None:
    """
    Handle tool tracking errors with structured output and deduplication.

    Args:
        error: The exception that occurred
        tool_name: Name of the tool being tracked
        command: Command string being executed
    """
    import traceback

    # Create error key for deduplication
    error_type = type(error).__name__
    error_msg = str(error)
    error_key = f"{error_type}:{error_msg[:50]}"

    # Track error in cache
    if error_key not in ERROR_CACHE:
        ERROR_CACHE[error_key] = {
            "count": 0,
            "first_seen": time.time(),
            "last_seen": time.time(),
        }

    ERROR_CACHE[error_key]["count"] += 1
    ERROR_CACHE[error_key]["last_seen"] = time.time()
    count = ERROR_CACHE[error_key]["count"]

    # Log to file on first occurrence or every 10th occurrence
    if count == 1 or count % 10 == 0:
        hook_name = "PostToolUse_router"
        hook_file = Path(__file__).absolute()

        # Prepare structured error record
        error_record = {
            "timestamp": time.time(),
            "hook": hook_name,
            "hook_file": str(hook_file),
            "tool": tool_name,
            "command": command[:100] + ("..." if len(command) > 100 else ""),
            "error_type": error_type,
            "error_msg": error_msg,
            "occurrence": count,
            "first_seen": ERROR_CACHE[error_key]["first_seen"],
            "traceback": traceback.format_exc(),
        }

        # Write to log file (graceful degradation if file write fails)
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(error_record) + "\n")
        except OSError:
            pass  # Best-effort logging, never block hook execution

        # Also log to stdout for ROUTER_DEBUG mode
        if ROUTER_DEBUG:
            _logger.warning(f"\n{'='*70}")
            _logger.warning(f"Tool tracking error in {hook_name}")
            _logger.warning("="*70)
            _logger.warning(f"Hook: {hook_name}")
            _logger.warning(f"Hook file: {hook_file}")
            _logger.warning(f"Tool: {tool_name}")
            _logger.warning(f"Command: {command[:100]}...")
            _logger.warning(f"Error: {error_type}: {error_msg}")
            _logger.warning(f"Occurrence: #{count} (first seen: {ERROR_CACHE[error_key]['first_seen']})")
            _logger.warning("Run hook directly with --test flag for diagnostics")
            _logger.warning(f"  python {hook_file} --test")
            _logger.warning("\nTraceback (last 50 lines):")
            _logger.warning("-"*70)

            # Get last 50 lines of traceback
            tb_lines = traceback.format_exc().splitlines()
            for line in tb_lines[-50:]:
                _logger.warning(line)

            _logger.warning(f"{'='*70}\n")
    else:
        log(f"Tool tracking error (occurrence #{count}, suppressed): {error}")


SIGNAL_DIR = Path("P:/.claude/state/signals")


def _resolve_session_id_for_intent(data: dict[str, object]) -> str:
    """Resolve session id from nested/flat payload first, then env."""
    session_obj = data.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in (
        "session_id",
        "sessionId",
        "conversation_id",
        "conversationId",
        "CLAUDE_SESSION_ID",
    ):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return os.environ.get("CLAUDE_SESSION_ID", "").strip()


def _resolve_terminal_id_for_intent() -> str:
    """Resolve terminal id, mirroring skill_enforcer._get_terminal_id."""
    terminal = os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    if terminal:
        return terminal
    try:
        from __lib.terminal_detection import detect_terminal_id

        detected = str(detect_terminal_id() or "").strip()
        if detected:
            return detected
    except Exception:
        pass
    return ""


def _clear_pending_skill_intent(data: dict[str, object]) -> None:
    """Clear pending_command_intent file when Skill() is called.

    Handshake: UserPromptSubmit sets the flag, PreToolUse blocks
    until Skill is called, and PostToolUse clears the flag here.

    Writer (skill_enforcer) uses terminal-scoped filenames. We must delete the
    same terminal-scoped file; session-scoped is kept as a legacy fallback.

    Enhancement: Write signal file for PreToolUse to inject workflow reminder
    on first tool use after Skill() is called.
    """
    session_id = _resolve_session_id_for_intent(data)
    terminal_id = _resolve_terminal_id_for_intent()

    state_dirs = (
        HOOKS_DIR / "state",
        Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state",
    )

    # Extract skill name from tool input for signal file
    tool_input = data.get("toolInput") or data.get("tool_input") or {}
    skill_name = str(tool_input.get("skill", "")).strip() if isinstance(tool_input, dict) else ""

    # Primary: terminal-scoped (matches what skill_enforcer writes)
    if terminal_id:
        safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)
        for base_dir in state_dirs:
            intent_file = base_dir / f"pending_command_intent_{safe_terminal}.json"
            if intent_file.exists():
                intent_file.unlink(missing_ok=True)
                # Write signal file for PreToolUse workflow reminder
                if skill_name:
                    signal_file = base_dir / f"first_tool_after_skill_{safe_terminal}.json"
                    try:
                        import json
                        from datetime import datetime

                        signal_file.write_text(
                            json.dumps(
                                {
                                    "skill": skill_name,
                                    "timestamp": datetime.now().isoformat(),
                                    "terminal_id": terminal_id,
                                }
                            ),
                            encoding="utf-8",
                        )
                    except Exception:
                        pass  # Best-effort signal write
                return

    # Legacy fallback: session-scoped (pre-terminal-scoped intent files)
    if session_id:
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
        for base_dir in state_dirs:
            intent_file = base_dir / f"pending_command_intent_{safe_session}.json"
            if intent_file.exists():
                intent_file.unlink(missing_ok=True)
                return


def _write_error_signal(tool_name: str, tool_input: dict, tool_result: object) -> None:
    """Delegate to shared writer (eliminates dual-writer conflict)."""
    try:
        from __lib.write_tool_error_signal import write_tool_error_signal as _write
        _write(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_result=tool_result,
        )
    except Exception:
        pass


@hook_main
def main() -> None:
    """
    Main entry point for PostToolUse hook.

    Reads JSON from stdin with tool_name, tool_input, tool_response.
    Runs all hooks in-process and outputs combined results.

    Input format:
    {
        "tool_name": "Edit|Write|Bash|...",
        "tool_input": {...},
        "tool_response": {...}
    }

    Output format:
    {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "combined messages..."
        }
    }
    """
    input_text = sys.stdin.read().strip()
    if not input_text:
        print("{}")
        sys.exit(0)

    # Parse input data - handle malformed JSON gracefully
    try:
        data = json.loads(input_text)
    except json.JSONDecodeError:
        if ROUTER_DEBUG:
            log("Invalid JSON input")
            # Also log to file for diagnostics
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(
                        json.dumps(
                            {
                                "timestamp": time.time(),
                                "hook": "PostToolUse_router",
                                "error": "Invalid JSON input",
                                "input_length": len(input_text),
                            }
                        )
                        + "\n"
                    )
            except OSError:
                pass
        print("{}")
        sys.exit(0)

    if not isinstance(data, dict):
        print("{}")
        sys.exit(0)

    # Normalize input field names
    if "tool_input" not in data and "toolInput" in data:
        data["tool_input"] = data["toolInput"]
    if "tool_response" not in data:
        if "toolResult" in data:
            data["tool_response"] = data["toolResult"]
        elif "tool_result" in data:
            data["tool_response"] = data["tool_result"]

    tool_name_raw = data.get("tool_name")
    if not isinstance(tool_name_raw, str) or not tool_name_raw.strip():
        print("{}")
        sys.exit(0)

    tool_name_raw = tool_name_raw.strip()
    data["tool_name"] = tool_name_raw

    if "tool_input" in data and not isinstance(data.get("tool_input"), dict):
        data["tool_input"] = {}

    # Registry preflight: block before any logging or side effects run.
    registry = create_registry()
    result = registry.run_all(data)
    if is_block_result(result):
        print(json.dumps(result))
        sys.exit(0)

    session_id = _set_session_terminal_context(data)

    # Track tool usage for empirical claims validation
    if LEGACY_TRACKING_AVAILABLE or EVIDENCE_AVAILABLE:
        try:
            tool_name = data.get("tool_name", "Unknown")
            tool_input = data.get("tool_input", {})
            tool_response = data.get("tool_response", {})

            command = ""
            if isinstance(tool_input, dict):
                command = (
                    tool_input.get("command", "")
                    or tool_input.get("file_path", "")
                    or tool_input.get("TargetFile", "")
                    or tool_input.get("AbsolutePath", "")
                    or tool_input.get("SearchPath", "")
                    or tool_input.get("DirectoryPath", "")
                    or tool_input.get("SearchDirectory", "")
                )
            cwd = tool_input.get("cwd", "") or tool_input.get("Cwd", "")

            # Extract output for evidence entity extraction (truncated for storage)
            output = ""
            if tool_response:
                if isinstance(tool_response, str):
                    output = tool_response[:2000]
                elif isinstance(tool_response, dict):
                    # Try common output fields
                    output = str(
                        tool_response.get("content", "")
                        or tool_response.get("output", "")
                        or tool_response.get("result", "")
                        or tool_response.get("stdout", "")
                    )[:2000]

            terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "") or detect_terminal_id()
            session_id = session_id or os.environ.get("CLAUDE_SESSION_ID", "")

            active_turn_id = (
                get_active_evidence_turn(session_id, terminal_id) if terminal_id else None
            )

            if active_turn_id and LEDGER_AVAILABLE:
                append_ledger_event(
                    terminal_id=terminal_id,
                    turn_id=str(active_turn_id),
                    phase="PostToolUse",
                    event_type="tool_used",
                    payload={
                        "name": str(tool_name),
                        "command": str(command),
                        "cwd": str(cwd),
                        "output": str(output),
                        "success": True,
                        "session_id": session_id,
                        "tool_input": tool_input if isinstance(tool_input, dict) else {},
                    },
                )
            elif session_id and EVIDENCE_AVAILABLE:
                append_tool_event(
                    session_id=session_id,
                    terminal_id=terminal_id,
                    tool_name=str(tool_name),
                    command=str(command),
                    cwd=str(cwd),
                    output_excerpt=str(output),
                    success=True,
                    metadata={"source": "PostToolUse_router", "fallback": "evidence_store"},
                )

            if LEGACY_TRACKING_AVAILABLE and not active_turn_id:
                from datetime import UTC, datetime

                ToolSequenceManager.append(
                    {
                        "name": tool_name,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "command": command,
                        "cwd": cwd,
                        "session_id": session_id,
                        "terminal_id": terminal_id,
                        "output": output,
                    },
                    session_id=session_id,
                )
            log(f"Tracked tool: {tool_name}")
        except Exception as e:
            _handle_tracking_error(e, tool_name, command)

    # Track file access for claim-layer enforcement (artifact access log)
    try:
        tool_name_raw = data.get("tool_name", "Unknown")
        tool_input_raw = data.get("tool_input", {}) if isinstance(data.get("tool_input"), dict) else {}
        terminal_id_str = os.environ.get("CLAUDE_TERMINAL_ID", "") or detect_terminal_id()
        session_id_str = session_id or os.environ.get("CLAUDE_SESSION_ID", "")

        if tool_name_raw in ("Read", "Grep", "Glob", "Bash"):
            from PostToolUse_artifact_access_tracker import track_tool_use
            track_tool_use(session_id_str, terminal_id_str, tool_name_raw, tool_input_raw)
    except Exception:
        pass  # Non-blocking artifact tracking

    # --- Features absorbed from PostToolUse.py ---
    tool_input_raw = data.get("tool_input", {}) if isinstance(data.get("tool_input"), dict) else {}

    # A. Skill-first gate: clear pending intent when Skill() is called
    if tool_name_raw == "Skill":
        _clear_pending_skill_intent(data)

    # B. Error signal for competence_injector conditional injection
    try:
        _write_error_signal(tool_name_raw, tool_input_raw, data.get("tool_response", ""))
    except Exception:
        pass  # Best-effort, never block

    # Create hook registry and run all hooks
    router_start = time.perf_counter()
    hooks_executed = []
    any_blocked = False

    # Track router execution for logging
    total_latency = (time.perf_counter() - router_start) * 1000
    tool_name = data.get("tool_name", "Unknown")

    # Log router orchestration
    if get_hook_invocation_logger and create_router_entry:
        try:
            logger = get_hook_invocation_logger()
            logger.log(
                create_router_entry(
                    router_name="PostToolUse_router",
                    hook_type="PostToolUse",
                    tool_name=tool_name,
                    hooks_executed=hooks_executed,
                    total_latency_ms=total_latency,
                    any_blocked=any_blocked,
                )
            )
        except Exception:
            pass  # Fail silently if logging fails

    # Output combined results
    if result:
        print(json.dumps(result))
    else:
        # Return ok:true for newer Claude Code schema validation
        print("{}")


if __name__ == "__main__":
    main()
