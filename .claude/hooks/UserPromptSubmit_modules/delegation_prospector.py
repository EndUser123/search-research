"""Delegation Prospector - UserPromptSubmit hook.

Detects multi-surface work patterns that could benefit from subagent delegation.
Writes blocking state for PreToolUse_delegation_gate to enforce the pattern.
"""

from __future__ import annotations

import json
import os
import re
import stat
import tempfile
import time
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# Telemetry log path
_LOG_DIR = Path(__file__).resolve().parent.parent / "logs" / "diagnostics"
_LOG_FILE = _LOG_DIR / "delegation_prospector.jsonl"

# State directory for cross-hook communication
# File: hooks/UserPromptSubmit_modules/delegation_prospector.py
# State goes to .claude/.artifacts/{terminal_id}/hook_state/ for terminal isolation
import os as _os

# Get terminal ID from environment (no-arg version for file-based ops)
def _get_terminal_id() -> str:
    """Get normalized terminal ID from environment."""
    raw = _os.environ.get("WT_SESSION", "")
    return f"console_{raw}" if raw else "unknown"

def _get_state_dir() -> Path:
    """Get terminal-scoped state directory."""
    claude_root = Path(__file__).resolve().parent.parent.parent  # .claude
    return claude_root / ".artifacts" / _get_terminal_id() / "hook_state"
_DELEGATION_TTL_SECONDS = 300  # 5 minutes

# Hook priority constant (runs before subagent_enforcer at priority 13)
_PROSPECTOR_PRIORITY = 12

# Sensitive data redaction patterns (SEC-002 fix)
_SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(?:bearer|api[_-]?key|token|secret|password|credential)[:\s]+[\S]{8,}"),
    re.compile(r"(?i)sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"-----BEGIN [A-Z]+ PRIVATE KEY-----"),
    # GitHub tokens
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"gho_[A-Za-z0-9]{36}"),
    re.compile(r"ghu_[A-Za-z0-9]{36}"),
    re.compile(r"ghs_[A-Za-z0-9]{36}"),
    re.compile(r"ghr_[A-Za-z0-9]{36}"),
    # AWS access keys
    re.compile(r"(?i)AKIA[0-9A-Z]{16}"),
    # JWT tokens
    re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"),
]

def _redact_sensitive(value: str) -> str:
    if not value:
        return value
    result = value
    for pattern in _SENSITIVE_PATTERNS:
        result = pattern.sub("[REDACTED]", result)
    return result

# Skills that are inherently delegation-oriented
# Detection: prompt.lstrip().startswith(f"/{skill}") or f" /{skill} " in prompt
_DELEGATION_HEAVY_SKILLS = frozenset([
    # /go variants (dispatches subagents to worktrees)
    "go", "go_pi", "go2", "go-ct",
    # TDD implementation (uses subagents for red/green/refactor)
    "code", "code_v3.0", "code_v4.0", "code_v3-0", "code_v4-0",
    # Code review (dispatches parallel specialist agents)
    "code-review", "requesting-code-review",
    # Planning/dispatching (adversarial subagents)
    "planning", "dispatching-parallel-agents", "subagent-driven-development",
    # Multi-agent workflows
    "executing-plans", "improve-codebase-architecture", "team",
    # TDD phases
    "tdd", "test-driven-development", "refactor",
    # Quality analysis
    "sqa", "pre-mortem",
    # Architecture
    "design",
])

# Detection patterns for implicit multi-surface work (fallback when no skill invoked)
_DELEGATION_PATTERNS = [
    re.compile(r"(?:inspect|review|analyze|check)\s+\w+\s+(?:and|,|\&)\s+\w+", re.IGNORECASE),
    re.compile(r"(?:create|add|implement)\s+(?:[^,]+,){2,}[^,]+", re.IGNORECASE),
    re.compile(r"(?:parallel|concurrent)\s+(?:agent|subagent|work)", re.IGNORECASE),
    re.compile(r"\bsubagent\b", re.IGNORECASE),
    re.compile(r"(?:use|spawn|create|launch)\s+(?:an?\s+)?agent", re.IGNORECASE),
    re.compile(r"(?:both|all)\s+of\s+(?:the\s+)?(?:the\s+)?", re.IGNORECASE),
    re.compile(r"\beach\s+(?:of\s+)?(?:the\s+)?", re.IGNORECASE),
    re.compile(r"(?:^|,|\s)(?:\w+\s*,){2,}", re.IGNORECASE),
    re.compile(r"(?:test|check|verify)\s+(?:both|all|each)\b", re.IGNORECASE),
    re.compile(r"(?:grep|search|find)\s+all\b", re.IGNORECASE),
]

_DELEGATION_ADVISORY = """
[SUBAGENT DELEGATION OPPORTUNITY]

This task appears to involve multiple surfaces that could benefit from parallel
verification using subagents.

When to delegate:
  - Bounded verification tasks (file inspection, grep/read passes, running tests)
  - Multi-target inspection where each target is independent
  - When each subagent can return a compact factual summary

When NOT to delegate:
  - Final synthesis, patch prioritization, cross-cutting judgment
  - Trivial lookups or single-file reads
  - Tasks requiring main-context reasoning to integrate findings

Tip: You can use the Agent tool to spawn parallel subagents. Each should return
only: (1) verified facts, (2) exact file/function references, (3) concise implications.
""".strip()


def _extract_skill_name(prompt: str) -> str | None:
    """Extract skill name from prompt if it's a slash command."""
    stripped = prompt.strip()
    if not stripped.startswith("/"):
        return None
    # Handle "/skill:args" or "/skill args" formats
    after_slash = stripped.lstrip("/")
    # Split on whitespace or colon
    for sep in (":", " ", "\t"):
        if sep in after_slash:
            return after_slash.split(sep)[0]
    return after_slash.split()[0] if after_slash else None


def _detect_delegation_opportunity(prompt: str) -> tuple[bool, str | None]:
    """Detect delegation opportunity via skill invocation (priority) or pattern matching."""
    if not prompt:
        return False, None

    # Priority 1: Check for delegation-heavy skill invocations
    skill_name = _extract_skill_name(prompt)
    if skill_name and skill_name in _DELEGATION_HEAVY_SKILLS:
        return True, f"skill:/{skill_name}"

    # Priority 2: Fallback to pattern matching for implicit delegation hints
    for pattern in _DELEGATION_PATTERNS:
        if pattern.search(prompt):
            return True, f"matched: {pattern.pattern[:50]}..."
    return False, None


def _get_terminal_id_from_context(context: HookContext) -> str:
    return (context.data.get("terminal_id") or context.data.get("terminalId") or context.data.get("CLAUDE_TERMINAL_ID") or os.environ.get("CLAUDE_TERMINAL_ID") or "default")

def _get_session_id(context: HookContext) -> str:
    return (context.data.get("session_id") or context.data.get("sessionId") or context.session_id or "unknown")


def _log_delegation_event(event_type: str, terminal_id: str, session_id: str, matched_pattern: str | None, prompt_snippet: str) -> None:
    try:
        _LOG_DIR.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "event": event_type,
            "terminal_id": terminal_id,
            "session_id": session_id,
            "matched_pattern": (matched_pattern[:100] if matched_pattern else None),
            "prompt_snippet": _redact_sensitive(prompt_snippet[:200]) if prompt_snippet else "",
        }
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError as e:
        import warnings
        warnings.warn(f"delegation_prospector: failed to log: {e}")


def _write_delegation_state(terminal_id: str, matched_pattern: str | None, prompt_snippet: str) -> None:
    """Write blocking state for PreToolUse_delegation_gate (terminal-scoped)."""
    state_dir = _get_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "delegation_expected.json"
    state_data = {
        "terminal_id": terminal_id,
        "detected_at": time.time(),
        "matched_pattern": _redact_sensitive(matched_pattern) if matched_pattern else None,
        "prompt_snippet": _redact_sensitive(prompt_snippet)[:200] if prompt_snippet else "",
    }
    # Atomic write with explicit permissions
    with tempfile.NamedTemporaryFile(
        mode="w", dir=str(state_dir), delete=False, suffix=".tmp", encoding="utf-8"
    ) as tmp:
        json.dump(state_data, tmp, indent=2)
        tmp_path = tmp.name
    os.replace(tmp_path, str(state_file))
    # Set restrictive permissions (owner read/write only)
    import stat as _stat
    os.chmod(state_file, _stat.S_IRUSR | _stat.S_IWUSR)


def _clear_delegation_state() -> None:
    """Clear delegation state after Task tool invocation."""
    state_dir = _get_state_dir()
    state_file = state_dir / "delegation_expected.json"
    try:
        state_file.unlink(missing_ok=True)
    except OSError:
        pass


@register_hook("delegation_prospector", priority=_PROSPECTOR_PRIORITY)
def delegation_prospector_hook(context: HookContext) -> HookResult:
    prompt = context.prompt
    is_opportunity, matched_pattern = _detect_delegation_opportunity(prompt)
    terminal_id = _get_terminal_id_from_context(context)
    _log_delegation_event("delegation_opportunity_detected" if is_opportunity else "no_opportunity", terminal_id, "", matched_pattern, prompt)
    if not is_opportunity:
        return HookResult.empty()
    # Write blocking state for PreToolUse_delegation_gate (terminal-scoped)
    _write_delegation_state(terminal_id, matched_pattern, prompt)
    tokens = len(_DELEGATION_ADVISORY.split())
    return HookResult(context=_DELEGATION_ADVISORY, tokens=tokens, priority=_PROSPECTOR_PRIORITY)


def clear_delegation_state() -> None:
    """Public API for PostToolUse hook to clear state after Task invocation."""
    _clear_delegation_state()
