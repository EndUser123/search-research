#!/usr/bin/env python3
"""
PreToolUse - Lean Router v2.2
=============================

Dispatches tool-specific hooks based on the current tool being called.
Enforces security gates, syntax validation, and loop detection.
"""

# =============================================================================
# DISPATCH CHAIN — this is what actually runs for PreToolUse
# =============================================================================
# Entry: HookImporter('P:/.claude/hooks').execute_hook('PreToolUse')
#        → loads THIS file → calls main()
#
# main() runs in order:
#   1. _pin_terminal_env()
#   2. _check_skill_first_gate()   ← THE skill-first gate. Nowhere else.
#   3. UNIVERSAL hooks (via run_hook subprocess):
#      - PreToolUse_path_validator.py
#      - PreToolUse/PreToolUse_skill_pattern_gate.py
#      - PreToolUse_risk_tier_gate.py
#      - PreToolUse_observe_before_act_gate.py
#   4. TOOL_HOOKS for the specific tool_name
#
# Files NOT in the dispatch chain (do not edit these expecting results):
#   - PreToolUse_skill_first_gate.py    (standalone, not called)
#   - PreToolUse_workflow_steps_gate.py  (deleted, was never in dispatch chain)
# =============================================================================

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))
hooks_lib = HOOKS_DIR / "__lib"
if str(hooks_lib) not in sys.path:
    sys.path.insert(0, str(hooks_lib))

try:
    from __lib.runtime_env import ledger_available as _ledger_available
except ImportError:

    def _ledger_available() -> bool:
        return False

from __lib.ttl_utils import is_expired as _is_expired


try:
    from shared_utils import resolve_session_id as _resolve_session_id_from_utils
except ImportError:

    def _resolve_session_id_from_utils(data: dict) -> str:
        """Fallback session-id resolver used only when shared_utils is unavailable."""
        for key in (
            "session_id",
            "sessionId",
            "conversation_id",
            "conversationId",
            "CLAUDE_SESSION_ID",
        ):
            value = data.get(key) if isinstance(data, dict) else None
            if isinstance(value, str) and value.strip():
                return value.strip()
        return os.environ.get("CLAUDE_SESSION_ID", "").strip()

try:
    from evidence_store import get_active_turn as get_active_evidence_turn
except ImportError:

    def get_active_evidence_turn(session_id: str, terminal_id: str) -> str | None:
        return None


LEDGER_AVAILABLE = _ledger_available()

try:
    from __lib.hook_ledger import append_event as append_ledger_event
except ImportError:

    def append_ledger_event(*args, **kwargs) -> bool:  # type: ignore[misc]
        return False


# Hooks that must never fail open.
CRITICAL_HOOKS = {
    "PreToolUse_path_validator.py",
    "PreToolUse_authorization_gate.py",
    "PreToolUse_deny_root_write.py",
    "PreToolUse_risk_tier_gate.py",
    "PreToolUse_protected_file_recovery_gate.py",  # Fail-closed: block edits on broken protected files
}

HOOK_TIMEOUTS = {
    "PreToolUse_file_existence_guard.py": 15.0,
    "pre/PreToolUse_tool_check.py": 5.0,
    "PreToolUse_verification_router.py": 15.0,
    "PreToolUse_authorization_gate.py": 30.0,  # Increased from 5s default - reads transcripts, queries CKS
}

# Content-based filters: hook only runs if command matches at least one pattern.
# Format: {hook_name: [list of regex patterns]}
# If a hook has no entry here, it runs for all commands (backward compatible).
#
# NOTE: Patterns use re.search() (substring match), so "python -c" matches.
# For windows_path_unicode_gate: matches python, python3, python2, py (Windows launcher)
HOOK_CONTENT_FILTERS: dict[str, list[str]] = {
    "PreToolUse_windows_path_unicode_gate.py": [
        r"python3?\s+-c",  # python -c, python3 -c (not python2 -c which is EOL)
        r"py\s+-c",  # Windows Python launcher
    ],
    "PreToolUse_dependency_verification_gate.py": [
        r"npm\s+install",
        r"pip\s+install",
        r"cargo\s+add",
    ],
    "PreToolUse_skill_script_path_gate.py": [
        r"python(?:3)?\s+[\"']?P:[/\\]",  # python "P:\..." or python P:/...
    ],
}

# =============================================================================
# SKILL-FIRST GATE (in-process, runs before all other hooks)
# =============================================================================
# When a slash command was detected by UserPromptSubmit but Skill() hasn't
# been called yet, block non-investigation tools. This prevents the LLM from
# substituting its own analysis instead of invoking the skill.
#
# Design: Uses session-scoped state files keyed by CLAUDE_SESSION_ID.
# Stale files from other sessions are ignored (not globbed).
# Expired files are cleaned up opportunistically.

# Tools allowed BEFORE Skill() is called.
# TIGHT: Only Skill itself and harmless metadata tools.
# Read/Grep/Glob/Edit/Write are NOT allowed — the LLM must call Skill() first,
# not read the SKILL.md and improvise its own version.
_SKILL_FIRST_ALLOWED = {"Skill", "AskUserQuestion", "TodoWrite"}
_SKILL_FIRST_MODES = {"off", "monitor", "soft_block", "hard_block"}
_SKILL_FIRST_LOG = HOOKS_DIR / "logs" / "skill_first_enforcement.jsonl"
_STALE_TERMINAL_INTENT_SECONDS = 15 * 60
# Hard TTL: intent files older than this are discarded unconditionally.
# Covers crash/force-kill where SessionEnd never fires, and abandoned slash commands.
#
# Semantic: this file lives for ONE model turn (user hits Enter → model calls Skill()).
# That round-trip is measured in seconds, not minutes. 90s is generous for any
# realistic slow-model / heavy-hook scenario while still recovering quickly from
# crashes. Override with SKILL_FIRST_INTENT_TTL_SECONDS env var if needed.


def _validate_intent_ttl(value: str | None) -> int:
    """Validate SKILL_FIRST_INTENT_TTL_SECONDS environment variable.

    Args:
        value: Environment variable value (string from os.environ.get()) or None

    Returns:
        Validated TTL in seconds (default 90 if invalid, actual value if valid)

    Validation rules:
    - None (unset) → 90 (default)
    - Empty string → 90 (treated as unset)
    - Negative values → 90 (invalid)
    - Zero → 90 (invalid, must be positive)
    - Non-numeric strings → 90 (invalid)
    - Very large values (>86400, 1 day) → accepted but WARNING logged
    - Valid positive integers → accepted as-is
    """
    import logging

    logger = logging.getLogger(__name__)

    DEFAULT_TTL = 90
    LARGE_TTL_THRESHOLD = 86400  # 1 day in seconds

    # None or empty string → use default
    if value is None or value == "":
        return DEFAULT_TTL

    # Try to parse as integer
    try:
        ttl = int(value)
    except (ValueError, TypeError):
        # Non-numeric string
        return DEFAULT_TTL

    # Negative or zero → invalid, use default
    if ttl <= 0:
        return DEFAULT_TTL

    # Very large TTL → accept but log warning
    if ttl > LARGE_TTL_THRESHOLD:
        logger.warning(
            f"Unusually large SKILL_FIRST_INTENT_TTL_SECONDS value: {ttl} seconds "
            f"({ttl // 3600} hours). This may cause stale intent files to persist longer "
            f"than expected. Consider using a shorter TTL (default: {DEFAULT_TTL}s)."
        )
        return ttl

    # Valid positive integer
    return ttl


_INTENT_TTL_SECONDS = _validate_intent_ttl(os.environ.get("SKILL_FIRST_INTENT_TTL_SECONDS"))


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _skill_first_mode_pretool() -> str:
    if not _env_bool("ENFORCE_SKILL_FIRST_PRETOOLUSE", default=False):
        return "off"
    mode = str(os.environ.get("SKILL_FIRST_MODE", "off")).strip().lower()
    if mode not in _SKILL_FIRST_MODES:
        return "off"
    return mode


def _log_skill_first_event(
    event: str, session_id: str, tool_name: str, skill_name: str, mode: str
) -> None:
    if not _env_bool("SKILL_FIRST_LOGGING_ENABLED", default=True):
        return
    payload = {
        "timestamp": time.time(),
        "hook": "PreToolUse",
        "event": event,
        "reason_code": "E_SKILL_FIRST_PENDING_INTENT",
        "session_id": session_id or "",
        "tool_name": tool_name or "",
        "skill_name": skill_name or "",
        "mode": mode,
    }
    line = json.dumps(payload, ensure_ascii=True) + "\n"
    candidates = [
        _SKILL_FIRST_LOG,
        Path(os.environ.get("TEMP", "/tmp"))
        / "claude_hooks"
        / "logs"
        / "skill_first_enforcement.jsonl",
    ]
    for path in candidates:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line)
            return
        except OSError:
            continue


def _safe_id(value: str) -> str:
    """Sanitize a string for use in filenames."""
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _parse_iso_timestamp(value: object) -> datetime | None:
    """Parse ISO 8601 timestamps emitted by the slash-intent writer."""
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _terminal_scoped_intent_is_stale(intent: dict) -> bool:
    """Return True when a terminal-scoped intent is old enough to ignore."""
    age_limit = _STALE_TERMINAL_INTENT_SECONDS
    raw_limit = os.environ.get("SKILL_FIRST_STALE_INTENT_SECONDS", "").strip()
    if raw_limit:
        try:
            age_limit = max(0, int(raw_limit))
        except ValueError:
            age_limit = _STALE_TERMINAL_INTENT_SECONDS

    timestamp = _parse_iso_timestamp(intent.get("timestamp"))
    if timestamp is None:
        return False

    now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
    return (now - timestamp).total_seconds() > age_limit


def _resolve_session_id(data: dict) -> str:
    """Resolve session id from hook payload first, then environment.

    Delegates to shared_utils.resolve_session_id() for consistent resolution logic
    across all routers and hooks.

    Must match the resolution logic in UserPromptSubmit/skill_enforcer.py
    so that intent files written by skill_enforcer can be found here.
    """
    return _resolve_session_id_from_utils(data)


def _is_mcp_tool(tool_name: str) -> bool:
    """Return True when the tool call is an MCP tool invocation."""
    return isinstance(tool_name, str) and tool_name.startswith("mcp__")


def _write_grounded_artifact(data: dict, artifact: dict) -> str:
    """Write grounded artifact to terminal-scoped and session-scoped state file."""
    session_id = _resolve_session_id(data)
    safe_session = _safe_id(session_id or "unknown")

    terminal_id = str(
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    ).strip()
    safe_terminal = _safe_id(terminal_id or "unknown")

    state_dir = HOOKS_DIR / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    artifact_path = state_dir / f"grounded_artifact_{safe_terminal}_{safe_session}.json"
    artifact_path.write_text(json.dumps(artifact, ensure_ascii=False), encoding="utf-8")
    return str(artifact_path)


def _degraded_state_paths(session_id: str, terminal_id: str = "") -> tuple[Path, Path]:
    safe_session = _safe_id(session_id or "unknown")
    safe_terminal = _safe_id(terminal_id or "unknown")
    state_dir = HOOKS_DIR / "state"
    fallback_dir = Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state"
    return (
        state_dir / f"pretool_degraded_{safe_terminal}_{safe_session}.json",
        fallback_dir / f"pretool_degraded_{safe_terminal}_{safe_session}.json",
    )


def _record_degraded_mode_once(data: dict, hook_name: str, reason: str) -> None:
    """Record degraded safety mode once per session and emit one concise warning."""
    session_id = _resolve_session_id(data) or "unknown"
    terminal_id = str(
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    ).strip()

    payload = {
        "session_id": session_id,
        "terminal_id": terminal_id,
        "hook": hook_name,
        "reason": reason,
    }

    primary, fallback = _degraded_state_paths(session_id, terminal_id)
    for marker_path in (primary, fallback):
        try:
            marker_path.parent.mkdir(parents=True, exist_ok=True)
            if marker_path.exists():
                return
            marker_path.write_text(json.dumps(payload, ensure_ascii=True), encoding="utf-8")
            # Claude Code treats stderr as hook error - silence this
            # print(
            #     f"⚠️ SAFETY DEGRADED: {hook_name} unavailable ({reason}). "
            #     "Continuing fail-open for this session.",
            #     file=sys.stderr,
            # )
            return
        except Exception:
            continue


def _pin_terminal_env(data: dict) -> None:
    """Resolve and pin terminal id for this hook process before dispatch.

    Ensures subprocess hooks inherit a stable
    CLAUDE_TERMINAL_ID in multi-terminal environments.
    """
    # Respect explicit env if already present.
    if os.environ.get("CLAUDE_TERMINAL_ID", "").strip():
        data.setdefault("terminal_id", os.environ.get("CLAUDE_TERMINAL_ID", ""))
        return
    try:
        sys.path.insert(0, str(HOOKS_DIR))
        from __lib.terminal_detection import detect_terminal_id

        tid = (detect_terminal_id() or "").strip()
        if tid:
            os.environ["CLAUDE_TERMINAL_ID"] = tid
            data.setdefault("terminal_id", tid)
    except Exception:
        # Terminal pinning is best-effort; never block on diagnostics.
        return


def _check_skill_first_gate(data: dict) -> dict | None:
    """Block tools when a slash command is pending but Skill hasn't been called.

    Uses session-specific file lookup (not glob) to avoid cross-session interference.
    Returns None to allow, or {"decision": "block", "reason": "..."} to block.
    """
    tool_name = data.get("tool_name", "")
    mode = _skill_first_mode_pretool()

    # Respect the mode setting: "off" means no blocking
    if mode == "off":
        return None

    # Always allow investigation and Skill tool itself
    if tool_name in _SKILL_FIRST_ALLOWED:
        return None

    # EXEMPTION: Allow editing SKILL.md files — legitimate documentation work
    if tool_name in ("Edit", "Write", "MultiEdit"):
        file_path = data.get("tool_input", {}).get("file_path", "")
        if isinstance(file_path, str) and re.search(r"\.claude/skills/[^/]+/SKILL\.md$", file_path):
            # Allow SKILL.md edits even when slash command is pending
            return None

    # Session id is helpful for stale-intent cleanup, but the current source of
    # truth is the terminal-scoped pending intent file. Do not disable the gate
    # just because session_id is absent from the payload.
    session_id = _resolve_session_id(data)
    terminal_id = str(
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    ).strip()
    if not session_id and not terminal_id:
        return None

    safe_session = _safe_id(session_id or "unknown")

    # Resolve terminal_id for multi-terminal safety
    safe_terminal = _safe_id(terminal_id or "unknown")

    # Check if there's a pending command intent for THIS session
    # No TTL — file is deleted when Skill() succeeds (happy path),
    # or by session_data_retention.py at next boot (orphan path).
    #
    # NOTE: UserPromptSubmit (skill_enforcer.py) writes terminal-scoped files.
    # Current format (TASK-005+): terminals/{terminal_id}/pending_command_intent.json
    # Legacy format:              pending_command_intent_{terminal_id}.json
    # Both are checked below to support files written by either version.
    state_dir = HOOKS_DIR / "state"
    fallback_dir = Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state"

    intent_file = None

    # Primary: new per-terminal directory format written by skill_enforcer.py (TASK-005+)
    # Format: state/terminals/{terminal_id}/pending_command_intent.json
    if terminal_id:
        for base in (state_dir, fallback_dir):
            candidate = base / "terminals" / terminal_id / "pending_command_intent.json"
            if candidate.exists():
                intent_file = candidate
                break

        # Fallback: try dash-stripped terminal ID (handles normalization drift from
        # WT_SESSION format changes). Old directories were created with dashes removed.
        if not intent_file and terminal_id.startswith("console_"):
            hex_part = terminal_id[8:]  # strip "console_" prefix
            stripped = f"console_{hex_part.replace('-', '')}"
            if stripped != terminal_id:
                for base in (state_dir, fallback_dir):
                    candidate = base / "terminals" / stripped / "pending_command_intent.json"
                    if candidate.exists():
                        intent_file = candidate
                        break

    # Secondary: flat terminal-scoped format (legacy, written before TASK-005)
    # Format: state/pending_command_intent_{terminal_id}.json
    if not intent_file:
        for base in (state_dir, fallback_dir):
            candidate = base / f"pending_command_intent_{safe_terminal}.json"
            if candidate.exists():
                intent_file = candidate
                break

    # Fallback: legacy session-scoped format (for backwards compatibility)
    if not intent_file:
        for base in (state_dir, fallback_dir):
            candidate = base / f"pending_command_intent_{safe_terminal}_{safe_session}.json"
            if candidate.exists():
                intent_file = candidate
                break

    if not intent_file:
        return None

    try:
        intent = json.loads(intent_file.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "decision": "block",
            "reason": (
                "⛔ SKILL-FIRST GATE: Pending slash-command intent exists but cannot be read.\n\n"
                f"intent_file={intent_file}\n"
                f"error={type(exc).__name__}: {exc}\n\n"
                "Run Skill(...) first to re-establish execution state."
            ),
            "blocking_hook": "PreToolUse.py:skill_first_gate",
        }

    skill_name = str(intent.get("skill", "")).strip()
    if not skill_name:
        return {
            "decision": "block",
            "reason": (
                "⛔ SKILL-FIRST GATE: Pending slash-command intent is malformed (missing skill).\n\n"
                f"intent_file={intent_file}\n\n"
                "Run Skill(...) first to re-establish execution state."
            ),
            "blocking_hook": "PreToolUse.py:skill_first_gate",
        }

    # Hard TTL check — discard intent regardless of session/terminal match.
    # Protects against crash/force-kill (no SessionEnd), abandoned slash commands,
    # and same-session files that outlive their originating turn.
    # Uses created_at (epoch) written by skill_enforcer.py; falls back to
    # ISO timestamp for files written before this field was added.
    _intent_created_at: float = 0.0
    if "created_at" in intent:
        try:
            _intent_created_at = float(intent["created_at"])
        except (TypeError, ValueError):
            pass
    elif "timestamp" in intent:
        try:
            _intent_created_at = datetime.fromisoformat(
                str(intent["timestamp"]).replace("Z", "+00:00")
            ).timestamp()
        except (TypeError, ValueError):
            pass
    if _intent_created_at and _is_expired(_intent_created_at, _INTENT_TTL_SECONDS):
        intent_file.unlink(missing_ok=True)
        return None

    # Terminal-scoped intent files are intentionally compact-proof, but they can
    # linger after the originating session is gone. Ignore old mismatched-session
    # intents so they do not block unrelated later work in the same terminal.
    terminal_scoped_name = f"pending_command_intent_{safe_terminal}.json"
    is_new_terminal_scoped_intent = (
        intent_file.name == "pending_command_intent.json"
        and intent_file.parent.name == (terminal_id or intent_file.parent.name)
        and intent_file.parent.parent.name == "terminals"
    )
    intent_session_id = str(intent.get("session_id", "")).strip()
    intent_terminal_id = str(intent.get("terminal_id", "")).strip()
    if intent_file.name == terminal_scoped_name or is_new_terminal_scoped_intent:
        if intent_terminal_id and _safe_id(intent_terminal_id) != safe_terminal:
            intent_file.unlink(missing_ok=True)
            return None
        if (
            intent_session_id
            and intent_session_id != session_id
            and _terminal_scoped_intent_is_stale(intent)
        ):
            intent_file.unlink(missing_ok=True)
            return None

    def _skill_first_reason(body: str) -> str:
        return (
            "[WORKFLOW_BLOCK_NOT_HOOK_CRASH]\n"
            "This is an intentional workflow block from the skill-first gate, not a broken hook.\n\n"
            f"{body}"
        )

    # Explicit MCP handling: always require Skill() first for slash intents.
    # This avoids opaque downstream failures for MCP tool names.
    if _is_mcp_tool(tool_name):
        _log_skill_first_event("mcp_before_skill", session_id, tool_name, skill_name, mode)
        if mode == "monitor":
            return None
        return {
            "decision": "block",
            "reason": _skill_first_reason(
                f"[E_SKILL_FIRST_PENDING_INTENT]\n"
                f"⛔ SKILL-FIRST GATE: You typed /{skill_name} and attempted MCP tool "
                f"'{tool_name}' before loading the skill.\n\n"
                f'Your FIRST action must be:  Skill(skill="{skill_name}")\n\n'
                "Do not run MCP tools before Skill(...) is loaded for this slash command."
            ),
            "blocking_hook": "PreToolUse.py:skill_first_gate",
        }

    # Check if the skill has been loaded via Skill tool.
    # Fail CLOSED when state lookup errors occur (permission/path issues).
    skill_loaded = False
    try:
        sys.path.insert(0, str(HOOKS_DIR))
        from skill_execution_state import read_pending_state

        state = read_pending_state()
        if state and str(state.get("skill", "")).lower() == skill_name.lower():
            skill_loaded = True
    except Exception:
        # skill_execution_state unavailable — fail CLOSED (skill_loaded stays False →
        # this tool call is blocked). That is intentional: if we can't confirm the
        # skill was loaded we should not allow arbitrary tool use.
        #
        # Permanent-block prevention relies on the TOCTOU cleanup loop that runs
        # earlier in main() when tool_name == "Skill": it deletes the intent file
        # immediately when Skill() is called, so subsequent tool calls won't reach
        # this branch at all (intent_file lookup above returns None → gate is skipped).
        skill_loaded = False

    if skill_loaded:
        # Skill was loaded — clear intent and allow
        intent_file.unlink(missing_ok=True)
        return None

    # BLOCK: Slash command pending but Skill() not called yet
    _log_skill_first_event("tool_before_skill", session_id, tool_name, skill_name, mode)
    if mode == "monitor":
        return None
    return {
        "decision": "block",
        "reason": _skill_first_reason(
            f"[E_SKILL_FIRST_PENDING_INTENT]\n"
            f'⛔ SKILL-FIRST GATE: You typed /{skill_name} but haven\'t called Skill("{skill_name}") yet.\n\n'
            f'Your FIRST action must be:  Skill(skill="{skill_name}")\n\n'
            f"Do NOT analyze the codebase, run scripts, or provide your own assessment.\n"
            f"Do NOT bypass this gate by outputting inline analysis text without calling Skill(...).\n"
            f'Call Skill("{skill_name}") to load the skill, then follow its instructions.'
        ),
        "blocking_hook": "PreToolUse.py:skill_first_gate",
    }


# Hooks that run for ALL tool types
#
# INVARIANT 3 WIRING (2026-05-05):
#   PreToolUse_skill_pattern_gate.py REMOVED from this list.
#   execution_hooks.py (skill-guard subprocess via hooks.json) is the SOLE
#   PreToolUse contract authority for /skill-name runs.
#   The legacy gate ran before the subprocess, causing double-gating with conflicting state.
#   It is now completely removed from the dispatch chain.
UNIVERSAL = [
    "PreToolUse_path_validator.py",
    "PreToolUse_domain_tool_router.py",  # NEW 2026-03-21: Advisory domain tool suggestions
    "PreToolUse_discovery_tracker.py",  # ADR-00X: Tracks discovery tool usage for discovery-first enforcement (2026-04-09)
    "PreToolUse_risk_tier_gate.py",
    "PreToolUse_observe_before_act_gate.py",
    "PreToolUse_arch_first_enforcer.py",  # Enforce arch-first workflow (2026-03-16)
    "PreToolUse_ownership_colocation_gate.py",  # Block writes to shared-infra paths without consumer verification (2026-03-19)
    "PreToolUse_session_id_capture.py",  # Session ID capture for git integration (AIR Auditor CHANGE-001)
    "PreToolUse_context_sufficiency_gate.py",  # Skill autonomy classification (ADR-20260329 CHANGE-002)
    "PreToolUse_skill_question_gate.py",  # One-question-max enforcement (ADR-20260329 CHANGE-003)
    "PreToolUse_delegation_gate.py",  # Block non-Task tools when delegation_expected state is set (2026-05-11)
    "PreToolUse_user_delegation_gate.py",  # Block ask-user when investigation insufficient for diagnostic turns (2026-05-11)
    # NOTE: skill_metadata_advisory moved to UserPromptSubmit_modules/cognitive_guardrails.py (2026-04-07)
]

# Legacy top-level PreToolUse entries are routed here now so Claude only has to
# spawn one Bash hook for PreToolUse instead of one per sub-hook.
#
# NOTE: PreToolUse_skill_pattern_gate.py was REMOVED from UNIVERSAL.
# It has been replaced by execution_hooks.py (skill-guard subprocess in hooks.json)
# which is the SOLE contract authority for /skill-name runs per INVARIANT 3.
# The legacy gate is kept in this list as documentation of its former position
# but is COMMENTED OUT to prevent double-gating. Do NOT uncomment.
COMPAT_POST_ROUTER_HOOKS = [
    "PreToolUse_file_existence_guard.py",
    "pre/PreToolUse_tool_check.py",
    "PreToolUse_verification_router.py",
    # "PreToolUse/PreToolUse_skill_pattern_gate.py",  # REMOVED - see note above
]

# Mutation tools rely on path_validator (UNIVERSAL) for path protection.
# deny_root_write removed from Write/Edit/MultiEdit to reduce duplicate blocking.
# External consent checks skipped for existing files (accepted tradeoff).
# Hooks by tool type
TOOL_HOOKS = {
    "Write": [
        "PreToolUse_win32_path_gate.py",  # Blocks backslash paths that cause silent failures on Windows MINGW
        "PreToolUse_directory_policy.py",
        "PreToolUse_type_validator.py",  # Blocks .py files at workspace root (type mismatch prevention)
        "PreToolUse_parent_directory_creator.py",  # Creates parent dirs before Write/Edit to prevent silent failure bug
        "PreToolUse_syntax_gate.py",
        "PreToolUse_python_import_gate.py",
        "PreToolUse_import_deletion_guard.py",  # Blocks overwriting existing imports without symbol search
        "recursive_failure_detector.py",
        "PreToolUse_git_safety.py",
        "PreToolUse_require_plan_for_features.py",
        "PreToolUse_settings_backup.py",
        "PreToolUse_implementation_default_gate.py",  # Flipped default: block Edit/Write unless explicit trigger
        "PreToolUse_investigation_gate.py",
        "PreToolUse_tdd95_gate.py",  # TDD enforcement
        "PreToolUse_protected_file_recovery_gate.py",  # Recovery lockout: block Edit/Write on broken protected files
    ],
    "Edit": [
        "PreToolUse_win32_path_gate.py",  # Blocks backslash paths that cause silent failures on Windows MINGW
        "PreToolUse_directory_policy.py",
        "PreToolUse_type_validator.py",  # Blocks .py files at workspace root (type mismatch prevention)
        "PreToolUse_syntax_gate.py",  # Validates Python syntax before Edit operations
        "PreToolUse_python_import_gate.py",
        "PreToolUse_import_deletion_guard.py",  # Blocks import removal without prior symbol grep
        "recursive_failure_detector.py",
        "PreToolUse_git_safety.py",
        "PreToolUse_require_plan_for_features.py",
        "PreToolUse_settings_backup.py",
        "PreToolUse_implementation_default_gate.py",  # Flipped default: block Edit/Write unless explicit trigger
        "PreToolUse_investigation_gate.py",
        "PreToolUse_tdd95_gate.py",  # TDD enforcement
        "PreToolUse_protected_file_recovery_gate.py",  # Recovery lockout: block Edit/Write on broken protected files
    ],
    "MultiEdit": [
        "PreToolUse_win32_path_gate.py",  # Blocks backslash paths that cause silent failures on Windows MINGW
        "PreToolUse_directory_policy.py",
        "PreToolUse_import_deletion_guard.py",  # Blocks import removal across batched edits
    ],
    "Glob": [
        "PreToolUse_skill_dir_gate.py",  # Phase 2: block unscoped Glob in wrong skill dir
    ],
    "Grep": [
        "PreToolUse_skill_dir_gate.py",  # Phase 2: block unscoped Grep in wrong skill dir
    ],
    "Bash": [
        "PreToolUse_git_state_capture.py",  # Capture git state BEFORE command (cross-agent isolation)
        "PreToolUse_skill_script_path_gate.py",  # Block stale P:\ skill script paths before execution (RC3)
        "PreToolUse_bash_syntax_validator.py",
        "PreToolUse_windows_path_unicode_gate.py",  # Detect Python -c with unescaped Windows paths
        "PreToolUse_directory_policy.py",
        "PreToolUse_destructive_git_guard.py",
        "PreToolUse_git_remote_check_order_guard.py",  # Require local HEAD check before origin/* inspection
        "PreToolUse_authorization_gate.py",
        "PreToolUse_dependency_verification_gate.py",
        "PreToolUse_evidence_hierarchy_gate.py",  # Enforce local-first: block external fetch if local evidence exists
        "PreToolUse_bulk_delete_gate.py",
        "PreToolUse_repo_visibility_guard.py",  # Blocks P:\ drive repos from being made public
        "recursive_failure_detector.py",
        "PreToolUse_command_intent_gate.py",
        "PreToolUse_pytest_timeout_guard.py",  # CRITICAL: Blocks pytest without --timeout (prevents computer hangs)
        "PreToolUse_git_commit_test_gate.py",  # HIGH: Blocks commit if tests fail (prevents data loss)
        "PreToolUse_referent_scope_gate.py",  # Blocks off-topic investigation when user listed specific entities
        "PreToolUse_git_auto_stage.py",  # Auto-stage tracked files before deletion/move commands
    ],
    "Task": [
        "PreToolUse_task_self_doc_gate.py",
        "PreToolUse_authorization_gate.py",
    ],
    # MCP full-read guard: blocks large-payload URL patterns before the call is made
    # (tavily_extract not listed — advisory handled post-call by PostToolUse.py bloat detection)
    "mcp__web-reader__webReader": [
        "PreToolUse_mcp_full_read_guard.py",
    ],
    "WebFetch": [
        "PreToolUse_evidence_hierarchy_gate.py",  # Block if local evidence exists for same topic
    ],
    "WebSearch": [
        "PreToolUse_evidence_hierarchy_gate.py",  # Block if local evidence exists for same topic
    ],
}

# Map hook filenames to in-process functions for speed
try:
    sys.path.insert(0, str(HOOKS_DIR / "__lib"))

    # Plugin import path for skill-guard hooks (hardcoded — CLAUDE_PLUGIN_ROOT is per-plugin, not usable here)
    _PLUGIN_SRC = Path("P:/packages/skill-guard/src")
    if _PLUGIN_SRC.exists():
        sys.path.insert(1, str(_PLUGIN_SRC))  # position 1 preserves __lib at position 0

    import pre_tool_use_logic
    import PreToolUse_bash_syntax_validator
    import PreToolUse_bulk_delete_gate
    import PreToolUse_dependency_verification_gate
    import PreToolUse_destructive_git_guard
    import PreToolUse_directory_policy
    import PreToolUse_evidence_hierarchy_gate
    import PreToolUse_git_remote_check_order_guard
    import PreToolUse_git_auto_stage
    import PreToolUse_path_validator
    import PreToolUse_task_self_doc_gate
    import PreToolUse_protected_file_recovery_gate

    # skill-guard hooks imported from plugin (single source of truth)
    from skill_guard.PreToolUse.PreToolUse_import_deletion_guard import run as _import_deletion_run
    from skill_guard.PreToolUse.PreToolUse_skill_script_path_gate import run as _skill_script_path_run
    from skill_guard.PreToolUse.PreToolUse_skill_dir_gate import run as _skill_dir_gate_run
    from skill_guard.PreToolUse.PreToolUse_skill_question_gate import run as _skill_question_gate_run
    from skill_guard.PreToolUse.PreToolUse_context_sufficiency_gate import run as _context_sufficiency_run
    # NOTE: PreToolUse_skill_pattern_gate.py REMOVED from IN_PROCESS_HOOKS.
    # execution_hooks.py (skill-guard subprocess via hooks.json) is the sole contract gate.
    from artifact_grounder import ground_blocked_command, ground_git_safety_block
    from pretooluse_observability import (
        append_jsonl as append_observability_jsonl,
    )
    from pretooluse_observability import (
        build_pretooluse_block_entry,
    )

    IN_PROCESS_HOOKS = {
        "PreToolUse_syntax_gate.py": pre_tool_use_logic.check_syntax,
        "recursive_failure_detector.py": pre_tool_use_logic.check_recursive_failure,
        "PreToolUse_bash_syntax_validator.py": PreToolUse_bash_syntax_validator.run,
        "PreToolUse_path_validator.py": PreToolUse_path_validator.run,
        "PreToolUse_directory_policy.py": PreToolUse_directory_policy.run,
        "PreToolUse_bulk_delete_gate.py": PreToolUse_bulk_delete_gate.run,
        "PreToolUse_dependency_verification_gate.py": PreToolUse_dependency_verification_gate.run,
        "PreToolUse_destructive_git_guard.py": PreToolUse_destructive_git_guard.run,
        "PreToolUse_evidence_hierarchy_gate.py": PreToolUse_evidence_hierarchy_gate.run,
        "PreToolUse_git_remote_check_order_guard.py": PreToolUse_git_remote_check_order_guard.run,
        "PreToolUse_git_auto_stage.py": PreToolUse_git_auto_stage.run,
        "PreToolUse_import_deletion_guard.py": _import_deletion_run,
        "PreToolUse_skill_script_path_gate.py": _skill_script_path_run,
        "PreToolUse_skill_dir_gate.py": _skill_dir_gate_run,
        "PreToolUse_skill_question_gate.py": _skill_question_gate_run,
        "PreToolUse_context_sufficiency_gate.py": _context_sufficiency_run,
        # PreToolUse_skill_pattern_gate.py REMOVED - execution_hooks.py is sole contract gate
        "PreToolUse_task_self_doc_gate.py": PreToolUse_task_self_doc_gate.run,
        "PreToolUse_protected_file_recovery_gate.py": PreToolUse_protected_file_recovery_gate.run,
        "check_external_path_consent": pre_tool_use_logic.check_external_path_consent,
        "PreToolUse_protected_file_recovery_gate.py": PreToolUse_protected_file_recovery_gate.run,
    }
except ImportError:
    # Claude Code treats stderr as hook error - silence this
    # print(f"⚠️ Optimization Warning: Could not import in-process hooks: {e}", file=sys.stderr)
    IN_PROCESS_HOOKS = {}


def _log_pretooluse_block_event(
    data: dict,
    *,
    blocking_hook: str,
    reason: object,
    event_kind: str,
    active_turn_id: str = "",
    source_hook: str | None = None,
    child_exit_code: int | None = None,
    raw_stdout: object = "",
    raw_stderr: object = "",
    artifact_path: str = "",
) -> None:
    try:
        entry = build_pretooluse_block_entry(
            data,
            blocking_hook=blocking_hook,
            reason=reason,
            event_kind=event_kind,
            source_hook=source_hook,
            child_exit_code=child_exit_code,
            raw_stdout=raw_stdout,
            raw_stderr=raw_stderr,
            artifact_path=artifact_path,
            active_turn_id=active_turn_id,
        )
        append_observability_jsonl(
            HOOKS_DIR / "logs" / "diagnostics" / "pretooluse_blocks.jsonl",
            entry,
        )
    except Exception:
        pass


def run_hook(hook_name: str, data: dict) -> dict | None:
    # 0. Content-based filter: skip if command doesn't match hook's trigger patterns
    if hook_name in HOOK_CONTENT_FILTERS:
        command = data.get("tool_input", {}).get("command", "")
        patterns = HOOK_CONTENT_FILTERS[hook_name]
        if not any(re.search(p, command) for p in patterns):
            # Log filter skip for debugging (COGN-001: invisible behavior)
            try:
                import time as _t

                _diag_dir = HOOKS_DIR / "logs" / "diagnostics"
                _diag_dir.mkdir(parents=True, exist_ok=True)
                with open(_diag_dir / "content_filter_skips.jsonl", "a", encoding="utf-8") as _f:
                    _f.write(
                        json.dumps(
                            {
                                "ts": _t.strftime("%Y-%m-%dT%H:%M:%S"),
                                "hook": hook_name,
                                "command_preview": command[:80] if command else "",
                                "patterns": patterns,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
            except Exception:
                pass  # Logging failure is non-fatal
            return None  # Content not relevant to this hook

    # 1. Try In-Process Execution (Ultra-fast)
    if hook_name in IN_PROCESS_HOOKS:
        try:
            res = IN_PROCESS_HOOKS[hook_name](data)
            if res == "subprocess":
                pass  # Force subprocess fallback for complex logic
            else:
                return res
        except Exception as e:
            # DIAGNOSTIC: Log in-process hook failures
            try:
                _diag_dir = HOOKS_DIR / "logs" / "diagnostics"
                _diag_dir.mkdir(parents=True, exist_ok=True)
                import time as _t

                with open(_diag_dir / "in_process_errors.jsonl", "a", encoding="utf-8") as _df:
                    _df.write(
                        json.dumps(
                            {
                                "ts": _t.strftime("%Y-%m-%dT%H:%M:%S"),
                                "hook": hook_name,
                                "error": f"{type(e).__name__}: {str(e)}",
                                "command": data.get("tool_input", {}).get("command", "")[:200],
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass  # Never block on diagnostic logging
            # Claude Code treats stderr as hook error - silence this
            # print(f"In-process error {hook_name}: {e}", file=sys.stderr)
            # Fall back to subprocess on failure
            pass

    # 2. Subprocess Execution (Standard isolation)
    try:
        hook_path = HOOKS_DIR / hook_name
        if not hook_path.exists():
            if hook_name in CRITICAL_HOOKS:
                return {
                    "decision": "block",
                    "reason": f"Critical safety hook missing: {hook_name}",
                }
            # Warn if a non-critical hook is missing
            _record_degraded_mode_once(data, hook_name, "missing_file")
            # Claude Code treats stderr as hook error - silence this
            # print(f"⚠️ SYSTEM WARNING: Hook file '{hook_name}' not found. Security check skipped.", file=sys.stderr)
            return None

        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(data).encode(),
            capture_output=True,
            timeout=HOOK_TIMEOUTS.get(hook_name, 5.0),
            creationflags=creation_flags,
        )

        out = result.stdout.decode(errors="replace").strip()

        # Some hooks return decision JSON without using exit code 2.
        if out.startswith("{"):
            try:
                payload = json.loads(out)
                # Check for both "decision": "block" and "block": True formats
                is_block = (
                    payload.get("decision") == "block"
                    or payload.get("block") is True
                    or payload.get("continue") is False
                    or (isinstance(payload.get("hookSpecificOutput"), dict)
                        and payload["hookSpecificOutput"].get("permissionDecision") == "deny")
                )

                # FIXED: Preserve hookSpecificOutput for non-blocking hooks (e.g., advisories)
                has_advisory = "hookSpecificOutput" in payload and "advisory" in payload["hookSpecificOutput"]

                if is_block:
                    # Extract blocking_hook if provided by child hook, otherwise use hook_name
                    if "blocking_hook" not in payload:
                        payload["blocking_hook"] = hook_name
                    _log_pretooluse_block_event(
                        data,
                        blocking_hook=str(payload.get("blocking_hook", hook_name)),
                        reason=payload.get("reason") or payload.get("message") or out,
                        event_kind="child_hook_block",
                        source_hook=hook_name,
                        child_exit_code=result.returncode,
                        raw_stdout=out,
                        raw_stderr=result.stderr.decode(errors="replace").strip()
                        if result.stderr
                        else "",
                    )
                    return payload

                # NEW: Return non-blocking results with hookSpecificOutput preserved
                if has_advisory or payload.get("decision") == "modify":
                    return payload
            except Exception:
                pass

        # Exit code 2 = intentional block. Exit code 1 = crash/error → fail-open (not a block).
        if result.returncode == 2:
            try:
                if out:
                    _log_pretooluse_block_event(
                        data,
                        blocking_hook=hook_name,
                        reason=out,
                        event_kind="child_hook_block",
                        source_hook=hook_name,
                        child_exit_code=result.returncode,
                        raw_stdout=out,
                        raw_stderr=result.stderr.decode(errors="replace").strip()
                        if result.stderr
                        else "",
                    )
                    return {"decision": "block", "reason": out, "blocking_hook": hook_name}
                stderr_content = result.stderr.decode(errors="replace").strip()
                if stderr_content:
                    _log_pretooluse_block_event(
                        data,
                        blocking_hook=hook_name,
                        reason=stderr_content,
                        event_kind="child_hook_block",
                        source_hook=hook_name,
                        child_exit_code=result.returncode,
                        raw_stdout=out,
                        raw_stderr=stderr_content,
                    )
                    return {
                        "decision": "block",
                        "reason": stderr_content,
                        "blocking_hook": hook_name,
                    }

                # Clean block with no stderr - the hook blocked but didn't provide a reason.
                # Build the most descriptive message possible from available context.
                tool_name = data.get("tool_name", "unknown action")
                tool_input = data.get("tool_input", {})
                cwd = data.get("cwd", "")

                # Build context string with what we know
                context_parts = []
                if cwd:
                    context_parts.append(f"cwd={cwd}")
                context_parts.append(f"hook={hook_name}")

                context_str = ", ".join(context_parts)

                if tool_name == "Bash":
                    command = tool_input.get("command", "")
                    if command:
                        command_preview = command[:100]
                        if len(command) > 100:
                            command_preview += "..."
                        action_desc = (
                            f"⛔ BLOCKED: Bash command rejected by {hook_name}\n"
                            f"   Command: {command_preview}\n"
                            f"   {context_str}\n"
                            f"   Reason: The hook blocked this action but did not print a description to stderr.\n"
                            f"   Fix: The hook script should print a descriptive error to stderr before exiting with code 2."
                        )
                    else:
                        action_desc = (
                            f"⛔ BLOCKED: Bash command rejected by {hook_name}\n"
                            f"   {context_str}\n"
                            f"   Reason: The hook blocked this action but did not print a description to stderr."
                        )
                elif tool_name in ("Write", "Edit"):
                    file_path = tool_input.get("file_path", "")
                    if file_path:
                        action_desc = (
                            f"⛔ BLOCKED: {tool_name} operation rejected by {hook_name}\n"
                            f"   File: {file_path}\n"
                            f"   {context_str}\n"
                            f"   Reason: The hook blocked this action but did not print a description to stderr.\n"
                            f"   Fix: The hook script should print a descriptive error to stderr before exiting with code 2."
                        )
                    else:
                        action_desc = (
                            f"⛔ BLOCKED: {tool_name} operation rejected by {hook_name}\n"
                            f"   {context_str}\n"
                            f"   Reason: The hook blocked this action but did not print a description to stderr."
                        )
                else:
                    action_desc = (
                        f"⛔ BLOCKED: {tool_name} rejected by {hook_name}\n"
                        f"   {context_str}\n"
                        f"   Reason: The hook blocked this action but did not print a description to stderr.\n"
                        f"   Fix: The hook script should print a descriptive error to stderr before exiting with code 2."
                    )

                return {
                    "decision": "block",
                    "reason": action_desc,
                    "blocking_hook": hook_name,
                }

            except Exception:
                stderr_content = result.stderr.decode(errors="replace").strip()
                if stderr_content:
                    return {
                        "decision": "block",
                        "reason": stderr_content,
                        "blocking_hook": hook_name,
                    }

                # Exception during processing - still provide meaningful message
                tool_name = data.get("tool_name", "unknown action")
                return {
                    "decision": "block",
                    "reason": f"{tool_name} blocked by {hook_name}",
                    "blocking_hook": hook_name,
                    "note": "Hook blocked intentionally (exit code 2) with processing error",
                }

        return None
    except Exception as e:
        if hook_name in CRITICAL_HOOKS:
            return {
                "decision": "block",
                "reason": f"Critical safety hook failed: {hook_name}: {e}",
            }
        _record_degraded_mode_once(data, hook_name, f"exception:{type(e).__name__}")
        # Claude Code treats stderr as hook error - silence this
        # print(f"Error running {hook_name}: {e}", file=sys.stderr)
        return None


def main():
    # Optional canary for debugging router execution.
    if os.environ.get("PRETOOLUSE_CANARY_ENABLED", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }:
        try:
            import time as _t

            _canary_dir = Path(__file__).resolve().parent / "logs" / "diagnostics"
            _canary_dir.mkdir(parents=True, exist_ok=True)
            with open(_canary_dir / "pretooluse_canary.log", "a", encoding="utf-8") as _cf:
                _cf.write(f"[{_t.strftime('%H:%M:%S')}] main() entered\n")
        except Exception:
            pass

    raw_input = sys.stdin.read().strip()
    if not raw_input:
        sys.exit(0)

    try:
        raw_input = raw_input.lstrip("\ufeff")
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")

    # Track original tool_input for modify detection
    original_tool_input = data.get("tool_input", {}).copy() if "tool_input" in data else {}

    _pin_terminal_env(data)
    terminal_id = str(
        data.get("terminal_id")
        or data.get("terminalId")
        or os.environ.get("CLAUDE_TERMINAL_ID", "")
    ).strip()
    session_id = _resolve_session_id_from_utils(data)
    active_turn_id = get_active_evidence_turn(session_id, terminal_id) if terminal_id else None
    tool_input_payload = (
        data.get("tool_input", {}) if isinstance(data.get("tool_input"), dict) else {}
    )
    if active_turn_id:
        command_preview = str(
            tool_input_payload.get("command")
            or tool_input_payload.get("prompt")
            or tool_input_payload.get("file_path")
            or tool_input_payload.get("path")
            or ""
        )
        append_ledger_event(
            terminal_id=terminal_id,
            turn_id=str(active_turn_id),
            phase="PreToolUse",
            event_type="tool_invoked",
            payload={
                "tool_name": tool_name,
                "tool_input": tool_input_payload,
                "command_preview": command_preview[:500],
            },
        )

    # When Skill tool is called for a pending slash command, clear the intent
    # file immediately. _check_skill_first_gate() blocks when the intent file
    # exists; deleting it here allows all subsequent tools in the same turn
    # without waiting for skill_execution_state to be written externally.
    if tool_name == "Skill" and terminal_id:
        _skill_input = data.get("tool_input", {})
        if isinstance(_skill_input, dict):
            _skill_being_loaded = str(_skill_input.get("skill", "")).strip().lower()
            if _skill_being_loaded:
                _safe_term = _safe_id(terminal_id)
                _state_dir = HOOKS_DIR / "state"
                _fallback_dir = Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state"

                # Candidates in priority order (newest → oldest format).
                # Must mirror the lookup order in _check_skill_first_gate() so that
                # whichever path the intent file was written to, we delete it here.
                _candidate_paths_per_base = [
                    # TASK-005+ format: terminals/{terminal_id}/pending_command_intent.json
                    lambda base: base / "terminals" / terminal_id / "pending_command_intent.json",
                    # Legacy flat format: pending_command_intent_{terminal_id}.json
                    lambda base: base / f"pending_command_intent_{_safe_term}.json",
                ]

                # TASK-022 FIX: Retry loop with exponential backoff for TOCTOU race
                # Problem: exists() and read_text() are not atomic on concurrent terminals
                # Solution: Retry 3-5 times with exponential backoff (100ms → 200ms → 400ms → 800ms)
                max_retries = 4
                base_delay_ms = 100

                for _base in (_state_dir, _fallback_dir):
                    for _path_fn in _candidate_paths_per_base:
                        _intent_candidate = _path_fn(_base)

                        for attempt in range(max_retries):
                            try:
                                if _intent_candidate.exists():
                                    # Read intent file
                                    _intent_data = json.loads(
                                        _intent_candidate.read_text(encoding="utf-8")
                                    )
                                    # Verify skill matches before deleting
                                    if (
                                        str(_intent_data.get("skill", "")).strip().lower()
                                        == _skill_being_loaded
                                    ):
                                        _intent_candidate.unlink(missing_ok=True)
                                    break  # Read succeeded (match or mismatch); done.
                                else:
                                    break  # File already gone; nothing to delete.
                            except (FileNotFoundError, PermissionError):
                                # TOCTOU race: another process touched the file between
                                # exists() and read_text()/unlink(). Retry with backoff.
                                if attempt < max_retries - 1:
                                    # Exponential backoff: 100ms, 200ms, 400ms, 800ms
                                    delay_ms = base_delay_ms * (2**attempt)
                                    time.sleep(delay_ms / 1000.0)
                                # else: exhausted retries — fall through, loop ends.
                            except Exception:
                                # Non-retriable error (JSON decode, etc.) — bail immediately.
                                break

    # Run skill-first gate before all other hooks
    gate_result = _check_skill_first_gate(data)
    if gate_result and gate_result.get("decision") == "block":
        if active_turn_id:
            append_ledger_event(
                terminal_id=terminal_id,
                turn_id=str(active_turn_id),
                phase="PreToolUse",
                event_type="tool_blocked",
                payload={
                    "tool_name": tool_name,
                    "blocking_hook": "PreToolUse.py:skill_first_gate",
                    "reason": str(gate_result.get("reason", ""))[:2000],
                },
            )
        _msg = gate_result.get("reason", "Blocked by skill-first gate")

        # If _msg is already JSON (from subprocess hook), extract the reason
        if isinstance(_msg, str) and _msg.strip().startswith("{"):
            try:
                parsed = json.loads(_msg)
                if isinstance(parsed, dict) and "reason" in parsed:
                    _msg = parsed["reason"]
            except json.JSONDecodeError:
                pass  # Use original _msg

        response = {
            "decision": "block",
            "continue": False,
            "reason": _msg,
            "blocking_hook": "PreToolUse.py:skill_first_gate",
        }
        _log_pretooluse_block_event(
            data,
            blocking_hook="PreToolUse.py:skill_first_gate",
            reason=_msg,
            event_kind="router_gate_block",
            active_turn_id=str(active_turn_id or ""),
        )
        print(json.dumps(response))
        sys.exit(0)

    hooks_to_run = list(UNIVERSAL)
    hooks_to_run.extend(TOOL_HOOKS.get(tool_name, []))
    hooks_to_run.extend(COMPAT_POST_ROUTER_HOOKS)

    for hook in hooks_to_run:
        res = run_hook(hook, data)
        if not res:
            continue

        # NEW: Handle modify decision - hook provides corrected tool_input
        if res.get("decision") == "modify":
            if "tool_input" in res and isinstance(res["tool_input"], dict):
                # Update data with modified tool_input
                data["tool_input"] = res["tool_input"]
                # Continue to next hook (don't break loop)
                continue
            else:
                # Malformed modify response - fall back to block
                _msg = "Malformed modify response: missing or invalid tool_input"
                _blocking_hook = hook
                if active_turn_id:
                    append_ledger_event(
                        terminal_id=terminal_id,
                        turn_id=str(active_turn_id),
                        phase="PreToolUse",
                        event_type="tool_blocked",
                        payload={
                            "tool_name": tool_name,
                            "blocking_hook": _blocking_hook,
                            "reason": _msg,
                        },
                    )
                print(
                    json.dumps(
                        {
                            "decision": "block",
                            "continue": False,
                            "reason": _msg,
                            "blocking_hook": _blocking_hook,
                        }
                    )
                )
                sys.exit(0)

        # NEW: Handle hookSpecificOutput.advisory - display to user
        if "hookSpecificOutput" in res and "advisory" in res["hookSpecificOutput"]:
            advisory = res["hookSpecificOutput"]["advisory"]
            # Print advisory to stdout for Claude Code to display
            # Format: JSON with hookSpecificOutput wrapper
            print(json.dumps({"hookSpecificOutput": {"advisory": advisory, "source_hook": hook}}))
            sys.stdout.flush()  # Ensure advisory is visible immediately
            # Continue processing other hooks (don't break loop)

        # Check for both "decision": "block" and "block": True formats
        is_block = (
            res.get("decision") == "block"
            or res.get("block") is True
            or res.get("continue") is False
            or (isinstance(res.get("hookSpecificOutput"), dict)
                and res["hookSpecificOutput"].get("permissionDecision") == "deny")
        )
        if is_block:
            # Hard block - exit with code 2
            _msg = res.get("message") or res.get("reason")
            _blocking_hook = res.get("blocking_hook", hook)

            # If _msg is already JSON (from subprocess hook), extract the reason
            if isinstance(_msg, str) and _msg.strip().startswith("{"):
                try:
                    parsed = json.loads(_msg)
                    if isinstance(parsed, dict) and "reason" in parsed:
                        _msg = parsed["reason"]
                    if isinstance(parsed, dict) and "blocking_hook" in parsed:
                        _blocking_hook = parsed["blocking_hook"]
                except json.JSONDecodeError:
                    pass  # Use original _msg

            # Ground the artifact (best-effort, never block the block)
            artifact_path = ""
            try:
                if "git_safety" in _blocking_hook.lower():
                    artifact = ground_git_safety_block(data, _blocking_hook, _msg)
                else:
                    artifact = ground_blocked_command(data, _blocking_hook, _msg)
                artifact_path = _write_grounded_artifact(data, artifact)
            except Exception:
                pass  # Grounding is best-effort, never block the block

            _log_pretooluse_block_event(
                data,
                blocking_hook=_blocking_hook,
                reason=_msg,
                event_kind="router_final_block",
                active_turn_id=str(active_turn_id or ""),
                source_hook=hook,
                artifact_path=artifact_path,
            )
            if active_turn_id:
                append_ledger_event(
                    terminal_id=terminal_id,
                    turn_id=str(active_turn_id),
                    phase="PreToolUse",
                    event_type="tool_blocked",
                    payload={
                        "tool_name": tool_name,
                        "blocking_hook": _blocking_hook,
                        "reason": str(_msg)[:2000],
                        "artifact_path": artifact_path,
                    },
                )
            print(
                json.dumps(
                    {
                        "decision": "block",
                        "continue": False,
                        "reason": _msg,
                        "blocking_hook": _blocking_hook,
                    }
                )
            )
            sys.exit(0)

    # All hooks passed
    if active_turn_id:
        append_ledger_event(
            terminal_id=terminal_id,
            turn_id=str(active_turn_id),
            phase="PreToolUse",
            event_type="tool_allowed",
            payload={
                "tool_name": tool_name,
                "modified": bool(
                    "tool_input" in data and data["tool_input"] != original_tool_input
                ),
            },
        )
    # Check if tool_input was modified (compare with original)
    if "tool_input" in data and data["tool_input"] != original_tool_input:
        # Output modified tool_input using the format Claude Code recognizes:
        # {"tool_input": {...}} with exit 0.  The "continue: true" wrapper that was
        # here previously is NOT a Claude Code hook API key and caused modifications
        # to be silently ignored (PROTOCOL.md: "Modify: no current implementation").
        print(json.dumps({"tool_input": data["tool_input"]}))
    else:
        # No modifications - output empty allow
        print("{}")
    sys.exit(0)


def process_tool_use(event_data: dict) -> dict:
    """In-process entry point for router integration.

    Args:
        event_data: Hook event data (tool_name, tool_input, etc.)

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
        # Exit code 2 means blocked, 0 means allowed
        return {"ok": e.code == 0, "exit_code": e.code}

    except Exception as e:
        return {"ok": False, "diagnostic": str(e)}

    finally:
        # Restore stdin
        sys.stdin = old_stdin


if __name__ == "__main__":
    main()
