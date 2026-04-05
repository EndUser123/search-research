#!/usr/bin/env python3
"""
Competence Injector - UserPromptSubmit Hook
=============================================

Injects competence template guidance when a skill loads.

Based on skill type (research, analysis, implementation, validation, planning),
injects a 5-step lifecycle, anti-avoidance principles, reasoning checklist,
and required output structure.

Conditional injection: The root-cause obligation principle is only injected
when context signals indicate risk of lazy shortcuts (error encountered,
fix/debug intent in prompt, or previous response was blocked).

Meta skills (ask, search, task, commit, help, status) receive no template.
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
    from typing import Any

# Import hook base classes and registry (strict - fail fast on errors)
from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Add competence module to path
COMPETENCE_DIR = Path(__file__).resolve().parent.parent / "competence"
sys.path.insert(0, str(COMPETENCE_DIR))

# skill_execution_state is in hooks parent directory
HOOKS_ROOT = Path(__file__).resolve().parent.parent
if str(HOOKS_ROOT) not in sys.path:
    sys.path.insert(0, str(HOOKS_ROOT))

# Try to import competence functions, with fallback stubs
try:
    from competence import (
        META_TASK_TYPE,
        get_task_type_for_skill,
        render_template,
    )
except ImportError:
    # Competence module not available - define fallback stubs
    def get_task_type_for_skill(skill_name: str, category: str | None = None) -> str | None:
        return None

    def render_template(
        task_type: str, minimal: bool = False, context_signals: dict | None = None
    ) -> str:
        return ""

    META_TASK_TYPE = "meta"

# Import skill execution state from local hooks module
try:
    from skill_execution_state import read_pending_state
except ImportError:

    def read_pending_state() -> dict | None:
        return None


# Trivial prompt patterns that get minimal template
TRIVIAL_PATTERNS = {
    "help",
    "status",
    "list",
    "info",
    "version",
    "what",
    "how",
    "why",
}

META_SKILLS = {"ask", "search", "task", "commit", "help", "status"}

# Signal file for error state (written by PostToolUse, read here)
SIGNAL_DIR = Path("P:/.claude/state/signals")

# Patterns in user prompt that indicate fix/debug/error intent
FIX_INTENT_PATTERNS = re.compile(
    r"\b(fix|debug|error|broken|crash(?:ed|es|ing)?|fail(?:ed|s|ing)?|"
    r"bug|issue|wrong|not working|"
    r"doesn't work|doesn't work|won't|can't|cannot|exception|traceback|"
    r"stacktrace|stack trace|segfault|panic|abort)\b",
    re.IGNORECASE,
)

# Patterns that indicate greenfield/new-build intent (triggers Library-First Gate)
GREENFIELD_INTENT_PATTERNS = re.compile(
    r"\b(build|create|implement|new\s+(feature|module|system|component|backend|skill|tool|class|service|pipeline|indexer|engine)|"
    r"add\s+(a|an|the|new)\s+\w+|design|architect|from\s+scratch|greenfield|"
    r"propose|proposal|suggesting|let'?s\s+make|we\s+need\s+(a|an|to\s+build))\b",
    re.IGNORECASE,
)

# Patterns for detecting implementation intent without a skill (#5 fallback + #D declarative)
# Covers both imperative ("build X") and declarative ("I need X", "we should add X")
IMPLEMENTATION_INTENT_PATTERNS = re.compile(
    r"\b("
    # Imperative verbs
    r"build|create|implement|refactor|optimize|add|write|develop|code|make|set\s+up|configure|wire\s+up|hook\s+up|"
    # Declarative patterns
    r"i\s+need\s+(a|an|to)|we\s+need\s+(a|an|to)|we\s+should\s+(add|build|create|implement|write)|"
    r"(?:the|this|our)\s+\w+\s+(?:system|module|component|service)\s+should|"
    r"let'?s\s+(add|build|create|implement|make|write)|"
    r"i\s+want\s+to\s+(add|build|create|implement|make|write)|"
    r"(?:please|can\s+you|could\s+you)\s+(add|build|create|implement|make|write)"
    r")\b",
    re.IGNORECASE,
)

# Patterns for detecting planning intent without a skill
PLANNING_INTENT_PATTERNS = re.compile(
    r"\b("
    r"plan|roadmap|breakdown|architect|design\s+(a|the|an)|strategy|phase|milestone|"
    r"how\s+should\s+we\s+(approach|implement|build|structure)|"
    r"what'?s\s+the\s+best\s+(approach|way|strategy)"
    r")\b",
    re.IGNORECASE,
)


# Intent-to-task-type mapping for fallback (no skill active)
def _detect_task_type_from_prompt(prompt: str) -> str | None:
    """Detect task type from prompt text when no skill is active.

    Only returns task types where competence templates add value:
    implementation and planning. Questions and simple requests
    get no template (handled by unified_injector intent classification).

    Args:
        prompt: The user's prompt text

    Returns:
        Task type string or None (no template needed)
    """
    if not prompt or len(prompt.strip()) < 20:
        return None

    prompt_stripped = prompt.strip()

    # Skip slash commands (skill system handles these)
    if prompt_stripped.startswith("/"):
        return None

    # Skip questions — unified_injector handles these
    if "?" in prompt_stripped and not IMPLEMENTATION_INTENT_PATTERNS.search(prompt_stripped):
        return None

    # Check for implementation intent
    if IMPLEMENTATION_INTENT_PATTERNS.search(prompt_stripped):
        return "implementation"

    # Check for planning intent
    if PLANNING_INTENT_PATTERNS.search(prompt_stripped):
        return "planning"

    return None


def _detect_context_signals(prompt: str, data: dict[str, Any]) -> dict[str, bool]:
    """Detect context signals that trigger conditional principle injection.

    Checks four independent signal sources:
    1. fix_requested: User prompt contains fix/debug/error language
    2. error_encountered: A recent tool call wrote an error signal file
    3. previous_block: The behavior audit blocked the previous response
    4. greenfield_intent: User prompt suggests building new systems/components

    Args:
        prompt: The user's prompt text
        data: Event data dictionary with session/terminal IDs

    Returns:
        Dict of boolean flags, one per signal type
    """
    signals: dict[str, bool] = {
        "fix_requested": False,
        "error_encountered": False,
        "previous_block": False,
        "greenfield_intent": False,
    }

    # 1. Check prompt for fix/debug intent
    if prompt and FIX_INTENT_PATTERNS.search(prompt):
        signals["fix_requested"] = True

    # 1b. Check prompt for greenfield/new-build intent
    if prompt and GREENFIELD_INTENT_PATTERNS.search(prompt):
        signals["greenfield_intent"] = True

    # 2. Check for recent error signal file (written by PostToolUse)
    try:
        signal_file = SIGNAL_DIR / "last_tool_error.json"
        if signal_file.exists():
            signal_data = json.loads(signal_file.read_text(encoding="utf-8"))
            # Signal is valid if less than 5 minutes old
            if time.monotonic() - signal_data.get("timestamp", 0) < 300:
                signals["error_encountered"] = True
            else:
                # Stale signal — clean up
                signal_file.unlink(missing_ok=True)
    except (json.JSONDecodeError, OSError):
        pass

    # 3. Check for pushback marker (behavior audit blocked previous response)
    try:
        session_id = (
            data.get("session_id")
            or data.get("sessionId")
            or os.environ.get("CLAUDE_SESSION_ID")
            or ""
        )
        terminal_id = (
            data.get("terminal_id")
            or data.get("terminalId")
            or os.environ.get("CLAUDE_TERMINAL_ID")
            or ""
        )
        safe_session = (
            re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(session_id)) if session_id else "unknown"
        )
        safe_terminal = (
            re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(terminal_id)) if terminal_id else "unknown"
        )
        marker_name = f"last_blocked_claim_{safe_session}_{safe_terminal}.json"
        marker_path = HOOKS_ROOT / "session_data" / marker_name
        if marker_path.exists():
            marker_data = json.loads(marker_path.read_text(encoding="utf-8"))
            if time.time() - marker_data.get("timestamp", 0) < 300:
                signals["previous_block"] = True
    except (json.JSONDecodeError, OSError):
        pass

    return signals


def is_trivial_prompt(prompt: str, skill_name: str | None = None) -> bool:
    """Check if prompt is trivially short and should get minimal template.

    Args:
        prompt: The user's prompt text
        skill_name: Optional skill name for additional context

    Returns:
        True if prompt is trivial (< 15 chars after stripping command prefix)
    """
    if not prompt:
        return True

    # Strip the skill command prefix if present
    stripped = prompt.strip()
    if skill_name:
        # Remove "/skillname" prefix
        prefix = f"/{skill_name.lower()}"
        if stripped.lower().startswith(prefix):
            stripped = stripped[len(prefix) :].strip()

    # Check length
    if len(stripped) < 15:
        return True

    # Check for known trivial patterns
    first_word = stripped.split()[0].lower() if stripped.split() else ""
    if first_word in TRIVIAL_PATTERNS:
        return True

    return False


def get_user_skill_name(data: dict[str, Any]) -> str | None:
    """Extract skill name from event data.

    Checks multiple possible locations for the skill name.

    Args:
        data: Event data dictionary

    Returns:
        Skill name or None
    """
    # Direct skill field
    if "skill" in data:
        return str(data["skill"])

    # Tool input might have skill name
    tool_input = data.get("toolInput") or data.get("tool_input") or {}
    if isinstance(tool_input, dict):
        skill = tool_input.get("skill")
        if skill:
            return str(skill)

    # Check tool name for Skill tool
    tool_name = data.get("toolName") or data.get("tool_name") or ""
    if tool_name == "Skill":
        # Skill was used, check state
        return None  # State will tell us

    return None


# State file for contract completeness gate to read at Stop time
DETECTED_TASK_TYPE_DIR = Path("P:/.claude/state/competence")


def _write_detected_task_type(task_type: str, skill_name: str | None) -> None:
    """Write detected task type to state for the contract completeness gate.

    This bridges UserPromptSubmit (where we know the task type) to Stop
    (where contract_completeness_gate needs it). Without this, the Stop
    hook can only check contracts when a skill is explicitly active.

    Args:
        task_type: The detected task type (e.g., "implementation")
        skill_name: The skill name if one is active, or None for fallback
    """
    try:
        DETECTED_TASK_TYPE_DIR.mkdir(parents=True, exist_ok=True)
        state_file = DETECTED_TASK_TYPE_DIR / "last_task_type.json"
        state_file.write_text(
            json.dumps(
                {
                    "task_type": task_type,
                    "skill": skill_name,
                    "source": "skill" if skill_name else "prompt_fallback",
                    "timestamp": time.time(),
                }
            ),
            encoding="utf-8",
        )
    except OSError:
        pass  # Fail silently — this is advisory state


def process_skill_load(context: HookContext) -> HookResult:
    """Main hook function - inject competence template for active skill or detected intent.

    Two paths:
    1. Skill active: Map skill -> task type -> render template (original behavior)
    2. No skill: Detect implementation/planning intent from prompt -> render template
       This closes the gap where freeform prompts got no competence guidance.

    Args:
        context: HookContext with prompt, data, session_id, terminal_id

    Returns:
        HookResult with injected template or empty result
    """
    try:
        prompt = context.prompt or ""
        skill_name = None
        task_type = None

        # Path 1: Check if a skill is loaded via state
        state = read_pending_state()
        if state:
            skill_name = state.get("skill")

        if skill_name:
            # Skill-based path (original behavior)
            if str(skill_name).lower() in META_SKILLS:
                return HookResult.empty()
            task_type = get_task_type_for_skill(skill_name)
            if task_type is None or task_type == META_TASK_TYPE:
                return HookResult.empty()
        else:
            # Path 2: No skill loaded — detect task type from prompt
            task_type = _detect_task_type_from_prompt(prompt)
            if task_type is None:
                return HookResult.empty()

        # Check if prompt is trivial
        use_minimal = is_trivial_prompt(prompt, skill_name)

        # Detect context signals for conditional root-cause obligation
        context_signals = _detect_context_signals(prompt, context.data)

        # Render template with signals
        template = render_template(
            task_type,
            minimal=use_minimal,
            context_signals=context_signals,
        )

        if not template:
            return HookResult.empty()

        # Write detected task type to state for contract completeness gate (#B)
        # This allows the Stop hook to check output contracts even without a skill
        _write_detected_task_type(task_type, skill_name)

        # Estimate tokens (chars / 4 is standard heuristic)
        estimated_tokens = len(template) // 4

        return HookResult(
            context=template,
            tokens=estimated_tokens,
            priority=7.0,
        )

    except Exception as e:
        # Fail open - log error but don't break the session
        # NOTE: Hooks must NOT print to stdout (Claude Code treats it as error)
        import traceback as tb

        # Log to file instead of stdout
        try:
            log_dir = Path("P:/.claude/state/logs")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "competence_injector_errors.log"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} [ERROR] {e}\n")
                f.write(f"{tb.format_exc()}\n")
        except Exception:
            pass  # Fail silently if logging fails
        return HookResult.empty()


# Register the hook
@register_hook("competence_injector", priority=7.0)
def competence_injector_hook(context: HookContext) -> HookResult:
    """Hook entry point - injects competence template for active skill."""
    return process_skill_load(context)
