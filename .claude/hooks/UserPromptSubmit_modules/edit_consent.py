"""Detect explicit approve-edit commands and issue consent tokens."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from __lib import pre_tool_use_logic

APPROVE_EDIT_RE = re.compile(r"^\s*approve\s+edit\s+(.+?)\s*$", re.IGNORECASE)

# Hook development session intent patterns
HOOK_DEV_START_RE = re.compile(
    r"^\s*(?:editing\s+hooks|hook\s+development|developing\s+hooks|"
    r"start\s+hook\s+development|hook\s+dev\s+mode|"
    r"enable\s+hook\s+development|hooks?\s+development\s+session)",
    re.IGNORECASE
)

HOOK_DEV_STOP_RE = re.compile(
    r"^\s*(?:stop\s+editing\s+hooks|end\s+hook\s+development|"
    r"disable\s+hook\s+development|exit\s+hook\s+dev)",
    re.IGNORECASE
)


def _create_hook_dev_session(session_id: str, hooks_dir: Path) -> tuple[bool, str]:
    """Create a hook development session marker file.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        session_data_dir = hooks_dir / "session_data"
        session_data_dir.mkdir(parents=True, exist_ok=True)

        marker_file = session_data_dir / f"hook_dev_session_{session_id}.json"

        session_data = {
            "start_time": time.time(),
            "session_id": session_id,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        marker_file.write_text(json.dumps(session_data, indent=2), encoding="utf-8")

        return True, f"Hook development session started. Expires in 30 minutes at {time.strftime('%H:%M:%S', time.gmtime(session_data['start_time'] + 1800))}"

    except (OSError, json.JSONDecodeError, PermissionError) as e:
        return False, f"Failed to create session: {e}"


def _end_hook_dev_session(session_id: str, hooks_dir: Path) -> tuple[bool, str]:
    """End a hook development session by deleting the marker file.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        session_data_dir = hooks_dir / "session_data"
        marker_file = session_data_dir / f"hook_dev_session_{session_id}.json"

        if marker_file.exists():
            marker_file.unlink()
            return True, "Hook development session ended."
        else:
            return True, "No active hook development session found."

    except (OSError, json.JSONDecodeError, PermissionError) as e:
        return False, f"Failed to end session: {e}"


@register_hook("edit_consent", priority=1.5)
def run_edit_consent(context: HookContext) -> HookResult:
    """Create task-scoped consent token from explicit user approval command.
    
    Also handles hook development session start/stop commands.
    """
    prompt = (context.prompt or "").strip()

    # Check for hook development session commands first
    hook_dev_start = HOOK_DEV_START_RE.match(prompt)
    if hook_dev_start:
        session_id = pre_tool_use_logic.resolve_session_id(context.data)
        if not session_id:
            return HookResult(
                context={
                    "additionalContext": (
                        "Could not start hook development session: missing session id. "
                        "Retry in the same active session."
                    ),
                },
                tokens=35,
                priority=1.5,
            )

        ok, msg = _create_hook_dev_session(session_id, HOOKS_DIR)

        return HookResult(
            context={
                "additionalContext": msg,
            },
            tokens=40,
            priority=1.5,
        )

    # Check for hook development session stop
    hook_dev_stop = HOOK_DEV_STOP_RE.match(prompt)
    if hook_dev_stop:
        session_id = pre_tool_use_logic.resolve_session_id(context.data)
        if not session_id:
            return HookResult(
                context={
                    "additionalContext": (
                        "Could not end hook development session: missing session id."
                    ),
                },
                tokens=30,
                priority=1.5,
            )

        ok, msg = _end_hook_dev_session(session_id, HOOKS_DIR)

        return HookResult(
            context={
                "additionalContext": msg,
            },
            tokens=25,
            priority=1.5,
        )

    # Original approve edit logic
    match = APPROVE_EDIT_RE.match(prompt)
    if not match:
        return HookResult.empty()

    target = match.group(1).strip()
    session_id = pre_tool_use_logic.resolve_session_id(context.data)
    if not session_id:
        return HookResult(
            context={
                "additionalContext": (
                    "Could not issue edit consent token: missing session id. "
                    "Retry in the same active session."
                ),
            },
            tokens=35,
            priority=1.5,
        )

    canonical_path, reason = pre_tool_use_logic.resolve_claude_target_path(target)
    if not canonical_path:
        if reason == "ambiguous_target":
            return HookResult(
                context={
                    "additionalContext": (
                        "Edit approval is ambiguous. Use a .claude-relative path, for example:\n"
                        "approve edit hooks/__lib/pre_tool_use_logic.py"
                    ),
                },
                tokens=45,
                priority=1.5,
            )
        return HookResult(
            context={
                "additionalContext": (
                    "Edit approval rejected: target must resolve under P:/.claude/. "
                    "Use `approve edit <.claude-relative-path>`."
                ),
            },
            tokens=35,
            priority=1.5,
        )

    terminal_id = (
        context.terminal_id
        or pre_tool_use_logic.resolve_terminal_id(context.data)
    )
    major_task_id = pre_tool_use_logic.resolve_major_task_id(
        context.data,
        terminal_id=terminal_id,
    )

    ok, status = pre_tool_use_logic.create_claude_edit_consent_token(
        session_id,
        canonical_path,
        terminal_id=terminal_id,
        major_task_id=major_task_id,
    )
    if not ok:
        return HookResult(
            context={
                "additionalContext": (
                    "Failed to issue edit consent token. "
                    f"reason={status}, path={canonical_path}"
                ),
            },
            tokens=30,
            priority=1.5,
        )

    relative = canonical_path.removeprefix("p:/.claude/")
    return HookResult(
        context={
            "additionalContext": (
                f"Edit consent recorded for `{relative}` in task `{major_task_id}`."
            ),
        },
        tokens=20,
        priority=1.5,
    )
