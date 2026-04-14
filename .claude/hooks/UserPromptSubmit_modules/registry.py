"""Hook registry for UserPromptSubmit modules.

Provides centralized hook discovery, registration, and execution.
Hooks register via decorator and are run in priority order.
"""

from __future__ import annotations

import importlib
import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

from UserPromptSubmit_modules.base import HookContext, HookResult

if __name__ == "UserPromptSubmit_modules.registry":
    sys.modules["UserPromptSubmit.registry"] = sys.modules[__name__]
elif __name__ == "UserPromptSubmit.registry":
    sys.modules["UserPromptSubmit_modules.registry"] = sys.modules[__name__]

# Diagnostic logging for module failures
_HOOK_ERROR_LOG = (
    Path(__file__).resolve().parent.parent / "logs" / "diagnostics" / "ups_module_errors.jsonl"
)

# Execution trace logging
_EXECUTION_TRACE_LOG = (
    Path(__file__).resolve().parent.parent / "logs" / "diagnostics" / "ups_execution_trace.jsonl"
)

# Add package directories to sys.path for importing hook modules from packages
# This allows hooks to live in packages (e.g., P:/packages/prompt-enhancement/)
# while being imported by the router
_package_dirs = [
    Path("P:/packages"),
    Path("P:/packages/handoff"),  # hooks live at handoff/scripts/hooks/
    Path.home() / ".claude" / "hooks" / "_packages",
]
for pkg_dir in _package_dirs:
    if pkg_dir.exists() and str(pkg_dir) not in sys.path:
        sys.path.insert(0, str(pkg_dir))


# Hook registry
HOOKS: dict[str, Callable[[HookContext], HookResult]] = {}

# Priority order (lower = earlier execution)
HOOK_PRIORITY: dict[str, float] = {}

# Model name cache to avoid re-parsing transcript paths
_MODEL_NAME_CACHE: dict[str, str | None] = {}

# Log rotation settings
_MAX_ERROR_LOG_ENTRIES = 1000
_MAX_ERROR_LOG_SIZE_MB = 10


def _extract_model_from_transcript(transcript_path: str | None) -> str | None:
    """Extract Claude model name from transcript path filename.

    Args:
        transcript_path: Path to transcript file (e.g., "4e2ed5b1-...-claude-sonnet-4-6.jsonl")

    Returns:
        Model name (e.g., "claude-sonnet-4-6") or None if not found

    Examples:
        >>> _extract_model_from_transcript("session-abc123-claude-opus-4-6.jsonl")
        "claude-opus-4-6"
        >>> _extract_model_from_transcript("session.jsonl")
        None
        >>> _extract_model_from_transcript(None)
        None
    """
    if not transcript_path:
        return None

    # Check cache first
    if transcript_path in _MODEL_NAME_CACHE:
        return _MODEL_NAME_CACHE[transcript_path]

    try:
        # Extract filename from path
        filename = Path(transcript_path).stem  # Remove .jsonl extension

        # Look for model pattern: typically ends with "-claude-{model}-{version}"
        # Pattern: anything ending with "claude-{model}-{version}" where model is opus/sonnet/haiku
        import re

        model_pattern = r"-claude-(opus|sonnet|haiku)-[\d.]+(?:-[\d]+)?$"
        match = re.search(model_pattern, filename, re.IGNORECASE)

        if match:
            # Extract full match including the leading hyphen
            full_match = match.group(0)
            # Remove leading hyphen to get just the model name
            model_name = full_match[1:] if full_match.startswith("-") else full_match
            _MODEL_NAME_CACHE[transcript_path] = model_name
            return model_name

        # Not found - cache None to avoid re-parsing
        _MODEL_NAME_CACHE[transcript_path] = None
        return None
    except Exception:
        # Graceful degradation on any error
        _MODEL_NAME_CACHE[transcript_path] = None
        return None


def _rotate_hook_error_log() -> None:
    """Rotate ups_module_errors.jsonl to prevent unbounded growth.

    Keeps last 1000 entries and ensures file size < 10MB.
    """
    if not _HOOK_ERROR_LOG.exists():
        return

    try:
        # Check file size
        file_size_mb = _HOOK_ERROR_LOG.stat().st_size / (1024 * 1024)
        if file_size_mb > _MAX_ERROR_LOG_SIZE_MB:
            # File too large, rotate
            backup_path = _HOOK_ERROR_LOG.with_suffix(f".old.{int(time.time())}")
            _HOOK_ERROR_LOG.rename(backup_path)
            # Keep last 3 backups
            for old_backup in sorted(_HOOK_ERROR_LOG.parent.glob("*.old.*"))[:-3]:
                try:
                    old_backup.unlink()
                except Exception:
                    pass

        # Count entries and truncate if needed
        with open(_HOOK_ERROR_LOG, encoding="utf-8") as f:
            lines = f.readlines()

        if len(lines) > _MAX_ERROR_LOG_ENTRIES:
            # Keep last MAX_ERROR_LOG_ENTRIES entries
            with open(_HOOK_ERROR_LOG, "w", encoding="utf-8") as f:
                f.writelines(lines[-_MAX_ERROR_LOG_ENTRIES:])
    except Exception:
        pass  # Fail silently if rotation fails


def _log_execution_trace(
    log_file: Path,
    hook_name: str,
    context: HookContext,
    result: HookResult | None,
    stdout_captured: str = "",
    stderr_captured: str = "",
    duration_ms: float | None = None,
    transcript_path: str | None = None,
) -> None:
    """Log execution trace for hook calls to JSONL file.

    Creates structured log entries for debugging and monitoring hook execution.
    Log file is created if it doesn't exist, parent directories are created as needed.
    Entries are appended in JSONL format (one JSON object per line).

    Args:
        log_file: Path to log file (will be created if needed)
        hook_name: Name of the hook being executed
        context: HookContext object with session/terminal IDs
        result: HookResult object (or None if hook failed)
        stdout_captured: Captured stdout from hook execution (optional)
        stderr_captured: Captured stderr from hook execution (optional)
        duration_ms: Hook execution time in milliseconds (optional)
        transcript_path: Path to Claude Code session transcript file (optional)

    Log entry structure:
        {
            "ts": "2026-03-08T13:25:00",
            "session_id": "abc123",
            "terminal_id": "slug",
            "hook_name": "memory_size_check",
            "result": {
                "is_empty": false,
                "has_context": true,
                "context_type": "str",
                "tokens_added": 150
            },
            "duration_ms": 15.5,
            "transcript_path": "/path/to/transcript.jsonl",
            "model_name": "claude-sonnet-4-6"
        }

    Note: Fails silently if logging fails to avoid breaking hooks.
    """
    try:
        # Create parent directories if they don't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Build result summary
        result_summary = {}
        if result is not None:
            result_summary = {
                "is_empty": result.is_empty(),
                "has_context": result.context is not None,
                "tokens_added": result.tokens,
            }
            # Add context type if context exists
            if result.context is not None:
                if isinstance(result.context, dict):
                    result_summary["context_type"] = "dict"
                elif isinstance(result.context, str):
                    result_summary["context_type"] = "str"
                else:
                    result_summary["context_type"] = type(result.context).__name__
                # Include actual context for debugging
                result_summary["context"] = result.context
        else:
            result_summary = {
                "is_empty": True,
                "has_context": False,
                "tokens_added": 0,
            }

        # Build log entry
        log_entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "session_id": context.session_id,
            "terminal_id": context.terminal_id,
            "hook_name": hook_name,
            "result": result_summary,
        }

        # Add optional fields
        if duration_ms is not None:
            log_entry["duration_ms"] = round(duration_ms, 2)

        if transcript_path is not None:
            log_entry["transcript_path"] = transcript_path
            # Extract model name from transcript path
            model_name = _extract_model_from_transcript(transcript_path)
            if model_name is not None:
                log_entry["model_name"] = model_name

        # Add stdout/stderr capture if non-empty (truncate to 1000 chars total)
        if stdout_captured:
            if len(stdout_captured) > 1000:
                truncated_stdout = stdout_captured[:985] + "... (truncated)"
            else:
                truncated_stdout = stdout_captured
            log_entry["stdout"] = truncated_stdout

        if stderr_captured:
            if len(stderr_captured) > 1000:
                truncated_stderr = stderr_captured[:985] + "... (truncated)"
            else:
                truncated_stderr = stderr_captured
            log_entry["stderr"] = truncated_stderr

        # Append to log file (JSONL format - one JSON per line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Fail silently if logging fails


def _log_final_results(
    log_file: Path,
    context: HookContext,
    sorted_hooks: list,
    results: list[HookResult],
) -> None:
    """Log final results summary after all hooks complete.

    Creates a summary log entry with aggregate statistics about hook execution.
    Logs to ups_execution_trace.jsonl (same file as execution traces).

    Args:
        log_file: Path to log file (will be created if needed)
        context: HookContext object with session/terminal IDs
        sorted_hooks: List of (hook_name, priority) tuples executed
        results: List of HookResult objects from non-empty results

    Log entry structure:
        {
            "ts": "2026-03-08T13:25:00",
            "session_id": "abc123",
            "terminal_id": "slug",
            "num_hooks_run": 5,
            "num_results": 3,
            "results_summary": [
                {"is_empty": false, "has_context": true, "context_type": "str"},
                ...
            ]
        }

    Note: Fails silently if logging fails to avoid breaking hooks.
    """
    try:
        # Create parent directories if they don't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Build results summary
        results_summary = []
        for result in results:
            summary_entry = {
                "is_empty": result.is_empty(),
                "has_context": result.context is not None,
            }
            # Add context type if context exists
            if result.context is not None:
                if isinstance(result.context, dict):
                    summary_entry["context_type"] = "dict"
                elif isinstance(result.context, str):
                    summary_entry["context_type"] = "str"
                else:
                    summary_entry["context_type"] = type(result.context).__name__
            else:
                summary_entry["context_type"] = None
            results_summary.append(summary_entry)

        # Build log entry
        log_entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "session_id": context.session_id,
            "terminal_id": context.terminal_id,
            "num_hooks_run": len(sorted_hooks),
            "num_results": len(results),
            "results_summary": results_summary,
        }

        # Append to log file (JSONL format - one JSON per line)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Fail silently if logging fails


def register_hook(name: str, priority: float = 10.0):
    """Decorator to register a UserPromptSubmit hook.

    Args:
        name: Unique hook identifier
        priority: Execution priority (lower = earlier)

    Returns:
        Decorator function

    Example:
        @register_hook("my_hook", priority=5.0)
        def my_hook_function(context: HookContext) -> HookResult:
            return HookResult.empty()
    """

    def decorator(func: Callable[[HookContext], HookResult]) -> Callable[[HookContext], HookResult]:
        HOOKS[name] = func
        HOOK_PRIORITY[name] = priority
        return func

    return decorator


def register_hook_function(
    name: str, func: Callable[[HookContext], HookResult], priority: float = 10.0
):
    """Register a hook function directly (without decorator).

    Used for hooks that need to avoid circular import issues.

    Args:
        name: Unique hook identifier
        func: Hook function
        priority: Execution priority (lower = earlier)
    """
    HOOKS[name] = func
    HOOK_PRIORITY[name] = priority


def run_hooks(
    data: dict[str, Any], prompt: str, priority_dict: dict[str, float] | None = None
) -> list[HookResult]:
    """Run all registered hooks in priority order.

    Args:
        data: Event data dictionary
        prompt: User prompt text
        priority_dict: Optional priority override dict

    Returns:
        List of HookResult objects from all executed hooks
    """
    effective_priority = dict(HOOK_PRIORITY)
    if priority_dict:
        effective_priority.update(priority_dict)

    # Sort hooks by priority, then name for deterministic ordering
    sorted_hooks = sorted(effective_priority.items(), key=lambda x: (x[1], x[0]))

    # Create shared context
    context = HookContext(
        prompt=prompt,
        data=data,
        session_id=(
            data.get("session_id") or data.get("sessionId") or data.get("CLAUDE_SESSION_ID")
        ),
        terminal_id=(
            data.get("terminal_id") or data.get("terminalId") or data.get("CLAUDE_TERMINAL_ID")
        ),
    )

    # Run each hook with suppression support
    suppressed_hooks = set()
    results = []

    # Extract transcript_path once for all hooks (from context.data)
    transcript_path = context.data.get("transcript_path")

    for name, _ in sorted_hooks:
        if name not in HOOKS:
            continue
        if name in suppressed_hooks:
            continue  # Skip suppressed hooks
        hook_func = HOOKS[name]

        # Track execution time
        start_time = time.time()

        # Capture stdout/stderr during hook execution
        import io

        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        try:
            result = hook_func(context)

            # Restore original stdout/stderr
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Get captured content
            stdout_captured = stdout_capture.getvalue()
            stderr_captured = stderr_capture.getvalue()

            # Calculate duration
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # Log execution trace (success path)
            _log_execution_trace(
                log_file=_EXECUTION_TRACE_LOG,
                hook_name=name,
                context=context,
                result=result,
                stdout_captured=stdout_captured,
                stderr_captured=stderr_captured,
                duration_ms=duration_ms,
                transcript_path=transcript_path,
            )

            if result and not result.is_empty():
                # Extract suppress signal from dict context (e.g., continuation spine)
                if isinstance(result.context, dict):
                    suppress_list = result.context.get("suppress", [])
                    if suppress_list:
                        # Validate suppress list against known hooks
                        unknown_hooks = set(suppress_list) - set(HOOKS.keys())
                        if unknown_hooks:
                            print(
                                f"Warning: Hook {name} suppressing unknown hooks: {unknown_hooks}",
                                file=sys.stdout,
                            )
                        suppressed_hooks.update(suppress_list)
                results.append(result)
        except Exception:
            # Restore original stdout/stderr even on exception
            sys.stdout = old_stdout
            sys.stderr = old_stderr

            # Get captured content (even if hook failed)
            stdout_captured = stdout_capture.getvalue()
            stderr_captured = stderr_capture.getvalue()

            # Calculate duration even on failure
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000

            # Log error but continue to next hook
            # Claude Code treats stderr as hook error - use stdout for diagnostics
            import traceback

            exc_info = sys.exc_info()
            print(f"Hook {name} failed: {exc_info}", file=sys.stdout)

            # Log execution trace (failure path)
            _log_execution_trace(
                log_file=_EXECUTION_TRACE_LOG,
                hook_name=name,
                context=context,
                result=None,
                stdout_captured=stdout_captured,
                stderr_captured=stderr_captured,
                duration_ms=duration_ms,
                transcript_path=transcript_path,
            )

            # Also log to diagnostic file for analysis
            try:
                _HOOK_ERROR_LOG.parent.mkdir(parents=True, exist_ok=True)

                # Log rotation: keep last 1000 entries, max 10MB file size
                _rotate_hook_error_log()

                error_entry = {
                    "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                    "hook": name,
                    "exception": str(exc_info[1]),
                    "traceback": traceback.format_exc(),
                }
                with open(_HOOK_ERROR_LOG, "a", encoding="utf-8") as f:
                    f.write(json.dumps(error_entry) + "\n")
            except Exception:
                pass  # Fail silently if logging fails

    # Log final results summary
    _log_final_results(_EXECUTION_TRACE_LOG, context, sorted_hooks, results)

    return results


# Import and register hooks (lazy loading)
def _try_import_hook(
    module_name: str, module_path: str, hook_attr: str | None = None, priority: float = 10.0
) -> bool:
    """Try importing an optional hook module, register if successful.

    Uses importlib for flexible import handling. Logs all attempts (success or failure)
    to hook event log for observability. Never propagates exceptions.

    Args:
        module_name: Display name for the hook (used in logging)
        module_path: Full Python module path for importlib.import_module()
        hook_attr: Attribute name to extract from module (if None, module uses @register_hook)
        priority: Hook priority if registering manually

    Returns:
        True if import and registration succeeded, False otherwise
    """
    try:
        module = importlib.import_module(module_path)

        # If hook_attr specified, manually register the hook function
        if hook_attr:
            hook_fn = getattr(module, hook_attr)
            register_hook_function(module_name, hook_fn, priority=priority)

        # Log success for observability
        try:
            from __lib.shared_utils import log_hook_event

            log_hook_event(
                "UserPromptSubmit_registry",
                "info",
                f"Loaded hook: {module_name} from {module_path}",
            )
        except Exception:
            # shared_utils might not be available, fail silently
            pass

        return True

    except (ImportError, AttributeError) as e:
        # Log failure for observability (not to stderr - CC treats stderr as error)
        try:
            from __lib.shared_utils import log_hook_event

            log_hook_event(
                "UserPromptSubmit_registry",
                "warn",
                f"Optional hook {module_name} not loaded from {module_path}: {e}",
            )
        except Exception:
            # shared_utils might not be available, fail silently
            pass

        return False


def _load_hooks() -> None:
    """Lazy-load all hook modules.

    Called automatically on first run_hooks() call.

    Uses importlib for flexible import handling that doesn't propagate exceptions.
    All import attempts (success or failure) are logged to hook event log.

    Hooks are loaded from two sources:
    1. Local modules in UserPromptSubmit_modules/ directory
    2. External packages in P:/packages/ or ~/.claude/hooks/_packages/
    """

    # Core hooks - these use @register_hook decorator internally
    # Load them as a batch using relative import from parent package
    core_hook_modules = [
        "unified_detection",  # Runs FIRST to populate context data
        "abstraction_clarity_gate",
        "handoff_context_injector",  # NEW 2026-03-21: Inject handoff V2 context (transcript_path, session_id)
        "handoff_task_injector",  # NEW 2026-03-18: Inject current task after intra-session compaction
        "analysis_protocol_gate",
        "anti_sycophancy_injector",
        # "breadcrumb_init",  # DEPRECATED 2026-03-11: Superseded by workflow_tier_tagging
        "coach_note_reader",
        "cognitive_guardrails",  # NEW 2026-04-07: Inject discovery mandate and generalization check before design/implementation
        "cognitive_enhancers",
        "competence_injector",
        "context_summary",  # NEW 2026-03-13: Inject key facts from recent conversation to reduce context_reuse violations
        "continuation_spine",
        "consultation_awareness",  # NEW 2026-03-30: Detect directive repeat with prior LLM question
        "declaration_reminder",  # NEW 2026-03-16: Prevent "I'll update template" declarations without execution
        "discovery_block",  # NEW 2026-04-09: Block implementation prompts until discovery tools are used (ADR-00X)
        "rca_schema_injector",  # NEW 2026-04-07: Inject RCA 9-field schema before RCA generation to prevent block/regenerate cycles
        "failure_context_injector",  # NEW 2026-04-05: Inject failed Bash stderr/stdout evidence into next reasoning turn
        "ownership_colocation_nudge",  # NEW 2026-03-19: Inject colocation checklist before infra placement decisions
        "diagnostic_guard",
        "edit_consent",
        "frameguard_classifier",  # NEW 2026-03-18: FrameGuard - systemic frame detection
        "intent_classifier",
        "intent_extractor",
        "claim_risk_router",  # NEW 2026-04-11: Evidence-first routing tree for disputed claims and root-cause prompts
        "memory_size",
        "operating_rules",
        "path_syntax_corrector",
        "plan_injector",
        "behavior_contract",  # NEW 2026-04-13: Keep responses grounded and concise before generation
        "reasoning_mode_selector",
        # "skill_compliance_indicator",  # DEPRECATED 2026-03-11: Pre-run indicator redundant with step headers
        "sequential_thinking",
        "skill_enforcer",
        "skill_forced_eval",
        # "stdout_protocol_test",  # TASK-000: Prototype to verify hook stdout → Skill() emission protocol
        "synergy_detector",  # NEW 2026-03-22: Detect framework+mode synergies
        "context_followup_detector",  # NEW 2026-03-25: Detect follow-up queries and inject prior context
        "tdd_contract_auto_gate",  # NEW 2026-04-08: Auto-create TDD contract for /code, /tdd skills
        "testing_strategy_router",  # NEW 2026-04-12: Inject smallest-sufficient test mix guidance
        "evidence_grounding_reminder",  # NEW 2026-04-08: Conditional epistemic priming every N turns
        "file_immediate_read",  # NEW 2026-04-09: Read file paths in prompts immediately to prevent semantic satisficing
        "think_trigger",
        "truthfulness_gate",  # NEW 2026-03-13: Enforce proactive honesty on completion queries
        "turn_marker",
        "subagent_enforcer",  # NEW 2026-04-12: Inject constitutional constraints into subagent contexts + telemetry
        "verify_before_claim",  # NEW 2026-03-14: Remind to verify before existence/absence claims
        "unified_injector",
        "workflow_tier_tagging",
    ]

    # Try loading core hooks via relative import (batch import for efficiency)
    try:
        # Import the parent package to enable relative imports
        parent_package = importlib.import_module("UserPromptSubmit_modules")

        # Load each core hook module
        for hook_module_name in core_hook_modules:
            module_path = f"UserPromptSubmit_modules.{hook_module_name}"
            _try_import_hook(hook_module_name, module_path)

    except ImportError:
        # Parent package failed to import - try individual absolute imports as fallback
        for hook_module_name in core_hook_modules:
            module_path = f"UserPromptSubmit_modules.{hook_module_name}"
            _try_import_hook(hook_module_name, module_path)

    # Optional hooks with manual registration (avoid circular import issues)
    # cks_context requires special handling due to circular dependencies
    _try_import_hook(
        module_name="cks_context",
        module_path="UserPromptSubmit_modules.cks_context",
        hook_attr="cks_context_hook",
        priority=5.0,
    )

    # Load prompt_enhancement from prompting-toolkit package
    # Package structure: P:/packages/prompting-toolkit/packages/hook/prompting_toolkit/
    _try_import_hook(
        module_name="prompt_enhancement",
        module_path="prompting_toolkit.enhancement",
        # Module self-registers via @register_hook decorator
    )

    # Load handoff_task_injector from handoff package
    # Package structure: P:/packages/handoff/scripts/hooks/userpromptsubmit_task_injector.py
    _try_import_hook(
        module_name="handoff_task_injector",
        module_path="scripts.hooks.userpromptsubmit_task_injector",
        # Module self-registers via @register_hook decorator
    )

    # Load skill_forced_eval from skill-guard package
    # Package structure: P:/packages/skill-guard/src/skill_guard/skill_forced_eval.py
    # Module adds P:/.claude/hooks to sys.path for UserPromptSubmit_modules imports
    _try_import_hook(
        module_name="skill_forced_eval",
        module_path="skill_guard.skill_forced_eval",
        # Module self-registers via @register_hook decorator
    )


# Auto-load on module import
_load_hooks()
