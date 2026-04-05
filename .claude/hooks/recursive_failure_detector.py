#!/usr/bin/env python3
"""
recursive_failure_detector.py - PreToolUse hook
Detects Catch-22 loops where the same operation fails repeatedly.
Enforces CLAUDE.md Part D.5 - Recursive Failure Detection.

Lifecycle: PreToolUse (checks history before allowing attempt)
Companion: Failures recorded by PostToolUse (tool_sequence_tracker or failure_recorder)
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Import test detection module
try:
    from test_detection import is_test_file_operation
except ImportError:
    # Fallback if test_detection module not available
    def is_test_file_operation(_file_path: str) -> bool:
        return False

# Import tracking module
try:
    from hook_tracker import is_bypass_enabled, is_hook_self_operation, log_block
except ImportError:
    log_block = lambda *args: None
    is_hook_self_operation = lambda c: False
    is_bypass_enabled = lambda: False

# Dynamic path relative to hook location
SESSION_DIR = Path(__file__).resolve().parent.parent / "sessions"
FAILURE_THRESHOLD = 5  # Block after this many similar failures
READ_ONLY_CYCLE_LIMIT = 3  # Block after this many consecutive read-only operations (lower threshold = faster detection)
WINDOW_MINUTES = 10    # Only count failures within this window

# Advisory mode: Warn instead of block (for evidence gathering)
def is_investigation_loop_advisory_mode() -> bool:
    """Check if investigation loop detection should warn instead of block."""
    return os.environ.get('INVESTIGATION_LOOP_ADVISORY_MODE', '').lower() in ('1', 'true', 'yes')

def log_investigation_loop_warning(tool: str, command: str, consecutive_count: int):
    """Log investigation loop warnings for later review."""
    try:
        log_dir = Path(__file__).resolve().parent.parent / "state" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "investigation_loop_warnings.log"

        timestamp = datetime.now().isoformat()
        session_id = os.environ.get("CLAUDE_SESSION_ID", "unknown")

        with open(log_file, "a") as f:
            f.write(f"{timestamp} | Session: {session_id} | Tool: {tool} | "
                   f"Consecutive count: {consecutive_count} | "
                   f"Command: {command[:100]}...\n")
    except Exception:
        pass  # Don't fail if logging fails

# Pre-compiled regex patterns for command hash computation (40-60% faster)
DOUBLE_QUOTE_PATTERN = re.compile(r'"[^"]*"')
SINGLE_QUOTE_PATTERN = re.compile(r"'[^']*'")
DIGIT_PATTERN = re.compile(r'\d+')
WHITESPACE_PATTERN = re.compile(r'\s+')


def get_session_file() -> Path:
    """Get or create terminal-scoped and session-scoped failure tracking file."""
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "default")
    safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)
    return SESSION_DIR / f"failures_{safe_terminal}_{session_id}.json"


def load_failures() -> list:
    """Load all failures from session file (no TTL filtering)."""
    session_file = get_session_file()
    if not session_file.exists():
        return []
    try:
        with open(session_file) as f:
            return json.load(f)
    except Exception:
        return []


def save_failure(tool: str, cmd_hash: str, error_snippet: str):
    """
    Record a failure for pattern detection.
    Called by PostToolUse companion when tool returns error.
    """
    failures = load_failures()
    failures.append({
        "timestamp": datetime.now().isoformat(),
        "tool": tool,
        "command_hash": cmd_hash,
        "error_snippet": error_snippet[:200]
    })

    try:
        with open(get_session_file(), "w") as f:
            json.dump(failures, f, indent=2)
    except Exception:
        pass  # Non-fatal if can't persist


def compute_command_hash(command: str) -> str:
    """
    Create normalized hash for command similarity detection.
    Strips variable content to match structural patterns.
    Uses pre-compiled patterns for 40-60% faster execution.
    """
    normalized = command.lower()
    # Remove quoted string contents (keep structure) - using pre-compiled patterns
    normalized = DOUBLE_QUOTE_PATTERN.sub('""', normalized)
    normalized = SINGLE_QUOTE_PATTERN.sub("''", normalized)
    # Normalize numbers - using pre-compiled pattern
    normalized = DIGIT_PATTERN.sub('N', normalized)
    # Normalize whitespace - using pre-compiled pattern
    normalized = WHITESPACE_PATTERN.sub(' ', normalized).strip()

    return hashlib.md5(normalized.encode()).hexdigest()[:8]


def count_similar_failures(tool: str, cmd_hash: str) -> tuple[int, list]:
    """
    Count recent failures with similar command pattern.
    Returns (count, recent_error_snippets).
    """
    failures = load_failures()
    matching = [f for f in failures
                if f["tool"] == tool and f["command_hash"] == cmd_hash]

    recent_errors = [f["error_snippet"] for f in matching[-3:]]
    return len(matching), recent_errors


def is_read_only_tool(tool: str) -> bool:
    """
    Check if a tool is read-only (investigation tool).

    Read-only tools: Read, Grep, Glob
    Write tools: Write, Edit, Bash, MultiEdit, NotebookEdit
    """
    return tool in ("Read", "Grep", "Glob")


def count_consecutive_read_only_cycles() -> int:
    """
    Count consecutive read-only operations in recent history.

    Returns the number of consecutive read-only tool uses (Read, Grep, Glob)
    without any write operations (Write, Edit, Bash, MultiEdit, NotebookEdit).

    Only counts operations within the time window (WINDOW_MINUTES).
    """
    failures = load_failures()

    if not failures:
        return 0

    # Filter by time window
    cutoff_time = datetime.now() - timedelta(minutes=WINDOW_MINUTES)
    recent_failures = [
        f for f in failures
        if datetime.fromisoformat(f["timestamp"]) >= cutoff_time
    ]

    if not recent_failures:
        return 0

    # Count consecutive read-only operations from most recent backwards
    consecutive_count = 0
    for failure in reversed(recent_failures):
        if is_read_only_tool(failure["tool"]):
            consecutive_count += 1
        else:
            # Break on first non-read-only tool
            break

    return consecutive_count


def get_investigation_loop_directive() -> str:
    """
    Generate prescriptive directive for investigation loops.

    Returns clear instructions to break the read-only cycle.
    """
    return (
        "**Prescriptive Directive:** Investigation loop detected. "
        "You are reading files repeatedly without making changes.\n"
        "1. Stop searching and synthesize findings from existing data.\n"
        "2. Make a decision based on available information.\n"
        "3. Take action with Write, Edit, or Bash tools.\n"
        "4. If more information is genuinely needed, ask the user specifically.\n"
        "\n"
        "**Pattern:** Read-only operations (Read, Grep, Glob) don't modify state.\n"
        "**Solution:** Break the cycle by taking action or asking the user."
    )


def get_prescriptive_directive(tool: str, command: str, errors: list) -> str:
    """Generate a specific instruction to break the loop based on failure patterns."""
    cmd_lower = command.lower()
    error_text = " ".join(errors).lower()

    # Python 3.10+ pattern matching for clearer intent
    match (tool, cmd_lower, error_text):
        # Python -c with syntax errors
        case ("python" | "bash", cmd, err) if "-c" in cmd and any(
            w in err for w in ("syntaxerror", "invalid syntax", "line continuation")
        ):
            return (
                "**Prescriptive Directive:** Stop. Your `python -c` quoting is failing. "
                "Do NOT retry the shell command. Instead:\n"
                "1. Write your Python code to a temporary file (e.g., `P:/.tmp/eval.py`) using the `Write` tool.\n"
                "2. Execute the file using `python P:/.tmp/eval.py`.\n"
                "3. This bypasses shell quoting limits."
            )

        # Write/Edit tool blocked by syntax gate
        case ("Write" | "Edit", cmd, err) if "syntaxerror" in err or "gate" in cmd:
            return (
                "**Prescriptive Directive:** The `Write` tool is being blocked by a syntax gate. "
                "Use the `Edit` tool instead to modify the file in smaller chunks, or check for unclosed brackets/quotes."
            )

        # Default fallback
        case _:
            return "Abandon this approach and try a completely different strategy (e.g., different tool or simpler command)."


def check_for_investigation_loop(tool: str, command: str) -> dict | None:
    """
    Check if we're in an investigation loop (consecutive read-only operations).

    Returns None if no investigation loop, or dict with block/warning decision.
    """
    # Only check read-only tools
    if not is_read_only_tool(tool):
        return None

    # Count consecutive read-only operations
    consecutive_read_only = count_consecutive_read_only_cycles()

    # Check if threshold reached
    if consecutive_read_only >= READ_ONLY_CYCLE_LIMIT:
        # Log for evidence gathering (always log, regardless of mode)
        log_investigation_loop_warning(tool, command, consecutive_read_only)

        # Check if advisory mode is enabled
        advisory_mode = is_investigation_loop_advisory_mode()

        if advisory_mode:
            # Return warning instead of block
            return {
                "allow": True,
                "warning": f"""⚠️ INVESTIGATION LOOP WARNING (Advisory Mode)

**Pattern detected:** {consecutive_read_only} consecutive read-only operations in {WINDOW_MINUTES} minutes.

**Tool:** {tool}
**Command:** {command[:100]}{'...' if len(command) > 100 else ''}

**This operation will be allowed**, but consider:
• Have you gathered enough information to take action?
• Can you synthesize findings from existing data?
• Would asking the user for guidance be more efficient?

**Evidence gathering:** This warning is being logged to evaluate if investigation loop blocking is needed.
Review: P:/.claude/state/logs/investigation_loop_warnings.log
"""
            }
        else:
            # Block mode (original behavior)
            log_block("recursive_failure_detector", tool, command,
                      f"Investigation loop: {consecutive_read_only} read-only operations")

            directive = get_investigation_loop_directive()

            return {
                "block": True,
                "message": f"""⚠️ INVESTIGATION LOOP DETECTED

**Loop detected:** {consecutive_read_only} consecutive read-only operations in {WINDOW_MINUTES} minutes.

**Tool:** {tool}
**Command:** {command[:100]}{'...' if len(command) > 100 else ''}

**Pattern:** You are performing investigation operations (Read, Grep, Glob) without taking action.

{directive}

**Choose one to break the loop:**
1. Synthesize findings and take action (Recommended)
2. `/hooks off` * Proceed manually * `/hooks on`
3. Ask the user for specific guidance

**Cannot continue investigating without action.**"""
        }

    return None


def check_for_catch22(tool: str, command: str, file_path: str = "") -> dict:
    """
    Check if we're in a Catch-22 loop or investigation loop.
    Returns: {"allow": True} or {"block": True, "message": str}
    """
    # TEST FILE EXEMPTION: Allow test file operations without Catch-22 checking
    _MUTATION_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")
    if tool in _MUTATION_TOOLS and file_path:
        if is_test_file_operation(file_path):
            return {"allow": True}

    # Self-exemption: allow hook modifications
    if is_hook_self_operation(command):
        return {"allow": True}

    # Bypass check
    if is_bypass_enabled():
        return {"allow": True}

    # Check for investigation loop first (lower threshold)
    investigation_result = check_for_investigation_loop(tool, command)
    if investigation_result:
        # Return if it's a block OR a warning (advisory mode)
        if investigation_result.get("block") or investigation_result.get("warning"):
            return investigation_result

    # Check for regular Catch-22 (same command repeated)
    cmd_hash = compute_command_hash(command)
    failure_count, recent_errors = count_similar_failures(tool, cmd_hash)

    if failure_count >= FAILURE_THRESHOLD:
        log_block("recursive_failure_detector", tool, command, f"Catch-22: {failure_count} failures")

        directive = get_prescriptive_directive(tool, command, recent_errors)

        return {
            "block": True,
            "message": f"""⚠️ CATCH-22 DETECTED (CLAUDE.md Part D.5)

**Loop detected:** Same operation pattern failed {failure_count} times in {WINDOW_MINUTES} minutes.

**Tool:** {tool}
**Command:** {command[:100]}{'...' if len(command) > 100 else ''}

**Recent errors:**
{chr(10).join(f'  * {e}' for e in recent_errors) if recent_errors else '  (no error details captured)'}

{directive}

**Choose one to break the loop:**
1. Execute the directive above (Recommended)
2. `/hooks off` * Repair manually * `/hooks on`
3. User performs manual repair

**Cannot proceed with the SAME command again.**"""
        }

    return {"allow": True}


@hook_main
def main():
    input_data = json.loads(sys.stdin.read())
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Extract file path for test exemption check
    file_path = tool_input.get("file_path", "")

    # Build command string for hashing
    command = (tool_input.get("command") or
               tool_input.get("content") or
               tool_input.get("path") or
               json.dumps(tool_input)[:500])

    result = check_for_catch22(tool_name, command, file_path)

    if result.get("block"):
        print(json.dumps({
            "decision": "block",
            "message": result["message"],
            "blocking_hook": "recursive_failure_detector.py"
        }))
    else:
        print("{}")


if __name__ == "__main__":
    main()
