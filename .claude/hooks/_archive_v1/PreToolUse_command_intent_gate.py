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

ARCHITECTURE (v1.1 - concurrent-safe):
- State file: P:/.claude/hooks/state/pending_command_intent_{session_id}.json
- Session ID: Parent PID (CC process) for consistency across hook invocations
- Set by: UserPromptSubmit_router.py (_store_command_intent)
- Consumed by: This hook
- TTL: 5 minutes, auto-cleanup of stale files

FAIL-SAFE BEHAVIOR:
- Missing state file → Allow (no slash command active)
- Expired state → Allow (cleaned up automatically)
- psutil unavailable → Falls back to os.getppid() → os.getpid()
"""

import json
import os
import sys
import time
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

STATE_DIR = Path("P:/.claude/hooks/state")
LOG_FILE = Path("P:/.claude/logs/command_intent_gate.jsonl")
INTENT_TTL_SECONDS = 300  # 5 minute TTL

# Skills that execute via bash and need intent validation
SKILL_COMMAND_PATTERNS = {
    "ask-cli4": ["ask_cli.py", "llm_cli.py"],
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
    "ask-cli4": ["--qwen-only", "--gemini-only", "--codex-only", "--vibe-only", "--skip-"],
    "ask-cli": ["--qwen-only", "--gemini-only", "--codex-only", "--vibe-only"],
    "git-sync": ["--dry-run", "--skip-push", "--skip-pull"],
}

# =============================================================================
# SESSION IDENTIFICATION
# =============================================================================

def _get_session_id() -> str:
    """Get consistent session ID for this CC instance.
    
    Uses parent PID (Claude Code process) for consistency across hook invocations.
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


def _get_intent_state_file() -> Path:
    """Get session-specific intent state file path."""
    session_id = _get_session_id()
    return STATE_DIR / f"pending_command_intent_{session_id}.json"

# =============================================================================
# STATE MANAGEMENT
# =============================================================================

def get_pending_intent() -> dict | None:
    """Read pending slash command intent from session-specific state file."""
    state_file = _get_intent_state_file()
    if not state_file.exists():
        return None
    try:
        with open(state_file, encoding="utf-8") as f:
            state = json.load(f)
        # Check expiry
        if state.get("expires_at", 0) < time.time():
            state_file.unlink(missing_ok=True)
            return None
        return state
    except Exception:
        return None


def clear_intent_state():
    """Clear the pending intent state after validation."""
    try:
        state_file = _get_intent_state_file()
        state_file.unlink(missing_ok=True)
    except Exception:
        pass


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
        return False

    import re
    for pattern in patterns:
        if re.search(pattern, command, re.IGNORECASE):
            return True
    return False


def has_restrictive_flags(command: str, skill: str) -> list[str]:
    """Return list of restrictive flags found in command."""
    flags = RESTRICTIVE_FLAGS.get(skill, [])
    found = []
    for flag in flags:
        if flag in command:
            found.append(flag)
    return found


def check_intent_justification(user_prompt: str, flags: list[str]) -> tuple[bool, str]:
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

    print(json.dumps(output))
    sys.exit(0)


if __name__ == "__main__":
    main()
