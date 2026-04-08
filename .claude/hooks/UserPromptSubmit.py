#!/usr/bin/env python3
"""
UserPromptSubmit - Lean Router v2.0
==================================

Replaces monolithic UserPromptSubmit_router.py with a decoupled dispatcher.
Utilizes modules in .claude/hooks/UserPromptSubmit/ package.

Key Features:
1. Behavior-Gating: Focuses on engineering directives over text-policing.
2. User Pushback Protocol: Mandatory re-verification if previous claim was challenged.
3. Decoupled Architecture: Modules register via registry.py.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

# Add project root and hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

# Import modular infrastructure
# Note: Package moved to UserPromptSubmit_modules to avoid naming conflict
# with this router file (UserPromptSubmit.py)
from UserPromptSubmit_modules import registry

try:
    from __lib import prompt_session_state
except Exception:
    prompt_session_state = None

# Performance tracking
MAX_TOTAL_TOKENS = 5000
ACCEPTANCE_RESPONSES = {
    "ok",
    "okay",
    "thanks",
    "thank you",
    "got it",
    "acknowledged",
    "proceed",
    "yes",
}


def _safe_id(value: str | None) -> str:
    """Convert session/terminal id to filesystem-safe fragment."""
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _get_challenge_marker_paths(data: dict) -> tuple[Path, Path]:
    """Return scoped marker path and legacy fallback marker path."""
    session_id = (
        data.get("session_id")
        or data.get("sessionId")
        or data.get("CLAUDE_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
    )
    terminal_id = (
        data.get("terminal_id")
        or data.get("terminalId")
        or data.get("CLAUDE_TERMINAL_ID")
        or os.environ.get("CLAUDE_TERMINAL_ID")
    )
    scoped_name = f"last_blocked_claim_{_safe_id(str(session_id) if session_id else None)}_{_safe_id(str(terminal_id) if terminal_id else None)}.json"
    scoped_marker = HOOKS_DIR / "session_data" / scoped_name
    legacy_marker = HOOKS_DIR / "session_data" / "last_blocked_claim.json"
    return scoped_marker, legacy_marker


def _marker_matches_scope(marker_data: dict, data: dict) -> bool:
    """Require marker session/terminal identity to match current scope."""
    expected_session = str(
        data.get("session_id")
        or data.get("sessionId")
        or data.get("CLAUDE_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or ""
    )
    expected_terminal = str(
        data.get("terminal_id")
        or data.get("terminalId")
        or data.get("CLAUDE_TERMINAL_ID")
        or os.environ.get("CLAUDE_TERMINAL_ID")
        or ""
    )
    marker_session = str(marker_data.get("session_id", ""))
    marker_terminal = str(marker_data.get("terminal_id", ""))

    # Legacy markers without explicit scope are considered ambiguous and ignored.
    if not marker_session and not marker_terminal:
        return False
    if expected_session and marker_session and marker_session != expected_session:
        return False
    if expected_terminal and marker_terminal and marker_terminal != expected_terminal:
        return False
    return True


def check_user_pushback(data: dict, prompt: str) -> str | None:
    """
    User Pushback Protocol.
    Injects a hard directive if the previous turn was blocked and the user didn't accept.
    """
    # Implementation detail: Check a session-local flag for "Last blocked claim"
    # This is set by Stop hooks when they block.
    scoped_marker, legacy_marker = _get_challenge_marker_paths(data)
    if not scoped_marker.exists() and not legacy_marker.exists():
        return None

    try:
        challenge_marker = None
        marker_data = None

        allow_legacy = os.environ.get("ALLOW_LEGACY_BLOCK_MARKER", "0").lower() in (
            "1",
            "true",
            "yes",
        )

        if scoped_marker.exists():
            challenge_marker = scoped_marker
            marker_data = json.loads(scoped_marker.read_text(encoding="utf-8"))
        elif allow_legacy and legacy_marker.exists():
            candidate = json.loads(legacy_marker.read_text(encoding="utf-8"))
            if _marker_matches_scope(candidate, data):
                challenge_marker = legacy_marker
                marker_data = candidate

        if challenge_marker is None or marker_data is None:
            return None

        # Check TTL (5 minutes) using wall-clock timestamps shared with Stop hooks.
        if time.time() - marker_data.get("timestamp", 0) > 300:
            challenge_marker.unlink()
            return None

        # Is the prompt an acceptance?
        prompt_lower = prompt.lower().strip()
        # Non-acceptance triggers re-verification directive
        if prompt_lower not in ACCEPTANCE_RESPONSES:
            injection = (
                "⚠️ **USER CHALLENGE DETECTED**\n\n"
                "Your previous claim was blocked or challenged. You MUST perform an "
                "exhaustive manual verification (raw `grep`, `ls -R`, or `cat`) before "
                "re-stating any system state claims."
            )
            return injection
        else:
            challenge_marker.unlink()  # User accepted, clear marker
            return None
    except Exception:
        return None


def _pin_scope_env(data: dict) -> None:
    """Pin session/terminal ids in payload + env for cross-hook consistency."""
    session_id = (
        data.get("session_id")
        or data.get("sessionId")
        or data.get("CLAUDE_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID", "").strip()
    )
    if session_id:
        session_id = str(session_id).strip()
        data.setdefault("session_id", session_id)
        os.environ["CLAUDE_SESSION_ID"] = session_id

    terminal_id = (
        data.get("terminal_id")
        or data.get("terminalId")
        or data.get("CLAUDE_TERMINAL_ID")
        or os.environ.get("CLAUDE_TERMINAL_ID", "").strip()
    )
    if not terminal_id:
        try:
            from __lib.terminal_detection import detect_terminal_id

            terminal_id = (detect_terminal_id() or "").strip()
        except Exception:
            terminal_id = ""
    if terminal_id:
        terminal_id = str(terminal_id).strip()
        data.setdefault("terminal_id", terminal_id)
        os.environ["CLAUDE_TERMINAL_ID"] = terminal_id

    # CRITICAL: Start a new DB-backed turn BEFORE hooks run.
    from evidence_store import start_turn

    turn_id = data.get("turn_id") or start_turn(
        session_id=session_id,
        terminal_id=terminal_id,
        prompt=str(data.get("prompt", "") or data.get("message", "") or ""),
        transcript_path=str(data.get("transcript_path", "") or ""),
    )
    data.setdefault("turn_id", turn_id)


def main():
    """Main router entry point."""
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        print("{}")
        sys.exit(0)

    try:
        # Strip BOM if present
        raw_input = raw_input.lstrip("\ufeff")
        data = json.loads(raw_input)
        prompt = data.get("prompt", "") or data.get("message", "")
    except json.JSONDecodeError:
        prompt = raw_input
        data = {"prompt": prompt}

    _pin_scope_env(data)

    # Keep per-session/terminal latest prompt state up to date for PreToolUse checks.
    if prompt_session_state is not None:
        try:
            prompt_session_state.write_latest_prompt(data, prompt)
        except Exception:
            pass

    # --- Next Step Options: single-letter choice bridge (A/B/...) ---
    # This must run BEFORE the "len(prompt) < 5" early-exit.
    #
    # Stale immunity WITHOUT TTL:
    # - If there's a pending menu and the user does NOT reply with a single letter,
    #   we clear the menu state immediately.
    # - If the user replies with a valid letter, we clear state and rewrite prompt.
    try:
        from __lib.next_step_choice_state import (
            clear_next_step_menu,
            detect_letter_choice,
            get_pending_next_step_menu,
            resolve_choice_to_command,
        )

        pending_menu = get_pending_next_step_menu(data)
        choice = detect_letter_choice(prompt)

        if pending_menu and choice is not None:
            resolved = resolve_choice_to_command(pending_menu, choice)
            if resolved:
                cmd, display = resolved
                clear_next_step_menu(data)

                output = {
                    "hookSpecificOutput": {
                        "hookEventName": "UserPromptSubmit",
                        "additionalContext": f"**✓ Next Step selected:** {choice} - {display}",
                        "replacePrompt": cmd,
                    }
                }
                print(json.dumps(output))
                sys.exit(0)

            # Choice provided, but not valid for the pending menu => clear (stale immune).
            clear_next_step_menu(data)

        elif pending_menu and choice is None:
            # User said something else; do not keep the old menu alive.
            clear_next_step_menu(data)

    except Exception:
        # Fail open: never block user prompts.
        pass

    # Check for prompt choice responses (short prompts like "0", "1", "enhanced")
    # These should be allowed even if less than 5 characters
    choice_indicators = ["0", "1", "enhanced", "original", "[0]", "[1]"]
    is_choice_response = any(prompt.strip().lower() == c.lower() for c in choice_indicators)

    # Also allow numeric Next Step choice inputs (even if no menu is pending).
    is_next_step_choice = bool(re.fullmatch(r"\d+", prompt.strip()))

    # Also allow slash commands (e.g., /gto, /ask, /arch) - these trigger skill execution
    is_slash_command = bool(re.match(r"^/\w+", prompt.strip()))

    if not prompt or (
        len(prompt.strip()) < 5
        and not is_choice_response
        and not is_next_step_choice
        and not is_slash_command
    ):
        print("{}")
        sys.exit(0)

    # 1. Run Modular Hooks via Registry
    try:
        hook_results = registry.run_hooks(data, prompt)
    except Exception as e:
        # Claude Code treats stderr as hook error - use stdout for diagnostics
        print(f"Error running hooks: {e}", file=sys.stdout)
        hook_results = []

    injections = []
    replacement_prompt = None
    suppress_echo = False

    for res in hook_results:
        if res and res.context:
            # Check for replacePrompt action
            if isinstance(res.context, dict) and "replacePrompt" in res.context:
                replacement_prompt = res.context["replacePrompt"]
                suppress_echo = bool(res.context.get("suppressEcho", False))
                # Also include any additionalContext from the same result
                if "additionalContext" in res.context:
                    _ctx = res.context["additionalContext"]
                    if isinstance(_ctx, dict):
                        _ctx = json.dumps(_ctx)
                    elif not isinstance(_ctx, str):
                        _ctx = str(_ctx)
                    injections.append(_ctx)
            elif isinstance(res.context, dict) and "additionalContext" in res.context:
                # Dict with additionalContext but no replacePrompt (e.g. operating_rules)
                _ctx = res.context["additionalContext"]
                if isinstance(_ctx, dict):
                    _ctx = json.dumps(_ctx)
                elif not isinstance(_ctx, str):
                    _ctx = str(_ctx)
                injections.append(_ctx)
            else:
                injections.append(res.context)

    # 2. Add User Pushback Logic
    pushback = check_user_pushback(data, prompt)
    if pushback:
        injections.append(pushback)

    # 3. Output - handle prompt replacement
    if replacement_prompt:
        # User chose to replace their prompt
        combined_context = "\n\n".join(injections)
        if combined_context and not suppress_echo:
            combined_context += "\n\n"
            combined_context += f"**Original prompt replaced with:**\n\n{replacement_prompt}"

        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": combined_context,
                "replacePrompt": replacement_prompt,
            }
        }
    elif injections:
        # 3. Merge and Output
        combined_context = "\n\n".join(injections)

        if combined_context:
            # Respect token budget
            if len(combined_context) > MAX_TOTAL_TOKENS * 4:
                combined_context = combined_context[: MAX_TOTAL_TOKENS * 4] + "... [truncated]"

            output = {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": combined_context,
                }
            }
        else:
            output = {}
    else:
        output = {}

    print(json.dumps(output))


# --- Diagnostic logging (temporary) ---
_DIAG_LOG = HOOKS_DIR / "logs" / "diagnostics" / "ups_router_diag.jsonl"


def _log_diagnostic(stage: str, detail: str = "") -> None:
    """Append a diagnostic entry. Never fails."""
    try:
        _DIAG_LOG.parent.mkdir(parents=True, exist_ok=True)
        import json as _j

        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "stage": stage,
            "detail": detail[:500],
        }
        with open(_DIAG_LOG, "a", encoding="utf-8") as f:
            f.write(_j.dumps(entry) + "\n")
    except Exception:
        pass


def main_with_diag():
    """Wrapper that logs any exception or stderr leak from main()."""
    import contextlib
    import io

    from __lib.subprocess_patch import patch_subprocess_context

    _log_diagnostic("start")
    stderr_capture = io.StringIO()

    # Use context manager for scoped subprocess patching
    with patch_subprocess_context():
        try:
            with contextlib.redirect_stderr(stderr_capture):
                main()
            stderr_text = stderr_capture.getvalue()
            if stderr_text:
                _log_diagnostic("stderr_leak", stderr_text)
            _log_diagnostic("ok")
        except SystemExit as e:
            stderr_text = stderr_capture.getvalue()
            if stderr_text:
                _log_diagnostic("stderr_leak", stderr_text)
            _log_diagnostic("exit", str(e.code))
            raise
        except Exception as e:
            _log_diagnostic("exception", f"{type(e).__name__}: {e}")
            # Still output valid JSON so Claude Code doesn't get garbage
            print("{}")


def process_prompt(event_data: dict) -> dict:
    """In-process entry point for router integration.

    Args:
        event_data: Hook event data (prompt, message, session_id, etc.)

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
        return {"ok": False, "diagnostic": str(e)}

    finally:
        # Restore stdin
        sys.stdin = old_stdin


if __name__ == "__main__":
    main_with_diag()
