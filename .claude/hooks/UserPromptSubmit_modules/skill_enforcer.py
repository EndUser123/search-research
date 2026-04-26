"""Skill Enforcer Module.

Extracted from UserPromptSubmit_router.py.
Provides slash command detection and routing for skill execution.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import tempfile
import time
from datetime import datetime
from pathlib import Path
import sys

_script_path = Path(__file__)
for _hooks_root in (
    Path(r"P:\.claude\hooks"),
    _script_path.parent.parent,
    _script_path.resolve().parent.parent,
):
    _hooks_root_str = str(_hooks_root)
    if _hooks_root_str not in sys.path:
        sys.path.insert(0, _hooks_root_str)

try:
    from __lib.hook_base import get_terminal_id
    from __lib.ttl_utils import write_monotonic_ts as _write_monotonic_ts
    from __lib.ttl_utils import sanitize_future_ts as _sanitize_future_ts
except ImportError:
    _hooks_root = Path(__file__).resolve().parent.parent

    def _load_hook_module(module_name: str, relative_path: str):
        module_path = _hooks_root / relative_path
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load {relative_path} from {_hooks_root}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    _hook_base = _load_hook_module("_hooks_hook_base", "__lib/hook_base.py")
    _ttl_utils = _load_hook_module("_hooks_ttl_utils", "__lib/ttl_utils.py")
    get_terminal_id = _hook_base.get_terminal_id
    _write_monotonic_ts = _ttl_utils.write_monotonic_ts
    _sanitize_future_ts = _ttl_utils.sanitize_future_ts
from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

from .intent_classifier import is_topic_inquiry

# Flags that universally mean "show me what this skill supports"
_HELP_FLAGS = frozenset({"--list", "--help", "-h", "--flags", "--usage"})


def _is_help_request(args: str) -> bool:
    """Return True when the only args are help flags — no substantive topic."""
    tokens = set(args.strip().split()) if args else set()
    return bool(tokens) and tokens.issubset(_HELP_FLAGS)


HELP_REQUEST_LANE = """
The user passed a help flag ({flag}). After calling Skill("{command}"):
- Look for a flags/options/usage section in the skill's documentation.
- Display that section as a formatted list. This is a valid prose-only response.
- Do NOT run the skill's main execution script.
""".strip()

# Constants
SLASH_EXECUTION_LANE = """
INSTRUCTION: Execute skill {command}

Step 1: Call Skill("{command}") to load workflow  ← YOUR FIRST ACTION, no exceptions
Step 2: Follow the skill's documented procedure exactly

Do NOT use Bash, Read, Glob, Grep, or any other tool before Skill() is called.
Path validation, directory checks, and orientation all happen INSIDE the skill, after loading.
Do NOT substitute your own analysis or improvise.
""".strip()

# Command detection patterns
SLASH_COMMAND_RE = re.compile(r"^/([a-z0-9-]+)(?:\s+(.*))?$", re.IGNORECASE)
LEADING_PROMPT_GLYPHS_RE = re.compile(r"^\s*(?:[❯›»>$#]+\s*)+")
COMMAND_BLOCKLIST = {
    "help",
    "clear",
    "exit",
    "quit",
    "save",
    "load",
}
HOOK_HEALTH_REPORT = Path("P:/.claude/hooks/logs/diagnostics/hook_health.json")
FALLBACK_HOOK_HEALTH_REPORT = Path(tempfile.gettempdir()) / "claude_hooks" / "hook_health.json"
HOOKS_DIR = Path(__file__).resolve().parent.parent
INTENT_STATE_DIR = HOOKS_DIR / "state"
SESSION_DATA_DIR = HOOKS_DIR / "session_data"
ENFORCEMENT_CONFIG_FILE = HOOKS_DIR / "config" / "skill_enforcement.json"
FALLBACK_STATE_DIR = Path(tempfile.gettempdir()) / "claude_hooks" / "state"
FALLBACK_SESSION_DATA_DIR = Path(tempfile.gettempdir()) / "claude_hooks" / "session_data"

DEFAULT_ENFORCEMENT_CONFIG = {
    "mode": "all",
    "ignored_commands": ["help", "clear", "exit", "quit", "save", "load"],
    "enforced_skills": [],
}


def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _prompt_fingerprint(prompt: str) -> str:
    text = (prompt or "").strip()
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _normalize_prompt_for_command_detection(prompt: str) -> str:
    """Normalize leading terminal prompt glyphs before slash parsing."""
    stripped = prompt.strip()
    # Supports transcript/pasted terminal lines like: "❯ /search ...".
    stripped = LEADING_PROMPT_GLYPHS_RE.sub("", stripped)
    return stripped


def _load_enforcement_config() -> dict:
    """Load config controlling which slash commands are enforced."""
    config = dict(DEFAULT_ENFORCEMENT_CONFIG)
    try:
        if ENFORCEMENT_CONFIG_FILE.exists():
            data = json.loads(ENFORCEMENT_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                config.update(data)
    except Exception:
        pass
    return config


def _get_session_id(context: HookContext) -> str:
    data = context.data or {}
    session_obj = data.get("session")
    if isinstance(session_obj, dict):
        for key in ("id", "session_id", "sessionId"):
            value = session_obj.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    for key in ("session_id", "sessionId", "CLAUDE_SESSION_ID"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return str(context.session_id or "") or os.environ.get("CLAUDE_SESSION_ID", "") or "unknown"


def _get_terminal_id(context: HookContext) -> str:
    """Get terminal ID using centralized detection from hook_base.py."""
    data = context.data or {} if context.data else {}
    return get_terminal_id(data)


def _log_command_intent_telemetry(context: HookContext, command: str) -> None:
    """
    Log slash command telemetry for debugging/analytics.

    TELEMETRY ONLY - NOT USED FOR ENFORCEMENT:
    This function creates pending_command_intent state files, but they are
    NOT used by any hook for gating decisions. The v4.0 enforcement is stateless
    and per-turn only (see PreToolUse_skill_pattern_gate.py).

    These files serve as:
    - Debug telemetry for what slash commands were used
    - Analytics for skill invocation patterns
    - Historical analysis (if needed)

    DO NOT wire these files into PreToolUse or Stop hook blocking logic.
    Doing so will re-introduce the v3.5 deadlock failure mode.
    """
    raw_session_id = _get_session_id(context)
    raw_terminal_id = _get_terminal_id(context)
    if not raw_terminal_id:
        # No terminal ID detectable — skip writing intent file rather than
        # creating a shared "pending_command_intent_.json" that all undetectable
        # terminals would clobber each other with.
        return
    terminal_id = _safe_id(raw_terminal_id)
    payload = {
        "skill": command,
        "prompt": context.prompt,
        "prompt_fingerprint": _prompt_fingerprint(context.prompt),
        "timestamp": datetime.now().isoformat(),
        # Epoch seconds for TTL enforcement in PreToolUse gate.
        # The gate discards files older than SKILL_FIRST_INTENT_TTL_SECONDS (default 90s)
        # regardless of session match — covers crash/force-kill where SessionEnd never fires.
        "created_at": _sanitize_future_ts(_write_monotonic_ts()),
        # Scope identity for stale-data immunity and cross-checking.
        "session_id": raw_session_id,
        "terminal_id": raw_terminal_id,
        # Slash command satisfaction tracking (v3.5 - platform bug workaround)
        "skill_loaded": False,
        "execution_tools_used": False,
        "satisfied": False,
    }
    content = json.dumps(payload)

    # Try primary location first, then fallback temp path.
    wrote = False
    for base in (INTENT_STATE_DIR, FALLBACK_STATE_DIR):
        try:
            # Use new terminal-scoped state path structure
            state_file = base / f"terminals/{raw_terminal_id}/pending_command_intent.json"
            state_file.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write with one retry to tolerate transient FS races.
            tmp = state_file.with_suffix(".tmp")
            for attempt in range(2):
                try:
                    tmp.write_text(content, encoding="utf-8")
                    tmp.replace(state_file)
                    break
                except OSError:
                    if attempt == 1:
                        raise
                    time.sleep(0.05)
            # Best-effort cleanup of legacy filename patterns
            try:
                # Old terminal-scoped pattern: pending_command_intent_{terminal_id}.json
                legacy_terminal = base / f"pending_command_intent_{terminal_id}.json"
                legacy_terminal.unlink(missing_ok=True)
                # Old session-scoped pattern: pending_command_intent_{terminal_id}_{session_id}.json
                legacy_session = (
                    base / f"pending_command_intent_{terminal_id}_{_safe_id(raw_session_id)}.json"
                )
                legacy_session.unlink(missing_ok=True)
            except Exception:
                pass
            wrote = True
            break
        except Exception:
            continue
    if not wrote:
        raise OSError("Failed to persist pending command intent to primary or fallback path")


def _clear_command_intent(context: HookContext) -> None:
    """Clear any pending command intent superseded by a new user prompt.

    Slash intents are terminal-scoped in the current implementation. When the
    user sends a new non-slash prompt, that supersedes the prior slash request
    and should not keep blocking subsequent tool use in the same terminal.
    """
    raw_session_id = _get_session_id(context)
    raw_terminal_id = _get_terminal_id(context)

    safe_session = _safe_id(raw_session_id) if raw_session_id else ""
    safe_terminal = _safe_id(raw_terminal_id) if raw_terminal_id else ""

    for base in (INTENT_STATE_DIR, FALLBACK_STATE_DIR):
        try:
            # New terminal-scoped path
            if raw_terminal_id:
                new_path = base / f"terminals/{raw_terminal_id}/pending_command_intent.json"
                new_path.unlink(missing_ok=True)

            # Legacy terminal-scoped pattern
            if safe_terminal:
                (base / f"pending_command_intent_{safe_terminal}.json").unlink(missing_ok=True)
                if safe_session:
                    (base / f"pending_command_intent_{safe_terminal}_{safe_session}.json").unlink(
                        missing_ok=True
                    )

            # Legacy session-only pattern
            if safe_session:
                (base / f"pending_command_intent_{safe_session}.json").unlink(missing_ok=True)
        except Exception:
            continue


def _store_active_command(context: HookContext, command: str) -> None:
    """Persist active command for command_execution_validator.py."""
    terminal_id = _safe_id(_get_terminal_id(context))
    payload = {
        "command_name": command,
        "do_not_rules": [],
        "timestamp": datetime.now().isoformat(),
        "prompt": context.prompt,
        "session_id": _get_session_id(context),
        "terminal_id": _get_terminal_id(context),
    }
    content = json.dumps(payload)
    wrote = False
    for base in (SESSION_DATA_DIR, FALLBACK_SESSION_DATA_DIR):
        try:
            base.mkdir(parents=True, exist_ok=True)
            scoped_file = base / f"active_command_{terminal_id}.json"
            legacy_file = base / "active_command.json"
            scoped_file.write_text(content, encoding="utf-8")
            # Keep legacy file in sync for backward compatibility.
            legacy_file.write_text(content, encoding="utf-8")
            wrote = True
            break
        except Exception:
            continue
    if not wrote:
        raise OSError("Failed to persist active command state to primary or fallback path")


def _health_report_paths() -> list[Path]:
    override = os.environ.get("HOOK_HEALTH_REPORT_PATH", "").strip()
    if override:
        return [Path(override)]
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return [FALLBACK_HOOK_HEALTH_REPORT]
    return [HOOK_HEALTH_REPORT, FALLBACK_HOOK_HEALTH_REPORT]


def is_command_directive(prompt: str) -> bool:
    """Check if prompt starts with a slash command.

    Args:
        prompt: User prompt text

        context: Hook context (for marking skill as loaded in execution state)

    Returns:
        True if prompt appears to be a slash command
    """
    stripped = _normalize_prompt_for_command_detection(prompt)

    # Check if this is a topic inquiry about slash commands (not an invocation)
    # Topic inquiries like "tell me about /s" should NOT trigger skill enforcement
    if is_topic_inquiry(stripped):
        return False

    return bool(SLASH_COMMAND_RE.match(stripped))


def extract_command_name(prompt: str) -> str | None:
    """Extract command name from slash command.

    Args:
        prompt: User prompt text

    Returns:
        Command name string or None
    """
    normalized = _normalize_prompt_for_command_detection(prompt)
    match = SLASH_COMMAND_RE.match(normalized)
    if match:
        return match.group(1)
    return None


def _skill_exists(command: str) -> bool:
    """Check if a SKILL.md exists for this command in any skill directory.

    Scans project skills, user skills, and plugin cache. Returns True
    if a matching skill is found, False otherwise (built-in CLI command or typo).
    """
    cmd = command.lower()
    candidates: list[Path] = []

    # Project-level skills
    project_skills = HOOKS_DIR.parent / "skills"
    if project_skills.is_dir():
        candidates.append(project_skills / cmd / "SKILL.md")

    # User-level skills
    user_skills = Path.home() / ".claude" / "skills"
    if user_skills.is_dir():
        candidates.append(user_skills / cmd / "SKILL.md")

    # Plugin cache (any marketplace/plugin/skills/<cmd>/SKILL.md)
    plugin_cache = Path.home() / ".claude" / "plugins" / "cache"
    if plugin_cache.is_dir():
        for marketplace_dir in plugin_cache.iterdir():
            if not marketplace_dir.is_dir():
                continue
            for plugin_dir in marketplace_dir.iterdir():
                if not plugin_dir.is_dir():
                    continue
                for version_dir in plugin_dir.iterdir():
                    skill_file = version_dir / "skills" / cmd / "SKILL.md"
                    candidates.append(skill_file)

    return any(p.is_file() for p in candidates)


def should_block_command(command: str) -> bool:
    """Check if command should be excluded from enforcement.

    Dynamic check: if no SKILL.md exists for the command, it's a built-in
    CLI command (like /plugin, /compact, /config) — pass through without
    enforcement. This eliminates the need for a hardcoded blocklist of
    built-in commands.
    """
    cmd = command.lower()

    # Static blocklist still honored for explicit exclusions
    config = _load_enforcement_config()
    ignored = {
        str(x).strip().lower()
        for x in config.get("ignored_commands", COMMAND_BLOCKLIST)
        if str(x).strip()
    }
    if cmd in ignored:
        return True

    # Allowlist mode: only enforce commands in the allowlist
    mode = str(config.get("mode", "all")).strip().lower()
    if mode == "allowlist":
        allowlist = {
            str(x).strip().lower() for x in config.get("enforced_skills", []) if str(x).strip()
        }
        return cmd not in allowlist

    # Dynamic check: if no skill exists, it's a built-in CLI command — don't enforce
    if not _skill_exists(cmd):
        return True

    # Skill exists — enforce skill-first execution
    return False


# Template for forced skill evaluation (applied to all enforced skills)
EVALUATION_DIRECTIVE = """
INSTRUCTION: Execute skill {command}

Step 1: Call Skill("{command}")  ← YOUR FIRST ACTION, no exceptions
Step 2: Follow skill workflow exactly

Do NOT use Bash, Read, Glob, Grep, or any other tool before Skill() is called.
Path arguments, typos, and ambiguous inputs are resolved INSIDE the skill after loading.
""".strip()


def _check_workflow_steps_advisory(command: str) -> str | None:
    """Check if skill has workflow_steps declared.

    If workflow_steps are present, returns None (enforcement handled by Stop hook).
    If absent, returns a directive to follow the Execution section — NOT a "fail-open"
    signal. The absence of workflow_steps does not relax enforcement; it just means
    the Stop hook uses tool-use checking instead of marker-based governance.
    """
    try:
        from skill_guard.breadcrumb.tracker import _load_workflow_steps

        result = _load_workflow_steps(command)
        workflow_steps = result.steps

        if not workflow_steps:
            return (
                f"\nNOTE: /{command} has no declared workflow_steps. "
                f"You MUST still follow the skill's Execution section exactly. "
                f"Responding with prose without executing the skill workflow is not acceptable.\n"
            )
    except ImportError:
        pass
    except Exception:
        pass

    return None


def build_command_context(command: str, args: str, context: HookContext | None = None) -> str:
    """Build context injection for command execution.

    Forces AI to call Skill() tool via directive approach.
    Does NOT inject SKILL.md content - AI must invoke Skill tool explicitly.

    Args:
        command: Command name
        args: Command arguments
        context: Hook context (for marking skill as loaded in execution state)

    Returns:
        Context injection text

    NOTE: Do NOT call set_skill_loaded() here! That would bypass the PreToolUse gate.
    The skill is only marked as loaded when Skill() tool is actually called.
    """
    # DO NOT mark skill as loaded here - let PreToolUse gate enforce Skill() call first
    # set_skill_loaded() is called by skill_execution_state when Skill tool is used

    parts = []

    # Check for workflow_steps advisory (fail-open with notice)
    advisory = _check_workflow_steps_advisory(command)
    if advisory:
        parts.append(advisory)

    # Single execution lane template (removed duplicate EVALUATION_DIRECTIVE)
    parts.append(SLASH_EXECUTION_LANE.replace("{command}", command))
    parts.append(f"**Detected Command**: /{command}")
    if args and args.strip():
        parts.append(f"**Command Args**: {args.strip()}")
        # Universal help flag handling — works for every skill without per-skill docs
        if _is_help_request(args):
            detected_flag = next(t for t in args.strip().split() if t in _HELP_FLAGS)
            parts.append(
                HELP_REQUEST_LANE.replace("{flag}", detected_flag).replace("{command}", command)
            )
    if command.lower() == "main":
        parts.append(build_main_health_context())
    report_path = None
    for candidate in _health_report_paths():
        if candidate.exists():
            report_path = candidate
            break

    return "\n\n".join(parts)


def build_main_health_context() -> str:
    """Build health report context for /main command."""
    if os.environ.get("PYTEST_CURRENT_TEST"):
        checked_paths = [HOOK_HEALTH_REPORT, FALLBACK_HOOK_HEALTH_REPORT]
        lines = []
        for candidate in (FALLBACK_HOOK_HEALTH_REPORT,):
            if candidate.exists():
                try:
                    data = json.loads(candidate.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        for hook_name, status in sorted(data.items()):
                            lines.append(f"- {hook_name}: {status}")
                except Exception:
                    pass
        if lines:
            return "\n\n**Hook Health Report:**\n" + "\n".join(lines)
        checked = "\n".join(f"- {path}" for path in checked_paths)
        return "No startup health report found yet\nChecked:\n" + checked

    checked_paths = _health_report_paths()
    if not checked_paths:
        checked_paths = [HOOK_HEALTH_REPORT, FALLBACK_HOOK_HEALTH_REPORT]
    lines = []
    for candidate in checked_paths:
        if candidate.exists():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    for hook_name, status in sorted(data.items()):
                        lines.append(f"- {hook_name}: {status}")
            except Exception:
                pass
    if lines:
        return "\n\n**Hook Health Report:**\n" + "\n".join(lines)
    checked = "\n".join(f"- {path}" for path in checked_paths)
    return "No startup health report found yet\nChecked:\n" + checked


# Hook registration for UserPromptSubmit event
# Priority 1.0 runs before unified_injector (priority 2.0) to enforce skill-first execution
@register_hook("skill_enforcer", priority=1.0)
def skill_enforcement_hook(context: HookContext) -> HookResult:
    """Enforce skill-first execution for slash commands.

    When a slash command is detected, this hook:
    1. Persists command intent for PreToolUse gate (with graceful degradation)
    2. Injects SKILL EXECUTION LANE directive to force Skill() tool call
    3. Post-Skill() reminder: Checks for signal file and injects workflow reminder

    Graceful degradation (PR-002): If intent file write fails, hook continues
    and still creates injection. The enforcement is advisory without the gate.

    Multi-terminal isolation (PR-003): Intent files include terminal_id
    in filename to prevent cross-talk between concurrent terminals.
    """
    # Check for post-Skill() workflow reminder signal
    terminal_id = _get_terminal_id(context)
    if terminal_id:
        for base in (INTENT_STATE_DIR, FALLBACK_STATE_DIR):
            # New terminal-scoped signal path
            signal_file = base / f"terminals/{terminal_id}/first_tool_after_skill.json"
            # Also check legacy path for backward compatibility
            safe_terminal = _safe_id(terminal_id)
            legacy_signal = base / f"first_tool_after_skill_{safe_terminal}.json"

            if signal_file.exists() or legacy_signal.exists():
                try:
                    # Try new path first, then legacy
                    active_signal = signal_file if signal_file.exists() else legacy_signal
                    signal = json.loads(active_signal.read_text(encoding="utf-8"))
                    skill_name = str(signal.get("skill", "")).strip()
                    # Clean up both new and legacy signal files
                    signal_file.unlink(missing_ok=True)
                    legacy_signal.unlink(missing_ok=True)

                    if skill_name:
                        # Inject workflow execution reminder
                        reminder = f"""

═══════════════════════════════════════════════════════════════
⚠️  WORKFLOW EXECUTION REQUIRED
═══════════════════════════════════════════════════════════════

You just loaded skill: /{skill_name}

NEXT STEP: Follow the skill's workflow_steps (from SKILL.md)

✓ Use Bash/Task/Read tools to execute the workflow
✗ Do NOT respond with prose analysis or summaries
✗ Do NOT skip steps or improvise your own approach

The skill has documented workflow_steps for a reason — follow them.

═══════════════════════════════════════════════════════════════
"""
                        token_count = len(reminder) // 4
                        return HookResult(
                            context=reminder,
                            tokens=token_count,
                            priority=0.5,  # High priority to show early
                        )
                except Exception:
                    pass  # Best-effort reminder

    # Skip if no slash command detected
    if not is_command_directive(context.prompt):
        _clear_command_intent(context)
        return HookResult.empty()

    # Extract command and args
    command = extract_command_name(context.prompt)
    if not command:
        _clear_command_intent(context)
        return HookResult.empty()

    # Check if command should be blocked from enforcement
    if should_block_command(command):
        _clear_command_intent(context)
        return HookResult.empty()

    # Extract args (everything after the command name)
    normalized = _normalize_prompt_for_command_detection(context.prompt)
    match = SLASH_COMMAND_RE.match(normalized)
    args = match.group(2) if match else ""

    # Log command intent telemetry (v4.0: TELEMETRY ONLY - NOT USED FOR ENFORCEMENT)
    # Graceful degradation: Log warning but continue if write fails (PR-002)
    try:
        _log_command_intent_telemetry(context, command)
    except OSError as e:
        # Log warning but don't fail - enforcement becomes advisory
        # Claude Code treats stderr as hook error - use stdout instead
        import sys

        print(
            f"[skill_enforcer] Failed to persist command intent: {e}. "
            f"Enforcement will be advisory (PreToolUse gate won't block).",
            file=sys.stdout,
        )

    # Build injection context
    injection_text = build_command_context(command, args, context)

    # Estimate tokens (rough estimate: ~4 chars per token)
    token_count = len(injection_text) // 4

    return HookResult(context=injection_text, tokens=token_count, priority=1.0)
