#!/usr/bin/env python3
"""
SessionStart - Lean Router v2.0
===============================

Replaces monolithic SessionStart_router.py.
Orchestrates cold-start setup tasks: daemons, state restore, and cleanup.

v2.1: Added timing observability for sub-hook profiling (2026-03-17)
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

# Try to import diagnostics logger for timing logs
try:
    from cc_diagnostic_logger import log_hook_invocation

    DIAGNOSTICS_AVAILABLE = True
except ImportError:
    DIAGNOSTICS_AVAILABLE = False
    log_hook_invocation = None

# setup sequence (Priority-ordered)
SETUP_SEQUENCE = [
    # 1. Identity & Environment
    "SessionStart_terminal_id.py",
    # "SessionStart_folder_context.py",  # DISABLED: Missing features.lib_folder_context module
    # 2. Health Check (cleanup now handled by session_data_retention inline)
    # "SessionStart_hook_health_check.py",  # DISABLED: 319ms avg, never caught a failure in 17 runs
    # 3. Log Rotation (throttled to once per day)
    "SessionStart_log_rotation.py",
    # 4. State Restore (Session Continuity)
    "SessionStart_handoff_restore.py",
    # 4. Memory & Daemons (Long-term context)
    "SessionStart_semantic_daemon.py",  # Semantic search daemon (named pipe server)
    "SessionStart_dreaming_daemon.py",  # Insight/reflection daemon
    # "SessionStart_search_daemon.py",  # DISABLED: spawns dreaming daemon --daemon-type search (identical to dreaming daemon, no differentiation)
    # Memory auto-ingestion (after daemons, uses CKS)
    "SessionStart_memory_cks_auto.py",  # Auto-ingest memory files when changed
    # 5. Cognitive Framing
    # "SessionStart_task_identity.py",  # DISABLED: 153ms avg, output not consumed by PreCompact
    "SessionStart_timeline.py",
    "SessionStart_constraint_display.py",
    # 6. Commitment Tracking (uncompleted commitments on compaction resume) (uncompleted commitments on compaction resume)
    "SessionStart_commitment_tracker.py",
]


def _extract_contexts(stdout_text: str) -> list[str]:
    """Extract additionalContext/systemMessage payloads from hook stdout.

    Non-JSON lines are passed through as visible context (e.g., TLDR plain text output).
    """
    contexts: list[str] = []
    for line in stdout_text.splitlines():
        payload = line.strip()
        if not payload:
            continue
        # Non-JSON lines = visible text output (e.g., TLDR summary)
        if not payload.startswith("{"):
            contexts.append(payload)
            continue
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            # Malformed JSON — treat as visible text
            contexts.append(payload)
            continue
        if not isinstance(obj, dict):
            continue

        hook_output = obj.get("hookSpecificOutput")
        if isinstance(hook_output, dict):
            ctx = hook_output.get("additionalContext")
            if isinstance(ctx, str) and ctx.strip():
                contexts.append(ctx.strip())

        direct_ctx = obj.get("additionalContext")
        if isinstance(direct_ctx, str) and direct_ctx.strip():
            contexts.append(direct_ctx.strip())

        system_msg = obj.get("systemMessage")
        if isinstance(system_msg, str) and system_msg.strip():
            contexts.append(system_msg.strip())
    return contexts


def run_setup_task(hook_name: str, input_data: str) -> tuple[list[str], float]:
    """Run a setup task and return contexts + duration_ms.

    Returns:
        Tuple of (extracted_contexts, duration_ms)
    """
    start_time = time.perf_counter()
    try:
        hook_path = HOOKS_DIR / hook_name
        if not hook_path.exists():
            return [], 0.0

        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=input_data.encode(),
            capture_output=True,
            timeout=15.0,  # Setup tasks can be slower
            creationflags=creation_flags,
        )
        stdout_text = result.stdout.decode(errors="replace")
        stderr_text = result.stderr.decode(errors="replace").strip()

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log timing to diagnostics for slow hooks (>100ms)
        if duration_ms > 100 and DIAGNOSTICS_AVAILABLE and log_hook_invocation:
            try:
                log_hook_invocation(
                    hook_name=f"SessionStart.{hook_name}",
                    event_type="SessionStart",
                    action="pass" if result.returncode == 0 else "warn",
                    reason=f"Sub-hook completed in {duration_ms:.0f}ms",
                    duration_ms=duration_ms,
                )
            except Exception:
                pass  # Diagnostics failures must not break session start

        if result.returncode != 0:
            # NOTE: stderr output suppressed - any stderr is treated as "hook error" by Claude Code
            # Setup task failures are logged but don't block session start
            pass
        return _extract_contexts(stdout_text), duration_ms
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000
        # NOTE: stderr output suppressed - any stderr is treated as "hook error" by Claude Code
        # Errors are logged but don't block session start
        return [], duration_ms


def main():
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        sys.exit(0)

    try:
        raw_input = raw_input.lstrip("\ufeff")
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    # SessionStart semantics: run once when a Claude Code session initializes.
    # Remove orphan edit-consent tokens scoped to this session id only.
    try:
        sys.path.insert(0, str(HOOKS_DIR / "__lib"))
        import pre_tool_use_logic

        session_id = pre_tool_use_logic.resolve_session_id(data)
        terminal_id = pre_tool_use_logic.resolve_terminal_id(data)
        major_task_id = pre_tool_use_logic.resolve_major_task_id(data, terminal_id=terminal_id)
        if session_id:
            pre_tool_use_logic.cleanup_session_edit_consent_tokens(
                session_id,
                terminal_id=terminal_id,
                major_task_id=major_task_id,
            )
    except Exception:
        pass

    # Housekeeping: prune stale locks and old logs before setup
    try:
        from session_data_retention import cleanup as _retention_cleanup

        _retention_cleanup()
    except Exception:
        pass

    contexts: list[str] = []
    total_start = time.perf_counter()
    task_timings: dict[str, float] = {}

    # Execute setup tasks in sequence
    for task in SETUP_SEQUENCE:
        task_contexts, duration_ms = run_setup_task(task, json.dumps(data))
        contexts.extend(task_contexts)
        task_timings[task] = duration_ms

    total_duration_ms = (time.perf_counter() - total_start) * 1000

    # Log total SessionStart duration to diagnostics
    if DIAGNOSTICS_AVAILABLE and log_hook_invocation:
        try:
            # Find slowest sub-hooks for diagnostic context
            slow_hooks = sorted(task_timings.items(), key=lambda x: x[1], reverse=True)[:3]
            slow_summary = ", ".join(f"{k}:{v:.0f}ms" for k, v in slow_hooks if v > 0)

            log_hook_invocation(
                hook_name="SessionStart",
                event_type="SessionStart",
                action="pass",
                reason=f"Total duration: {total_duration_ms:.0f}ms. Slowest: {slow_summary}"
                if slow_summary
                else f"Total duration: {total_duration_ms:.0f}ms",
                duration_ms=total_duration_ms,
            )
        except Exception:
            pass  # Diagnostics failures must not break session start

    if contexts:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": "\n\n".join(contexts),
                    }
                }
            )
        )
    else:
        print("{}")

    sys.exit(0)


def process_start(event_data: dict) -> dict:
    """In-process entry point for router integration.

    Args:
        event_data: Hook event data (session_id, terminal_id, etc.)

    Returns:
        Hook result dict with output from main()
    """
    import io

    # Prepare event_data as JSON input for main()
    json_input = json.dumps(event_data)

    # Save original stdin
    old_stdin = sys.stdin

    try:
        # Replace stdin with event data
        sys.stdin = io.StringIO(json_input)

        # Call main() which reads from stdin
        main()

        # main() prints output to stdout - we could capture it here if needed
        # For now, main() handles its own output
        return {"ok": True}

    except SystemExit as e:
        # main() called sys.exit() - capture exit code
        return {"ok": e.code == 0, "exit_code": e.code}

    except Exception as e:
        return {"ok": False, "error": str(e)}

    finally:
        # Restore stdin
        sys.stdin = old_stdin


if __name__ == "__main__":
    main()
