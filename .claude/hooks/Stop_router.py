#!/usr/bin/env python3
"""Single Stop hook router with terminal + turn scoped ledger snapshots.

This router replaces the old sequential Stop subprocess chain with one
authoritative entrypoint. It materializes the active turn once, runs migrated
validators in-process when possible, falls back to subprocess mode when needed,
 and emits a single final Stop decision.

Diagnostic evidence examples for user-facing messages:
- From bash output, pytest shows `test_checkpoint_restore FAILED`
- From Read on `P:/.claude/hooks/Stop_router.py`, the dispatch branch allows
  fail-open on missing transcript data instead of retry loops
"""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import re
import subprocess
import sys
import threading
import time
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any

import yaml

HOOKS_DIR = Path(__file__).resolve().parent
# Stop_router.py is at P:/.claude/hooks/Stop_router.py (NOT in __lib/)
# For "from __lib.xxx" imports to resolve, we need hooks/ at front of sys.path
# to resolve against P:/.claude/hooks/__lib/ (where circuit_breaker.py lives)
HOOKS_LIB_DIR = HOOKS_DIR  # HOOKS_DIR is P:/.claude/hooks/
HOOKS_ROOT_DIR = HOOKS_DIR.parent  # P:/.claude/
LOG_DIR = HOOKS_DIR / "state" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# CRITICAL: Ensure hooks/ is at front of sys.path BEFORE any __lib imports
# to resolve __lib.circuit_breaker against P:/.claude/hooks/__lib/
# (not P:/__csf/__lib which is a different package)
_hooks_path = str(HOOKS_DIR)
if _hooks_path in sys.path:
    # Already present - move to front to take precedence over other __lib packages
    sys.path.remove(_hooks_path)
    sys.path.insert(0, _hooks_path)
else:
    sys.path.insert(0, _hooks_path)

# CRITICAL: Clear any cached __lib modules from other packages (e.g., P:/__csf/__lib)
# Python's import system caches modules in sys.modules, so fixing sys.path alone
# is insufficient if __lib was already imported from a different location
for _key in list(sys.modules.keys()):
    if _key == "__lib" or _key.startswith("__lib."):
        del sys.modules[_key]

SKILL_GUARD_SRC = Path("P:/packages/skill-guard/src")
for path in (HOOKS_ROOT_DIR, SKILL_GUARD_SRC):
    if path.exists() and str(path) not in sys.path:
        sys.path.insert(0, str(path))

try:  # noqa: E402
    from __lib.hook_base import (
        HookTimeoutError,
        hook_main,
    )
    from __lib.hook_ledger import (
        append_event,
        build_response_snapshot,
        close_turn,
        detect_terminal_id_from_payload,
        ingest_stop_payload,
    )
    from evidence_store import get_active_turn as get_active_evidence_turn
    from shared_utils import resolve_session_id as _resolve_session_id_from_utils
except ImportError:  # pragma: no cover - import-path compatibility
    from hook_base import (  # type: ignore
        HookTimeoutError,
        hook_main,
    )
    from hook_ledger import (  # type: ignore
        append_event,
        build_response_snapshot,
        close_turn,
        detect_terminal_id_from_payload,
        ingest_stop_payload,
    )
    from evidence_store import get_active_turn as get_active_evidence_turn  # type: ignore

    try:
        from shared_utils import resolve_session_id as _resolve_session_id_from_utils
    except ImportError:
        import os as _os

        def _resolve_session_id_from_utils(data: dict) -> str:  # type: ignore[misc]
            session_obj = data.get("session")
            if isinstance(session_obj, dict):
                for key in ("id", "session_id", "sessionId"):
                    value = session_obj.get(key)
                    if isinstance(value, str) and value.strip():
                        return value.strip()
            for key in ("session_id", "sessionId", "conversation_id", "conversationId"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return _os.environ.get("CLAUDE_SESSION_ID", "").strip()


try:  # noqa: E402
    from skill_guard.utils import terminal_detection as _terminal_detection_module

    sys.modules.setdefault("terminal_detection", _terminal_detection_module)

    def detect_terminal_id() -> str:
        try:
            return str(_terminal_detection_module.detect_terminal_id() or "")
        except Exception:
            return ""
except Exception:  # pragma: no cover - fail-open fallback

    def detect_terminal_id() -> str:
        return ""


_router_logger = logging.getLogger("stop_router")
if not _router_logger.handlers:
    _router_handler = logging.FileHandler(LOG_DIR / "stop_router_timing.log", encoding="utf-8")
    _router_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    _router_logger.addHandler(_router_handler)
_router_logger.setLevel(logging.INFO)


# =============================================================================
# Phase 0: depends_on_skills Gate
# =============================================================================


def _detect_skill_from_transcript(transcript_entries: list[dict[str, Any]]) -> str | None:
    """Scan transcript for skill invocation patterns like /retro, /gto, etc.

    Transcript entries have structure: {"type": "user", "message": {"role": "user", "content": "..."}}
    where content contains XML-style command tags:
    <command-name>/skillname</command-name>
    <command-args>args</command-args>
    """
    command_pattern = re.compile(r"<command-name>(/[^<]+)</command-name>")
    for entry in reversed(transcript_entries[-10:]):  # Last 10 entries
        entry_text = ""
        # Try "text" field first (alternative format)
        if "text" in entry:
            entry_text = entry["text"]
        # Try message.content nested structure
        elif isinstance(entry.get("message"), dict):
            content = entry["message"].get("content", "")
            if isinstance(content, str):
                entry_text = content
        match = command_pattern.search(entry_text)
        if match:
            # Return skill name without leading slash
            return match.group(1).lstrip("/")
    return None


def _get_depends_on_skills(skill_name: str) -> list[str] | None:
    """Read skill's SKILL.md and return depends_on_skills list or None."""
    skills_dirs = [
        Path("P:/.claude/skills"),
        Path.home() / ".claude" / "skills",
    ]
    for skills_dir in skills_dirs:
        skill_md = skills_dir / skill_name / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            # Parse YAML frontmatter using PyYAML (handles both inline and block styles)
            match = re.search(r"^---\n(.*?)\n---", content, re.DOTALL)
            if match:
                frontmatter = match.group(1)
                data = yaml.safe_load(frontmatter)
                deps = data.get("depends_on_skills", [])
                if deps:
                    return [d.strip() for d in deps] if isinstance(deps, str) else [str(d).strip() for d in deps]
    return None


def _get_evidence_dir_for_skill(skill_name: str, terminal_id: str) -> Path:
    """Resolve evidence directory for a skill+terminal pair with path sanitization."""
    evidence_root = Path.home() / ".claude" / ".evidence"
    # Sanitize skill name and terminal_id for path safety
    safe_skill = re.sub(r"[^a-z0-9_-]", "", skill_name.lower())
    safe_terminal = re.sub(r"[^a-z0-9_-]", "", terminal_id.lower())
    return evidence_root / f"{safe_skill}-{safe_terminal}"


def _check_step1_evidence(evidence_dir: Path, step1_name: str) -> tuple[bool, str]:
    """Check if step-1 evidence file exists, is non-empty, and valid JSONL."""
    step_file = evidence_dir / f"step_{step1_name}.jsonl"
    if not step_file.exists():
        return False, f"step-1 evidence missing: {step_file}"
    if step_file.stat().st_size == 0:
        return False, f"step-1 evidence empty: {step_file}"
    # Verify it's valid JSONL (first line must be JSON)
    try:
        first_line = step_file.read_text(encoding="utf-8").split("\n")[0]
        json.loads(first_line)
        return True, "step-1 evidence valid"
    except (json.JSONDecodeError, IndexError):
        return False, f"step-1 evidence corrupted: {step_file}"


def _run_phase0_depends_on_skills_gate(
    validator_input: dict[str, Any],
) -> dict[str, Any] | None:
    """Phase 0 gate: verify step-1 evidence exists for depends_on_skills skills.

    Returns None (pass) if:
      - DEPENDS_ON_SKILLS_GATE_ENABLED is false
      - Skill has no depends_on_skills
      - Skill name or terminal_id cannot be resolved (bypass)
      - Evidence file exists and is valid JSONL

    Returns {"decision": "block", "reason": ...} if:
      - Skill has depends_on_skills but step-1 evidence is missing/empty/corrupt
    """
    if not _is_enabled("DEPENDS_ON_SKILLS_GATE_ENABLED", True):
        return None

    # Get transcript entries from validator_input
    transcript_entries: list[dict[str, Any]] = validator_input.get("transcript_entries", [])
    if not transcript_entries:
        return None

    # Detect skill name from transcript
    skill_name = _detect_skill_from_transcript(transcript_entries)
    if not skill_name:
        # Cannot determine skill — bypass gate
        return None

    # Get depends_on_skills list
    depends_on = _get_depends_on_skills(skill_name)
    if not depends_on:
        # Skill has no depends_on_skills — bypass gate
        return None

    # Get terminal_id
    terminal_id = str(validator_input.get("terminal_id", "")).strip()
    if not terminal_id:
        return None

    # First element of depends_on list is step-1
    step1_name = depends_on[0]

    # Check evidence
    evidence_dir = _get_evidence_dir_for_skill(skill_name, terminal_id)
    exists, reason = _check_step1_evidence(evidence_dir, step1_name)
    if not exists:
        return {
            "decision": "block",
            "reason": f"Phase 0: step-1 evidence required for depends_on_skills workflow. {reason}",
            "blocking_hook": "Stop_router.py:Phase0",
        }
    return None


INPROCESS_HOOK_DISPATCH_ENABLED = os.environ.get("STOP_ROUTER_INPROCESS", "true").lower() == "true"

OBSERVATION_TOOL_NAMES = frozenset(
    {
        "Read",
        "Grep",
        "Glob",
        "Bash",
        "View",
        "WebFetch",
    }
)

HOOK_SEQUENCE = [
    ("speculation_gate.py", "SPECULATION_GATE_ENABLED", False, "inprocess"),
    ("StopHook_perf_attribution_gate.py", "PERF_ATTRIBUTION_GATE_ENABLED", True, "inprocess"),
    ("empirical_claims_gate.py", "EMPIRICAL_CLAIMS_GATE_ENABLED", True, "inprocess"),
    ("unified_claim_verifier.py", "UNIFIED_CLAIM_VERIFIER_ENABLED", True, "inprocess"),
    ("assumption_audit_v2.py", "ASSUMPTION_AUDIT_V2_ENABLED", False, "inprocess"),
    ("stop_success_validator.py", "STOP_SUCCESS_VALIDATOR_ENABLED", False, "inprocess"),
    ("StopHook_cross_validator.py", "STOP_CROSS_VALIDATOR_ENABLED", False, "inprocess"),
    ("StopHook_drift_sentinel.py", "DRIFT_SENTINEL_ENABLED", False, "inprocess"),
    ("StopHook_correction_acknowledgment.py", "CORRECTION_GATE_ENABLED", False, "inprocess"),
    ("Stop_correction_followthrough_gate.py", "CORRECTION_FOLLOWTHROUGH_ENABLED", True, "inprocess"),
    # StopHook_skill_execution_gate moved to skill-guard plugin hooks.json (v2.1.0)
    (
        "StopHook_behavioral_quality_gate.py",
        "BEHAVIORAL_QUALITY_GATE_ENABLED",
        True,
        "inprocess",
    ),
    ("architecture_evidence_gate.py", "ARCHITECTURE_EVIDENCE_GATE_ENABLED", False, "inprocess"),
    ("StopHook_reflexion_validator.py", "STOP_REFLEXION_VALIDATOR_ENABLED", False, "inprocess"),
    ("StopHook_value_assessment.py", "STOP_VALUE_ASSESSMENT_ENABLED", False, "inprocess"),
    ("StopHook_unverified_stance.py", "UNVERIFIED_STANCE_ENABLED", True, "inprocess"),
    (
        "StopHook_overconfidence_detector.py",
        "OVERCONFIDENCE_DETECTOR_ENABLED",
        True,
        "inprocess",
    ),
    ("Stop_hypothesis_as_fact_gate.py", "HYPOTHESIS_AS_FACT_GATE_ENABLED", True, "inprocess"),
    ("Stop_hypothesis_enforcement.py", "REASONING_HYGIENE_ENABLED", True, "inprocess"),
    ("Stop_good_question_gate.py", "STOP_GOOD_QUESTION_GATE_ENABLED", True, "inprocess"),
    ("Stop_skill_question_marker.py", "STOP_QUESTION_MARKER_ENABLED", True, "inprocess"),
    ("Stop_fix_verification_enforcer.py", "FIX_VERIFICATION_ENFORCER_ENABLED", True, "inprocess"),
    ("Stop_optimality_check.py", "OPTIMALITY_CHECK_ENABLED", True, "inprocess"),
    ("Stop_ralph_loop.py", "RALPH_LOOP_ENABLED", True, "inprocess"),
    ("Stop_symptom_map.py", "SYMPTOM_MAP_ENABLED", True, "inprocess"),
    ("Stop_negative_existence_guard.py", "NEGATIVE_EXISTENCE_GUARD_ENABLED", True, "inprocess"),
    ("Stop_positive_existence_guard.py", "POSITIVE_EXISTENCE_GUARD_ENABLED", False, "inprocess"),
    ("Stop_comparative_claim_guard.py", "COMPARATIVE_CLAIM_GUARD_ENABLED", True, "inprocess"),
    ("StopHook_step_header_verifier.py", "STEP_HEADER_VERIFIER_ENABLED", True, "inprocess"),
    ("stop/Stop_verification_gate.py", "STOP_VERIFICATION_GATE_ENABLED", True, "inprocess"),
    ("stop/Stop_gto_checklist_gate.py", "GTO_CHECKLIST_GATE_ENABLED", True, "inprocess"),
    ("principle_monitor.py", "PRINCIPLE_MONITOR_ENABLED", True, "inprocess"),
    (
        "stop/StopHook_directive_obligation.py",
        "DIRECTIVE_OBLIGATION_ENABLED",
        True,
        "inprocess",
    ),
    ("StopHook_rca_reflector.py", "RCA_REFLECTOR_ENABLED", True, "inprocess"),
    ("StopHook_rca_contract.py", "RCA_CONTRACT_ENABLED", True, "inprocess"),
    ("StopHook_rca_auto_promotion.py", "RCA_AUTO_PROMO_ENABLED", True, "inprocess"),
    ("Stop_tdd_refactor_gate.py", "TDD_REFACTOR_GATE_ENABLED", True, "inprocess"),
    ("autonomy_gate.py", "AUTONOMY_GATE_ENABLED", True, "inprocess"),
    (
        "Stop_completion_verification_guard.py",
        "COMPLETION_VERIFICATION_GUARD_ENABLED",
        True,
        "inprocess",
    ),
    (
        "Stop_deletion_verification_guard.py",
        "DELETION_VERIFICATION_GUARD_ENABLED",
        True,
        "inprocess",
    ),
    (
        "Stop_task_completion_gate.py",
        "TASK_SELF_DOC_ENABLED",
        True,
        "inprocess",
    ),
    ("StopHook_rsn_display_gate.py", "RSN_DISPLAY_GATE_ENABLED", True, "inprocess"),
    ("StopHook_arch_gap_detection.py", "ARCH_GAP_DETECTION_ENABLED", True, "inprocess"),
    ("StopHook_cited_content_guard.py", "CITED_CONTENT_GUARD_ENABLED", True, "inprocess"),
    (
        "__lib/StopHook_consultation_loop_interrupt.py",
        "CONSULTATION_LOOP_INTERRUPT_ENABLED",
        True,
        "inprocess",
    ),
    ("Stop_proposal_decision_scanner.py", "PROPOSAL_DECISION_SCANNER_ENABLED", True, "inprocess"),
    ("Stop_self_reflection_gate.py", "SELF_REFLECTION_GATE_ENABLED", True, "inprocess"),
    (
        "Stop_diagnostic_analysis_quality_gate.py",
        "DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED",
        True,
        "inprocess",
    ),
    ("auto_commit_hook.py", "AUTO_COMMIT_ON_STOP_ENABLED", True, "inprocess"),
]

HOOK_PRIORITY = {
    hook_name: index
    for index, (hook_name, _env_var, _default, _dispatch) in enumerate(HOOK_SEQUENCE)
}

HOOK_DISPATCH = {
    hook_name: dispatch_mode
    for hook_name, _env_var, _default_enabled, dispatch_mode in HOOK_SEQUENCE
}

# Only migrated validators participate in the live Stop path. Additional hook
# names remain in HOOK_SEQUENCE for test/registration visibility, but they must
# not become executable just because an environment flag exists elsewhere.
ACTIVE_RUNTIME_HOOKS = frozenset(
    {
        "empirical_claims_gate.py",
        "unified_claim_verifier.py",
        # StopHook_skill_execution_gate moved to skill-guard plugin hooks.json (v2.1.0)
        "StopHook_behavioral_quality_gate.py",
        "StopHook_overconfidence_detector.py",
        "StopHook_unverified_stance.py",
        "Stop_hypothesis_as_fact_gate.py",
        "Stop_hypothesis_enforcement.py",
        "Stop_good_question_gate.py",
        "Stop_skill_question_marker.py",
        "Stop_fix_verification_enforcer.py",
        "Stop_optimality_check.py",
        "Stop_symptom_map.py",
        "Stop_negative_existence_guard.py",
        "Stop_positive_existence_guard.py",
        "Stop_comparative_claim_guard.py",
        "StopHook_step_header_verifier.py",
        "stop/Stop_verification_gate.py",
        "principle_monitor.py",
        "StopHook_rca_reflector.py",
        "StopHook_rca_contract.py",
        "StopHook_rca_auto_promotion.py",
        "Stop_tdd_refactor_gate.py",
        "autonomy_gate.py",
        "Stop_completion_verification_guard.py",
        "Stop_deletion_verification_guard.py",
        "Stop_task_completion_gate.py",
        "StopHook_rsn_display_gate.py",
        "StopHook_arch_gap_detection.py",
        "StopHook_cited_content_guard.py",
        "StopHook_drift_sentinel.py",
        "StopHook_correction_acknowledgment.py",
        "Stop_correction_followthrough_gate.py",
        "__lib/StopHook_consultation_loop_interrupt.py",
        "Stop_proposal_decision_scanner.py",
        "StopHook_perf_attribution_gate.py",
        "Stop_self_reflection_gate.py",
        "Stop_diagnostic_analysis_quality_gate.py",
    }
)


# RCA turn detection: skill names that trigger RCA mode
RCA_SKILL_NAMES = frozenset({"rca", "r", "rca-v2", "rv2", "debugrca", "debug-rca"})


def _is_rca_turn(skill_state: dict | None) -> tuple[bool, str | None]:
    """Derive RCA turn flag and skill name from skill_state.

    Returns (rca_turn, rca_skill) tuple.
    rca_turn is True when the current turn is an RCA/debugRCA skill turn.
    rca_skill is the normalized skill name if RCA turn, None otherwise.
    """
    if not skill_state:
        return False, None
    skill = skill_state.get("skill", "")
    if not skill:
        return False, None
    skill_lower = skill.lower()
    if skill_lower in RCA_SKILL_NAMES:
        return True, skill_lower
    return False, None


def _is_hook_skipped_for_rca(
    hook_name: str,
    rca_turn: bool,
) -> bool:
    """Check if a hook should be skipped entirely for RCA turns.

    RCA-turn policy:
    - StopHook_step_header_verifier.py: SKIPPED (not run at all)
    - All other hooks: run normally (advisory/demotion is per-hook responsibility)
    """
    if not rca_turn:
        return False
    return hook_name == "StopHook_step_header_verifier.py"


def _is_enabled(env_var: str, default_enabled: bool) -> bool:
    raw = os.environ.get(env_var)
    if raw is None:
        return default_enabled
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _resolve_hook_path(hook_name: str) -> Path:
    raw = Path(hook_name)
    candidates = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        # Skill-based hook: resolve from HOOKS_ROOT_DIR/skills (P:/,claude/skills/)
        # This handles paths like "../skills/pre-mortem/hooks/..." that were
        # incorrectly written with ".." but should resolve within .claude/skills/.
        # Use as_posix() for cross-platform consistent forward-slash comparison.
        raw_posix = raw.as_posix()
        if raw.parts[0] == ".." and "skills/" in raw_posix:
            # Strip the leading ".." since skill paths are relative to .claude/skills/
            # "../skills/pre-mortem/hooks/..." -> "pre-mortem/hooks/..."
            # This corrects the semantic error in the path construction
            skill_relative = Path(*raw.parts[2:])  # Remove ".." and "skills"
            candidates.append(HOOKS_ROOT_DIR / "skills" / skill_relative)
        else:
            candidates.append(HOOKS_DIR / raw)
            if len(raw.parts) == 1:
                candidates.append(HOOKS_DIR / "__lib" / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0] if candidates else HOOKS_DIR / raw


# PERF-001: Pre-resolve hook paths once at module load time to avoid repeated
# file existence checks on every Stop call (32 hooks * N Stop calls).
# Paths are static during runtime; changes require restart (acceptable tradeoff).
_HOOK_PATHS: dict[str, Path] = {
    hook_name: _resolve_hook_path(hook_name)
    for hook_name, _env_var, _default_enabled, _dispatch_mode in HOOK_SEQUENCE
}


def _module_name_for_path(hook_path: Path) -> str:
    safe_stem = hook_path.stem.replace("-", "_").replace(".", "_")
    safe_hash = abs(hash(str(hook_path.resolve()))) % (10**9)
    return f"stop_router_{safe_stem}_{safe_hash}"


def _import_hook_module(hook_path: Path) -> ModuleType | None:
    try:
        spec = importlib.util.spec_from_file_location(
            _module_name_for_path(hook_path),
            hook_path,
        )
        if spec is None or spec.loader is None:
            _router_logger.error(
                "stop_router: spec_from_file_location returned None for %s",
                hook_path,
            )
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    except Exception:
        _router_logger.exception(
            "stop_router: failed to import in-process hook %s", hook_path
        )
        return None


@lru_cache(maxsize=256)
def _load_inprocess_run_for_path(path_str: str, mtime_ns: int) -> Any | None:
    """Cache importable run() callables to avoid repeated module import on every Stop."""
    hook_path = Path(path_str)
    module = _import_hook_module(hook_path)
    run_func = getattr(module, "run", None) if module else None
    return run_func if callable(run_func) else None


def _get_inprocess_run(hook_name: str) -> Any | None:
    hook_path = _resolve_hook_path(hook_name)
    if not hook_path.exists():
        return None
    try:
        mtime_ns = hook_path.stat().st_mtime_ns
    except OSError:
        return None
    return _load_inprocess_run_for_path(str(hook_path.resolve()), mtime_ns)


def _supports_inprocess(hook_name: str) -> bool:
    return callable(_get_inprocess_run(hook_name))


def _run_callable_with_timeout(
    hook_name: str,
    run_func: Any,
    hook_data: dict[str, Any],
    timeout_seconds: float,
) -> dict[str, Any] | None:
    result_box: list[dict[str, Any] | None] = []
    exception_box: list[BaseException] = []

    def target() -> None:
        try:
            result = run_func(dict(hook_data))
            result_box.append(result)
        except BaseException as exc:  # pragma: no cover - defensive
            exception_box.append(exc)

    thread = threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)
    if thread.is_alive():
        raise HookTimeoutError(hook_name, timeout_seconds)
    if exception_box:
        raise exception_box[0]
    return result_box[0] if result_box else None


def run_hook_inprocess(
    hook_name: str,
    hook_data: dict[str, Any],
    timeout_seconds: float = 5.0,
) -> dict[str, Any] | None:
    """Run a Stop validator in-process when it exposes `run(data)`."""
    run_func = _get_inprocess_run(hook_name)
    if not callable(run_func):
        return None
    hook_path = _resolve_hook_path(hook_name)
    return _run_callable_with_timeout(hook_path.name, run_func, hook_data, timeout_seconds)


def run_hook_subprocess(
    hook_name: str,
    hook_data: dict[str, Any],
    timeout_seconds: float = 5.0,
) -> dict[str, Any] | None:
    """Run a Stop validator as a subprocess and parse its JSON result."""
    hook_path = _resolve_hook_path(hook_name)
    if not hook_path.exists():
        return None

    try:
        completed = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(hook_data),
            text=True,
            capture_output=True,
            cwd=str(HOOKS_DIR),
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return {
            "decision": "warn",
            "systemMessage": f"{hook_path.name} exceeded timeout of {timeout_seconds:.1f}s and was skipped.",
            "blocking_hook": hook_path.name,
        }
    except Exception as exc:  # pragma: no cover - defensive
        return {
            "decision": "warn",
            "systemMessage": f"{hook_path.name} failed to execute and was skipped: {exc}",
            "blocking_hook": hook_path.name,
        }

    stdout_text = completed.stdout.strip()
    if stdout_text:
        try:
            parsed = json.loads(stdout_text)
            if isinstance(parsed, dict):
                if parsed.get("block") is True:
                    return {
                        "decision": "block",
                        "reason": str(parsed.get("reason", "")),
                        "blocking_hook": parsed.get("blocking_hook") or hook_path.name,
                    }
                return parsed
        except json.JSONDecodeError:
            pass

    if completed.returncode == 2:
        # Hook exited 2 (intentional block) — extract what we can from available context
        response_preview = ""
        try:
            resp = hook_data.get("response", "") or ""
            response_preview = resp[:120] + "..." if len(resp) > 120 else resp
        except Exception:
            pass

        stderr_desc = completed.stderr.strip()
        if stderr_desc:
            # Hook printed something to stderr but no structured reason — use it
            reason = (
                f"⛔ BLOCKED by {hook_path.name}\n"
                f"   Response preview: {response_preview}\n"
                f"   stderr: {stderr_desc}"
            )
        else:
            # Hook blocked without any stderr explanation — this is the gap
            reason = (
                f"⛔ BLOCKED by {hook_path.name}\n"
                f"   Response preview: {response_preview}\n"
                f"   Reason: Hook exited with code 2 (intentional block) but printed no reason to stderr.\n"
                f"   Fix: The hook script must print a descriptive reason to stderr before exiting with sys.exit(2)."
            )

        return {
            "decision": "block",
            "reason": reason,
            "blocking_hook": hook_path.name,
        }

    return None


def _resolve_session_id(data: dict[str, Any]) -> str:
    """Delegates to shared_utils.resolve_session_id()."""
    return _resolve_session_id_from_utils(data)


def _set_session_terminal_context(data: dict[str, Any]) -> str:
    """Set session context, but never synthesize terminal scope from session_id."""
    session_id = _resolve_session_id(data)
    if session_id:
        os.environ["CLAUDE_SESSION_ID"] = session_id
        data.setdefault("session_id", session_id)

    terminal_id = detect_terminal_id_from_payload(data) or detect_terminal_id()
    if terminal_id:
        data.setdefault("terminal_id", terminal_id)
    return session_id


def _extract_observation_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []

    supplied = data.get("observations")
    if isinstance(supplied, list):
        for item in supplied:
            if isinstance(item, dict):
                observations.append(item)

    tool_events = data.get("tool_events")
    if isinstance(tool_events, list):
        for item in tool_events:
            if not isinstance(item, dict):
                continue
            tool_name = str(item.get("name") or item.get("tool_name") or "").strip()
            if tool_name in OBSERVATION_TOOL_NAMES:
                observations.append(item)

    if observations:
        return observations

    terminal_id = str(
        data.get("terminal_id") or os.environ.get("CLAUDE_TERMINAL_ID", "") or detect_terminal_id()
    ).strip()
    if not terminal_id:
        return []

    try:
        import tool_sequence_manager

        load_filtered = getattr(tool_sequence_manager, "load_tool_sequence_filtered", None)
        if callable(load_filtered):
            recovered = load_filtered(terminal_id=terminal_id)
            if isinstance(recovered, list):
                return [item for item in recovered if isinstance(item, dict)]

        get_recent = getattr(tool_sequence_manager, "get_recent_tool_sequence", None)
        if callable(get_recent):
            recovered = get_recent(count=50)
            if isinstance(recovered, list):
                return [
                    item
                    for item in recovered
                    if isinstance(item, dict)
                    and str(item.get("terminal_id", "")).strip() == terminal_id
                ]
    except Exception:
        pass
    return []


def _build_consolidated_observation_block() -> dict[str, Any]:
    examples = [
        "From bash output, pytest shows `test_checkpoint_restore FAILED`.",
        "From Read on `P:/.claude/hooks/Stop_router.py`, the Stop dispatch branch skipped stale transcript retries.",
    ]
    return {
        "decision": "block",
        "reason": (
            "Observation evidence is required before making diagnostic claims.\n\n"
            "Remediation: run one Read/Grep/Glob/Bash/View/WebFetch observation.\n"
            f"Examples:\n- {examples[0]}\n- {examples[1]}"
        ),
        "blocking_hook": "Stop_router.py",
    }


def _normalize_result(hook_name: str, result: dict[str, Any] | None) -> dict[str, Any]:
    if not result:
        return {"decision": "allow"}

    if result.get("decision") == "block" or result.get("block") is True:
        return {
            "decision": "block",
            "reason": str(result.get("reason", "")),
            "blocking_hook": str(result.get("blocking_hook") or hook_name),
        }

    if result.get("allow") is False:
        return {
            "decision": "block",
            "reason": str(result.get("reason", "")),
            "blocking_hook": str(result.get("blocking_hook") or hook_name),
        }

    if result.get("decision") == "warn":
        return {
            "systemMessage": str(
                result.get("systemMessage") or result.get("reason") or result.get("note") or ""
            ),
            "blocking_hook": str(result.get("blocking_hook") or hook_name),
        }

    note = str(
        result.get("systemMessage") or result.get("note") or result.get("additionalContext") or ""
    ).strip()
    reason = str(result.get("reason", "")).strip()
    if note:
        return {"systemMessage": note, "blocking_hook": hook_name}
    if reason and "warn" in reason.lower():
        return {"systemMessage": reason, "blocking_hook": hook_name}

    return {"decision": "allow"}


def _append_validator_result(
    terminal_id: str,
    turn_id: str,
    hook_name: str,
    dispatch_mode: str,
    result: dict[str, Any],
) -> None:
    if not terminal_id or not turn_id:
        return
    decision = str(result.get("decision", "allow"))
    reason = str(result.get("reason", ""))
    system_message = str(result.get("systemMessage", ""))
    # Skip high-volume allow-only writes; keep warnings/blocks for debugging.
    if decision == "allow" and not reason and not system_message:
        return
    payload = {
        "hook": hook_name,
        "dispatch_mode": dispatch_mode,
        "decision": decision,
        "reason": reason[:4000],
        "system_message": system_message[:4000],
    }
    append_event(terminal_id, turn_id, "Stop", "validator_result", payload)


def _build_validator_input(
    input_data: dict[str, Any],
    snapshot: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(input_data)
    merged.update(snapshot)
    merged["response"] = str(
        snapshot.get("assistant_response", "") or input_data.get("response", "") or ""
    )
    merged["assistant_response"] = merged["response"]
    merged["last_assistant_message"] = merged["response"]
    merged["assistant_message_kind"] = str(snapshot.get("assistant_message_kind", ""))
    merged["prompt"] = str(snapshot.get("user_prompt", "") or input_data.get("prompt", "") or "")
    merged["user_prompt"] = merged["prompt"]
    merged["session_id"] = str(snapshot.get("session_id", "") or _resolve_session_id(input_data))
    merged["tools_used"] = list(
        snapshot.get("tools_used", []) or input_data.get("tools_used", []) or []
    )
    merged["toolUse"] = [{"name": str(name)} for name in merged["tools_used"] if str(name).strip()]
    merged["tool_events"] = list(
        snapshot.get("tool_events", []) or input_data.get("tool_events", []) or []
    )
    merged["observations"] = list(
        snapshot.get("observations", []) or _extract_observation_entries(merged)
    )
    merged["transcript_entries"] = list(snapshot.get("transcript_entries", []))
    return merged


def _materialize_snapshot(input_data: dict[str, Any]) -> dict[str, Any]:
    _set_session_terminal_context(input_data)

    terminal_id = str(
        input_data.get("terminal_id")
        or detect_terminal_id_from_payload(input_data)
        or detect_terminal_id()
        or ""
    ).strip()
    if terminal_id:
        input_data["terminal_id"] = terminal_id

    turn_id = str(input_data.get("turn_id") or "").strip()
    if not turn_id and terminal_id:
        turn_id = str(get_active_evidence_turn(_resolve_session_id(input_data), terminal_id) or "").strip()

    if terminal_id and turn_id:
        snapshot = ingest_stop_payload(terminal_id, turn_id, input_data)
    else:
        response_snapshot = build_response_snapshot(
            input_data, default_prompt=str(input_data.get("prompt", "") or "")
        )
        snapshot = {
            "terminal_id": terminal_id,
            "turn_id": turn_id,
            "session_id": _resolve_session_id(input_data),
            "user_prompt": response_snapshot.get("user_prompt", ""),
            "assistant_response": response_snapshot.get("assistant_response", ""),
            "transcript_path": response_snapshot.get("transcript_path", ""),
            "tools_used": response_snapshot.get("tools_used", []),
            "tool_events": list(input_data.get("tool_events", []) or []),
            "governance": dict(input_data.get("governance", {}) or {}),
            "observations": [],
            "skill_state": input_data.get("skill_state"),
            "status": "open",
            "outcome": {},
        }

    snapshot["observations"] = list(
        snapshot.get("observations", []) or _extract_observation_entries(snapshot)
    )
    return snapshot


def route_stop(input_data: dict[str, Any]) -> dict[str, Any]:
    route_started = time.perf_counter()
    if input_data.get("hook_event_name") not in (None, "", "Stop"):
        return {}

    snapshot = _materialize_snapshot(input_data)
    terminal_id = str(snapshot.get("terminal_id", "") or "")
    turn_id = str(snapshot.get("turn_id", "") or "")

    if str(snapshot.get("assistant_message_kind", "")).strip() == "system_reminder":
        if terminal_id and turn_id:
            close_turn(
                terminal_id,
                turn_id,
                {
                    "status": "skipped",
                    "skip_reason": "system_reminder",
                },
            )
        return {}

    validator_input = _build_validator_input(input_data, snapshot)

    # Phase 0 gate: check depends_on_skills evidence before Phase 2 hooks
    phase0_result = _run_phase0_depends_on_skills_gate(validator_input)
    if phase0_result is not None and phase0_result.get("decision") == "block":
        if terminal_id and turn_id:
            close_turn(
                terminal_id,
                turn_id,
                {
                    "status": "blocked",
                    "blocking_hook": str(phase0_result.get("blocking_hook", "Stop_router.py:Phase0")),
                    "reason": str(phase0_result.get("reason", "")),
                    "warnings": [],
                },
            )
        return {
            "decision": "block",
            "reason": str(phase0_result.get("reason", "")),
            "blocking_hook": str(phase0_result.get("blocking_hook", "Stop_router.py:Phase0")),
        }

    # Derive RCA turn info from skill_state for hook policy
    skill_state = validator_input.get("skill_state")
    rca_turn, rca_skill = _is_rca_turn(skill_state)
    validator_input["rca_turn"] = rca_turn
    validator_input["rca_skill"] = rca_skill
    # AP5 (stale-execution-path) requires session_start_ts to function.
    # Without it, _check_stale_execution_path returns [] immediately (fail-open).
    # Monotonic time is used to match the TTL mechanism in band-aid state.
    validator_input["session_start_ts"] = time.monotonic()

    warning_messages: list[str] = []
    warning_tuples: list[tuple[str, str, str]] = []  # (hook_name, severity, message) for aggregation

    _HOOK_TIMEOUTS: dict[str, float] = {
        "StopHook_drift_sentinel.py": 15.0,  # TF-IDF computation is expensive
    }
    _DEFAULT_TIMEOUT = 5.0

    for hook_name, env_var, default_enabled, dispatch_mode in HOOK_SEQUENCE:
        if hook_name not in ACTIVE_RUNTIME_HOOKS:
            continue
        if not _is_enabled(env_var, default_enabled):
            continue
        # RCA turn policy: skip StopHook_step_header_verifier.py entirely
        if _is_hook_skipped_for_rca(hook_name, rca_turn):
            continue

        # PERF-001: Use pre-resolved path from _HOOK_PATHS instead of calling
        # _resolve_hook_path() on every Stop call (saves 32 path resolutions)
        hook_path = _HOOK_PATHS.get(hook_name)
        if not hook_path or not hook_path.exists():
            continue

        raw_result: dict[str, Any] | None
        used_dispatch = dispatch_mode
        hook_started = time.perf_counter()
        try:
            _timeout = _HOOK_TIMEOUTS.get(hook_name, _DEFAULT_TIMEOUT)
            if (
                dispatch_mode == "inprocess"
                and INPROCESS_HOOK_DISPATCH_ENABLED
                and _supports_inprocess(hook_name)
            ):
                raw_result = run_hook_inprocess(hook_name, validator_input, timeout_seconds=_timeout)
            else:
                used_dispatch = "subprocess"
                raw_result = run_hook_subprocess(hook_name, validator_input, timeout_seconds=_timeout)
        except HookTimeoutError as exc:
            raw_result = {
                "systemMessage": f"{hook_path.name} timed out and was skipped: {exc}",
                "blocking_hook": hook_path.name,
            }
        except Exception as exc:  # pragma: no cover - defensive
            raw_result = {
                "systemMessage": f"{hook_path.name} failed and was skipped: {exc}",
                "blocking_hook": hook_path.name,
            }
        elapsed_ms = (time.perf_counter() - hook_started) * 1000.0
        _router_logger.info(
            "hook=%s dispatch=%s elapsed_ms=%.1f timeout_s=%.1f",
            hook_name,
            used_dispatch,
            elapsed_ms,
            _HOOK_TIMEOUTS.get(hook_name, _DEFAULT_TIMEOUT),
        )

        result = _normalize_result(hook_name, raw_result)
        _append_validator_result(terminal_id, turn_id, hook_name, used_dispatch, result)

        message = str(result.get("systemMessage", "")).strip()
        if message:
            warning_messages.append(message)
            warning_tuples.append((hook_name, "warn", message))

        if result.get("decision") == "block":
            if terminal_id and turn_id:
                close_turn(
                    terminal_id,
                    turn_id,
                    {
                        "status": "blocked",
                        "blocking_hook": str(result.get("blocking_hook", hook_name)),
                        "reason": str(result.get("reason", "")),
                        "warnings": warning_messages,
                    },
                )
            return {
                "decision": "block",
                "reason": str(result.get("reason", "")),
                "blocking_hook": str(result.get("blocking_hook", hook_name)),
            }

    if terminal_id and turn_id:
        close_turn(
            terminal_id,
            turn_id,
            {
                "status": "allowed",
                "warnings": warning_messages,
            },
        )
    _router_logger.info(
        "route_stop total_elapsed_ms=%.1f terminal_id=%s turn_id=%s warnings=%d",
        (time.perf_counter() - route_started) * 1000.0,
        terminal_id,
        turn_id,
        len(warning_messages),
    )

    if warning_messages:
        return {
            "systemMessage": "\n\n".join(dict.fromkeys(warning_messages)),
        }

    return {}


@hook_main
def main() -> None:
    try:
        raw = sys.stdin.read().strip()
        input_data = json.loads(raw) if raw else {}
        if not isinstance(input_data, dict):
            input_data = {}
    except Exception:
        input_data = {}

    result = route_stop(input_data)
    print(json.dumps(result or {}))


if __name__ == "__main__":
    main()
