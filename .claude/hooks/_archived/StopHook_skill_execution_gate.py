#!/usr/bin/env python3
"""
StopHook_skill_execution_gate.py
=================================

Safety net for skill execution validation.

This is the SECONDARY defense - the PreToolUse hook handles real-time
blocking. This Stop hook only fires when PreToolUse failed to block,
indicating a system issue that should be logged.

PROBLEM SOLVED:
Claude loads skill documentation, then provides its own analysis instead
of executing the skill's designated workflow.

v3.2 CHANGES:
- Simplified to safety net only (PreToolUse is primary defense)
- Late violation logging indicates PreToolUse failure
- Extended registry schema with hint and intent_enabled

v3.3 CHANGES:
- Added Layer 1 marker-based governance (from v3.0 port)
- extract_response_text() reads from transcript_path JSONL
- Governance state read from skill_governance_state.json
- Two-strike pattern: retry on first bypass, hard block on second

v3.4 CHANGES:
- Slash command bypass detection: blocks when user types /command but
  assistant ignores it and responds with prose (no tools used)
- Extracts user prompt from transcript_path to detect slash commands
- Works even when no governance state exists (skill file not found)
- Excludes built-in CLI commands, lightweight skills, and knowledge skills

AUTHOR: CSF NIP
VERSION: 3.4.0
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# Import hook_main decorator
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from __lib.hook_base import hook_main

# =============================================================================
# CONFIGURATION
# =============================================================================

ENABLED = os.environ.get("SKILL_EXECUTION_GATE_ENABLED", "true").lower() == "true"

STATE_DIR = Path("P:/.claude/state")
LOG_FILE = Path("P:/.claude/logs/skill_execution_gate.jsonl")

# Stale timeout (prevents blocking indefinitely)
STALE_TIMEOUT = 300  # 5 minutes

DEBUG = os.environ.get("SKILL_EXEC_DEBUG", "0") == "1"

# Slash commands that are NOT skills (built-in CLI commands)
# These should never be blocked by skill enforcement
BUILTIN_SLASH_COMMANDS = {
    "help",
    "clear",
    "compact",
    "cost",
    "doctor",
    "init",
    "login",
    "logout",
    "memory",
    "permissions",
    "review",
    "status",
    "terminal-setup",
    "vim",
    "bug",
    "config",
    "model",
    "tasks",
    "listen",
}

# Slash commands that are lightweight/meta and don't need enforcement
LIGHTWEIGHT_SLASH_COMMANDS = {
    "context-status",
    "clear-notifications",
    "obs",
    "recent",
    "constraints",
    "standards",
}

# =============================================================================
# SKILL EXECUTION REGISTRY (Extended v3.2 Schema)
# =============================================================================
# Each skill declares:
#   - tools: List of tool names that count as execution
#   - pattern: Optional regex that must appear in tool input (e.g., command)
#   - hint: User-facing message when blocked (NEW in v3.2)
#   - intent_enabled: Use daemon semantic validation (NEW in v3.2)

SKILL_EXECUTION_REGISTRY = {
    # External CLI skills (require Bash with specific command)
    "ask-olymp": {
        "tools": ["Bash", "Task"],
        "pattern": r"ask_cli\.py|ask-olymp",
        "hint": "Use /ask-olymp via ask_cli.py with opencode provider",
        "intent_enabled": False,
    },
    "olymp": {  # Alias
        "tools": ["Bash", "Task"],
        "pattern": r"ask_cli\.py|ask-olymp",
        "hint": "Use /ask-olymp via ask_cli.py with opencode provider",
        "intent_enabled": False,
    },
    "multi-llm": {  # Alias
        "tools": ["Bash", "Task"],
        "pattern": r"ask_cli\.py",
        "hint": "Use /ask-olymp via ask_cli.py with opencode provider",
        "intent_enabled": False,
    },
    # RCA/Truth - CLI launcher (v4.0: matches python -m rca.hook_launcher)
    "rca": {
        "tools": ["Bash", "Task"],
        "pattern": r"rca\.hook_launcher|python.*-m.*rca|rca\s+\w+\.py",
        "hint": "Use /rca via python -m rca.hook_launcher or the rca CLI",
        "intent_enabled": True,
    },
    "truth": {
        "tools": ["Bash", "Task"],
        "pattern": r"src\.truth|validator|verify|truth_cli",
        "hint": "Use /truth via truth_cli.py or src.truth imports",
        "intent_enabled": True,
    },
    # Git operations
    "git": {
        "tools": ["Bash"],
        "pattern": r"git\s+",
        "hint": "Use git commands directly via Bash",
        "intent_enabled": False,
    },
    "commit": {
        "tools": ["Bash"],
        "pattern": r"git\s+commit",
        "hint": "Use git commit via Bash",
        "intent_enabled": False,
    },
    "push": {
        "tools": ["Bash"],
        "pattern": r"git\s+push",
        "hint": "Use git push via Bash",
        "intent_enabled": False,
    },
    # Build/test
    "build": {
        "tools": ["Bash", "Task"],
        "pattern": r"build|npm|pip|pytest|make",
        "hint": "Use build tools via Bash or Task",
        "intent_enabled": False,
    },
    # /test skill - requires actual test execution, not analysis
    "test": {
        "tools": ["Bash", "Task"],
        "pattern": r"pytest|python\s+-m\s+pytest|npm\s+test|coverage",
        "hint": "Run /test via actual test execution (pytest, npm test) - do not provide prose analysis without running tests",
        "intent_enabled": False,
    },
    # File exploration skills - require Read/Glob/Grep
    "discover": {
        "tools": ["Read", "Glob", "Grep", "Bash"],
        "pattern": None,
        "hint": "Use Read, Glob, Grep, or Bash for file exploration",
        "intent_enabled": False,
    },
    "aid": {
        "tools": ["Bash"],
        "pattern": r"aid\s+|ai-distiller",
        "hint": "Use aid via ai-distiller",
        "intent_enabled": False,
    },
    # Web skills
    "crawl": {
        "tools": ["WebFetch", "Bash"],
        "pattern": None,
        "hint": "Use WebFetch or Bash for web crawling",
        "intent_enabled": False,
    },
    "research": {
        "tools": ["Bash", "Task"],
        "pattern": r"(python(\.exe)?\s+(-m\s+research\.cli|.*[\\/]research[\\/]cli\.py)|uv\s+run\s+(-m\s+)?research\.cli)",
        "hint": "Use /research via python -m research.cli (or research/cli.py)",
        "intent_enabled": False,
    },
    # Task management
    "tm": {
        "tools": ["Bash", "Task"],
        "pattern": r"tm|taskmaster",
        "hint": "Use taskmaster via Bash or Task",
        "intent_enabled": False,
    },
    # Orchestration
    "exec": {
        "tools": ["Bash", "Task"],
        "pattern": None,
        "hint": "Use exec via Bash or Task",
        "intent_enabled": False,
    },
    "flow": {
        "tools": ["Bash", "Task"],
        "pattern": None,
        "hint": "Use flow via Bash or Task",
        "intent_enabled": False,
    },
    "orchestrator": {
        "tools": ["Bash", "Task"],
        "pattern": r"orchestrat",
        "hint": "Use orchestrator via Bash or Task",
        "intent_enabled": False,
    },
    # Quality/Analysis skills - require observation tools, session activity tracker
    "q": {
        "tools": ["Read", "Grep", "Glob"],
        "pattern": r"session.*activity|wt_session|q_context",
        "hint": "Use /q via session activity tracker (WT_SESSION) as PRIMARY source, git as verification only",
        "intent_enabled": False,
    },
    "duf": {
        "tools": ["Read", "Grep", "Glob"],
        "pattern": r"pre-mortem|cognitive.*check",
        "hint": "Use /duf via session activity tracker first",
        "intent_enabled": False,
    },
    # Validation pipeline (PROCEDURE skill - sequential stages)
    "v": {
        "tools": ["Bash", "Task"],
        "pattern": r"\.claude[\\/]skills[\\/]v[\\/]scripts[\\/]stage|pylint.*delta|adversarial.*(security|performance|quality|testing)",
        "hint": "Use /v via sequential stage execution (stage1_syntax, stage2_pylint_delta, stage3_adversarial, etc.)",
        "intent_enabled": False,
    },
    "quality": {  # Alias
        "tools": ["Bash", "Task"],
        "pattern": r"\.claude[\\/]skills[\\/]v[\\/]scripts[\\/]stage|pylint.*delta|adversarial.*(security|performance|quality|testing)",
        "hint": "Use /v via sequential stage execution (stage1_syntax, stage2_pylint_delta, stage3_adversarial, etc.)",
        "intent_enabled": False,
    },
    "pipeline": {  # Alias
        "tools": ["Bash", "Task"],
        "pattern": r"\.claude[\\/]skills[\\/]v[\\/]scripts[\\/]stage|pylint.*delta|adversarial.*(security|performance|quality|testing)",
        "hint": "Use /v via sequential stage execution (stage1_syntax, stage2_pylint_delta, stage3_adversarial, etc.)",
        "intent_enabled": False,
    },
}

# Skills that are KNOWLEDGE/REFERENCE type (don't require execution)
KNOWLEDGE_SKILLS = {
    "standards",
    "constraints",
    "techniques",
    "evidence-tiers",
    "constitutional-patterns",
    "cognitive-frameworks",
    "prompt_refiner",
    "library-first",
    "solo-dev-authority",
    "data-safety-vcs",
}


def extract_user_prompt(input_data: dict) -> str:
    """Extract the user's LAST prompt from transcript_path.

    Reads the JSONL transcript to find the most recent user message.
    This is used to detect if the user typed a slash command that
    the assistant then ignored without invoking the Skill tool.
    """
    transcript_path = input_data.get("transcript_path", "")
    if not transcript_path:
        return ""

    try:
        transcript = Path(transcript_path)
        if not transcript.exists():
            return ""

        content = transcript.read_text(encoding="utf-8")
        last_user_text = ""

        for line in content.strip().split("\n"):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                # Look for user messages
                role = entry.get("role", "")
                msg_type = entry.get("type", "")

                if role == "user" or (msg_type == "message" and role == "user"):
                    msg = entry.get("message", entry)
                    msg_content = msg.get("content", entry.get("content", ""))

                    if isinstance(msg_content, list):
                        text_parts = [
                            b.get("text", "")
                            for b in msg_content
                            if isinstance(b, dict) and b.get("type") == "text"
                        ]
                        if text_parts:
                            last_user_text = " ".join(text_parts)
                    elif isinstance(msg_content, str) and msg_content:
                        last_user_text = msg_content
            except json.JSONDecodeError:
                continue

        return last_user_text.strip()

    except Exception as e:
        log(f"Error extracting user prompt: {e}")
        return ""


def _extract_slash_command(prompt: str) -> str | None:
    """Extract slash command name from prompt.

    Returns the command name (e.g., 'debugRCA') or None if not a slash command.
    """
    match = re.match(r"^/([a-zA-Z][\w-]*)", prompt.strip())
    if match:
        return match.group(1)
    return None


def log(msg: str) -> None:
    """Debug logging."""
    if DEBUG:
        print(f"[skill_exec_gate] {msg}", file=sys.stderr)


def log_event(event: str, data: dict) -> None:
    """Log structured event for analysis."""
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {"timestamp": time.time(), "event": event, **data}
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


# =============================================================================
# LAYER 1: MARKER-BASED GOVERNANCE
# =============================================================================


def _get_governance_state_file() -> Path:
    """Get governance state file path for this terminal."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
        from skill_guard.utils.terminal_detection import detect_terminal_id

        terminal_id = detect_terminal_id()
    except ImportError:
        terminal_id = f"term_{os.getpid()}"
    state_dir = STATE_DIR / f"skill_execution_{terminal_id}"
    return state_dir / "skill_governance_state.json"


def _read_governance_state() -> dict | None:
    """Read governance state written by the router."""
    gov_file = _get_governance_state_file()
    if not gov_file.exists():
        return None
    try:
        state = json.loads(gov_file.read_text(encoding="utf-8"))
        # Stale check
        if time.time() - state.get("loaded_at", 0) > STALE_TIMEOUT:
            log("Stale governance state, clearing")
            gov_file.unlink(missing_ok=True)
            return None
        return state
    except (json.JSONDecodeError, OSError) as e:
        log(f"Error reading governance state: {e}")
        return None


def _update_governance_retry(state: dict) -> None:
    """Increment retry_count in governance state."""
    try:
        state["retry_count"] = state.get("retry_count", 0) + 1
        gov_file = _get_governance_state_file()
        gov_file.write_text(json.dumps(state), encoding="utf-8")
    except Exception:
        pass


def _clear_governance_state() -> None:
    """Remove governance state file."""
    try:
        gov_file = _get_governance_state_file()
        gov_file.unlink(missing_ok=True)
    except Exception:
        pass


def extract_tools_used(input_data: dict) -> list[str]:
    """Extract tool names used in the current assistant response.

    Returns a list of tool names (e.g., ["Edit", "Read", "Skill"]) from the
    most recent assistant message.

    Claude Code provides a transcript_path pointing to a JSONL file.
    The last assistant entry contains content blocks with type "tool_use".
    """
    tools_used = []

    # Primary: read from transcript_path
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        try:
            transcript = Path(transcript_path)
            if transcript.exists():
                content = transcript.read_text(encoding="utf-8")
                for line in reversed(content.strip().split("\n")):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        # Format: {"type": "message", "role": "assistant", "message": {"content": [...]}}
                        if entry.get("type") == "message" and entry.get("role") == "assistant":
                            msg_content = entry.get("message", {}).get("content", [])
                            if isinstance(msg_content, list):
                                for block in msg_content:
                                    if block.get("type") == "tool_use":
                                        tools_used.append(block.get("name", ""))
                            break
                        elif entry.get("type") == "assistant":
                            msg_content = entry.get("message", {}).get("content", [])
                            if isinstance(msg_content, list):
                                for block in msg_content:
                                    if block.get("type") == "tool_use":
                                        tools_used.append(block.get("name", ""))
                            break
                        elif entry.get("role") == "assistant":
                            msg = entry.get("message", entry)
                            msg_content = msg.get("content", entry.get("content", ""))
                            if isinstance(msg_content, list):
                                for block in msg_content:
                                    if block.get("type") == "tool_use":
                                        tools_used.append(block.get("name", ""))
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            log(f"Error reading transcript for tools: {e}")

    return tools_used


def extract_response_text(input_data: dict) -> str:
    """Extract assistant response text from Stop hook input.

    Claude Code provides a transcript_path pointing to a JSONL file.
    The last assistant entry contains the response in:
      {"type": "message", "role": "assistant", "message": {"content": [{"type": "text", "text": "..."}]}}
    """
    response = ""

    # Primary: read from transcript_path (proven method from verify_claims_transcript.py)
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        try:
            transcript = Path(transcript_path)
            if transcript.exists():
                content = transcript.read_text(encoding="utf-8")
                for line in reversed(content.strip().split("\n")):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        # Format: {"type": "message", "role": "assistant", "message": {"content": [...]}}
                        if entry.get("type") == "message" and entry.get("role") == "assistant":
                            msg_content = entry.get("message", {}).get("content", [])
                            if isinstance(msg_content, list):
                                response = " ".join(
                                    b.get("text", "")
                                    for b in msg_content
                                    if b.get("type") == "text"
                                )
                            else:
                                response = str(msg_content)
                            break
                        elif entry.get("type") == "assistant":
                            msg_content = entry.get("message", {}).get("content", [])
                            if isinstance(msg_content, list):
                                response = " ".join(
                                    b.get("text", "")
                                    for b in msg_content
                                    if b.get("type") == "text"
                                )
                            else:
                                response = str(msg_content)
                            break
                        elif entry.get("role") == "assistant":
                            msg = entry.get("message", entry)
                            msg_content = msg.get("content", entry.get("content", ""))
                            if isinstance(msg_content, list):
                                response = " ".join(
                                    b.get("text", "")
                                    for b in msg_content
                                    if b.get("type") == "text"
                                )
                            else:
                                response = str(msg_content)
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            log(f"Error reading transcript: {e}")

    # Fallback: conversation/messages array in stdin data
    if not response:
        conversation = input_data.get("conversation", []) or input_data.get("messages", [])
        if isinstance(conversation, list):
            for msg in reversed(conversation):
                if isinstance(msg, dict) and msg.get("role") == "assistant":
                    content = msg.get("content", "")
                    if isinstance(content, list):
                        response = " ".join(
                            b.get("text", "")
                            for b in content
                            if isinstance(b, dict) and b.get("type") == "text"
                        )
                    else:
                        response = str(content)
                    break

    # Fallback: direct fields
    if not response:
        response = input_data.get("response", "") or input_data.get("assistant_response", "")

    return str(response)


def _check_governance_markers(input_data: dict) -> dict:
    """Layer 1 marker-based governance check.

    Returns:
        {"allow": True/False, "reason": "..."} or empty dict if no governance active.
    """
    gov_state = _read_governance_state()
    if not gov_state:
        return {}  # No governance active

    skill = gov_state.get("skill", "unknown")
    markers = gov_state.get("markers", [])
    retry_count = gov_state.get("retry_count", 0)

    if not markers:
        _clear_governance_state()
        return {}

    # Extract response text
    response = extract_response_text(input_data)
    log(f"Governance check for /{skill}: response length={len(response)}, markers={markers[:3]}")

    # Check markers (case-insensitive substring)
    response_lower = response.lower()
    found = [m for m in markers if m.lower() in response_lower]

    if found:
        log(f"Governance PASS for /{skill}: found markers {found[:3]}")
        log_event("governance_pass", {"skill": skill, "found_markers": found})
        _clear_governance_state()
        return {"allow": True, "reason": f"skill_markers_present: {found[:3]}"}

    # VIOLATION: no markers found
    log(f"Governance VIOLATION for /{skill}: no markers in {len(response)} chars")
    log_event(
        "governance_violation",
        {
            "skill": skill,
            "expected_markers": markers[:5],
            "retry_count": retry_count,
            "response_length": len(response),
        },
    )

    if retry_count == 0:
        _update_governance_retry(gov_state)
        return {
            "allow": False,
            "reason": (
                f"SKILL BYPASSED - RETRY REQUIRED\n\n"
                f"You invoked /{skill} but your response doesn't follow the skill workflow.\n\n"
                f"Expected: Response should contain skill markers like:\n"
                + "\n".join(f'  - "{m}"' for m in markers[:5])
                + f"\n\nActual: None of these markers were found in your response.\n\n"
                f"Follow the /{skill} skill instructions that were injected.\n"
                f"This is attempt 1/2. Next bypass will be blocked."
            ),
        }
    else:
        _clear_governance_state()
        return {
            "allow": False,
            "reason": (
                f"SKILL GOVERNANCE FAILURE\n\n"
                f"/{skill} was invoked but IGNORED twice.\n\n"
                f"Required markers: {markers[:5]}\n"
                f"Found: None\n\n"
                f"You MUST follow the skill's workflow. Re-read the skill instructions."
            ),
        }


# =============================================================================
# TOOL-BASED STATE MANAGEMENT (v3.2 legacy)
# =============================================================================


def _get_state_file() -> Path:
    """Get the state file path for this terminal."""
    try:
        from skill_guard.skill_execution_state import _get_state_file

        return _get_state_file()
    except ImportError:
        # Fallback to generic location
        return STATE_DIR / "skill_execution_pending.json"


def _read_state() -> dict | None:
    """Read current skill execution state."""
    state_file = _get_state_file()
    if not state_file.exists():
        return None

    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def _clear_state() -> None:
    """Clear the current skill execution state."""
    state_file = _get_state_file()
    state_file.unlink(missing_ok=True)


# =============================================================================
# VALIDATION
# =============================================================================


def _is_stale(state: dict) -> bool:
    """Check if state is stale (older than STALE_TIMEOUT)."""
    loaded_at = state.get("loaded_at", 0)
    return (time.time() - loaded_at) > STALE_TIMEOUT


def _check_pattern_match(command: str, pattern: str) -> bool:
    """Check if command matches the required pattern."""
    if not pattern:
        return True  # No pattern requirement

    try:
        return bool(re.search(pattern, command, re.IGNORECASE))
    except re.error:
        return False


def validate_execution(state: dict, tool_history: list) -> dict:
    """Validate that skill was properly executed.

    Args:
        state: Skill execution state from state file
        tool_history: List of tools used in this session

    Returns:
        Dict with "satisfied" (bool) and "reason" (str)
    """
    skill = state.get("skill", "")

    # Check if stale
    if _is_stale(state):
        log_event("stale_state", {"skill": skill})
        return {
            "satisfied": True,  # Don't block on stale state
            "reason": f"State for '{skill}' is stale ({STALE_TIMEOUT}s timeout)",
        }

    # Get required tools
    required_tools = state.get("required_tools", [])
    if not required_tools:
        # No tool requirement, consider satisfied
        return {"satisfied": True, "reason": ""}

    # Check if any required tool was used
    tools_used = state.get("tools_used", [])
    execution_tool_used = any(t in required_tools for t in tools_used)

    if not execution_tool_used:
        # No execution tool used - violation
        # v3.2: This is a LATE violation (PreToolUse should have blocked)
        hint = state.get("hint", f"Use /{skill} via its designated execution mechanism")
        reason = (
            f"⚠️ LATE VIOLATION DETECTED: /{skill} execution not satisfied.\n"
            f"💡 {hint}\n"
            f"🔧 PreToolUse hook should have blocked this - check hook status.\n"
            f"📋 Required tools: {', '.join(required_tools)}\n"
            f"📋 Tools used: {', '.join(tools_used) if tools_used else 'None'}"
        )
        log_event(
            "late_violation",
            {
                "skill": skill,
                "required_tools": required_tools,
                "tools_used": tools_used,
            },
        )
        return {"satisfied": False, "reason": reason}

    # Check pattern match for commands
    pattern = state.get("pattern", "")
    if pattern:
        commands_run = state.get("commands_run", [])
        pattern_matched = any(_check_pattern_match(cmd, pattern) for cmd in commands_run)

        if not pattern_matched:
            hint = state.get("hint", f"Use /{skill} with correct command pattern")
            reason = (
                f"⚠️ LATE VIOLATION DETECTED: /{skill} command pattern not matched.\n"
                f"💡 {hint}\n"
                f"🔧 PreToolUse hook should have blocked this - check hook status.\n"
                f"📋 Pattern: {pattern}\n"
                f"📋 Commands run: {commands_run[:3]}"
            )
            log_event(
                "late_violation_pattern",
                {
                    "skill": skill,
                    "pattern": pattern,
                    "commands": commands_run,
                },
            )
            return {"satisfied": False, "reason": reason}

    return {"satisfied": True, "reason": ""}


# =============================================================================
# STOP HANDLER
# =============================================================================


@hook_main
def main():
    """Main entry point - reads stdin, runs governance then tool-based checks."""
    if not ENABLED:
        print(json.dumps({"allow": True, "reason": ""}))
        return

    # Parse stdin (Claude Code sends hook input as JSON)
    try:
        input_text = sys.stdin.read().strip()
        input_data = json.loads(input_text) if input_text else {}
    except (json.JSONDecodeError, Exception):
        input_data = {}

    # =================================================================
    # TOOL-USE VERIFICATION (check if Skill tool was actually used)
    # =================================================================
    # Only enforce governance markers if Skill tool was actually invoked THIS turn.
    # File edits (Edit/Write) mentioning skill names should not trigger governance.
    tools_used_this_turn = extract_tools_used(input_data)

    # Guard against empty list (parse failure)
    # Also check for slash command bypass when no tools were used at all
    if not tools_used_this_turn:
        user_prompt = extract_user_prompt(input_data)
        slash_cmd = _extract_slash_command(user_prompt) if user_prompt else None

        if (
            slash_cmd
            and slash_cmd not in BUILTIN_SLASH_COMMANDS
            and slash_cmd not in LIGHTWEIGHT_SLASH_COMMANDS
            and slash_cmd not in KNOWLEDGE_SKILLS
        ):
            log(
                f"SLASH COMMAND BYPASS (no tools): user typed /{slash_cmd} but assistant used NO tools at all"
            )
            log_event(
                "slash_command_bypass_no_tools",
                {
                    "skill": slash_cmd,
                    "user_prompt": user_prompt[:200],
                },
            )
            _clear_governance_state()
            print(
                json.dumps(
                    {
                        "decision": "block",
                        "reason": (
                            f"SLASH COMMAND IGNORED\n\n"
                            f"The user invoked /{slash_cmd} but you responded with prose without using any tools.\n\n"
                            f"You MUST:\n"
                            f"1. Use the Skill tool to load /{slash_cmd}\n"
                            f"2. Follow the skill's workflow instructions\n"
                            f"3. Execute using the appropriate tools (Bash, Task, etc.)\n\n"
                            f"Do NOT interpret slash commands as conversational text."
                        ),
                    }
                )
            )
            return

        log("WARNING: Tool extraction returned empty list. Assuming no Skill invocation.")
        _clear_governance_state()  # Clean up any stale state
        print(json.dumps({}))
        return

    if "Skill" not in tools_used_this_turn:
        # No skill invocation this turn.
        # BUT: Check if user typed a slash command that the assistant ignored entirely.
        # This catches the case where Claude Code injects skill content via system-reminder
        # but the assistant never calls the Skill tool and responds with unrelated prose.
        user_prompt = extract_user_prompt(input_data)
        slash_cmd = _extract_slash_command(user_prompt) if user_prompt else None

        if (
            slash_cmd
            and slash_cmd not in BUILTIN_SLASH_COMMANDS
            and slash_cmd not in LIGHTWEIGHT_SLASH_COMMANDS
            and slash_cmd not in KNOWLEDGE_SKILLS
        ):
            # User typed a skill slash command but assistant never invoked Skill tool.
            # Check if assistant used ANY execution tools (Bash, Task, etc.)
            # If it did, it may be legitimately working - only block pure prose responses.
            execution_tools_used = {
                t
                for t in tools_used_this_turn
                if t
                in (
                    "Bash",
                    "Task",
                    "Read",
                    "Grep",
                    "Glob",
                    "Write",
                    "Edit",
                    "WebFetch",
                    "WebSearch",
                )
            }

            if not execution_tools_used:
                # Pure prose response to a slash command = bypass
                log(
                    f"SLASH COMMAND BYPASS: user typed /{slash_cmd} but assistant used no execution tools. Tools: {tools_used_this_turn}"
                )
                log_event(
                    "slash_command_bypass",
                    {
                        "skill": slash_cmd,
                        "user_prompt": user_prompt[:200],
                        "tools_used": tools_used_this_turn,
                    },
                )
                _clear_governance_state()
                print(
                    json.dumps(
                        {
                            "decision": "block",
                            "reason": (
                                f"SLASH COMMAND IGNORED\n\n"
                                f"The user invoked /{slash_cmd} but you responded with prose instead of executing it.\n\n"
                                f"You MUST:\n"
                                f"1. Use the Skill tool to load /{slash_cmd}\n"
                                f"2. Follow the skill's workflow instructions\n"
                                f"3. Execute using the appropriate tools (Bash, Task, etc.)\n\n"
                                f"Do NOT interpret slash commands as conversational text.\n"
                                f"Do NOT respond about unrelated previous work."
                            ),
                        }
                    )
                )
                return

        # No slash command bypass detected - clean up and allow
        _clear_governance_state()
        log(f"Skipping governance: Skill tool not used. Tools used: {tools_used_this_turn}")
        print(json.dumps({}))
        return

    # =================================================================
    # LAYER 1: MARKER-BASED GOVERNANCE (checked first)
    # =================================================================
    gov_result = _check_governance_markers(input_data)
    if gov_result and not gov_result.get("allow", True):
        print(json.dumps({"decision": "block", "reason": gov_result["reason"]}))
        return

    # =================================================================
    # LAYER 2: TOOL-BASED ENFORCEMENT (v3.2 safety net)
    # =================================================================
    state = _read_state()
    if not state:
        print(json.dumps({}))
        return

    skill = state.get("skill", "")

    # Skip knowledge skills
    if skill in KNOWLEDGE_SKILLS:
        _clear_state()
        print(json.dumps({}))
        return

    # Validate execution
    result = validate_execution(state, [])

    # Clear state after validation
    _clear_state()

    if result["satisfied"]:
        print(json.dumps({}))
    else:
        print(json.dumps({"decision": "block", "reason": result["reason"]}))


if __name__ == "__main__":
    main()
