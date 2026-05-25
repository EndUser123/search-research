#!/usr/bin/env python3
"""
Command Intent Validation Gate v1.1

Validates that Claude's bash commands match user intent when executing slash commands.

PROBLEM SOLVED:
- User says: /ask-cli4 "review the plan"
- Claude executes: python ask_cli.py "..." --qwen-only  ← UNAUTHORIZED RESTRICTION
- This gate blocks commands that deviate from user intent

FLOW:
1. UserPromptSubmit stores {skill, prompt} when slash command detected
2. This PreToolUse hook reads state when Bash tool is about to execute
3. Validates that any restrictive flags are justified by user's prompt
4. Returns permissionDecision: allow/deny

ARCHITECTURE (v1.2 - multi-terminal safe):
- State file: P:/.claude/hooks/state/pending_command_intent_{terminal_id}_{session_id}.json
- Session ID: Parent PID (CC process) for consistency across hook invocations
- Terminal ID: Environment variable or detected terminal identifier
- Set by: UserPromptSubmit_router.py (_store_command_intent)
- Consumed by: This hook and PreToolUse.py
- TTL: 5 minutes, auto-cleanup of stale files

FAIL-SAFE BEHAVIOR:
- Missing state file → Allow (no slash command active)
- Expired state → Allow (cleaned up automatically)
- psutil unavailable → Falls back to os.getppid() → os.getpid()
"""


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data


_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# Import hybrid clock-safe TTL utilities
from __lib.ttl_utils import is_expired as _is_expired

# =============================================================================
# CONFIGURATION
# =============================================================================

STATE_DIR = Path("P:/.claude/hooks/state")
FALLBACK_STATE_DIR = Path(tempfile.gettempdir()) / "claude_hooks" / "state"
LOG_FILE = Path("P:/.claude/logs/command_intent_gate.jsonl")
INTENT_TTL_SECONDS = 300  # 5 minute TTL

# Skills that execute via bash and need intent validation
SKILL_COMMAND_PATTERNS = {
    "ask-olymp": ["ask_cli.py", "llm_cli.py"],
    "ask-cli": ["ask_cli.py", "llm_cli.py"],
    "qwen": ["qwen"],
    "gemini": ["gemini"],
    "codex": ["codex"],
    "vibe": ["vibe"],
    "git": ["git ", "sl "],
    "git-sync": ["git ", "sl "],
}

# Restrictive flags that reduce scope (require justification)
RESTRICTIVE_FLAGS = {
    "ask-olymp": ["--qwen-only", "--gemini-only", "--codex-only", "--vibe-only", "--skip-"],
    "ask-cli": ["--qwen-only", "--gemini-only", "--codex-only", "--vibe-only"],
    "git-sync": ["--dry-run", "--skip-push", "--skip-pull"],
}

# =============================================================================
# SESSION IDENTIFICATION
# =============================================================================

def _get_session_id() -> str:
    """Get consistent session ID for this CC instance.

    Uses parent process ID (Claude Code process) for consistency across hook invocations.
    All hooks spawned by the same CC instance share the parent PID.
    """
    # Try environment variable first
    if env_id := os.environ.get("CLAUDE_SESSION_ID"):
        return env_id

    # Use parent process ID (Claude Code's PID)
    try:
        import psutil
        parent = psutil.Process(os.getpid()).parent()
        if parent:
            return str(parent.pid)
    except (ImportError, Exception):
        pass

    # Fallback to parent PID without psutil
    try:
        return str(os.getppid())
    except Exception:
        pass

    # Last resort: current PID (less reliable)
    return str(os.getpid())


def _get_intent_state_files() -> list[Path]:
    """Get candidate terminal-scoped and session-scoped intent state file paths."""
    import re

    session_id = _get_session_id()
    terminal_id = str(
        os.environ.get("CLAUDE_TERMINAL_ID", "")
    ).strip()
    safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id or "unknown")
    filename = f"pending_command_intent_{safe_terminal}_{session_id}.json"
    return [STATE_DIR / filename, FALLBACK_STATE_DIR / filename]

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

def get_pending_intent() -> dict | None:
    """Read pending slash command intent from session-specific state file."""
    for state_file in _get_intent_state_files():
        if not state_file.exists():
            continue
        try:
            with open(state_file, encoding="utf-8") as f:
                state = json.load(f)
            # Check expiry
            if state.get("expires_at", 0) < time.time():
                state_file.unlink(missing_ok=True)
                continue
            return state
        except Exception:
            continue
    return None


def clear_intent_state():
    """Clear the pending intent state after validation."""
    for state_file in _get_intent_state_files():
        try:
            state_file.unlink(missing_ok=True)
        except Exception:
            continue


def log_decision(skill: str, user_prompt: str, command: str, decision: str, reason: str):
    """Log validation decisions for audit."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "skill": skill,
            "user_prompt": user_prompt[:200],
            "command": command[:300],
            "decision": decision,
            "reason": reason,
        }
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass

# =============================================================================
# INTENT VALIDATION
# =============================================================================

def is_skill_execution(command: str, skill: str) -> bool:
    """Check if this bash command is executing the skill."""
    patterns = SKILL_COMMAND_PATTERNS.get(skill, [])
    if not patterns:
        # Default to True for unknown skills so intent validation applies
        # to all slash commands, not only hardcoded ones.
        return True

    import re
    for pattern in patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def has_restrictive_flags(command: str, skill: str) -> list:
    """Return list of restrictive flags found in command."""
    flags = RESTRICTIVE_FLAGS.get(skill, [])
    found = []
    for flag in flags:
        if flag in command:
            found.append(flag)
    return found


def check_intent_justification(user_prompt: str, flags: list) -> tuple:
    """
    Check if restrictive flags are justified by user's prompt.

    Returns (justified, reason)
    """
    prompt_lower = user_prompt.lower()

    # Build justification patterns for each flag type
    justifications = {
        "--qwen-only": ["qwen", "use qwen", "just qwen", "only qwen", "with qwen"],
        "--gemini-only": ["gemini", "use gemini", "just gemini", "only gemini", "with gemini"],
        "--codex-only": ["codex", "use codex", "just codex", "only codex", "with codex"],
        "--vibe-only": ["vibe", "use vibe", "just vibe", "only vibe", "with vibe"],
        "--dry-run": ["dry run", "dry-run", "simulate", "test run", "don't actually", "without executing"],
        "--skip-push": ["skip push", "don't push", "no push", "without push"],
        "--skip-pull": ["skip pull", "don't pull", "no pull", "without pull"],
    }

    unjustified = []
    for flag in flags:
        patterns = justifications.get(flag, [])
        if not any(p in prompt_lower for p in patterns):
            unjustified.append(flag)

    if unjustified:
        return False, f"Unauthorized restrictive flags: {', '.join(unjustified)}"
    return True, "Flags justified by user prompt"

# =============================================================================
# MAIN HOOK LOGIC
# =============================================================================

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # No input, allow

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Only validate Bash commands
    if tool_name != "Bash":
        sys.exit(0)

    command = tool_input.get("command", "")
    if not command:
        sys.exit(0)

    # Check for pending slash command intent
    intent = get_pending_intent()
    if not intent:
        sys.exit(0)  # No slash command active, allow

    skill = intent.get("skill", "")
    user_prompt = intent.get("prompt", "")

    # Check if this is the skill's execution command
    if not is_skill_execution(command, skill):
        sys.exit(0)  # Not the skill execution, allow

    # Check for restrictive flags
    restrictive = has_restrictive_flags(command, skill)

    if not restrictive:
        # No restrictive flags, allow
        clear_intent_state()
        log_decision(skill, user_prompt, command, "allow", "No restrictive flags")
        sys.exit(0)

    # Validate that restrictive flags are justified
    justified, reason = check_intent_justification(user_prompt, restrictive)

    if justified:
        clear_intent_state()
        log_decision(skill, user_prompt, command, "allow", reason)
        sys.exit(0)

    # BLOCK: Unjustified restrictive flags
    log_decision(skill, user_prompt, command, "deny", reason)

    # Output JSON for structured denial
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"""⛔ COMMAND INTENT MISMATCH

User invoked: /{skill} {user_prompt}
Your command: {command}

VIOLATION: {reason}

The user did not authorize these restrictions. Either:
1. Remove the unauthorized flags and use skill defaults
2. Or ask the user if they want to restrict execution

Re-execute with correct flags."""
        }
    }

    print(json.dumps(_normalize_stdout(output)))
    sys.exit(0)


if __name__ == "__main__":
    main()
