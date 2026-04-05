#!/usr/bin/env python3
"""Transparent diagnostic wrapper for hook commands.

Runs the real hook command, captures stdout/stderr/exit code,
logs everything to a diagnostic file, then passes output through
unchanged. Claude Code sees identical behavior.

Usage in settings.json:
    "command": "python P:/.claude/hooks/__lib/hook_diagnostic_wrapper.py python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/UserPromptSubmit.py --timeout 15.0"
"""

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

DIAG_LOG = Path(__file__).resolve().parent.parent / "logs" / "diagnostics" / "hook_wrapper_diag.jsonl"


def main():
    # Everything after this script's name is the real command
    real_cmd = sys.argv[1:]
    if not real_cmd:
        print("{}")
        sys.exit(0)

    # Read stdin to pass through
    stdin_data = sys.stdin.read()

    # Run the real command
    try:
        proc = subprocess.run(
            real_cmd,
            input=stdin_data,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "cmd": " ".join(real_cmd[:3]),
            "event": "TIMEOUT",
            "stdin_len": len(stdin_data),
        }
        DIAG_LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(DIAG_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        print("{}")
        sys.exit(1)

    # Log diagnostics
    entry = {
        "ts": datetime.now(UTC).isoformat(),
        "cmd": " ".join(real_cmd[:3]),
        "exit_code": proc.returncode,
        "stdout_len": len(proc.stdout),
        "stderr_len": len(proc.stderr),
        "stderr": proc.stderr[:2000] if proc.stderr else "",
        "stdout_valid_json": False,
        "stdin_len": len(stdin_data),
    }

    # Check if stdout is valid JSON
    try:
        json.loads(proc.stdout)
        entry["stdout_valid_json"] = True
    except (json.JSONDecodeError, ValueError):
        entry["stdout_valid_json"] = False
        entry["stdout_prefix"] = repr(proc.stdout[:500])

    # Only log if something looks wrong (or always for first 50 invocations to establish baseline)
    always_log = True  # Set to False after debugging
    is_error = proc.returncode != 0 or proc.stderr or not entry["stdout_valid_json"]

    if always_log or is_error:
        try:
            DIAG_LOG.parent.mkdir(parents=True, exist_ok=True)
            with open(DIAG_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass

    # Pass through exactly what the real command produced
    if proc.stdout:
        sys.stdout.write(proc.stdout)
        sys.stdout.flush()
    if proc.stderr:
        sys.stderr.write(proc.stderr)
        sys.stderr.flush()

    sys.exit(proc.returncode)


if __name__ == "__main__":
    main()


# =============================================================================
# Routing Functions for Smart Stderr Handling
# =============================================================================


def extract_hook_type_from_cmd_args(real_cmd: list) -> str | None:
    """Extract hook type from command arguments.

    Handles patterns like:
    - PreToolUse_file_existence_guard.py -> PreToolUse
    - PostToolUse_artifact_validator.py -> PostToolUse
    - StopHook_reality_check.py -> Stop
    - UserPromptSubmit_router.py -> UserPromptSubmit
    - posttooluse/integration_verifier.py -> PostToolUse (nested paths)

    Args:
        real_cmd: Command argument list from sys.argv

    Returns:
        Hook type string (e.g., "PreToolUse") or None for unknown formats
    """
    if not real_cmd:
        return None

    # Find the hook script path in command args
    # Skip common utility files like hook_runner.py
    skip_files = {"hook_runner.py", "hook_diagnostic_wrapper.py"}

    hook_path = None
    for arg in real_cmd:
        # Look for .py files that aren't utility files
        if isinstance(arg, str) and arg.endswith('.py'):
            path_obj = Path(arg)
            if path_obj.name not in skip_files:
                hook_path = arg
                break

    if not hook_path:
        return None

    # Convert to Path for easier handling
    path_obj = Path(hook_path)

    # Try extracting from filename first (e.g., PreToolUse_*.py)
    filename = path_obj.name
    for prefix in ["PreToolUse", "PostToolUse", "StopHook", "UserPromptSubmit"]:
        if filename.startswith(prefix):
            if prefix == "StopHook":
                return "Stop"
            return prefix

    # Try extracting from directory path (e.g., posttooluse/*.py)
    dirname = path_obj.parent.name.lower()
    dir_to_type = {
        "pretooluse": "PreToolUse",
        "posttooluse": "PostToolUse",
        "userpromptsubmit": "UserPromptSubmit",
        "stop": "Stop",
    }

    return dir_to_type.get(dirname)


def should_log_to_file_stderr(hook_type: str, stderr_content: str) -> bool:
    """Determine if stderr should be logged to file based on hook type.

    Routing logic:
    - Blocking hooks (PreToolUse, Stop) -> False (pass through)
    - Advisory hooks (PostToolUse, UserPromptSubmit) -> True (log to file)
    - Unknown/empty hook types -> False (fallback to pass-through)

    Args:
        hook_type: Hook type string (e.g., "PreToolUse", "PostToolUse")
        stderr_content: Stderr content (not used for routing decision but kept for interface)

    Returns:
        True if stderr should log to file, False if it should pass through
    """
    if not hook_type:
        return False

    # Advisory hooks log to file
    advisory_hooks = {"PostToolUse", "UserPromptSubmit"}
    if hook_type in advisory_hooks:
        return True

    # Blocking hooks (and unknown types) pass through
    return False


def log_to_hook_stderr_file(hook_type: str, stderr_content: str, log_dir: Path | None = None) -> Path:
    """Write stderr content to log file with metadata.

    Creates log file with timestamp, hook type, and stderr content.
    Appends to existing log file if it exists.

    Args:
        hook_type: Type of hook generating the stderr
        stderr_content: The stderr content to log
        log_dir: Directory for log file (default: P:/.claude/hooks/logs/diagnostics)

    Returns:
        Path to the log file
    """
    if log_dir is None:
        log_dir = Path(__file__).resolve().parent.parent / "logs" / "diagnostics"

    log_file = log_dir / "hook_stderr.log"

    # Create directory if needed
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log entry with timestamp
    timestamp = datetime.now(UTC).isoformat()
    log_entry = f"[{timestamp}] Hook: {hook_type}\n{stderr_content}\n{'-' * 80}\n"

    # Append to log file
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)

    return log_file
