#!/usr/bin/env python3
"""Module-level hook runner that catches ALL errors including imports.

This module provides a universal hook runner that catches errors at every level:
- Import errors (ModuleNotFoundError, ImportError)
- Syntax errors (SyntaxError)
- Runtime errors (any Exception)

Usage from settings.json:
    "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/MyHook.py"

Or call programmatically:
    from __lib.hook_runner import safe_run
    exit_code = safe_run("path/to/hook.py")
"""

from __future__ import annotations

import os

# Prevent the hook subprocess from creating .pyc bytecode files.
# Hooks are loaded via HookImporter (in-process) which handles pyc clearing proactively.
# The subprocess runner is protected here to prevent it from creating stale pyc
# that could outlive the parent process.
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

# Monkey-patch subprocess to prevent blue console flashes on Windows.
# Uses a proper subclass so asyncio.windows_utils can still subclass Popen.
import subprocess as _subprocess


class _NoWindowPopen(_subprocess.Popen):
    def __init__(self, *args, **kwargs):
        if "creationflags" not in kwargs:
            kwargs["creationflags"] = _subprocess.CREATE_NO_WINDOW
        super().__init__(*args, **kwargs)


_subprocess.Popen = _NoWindowPopen

import argparse
import contextlib
import io
import json
import runpy
import sys
import threading
import traceback
from datetime import UTC, datetime
from pathlib import Path

try:
    from pretooluse_observability import extract_runner_input_metadata
except ImportError:
    from __lib.pretooluse_observability import extract_runner_input_metadata

# Paths for logging
HOOKS_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = HOOKS_DIR / "logs" / "diagnostics"
ERRORS_LOG = LOGS_DIR / "cc_errors.jsonl"
FAILSAFE_LOG = LOGS_DIR / "failsafe_errors.log"  # Plain text fallback
STARTUP_PROBE_LOG = LOGS_DIR / "startup_probe.log"  # Trace invocations

# IMMEDIATE STARTUP PROBE - logs before ANY code runs
# This helps debug "silent" errors where Python fails to start
try:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    import time as _probe_time
    _probe_start = _probe_time.perf_counter()
    with open(STARTUP_PROBE_LOG, "a", encoding="utf-8") as _f:
        _ts = datetime.now(UTC).isoformat()
        _args = " ".join(sys.argv[1:3]) if len(sys.argv) > 1 else "(no args)"
        _f.write(f"[{_ts}] STARTED: {_args}\n")
except Exception:
    pass  # Never fail on probe


def _failsafe_log(message: str) -> None:
    """Absolute last-resort logging to plain text file.

    This bypasses all complex logging infrastructure. Use when:
    - JSON logger fails to initialize
    - Exception occurs before imports complete
    - Any other catastrophic failure scenario
    """
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(FAILSAFE_LOG, "a", encoding="utf-8") as f:
            ts = datetime.now(UTC).isoformat()
            f.write(f"[{ts}] {message}\n")
    except Exception:
        # Truly last resort - stderr
        _safe_stderr_print(f"[HOOK_RUNNER_FAILSAFE] {message}")


def _error_class_and_code(
    hook_name: str, error_type: str, error_msg: str, tb: str,
) -> tuple[str, str, bool, str]:
    """Derive structured classification fields from error type + traceback.

    Maps error_type -> (error_class, failure_code, is_startup_actionable, root_cause_key).

    Mapping rules (A3):
      timeout_imminent/killed/terminated/exceeded -> ("timeout", code, False, key)
        Rationale: operational noise; timeout means hook ran but took too long — not a bug.
      syntax_error/parse_error -> ("load_failure", code, False, key)
        Rationale: known fixed; syntax errors from previous edits are not current failures.
      import_error/module_not_found -> ("load_failure", code, True, key)
        Rationale: actionable; missing dependencies are real problems requiring user action.
      runtime_error with known traceback patterns (name 'anomalies', name 'user_prompt',
        AttributeError.*unknown, AttributeError.*audit_report) -> ("known_fixed", code, False, key)
        Rationale: known fixed; these are refactoring artifacts already addressed.
      runtime_error generic -> ("runtime_error", code, True, key)
        Rationale: actionable; genuine unexpected errors need investigation.
      unknown error_type -> ("runtime_error", code, True, key)
        Rationale: fail-open; unclassified errors default to actionable to avoid silencing real bugs.

    The four output fields feed the startup health classifier (A4):
      error_class: coarse bucket for routing in Layer 1 of _classify_error_events.
      failure_code: stable identifier; used as root_cause_key for telemetry grouping.
      is_startup_actionable: True = real failure to count; False = suppress from alert.
      root_cause_key: stable key for grouping; mirrors failure_code.
    """
    failure_code = f"{hook_name}_{error_type}"
    root_cause_key = failure_code  # stable identifier

    # Map error_type -> error_class + startup_actionable
    if error_type in ("timeout_imminent", "timeout_killed", "timeout_terminated", "timeout_exceeded"):
        return "timeout", failure_code, False, root_cause_key
    if error_type in ("syntax_error", "parse_error"):
        return "load_failure", failure_code, False, root_cause_key  # known fixed
    if error_type in ("import_error", "module_not_found"):
        return "load_failure", failure_code, True, root_cause_key  # actionable
    if error_type == "runtime_error":
        # Inspect traceback for known-fixed patterns
        msg_lower = error_msg.lower()
        tb_lower = (tb or "").lower()
        combined = f"{msg_lower}|{tb_lower}"
        if any(k in combined for k in ("name 'anomalies'", "name 'user_prompt'",
                                        "attributeerror.*unknown", "attributeerror.*audit_report")):
            return "known_fixed", failure_code, False, root_cause_key
        return "runtime_error", failure_code, True, root_cause_key
    # default
    return "runtime_error", failure_code, True, root_cause_key


def _log_error(hook_name: str, error_type: str, error_msg: str, tb: str) -> None:
    """Log error to cc_errors.jsonl, creating dirs if needed."""
    try:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        error_class, failure_code, is_startup_actionable, root_cause_key = (
            _error_class_and_code(hook_name, error_type, error_msg, tb)
        )

        entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "session_id": None,
            "event": "error",
            "error_type": f"{hook_name}_{error_type}",
            "error_message": error_msg,
            "stack_trace": tb,
            # Structured classification (A3)
            "error_class": error_class,
            "failure_code": failure_code,
            "is_startup_actionable": is_startup_actionable,
            "root_cause_key": root_cause_key,
            "context": {
                "hook": hook_name,
                "error_category": error_type,
                "runner": "hook_runner",
            },
        }

        from file_lock import append_jsonl_safe
        append_jsonl_safe(ERRORS_LOG, entry)
    except OSError:
        # Last resort - print to stderr
        _safe_stderr_print(f"[HOOK_RUNNER] Failed to log error: {error_msg}")


def _output_error(error_msg: str, hook_name: str = "", error_type: str = "", tb: str = "") -> None:
    """Output JSON error to stdout (for Claude Code) with structured interrupts."""
    error_class, failure_code, is_startup_actionable, root_cause_key = (
        _error_class_and_code(hook_name or "unknown", error_type or "unknown", error_msg, tb)
    )

    # Prescriptive strategy shifts for structured interrupts
    remediation = "Abandon this approach and try a completely different strategy. Do NOT retry the same action."
    msg_lower = error_msg.lower()
    type_lower = (error_type or "").lower()

    if "import" in msg_lower or "module_not_found" in type_lower:
        remediation = (
            "**Prescriptive Directive (Import Error):** Required module or package is missing or not importable.\n"
            "1. Verify that P:/.claude/hooks/__lib/ is in sys.path and the module file exists.\n"
            "2. Perform Symmetry Analysis: verify if the target package was correctly refactored or colocated.\n"
            "3. Do NOT retry without fixing the import paths."
        )
    elif "syntax" in msg_lower or "syntax_error" in type_lower:
        remediation = (
            "**Prescriptive Directive (Syntax Error):** The hook script has invalid Python syntax.\n"
            "1. Run `python -m py_compile <path>` on the file directly to find the syntax error.\n"
            "2. Repair the syntax error (e.g., unmatched brackets, quotes, or trailing characters).\n"
            "3. Do NOT execute or retry until `py_compile` succeeds."
        )
    elif "timeout" in type_lower:
        remediation = (
            "**Prescriptive Directive (Timeout Error):** Hook execution exceeded its timeout budget.\n"
            "1. Check for infinite loops, blocking subprocesses, or slow file I/O operations.\n"
            "2. Optimize the hook's execution paths, database locks, or query parameters.\n"
            "3. Ensure the operation completes under 3 seconds to avoid blocking the developer workflow."
        )

    interrupt_payload = {
        "ok": False,
        "error": error_msg,
        "interrupt": {
            "type": "HOOK_INTERRUPT",
            "hook": hook_name or "unknown",
            "error_class": error_class,
            "failure_code": failure_code,
            "remediation": remediation,
            "is_actionable": is_startup_actionable
        }
    }
    print(json.dumps(interrupt_payload))



def _safe_stderr_print(message: str) -> None:
    """Safely print to stderr, handling encoding errors on Windows.

    On Windows, printing to stderr can fail with OSError: [Errno 22] Invalid argument
    when the message contains characters not representable in the console encoding.
    This function handles that gracefully by:
    1. Trying to print normally
    2. On OSError, trying with ascii encoding and error replacement
    3. If that fails, silently skip the output (log file already has it)
    """
    try:
        print(message, file=sys.stderr, flush=True)
    except (OSError, UnicodeError):
        try:
            # Try with ascii encoding and backslashreplace for problematic chars
            safe_msg = message.encode("ascii", errors="backslashreplace").decode("ascii")
            print(safe_msg, file=sys.stderr, flush=True)
        except (OSError, UnicodeError):
            # stderr is broken or unavailable - log file has the error, so skip
            pass


def _is_stop_hook(hook_name: str) -> bool:
    """Best-effort classification for Stop hooks."""
    return "stop" in hook_name.lower()


def _normalize_stop_protocol(
    hook_name: str, exit_code: int, stdout_text: str, stderr_text: str
) -> tuple[int, str, str]:
    """Normalize malformed Stop hook outputs so they are not silently allowed."""
    if not _is_stop_hook(hook_name):
        return exit_code, stdout_text, stderr_text

    parsed: dict | None = None
    payload = stdout_text.strip()
    if payload:
        try:
            obj = json.loads(payload)
            if isinstance(obj, dict):
                parsed = obj
        except json.JSONDecodeError:
            parsed = None

    # Non-compliant: hook emitted block decision JSON but used exit code 1.
    if exit_code == 1 and parsed and parsed.get("decision") == "block":
        stderr_text = (
            f"{stderr_text}\n[HOOK_RUNNER] Normalized Stop protocol: exit 1 -> exit 2 "
            f"for block decision in {hook_name}"
        ).strip()
        return 2, stdout_text, stderr_text

    # hookSpecificOutput.additionalContext is the modern channel for delivering
    # Stop feedback to the MODEL ONLY (not surfaced to the user). The current
    # Claude Code CLI honors it; an earlier build of this runner wrongly rejected
    # it as "legacy" and forced the user-visible decision/reason path. Pass it
    # through. Block-decision exit semantics are already enforced above
    # (exit 1 + decision==block -> exit 2), so a block here is never silently
    # downgraded to allow.
    if parsed and "hookSpecificOutput" in parsed:
        return exit_code, stdout_text, stderr_text

    # Non-compliant: "decision": "allow" not in schema -- normalize to "approve".
    if parsed and parsed.get("decision") == "allow":
        normalized = {"decision": "approve"}
        for k, v in parsed.items():
            if k != "decision":
                normalized[k] = v
        return exit_code, json.dumps(normalized), stderr_text

    return exit_code, stdout_text, stderr_text


def _timeout_monitor(hook_name: str, duration: float) -> None:
    """Log warning that timeout is imminent.

    NOTE: Stderr warning intentionally removed - Claude Code treats any stderr
    as "hook error" even for warnings. The log entry to cc_errors.jsonl is
    sufficient for debugging slow hooks.
    """
    error_msg = f"Hook execution exceeded {duration:.1f}s - timeout imminent"
    _log_error(hook_name, "timeout_imminent", error_msg, "")
    # NO stderr output - any stderr triggers "hook error" from Claude Code


def _clear_shadowed_hook_packages() -> None:
    """Remove unrelated __lib modules that were imported before path fixups.

    When the runner starts from a broad workspace cwd, Python can resolve a
    different top-level ``__lib`` package before we prioritize the target
    hook paths. Once cached in ``sys.modules``, later imports reuse that wrong
    package even after ``sys.path`` is corrected.
    """
    hooks_root = HOOKS_DIR.resolve()
    for module_name in list(sys.modules):
        if module_name != "__lib" and not module_name.startswith("__lib."):
            continue
        module = sys.modules.get(module_name)
        module_file = getattr(module, "__file__", None)
        if not module_file:
            continue
        try:
            resolved = Path(module_file).resolve()
        except OSError:
            continue
        if hooks_root not in resolved.parents and resolved != hooks_root:
            del sys.modules[module_name]


def safe_run(hook_path: str | Path, timeout: float | None = None) -> int:
    """Safely run a hook, catching ALL errors including imports.

    Uses runpy.run_path to execute the hook as __main__, ensuring that
    `if __name__ == "__main__":` blocks are properly executed.

    Args:
        hook_path: Path to the hook Python file
        timeout: Optional timeout in seconds to warn before

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    hook_path = Path(hook_path).resolve()
    hook_name = hook_path.stem

    # Verify hook exists
    if not hook_path.exists():
        error_msg = f"Hook file not found: {hook_path}"
        _log_error(hook_name, "file_not_found", error_msg, "")
        _output_error(error_msg)
        _safe_stderr_print(f"[HOOK_RUNNER] {error_msg}")
        return 1

    # Setup timeout monitor if configured
    timer = None
    if timeout and timeout > 0.5:
        # Warn 0.5s before the hard kill
        warn_time = timeout - 0.5
        timer = threading.Timer(warn_time, _timeout_monitor, args=(hook_name, warn_time))
        timer.daemon = True  # Ensure it doesn't keep process alive
        timer.start()

    # Save original sys.argv, sys.path, and stdin
    original_argv = sys.argv.copy()
    original_path = sys.path.copy()
    original_stdin = sys.stdin

    # Resolve hook_path to absolute path to handle relative paths from any directory
    hook_path = hook_path.resolve()

    input_metadata: dict[str, str] = {}

    # Pre-validate JSON from stdin to protect hooks from malformed input
    # This catches issues like unescaped backslashes in Windows paths
    try:
        stdin_content = sys.stdin.read()
        if stdin_content.strip():
            try:
                # Validate JSON is parseable
                json.loads(stdin_content)
            except json.JSONDecodeError:
                # Invalid JSON - pass empty object to hook instead of crashing
                stdin_content = "{}"
        input_metadata = extract_runner_input_metadata(stdin_content)
        # Replace stdin with validated content
        sys.stdin = io.StringIO(stdin_content)
    except Exception:
        # If stdin read fails, provide empty object
        sys.stdin = io.StringIO("{}")

    try:
        # Force target hook paths to the front of sys.path.
        # This prevents unrelated workspace packages (for example P:\__csf\__lib)
        # from shadowing the hook-local __lib package when the runner is launched
        # from a broader workspace cwd.
        hook_dir = str(hook_path.parent)
        hooks_root = str(HOOKS_DIR)
        prioritized_paths: list[str] = []
        for path in (hook_dir, hooks_root):
            if path not in prioritized_paths:
                prioritized_paths.append(path)
        sys.path = prioritized_paths + [p for p in sys.path if p not in prioritized_paths]
        _clear_shadowed_hook_packages()

        # Prepare sys.argv to mimic direct script execution
        # The target hook should see itself as argv[0], with remaining args
        sys.argv = [str(hook_path)] + original_argv[2:]  # Skip hook_runner.py and hook_path

        # Capture script output so Stop hook protocol can be normalized.
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        exit_code = 0
        with contextlib.redirect_stdout(captured_stdout), contextlib.redirect_stderr(
            captured_stderr
        ):
            try:
                # Execute the hook as __main__ using runpy
                # This properly executes `if __name__ == "__main__":` blocks
                runpy.run_path(str(hook_path), run_name="__main__")
            except SystemExit as e:
                exit_code = e.code if isinstance(e.code, int) else (1 if e.code else 0)

        # END marker for startup_probe.log: a START-without-END is itself a
        # hang/timeout signal. Best-effort; never fail the hook.
        try:
            import time as _t
            _dur_ms = int((_t.perf_counter() - _probe_start) * 1000)
            with open(STARTUP_PROBE_LOG, "a", encoding="utf-8") as _ef:
                _ef.write(
                    f"[{datetime.now(UTC).isoformat()}] END: {_args} RC={exit_code} dur={_dur_ms}ms\n"
                )
        except Exception:
            pass

        stdout_text = captured_stdout.getvalue()
        stderr_text = captured_stderr.getvalue()
        exit_code, stdout_text, stderr_text = _normalize_stop_protocol(
            hook_name, exit_code, stdout_text, stderr_text
        )

        if stdout_text:
            print(stdout_text, end="")

        # Stderr handling: Log and re-emit
        # Claude Code treats ANY stderr as "hook error"
        if stderr_text:
            # DIAGNOSTIC: Log what is causing the "hook error"
            try:
                diag_path = HOOKS_DIR / "logs" / "diagnostics" / "hook_runner_stderr.jsonl"
                diag_path.parent.mkdir(parents=True, exist_ok=True)
                diag_entry = {
                    "ts": datetime.now(UTC).isoformat(),
                    "hook": hook_name,
                    "hook_path": str(hook_path),
                    "session_id": input_metadata.get("session_id", ""),
                    "terminal_id": input_metadata.get("terminal_id", ""),
                    "prompt_id": input_metadata.get("prompt_id", ""),
                    "tool_name": input_metadata.get("tool_name", ""),
                    "cwd": input_metadata.get("cwd", ""),
                    "command_preview": input_metadata.get("command", ""),
                    "file_path": input_metadata.get("file_path", ""),
                    "event_kind": "blocked" if exit_code == 2 else "stderr",
                    "stderr_len": len(stderr_text),
                    "stderr": stderr_text[:2000],
                    "exit_code": exit_code,
                }
                from file_lock import append_jsonl_safe
                append_jsonl_safe(diag_path, diag_entry)
            except OSError:
                pass
            # DO NOT re-emit stderr — Claude Code treats ANY stderr as "hook error".
            # The diagnostic log above is sufficient for debugging.
        return exit_code

    except SyntaxError as e:
        error_msg = f"Syntax error in {hook_name}: {e}"
        tb = traceback.format_exc()
        _log_error(hook_name, "syntax_error", error_msg, tb)
        _output_error(error_msg, hook_name, "syntax_error", tb)
        _safe_stderr_print(f"[HOOK_RUNNER] {error_msg}")
        return 1

    except (ImportError, ModuleNotFoundError) as e:
        error_msg = f"Import error in {hook_name}: {e}"
        tb = traceback.format_exc()
        _log_error(hook_name, "import_error", error_msg, tb)
        _output_error(error_msg, hook_name, "import_error", tb)
        _safe_stderr_print(f"[HOOK_RUNNER] {error_msg}")
        return 1

    except Exception as e:
        error_msg = f"Runtime error in {hook_name}: {type(e).__name__}: {e}"
        tb = traceback.format_exc()
        _log_error(hook_name, "runtime_error", error_msg, tb)
        _output_error(error_msg, hook_name, "runtime_error", tb)
        _safe_stderr_print(f"[HOOK_RUNNER] {error_msg}")
        return 1

    finally:
        # Restore original sys.argv, sys.path, and stdin
        sys.argv = original_argv
        sys.path = original_path
        sys.stdin = original_stdin
        # Cancel timeout warning if we finished in time
        if timer:
            timer.cancel()


def main() -> None:
    """CLI entry point: python hook_runner.py <hook_path> [--timeout N]"""
    parser = argparse.ArgumentParser(description="Universal Hook Runner")
    parser.add_argument("hook_path", help="Path to the hook Python file")
    parser.add_argument("--timeout", type=float, help="Timeout in seconds for warning")

    args = parser.parse_args()

    exit_code = safe_run(args.hook_path, args.timeout)
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Absolute last-ditch catch - something failed at the outermost level
        tb = traceback.format_exc()
        msg = f"CATASTROPHIC: hook_runner crashed: {type(e).__name__}: {e}\n{tb}"
        _failsafe_log(msg)
        _safe_stderr_print(f"[HOOK_RUNNER] {msg}")
        sys.exit(1)
