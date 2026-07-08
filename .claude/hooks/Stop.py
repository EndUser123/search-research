#!/usr/bin/env python3
"""
Stop - Lean Router v3.0 (In-Process)
=====================================

Runs blocking gates IN-PROCESS (no subprocess overhead).
Side effects still use subprocess + ThreadPool for isolation.

v3.0: Converted safety_gate, behavior_audit, advisory to direct function calls.
      Eliminates 3 Python subprocess boots per response (~300-500ms saved).

v3.1: Stores Stop-time "Next Step Options" as a one-turn menu so the user can
      reply with a single letter (A/B/...) to run the chosen option.

v3.2: Added Stop_aggregator for hook result deduplication/prioritization.

=============================================================================
EPISTEMIC / QUALITY ADVISORY CLASSIFICATION (Steps 1-5 implementation)
=============================================================================

Hook: _run_epistemic_contract (Stop.py, via epistemic_validator)

LOCATION OF NOISE SOURCES:
  • Line ~380: "EPISTEMIC FORMAT REPAIR: Your response is missing required..."
    → Injected into user-visible response (format-only, non-critical)
  • Line ~392: "EPISTEMIC ADVISORY (N issue(s)):" + issue list
    → Injected into user-visible response (mixed/coaching, non-critical)

Both were surfaced inline on every analytical turn — ~3-5 lines of coaching
text per response regardless of issue severity.

WHAT CHANGED (Steps 3-4):
  Non-critical advisories are now log-only by default:
    • format_repair → logged to logs/diagnostics/epistemic_advisories.jsonl
      (systemMessage = None, decision = "warn" still recorded in telemetry)
    • mixed_advisory → same, logged silently
    • Full advisory text is NOT injected into the user-visible response

Critical advisories SURVIVE unchanged:
    • block verdict (unsupported_fact, causal, comparative, serious) →
      "EPISTEMIC VIOLATION (N issue(s)):" + issue list → still inline
    • Format repair on analytical responses — if --epistemic-verbose is in prompt,
      the full repair text is surfaced for this turn only

CRITICAL vs NON-CRITICAL TABLE:
  Critical (still inline)          | Non-critical (now log-only)
  ------------------------------- | --------------------------------
  epistemic violation (block)    | format_repair (format-only, analytical)
  unsupported_fact                | mixed_advisory (citations, minor causal)
  causal without uncertainty      | coaching-level epistemic notes
  comparative without hedging

ON-DEMAND DIAGNOSTICS (Step 4):
  Flag: --epistemic-verbose in user prompt
  Effect: Full non-critical advisory text surfaced inline for that turn only.
  Use when you want to see the coaching output without changing defaults.

LOG STREAMS:
  • logs/diagnostics/epistemic_telemetry.jsonl — all verdicts (block/warn/allow)
  • logs/diagnostics/epistemic_advisories.jsonl — non-critical advisory detail

GATE CLASS: "quality" — suppressed on control/exploration turns.
  (classified in GATE_CLASSES dict, respects turn_mode suppression)

=============================================================================
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

# ACA plugin Stop-hook dirs on sys.path. PRECEDENCE NOTE: HOOKS_DIR is inserted
# LAST (line ~119) so it has the HIGHEST import priority — a local module wins
# over these plugin dirs. This is by design: the local HOOKS_DIR entries for
# these gates are thin SHIMS that import + normalize the canonical plugin logic
# (see StopHook_cross_validator.py). A local FULL copy that drifts from the
# plugin canonical is a silent stale-shadow bug. The plugin audit's in-process
# module-shadow check flags divergent same-name modules across these dirs.
_EPISTEMIC_STOP = Path("P:/packages/cc-aca-epistemic/hooks/stop")
if not _EPISTEMIC_STOP.exists():
    _EPISTEMIC_STOP = Path("P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/hooks/stop")
if _EPISTEMIC_STOP.exists() and str(_EPISTEMIC_STOP) not in sys.path:
    sys.path.insert(0, str(_EPISTEMIC_STOP))

_AUTHORITY_STOP = Path("P:/packages/cc-aca-authority/hooks/stop")
if not _AUTHORITY_STOP.exists():
    _AUTHORITY_STOP = Path("P:/packages/.claude-marketplace/plugins/cc-aca-authority/hooks/stop")
if _AUTHORITY_STOP.exists() and str(_AUTHORITY_STOP) not in sys.path:
    sys.path.insert(0, str(_AUTHORITY_STOP))

_REASONING_STOP = Path("P:/packages/cc-aca-reasoning/hooks/stop")
if not _REASONING_STOP.exists():
    _REASONING_STOP = Path("P:/packages/.claude-marketplace/plugins/cc-aca-reasoning/hooks/stop")
if _REASONING_STOP.exists() and str(_REASONING_STOP) not in sys.path:
    sys.path.insert(0, str(_REASONING_STOP))

# ACA plugin __lib on sys.path (shared modules like anti_sycophancy). Same
# precedence caveat as above: HOOKS_DIR (line ~119) outranks this, so a local
# __lib module of the same name wins. Keep local copies as shims OR byte-
# identical to the plugin canonical — divergence = silent stale-shadow.
_EPISTEMIC_LIB = Path("P:/packages/cc-aca-epistemic/__lib")
if not _EPISTEMIC_LIB.exists():
    _EPISTEMIC_LIB = Path("P:/packages/.claude-marketplace/plugins/cc-aca-epistemic/__lib")
if _EPISTEMIC_LIB.exists() and str(_EPISTEMIC_LIB) not in sys.path:
    sys.path.insert(0, str(_EPISTEMIC_LIB))

# ACA observability plugin — posttool dir for cjk_drift_detector
_OBSERVABILITY_POSTTOOL = Path("P:/packages/cc-aca-observability/hooks/posttool")
if not _OBSERVABILITY_POSTTOOL.exists():
    _OBSERVABILITY_POSTTOOL = Path(
        "P:/packages/.claude-marketplace/plugins/cc-aca-observability/hooks/posttool"
    )
if _OBSERVABILITY_POSTTOOL.exists() and str(_OBSERVABILITY_POSTTOOL) not in sys.path:
    sys.path.insert(0, str(_OBSERVABILITY_POSTTOOL))

sys.path.insert(0, str(HOOKS_DIR))
ANTI_SYCOPHANCY_LOG = HOOKS_DIR / "logs" / "anti_sycophancy_violations.jsonl"
SKILL_FIRST_LOG = HOOKS_DIR / "logs" / "skill_first_enforcement.jsonl"
SKILL_FIRST_MODES = {"off", "monitor", "soft_block", "hard_block"}

try:
    from cc_diagnostic_logger import log_hook_invocation as _log_hook_invocation
except Exception:  # pragma: no cover - observability must fail open
    _log_hook_invocation = None

import logging as _logging
_logger = _logging.getLogger("Stop")

from __lib.turn_mode import (
    classify as _classify_turn_mode,
    is_quality_mode_suppressed,
    is_format_required,
    mode_display_label,
    get_session_mode,
    is_quality_gate_disabled,
    get_effective_turn_mode_for_gate,
    TurnMode,
    SessionMode,
)

# Model-tier gating: weak (non-Claude / Bifrost-routed) models cannot satisfy the
# epistemic/rubric contract and get trapped in capitulation loops. is_weak_model()
# reads the active model from the transcript and lets quality gates self-suppress
# while policy/safety gates stay active. Fails open to strong on any error.
try:
    from __lib.model_tier import is_weak_model
except Exception:  # pragma: no cover - never let a missing helper break Stop
    def is_weak_model(data: dict) -> bool:  # type: ignore[misc]
        return False

from __lib.epistemic_applicability import (
    is_substantive_reasoning_turn,
    is_grounded_delivery_summary,
    is_simple_epistemic_response,
    determine_epistemic_applicability,
    EpistemicApplicabilityDecision,
)

from __lib.trivial_turns import is_trivial_exchange as _is_trivial_exchange

from __lib.claim_type import _read_claim_type

from Stop_aggregator import aggregate_and_render as _aggregate_and_render
from Stop_artifact_enforcement import run as _run_artifact_enforcement
# approval_gate, commit_gate deleted 2026-06-18 — orphaned post plugin->in-process
# migration (router unwired) and redundant with the live PreToolUse authority/git guards.
from Stop_subagent_opportunity import run as _run_subagent_opportunity
from Stop_claim_gap_telemetry_probe import run as _run_claim_gap_telemetry_probe

# Referent coverage (Stop advisory) removed 2026-05-10.
# Lexical anchor-matching is not a reliable proxy for task completion.
# The PreToolUse scope gate (PreToolUse_referent_scope_gate.py) still prevents
# off-topic tool calls during investigation — that is the right intervention point.
# The UserPromptSubmit anchor writer (referent_anchor.py) is retained for that gate.


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _append_jsonl_safe(log_path, entry) -> bool:
    """Lazy wrapper so module-top writers don't require an import-time file_lock dep."""
    from file_lock import append_jsonl_safe
    return append_jsonl_safe(log_path, entry)


# <<< SHADOW_EMITTER_BEGIN >>>
def _run_external_fact_shadow(data: dict) -> None:
    """Close-the-Loop Phase 3b — log-only SHADOW emitter for external-fact claims.

    Runs the integrated predicate (verification.claims) + evidence join
    (verification.engine) against the turn's response and appends one row per
    UNGROUNDED EXTERNAL_FACT claim (SILENT verdict) to
    ``logs/diagnostics/external_fact_shadow.jsonl``. Non-blocking, no stderr,
    no additionalContext — telemetry only. Fail-open: any error returns silently.
    Gated by ``EXTERNAL_FACT_SHADOW_ENABLED`` (default true).
    """
    if not _env_bool("EXTERNAL_FACT_SHADOW_ENABLED", True):
        return
    try:
        response = data.get("response", "") or data.get("last_assistant_message", "") or ""
        if not response:
            return
        import verification.claims  # noqa: E402
        import verification.engine  # noqa: E402
        _VS = verification.engine.VerificationStatus

        tool_events = data.get("tool_events")
        if not tool_events:
            from __lib.turn_tool_events import build_turn_tool_events
            tool_events = build_turn_tool_events(data.get("transcript_path", ""))

        claims = [c for c in verification.claims.extract_claims(response) if c.type == "EXTERNAL_FACT"]
        if not claims:
            return
        verdicts = verification.engine.build_verdicts(claims, tool_events)

        import hashlib
        import datetime as _dt
        session_id, terminal_id = _resolve_scope_ids(data)
        transcript_path = data.get("transcript_path", "")
        response_hash = hashlib.sha256(response.encode("utf-8", "replace")).hexdigest()[:16]
        log_path = HOOKS_DIR / "logs" / "diagnostics" / "external_fact_shadow.jsonl"
        tool_events_seen = len(tool_events or [])

        for claim, verdict in zip(claims, verdicts):
            if verdict.status != _VS.SILENT:
                continue
            _append_jsonl_safe(log_path, {
                "timestamp": _dt.datetime.now().isoformat(timespec="seconds"),
                "session_id": str(session_id),
                "terminal_id": str(terminal_id),
                "transcript_path": transcript_path,
                "claim_text": claim.text,
                "claim_targets": list(getattr(claim, "targets", []) or []),
                "kind": "EXTERNAL_FACT",
                "verdict": verdict.status.value,
                "tool_events_seen": tool_events_seen,
                "response_hash": response_hash,
            })
    except Exception:
        return
# <<< SHADOW_EMITTER_END >>>


def _skill_first_mode_stop() -> str:
    if not _env_bool("ENFORCE_SKILL_FIRST_STOP_FALLBACK", default=False):
        return "off"
    mode = str(os.environ.get("SKILL_FIRST_MODE", "off")).strip().lower()
    if mode not in SKILL_FIRST_MODES:
        return "off"
    return mode


def _log_skill_first_stop_event(event: str, session_id: str, skill_name: str, mode: str) -> None:
    if not _env_bool("SKILL_FIRST_LOGGING_ENABLED", default=True):
        return
    payload = {
        "timestamp": time.time(),
        "hook": "Stop",
        "event": event,
        "reason_code": "E_SKILL_FIRST_INLINE_BYPASS",
        "session_id": session_id or "",
        "skill_name": skill_name or "",
        "mode": mode,
    }
    for path in (
        SKILL_FIRST_LOG,
        Path(os.environ.get("TEMP", "/tmp"))
        / "claude_hooks"
        / "logs"
        / "skill_first_enforcement.jsonl",
    ):
        if _append_jsonl_safe(path, payload):
            return


def _log_stop_block_event(data: dict, gate_name: str, result: dict) -> None:
    """Persist a blocking Stop decision into the diagnostics DB."""
    if _log_hook_invocation is None:
        return

    try:
        _log_hook_invocation(
            hook_name=result.get("blocking_hook") or f"Stop.py:{gate_name}",
            event_type="Stop",
            action="block",
            reason=result.get("reason"),
            turn_id=data.get("turn_id"),
            session_id=(
                data.get("session_id")
                or data.get("sessionId")
                or data.get("CLAUDE_SESSION_ID")
            ),
            terminal_id=(
                data.get("terminal_id")
                or data.get("terminalId")
                or data.get("CLAUDE_TERMINAL_ID")
            ),
        )
    except Exception:
        # Observability must never change hook behavior.
        return


def _resolve_anti_sycophancy_log_path() -> Path:
    """Choose a writable log path (workspace first, temp fallback)."""
    candidates = [
        ANTI_SYCOPHANCY_LOG,
        Path(os.environ.get("TEMP", "/tmp"))
        / "claude_hooks"
        / "logs"
        / "anti_sycophancy_violations.jsonl",
    ]
    for candidate in candidates:
        try:
            candidate.parent.mkdir(parents=True, exist_ok=True)
            return candidate
        except OSError:
            continue
    return candidates[-1]


def _anti_sycophancy_log_candidates() -> list[Path]:
    """Ordered candidates for anti-sycophancy logging."""
    return [
        ANTI_SYCOPHANCY_LOG,
        Path(os.environ.get("TEMP", "/tmp"))
        / "claude_hooks"
        / "logs"
        / "anti_sycophancy_violations.jsonl",
    ]


def _append_anti_sycophancy_log(
    data: dict, detector: str, severity: str, findings: list[str]
) -> None:
    """Best-effort JSONL log for anti-sycophancy observability."""
    if os.environ.get("ANTI_SYCOPHANCY_LOGGING_ENABLED", "true").lower() not in (
        "1",
        "true",
        "yes",
    ):
        return
    if not findings:
        return
    entry = {
        "timestamp": time.time(),
        "detector": detector,
        "severity": severity,
        "findings": findings[:20],
        "session_id": (
            data.get("session_id")
            or data.get("sessionId")
            or os.environ.get("CLAUDE_SESSION_ID")
            or ""
        ),
        "terminal_id": (
            data.get("terminal_id")
            or data.get("terminalId")
            or os.environ.get("CLAUDE_TERMINAL_ID")
            or ""
        ),
    }
    for log_path in _anti_sycophancy_log_candidates():
        if _append_jsonl_safe(log_path, entry):
            return


# === IN-PROCESS BLOCKING GATES ===
# Each returns: dict with decision/reason/systemMessage, or None to pass through.


# _run_safety_gate removed — handled by cc-aca-authority plugin Stop_safety_gate.py via subprocess router


def _is_analytical_response(response: str) -> bool:
    """Heuristic: only demand full epistemic schema for clearly analytical responses."""
    lines = [l for l in response.strip().splitlines() if l.strip()]
    if len(lines) <= 3:
        return False
    # NOTE: "source:" removed — too generic; matches file paths like
    # "source: ai-probe-nim/scripts/cli.py" and causes false positives.
    markers = (
        "because", "due to", "is caused by", "the reason is",
        "root cause", "evidence", "[fact]", "[inference]",
        "verified", "unverified", "unproven", "falsification",
    )
    lower = response.lower()
    return any(m in lower for m in markers)


# Planning-style prompt detection for turn mode classification
_PLANNING_PROMPT_RE = re.compile(
    r"(?i)"
    r"(?:what(?:'s| is) (?:the )?next|next steps?|what should we|"
    r"prioritized? list|plan for|roadmap|action items|what to work on|"
    r"what are the next|top \d+ (?:things|tasks|items|priorities)|"
    r"give me \d+|what \d+ things|recommend \d+|list \d+)"
)


def _challenge_marker_active() -> bool:
    """Check if anti_sycophancy_injector wrote a challenge marker for this turn."""
    import glob as _glob
    from pathlib import Path as _Path
    import time as _time

    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "")
    safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id) if session_id else ""
    safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id) if terminal_id else ""

    state_dir = _Path("P:/.claude/hooks/state/anti_sycophancy_injector")
    if not state_dir.exists():
        return False

    # Check exact marker first, then fall back to any recent marker in this scope
    marker = state_dir / f"challenge__{safe_session}__{safe_terminal}.json"
    if marker.exists():
        try:
            data = json.loads(marker.read_text(encoding="utf-8"))
            return _time.time() - data.get("timestamp", 0) < 120  # 2 min TTL
        except Exception:
            return True  # exists but unreadable — assume active
    return False


def _write_local_summary_guidance_marker(
    data: dict, tool_name: str, tool_transcript: str
) -> None:
    """Write a one-turn local-summary guidance marker consumed by UserPromptSubmit.

    The marker is terminal-scoped and self-deleting on read (TTL: 120s).
    This is separate from the challenge/pushback marker namespace to avoid
    interference with existing pushback behavior.
    """
    try:
        from pathlib import Path as _Path
        import time as _time

        session_id = (
            data.get("session_id")
            or os.environ.get("CLAUDE_SESSION_ID", "")
        )
        terminal_id = (
            data.get("terminal_id")
            or os.environ.get("CLAUDE_TERMINAL_ID", "")
        )
        safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(session_id)) if session_id else "anon"
        safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", str(terminal_id)) if terminal_id else "anon"

        state_dir = HOOKS_DIR / "state" / "local_summary_guidance"
        state_dir.mkdir(parents=True, exist_ok=True)

        marker_path = state_dir / f"guidance__{safe_session}__{safe_terminal}.json"

        # Build guidance using the epistemic_validator helper
        from epistemic_validator import build_local_summary_guidance

        guidance = build_local_summary_guidance(tool_name, tool_transcript)
        if not guidance:
            return

        marker_data = {
            "session_id": str(session_id),
            "terminal_id": str(terminal_id),
            "timestamp": _time.time(),
            "guidance": guidance,
        }
        marker_path.write_text(json.dumps(marker_data), encoding="utf-8")
    except Exception:
        pass  # Fail silently — guidance is best-effort, never a block


def _run_intent_artifact_alignment(data: dict) -> dict | None:
    """Intent vs Artifacts alignment gate.

    Detects when the assistant did adjacent work instead of modifying
    the requested targets. Quality gate — suppressed on control/exploration/meta turns.
    """
    from intent_artifact_alignment import check_alignment

    prompt = data.get("user_prompt") or data.get("prompt") or ""
    # Real Stop payloads carry no tool_events; fall back to transcript-derived
    # events so this gate can see what was actually modified (else every target
    # reads as "missed" → false misalignment). See memory stop-payload-no-tool-events.
    tool_events = data.get("tool_events")
    if not tool_events:
        from __lib.turn_tool_events import build_turn_tool_events
        tool_events = build_turn_tool_events(data.get("transcript_path", ""))
    response = data.get("response", "")
    return check_alignment(prompt, tool_events, response)


def _run_semantic_critic(data: dict) -> dict | None:
    """Semantic quality gate for diagnostic/analytical responses.

    Evaluates whether analytical responses adequately address the diagnostic question.
    Uses Haiku for semantic evaluation. Quality gate — suppressed on control/exploration.
    """
    from Stop_semantic_critic import run as _semantic_critic_run

    result = _semantic_critic_run(data)
    # None = critic allowed (or skipped/failed open). Nothing to surface or escalate.
    if result is None:
        return None

    # Surface the critic profile so Stop can log it via telemetry, and decide
    # whether to escalate this veto from advisory to a one-shot block.
    profile = ""
    try:
        from Stop_semantic_critic import _detect_critic_profile

        user_prompt = ""
        response_text = ""
        if "transcript" in data:
            for msg in reversed(data.get("transcript", [])):
                content = msg.get("content", "")
                if isinstance(content, str):
                    if msg.get("role") == "user" and not user_prompt:
                        user_prompt = content
                    elif msg.get("role") == "assistant" and not response_text:
                        response_text = content
        if not user_prompt:
            user_prompt = data.get("user_prompt", data.get("prompt", ""))
        if not response_text:
            response_text = data.get("response", data.get("raw_response", ""))
        profile = _detect_critic_profile(user_prompt, response_text)
    except Exception:
        profile = ""

    result = dict(result)
    if profile:
        result["_critic_profile"] = profile

    # Scoped self-critique enforcement. When the gate's rollout is BLOCK and the
    # critic vetoed a HIGH-SIGNAL turn (a recommendation/decision, or a software
    # root-cause answer), convert the advisory note into a one-shot block so the
    # self-critique forces a revision BEFORE the user sees the flawed proposal.
    # Lower-signal general_diagnostic vetoes stay advisory. The block is
    # quality-class, so _process_gate_result still applies turn-mode suppression,
    # weak-model suppression, and the regen circuit breaker — bounding it to a
    # finite block->regenerate loop instead of a per-turn nag. Fail-open is
    # inherited: the critic returns None (no veto) on any backend error.
    _enforce_profiles = {"evaluative_recommendation", "software_rca"}
    _default_rollout = GATE_METADATA.get("semantic_critic", {}).get(
        "rollout_mode", RolloutMode.ADVISORY
    )
    _rollout = _get_rollout_mode("semantic_critic", _default_rollout)
    _veto_msg = str(result.get("systemMessage", "")).strip()
    if _rollout == RolloutMode.BLOCK and profile in _enforce_profiles and _veto_msg:
        return {
            "decision": "block",
            "reason": _veto_msg,
            "_critic_profile": profile,
        }
    return result


def _run_proposal_critique_gate(data: dict) -> dict | None:
    """Block a proposal/recommendation turn that carries NO self-critique.

    Deterministic presence check (not a quality judgment): if the response makes
    a recommendation but contains zero failure-mode/falsification markers, block
    so the self-critique is added before the user sees it. Measured 2026-06-20:
    53% of the user's "please critically review" reminders were zero-critique
    proposals. Quality-class + BLOCK → Stop.py applies turn-mode suppression and
    the regen circuit breaker, so it cannot nag on control turns or livelock.
    """
    from proposal_critique_gate import run as _proposal_critique_run

    return _proposal_critique_run(data)


def _run_epistemic_contract(data: dict) -> dict | None:
    """Unified epistemic validator — format, citations, causal, comparative.

    Turn mode behavior (see turn_mode.py for classification):
      - control:           SKIP entirely (direct command, no format nagging).
      - exploration:       SKIP entirely (open-ended reasoning, format relaxed).
      - plan / exec-report: skip format repair on warns; block-level still fires.
      - analysis / final-answer: FULL enforcement (format repair + block).

    Strict mode override:
      ``--epistemic-strict`` in the user prompt forces full validation even on
      control/exploration turns.  ``STOP_QUALITY_MODE=strict`` re-enables quality
      gates for exploration but still suppresses control — you never nag on "stop".

    ``_challenge_marker_active()`` deduplicates format-only repair when the
    upstream ADVOCATE_PROTOCOL already injected a challenge (2-min TTL).
    """
    try:
        from epistemic_validator import (
            EpistemicConfig, validate, sanitize_response,
            _is_repair_response_in_active_challenge,
            apply_epistemic_policy,
        )

        response = data.get("response", "")
        # Strip internal scaffolding (TEST STRATEGY CONTRACT, [THINK:*], cognitive-tags)
        # before validation so the validator only sees the assistant's answer body.
        response = sanitize_response(response)
        if not response:
            return None

        turn_mode = _classify_turn_mode(data)
        user_prompt = data.get("user_prompt") or data.get("prompt") or ""
        quality_mode = os.environ.get("STOP_QUALITY_MODE", "normal")

        # Per-turn strict override: --epistemic-strict forces full validation
        # regardless of turn mode or quality mode.
        strict_override = "--epistemic-strict" in user_prompt

        # Per-turn verbose mode: --epistemic-verbose surfaces full non-critical
        # advisory text inline instead of silently logging. Intended for
        # deep-diagnosis turns where you want to see the full coaching output.
        verbose_override = "--epistemic-verbose" in user_prompt

        # Exploration and meta: skip unless --epistemic-strict overrides.
        # CONTROL mode: allow validation to run (CONTROL schema enforces no substantive claims).
        # Session mode: debug_gates = skip all quality gates; audit = treat all as CONTROL.
        session_mode = get_session_mode(user_prompt)
        if is_quality_gate_disabled(session_mode) or is_weak_model(data):
            return None
        effective_mode = get_effective_turn_mode_for_gate(turn_mode, session_mode)
        if not strict_override and effective_mode in ("exploration", "meta") and is_quality_mode_suppressed(effective_mode, quality_mode):
            return None

        # Trivial exchange bypass: skip epistemic enforcement on low-stakes turns
        # (numeric answers, short acks, smoke tests) — but NOT contract completions.
        contract = None
        try:
            from __lib.task_contract import load_contract as _load_contract
            _, tid = _resolve_scope_ids(data)
            if tid:
                contract = _load_contract(tid)
        except Exception as e:
            # Fail open on contract lookup errors — but log so degradation is observable
            from __lib.trivial_turns import log_trivial_skip
            log_trivial_skip("epistemic_contract", f"contract_lookup_failed:{e}", turn_mode, response)

        trivial, trivial_reason = _is_trivial_exchange(
            context=data,
            response=response,
            turn_mode=turn_mode,
            contract_active=contract is not None,
        )
        if trivial:
            # Belt-and-suspenders: GATE_CLASSES already suppresses quality gates on
            # control/exploration turns, but this catches numeric answers and acks
            # that pass through on analysis/final-answer turns.
            from __lib.trivial_turns import log_trivial_skip
            log_trivial_skip("epistemic_contract", trivial_reason, turn_mode, response)
            return None

        # Authoritative applicability — one decision, drives all enforcement in this gate
        decision = determine_epistemic_applicability(response, turn_mode=turn_mode)

        # Turn-mode suppression (Layer 1 of applicability) — skip non-substantive turns
        if not decision.applicable:
            return None

        # Layer 2 fast path: bypass section-header requirement for simple responses
        # on analytical/final-answer turns. Simple answers (direct yes/no, grounded
        # summaries, compact assessments) don't need [FACT]/[INFERENCE].
        if decision.enforcement_level == "simple":
            return None

        # Determine validator mode: block vs warn
        mode = os.environ.get("EPISTEMIC_CONTRACT_MODE", "warn")
        if strict_override:
            mode = "block"
        elif "--epistemic-warn" in user_prompt:
            mode = "warn"

        cfg = EpistemicConfig(mode=mode, turn_mode=effective_mode)
        # Require 4-section format for final-answer mode when response is substantial.
        # Short final-answers (<=100 words) are direct answers that don't need structure.
        # Substantial final-answers (>100 words) are analytical and should use
        # [FACT]/[INFERENCE]/[UNKNOWN]/[RECOMMENDATION] sections.
        if effective_mode == "final-answer":
            # Set as dynamic attribute (read via getattr in epistemic_validator);
            # it is not an EpistemicConfig __init__ field. ponytail: matches how
            # tool_transcript is assigned below.
            cfg.sectional_response_required = True
        # Assemble tool_transcript from tool_events if not already populated.
        # This feeds the local-summary bypass predicate in epistemic_validator.
        if not data.get("tool_transcript"):
            tool_events = data.get("tool_events", [])
            if tool_events:
                parts = []
                for event in tool_events[-5:]:  # last 5 events caps noise
                    output = event.get("output", "")
                    if output and isinstance(output, str):
                        parts.append(output[:500])  # truncate per-event to 500 chars
                data["tool_transcript"] = "\n".join(parts)
        cfg.tool_transcript = data.get("tool_transcript") or ""

        # Detect repair-bypass before validate so we can flag it in telemetry
        # even when the gate short-circuits (short repair in active challenge context)
        word_count = len(response.split())
        repair_bypass = _is_repair_response_in_active_challenge(response, word_count)

        verdict = validate(response, cfg)

        # Write local-summary guidance marker when the block is a citation failure
        # AND tool_transcript is non-empty.  The marker is one-turn scoped and
        # consumed by UserPromptSubmit on the next turn.
        if verdict.decision == "block" and cfg.tool_transcript:
            block_issues = {i.type for i in verdict.issues}
            citation_fail = (
                "unsupported_fact" in block_issues
                or ("format" in block_issues and not cfg.tool_transcript)
            )
            if citation_fail:
                tool_name = "the tool"
                tool_events = data.get("tool_events", [])
                if tool_events:
                    tool_name = tool_events[-1].get("name", "the tool")
                _write_local_summary_guidance_marker(data, tool_name, cfg.tool_transcript)

        # Structured telemetry — one line per validation, all decisions.
        _log_epistemic_telemetry(data, verdict, mode, repair_bypass=repair_bypass)

        # Route through apply_epistemic_policy for warn/retry/allow decisions
        is_analytical = _is_analytical_response(response)
        policy_result = apply_epistemic_policy(
            verdict,
            cfg,
            tool_transcript=cfg.tool_transcript,
            is_analytical=is_analytical,
            turn_mode=turn_mode,
            verbose_override=verbose_override,
        )

        if policy_result.decision == "block":
            # Schema-aware policy routing: epistemic_policy now handles plan-mode
            # suppression discriminately (only pure format-only issues suppressed).
            # Non-format blocks on plan mode now fire properly.
            reason_parts = [f"EPISTEMIC VIOLATION ({len(verdict.issues)} issue(s)):"]
            for issue in verdict.issues[:5]:
                reason_parts.append(
                    f"  [{issue.section}] {issue.type}: {issue.message}"
                )
            return {
                "decision": "block",
                "reason": "\n".join(reason_parts),
                "blocking_hook": "Stop.py:epistemic_contract",
            }

        if policy_result.decision == "retry_with_guidance":
            # Unsupported fact on analytical response → inject guidance marker
            if policy_result.actions.get("write_guidance_marker"):
                tool_name = "the tool"
                tool_events = data.get("tool_events", [])
                if tool_events:
                    tool_name = tool_events[-1].get("name", "the tool")
                _write_local_summary_guidance_marker(data, tool_name, cfg.tool_transcript or "")
            _log_non_critical_advisory(data, "unsupported_fact_retry", verdict.issues)
            if verbose_override:
                parts = [f"EPISTEMIC ADVISORY ({len(verdict.issues)} issue(s)):"]
                for issue in verdict.issues[:3]:
                    parts.append(f"  [{issue.section}] {issue.type}: {issue.message}")
                return {"decision": "warn", "reason": "\n".join(parts), "systemMessage": "\n".join(parts)}
            return {
                "decision": "warn",
                "reason": "epistemic_advisory_logged",
                "systemMessage": None,
            }

        if policy_result.decision == "retry_auto_wrap":
            # Format-only issues on analytical responses → auto-repair hint
            missing = [
                i.section for i in verdict.issues
                if i.type == "format" and i.section != "__GLOBAL__"
            ]
            sections_hint = ", ".join(sorted(set(missing))) if missing else "all"
            _log_non_critical_advisory(data, "format_repair", verdict.issues)
            if verbose_override:
                repair = (
                    "EPISTEMIC FORMAT REPAIR: Your response is missing required "
                    "section headers. Reformat your previous answer into the "
                    "required schema only. Do not add or remove substantive "
                    "content. Do not include text outside the required section "
                    f"headers. Missing: {sections_hint}."
                )
                return {"decision": "warn", "reason": repair, "systemMessage": repair}
            return {
                "decision": "warn",
                "reason": "format_repair_logged",
                "systemMessage": None,
            }

        if policy_result.decision == "log_warn":
            # Mixed or non-format issues → silent advisory log
            _log_non_critical_advisory(data, "mixed_advisory", verdict.issues)
            if verbose_override:
                parts = [f"EPISTEMIC ADVISORY ({len(verdict.issues)} issue(s)):"]
                for issue in verdict.issues[:3]:
                    parts.append(f"  [{issue.section}] {issue.type}: {issue.message}")
                return {"decision": "warn", "reason": "\n".join(parts), "systemMessage": "\n".join(parts)}
            return {
                "decision": "warn",
                "reason": "epistemic_advisory_logged",
                "systemMessage": None,
            }

        # allow — nothing to do
        return None
    except Exception as e:
        _logger.warning(f"epistemic_contract error: {e}")
        return None


def _run_behavior_audit(data: dict) -> dict | None:
    """Claim verification — telemetry-only. Retired from blocking/warn duty.

    The unified epistemic_validator (run via _run_epistemic_contract) now owns
    structural, citation, causal, and comparative checks.  This gate still runs
    evaluate_claims() for telemetry but returns None so it never blocks or
    injects advisories.  Re-enable by returning a decision dict if needed.
    """
    try:
        import os

        from unified_claim_verifier import evaluate_claims

        response = data.get("response", "")
        if not response:
            return None

        result = evaluate_claims(
            response,
            session_id=data.get("session_id", ""),
            terminal_id=(
                data.get("terminal_id")
                or data.get("terminalId")
                or os.environ.get("CLAUDE_TERMINAL_ID")
                or ""
            ),
        )

        # Log to diagnostics for future analysis, but never block/warn.
        if result.get("decision") in ("block", "warn"):
            _log_behavior_audit_telemetry(data, result)

        return None
    except Exception as e:
        _logger.warning(f"behavior_audit telemetry error: {e}")
        return None


def _log_behavior_audit_telemetry(data: dict, result: dict) -> None:
    """Append behavior_audit findings to diagnostics JSONL."""
    try:
        log_path = HOOKS_DIR / "logs" / "diagnostics" / "behavior_audit_telemetry.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": time.time(),
            "session_id": data.get("session_id", ""),
            "terminal_id": data.get("terminal_id", ""),
            "decision": result.get("decision"),
            "reason": result.get("reason", "")[:500],
            "missing_claims": result.get("missing_claims", [])[:10],
        }
        from file_lock import append_jsonl_safe
        append_jsonl_safe(log_path, entry)
    except OSError:
        pass


def _log_epistemic_telemetry(data: dict, verdict, mode: str, repair_bypass: bool = False) -> None:
    """Append one structured line per epistemic validation to JSONL."""
    try:
        from epistemic_validator import detect_response_mode

        raw = data.get("response", "")
        response_mode = detect_response_mode(raw)
        log_path = HOOKS_DIR / "logs" / "diagnostics" / "epistemic_telemetry.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        issue_types = sorted({i.type for i in verdict.issues})
        entry = {
            "timestamp": time.time(),
            "gate": "epistemic_contract",
            "decision": verdict.decision,
            "issue_count": len(verdict.issues),
            "issue_types": issue_types,
            "has_format_issues": "format" in issue_types,
            "has_unsupported_fact": "unsupported_fact" in issue_types,
            "has_causal_issues": any(t.startswith("causal") for t in issue_types),
            "has_comparative_issues": any(t.startswith("comparative") for t in issue_types),
            "mode": mode,
            "responseMode": response_mode,
            "repair_bypass": repair_bypass,
            "session_id": data.get("session_id", ""),
            "terminal_id": data.get("terminal_id", ""),
            # Observability for tool_transcript runtime wiring (Phase 1 verification)
            "tool_transcript_len": len(data.get("tool_transcript") or ""),
            "tool_transcript_present": bool(data.get("tool_transcript")),
        }
        # Per-issue detail for block decisions — enables true-positive/false-positive analysis.
        # Not written on allow/warn to keep the log compact; block is the only decision
        # that matters for precision measurement.
        if verdict.decision == "block" and verdict.issues:
            entry["issues"] = [
                {
                    "type": i.type,
                    "section": i.section,
                    "message": str(i.message)[:200],  # truncate long claim text
                }
                for i in verdict.issues[:10]  # cap at 10 to bound entry size
            ]
        from file_lock import append_jsonl
        append_jsonl(log_path, entry)
    except TimeoutError:
        import sys
        print(f"[telemetry] lock timeout writing {log_path.name}", file=sys.stderr)


def _log_non_critical_advisory(
    data: dict, advisory_type: str, issues, strategy=None, reason_code=None,
    triggering_codes=None, repeat_key=None, retry_count=None,
) -> None:
    """Append non-critical advisory detail to diagnostics JSONL.

    These advisories (format-only, mixed/coaching, unsupported_fact_retry) are
    logged for observability but NOT injected into the user-visible response.
    Critical blocks (epistemic violations with unsupported_fact, causal,
    comparative) still surface inline and are already covered by
    _log_epistemic_telemetry.

    Fields logged:
      advisory_type: "format_repair" | "mixed_advisory" | "unsupported_fact_retry"
      issue_count, issue_types, sections, messages: issue details
      strategy: action strategy (retry_with_guidance, etc.) from validator
      reason_code: specific reason from validator
      triggering_codes: tuple/list of error codes that triggered advisory
      repeat_key: session+mode key for repeat detection
      retry_count: retry attempt number
    """
    try:
        log_path = HOOKS_DIR / "logs" / "diagnostics" / "epistemic_advisories.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        issue_types = sorted({i.type for i in issues})
        entry = {
            "timestamp": time.time(),
            "advisory_type": advisory_type,
            "issue_count": len(issues),
            "issue_types": issue_types,
            "sections": sorted({i.section for i in issues if i.section != "__GLOBAL__"}),
            "messages": [i.message for i in issues[:5]],
            "session_id": data.get("session_id", ""),
            "terminal_id": data.get("terminal_id", ""),
            "response_length": len(data.get("response", "")),
        }
        # Extract fields from RetryStrategy object if passed, otherwise use direct args
        if strategy is not None:
            if hasattr(strategy, "strategy"):  # RetryStrategy dataclass
                entry["strategy"] = strategy.strategy
                entry["reason_code"] = strategy.reason_code
                entry["triggering_codes"] = strategy.triggering_codes
                entry["repeat_key"] = strategy.repeat_key
            else:
                entry["strategy"] = strategy
        if reason_code is not None and "reason_code" not in entry:
            entry["reason_code"] = reason_code
        if triggering_codes is not None and "triggering_codes" not in entry:
            entry["triggering_codes"] = triggering_codes
        if repeat_key is not None and "repeat_key" not in entry:
            entry["repeat_key"] = repeat_key
        if retry_count is not None:
            entry["retry_count"] = retry_count
        from file_lock import append_jsonl
        append_jsonl(log_path, entry)
    except TimeoutError:
        import sys
        print(f"[advisory] lock timeout writing {log_path.name}", file=sys.stderr)


def _run_cross_validator(data: dict) -> dict | None:
    """Block document and action fabrication claims without evidence."""
    try:
        from StopHook_cross_validator import run as cross_validate

        result = cross_validate(
            {
                "assistant_response": data.get("response", ""),
                "response": data.get("response", ""),
                "session_id": data.get("session_id") or data.get("sessionId") or "",
                "terminal_id": data.get("terminal_id") or data.get("terminalId") or "",
                "tool_events": data.get("tool_events", []),
                "transcript_path": data.get("transcript_path", ""),
                "transcript": data.get("transcript", []),
            }
        )
        if result and not result.get("allow", True):
            return {
                "decision": "block",
                "reason": result.get("reason", "Cross validation failed."),
                "blocking_hook": result.get("blocking_hook", "Stop.py:cross_validator"),
            }
        return None
    except Exception as e:
        _logger.warning(f"cross_validator error: {e}")
        return None


def _run_unverified_stance(data: dict) -> dict | None:
    """Block unverified stances: ungrounded confident claims, lazy closure, completion claims without evidence."""
    try:
        from StopHook_unverified_stance import run as unverified_stance_run

        result = unverified_stance_run(
            {
                "assistant_response": data.get("response", ""),
                "response": data.get("response", ""),
                "session_id": data.get("session_id") or data.get("sessionId") or "",
                "terminal_id": data.get("terminal_id") or data.get("terminalId") or "",
                "tool_events": data.get("tool_events", []),
                "transcript_path": data.get("transcript_path", ""),
                "transcript": data.get("transcript", []),
                # Loop-fix monitoring: pass toolUse for evidence discrimination
                "toolUse": data.get("tool_calls") or [],
            }
        )
        # StopHook_unverified_stance.run() returns None for clean responses
        # and a dict with block=True for blocks. We MUST return a dict on the
        # allow path so telemetry fires (observability fix).
        if result is None:
            return {"decision": "allow", "allow": True}
        if result.get("block") is True or result.get("allow") is False:
            return {
                "decision": "block",
                "reason": result.get("reason", "Unverified stance detected."),
                "blocking_hook": result.get("blocking_hook", "Stop.py:unverified_stance"),
                "block": True,  # preserve for telemetry extra fields
            }
        # Clean path: gate ran and found no violations — return dict so
        # telemetry fires (otherwise log_gate_event skips this gate).
        return {"decision": "allow", "allow": True}
    except Exception as e:
        _logger.warning(f"unverified_stance error: {e}")
        return None


def _run_correction_acknowledgment(data: dict) -> dict | None:
    """Block denial or non-acknowledgment of user corrections ('I didn't say that', etc.)."""
    try:
        from StopHook_correction_acknowledgment import run as correction_run

        result = correction_run(
            {
                "response": data.get("response", ""),
                "user_prompt": data.get("user_prompt") or data.get("prompt") or "",
                "session_id": data.get("session_id") or data.get("sessionId") or "",
                "terminal_id": data.get("terminal_id") or data.get("terminalId") or "",
            }
        )
        if not result:
            return None
        if result.get("allow") is False:
            return {
                "decision": "block",
                "reason": result.get("reason", "Correction not acknowledged."),
                "blocking_hook": result.get("blocking_hook", "Stop.py:correction_acknowledgment"),
            }
        return None
    except Exception as e:
        _logger.warning(f"correction_acknowledgment error: {e}")
        return None


def _run_cited_content_guard(data: dict) -> dict | None:
    """Block fabricated file citations that are not supported by Read output."""
    try:
        from StopHook_cited_content_guard import run as cited_content_run

        result = cited_content_run(
            {
                "assistant_response": data.get("response", ""),
                "response": data.get("response", ""),
                "session_id": data.get("session_id") or data.get("sessionId") or "",
                "terminal_id": data.get("terminal_id") or data.get("terminalId") or "",
                "tool_events": data.get("tool_events", []),
                "transcript_path": data.get("transcript_path", ""),
                "transcript": data.get("transcript", []),
            }
        )
        if not result:
            return None
        if result.get("block") is True or result.get("allow") is False:
            return {
                "decision": "block",
                "reason": result.get("reason", "Cited content verification failed."),
                "blocking_hook": result.get("blocking_hook", "Stop.py:cited_content_guard"),
            }
        warning = str(result.get("warning") or result.get("systemMessage") or "").strip()
        if warning:
            return {"systemMessage": warning}
        return None
    except Exception as e:
        _logger.warning(f"cited_content_guard error: {e}")
        return None


def _run_dependency_chain_guard(data: dict) -> dict | None:
    """Block comparative conclusions that ignore known prerequisites."""
    if os.environ.get("DEPENDENCY_CHAIN_GUARD_ENABLED", "true").lower() not in (
        "1",
        "true",
        "yes",
    ):
        return None
    try:
        from dependency_chain_guard import run as guard_run

        response = data.get("response", "")
        if not response:
            return None

        return guard_run(
            {
                "response": response,
                "assistant_response": response,
                "prompt": data.get("prompt") or data.get("user_prompt") or "",
                "user_prompt": data.get("user_prompt") or data.get("prompt") or "",
                "message": data.get("message") or "",
                "transcript": data.get("transcript", []),
            }
        )
    except Exception as e:
        _logger.warning(f"dependency_chain_guard error: {e}")
        return None


def _run_comparative_claim_guard(data: dict) -> dict | None:
    """Activate existing file/skill comparative verification guard."""
    # Claim-type short-circuit: skip on irrelevant claim types
    _, terminal_id = _resolve_scope_ids(data)
    claim_type = _read_claim_type(terminal_id)
    # comparative_claim_guard relevant for: mechanism_investigation
    if not _claim_relevant(claim_type, frozenset({"mechanism_investigation"})):
        return None  # Skip: claim type not relevant

    if os.environ.get("COMPARATIVE_CLAIM_GUARD_ENABLED", "true").lower() not in (
        "1",
        "true",
        "yes",
    ):
        return None
    try:
        from Stop_comparative_claim_guard import check

        result = check(
            {
                "assistant_response": data.get("response", ""),
                "tool_events": data.get("tool_events", []),
                "transcript_path": data.get("transcript_path", ""),
                "transcript": data.get("transcript", []),
                "session_id": data.get("session_id") or data.get("sessionId") or "",
                "terminal_id": data.get("terminal_id") or data.get("terminalId") or "",
            }
        )
        if result and not result.get("allow", True):
            return {
                "decision": "block",
                "reason": result.get("reason", "Comparative claim without verification."),
                "blocking_hook": result.get("blocking_hook", "Stop.py:comparative_claim_guard"),
            }
        return None
    except Exception as e:
        _logger.warning(f"comparative_claim_guard error: {e}")
        return None


def _run_narrative_intent(data: dict) -> dict | None:
    """narrative_intent_detector.py — warn on un-hedged design-intent speculation."""
    # Claim-type short-circuit: skip on irrelevant claim types
    _, terminal_id = _resolve_scope_ids(data)
    claim_type = _read_claim_type(terminal_id)
    if not _claim_relevant(claim_type, _CLAIM_GATE_RELEVANCE["narrative_intent"]):
        return None  # Skip: claim type not relevant

    try:
        from narrative_intent_detector import evaluate_narratives

        response = data.get("response", "")
        if not response:
            return None

        result = evaluate_narratives(response, session_id=data.get("session_id", ""))

        if result.get("decision") == "warn" and result.get("systemMessage"):
            return {"systemMessage": result["systemMessage"]}
        return None
    except Exception as e:
        # Narrative detector fails OPEN
        _logger.warning(f"narrative_intent error: {e}")
        return None


def _run_anti_sycophancy_quality(data: dict) -> dict | None:
    """Run anti-sycophancy behavioral detectors (affirmation/overconfidence/lazy closure)."""
    _, terminal_id = _resolve_scope_ids(data)
    claim_type = _read_claim_type(terminal_id)
    if not _claim_relevant(claim_type, _CLAIM_GATE_RELEVANCE["anti_sycophancy_quality"]):
        return None
    try:
        import os

        from anti_sycophancy.affirmation_detector import detect_praise_opener
        from anti_sycophancy.lazy_closure_detector import detect_all_lazy_closure
        from anti_sycophancy.overconfidence_detector import detect_all_overconfidence
        from anti_sycophancy.destructive_cleanup_detector import detect_all_destructive_cleanup

        response = data.get("response", "")

        # PROBE: log lam length for truncation verification (remove after)
        try:
            import time as _t
            _pp = HOOKS_DIR / "logs" / "lam_truncation_probe.jsonl"
            from file_lock import append_jsonl_safe
            append_jsonl_safe(_pp, {
                "ts": _t.time(),
                "lam_len": len(response),
                "lam_words": len(response.split()) if response else 0,
                "first_60": response[:60] if response else "",
                "last_60": response[-60:] if response else "",
            })
        except OSError:
            pass

        if not response:
            return None

        messages: list[str] = []

        if os.environ.get("AFFIRMATION_DETECTOR_ENABLED", "true").lower() in ("1", "true", "yes"):
            praise = detect_praise_opener(response)
            if praise and praise.self_prompt:
                _append_anti_sycophancy_log(
                    data=data,
                    detector="affirmation_detector",
                    severity="warn",
                    findings=[praise.matched],
                )
                messages.append(praise.self_prompt.strip())

        if os.environ.get("OVERCONFIDENCE_DETECTOR_ENABLED", "true").lower() in (
            "1",
            "true",
            "yes",
        ):
            # Real Stop payloads carry no tool_events; fall back to transcript so
            # the comparison-evidence exemption can apply (else structural claims
            # backed by real comparison work are falsely flagged).
            tool_events = data.get("tool_events")
            if not tool_events:
                from __lib.turn_tool_events import build_turn_tool_events
                tool_events = build_turn_tool_events(data.get("transcript_path", ""))
            overconfidence = detect_all_overconfidence(response, tool_events=tool_events)
            if overconfidence:
                block_matches = [m for m in overconfidence if m.severity == "block"]
                if block_matches:
                    samples = ", ".join(sorted({m.matched for m in block_matches})[:3])
                    _append_anti_sycophancy_log(
                        data=data,
                        detector="overconfidence_detector",
                        severity="block",
                        findings=sorted({m.matched for m in block_matches}),
                    )
                    return {
                        "decision": "block",
                        "reason": (
                            "OVERCONFIDENCE VIOLATION: Blocking severity overconfidence patterns detected. "
                            f"Examples: {samples}"
                        ),
                        "blocking_hook": "Stop.py:anti_sycophancy_quality",
                    }
                _append_anti_sycophancy_log(
                    data=data,
                    detector="overconfidence_detector",
                    severity="warn",
                    findings=sorted({m.matched for m in overconfidence}),
                )
                sample = sorted({f"{m.matched} -> {m.suggestion}" for m in overconfidence})[:5]
                messages.append("OVERCONFIDENCE CHECK:\n- " + "\n- ".join(sample))

        if os.environ.get("LAZY_CLOSURE_DETECTOR_ENABLED", "true").lower() in ("1", "true", "yes"):
            lazy = detect_all_lazy_closure(response)
            # After a format-only repair, suppress lazy_fix to avoid
            # infinite loop between format repair and lazy_closure flags.
            if lazy:
                _epistemic_verdict = None
                try:
                    from epistemic_validator import validate as _ev_validate
                    _epistemic_verdict = _ev_validate(response)
                except Exception:
                    pass
                if _epistemic_verdict and _epistemic_verdict.issues:
                    all_format = all(i.type == "format" for i in _epistemic_verdict.issues)
                    if all_format:
                        lazy = [m for m in lazy if m.pattern_type != "lazy_fix"]
                # Only suppress plan_mode_futurizing on plan/execution-report turns.
                # lazy_fix and sycophancy_capitulation are UNCONDITIONAL —
                # they fire regardless of turn mode.
                _turn = _classify_turn_mode(data)
                if _turn in ("plan", "execution-report"):
                    lazy = [m for m in lazy if m.pattern_type != "plan_mode_futurizing"]
            if lazy:
                block_matches = [m for m in lazy if m.severity == "block"]
                if block_matches:
                    samples = ", ".join(sorted({m.matched for m in block_matches})[:3])
                    _append_anti_sycophancy_log(
                        data=data,
                        detector="lazy_closure_detector",
                        severity="block",
                        findings=sorted({m.matched for m in block_matches}),
                    )
                    return {
                        "decision": "block",
                        "reason": (
                            "LAZY CLOSURE VIOLATION: Blocking severity lazy-closure patterns detected. "
                            f"Examples: {samples}"
                        ),
                        "blocking_hook": "Stop.py:anti_sycophancy_quality",
                    }
                _append_anti_sycophancy_log(
                    data=data,
                    detector="lazy_closure_detector",
                    severity="warn",
                    findings=sorted({m.matched for m in lazy}),
                )
                sample = sorted({f"{m.matched} -> {m.suggestion}" for m in lazy})[:5]
                messages.append("LAZY CLOSURE CHECK:\n- " + "\n- ".join(sample))

        if os.environ.get("DESTRUCTIVE_CLEANUP_DETECTOR_ENABLED", "true").lower() in (
            "1",
            "true",
            "yes",
        ):
            cleanup = detect_all_destructive_cleanup(response)
            if cleanup:
                _append_anti_sycophancy_log(
                    data=data,
                    detector="destructive_cleanup_detector",
                    severity="warn",
                    findings=[m.matched for m in cleanup],
                )
                samp = "\n- ".join(
                    f"{m.matched}: {m.suggestion}" for m in cleanup
                )
                messages.append("DESTRUCTIVE CLEANUP ADVISORY:\n- " + samp)

        if os.environ.get("RESPONSE_STRUCTURE_DETECTOR_ENABLED", "true").lower() in (
            "1",
            "true",
            "yes",
        ):
            from anti_sycophancy.response_structure_detector import (
                build_self_prompt as _build_structure_prompt,
            )
            from anti_sycophancy.response_structure_detector import (
                detect_response_structure,
            )

            structure = detect_response_structure(response)
            if structure:
                _append_anti_sycophancy_log(
                    data=data,
                    detector="response_structure_detector",
                    severity="warn",
                    findings=[f"{m.pattern}: {m.matched}" for m in structure],
                )
                messages.append(_build_structure_prompt(structure))
        if messages:
            return {"systemMessage": "\n\n".join(messages)}
        return None
    except Exception as e:
        _logger.warning(f"anti_sycophancy_quality error: {e}")
        return None


def _run_command_execution_validator(data: dict) -> dict | None:
    """Run command_execution_validator.py as a blocking gate."""
    try:
        validator = HOOKS_DIR / "command_execution_validator.py"
        if not validator.exists():
            return None
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [sys.executable, str(validator)],
            input=json.dumps(data).encode(),
            capture_output=True,
            timeout=5.0,
            creationflags=creation_flags,
        )
        if result.returncode == 2:
            reason = (
                result.stderr.decode(errors="replace").strip()
                or "Command execution validation failed."
            )
            return {
                "decision": "block",
                "reason": reason,
                "blocking_hook": "Stop.py:command_execution_validator",
            }
        return None
    except Exception as e:
        _logger.warning(f"command_execution_validator error: {e}")
        return None


def _run_behavior_gates_agreement(data: dict) -> dict | None:
    """Stop_behavior_gates.py Gate 3 — block empty agreements without action tools."""
    try:
        from Stop_behavior_gates import _extract_tools_used, check_gate3_agreement

        # Extract response text and tools from data
        response_text = data.get("response", "")
        tools_output = data.get("tool_calls", "")
        user_prompt = data.get("user_prompt") or data.get("prompt") or ""

        # Extract tools using helper from behavior_gates module
        tools_used = _extract_tools_used(tools_output)

        # v2.1: Get working directory for telemetry (use project_root, not cwd)
        project_root = Path(__file__).resolve().parents[1]  # P:\ from P:\.claude\hooks\
        working_dir = data.get("working_dir", project_root)

        # Run gate check (now with working_dir and user_prompt for turn-mode classification)
        is_violation, reason = check_gate3_agreement(response_text, tools_used, working_dir, user_prompt)

        if is_violation:
            return {
                "decision": "block",
                "reason": f"Empty agreement detected: {reason}",
                "blocking_hook": "Stop.py:behavior_gates_agreement",
            }
        return None
    except Exception as e:
        # Fails OPEN
        _logger.warning(f"behavior_gates_agreement error: {e}")
        return None


def _run_behavior_gates_guidance(data: dict) -> dict | None:
    """Stop_behavior_gates.py Gate 1 — warn about guidance without Read verification."""
    _, terminal_id = _resolve_scope_ids(data)
    claim_type = _read_claim_type(terminal_id)
    if not _claim_relevant(claim_type, _CLAIM_GATE_RELEVANCE["behavior_gates_guidance"]):
        return None
    try:
        from Stop_behavior_gates import _extract_tools_used, check_gate1_guidance

        response_text = data.get("response", "")
        tools_output = data.get("tool_calls", "")
        tools_used = _extract_tools_used(tools_output)

        # v2.1: Get working directory for telemetry (use project_root, not cwd)
        project_root = Path(__file__).resolve().parents[1]  # P:\ from P:\.claude\hooks\
        working_dir = data.get("working_dir", project_root)

        # Run gate check (now with working_dir for telemetry)
        is_violation, reason = check_gate1_guidance(response_text, tools_used, working_dir)

        if is_violation:
            return {
                "decision": "block",
                "reason": f"GUIDANCE WITHOUT EVIDENCE: {reason}",
                "blocking_hook": "Stop.py:behavior_gates_guidance",
            }
        return None
    except Exception as e:
        _logger.warning(f"behavior_gates_guidance error: {e}")
        return None


def _run_behavior_gates_blacklist(data: dict) -> dict | None:
    """Stop_behavior_gates.py Gate 2 — warn about blacklisted tools."""
    _, terminal_id = _resolve_scope_ids(data)
    claim_type = _read_claim_type(terminal_id)
    if not _claim_relevant(claim_type, _CLAIM_GATE_RELEVANCE["behavior_gates_blacklist"]):
        return None
    try:
        from Stop_behavior_gates import _extract_tools_used, check_gate2_tools

        response_text = data.get("response", "")
        tools_output = data.get("tool_calls", "")
        tools_used = _extract_tools_used(tools_output)

        # v2.1: Get working directory for project blacklist (use project_root, not cwd)
        project_root = Path(__file__).resolve().parents[1]  # P:\ from P:\.claude\hooks\
        working_dir = data.get("working_dir", project_root)

        # Run gate check (now with working_dir for project blacklist)
        is_violation, reason = check_gate2_tools(response_text, tools_used, working_dir)

        if is_violation:
            return {
                "decision": "block",
                "reason": f"BLACKLISTED TOOL USE: {reason}",
                "blocking_hook": "Stop.py:behavior_gates_blacklist",
            }
        return None
    except Exception as e:
        _logger.warning(f"behavior_gates_blacklist error: {e}")
        return None


def _run_advisory(data: dict) -> dict | None:
    """Stop_advisory.py logic - non-blocking suggestions."""
    try:
        from Stop_advisory import check_advisories

        response = data.get("response", "")
        if not response:
            return None

        messages: list[str] = []

        suggestions = check_advisories(response)
        if suggestions:
            messages.append("\n\n\U0001f4a1 **ADVISORY**: " + " | ".join(suggestions))

        if messages:
            return {"systemMessage": "".join(messages)}
        return None
    except Exception as e:
        _logger.warning(f"advisory error: {e}")
        return None


def _safe_id(value: str | None) -> str:
    """Convert session/terminal id to filesystem-safe fragment."""
    if not value:
        return "unknown"
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


def _resolve_scope_ids(data: dict) -> tuple[str, str]:
    """Resolve session_id and terminal_id for scoped state lookups."""
    session_obj = data.get("session")
    nested_session_id = ""
    nested_terminal_id = ""
    if isinstance(session_obj, dict):
        nested_session_id = str(
            session_obj.get("id")
            or session_obj.get("session_id")
            or session_obj.get("sessionId")
            or ""
        )
        nested_terminal_id = str(
            session_obj.get("terminal_id") or session_obj.get("terminalId") or ""
        )
    session_id = (
        nested_session_id
        or data.get("session_id")
        or data.get("sessionId")
        or data.get("CLAUDE_SESSION_ID")
        or os.environ.get("CLAUDE_SESSION_ID")
        or ""
    )
    terminal_id = (
        nested_terminal_id
        or data.get("terminal_id")
        or data.get("terminalId")
        or data.get("CLAUDE_TERMINAL_ID")
        or os.environ.get("CLAUDE_TERMINAL_ID")
        or ""
    )
    return str(session_id), str(terminal_id)


def _pin_scope_env(data: dict) -> None:
    """Pin scope ids in payload + env so side-effects resolve same scope."""
    session_id, terminal_id = _resolve_scope_ids(data)
    if session_id:
        session_id = session_id.strip()
        data.setdefault("session_id", session_id)
        os.environ["CLAUDE_SESSION_ID"] = session_id

    if not terminal_id:
        try:
            from __lib.terminal_detection import detect_terminal_id

            terminal_id = (detect_terminal_id() or "").strip()
        except Exception:
            terminal_id = ""
    if terminal_id:
        terminal_id = terminal_id.strip()
        data.setdefault("terminal_id", terminal_id)
        os.environ["CLAUDE_TERMINAL_ID"] = terminal_id


def _run_skill_first_stop_gate(data: dict) -> dict | None:
    """Block if user typed /command but the LLM responded with zero tools.

    This is the safety net for the PreToolUse skill-first gate. PreToolUse
    blocks tool calls before Skill() is invoked, but it can't catch the case
    where the LLM produces a pure-prose response with no tool calls at all.
    """
    import re

    session_id, terminal_id = _resolve_scope_ids(data)
    if not session_id:
        return None

    mode = _skill_first_mode_stop()
    if mode == "off":
        return None

    safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id)
    safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)

    # Check if there's still a pending skill intent (not cleared by PostToolUse)
    #
    # IMPORTANT: The lookup order MUST mirror PreToolUse._check_skill_first_gate()
    # and the deletion logic in PreToolUse (Skill-tool handler). skill_enforcer.py
    # (UserPromptSubmit) writes the per-terminal NESTED format and actively deletes
    # the flat format, so the nested path must be checked FIRST. A prior version of
    # this gate read only the flat path, which UPS no longer writes — that made this
    # backstop silently dead, letting prose-only responses to slash commands stand
    # unblocked (the persistent-halt bug).
    #
    # Current format (TASK-005+): terminals/{terminal_id}/pending_command_intent.json
    # Legacy flat terminal:       pending_command_intent_{terminal_id}.json
    # Legacy flat session:        pending_command_intent_{session_id}.json
    state_dir = HOOKS_DIR / "state"
    fallback_dir = Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state"
    intent_file = None

    # Primary: per-terminal nested directory format (what UPS actually writes today)
    if terminal_id:
        for base in (state_dir, fallback_dir):
            candidate = base / "terminals" / terminal_id / "pending_command_intent.json"
            if candidate.exists():
                intent_file = candidate
                break

        # Dash-stripped fallback for terminal-id normalization drift
        if not intent_file and terminal_id.startswith("console_"):
            stripped = f"console_{terminal_id[8:].replace('-', '')}"
            if stripped != terminal_id:
                for base in (state_dir, fallback_dir):
                    candidate = base / "terminals" / stripped / "pending_command_intent.json"
                    if candidate.exists():
                        intent_file = candidate
                        break

    # Secondary: legacy flat terminal-scoped format
    if not intent_file:
        for base in (state_dir, fallback_dir):
            candidate = base / f"pending_command_intent_{safe_terminal}.json"
            if candidate.exists():
                intent_file = candidate
                break

    # Tertiary: legacy session-scoped format (for backwards compatibility)
    if not intent_file:
        for base in (state_dir, fallback_dir):
            candidate = base / f"pending_command_intent_{safe_session}.json"
            if candidate.exists():
                intent_file = candidate
                break

    if not intent_file:
        return None

    try:
        intent = json.loads(intent_file.read_text(encoding="utf-8"))
        skill_name = intent.get("skill", "")
        if not skill_name:
            intent_file.unlink(missing_ok=True)
            return None

        # Clear the intent file to avoid blocking the next turn
        intent_file.unlink(missing_ok=True)
        _log_skill_first_stop_event("inline_response_before_skill", session_id, skill_name, mode)

        if mode == "monitor":
            return None

        # Silent steering: deliver the directive to the MODEL only via
        # hookSpecificOutput.additionalContext (CLI honors it as a system
        # reminder), NOT via `reason` which renders to the user as a
        # "Stop hook error" banner. decision=block still forces the retry.
        directive = (
            f"[E_SKILL_FIRST_INLINE_BYPASS]\n"
            f"SLASH COMMAND IGNORED\n\n"
            f"You typed /{skill_name} but responded with prose without calling the Skill tool.\n\n"
            f"You MUST:\n"
            f'1. Call Skill(skill="{skill_name}") to load the skill\n'
            f"2. Follow the skill's workflow instructions\n"
            f"3. READ THE LAST 10-20 MESSAGES of conversation to infer context before asking clarifying questions\n\n"
            f"Do NOT read the SKILL.md file manually or improvise your own version.\n"
            f"Do NOT bypass this by returning inline analysis text without Skill(...)."
        )
        return {
            "decision": "block",
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": directive,
            },
            "blocking_hook": "Stop.py:skill_first_stop_gate",
        }
    except Exception:
        # Fail open
        return None


def _check_post_skill_prose_response(data: dict) -> dict | None:
    """Detect prose response immediately after Skill() was called.

    This catches the case where AI calls Skill() but then responds with prose
    instead of using execution tools (Bash, Task, etc.) to execute the skill's workflow.

    Args:
        data: Stop hook input data

    Returns:
        Block decision dict if violation detected, None otherwise
    """
    try:
        from Stop_behavior_gates import _extract_tools_used

        # Extract tool names from this turn
        tools_used = _extract_tools_used(data.get("tool_calls", ""))

        # If Skill tool wasn't used, this check doesn't apply
        if "Skill" not in tools_used:
            return None

        # Check if execution tools were used
        execution_tools = {"Bash", "Task", "Write", "Edit", "Grep", "Glob", "Read"}
        execution_used = any(t in tools_used for t in execution_tools)
        execution_tools_used = [t for t in tools_used if t in execution_tools]

        # Extract skill name and context for logging
        skill_name = _extract_skill_name_from_data(data) or "unknown"
        session_id = data.get("session_id", "unknown")
        terminal_id = data.get("terminal_id", "unknown")

        # Determine skill type
        skill_type = "execution" if _is_execution_skill(skill_name) else "knowledge"

        # If Skill was called but NO execution tools used → prose response (BLOCK)
        if not execution_used:
            # Check if it's an execution skill (has workflow_steps)
            if skill_type == "execution":
                # Log block decision with enhanced fields
                try:
                    _log_post_skill_prose_event(
                        decision="block",
                        skill_name=skill_name,
                        skill_type=skill_type,
                        tools_used=list(tools_used),
                        execution_tools_used=execution_tools_used,
                        reason="E_POST_SKILL_PROSE_RESPONSE",
                        session_id=session_id,
                        terminal_id=terminal_id,
                    )
                except Exception:
                    # Logging failures don't break the gate
                    pass

                return {
                    "decision": "block",
                    "reason": (
                        f"[E_POST_SKILL_PROSE_RESPONSE]\n"
                        f"WORKFLOW EXECUTION REQUIRED\n\n"
                        f"You just loaded skill: /{skill_name}\n\n"
                        f"NEXT STEP: Follow the skill's workflow_steps (from SKILL.md)\n\n"
                        f"✓ Use Bash/Task/Read tools to execute the workflow\n"
                        f"✗ Do NOT respond with prose analysis or summaries\n"
                        f"✗ Do NOT skip steps or improvise your own approach\n\n"
                        f"The skill has documented workflow_steps for a reason — follow them."
                    ),
                    "blocking_hook": "Stop.py:post_skill_workflow_gate",
                }

        # Log allow decision (Skill used + execution tools, or knowledge skill)
        try:
            _log_post_skill_prose_event(
                decision="allow",
                skill_name=skill_name,
                skill_type=skill_type,
                tools_used=list(tools_used),
                execution_tools_used=execution_tools_used,
                reason="allow: execution_tools_used"
                if execution_used
                else "allow: knowledge_skill",
                session_id=session_id,
                terminal_id=terminal_id,
            )
        except Exception:
            # Logging failures don't break the gate
            pass

        return None

    except Exception:
        # Fail open - don't break the entire Stop hook
        return None


def _log_post_skill_prose_event(
    decision: str,
    skill_name: str,
    skill_type: str,
    tools_used: list[str],
    execution_tools_used: list[str],
    reason: str,
    session_id: str,
    terminal_id: str,
) -> None:
    """Log post-skill prose detection event with enhanced fields.

    Args:
        decision: "block" or "allow"
        skill_name: Name of skill invoked
        skill_type: "execution" or "knowledge"
        tools_used: List of all tools used this turn
        execution_tools_used: List of execution tools used
        reason: Reason for decision
        session_id: Session identifier
        terminal_id: Terminal identifier
    """
    if not _env_bool("SKILL_FIRST_LOGGING_ENABLED", default=True):
        return

    import time
    from pathlib import Path

    log_path = Path(__file__).resolve().parent / "skill_first_enforcement.jsonl"

    log_entry = {
        "timestamp": time.time(),
        "hook": "Stop",
        "event": "post_skill_prose_response",
        "decision": decision,
        "skill_name": skill_name,
        "skill_type": skill_type,
        "tools_used": tools_used,
        "execution_tools_used": execution_tools_used,
        "reason": reason,
        "session_id": session_id,
        "terminal_id": terminal_id,
    }

    try:
        from file_lock import append_jsonl_safe
        append_jsonl_safe(log_path, log_entry)
    except OSError:
        # Fail open - logging errors don't break the gate
        pass


def _extract_skill_name_from_data(data: dict) -> str | None:
    """Extract skill name from tool input data.

    Args:
        data: Stop hook input data

    Returns:
        Skill name or None
    """
    try:
        # First, check if tool_input is at top level (most common format)
        tool_input = data.get("tool_input", {})
        if isinstance(tool_input, dict) and "skill" in tool_input:
            return tool_input.get("skill")

        # Second, check if tool_input is in XML string format
        if isinstance(tool_input, str):
            import re

            skill_match = re.search(r'<parameter name="skill">(.*?)</parameter>', tool_input)
            if skill_match:
                return skill_match.group(1)

        # Third, check tool_calls list format (less common)
        tool_calls = data.get("tool_calls", "")
        if isinstance(tool_calls, list):
            for tool in tool_calls:
                if isinstance(tool, dict) and tool.get("name") == "Skill":
                    input_data = tool.get("input", {})
                    if isinstance(input_data, dict) and "skill" in input_data:
                        return input_data.get("skill")

        # Fourth, check for XML in tool_calls string
        elif isinstance(tool_calls, str):
            import re

            skill_match = re.search(r'<parameter name="skill">(.*?)</parameter>', tool_calls)
            if skill_match:
                return skill_match.group(1)

        return None

    except Exception:
        return None


def _is_execution_skill(skill_name: str) -> bool:
    """Check if skill requires execution tools vs knowledge-only.

    Args:
        skill_name: Name of the skill (without / prefix)

    Returns:
        True if skill has workflow_steps (execution skill), False otherwise
    """
    try:
        from skill_guard.breadcrumb.tracker import _load_workflow_steps

        # Try to load workflow steps for this skill
        result = _load_workflow_steps(skill_name)
        workflow_steps = result.steps

        # Has workflow_steps = execution skill
        # Empty list or None = knowledge skill
        is_execution = bool(workflow_steps)

        return is_execution

    except ModuleNotFoundError as e:
        # skill-guard package not installed — log as non-blocking, fail open
        _logger.warning(f"skill_guard import skipped (non-blocking): {e}")
        return False
    except Exception:
        # Other errors — fail open to avoid cascading blocks
        return False


# Blocking gate sequence - evaluated in order, first block wins


def _run_reflect_integration(data: dict) -> dict | None:
    """Stop_reflect_integration.py logic - spawn background reflection."""
    try:
        import Stop_reflect_integration

        return Stop_reflect_integration.run_reflect_hook(data)
    except Exception as e:
        _logger.warning(f"reflect_integration error: {e}")
        return None


def _run_existence_gate(data: dict) -> dict | None:
    """Disabled: Strategy B+C now handled by unified_claim_verifier via _run_behavior_audit."""
    return None


def _run_lazy_workaround_gate(data: dict) -> dict | None:
    """Detect accept-bug-as-feature lazy workaround suggestions."""
    _, terminal_id = _resolve_scope_ids(data)
    claim_type = _read_claim_type(terminal_id)
    if not _claim_relevant(claim_type, _CLAIM_GATE_RELEVANCE["lazy_workaround_gate"]):
        return None
    try:
        _turn = _classify_turn_mode(data)
        response = data.get("response", "")
        if not response:
            return None

        decision = determine_epistemic_applicability(response, turn_mode=_turn)

        # enforcement_level=="none": turn mode suppressed (Layer 1)
        if not decision.applicable:
            return None

        import Stop_lazy_workaround_gate

        # enforcement_level=="simple": simple/delivery responses — skip lazy check
        if decision.enforcement_level == "simple":
            return None
        result = Stop_lazy_workaround_gate.check_lazy_workarounds(response)
        if result.get("decision") == "block":
            return {
                "decision": "block",
                "reason": result.get("message", "LAZY WORKAROUND DETECTED"),
                "blocking_hook": "Stop_lazy_workaround_gate.py",
            }
        return None
    except Exception:
        return None


def _run_recommendation_gate(data: dict) -> dict | None:
    """Detect options presented without a recommendation."""
    _, terminal_id = _resolve_scope_ids(data)
    claim_type = _read_claim_type(terminal_id)
    if not _claim_relevant(claim_type, _CLAIM_GATE_RELEVANCE["recommendation_gate"]):
        return None
    try:
        import Stop_recommendation_gate

        response = data.get("response", "")
        if not response:
            return None
        return Stop_recommendation_gate.check_recommendation(response, data)
    except Exception as e:
        _logger.warning(f"recommendation_gate error: {e}")
        return None


def _run_reasoning_quality_gate(data: dict) -> dict | None:
    """Run automatic reasoning quality gate on responses using reasoning package."""
    try:
        hook_path = HOOKS_DIR / "Stop_reasoning_quality_gate.py"
        if not hook_path.exists():
            return None

        user_prompt = data.get("user_prompt") or data.get("prompt") or ""
        # DEBUG_GATES session mode: disable all quality gates (including reasoning quality).
        # Weak (non-Claude) models also skip reasoning-quality nagging.
        gate_session_mode = get_session_mode(user_prompt)
        if is_quality_gate_disabled(gate_session_mode) or is_weak_model(data):
            return None

        response = data.get("response", "")
        if not response or len(response) < 200:
            return None

        # Trivial exchange bypass: skip reasoning quality nagging on low-stakes turns.
        turn_mode = _classify_turn_mode(data)
        contract_active = False
        try:
            from __lib.task_contract import load_contract as _load_contract
            _, tid = _resolve_scope_ids(data)
            if tid and _load_contract(tid):
                contract_active = True
        except Exception:
            pass

        trivial, trivial_reason = _is_trivial_exchange(
            context=data,
            response=response,
            turn_mode=turn_mode,
            contract_active=contract_active,
        )
        if trivial:
            from __lib.trivial_turns import log_trivial_skip
            log_trivial_skip("reasoning_quality_gate", trivial_reason, turn_mode, response)
            return None

        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(data).encode(),
            capture_output=True,
            timeout=1.0,  # 1 second timeout
            creationflags=creation_flags,
        )

        if result.returncode == 0 and result.stdout:
            try:
                output = json.loads(result.stdout.decode())
                if output.get("systemMessage"):
                    return {"systemMessage": output["systemMessage"]}
            except json.JSONDecodeError:
                pass

        return None
    except Exception as e:
        # Fail open - don't block on reasoning quality gate errors
        _logger.warning(f"reasoning_quality_gate error: {e}")
        return None


def _run_reasoning_enhanced(data: dict) -> dict | None:
    """Run enhanced reasoning quality gate with full 5-stage thought chain."""
    try:
        # Check for the enhanced hook in .claude/hooks (symlinked from package)
        hook_path = HOOKS_DIR / "Stop_reasoning_enhanced.py"
        if not hook_path.exists():
            # Fallback to package path if symlink not created
            hook_path = Path("P:/packages/reasoning/hooks/Stop_reasoning_enhanced.py")
            if not hook_path.exists():
                return None

        response = data.get("response", "")
        if not response or len(response) < 200:
            return None

        # Trivial exchange bypass: skip enhanced reasoning quality nagging on low-stakes turns.
        turn_mode = _classify_turn_mode(data)
        contract_active = False
        try:
            from __lib.task_contract import load_contract as _load_contract
            _, tid = _resolve_scope_ids(data)
            if tid and _load_contract(tid):
                contract_active = True
        except Exception:
            pass

        trivial, trivial_reason = _is_trivial_exchange(
            context=data,
            response=response,
            turn_mode=turn_mode,
            contract_active=contract_active,
        )
        if trivial:
            from __lib.trivial_turns import log_trivial_skip
            log_trivial_skip("reasoning_enhanced", trivial_reason, turn_mode, response)
            return None

        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(data).encode(),
            capture_output=True,
            timeout=2.0,  # 2 second timeout for enhanced reasoning
            creationflags=creation_flags,
        )

        if result.returncode == 0 and result.stdout:
            try:
                output = json.loads(result.stdout.decode())
                if output.get("systemMessage"):
                    return {"systemMessage": output["systemMessage"]}
            except json.JSONDecodeError:
                pass

        return None
    except Exception as e:
        # Fail open - don't block on enhanced reasoning errors
        _logger.warning(f"reasoning_enhanced error: {e}")
        return None


def _run_post_skill_prose_gate(data: dict) -> dict | None:
    """Post-Skill prose response detection - prevents AI from responding with prose after calling Skill()."""
    # Claim-type short-circuit: skip on irrelevant claim types
    _, terminal_id = _resolve_scope_ids(data)
    claim_type = _read_claim_type(terminal_id)
    if not _claim_relevant(claim_type, _CLAIM_GATE_RELEVANCE["post_skill_prose_gate"]):
        return None  # Skip: claim type not relevant
    return _check_post_skill_prose_response(data)


def _run_verification_enforcement(data: dict) -> dict | None:
    """Enforce verification step completion - blocks if verification steps are incomplete.

    Checks breadcrumb trails for pending verification steps (steps with kind: verification
    that are not in completed_steps). Blocks when enforcement is enabled and pending
    verification is detected.

    Environment variables:
        VERIFICATION_ENFORCEMENT_ENABLED: Enable/disable enforcement (default: false)

    Bypass flags:
        --skip-verification: Allow this turn even with pending verification
    """
    try:
        # Claim-type short-circuit: skip on irrelevant claim types
        _, terminal_id = _resolve_scope_ids(data)
        claim_type = _read_claim_type(terminal_id)
        if not _claim_relevant(claim_type, _CLAIM_GATE_RELEVANCE["verification_enforcement"]):
            return None  # Skip: claim type not relevant

        # Check if enforcement is enabled
        if not _env_bool("VERIFICATION_ENFORCEMENT_ENABLED", default=False):
            return None

        # Check for bypass flag in user message
        user_message = data.get("userMessage", "") or data.get("user_message", "")
        if "--skip-verification" in user_message:
            return None

        # Import breadcrumb tracker
        try:
            from skill_guard.breadcrumb.tracker import get_active_breadcrumb_trails
        except ModuleNotFoundError as e:
            # skill-guard not installed — log as non-blocking, skip silently
            _logger.warning(f"skill_guard import skipped (non-blocking): {e}")
            return None

        # Get all active breadcrumb trails for this terminal
        trails = get_active_breadcrumb_trails()

        # Check each trail for pending verification steps
        pending_verifications = []
        for trail in trails:
            skill_name = trail.get("skill", "unknown")
            workflow_steps = trail.get("workflow_steps", [])
            completed_steps = trail.get("completed_steps", [])

            # Extract verification step IDs (filter for kind: verification)
            verification_step_ids = []
            for step in workflow_steps:
                if isinstance(step, dict):
                    if step.get("kind") == "verification":
                        step_id = step.get("id")
                        if step_id:
                            verification_step_ids.append(step_id)

            # Check if any verification steps are not completed
            for step_id in verification_step_ids:
                if step_id not in completed_steps:
                    pending_verifications.append(f"{skill_name}:{step_id}")

        # If no pending verifications, allow
        if not pending_verifications:
            return None

        # Block with message listing missing verification steps
        return {
            "decision": "block",
            "reason": (
                "PENDING VERIFICATION STEPS DETECTED\n\n"
                "The following verification steps must be completed before stopping:\n"
                + "\n".join(f"  • {step}" for step in pending_verifications)
                + "\n\n"
                "To bypass for this turn: Add --skip-verification to your message\n"
                "To disable enforcement: Set VERIFICATION_ENFORCEMENT_ENABLED=false"
            ),
            "blocking_hook": "Stop.py:verification_enforcement",
        }

    except Exception:
        # Fail open - don't block on verification enforcement errors
        # Note: Using logging would be better, but keeping consistent with existing error handling pattern in Stop.py
        return None


def _claim_relevant(claim_type: str | None, relevant: set[str]) -> bool:
    """Return True if claim_type is in the relevant set, or if claim_type is unknown (assume relevance)."""
    if claim_type is None:
        return True  # Unknown = assume relevant
    return claim_type in relevant


# Claim-type relevance maps: gate name -> set of relevant claim types
_CLAIM_GATE_RELEVANCE: dict[str, frozenset] = {
    "frameguard_stop": frozenset({"mechanism_investigation", "design_recommendation"}),
    "skill_first_stop_gate": frozenset({"code_work"}),
    "post_skill_prose_gate": frozenset({"style_heavy", "mechanism_investigation"}),
    "verification_enforcement": frozenset({"mechanism_investigation"}),
    "narrative_intent": frozenset({"style_heavy", "question"}),
    "behavior_gates_guidance": frozenset({"mechanism_investigation", "design_recommendation"}),
    "behavior_gates_blacklist": frozenset({"code_work", "mechanism_investigation"}),
    "anti_sycophancy_quality": frozenset({"style_heavy", "question"}),
    "lazy_workaround_gate": frozenset({"code_work", "mechanism_investigation"}),
    "recommendation_gate": frozenset({"design_recommendation", "mechanism_investigation"}),
}


def _run_frameguard_stop(data: dict) -> dict | None:
    """FrameGuard Stop hook - validates systemic frame handling."""
    try:
        import subprocess

        # Claim-type short-circuit: skip on irrelevant claim types
        _, terminal_id = _resolve_scope_ids(data)
        claim_type = _read_claim_type(terminal_id)
        if not _claim_relevant(claim_type, _CLAIM_GATE_RELEVANCE["frameguard_stop"]):
            return None  # Skip: claim type not relevant

        enabled = os.environ.get("FRAMEGUARD_ENABLED", "true").lower() == "true"
        if not enabled:
            return None

        # Run frameguard_stop.py as subprocess for isolation
        result = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "frameguard_stop.py")],
            input=json.dumps(data).encode("utf-8"),
            capture_output=True,
            timeout=5,
            text=True,
        )

        if result.returncode == 2:  # Block
            response = json.loads(result.stdout or "{}")
            return {
                "decision": "block",
                "reason": response.get("reason", "FRAMEGUARD: Systemic frame not addressed"),
                "blocking_hook": "Stop.py:frameguard_stop",
            }
        return None  # Allow
    except (subprocess.TimeoutExpired, json.JSONDecodeError, Exception):
        # Fail open - don't block on FrameGuard errors
        return None


def _run_deletion_verification_guard(data: dict) -> dict | None:
    """Deletion verification guard - checks actual file system state.

    Blocks responses claiming files are deleted WITHOUT verifying the files
    ACTUALLY don't exist on the file system.

    Unlike tool-based verification, this checks Path.exists() for the actual
    files mentioned in deletion claims.
    """
    try:
        from Stop_deletion_verification_guard import check as deletion_check
    except ImportError:
        return None  # Hook not available

    response = data.get("response", "")
    if not response:
        return None

    result = deletion_check(data)
    if result and result.get("decision") == "block":
        return {
            "decision": "block",
            "reason": result.get("reason", ""),
            "blocking_hook": "Stop_deletion_verification_guard",
        }
    return None


def _run_git_diff_reground(data: dict) -> dict | None:
    """Git-diff regrounding - warns when investigation files have changed from git HEAD."""
    # Stop_git_diff_reground.py was deleted; module removed.
    # Stub kept to avoid breaking callers; returns None (no-op).
    return None


def _run_acknowledgment_loop(data: dict) -> dict | None:
    """Detect acknowledgment loop: ack + same violation in one turn."""
    try:
        from Stop_acknowledgment_loop import run_acknowledgment_loop
        return run_acknowledgment_loop(data)
    except Exception:
        return None


def _run_repetition_blocker(data: dict) -> dict | None:
    """Block repeated violations after acknowledgment/correction."""
    try:
        from Stop_repetition_blocker import run_repetition_blocker
        return run_repetition_blocker(data)
    except Exception:
        return None


def _run_fake_done_detector(data: dict) -> dict | None:
    """Detect completion claims without evidence."""
    try:
        from Stop_fake_done_detector import run_fake_done_detector
        return run_fake_done_detector(data)
    except Exception:
        return None


def _run_perf_attribution_gate(data: dict) -> dict | None:
    """Performance-attribution gate.

    Migrated 2026-06-14 from cc-aca-epistemic plugin hooks.json (subprocess) to
    local in-process dispatch as part of the split-dispatch consolidation. Imports
    the canonical plugin logic (epistemic stop dir is on sys.path). Blocks
    unverified performance claims when timing code was not read this turn.
    Plugin run() returns {"continue": bool, "stopReason": str}; normalize to the
    in-process {"decision": "block", ...} contract.
    """
    try:
        from StopHook_perf_attribution_gate import run as _perf_run
    except ImportError:
        return None
    result = _perf_run(data)
    if result and result.get("continue") is False:
        return {
            "decision": "block",
            "reason": result.get("stopReason", ""),
            "blocking_hook": "StopHook_perf_attribution_gate",
        }
    return None


def _run_removal_completeness_guard(data: dict) -> dict | None:
    """Removal-completeness guard.

    Migrated 2026-06-14 from cc-aca-epistemic plugin hooks.json (subprocess) to
    local in-process dispatch. check() already returns the in-process
    {"decision": "block", ...} / None contract.
    """
    try:
        from Stop_removal_completeness_guard import check as _removal_check
    except ImportError:
        return None
    return _removal_check(data)


def _run_diagnostic_analysis_quality_gate(data: dict) -> dict | None:
    """Diagnostic-analysis quality gate.

    Migrated 2026-06-14 from cc-aca-epistemic plugin hooks.json (subprocess) to
    local in-process dispatch. run() already returns the in-process
    {"decision": "block"|"warn", ...} / None contract and applies its own
    env-driven enable/mode logic.
    """
    try:
        from Stop_diagnostic_analysis_quality_gate import run as _diag_run
    except ImportError:
        return None
    return _diag_run(data)


def _run_cjk_drift_detector(data: dict) -> dict | None:
    """Block CJK text drift in agent responses.

    Migrated 2026-06-15 from cc-aca-observability plugin hooks.json (subprocess) to
    local in-process dispatch (split-dispatch consolidation). Imports detect_cjk()
    from the canonical plugin file (observability posttool dir is on sys.path).
    """
    try:
        from cjk_drift_detector import detect_cjk
    except ImportError:
        return None
    text = data.get("response", "")
    sample = detect_cjk(text)
    if not sample:
        return None
    msg = (
        f"[CJK drift detected] Output contains non-English characters "
        f'(sample: "{sample}"). The underlying model drifted from English. '
        f"Respond in English only - no Chinese, Japanese, or Korean under any "
        f"circumstances, even when source content contains them."
    )
    return {
        "decision": "block",
        "reason": msg,
        "blocking_hook": "Stop.py:cjk_drift_detector",
    }


def _run_meta_analysis_trap(data: dict) -> dict | None:
    """Block meta-analysis: analyzing WHY instead of fixing."""
    try:
        from Stop_meta_analysis_trap import run_meta_analysis_trap
        return run_meta_analysis_trap(data)
    except Exception:
        return None


def _run_skill_dir_correlation_gate(data: dict) -> dict | None:
    """Advisory: warn when tool events accessed a different skill dir than user intended."""
    try:
        from Stop_skill_dir_correlation_gate import run as _skill_corr_run

        return _skill_corr_run(data)
    except Exception:
        return None


def _run_cks_correction_anchor(data: dict) -> dict | None:
    """Side-effect: persist skill-dir correction event to CKS."""
    try:
        from Stop_cks_correction_anchor import run as _anchor_run

        return _anchor_run(data)
    except Exception:
        return None


# ── Tool-call sanity checker ─────────────────────────────────────────────────

# Per-turn counts — cleared at start of each Stop invocation
_turn_bash_count: int = 0
_turn_edit_paths: dict[str, int] = {}  # path -> count
_turn_high_risk_bash: list[str] = []   # list of detected high-risk commands


def _extract_tool_calls(data: dict) -> list[tuple[str, dict]]:
    """Extract (tool_name, tool_input) pairs from Stop data."""
    calls: list[tuple[str, dict]] = []

    # tool_events is the canonical field for this turn's tool calls
    tool_events: list[dict] = data.get("tool_events", [])
    for event in tool_events:
        name = event.get("name", "")
        tool_input = event.get("input", {}) or event.get("tool_input", {}) or {}
        if name:
            calls.append((name, tool_input))

    # tool_calls string (some hooks pass this as a text summary)
    tc = data.get("tool_calls", "")
    if tc and isinstance(tc, str):
        import re
        # Match tool call patterns: "ToolName(" with optional path arg
        for m in re.finditer(r"(\w+)\s*\(", tc):
            calls.append((m.group(1), {}))

    return calls


def _run_tool_sanity_check(data: dict) -> dict | None:
    """Advisory: flag abnormal tool usage patterns this turn.

    Thresholds (conservative):
      - Bash: warn if >3 calls in a single turn
      - Same file edited/written: warn if >2 times
      - High-risk Bash commands (rm, git reset --hard, etc.): warn on any occurrence
        unless the command is already a Best Practice (e.g., git restore, git checkout HEAD)
    """
    global _turn_bash_count, _turn_edit_paths, _turn_high_risk_bash

    # Reset per turn
    _turn_bash_count = 0
    _turn_edit_paths.clear()
    _turn_high_risk_bash.clear()

    BASH_THRESHOLD = 3
    EDIT_THRESHOLD = 2
    HIGH_RISK_PATTERNS = [
        (r"\brm\s+-(?:rf|r)\b", "rm -rf / rm -r"),
        (r"\bgit\s+reset\s+--hard\b", "git reset --hard"),
        (r"\bgit\s+clean\s+-(?:fd|f)\b", "git clean -fd / -f"),
        (r"\bkill\s+-\s*9\b", "kill -9"),
        (r"\bpowershell\s+.*-Recurse\s+.*rm\b", "PowerShell recursive delete"),
        (r"\bdel\s+/[sq]\b", "del /s /q (Windows recursive delete)"),
        (r"\bFormat-Volume\b.*-Confirm", "Format-Volume"),
    ]
    # Commands that are best-practice recovery, not high-risk
    SAFE_RECOVERY = [
        r"\bgit\s+restore\b",
        r"\bgit\s+checkout\s+HEAD\b",
        r"\bgit\s+checkout\s+--\s+\S",  # git checkout -- file
    ]

    warnings: list[str] = []
    tool_calls = _extract_tool_calls(data)

    for tool_name, tool_input in tool_calls:
        if tool_name == "Bash":
            _turn_bash_count += 1
            command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
            for pat, label in HIGH_RISK_PATTERNS:
                import re
                if re.search(pat, command, re.I):
                    # Skip if it matches a safe-recovery pattern
                    if any(re.search(safe, command, re.I) for safe in SAFE_RECOVERY):
                        continue
                    _turn_high_risk_bash.append(label)
                    break

        if tool_name in ("Edit", "Write", "MultiEdit"):
            path = tool_input.get("file_path", "") if isinstance(tool_input, dict) else ""
            if path:
                _turn_edit_paths[path] = _turn_edit_paths.get(path, 0) + 1

    if _turn_bash_count > BASH_THRESHOLD:
        warnings.append(
            f"High Bash usage this turn: {_turn_bash_count} calls (> {BASH_THRESHOLD} threshold). "
            "Confirm all commands are intentional and necessary."
        )

    repeated_edits = {p: c for p, c in _turn_edit_paths.items() if c > EDIT_THRESHOLD}
    if repeated_edits:
        paths_str = ", ".join(f"'{p}' ({c}x)" for p, c in list(repeated_edits.items())[:3])
        warnings.append(
            f"Repeated edits to same file(s): {paths_str}. "
            "Consolidate edits or verify this is intentional."
        )

    if _turn_high_risk_bash:
        unique_risks = ", ".join(sorted(set(_turn_high_risk_bash)))
        warnings.append(
            f"High-risk Bash commands detected: {unique_risks}. "
            "Verify these commands are correct before proceeding."
        )

    if warnings:
        return {
            "decision": "allow",  # Advisory only — never blocks
            "systemMessage": "TOOL SANITY ADVISORY:\n" + "\n".join(f"  • {w}" for w in warnings),
        }
    return None


def _run_phase0_depends_on_skills(data: dict) -> dict | None:
    """Phase 0 gate: verify step-1 evidence exists for depends_on_skills skills."""
    try:
        from stop.experimental.phase0_depends_on_skills import run as _phase0_run

        return _phase0_run(data)
    except Exception:
        return None


def _clear_referent_anchors(data: dict) -> None:
    """Single-turn lifecycle: clear anchor state at end of every turn.

    Anchors are created by UPS referent_anchor.py, enforced by
    PreToolUse_referent_scope_gate.py, and cleared here unconditionally.
    No cross-turn persistence — prevents stale-anchor lock after topic shifts.

    ponytail: disabled per P3 proposal — referent-scope gate has produced
    126 false blocks on ls/find/Get-ChildItem in one session. The UPS writer
    and PreToolUse gate are both disabled; this clearer is no-op when no
    state file exists, but skipping it entirely is the cleanest reversal.
    """
    if os.environ.get("REFERENT_SCOPE_DISABLED", "1") != "0":
        return
    try:
        tid = (
            data.get("terminal_id")
            or data.get("terminalId")
            or os.environ.get("CLAUDE_TERMINAL_ID")
        )
        if not tid:
            lib_path = str(Path(__file__).resolve().parent / "__lib")
            if lib_path not in sys.path:
                sys.path.insert(0, lib_path)
            from terminal_detection import detect_terminal_id
            tid = detect_terminal_id()
        state_file = Path.home() / ".claude" / ".artifacts" / str(tid) / "referent_anchors.json"
        if state_file.exists():
            state_file.unlink()
    except Exception:
        pass


# ---------------------------------------------------------------------------
#
# ── task_contract_fit gate ────────────────────────────────────────────────────
#
# HOW STOP DECIDES TURN KINDS (for this gate's purposes):
#   _classify_turn_mode(data) → one of: control, exploration, analysis, plan,
#   execution-report, final-answer, meta.
#   - "analysis" / "final-answer": diagnostic/analytical → candidate for checking
#   - "control" / "exploration" / "plan" / "meta": not a completion attempt → skip
#
# WHICH EXISTING GATES TOUCH "did we do what was asked?":
#   intent_artifact_alignment: checks tool_events match prompt file/command targets
#   epistemic_contract: checks response structure (FACT/INFERENCE/etc.)
#   semantic_critic: Haiku-based semantic quality evaluation
#   None of these check "did you produce the specific deliverables the task required?"
#   That is the gap task_contract_fit fills.
#
# INSERTION POINT: After semantic_critic, before deletion_verification_guard.
#   Rationale: task_contract_fit is a quality gate that depends on the response
#   being a plausible completion attempt (not exploration/control). It runs after
#   structural checks have had their say but before policy-level gates.
#
# Gate class: "quality" — suppressed on control/exploration turns.
# V1 authority with V2 shadow mode: V1 enforces, V2 logs for threshold tuning.
# V2 only takes authority when V2_SHADOW_MODE=False and V2_AUTHORITY is set.
# ---------------------------------------------------------------------------


def _run_task_contract_fit_gate(data: dict) -> dict | None:
    """Task contract gate entry point — V1 authority, V2 shadow mode.

    V1 enforces the contract. V2 runs in parallel (returns None) to collect
    telemetry for threshold tuning. Disagreements are logged for post-hoc review.
    """
    # V1: always runs, is the enforcement authority
    v1_result = _run_task_contract_fit_gate_v1(data)

    # V2: shadow mode — runs after V1 to log comparison telemetry
    try:
        from __lib import v2_config as _cfg
        if _cfg.V2_ENABLED and _cfg.V2_SHADOW_MODE:
            _run_task_contract_fit_gate_v2(data)  # Always returns None in shadow mode
    except Exception:
        pass  # Shadow mode failures must not affect V1 enforcement

    return v1_result


def _run_task_contract_fit_gate_v1(data: dict) -> dict | None:
    """Check whether the response satisfies the active task contract.

    Only fires when:
    1. An active task_contract.json exists for this terminal.
    2. The current turn looks like a completion attempt (analysis/final-answer,
       response is substantive enough to plausibly be a final report).
    3. One or more required_outputs are clearly missing from the response.

    Returns None (silent) when no contract exists or the turn is not a
    completion attempt. Returns a block decision when required deliverables
    are missing.
    """
    try:
        from __lib.task_contract import load_contract, clear_contract, mark_provided_outputs

        _, terminal_id = _resolve_scope_ids(data)
        if not terminal_id:
            return None

        contract = load_contract(terminal_id)
        response = data.get("response", "")
        turn_mode = _classify_turn_mode(data)

        # Telemetry: gate entry
        _log_task_contract_telemetry(terminal_id, "check", {
            "contract_present": contract is not None,
            "turn_mode": turn_mode,
            "response_len": len(response),
        })

        if contract is None:
            return None

        # Task class awareness: skip enforcement for non-implementation task classes
        task_class = contract.get("task_class")
        _NON_IMPL_TASK_CLASSES = frozenset({
            "architecture_recommendation",
            "design_recommendation",
            "research_only",
        })
        if task_class in _NON_IMPL_TASK_CLASSES:
            _log_task_contract_telemetry(terminal_id, "silent", {
                "reason": "non_implementation_task_class",
                "task_class": task_class,
            })
            return None

        if not response:
            _log_task_contract_telemetry(terminal_id, "silent", {
                "reason": "empty_response",
            })
            return None

        # Some outputs still missing.

        # Phase-aware applicability: stay silent when implementation contract
        # gets a design/architecture response, or vice versa.
        _IMPL_TASK_CLASSES = frozenset({"bug_fix", "implementation", "refactor"})
        _DESIGN_SIGNALS = (
            "architecture", "design tradeoff", "approach would be",
            "high-level", "structure should",
        )
        _CODE_SIGNALS = ("def ", "class ", "async def", "if __name__", "import ")

        task_class = contract.get("task_class")
        if task_class in _IMPL_TASK_CLASSES:
            hit = next((s for s in _DESIGN_SIGNALS if s in response), None)
            if hit:
                _log_task_contract_telemetry(terminal_id, "silent", {
                    "reason": "phase_mismatch",
                    "contract_class": task_class,
                    "contract_desc": contract.get("description", "")[:50],
                    "triggered_signal": hit,
                })
                return None
        else:  # design/architecture contract
            hit = next((s for s in _CODE_SIGNALS if s in response), None)
            if hit:
                _log_task_contract_telemetry(terminal_id, "silent", {
                    "reason": "phase_mismatch",
                    "contract_class": task_class,
                    "contract_desc": contract.get("description", "")[:50],
                    "triggered_signal": hit,
                })
                return None

        # Load required outputs and historical provided_outputs state BEFORE bypass checks.
        # Detection runs next so short responses with explicit output labels can be recorded.
        required = contract.get("required_outputs", [])
        if not required:
            return None

        provided_historically = set(contract.get("provided_outputs", []))

        # Orthogonality check FIRST: before output detection, so orthogonal
        # responses are cleared regardless of incidental output keywords.
        # "tests" in a git status response != contract fulfillment.
        if _is_response_orthogonal_to_contract(response, contract):
            _log_task_contract_telemetry(terminal_id, "auto_clear", {
                "reason": "orthogonal_response",
                "contract_desc": contract.get("description", "")[:50],
            })
            clear_contract(terminal_id)
            return None

        # Bypass for responses too short to contain substantive output content.
        # But: run detection first so we can record outputs even from micro-turns.
        if len(response) < 80:
            # Still detect outputs in this turn even though the response is too short
            # to constitute a full completion attempt.
            provided_this_turn = _detect_provided_outputs(response, required)
            if provided_this_turn:
                mark_provided_outputs(terminal_id, provided_this_turn)
            _log_task_contract_telemetry(terminal_id, "silent", {
                "reason": "response_too_short",
                "response_len": len(response),
                "provided_this_turn": provided_this_turn,
            })
            return None

        # Stateful output tracking: detect outputs in this turn and record them.
        provided_this_turn = _detect_provided_outputs(response, required)
        if provided_this_turn:
            mark_provided_outputs(terminal_id, provided_this_turn)
            contract = load_contract(terminal_id)

        # Recompute after this turn's detection (short or long).
        provided_now = set(contract.get("provided_outputs", []))
        required_set = set(required)
        still_missing = [o for o in required if o not in provided_now]

        # Track whether ALL required outputs are now satisfied after this turn.
        was_satisfied = len(still_missing) == 0

        if not still_missing:
            # All required outputs have been provided across turns — allow this turn.
            # If this was satisfied for the FIRST time in this turn, clear the contract.
            if was_satisfied:
                clear_contract(terminal_id)
                _log_task_contract_telemetry(terminal_id, "auto_clear", {
                    "reason": "all_outputs_provided_this_turn",
                    "provided_outputs": sorted(provided_now),
                    "required": required,
                })
            else:
                _log_task_contract_telemetry(terminal_id, "silent", {
                    "reason": "all_outputs_previously_provided",
                    "provided_outputs": sorted(provided_now),
                    "required": required,
                })
            return None

        # Some outputs still missing.
        # Short responses (< 300 chars) that matched no output patterns are too risky
        # to block on — they may be genuine micro-follow-ups that the orthogonal
        # check already allowed. They also cannot complete a partial contract alone.
        # Block only if length >= 300 and nothing was detected in this turn.
        if len(response) >= 300 and not provided_this_turn:
            missing = _check_missing_outputs(response, required)
            if not missing:
                clear_contract(terminal_id)
                _log_task_contract_telemetry(terminal_id, "auto_clear", {
                    "required": required,
                })
                return None
        elif len(response) < 300 and provided_this_turn:
            # Short response that matched outputs but left other outputs still missing.
            # If ANY outputs were already recorded in earlier turns (provided_historically),
            # this is a legitimate micro-follow-up — silent pass. The contract was
            # not yet complete so the prior turn should have blocked if truly incomplete;
            # a short addendum after partial progress is not friction.
            if provided_historically:
                _log_task_contract_telemetry(terminal_id, "silent", {
                    "reason": "short_output_after_partial_satisfaction",
                    "response_len": len(response),
                    "provided_this_turn": provided_this_turn,
                    "provided_now": sorted(provided_now),
                })
                return None
            # No prior history but short response with detected outputs: the explicit
            # labels ("Root cause:", "Fixed.", "Tests pass.") demonstrate task-relevant
            # progress. Allow without blocking — the next turn can complete remaining.
            _log_task_contract_telemetry(terminal_id, "silent", {
                "reason": "short_output_first_turn",
                "response_len": len(response),
                "provided_this_turn": provided_this_turn,
                "provided_now": sorted(provided_now),
            })
            return None
        elif len(response) < 300 and not provided_this_turn:
            # Short response with no detected outputs — likely a trivial confirmation.
            # Silent pass regardless of prior partial satisfaction: if the contract was
            # truly incomplete the assistant would have been blocked on an earlier turn;
            # a short follow-up after partial progress is not contract friction.
            _log_task_contract_telemetry(terminal_id, "silent", {
                "reason": "short_no_outputs_no_contract_progress",
                "response_len": len(response),
                "provided_now": sorted(provided_now),
            })
            return None

        # Block path: compute missing from current provided_outputs state.
        missing = [o for o in required if o not in provided_now]
        _log_task_contract_telemetry(terminal_id, "block", {
            "required": required,
            "missing": missing,
            "provided_outputs": sorted(provided_now),
        })

        # Build a specific, actionable block message.
        required_str = ", ".join(required)
        missing_str = ", ".join(missing)
        already_provided = sorted(provided_now)
        provided_str = ", ".join(already_provided) if already_provided else "none"

        return {
            "decision": "block",
            "reason": (
                f"TASK CONTRACT INCOMPLETE: required outputs [{required_str}], "
                f"missing: [{missing_str}]."
            ),
            "systemMessage": (
                f"The user's task contract requires: {required_str}. "
                f"Your answer is missing: {missing_str}. "
                f"(Already provided in this task: {provided_str}.) "
                f"Extend your answer to include those explicitly before responding."
            ),
            "blocking_hook": "Stop.py:task_contract_fit",
        }
    except Exception as e:
        _logger.warning(f"task_contract_fit error: {e}")
        return None


def _log_task_contract_telemetry(
    terminal_id: str, event: str, fields: dict,
) -> None:
    """Append structured telemetry for task_contract_fit gate."""
    try:
        log_path = HOOKS_DIR / "logs" / "diagnostics" / "task_contract_telemetry.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": time.time(),
            "gate": "task_contract_fit",
            "event": event,
            "terminal_id": terminal_id,
            **fields,
        }
        from file_lock import append_jsonl_safe
        append_jsonl_safe(log_path, entry, ensure_ascii=True)
    except OSError:
        pass  # Observability must never change hook behavior


# ---------------------------------------------------------------------------------------
# Phase 3: Runtime Claim Enforcement Gate
# ---------------------------------------------------------------------------------------

def _run_runtime_claim_gate(data: dict) -> dict | None:
    """Verify runtime claims against artifact sources.

    Detects runtime claim subclasses (STOP_GATE_FIRING, UPS_HOOK_CO_FIRE,
    AGE_GUARD_RUNTIME, BENCHMARK_RUN_EVENT) in response text and verifies them
    against corresponding log artifacts. Policy gate — always applicable.
    """
    try:
        from __lib.runtime_claims import (
            classify_runtime_claim,
            verify_runtime_claim,
            RuntimeClaimType,
        )
    except Exception:
        return None  # Module not available

    response = data.get("response", "")
    if not response:
        return None

    # Detect runtime claim types in response
    claim_types = classify_runtime_claim(response)
    if not claim_types:
        return None  # No runtime claims detected

    # Get session context for artifact lookup
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")
    terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "")
    _, t_id = _resolve_scope_ids(data)
    terminal_id = t_id or terminal_id

    # Verify each detected claim type
    all_verified = True
    messages: list[str] = []

    for claim_type in claim_types:
        verified, msg = verify_runtime_claim(
            claim_type,
            response,
            session_id=session_id,
            terminal_id=terminal_id,
        )
        if not verified:
            all_verified = False
            messages.append(msg)

    if all_verified:
        return None  # Claims verified — allow

    # Build block message for unverified claims
    verdict = "BLOCK" if not all_verified else "allow"
    combined_msg = "\n".join(messages)

    return {
        "verdict": verdict,
        "gate": "runtime_claim_enforcement",
        "reason": f"Runtime claim verification failed:\n{combined_msg}",
        "messages": messages,
        "claim_types": [ct.value for ct in claim_types],
        "action": "block",
    }


# ---------------------------------------------------------------------------------------
# Phase 4: External Judge Evaluation Gate - DISABLED
# Removed: Judge produced no actionable value. Override already demoted blocks
# to advisory; 24h summary disabled in judge_feedback.py; first-query advisory
# disabled in judge_first_query_advisory.py.
# ---------------------------------------------------------------------------------------



# ---------------------------------------------------------------------------------------
# V2 Semantic State Gate
# ---------------------------------------------------------------------------------------

def _run_task_contract_fit_gate_v2(data: dict) -> dict | None:
    """V2 semantic state-based enforcement — shadow mode by default.

    When V2_SHADOW_MODE=True (default), logs all decisions but returns None so V1
    remains the enforcement authority. This collects V1/V2 disagreement data
    before promoting V2 to authority.
    """
    try:
        from __lib import v2_config as _cfg
        from __lib.task_contract import (
            load_contract,
            supersede_contract,
            update_phase,
            update_evidence,
            clear_contract,
            mark_provided_outputs,
        )
        from __lib.semantic_matcher_llm import (
            classify_task_relation,
            classify_trivial_same_task,
        )
        from __lib.phase_machine import (
            should_enforce_outputs,
            infer_phase_from_context,
            can_transition,
        )
        from __lib.evidence_collector import (
            collect_from_turn,
            accumulate,
        )

        if not _cfg.V2_ENABLED:
            return None

        _, terminal_id = _resolve_scope_ids(data)
        if not terminal_id:
            return None

        contract = load_contract(terminal_id)
        if not contract or contract.get("status") != "active":
            return None

        response = data.get("response", "")
        turn_mode = _classify_turn_mode(data)
        user_prompt = data.get("user_prompt", "")

        # Layer 1: Semantic Continuity (LLM-based)
        # The orchestrator classifies the relation between the current prompt
        # and the active contract's task. Short operational follow-ups use a
        # fast-path; everything else calls classify_task_relation which reads
        # _semantic_relation from the orchestrator's pre-populated context.
        relation_reason: str | None = None
        if _cfg.V2_SEMANTIC_MATCHER_ENABLED:
            # Fast-path: obvious same-task operational follow-ups
            if classify_trivial_same_task(user_prompt):
                relation_reason = "trivial_same_task"
            else:
                relation = classify_task_relation(
                    contract.get("description", ""),
                    contract.get("task_class", "implementation"),
                    user_prompt,
                    data.get("recent_summary"),
                )
                relation_reason = relation
                _log_task_contract_v2_telemetry(terminal_id, "v2_semantic_relation", {
                    "relation": relation,
                    "contract_desc": contract.get("description", "")[:50],
                    "user_prompt_preview": user_prompt[:50],
                    "source": "orchestrator",
                })
                if relation == "orthogonal":
                    # Only supersede in authority mode — shadow mode must not alter contract state
                    # (V1 is the enforcement authority in shadow mode)
                    if not _cfg.V2_SHADOW_MODE:
                        supersede_contract(terminal_id, reason="semantic_orthogonality")
                    _log_task_contract_v2_telemetry(terminal_id, "v2_auto_supersede", {
                        "reason": "semantic_orthogonality",
                        "relation": relation,
                        "task_id": contract.get("task_id", "?"),
                        "shadow_mode_superseded": not _cfg.V2_SHADOW_MODE,
                    })
                    return None

        # Layer 2: Phase Inference & Evidence Accumulation
        inferred_phase = None
        if _cfg.V2_PHASE_MACHINE_ENABLED and _cfg.V2_EVIDENCE_COLLECTOR_ENABLED:
            tool_uses = data.get("tool_uses", [])
            new_evidence = collect_from_turn(tool_uses) if tool_uses else {
                "files_modified": [],
                "tests_run": [],
                "verification_commands_executed": [],
                "code_generated": False,
                "design_artifacts": [],
                "git_commits": 0,
            }
            existing_evidence = contract.get("evidence", {})
            merged_evidence = accumulate(existing_evidence, new_evidence)
            # Only persist evidence in authority mode — shadow mode reads but does not write
            if not _cfg.V2_SHADOW_MODE:
                update_evidence(terminal_id, merged_evidence)
            _log_task_contract_v2_telemetry(terminal_id, "v2_evidence_accumulated", {
                "files": len(merged_evidence.get("files_modified", [])),
                "tests": len(merged_evidence.get("tests_run", [])),
                "shadow_mode_persisted": not _cfg.V2_SHADOW_MODE,
            })

            context_for_phase = {
                "response": response,
                "turn_mode": turn_mode,
                "user_prompt": user_prompt,
            }
            inferred_phase = infer_phase_from_context(context_for_phase, merged_evidence)

            current_phase = contract.get("phase", "exploration")
            if inferred_phase and inferred_phase != current_phase and can_transition(current_phase, inferred_phase):
                history = list(contract.get("phase_history", []))
                now_iso = _now_iso()
                for entry in reversed(history):
                    if entry.get("phase") == current_phase and "exited_at" not in entry:
                        entry["exited_at"] = now_iso
                        break
                history.append({"phase": inferred_phase, "entered_at": now_iso, "exited_at": None, "turns": 0})
                # Only persist phase in authority mode
                if not _cfg.V2_SHADOW_MODE:
                    update_phase(terminal_id, inferred_phase, phase_history=history)
                _log_task_contract_v2_telemetry(terminal_id, "v2_phase_transition", {
                    "from": current_phase,
                    "to": inferred_phase,
                    "task_id": contract.get("task_id", "?"),
                    "shadow_mode_persisted": not _cfg.V2_SHADOW_MODE,
                })

            _log_task_contract_v2_telemetry(terminal_id, "v2_phase_inference", {
                "inferred_phase": inferred_phase,
                "current_phase": current_phase,
                "evidence_summary": str(merged_evidence)[:100],
            })

        # Layer 3: Enforcement Decision
        if _cfg.V2_PHASE_MACHINE_ENABLED:
            phase_to_check = inferred_phase or contract.get("phase", "exploration")
            task_class = contract.get("task_class", "implementation")
            if not should_enforce_outputs(phase_to_check, task_class):
                _log_task_contract_v2_telemetry(terminal_id, "v2_phase_silent", {
                    "phase": phase_to_check,
                    "task_class": task_class,
                    "reason": "phase_not_enforcement_ready",
                })
                return None

        required = contract.get("required_outputs", [])
        if not required:
            return None

        # Stateful output tracking: update provided_outputs for outputs seen in this turn.
        if len(response) >= 300:
            provided_this_turn = _detect_provided_outputs(response, required)
            if provided_this_turn:
                mark_provided_outputs(terminal_id, provided_this_turn)
                # Re-load contract to get updated provided_outputs
                contract = load_contract(terminal_id)

        # Check which outputs are still truly missing from this task's history.
        provided_historically = set(contract.get("provided_outputs", []))
        required_set = set(required)
        still_missing = [o for o in required if o not in provided_historically]

        if not still_missing:
            _log_task_contract_v2_telemetry(terminal_id, "v2_silent_provided", {
                "provided_outputs": sorted(provided_historically),
                "required": required,
            })
            return None

        missing = _check_missing_outputs(response, required)

        if not missing:
            # Only clear in authority mode — shadow mode must not alter contract state
            # (V1 is the enforcement authority in shadow mode)
            if not _cfg.V2_SHADOW_MODE:
                clear_contract(terminal_id)
            _log_task_contract_v2_telemetry(terminal_id, "v2_auto_clear", {
                "required": required,
                "phase": contract.get("phase", "?"),
                "task_id": contract.get("task_id", "?"),
                "shadow_mode_cleared": not _cfg.V2_SHADOW_MODE,
            })
            return None

        if len(response) >= 300 and turn_mode in ("analysis", "final-answer"):
            if not _cfg.V2_SHADOW_MODE and _cfg.V2_AUTHORITY in ("full", "applicability"):
                _log_task_contract_v2_telemetry(terminal_id, "v2_block", {
                    "missing": missing,
                    "required": required,
                    "phase": contract.get("phase", "?"),
                    "provided_outputs": sorted(provided_historically),
                })
                already_provided = sorted(provided_historically)
                provided_str = ", ".join(already_provided) if already_provided else "none"
                return {
                    "decision": "block",
                    "reason": "v2_missing_required_outputs",
                    "systemMessage": (
                        f"The task contract (phase: {contract.get('phase', '?')}) "
                        f"requires: {', '.join(required)}. "
                        f"Your answer is missing: {', '.join(missing)}. "
                        f"(Already provided in this task: {provided_str}.) "
                        f"Extend your answer to include those explicitly."
                    ),
                    "blocking_hook": "Stop.py:task_contract_fit_v2",
                }
            else:
                _log_task_contract_v2_telemetry(terminal_id, "v2_would_block", {
                    "missing": missing,
                    "v1_decision": "v2_in_shadow",
                    "provided_outputs": sorted(provided_historically),
                })

        return None

    except Exception as e:
        _logger.warning(f"task_contract_fit_v2 error: {e}")
        return None


def _log_task_contract_v2_telemetry(
    terminal_id: str, event: str, fields: dict,
) -> None:
    """Append V2 telemetry to task_contract_v2_telemetry.jsonl."""
    try:
        log_path = HOOKS_DIR / "logs" / "diagnostics" / "task_contract_v2_telemetry.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "timestamp": time.time(),
            "gate": "task_contract_fit_v2",
            "event": event,
            "terminal_id": terminal_id,
            **fields,
        }
        from file_lock import append_jsonl_safe
        append_jsonl_safe(log_path, entry, ensure_ascii=True)
    except OSError:
        pass


def _now_iso() -> str:
    """Return current UTC time as ISO string."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# _classify_turn_mode is imported from __lib.turn_mode at module top (line ~90).


# Deterministic pattern checks for required output types.
# v1 uses simple keyword/heading detection — no external calls.

_OUTPUT_PATTERNS: dict[str, list[str]] = {
    "root_cause": [
        r"(?i)\broot\s*cause\b",
        r"(?i)\bcaused\s+by\b",
        r"(?i)\bthe\s+(?:underlying|actual|real)\s+(?:issue|problem|cause|bug)\b",
        r"(?i)\bwhat\s+(?:went\s+wrong|caused|broke)\b",
        r"(?i)\bthe\s+(?:issue|problem)\s+originates\b",
        r"(?i)\btraced?\s+(?:to|back|from)\b",
        r"(?i)\bthe\s+(?:call|import)\s+chain\b",
    ],
    "fix": [
        r"(?i)\bfix(?:ed|es)?\b",
        r"(?i)\bworkaround\b",
        r"(?i)\bpatch\b",
        r"(?i)\bchanged?\s+.*\bto\b",
        r"(?i)\bapplied\s+(?:the\s+)?(?:fix|change|patch)\b",
        r"(?i)\bthe\s+fix\b",
        r"(?i)\bsolution\b",
    ],
    "tests": [
        r"(?i)\btest[s]?\b",
        r"(?i)\bpytest\b",
        r"(?i)\bassert\b",
        r"(?i)\btest_",
        r"(?i)\bdef\s+test_",
        r"(?i)\bcoverage\b",
    ],
    "verification_commands": [
        r"(?i)\bverify(?:ing)?\b",
        r"(?i)\bverification\b",
        r"(?i)(?:python|pytest|npm|cargo|go\s+test)\s+",
        r"(?i)\brun\s+(?:the\s+)?(?:test|check|verify|command)",
        r"(?i)\bcommand[s]?\s+to\s+(?:verify|run|check|test)\b",
        r"(?i)```\s*(?:python|bash|sh)\s+.*(?:test|check|verify|run)",
    ],
}


def _check_missing_outputs(response: str, required: list[str]) -> list[str]:
    """Return the subset of required outputs that are NOT clearly present."""
    import re as _re

    missing: list[str] = []
    for output_type in required:
        patterns = _OUTPUT_PATTERNS.get(output_type, [])
        found = any(_re.search(p, response) for p in patterns)
        if not found:
            missing.append(output_type)
    return missing


def _detect_provided_outputs(response: str, required: list[str]) -> list[str]:
    """Return which required outputs ARE clearly present in this response."""
    import re as _re

    provided: list[str] = []
    for output_type in required:
        patterns = _OUTPUT_PATTERNS.get(output_type, [])
        found = any(_re.search(p, response) for p in patterns)
        if found:
            provided.append(output_type)
    return provided


# Stop words for semantic overlap check — common English + hook domain noise
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "as", "is", "was", "are", "were", "been", "be", "have", "has", "had",
    "do", "does", "did", "will", "would", "could", "should", "may", "might", "must",
    "shall", "can", "need", "dare", "ought", "used", "it", "its", "i", "we", "you",
    "he", "she", "they", "what", "which", "who", "whom", "this", "that", "these",
    "those", "am", "if", "else", "when", "where", "why", "how", "all", "each",
    "every", "both", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "just", "also",
    "now", "here", "there", "then", "once", "any", "about", "after", "before",
    "between", "into", "through", "during", "above", "below", "up", "down", "out",
    "off", "over", "under", "again", "further", "back", "look", "see", "make",
    "way", "want", "give", "take", "put", "use", "find", "tell", "ask", "work",
    "seem", "feel", "try", "leave", "call", "well", "even", "new", "want", "sure",
    "thing", "things", "something", "anything", "everything", "nothing",
    "yes", "no", "ok", "okay", "please", "thanks", "thank", "sorry", "sure",
})


def _tokenize(text: str) -> set[str]:
    """Extract significant words from text: lowercase, strip punctuation, drop stop words."""
    import re as _re
    # Split on non-word chars, lowercase, filter empties and stop words
    words = _re.findall(r"\b\w+\b", text.lower())
    return {w for w in words if len(w) > 2 and w not in _STOP_WORDS}


def _is_task_relevant_verification_update(response: str, contract: dict) -> bool:
    """
    INTERNAL: orthogonality disambiguator only.

    This helper is allowed to be used ONLY from _is_response_orthogonal_to_contract
    in this module. It is not a general semantic classifier and must not be
    imported or reused from other modules.

    See test_internal_helpers.py for the scope-guard test that enforces this.
    """
    import re as _re

    required = contract.get("required_outputs", [])
    if not required:
        return False

    needs_verification = any(o in required for o in ("tests", "verification_commands"))
    if not needs_verification:
        return False

    # Result/status patterns: explicit test/build/verify outcomes
    positive = _re.search(r"\b\d+\s*(?:passed?|pass|tests?)\b", response, _re.I)
    if not positive:
        positive = _re.search(r"\ball\s+\d+\s*(?:pass|tests?)\b", response, _re.I)
    if not positive:
        # "ok / passing / passed / pass" requires verification context
        # to distinguish from casual "that's ok" in unrelated prose
        context = _re.search(
            r"\b(?:pytest|tests?|build|verify|run|tested|verification)\b", response, _re.I
        )
        positive = bool(context and _re.search(r"\b(?:ok|passing|passed|pass)\b", response, _re.I))

    return bool(positive)


def _is_response_orthogonal_to_contract(response: str, contract: dict) -> bool:
    """Return True if response is semantically unrelated to the contract description.

    Uses a priority chain — earlier signals fire first; once one fires, later signals
    are not evaluated:
      1. In-progress: prior outputs mean the conversation is task-active.
      2. Semantic ratio: all responses checked regardless of length.
         High overlap → not orthogonal (early exit).
      3. Task-relevant verification update: brief progress report detected.
         Fires only when contract requires verification AND response is a result shape.
         (Early disambiguator before token-ratio fallback.)
      4. Short fallback: responses < 50 chars may be brief progress updates
         with zero vocabulary overlap. The short-response bypass handles these safely.
      5. Token-ratio fallback: remaining responses judged by word-overlap ratio.

    Rationale for priority order:
      - In-progress takes precedence: a conversation with prior outputs is task-active.
      - Semantic ratio is checked for ALL responses first, so genuinely orthogonal
        short responses (e.g. "git status shows clean.") still auto-clear.
      - The verification-update disambiguator catches medium-length first-turn
        verification results (50-300 chars, zero overlap) that the ratio might
        otherwise false-clear. Named to reflect its narrow scope — not a general
        semantic classifier.
      - The 50-char short fallback protects brief progress updates that the
        semantic ratio might not catch (zero-overlap confirmation messages).
      - Token ratio is the final fallback for long responses with no prior history.
    """
    desc_words = _tokenize(contract.get("description", ""))
    resp_words = _tokenize(response)
    provided_historically = set(contract.get("provided_outputs", []))

    # Signal 1: In-progress — prior outputs mean task-active conversation.
    if provided_historically:
        return False

    # Signal 2: Semantic ratio — checked for ALL responses regardless of length.
    # High overlap means task-relevant (not orthogonal).
    if desc_words and resp_words:
        overlap = desc_words & resp_words
        ratio = len(overlap) / len(desc_words)
        if ratio > 0.20:
            return False

    # Signal 3b: Task-relevant verification update — disambiguator before ratio fallback.
    # Only fires when contract requires verification AND response is a result shape.
    if _is_task_relevant_verification_update(response, contract):
        _log_task_contract_telemetry(
            contract.get("task_id", "?"),
            "verification_update_block",
            {"response_len": len(response)},
        )
        return False

    # Signal 3: Very short — may be brief progress updates with zero overlap.
    if len(response) < 50:
        return False

    if not desc_words:
        return False

    _log_task_contract_telemetry(
        contract.get("task_id", "?"),
        "semantic_check",
        {"overlap_words": list(desc_words & resp_words)[:10], "ratio": round(len(desc_words & resp_words) / len(desc_words), 3)},
    )

    return (len(desc_words & resp_words) / len(desc_words)) <= 0.20


# Gate classification: POLICY gates fire on all turns.
# QUALITY gates are suppressed on control turns in normal mode,
# allowing corrections and direct instructions to pass without
# epistemic/lazy advisory derailment.
GATE_CLASSES: dict[str, str] = {
    # Policy gates — always fire
    "safety_gate": "policy",
    "frameguard_stop": "policy",
    "skill_first_stop_gate": "policy",
    "post_skill_prose_gate": "policy",
    "verification_enforcement": "policy",
    "cited_content_guard": "policy",
    "cross_validator": "policy",
    "unverified_stance": "policy",
    "correction_acknowledgment": "policy",
    "dependency_chain_guard": "quality",
    "comparative_claim_guard": "quality",
    "behavior_gates_agreement": "policy",
    "behavior_gates_guidance": "quality",
    "behavior_gates_blacklist": "policy",
    "command_execution_validator": "policy",
    "recommendation_gate": "quality",
    "intent_artifact_alignment": "quality",
    "deletion_verification_guard": "policy",
    "git_diff_reground": "policy",
    "skill_dir_correlation": "policy",
    "cks_correction_anchor": "policy",
    "tool_sanity": "quality",
    "artifact_enforcement": "policy",  # Block unverified mechanism claims
    "runtime_claim_enforcement": "policy",  # Phase 3: Runtime claim artifact verification
    # Migrated 2026-06-14 from cc-aca-epistemic plugin hooks.json (subprocess) to
    # local in-process dispatch. "policy" = always-fire, preserving the prior
    # unconditional subprocess behavior (each gate keeps its own internal gating).
    "perf_attribution": "policy",
    "removal_completeness": "policy",
    "diagnostic_analysis_quality": "quality",
    # Migrated 2026-06-15 from cc-aca-observability plugin hooks.json (subprocess).
    "cjk_drift_detector": "policy",
    # Quality gates — suppressed on control turns in normal mode
    "epistemic_contract": "quality",
    "behavior_audit": "quality",
    "narrative_intent": "quality",
    "anti_sycophancy_quality": "quality",
    "advisory": "quality",
    "reflect_integration": "quality",
    "reasoning_quality_gate": "quality",
    "reasoning_enhanced": "quality",
    "existence_gate": "quality",
    "lazy_workaround_gate": "quality",
    "semantic_critic": "quality",
    "proposal_critique_gate": "quality",
    "task_contract_fit": "quality",
    "phase0_depends_on_skills": "quality",
    "acknowledgment_loop": "policy",
    "repetition_blocker": "policy",
    "fake_done": "policy",
    "meta_analysis_trap": "quality",
    # Phase 4: External judge evaluation — DISABLED (no actionable value)
    # "external_judge": "quality",
    # Telemetry-only probe (never blocks, never warns). Classified as "observability"
    # so it is not subject to policy/quality arbitration logic; run() returns {}
    # unconditionally, so the result path is a no-op regardless of class.
    "claim_gap_telemetry_probe": "observability",
}

# === Phase 1+2: Gate Metadata Registry ===
# Co-located with GATE_CLASSES so classification and metadata stay in sync.
# Used for: trivial detection, priority arbitration, applicability routing, diagnostics.
#
# Phase 1 fields:
#   class: "policy" | "quality" — mirrors GATE_CLASSES for cross-check
#   trivial_suppressible: whether is_trivial_exchange() short-circuits this gate
#                         Quality gates are suppressible; policy gates never are.
#   priority: arbitration priority when multiple blocks fire (lower = higher precedence)
#             0-9 = critical (safety, identity), 10-49 = policy (enforcement), 50-99 = quality (advisory)
#   description: one-line description for diagnostics
#
# Phase 2 fields:
#   relevant_turn_kinds: set of TurnKind values this gate fires on
#     Policy gates: all modes. Quality gates: primarily analysis/final-answer.
#   relevant_claim_kinds: set of ClaimKind values this gate addresses
#     Controls whether the gate runs given the detected claim type.
#     Empty set = no claim-kind filter (gate always applies regardless of claim type).
#   required_artifact_classes: set of artifact class strings required for the gate to fire
#     Empty set = no artifact requirement. Non-empty = gate runs only if those
#     artifact classes are detected in the response.
#   rollout_mode: "block" | "advisory" | "shadow" | "disabled"
#     Controls gate enforcement level. Env var STOP_GATE_ROLLOUT_<NAME> overrides.
#
# ClaimKind enum values: FORMAT_ONLY, FACTUAL, CAUSAL, STANCE, UNKNOWN
# TurnKind enum values: ANALYSIS, CONTROL, EXPLORATION, DEBUG_META, PLAN, EXECUTION_REPORT, FINAL_ANSWER
# RolloutMode: BLOCK=block, ADVISORY=block→warn, SHADOW=log-only, DISABLED=skip

from enum import Enum as _Enum


class ClaimKind(_Enum):
    FORMAT_ONLY = "format_only"
    FACTUAL = "factual"
    CAUSAL = "causal"
    STANCE = "stance"
    UNKNOWN = "unknown"


class TurnKind(_Enum):
    ANALYSIS = "analysis"
    CONTROL = "control"
    EXPLORATION = "exploration"
    DEBUG_META = "debug_meta"
    PLAN = "plan"
    EXECUTION_REPORT = "execution_report"
    FINAL_ANSWER = "final_answer"
    UNKNOWN = "unknown"


class RolloutMode(_Enum):
    BLOCK = "block"        # Normal enforcement (block on violation)
    ADVISORY = "advisory"  # Block → warn
    SHADOW = "shadow"     # Log only, never block
    DISABLED = "disabled"  # Gate skipped entirely


def _get_rollout_mode(name: str, default: RolloutMode) -> RolloutMode:
    """Check env var override for gate rollout mode. Returns default if not set."""
    env_var = f"STOP_GATE_ROLLOUT_{name.upper().replace('-', '_')}"
    val = os.environ.get(env_var, "").lower()
    if val == "shadow":
        return RolloutMode.SHADOW
    if val == "advisory":
        return RolloutMode.ADVISORY
    if val == "disabled":
        return RolloutMode.DISABLED
    if val in ("block", "on"):
        return RolloutMode.BLOCK
    return default


def is_gate_applicable(
    gate_name: str,
    turn_kind: TurnKind,
    claim_kind: ClaimKind,
    artifact_classes: set[str],
) -> tuple[bool, str]:
    """Check if a gate is applicable given current turn/claim/artifact context.

    Returns (applicable: bool, skip_reason: str) — skip_reason is empty when applicable.

    Check order:
      1. Rollout mode (DISABLED → skip)
      2. Turn kind filter
      3. Claim kind filter (empty set = always applicable)
      4. Artifact class requirement (empty set = no requirement)
    """
    meta = GATE_METADATA.get(gate_name)
    if not meta:
        return True, ""  # Unknown gate — allow

    rollout = _get_rollout_mode(gate_name, RolloutMode.BLOCK)
    if rollout == RolloutMode.DISABLED:
        return False, "rollout_disabled"

    # Turn kind check
    rtk = meta.get("relevant_turn_kinds", set())
    if rtk and turn_kind not in rtk:
        return False, f"turn_kind_excluded:{turn_kind.value}"

    # Claim kind check (empty = no filter)
    rck = meta.get("relevant_claim_kinds", set())
    if rck and claim_kind not in rck:
        return False, f"claim_kind_excluded:{claim_kind.value}"

    # Artifact class requirement
    rac = meta.get("required_artifact_classes", set())
    if rac:
        missing = rac - artifact_classes
        if missing:
            return False, f"missing_artifacts:{','.join(sorted(missing))}"

    return True, ""


# Minimal sets for gating — conservative defaults.
# Policy gates fire on all turn kinds.
_ALL_TURN_KINDS = frozenset(TurnKind)
# Quality gates: primarily analysis and final-answer (high-stakes reasoning).
_ANALYSIS_TURN_KINDS = frozenset({TurnKind.ANALYSIS, TurnKind.FINAL_ANSWER})
# semantic_critic also evaluates turns that classify as UNKNOWN. turn_mode's
# "meta"/"query"/"unknown" modes all collapse to TurnKind.UNKNOWN (see
# _turn_mode_to_turn_kind), which the bare _ANALYSIS_TURN_KINDS set excluded —
# silently skipping the critic on exactly the proposal/recommendation turns it
# exists to catch. The critic self-scopes internally via _is_diagnostic_scope
# (>50 words + diagnostic/evaluative keywords), so including UNKNOWN closes the
# hole without making it fire on greetings/control turns and without widening
# any other analysis-class gate.
_ANALYSIS_OR_UNKNOWN_TURN_KINDS = _ANALYSIS_TURN_KINDS | frozenset({TurnKind.UNKNOWN})
_ALL_CLAIM_KINDS = frozenset(ClaimKind)

GATE_METADATA: dict[str, dict] = {
    # Critical / identity — always fire, all modes, all claim types
    "safety_gate": {
        "class": "policy", "trivial_suppressible": False, "priority": 0,
        "description": "Dangerous command protection",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "frameguard_stop": {
        "class": "policy", "trivial_suppressible": False, "priority": 1,
        "description": "Frame injection guard",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    # Policy enforcement
    "skill_first_stop_gate": {
        "class": "policy", "trivial_suppressible": False, "priority": 10,
        "description": "Skill-first enforcement at stop",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "post_skill_prose_gate": {
        "class": "policy", "trivial_suppressible": False, "priority": 11,
        "description": "Post-skill prose detection",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "verification_enforcement": {
        "class": "policy", "trivial_suppressible": False, "priority": 12,
        "description": "Verify step enforcement",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "cited_content_guard": {
        "class": "policy", "trivial_suppressible": False, "priority": 13,
        "description": "Cross-validate cited sources",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.FACTUAL, ClaimKind.CAUSAL}),
        "required_artifact_classes": frozenset({"cited_source"}),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "cross_validator": {
        "class": "policy", "trivial_suppressible": False, "priority": 14,
        "description": "Fabrication and cross-validation",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.FACTUAL, ClaimKind.CAUSAL, ClaimKind.STANCE}),
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "unverified_stance": {
        "class": "policy", "trivial_suppressible": False, "priority": 15,
        "description": "Anti-sycophancy stance detection",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.STANCE, ClaimKind.FACTUAL}),
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "correction_acknowledgment": {
        "class": "policy", "trivial_suppressible": False, "priority": 16,
        "description": "CKS correction acknowledgment",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "behavior_gates_agreement": {
        "class": "policy", "trivial_suppressible": False, "priority": 17,
        "description": "Agreement consistency enforcement",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.FACTUAL}),
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "behavior_gates_blacklist": {
        "class": "policy", "trivial_suppressible": False, "priority": 18,
        "description": "Blacklist pattern detection",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "command_execution_validator": {
        "class": "policy", "trivial_suppressible": False, "priority": 19,
        "description": "Command execution alignment",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "deletion_verification_guard": {
        "class": "policy", "trivial_suppressible": False, "priority": 20,
        "description": "Deletion verification",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "git_diff_reground": {
        "class": "policy", "trivial_suppressible": False, "priority": 21,
        "description": "Git diff regrounding",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "skill_dir_correlation": {
        "class": "policy", "trivial_suppressible": False, "priority": 22,
        "description": "Skill directory correlation",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "cks_correction_anchor": {
        "class": "policy", "trivial_suppressible": False, "priority": 23,
        "description": "CKS correction anchoring",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "acknowledgment_loop": {
        "class": "policy", "trivial_suppressible": False, "priority": 24,
        "description": "Acknowledgment loop detection",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "repetition_blocker": {
        "class": "policy", "trivial_suppressible": False, "priority": 25,
        "description": "Repetitive response blocker",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "fake_done": {
        "class": "policy", "trivial_suppressible": False, "priority": 26,
        "description": "Fake done detection",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "artifact_enforcement": {
        "class": "policy", "trivial_suppressible": False, "priority": 28,
        "description": "Block unverified mechanism claims",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.FACTUAL, ClaimKind.CAUSAL}),
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,  # Phase 3: Default to ADVISORY for safe rollout
    },
    # Phase 3: Runtime Claim Enforcement
    "runtime_claim_enforcement": {
        "class": "policy", "trivial_suppressible": False, "priority": 29,
        "description": "Verify runtime claims against artifact logs",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset({"runtime_claim"}),  # Requires runtime claim detection
        "rollout_mode": RolloutMode.ADVISORY,
    },
    # Quality advisory — primarily analysis/final-answer turns
    "epistemic_contract": {
        "class": "quality", "trivial_suppressible": True, "priority": 50,
        "description": "Epistemic contract (format, causal, factual)",
        "relevant_turn_kinds": frozenset({TurnKind.ANALYSIS, TurnKind.FINAL_ANSWER, TurnKind.EXECUTION_REPORT}),
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "behavior_audit": {
        "class": "quality", "trivial_suppressible": True, "priority": 51,
        "description": "Behavior audit detector",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        # 2026-07-06: BLOCK→ADVISORY per retirement review (zero blocks in 22d, zero
        # telemetry warn/block). 30-day watch; remove if still zero at 2026-08-05.
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "narrative_intent": {
        "class": "quality", "trivial_suppressible": True, "priority": 52,
        "description": "Narrative intent detection",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "anti_sycophancy_quality": {
        "class": "quality", "trivial_suppressible": True, "priority": 53,
        "description": "Anti-sycophancy quality gate",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.STANCE, ClaimKind.FACTUAL}),
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "advisory": {
        "class": "quality", "trivial_suppressible": True, "priority": 54,
        "description": "Advisory gate",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "reflect_integration": {
        "class": "quality", "trivial_suppressible": True, "priority": 55,
        "description": "Reflect integration",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "reasoning_quality_gate": {
        "class": "quality", "trivial_suppressible": True, "priority": 56,
        "description": "Reasoning quality gate",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        # 2026-07-06: BLOCK→ADVISORY per retirement review (zero blocks in 22d).
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "reasoning_enhanced": {
        "class": "quality", "trivial_suppressible": True, "priority": 57,
        "description": "Enhanced reasoning quality",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "existence_gate": {
        "class": "quality", "trivial_suppressible": True, "priority": 58,
        "description": "Unverified existence claims",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.FACTUAL}),
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "lazy_workaround_gate": {
        "class": "quality", "trivial_suppressible": True, "priority": 59,
        "description": "Lazy workaround detection",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "semantic_critic": {
        "class": "quality", "trivial_suppressible": True, "priority": 60,
        "description": "Semantic critic",
        "relevant_turn_kinds": _ANALYSIS_OR_UNKNOWN_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        # BLOCK = scoped self-critique enforcement. _run_semantic_critic only
        # escalates the high-signal profiles (evaluative_recommendation,
        # software_rca) to a one-shot block; general_diagnostic stays advisory.
        # Revert to pure advisory without code change:
        #   STOP_GATE_ROLLOUT_SEMANTIC_CRITIC=advisory
        "rollout_mode": RolloutMode.BLOCK,
    },
    "diagnostic_analysis_quality": {
        "class": "quality", "trivial_suppressible": True, "priority": 58,
        "description": "Diagnostic analysis quality gate",
        # Include UNKNOWN: RCA turns often classify as 'query' → TurnKind.UNKNOWN
        # (e.g. "what's the root cause?" bare-question turns), which the bare
        # _ANALYSIS_TURN_KINDS set excluded, silently skipping the gate. The
        # gate's own _is_diagnostic_turn() still self-gates on text, so widening
        # eligibility here does not fire on non-diagnostic unknown turns.
        "relevant_turn_kinds": _ANALYSIS_OR_UNKNOWN_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.CAUSAL, ClaimKind.FACTUAL}),
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.BLOCK,
    },
    "proposal_critique_gate": {
        "class": "quality", "trivial_suppressible": True, "priority": 72,
        "description": "Block proposals presented with no self-critique (presence check)",
        # Includes PLAN: proposals frequently arrive on plan turns ("what should we
        # do?" → "I recommend X"). Verified 2026-06-21 that such a turn classified
        # as PLAN and was silently skipped under the analysis/unknown-only set.
        "relevant_turn_kinds": _ANALYSIS_OR_UNKNOWN_TURN_KINDS | frozenset({TurnKind.PLAN}),
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        # BLOCK = deterministic presence enforcement. Quality-class, so turn-mode
        # suppression + regen circuit breaker bound it. Disable without code:
        #   PROPOSAL_CRITIQUE_GATE_ENABLED=false  (one-turn: --skip-critique-gate)
        "rollout_mode": RolloutMode.BLOCK,
    },
    "task_contract_fit": {
        "class": "quality", "trivial_suppressible": True, "priority": 61,
        "description": "Task contract fit check",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        # 2026-07-06: BLOCK→ADVISORY per retirement review (zero blocks in 22d).
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "phase0_depends_on_skills": {
        "class": "quality", "trivial_suppressible": True, "priority": 62,
        "description": "Phase 0 skills dependency check",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        # 2026-07-06: BLOCK→ADVISORY per retirement review (zero blocks in 22d).
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "dependency_chain_guard": {
        "class": "quality", "trivial_suppressible": True, "priority": 63,
        "description": "Dependency chain guard",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.FACTUAL, ClaimKind.CAUSAL}),
        "required_artifact_classes": frozenset(),
        # 2026-07-06: BLOCK→ADVISORY per retirement review (zero blocks in 22d).
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "comparative_claim_guard": {
        "class": "quality", "trivial_suppressible": True, "priority": 64,
        "description": "Comparative claim guard",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.FACTUAL}),
        "required_artifact_classes": frozenset(),
        # 2026-07-06: BLOCK→ADVISORY per retirement review (zero blocks in 22d).
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "behavior_gates_guidance": {
        "class": "quality", "trivial_suppressible": True, "priority": 65,
        "description": "Behavior guidance gate",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "recommendation_gate": {
        "class": "quality", "trivial_suppressible": True, "priority": 66,
        "description": "Recommendation quality gate",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": frozenset({ClaimKind.FACTUAL, ClaimKind.CAUSAL}),
        "required_artifact_classes": frozenset(),
        # 2026-07-06: BLOCK→ADVISORY per retirement review (zero blocks in 22d).
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "intent_artifact_alignment": {
        "class": "quality", "trivial_suppressible": True, "priority": 67,
        "description": "Intent-artifact alignment",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "tool_sanity": {
        "class": "quality", "trivial_suppressible": True, "priority": 68,
        "description": "Tool call sanity check",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "meta_analysis_trap": {
        "class": "quality", "trivial_suppressible": True, "priority": 69,
        "description": "Meta-analysis trap",
        "relevant_turn_kinds": _ANALYSIS_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    # Missing gates - added for Phase 2 completeness
    "task_contract_fit_v2": {
        "class": "quality", "trivial_suppressible": True, "priority": 70,
        "description": "Task contract fit validation",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    "subagent_opportunity": {
        "class": "quality", "trivial_suppressible": True, "priority": 71,
        "description": "Subagent opportunity detection",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
    # Claim/validation gap telemetry probe. Always allow (returns {}); emits to
    # the existing agentic_reliability_telemetry sink. Trivial-suppressible=False
    # ensures it fires on every turn (telemetry only — no enforcement).
    "claim_gap_telemetry_probe": {
        "class": "observability", "trivial_suppressible": False, "priority": 99,
        "description": "Claim/validation gap telemetry + warn (warn for validation, telemetry for structural)",
        "relevant_turn_kinds": _ALL_TURN_KINDS,
        "relevant_claim_kinds": _ALL_CLAIM_KINDS,
        "required_artifact_classes": frozenset(),
        "rollout_mode": RolloutMode.ADVISORY,
    },
}

# Policy block arbitration: when multiple policy gates block, use priority ordering.
# Keys are gate names; absent keys default to priority 99 (lowest precedence).
_POLICY_BLOCK_PRIORITY: dict[str, int] = {
    # Critical — highest precedence
    g: GATE_METADATA[g]["priority"]
    for g in GATE_METADATA
    if GATE_METADATA[g]["class"] == "policy"
}
# Verify GATE_CLASSES and GATE_METADATA stay in sync (runs in dev/test only)
if __debug__:
    for name, cls in GATE_CLASSES.items():
        meta = GATE_METADATA.get(name)
        if meta and meta["class"] != cls:
            raise AssertionError(
                f"GATE_CLASSES and GATE_METADATA out of sync for '{name}': "
                f"GATE_CLASSES={cls}, GATE_METADATA['class']={meta['class']}"
            )

IN_PROCESS_GATES = [
    # Telemetry evidence (524 records, 4 sessions, 35 gates):
    # - 28 gates fired exclusively allow across all sessions (active but not triggered)
    # - 7 gates produced non-allow outcomes (unverified_stance, epistemic_contract,
    #   reasoning_quality_gate, semantic_critic, advisory,
    #   anti_sycophancy_quality)
    # - 3 gates removed per silent-gate investigation 2026-05-08:
    #     existence_gate: explicitly disabled (_run_existence_gate returns None;
    #       strategy moved to unified_claim_verifier via _run_behavior_audit)
    #     reasoning_enhanced: Stop_reasoning_enhanced.py missing from disk
    #     correction_acknowledgment: CORRECTION_GATE_ENABLED=false (flag disables gate)

    (
        "frameguard_stop",
        _run_frameguard_stop,
    ),  # NEW 2026-03-18: FrameGuard - systemic reasoning contract
    ("skill_first_stop_gate", _run_skill_first_stop_gate),
    ("post_skill_prose_gate", _run_post_skill_prose_gate),
    ("verification_enforcement", _run_verification_enforcement),
    ("epistemic_contract", _run_epistemic_contract),
    ("behavior_audit", _run_behavior_audit),
    ("cited_content_guard", _run_cited_content_guard),
    ("cross_validator", _run_cross_validator),
    ("unverified_stance", _run_unverified_stance),
    ("dependency_chain_guard", _run_dependency_chain_guard),
    ("comparative_claim_guard", _run_comparative_claim_guard),
    ("command_execution_validator", _run_command_execution_validator),
    ("reflect_integration", _run_reflect_integration),
    ("reasoning_quality_gate", _run_reasoning_quality_gate),
    ("lazy_workaround_gate", _run_lazy_workaround_gate),
    ("recommendation_gate", _run_recommendation_gate),
    ("intent_artifact_alignment", _run_intent_artifact_alignment),
    ("semantic_critic", _run_semantic_critic),
    ("proposal_critique_gate", _run_proposal_critique_gate),
    ("task_contract_fit", _run_task_contract_fit_gate),
    ("task_contract_fit_v2", _run_task_contract_fit_gate_v2),  # shadow mode by default
    (
        "deletion_verification_guard",
        _run_deletion_verification_guard,
    ),  # NEW 2026-03-24: Deletion verification - checks actual file system state

    (
        "artifact_enforcement",
        _run_artifact_enforcement,
    ),  # NEW 2026-05-08: Artifact enforcement for mechanism claims
    (
        "runtime_claim_enforcement",
        _run_runtime_claim_gate,
    ),  # Phase 3: Runtime claim artifact verification
    # ("external_judge", _run_judge_evaluation),  # DISABLED: Judge produced no actionable value.
    # Override already demoted blocks to advisory; 24h summary disabled in judge_feedback.py.
    ("git_diff_reground", _run_git_diff_reground),
    ("skill_dir_correlation", _run_skill_dir_correlation_gate),
    ("cks_correction_anchor", _run_cks_correction_anchor),
    ("phase0_depends_on_skills", _run_phase0_depends_on_skills),
    ("tool_sanity", _run_tool_sanity_check),
    ("repetition_blocker", _run_repetition_blocker),
    ("fake_done", _run_fake_done_detector),
    # Migrated 2026-06-14 from cc-aca-epistemic plugin hooks.json (subprocess) to
    # local in-process dispatch (split-dispatch consolidation). Logic stays in the
    # plugin stop dir (on sys.path); these wrappers import + normalize it.
    ("perf_attribution", _run_perf_attribution_gate),
    ("removal_completeness", _run_removal_completeness_guard),
    ("diagnostic_analysis_quality", _run_diagnostic_analysis_quality_gate),
    # Migrated 2026-06-15 from cc-aca-observability plugin hooks.json (subprocess).
    ("cjk_drift_detector", _run_cjk_drift_detector),
    ("subagent_opportunity", _run_subagent_opportunity),  # Advisory for delegation opportunities
    ("clear_referent_anchors", _clear_referent_anchors),  # Single-turn lifecycle: clear anchors at end of turn
    # Claim/validation gap telemetry probe (telemetry-only, never blocks).
    # run() returns {} unconditionally; emitting to agentic_reliability_telemetry.jsonl.
    ("claim_gap_telemetry_probe", _run_claim_gap_telemetry_probe),
]

# Non-Blocking Side Effects (still subprocess for isolation)
# Note: auto-commit now dispatches via the cc-skills-utils plugin Stop router.
SIDE_EFFECTS = [
    # Re-enabled 2026-07-04 BEHIND the calibrated quality gate (scripts/cks/quality_gate.py,
    # measured 109/109 junk rejected). Extractor quality fix still tracked as #1078.
    "Stop_cks_decision_capture.py",
    "Stop_cleanup_verifier.py",
    "Stop_contract_status.py",  # Auto-surfaces contract dashboard at turn end
]


def run_side_effect(hook_name: str, input_data: str) -> None:
    """Run a side-effect hook in subprocess (isolated, fire-and-forget)."""
    try:
        hook_path = HOOKS_DIR / hook_name
        if not hook_path.exists():
            return

        # CKS decision capture needs more time
        timeout = 30.0 if "cks_decision" in hook_name else 5.0
        creation_flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=input_data.encode(),
            capture_output=True,
            timeout=timeout,
            creationflags=creation_flags,
        )
        if result.returncode != 0:
            stderr = result.stderr.decode(errors="replace").strip()
            if stderr:
                _logger.warning(f"side-effect error {hook_name}: {stderr}")
    except Exception as e:
        _logger.warning(f"side-effect exception {hook_name}: {e}")


CRITICAL_STOP_GATES = frozenset((
    "destructive_cleanup_detector",  # advisory-only detector, but must not silently fail
))

# Module-level critical gate failure flag for this turn
_critical_gate_failed_this_turn: bool = False

# Phase 2 policy block arbitration: name of the winning policy blocker for this turn.
_policy_block_this_turn: str | None = None  # reset each turn in main()


def _log_policy_block_suppressed(
    data: dict, suppressed_gate: str, winner_gate: str,
    suppressed_prio: int, winner_prio: int, result: dict,
) -> None:
    """Log a suppressed policy block to telemetry for arbitration audit.

    This helps tune _POLICY_BLOCK_PRIORITY by showing which blocks were
    suppressed and why. Suppressed blocks don't exit — they're silent.
    """
    try:
        from __lib.stop_gate_telemetry import log_gate_event
        log_gate_event(
            gate_name=suppressed_gate,
            classification="policy",
            profile=result.get("_critic_profile"),
            decision="allow",  # was suppressed, so telemetry shows "allow"
            session_id=data.get("session_id") or data.get("sessionId"),
            terminal_id=data.get("terminal_id"),
            extra={
                "suppressed_by_policy_arb": winner_gate,
                "suppressed_priority": suppressed_prio,
                "winner_priority": winner_prio,
                "skip_reason": f"policy_arb:winner={winner_gate}",
            },
        )
    except Exception:
        pass  # Telemetry errors never disrupt gate processing


def _run_gate_safe(name: str, gate_fn, data: dict) -> dict | None:
    """Run a single gate, catching exceptions to prevent cascade failure.

    Critical gates fail CLOSED: if a critical gate crashes, the turn is flagged
    and advisory/warn messages surface the failure so the model does not silently proceed.

    NOTE: None returns from a gate (whether from an early-exit check, a disabled gate,
    or an exception caught here) map to allow — _process_gate_result checks 'if not res'
    and returns False. Gates that need to warn or block must return a dict with a
    'decision' key ('warn' or 'block') or a 'systemMessage' key.
    """
    global _critical_gate_failed_this_turn
    try:
        return gate_fn(data)
    except Exception as e:
        print(f"[STOP_GATE_ERROR] gate {name} crashed: {e}", file=sys.stderr)
        # Persistent dead-gate log: stderr flickers and is gone; this surfaces at
        # the next SessionStart via gate_health.read_recent_faults(). Before this,
        # a swallowed gate exception was invisible across the whole session.
        try:
            if str(HOOKS_DIR / "__lib") not in sys.path:
                sys.path.insert(0, str(HOOKS_DIR / "__lib"))
            from gate_health import record_fault
            record_fault("Stop", name, repr(e), terminal_id=str(data.get("terminal_id", "")))
        except Exception:
            pass  # never let the alarm itself become a fault source
        _critical_gate_failed_this_turn = True
        if name in CRITICAL_STOP_GATES:
            # Fail closed: surface the failure so the model is aware
            return {
                "decision": "allow",  # don't block the turn
                "systemMessage": (
                    f"SAFETY WARNING: {name} could not run (internal error: {e}). "
                    "Treat the system as degraded. Avoid destructive actions until the issue is diagnosed."
                ),
            }
        return None


def _log_regen_iteration(data: dict, gate_name: str, count: int, tripped: bool) -> None:
    """Append one regen-cap data point for threshold tuning. Best-effort, never raises.

    Stream: logs/diagnostics/regen_cap_telemetry.jsonl — one row per QUALITY-gate block.
    Fields: ts, gate, count (repair iterations so far this continuation chain),
            tripped (True when the cap fired -> allow+surface), stop_hook_active,
            terminal_id. Query/notify via scripts/regen_cap_stats.py.
    """
    try:
        import time as _t
        rec = {
            "ts": _t.time(),
            "gate": gate_name,
            "count": int(count),
            "tripped": bool(tripped),
            "stop_hook_active": bool(data.get("stop_hook_active", False)),
            "terminal_id": data.get("terminal_id") or data.get("session_id") or "",
        }
        p = HOOKS_DIR / "logs" / "diagnostics" / "regen_cap_telemetry.jsonl"
        p.parent.mkdir(parents=True, exist_ok=True)
        from file_lock import append_jsonl_safe
        append_jsonl_safe(p, rec, ensure_ascii=True)
    except OSError:
        pass


def _process_gate_result(
    res: dict, name: str, system_messages: list[str],
    quality_messages: list[str], data: dict,
    turn_mode: str, quality_mode: str,
    session_mode: SessionMode = "normal",
) -> bool:
    """Route a gate result: block exits immediately, otherwise route systemMessage.

    Quality gate blocks are suppressed on control/exploration turns (normal mode)
    or control turns only (strict mode), matching the systemMessage suppression.
    Policy gate blocks always fire regardless of turn mode.

    Phase 2 policy block arbitration: when multiple policy gates would block,
    only the highest-priority one is surfaced. Lower-priority blocks are suppressed
    and logged with suppressed_by_policy_arb for telemetry.

    Returns True if the turn was blocked (caller should exit), False to continue.
    """
    global _policy_block_this_turn
    if not res:
        return False
    if res.get("decision") == "block":
        gate_class = GATE_CLASSES.get(name, "policy")
        # DEBUG_GATES session mode: disable ALL quality gates.
        # AUDIT session mode: treat all as CONTROL (already reflected in effective_mode).
        # Weak (non-Claude) models: suppress quality blocks; policy blocks still fire.
        if gate_class == "quality" and (
            is_quality_gate_disabled(session_mode)
            or is_quality_mode_suppressed(turn_mode, quality_mode)
            or is_weak_model(data)
        ):
            return False

        # Regeneration cap (NBM-3 circuit breaker): bound how many times a QUALITY
        # gate can block-and-force-regenerate within one continuation chain. Once the
        # threshold of repair iterations is reached, surface the unresolved verdict as
        # an advisory instead of blocking again — turning an unbounded block->regenerate
        # loop into a bounded one. Policy gates are exempt (real violations keep blocking).
        # Fail-open: any breaker error must never disable gate enforcement.
        if gate_class == "quality":
            try:
                from __lib.circuit_breaker import (
                    should_allow_continue,
                    increment_iteration,
                    get_iteration_count,
                )
                _cb_key = (
                    data.get("terminal_id") or data.get("session_id")
                    or data.get("sessionId") or "default"
                )
                _cb_active = bool(data.get("stop_hook_active", False))
                if should_allow_continue(_cb_key, _cb_active):
                    # Breaker tripped: already blocked >= threshold times this chain.
                    # Allow the response, surface the unresolved gate verdict to the user.
                    _capped_reason = str(res.get("reason", "")).strip()
                    quality_messages.append(
                        f"[unresolved after repeated attempts — {name}] {_capped_reason}"
                    )
                    _log_stop_block_event(
                        data, name, {**res, "decision": "regen_capped"}
                    )
                    _log_regen_iteration(data, name, get_iteration_count(_cb_key), tripped=True)
                    return False
                if _cb_active:
                    # Still below threshold and actively continuing: count this block.
                    increment_iteration(_cb_key)
                # Record the per-block iteration count for threshold tuning.
                _log_regen_iteration(data, name, get_iteration_count(_cb_key), tripped=False)
            except Exception:
                pass

        # Phase 2 policy block arbitration: only surface the highest-priority block.
        # Higher priority = lower numeric value (0 is highest).
        if gate_class == "policy":
            existing_blocker = _policy_block_this_turn
            if existing_blocker is not None:
                # Another policy gate already blocked this turn.
                # Suppress this one if it has lower priority (higher number).
                my_prio = _POLICY_BLOCK_PRIORITY.get(name, 99)
                existing_prio = _POLICY_BLOCK_PRIORITY.get(existing_blocker, 99)
                if my_prio >= existing_prio:
                    # We have lower or equal priority — suppress this block.
                    # Log suppressed_by_policy_arb so telemetry captures both.
                    _log_policy_block_suppressed(data, name, existing_blocker, my_prio, existing_prio, res)
                    return False
            # We're the winning blocker (or first blocker).
            _policy_block_this_turn = name

        _log_stop_block_event(data, name, res)
        if "blocking_hook" not in res:
            res["blocking_hook"] = f"Stop.py:{name}"
        print(json.dumps(res))
        return True
    msg = res.get("systemMessage")
    if msg:
        gate_class = GATE_CLASSES.get(name, "policy")
        if gate_class == "policy":
            system_messages.append(msg)
        else:
            quality_messages.append(msg)
    return False


def _get_contract_status_output() -> str:
    """Get contract system status for display.

    Reads telemetry logs and returns a compact dashboard string.
    This is the in-process version used by Stop.py main().
    For the standalone side-effect, see Stop_contract_status.py.
    """
    from datetime import datetime as _datetime, timezone as _timezone

    # Paths resolved from hook location
    _writer_log = HOOKS_DIR / "logs" / "diagnostics" / "task_contract_writer_telemetry.jsonl"
    _stop_log = HOOKS_DIR / "logs" / "diagnostics" / "task_contract_telemetry.jsonl"

    def _load_events(path: Path) -> list[dict]:
        if not path.exists():
            return []
        events = []
        try:
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        except (OSError, IOError):
            pass
        return events

    def _age_hours(ts: float) -> str:
        now = _datetime.now(_timezone.utc).timestamp()
        h = (now - ts) / 3600
        return f"{h:.1f}h" if h < 24 else f"{h / 24:.1f}d"

    writer_events = _load_events(_writer_log)
    stop_events = _load_events(_stop_log)

    if not writer_events and not stop_events:
        return ""

    lines = ["─" * 40]

    # Writer summary
    active = [e for e in writer_events if e.get("event") == "contract_active"]
    skipped = [e for e in writer_events if e.get("event") == "contract_skip"]
    not_task = [e for e in skipped if e.get("reason") == "not_a_task_start"]
    if writer_events:
        latest = max(e.get("timestamp", 0) for e in writer_events)
        age = _age_hours(latest)
        tc_counts: dict[str, int] = {}
        for e in active:
            tc = e.get("task_class", "unknown")
            tc_counts[tc] = tc_counts.get(tc, 0) + 1
        tc_str = ", ".join(f"{k}={v}" for k, v in sorted(tc_counts.items())) if tc_counts else ""
        lines.append(
            f"Contract Writer: {len(active)} contracts, "
            f"{len(skipped)} skips ({len(not_task)} not-task) | "
            f"Last: {age}" + (f" [{tc_str}]" if tc_str else "")
        )

    # Stop summary
    allowed = [e for e in stop_events if e.get("decision") == "allow"]
    blocked = [e for e in stop_events if e.get("decision") == "block"]
    silent = [e for e in stop_events if e.get("event") == "silent"]
    if stop_events:
        silent_reasons: dict[str, int] = {}
        for e in silent:
            r = e.get("reason", "unknown")
            silent_reasons[r] = silent_reasons.get(r, 0) + 1
        sr = ", ".join(f"{k}={v}" for k, v in sorted(silent_reasons.items(), key=lambda x: -x[1])[:2])
        lines.append(
            f"Contract Stop: {len(allowed)} allow, {len(blocked)} block, "
            f"{len(silent)} silent" + (f" [{sr}]" if sr else "")
        )

    return "\n".join(lines)


def _turn_mode_to_turn_kind(mode: str) -> TurnKind:
    """Map string turn_mode from __lib.turn_mode to Phase 2 TurnKind enum."""
    mapping = {
        "analysis": TurnKind.ANALYSIS,
        "control": TurnKind.CONTROL,
        "exploration": TurnKind.EXPLORATION,
        "plan": TurnKind.PLAN,
        "execution-report": TurnKind.EXECUTION_REPORT,
        "final-answer": TurnKind.FINAL_ANSWER,
        "audit-report": TurnKind.CONTROL,  # Phase 4.A: audit reports treated like control for format enforcement
    }
    return mapping.get(mode.lower(), TurnKind.UNKNOWN)


def _log_gate_skip(
    name: str, reason: str,
    turn_kind: TurnKind, claim_kind: ClaimKind,
    data: dict, system_messages: list[str], quality_messages: list[str],
) -> None:
    """Log gate skip event and emit telemetry for a skipped gate."""
    try:
        from __lib.stop_gate_telemetry import log_gate_event
        log_gate_event(
            gate_name=name,
            classification=GATE_CLASSES.get(name, "policy"),
            profile=None,
            decision="allow",  # skipped = treated as allow
            session_id=data.get("session_id") or data.get("sessionId"),
            terminal_id=data.get("terminal_id"),
            skip_reason=reason,
            turn_kind=turn_kind.value if turn_kind else None,
            claim_kind=claim_kind.value if claim_kind else None,
            rollout_mode=GATE_METADATA.get(name, {}).get("rollout_mode", RolloutMode.BLOCK).value
                        if GATE_METADATA.get(name) else None,
        )
    except Exception:
        pass  # Telemetry errors never disrupt gate processing


def _merge_quality_messages(
    system_messages: list[str], quality_messages: list[str],
    turn_mode: str, quality_mode: str,
) -> None:
    """Append quality messages to system_messages only when not suppressed."""
    if not is_quality_mode_suppressed(turn_mode, quality_mode):
        system_messages.extend(quality_messages)


def _classify_error_events(cc_errors_log: Path) -> tuple[int, int, int, int]:
    """Classify events in cc_errors.jsonl into errors/real_failures/expected/known_fixed.

    Two-layer strategy (A4):
      Layer 1 (structured fields): error_class, is_startup_actionable from log producers
        - error_class="timeout" -> expected_ops
        - error_class="known_fixed" -> known_fixed (not real failure)
        - error_class="load_failure" + is_startup_actionable=False -> known_fixed
        - error_class="load_failure" + is_startup_actionable=True -> real failure
        - error_class="runtime_error" + is_startup_actionable=True -> real failure
      Layer 2 (legacy fallback): string patterns in error_type/error_message
        - For entries written before A3 structured tagging existed

    Args:
        cc_errors_log: Path to cc_errors.jsonl log file.

    Returns:
        Tuple of (total_errors_last_hour, real_failures_last_hour,
                 expected_timeouts_last_hour, known_fixed_last_hour).
    """
    errors_last_hour = 0
    real_failures_last_hour = 0
    expected_ops_last_hour = 0
    known_fixed_last_hour = 0

    _EXPECTED_TIMEOUT_TYPES = ("timeout_imminent", "timeout_terminated",
                               "timeout_killed", "timeout_exceeded")

    if not cc_errors_log.exists():
        return 0, 0, 0, 0

    try:
        one_hour_ago = time.time() - 3600

        with open(cc_errors_log, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts_str = entry.get("timestamp", "")
                    if not ts_str:
                        continue

                    try:
                        from datetime import datetime

                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        ts_epoch = ts.timestamp()
                        if ts_epoch >= one_hour_ago:
                            errors_last_hour += 1

                            # Layer 1: structured fields from A3 log producers
                            error_class = entry.get("error_class")
                            if error_class is not None:
                                # Use structured classification
                                if error_class == "timeout":
                                    expected_ops_last_hour += 1
                                elif error_class == "known_fixed":
                                    known_fixed_last_hour += 1
                                elif error_class == "load_failure":
                                    # actionable=True -> real failure; False -> known_fixed
                                    if entry.get("is_startup_actionable", True):
                                        real_failures_last_hour += 1
                                    else:
                                        known_fixed_last_hour += 1
                                elif error_class == "runtime_error":
                                    if entry.get("is_startup_actionable", True):
                                        real_failures_last_hour += 1
                                    else:
                                        known_fixed_last_hour += 1
                                else:
                                    # Unknown error_class - treat as real failure (fail-safe)
                                    real_failures_last_hour += 1
                                continue

                            # Layer 1 partial: has is_startup_actionable=False but no error_class
                            # This is still a structured signal — treat as known_fixed
                            if entry.get("is_startup_actionable") is False:
                                known_fixed_last_hour += 1
                                continue

                            # Layer 2: fallback for legacy records without structured fields
                            err_type = entry.get("error_type", "")
                            err_msg = entry.get("error_message", "")
                            if any(p in err_type.lower() for p in _EXPECTED_TIMEOUT_TYPES):
                                expected_ops_last_hour += 1
                            elif _is_known_fixed_legacy(err_type, err_msg):
                                known_fixed_last_hour += 1
                            else:
                                real_failures_last_hour += 1
                    except Exception:
                        continue
                except json.JSONDecodeError:
                    continue
    except Exception:
        pass

    return errors_last_hour, real_failures_last_hour, expected_ops_last_hour, known_fixed_last_hour


def _is_known_fixed_legacy(err_type: str, err_msg: str) -> bool:
    """Check legacy (pre-A3) record for known-fixed patterns.

    These are errors from refactoring artifacts that have already been addressed.
    Used only as Layer 2 fallback when structured error_class field is absent.
    """
    import re as _re
    combined = f"{err_type.lower()}|{err_msg.lower()}"
    _KNOWN_FIXED_PATTERNS = (
        "syntax_error",
        "parse_error",
        "name 'anomalies'",
        "name 'user_prompt'",
        _re.compile(r"attributeerror.*unknown", _re.IGNORECASE),
        _re.compile(r"attributeerror.*audit_report", _re.IGNORECASE),
    )
    for p in _KNOWN_FIXED_PATTERNS:
        if isinstance(p, _re.Pattern):
            if p.search(combined):
                return True
        elif p in combined:
            return True
    return False


def _enrich_user_prompt(data: dict) -> None:
    """Populate data["user_prompt"] from the transcript_path JSONL.

    The real Stop payload has no user_prompt/prompt/transcript fields — user
    text lives only in the transcript_path JSONL. Enrich once at entry so every
    gate that reads data["user_prompt"] (semantic critic, turn-mode flags,
    agreement gate, meta-analysis trap) sees the actual prompt instead of "".
    Fail-open: enrichment errors leave the payload unchanged.

    Works on stop-hook continuations too: synthetic "Stop hook feedback" user
    entries carry isMeta and are excluded by transcript_reader, so the last
    REAL user prompt is returned even on regen turns.
    """
    if data.get("user_prompt") or data.get("prompt"):
        return
    try:
        from __lib.transcript_reader import get_latest_user_text
        # Tail-read: the latest user message lives near the end; transcripts
        # grow unbounded and a full read would sit on every Stop's critical
        # path. A single >1MB trailing tool_result can push the prompt out of
        # the first window, so escalate once before giving up (fail-open).
        for _tail in (1_048_576, 16_777_216):
            latest_user = get_latest_user_text(data, tail_bytes=_tail)
            if latest_user:
                data["user_prompt"] = latest_user
                return
    except Exception:
        pass


def _apply_json_validation_guard(
    output: dict, data: dict, hooks_dir: "Path",
) -> None:
    """Warn if the current session has a recent JSON validation failure in stderr log.

    Advisory only — adds to systemMessage, never blocks.
    Reads hooks_dir/logs/diagnostics/hook_runner_stderr.jsonl and checks
    for "JSON validation failed" entries matching the current session_id
    within the last 5 minutes.
    """
    from datetime import datetime as _dt, timezone as _tz

    stderr_log = hooks_dir / "logs" / "diagnostics" / "hook_runner_stderr.jsonl"
    session = data.get("session_id", "")
    if not stderr_log.exists() or not session:
        return

    now = _dt.now(_tz.utc)
    for line in stderr_log.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get("session_id") != session:
            continue
        if "JSON validation failed" not in str(entry.get("stderr", "")):
            continue
        ts_str = str(entry.get("ts", ""))
        try:
            ts = _dt.fromisoformat(ts_str)
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=_tz.utc)
        except (ValueError, TypeError):
            continue
        if (now - ts).total_seconds() < 300:
            warn = (
                "Stop hook JSON validation failure detected in this session "
                "(last 5 minutes). Do not claim clean DONE — verify the "
                "actual hook-runner output is schema-valid first."
            )
            if "systemMessage" in output:
                output["systemMessage"] = output["systemMessage"] + "\n\n" + warn
            else:
                output["systemMessage"] = warn
            return


def main():
    global _critical_gate_failed_this_turn, _policy_block_this_turn
    _critical_gate_failed_this_turn = False  # reset per turn
    _policy_block_this_turn = None  # reset per turn (Phase 2 policy block arbitration)
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        print("{}")
        sys.exit(0)

    try:
        raw_input = raw_input.lstrip("\ufeff")
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        print("{}")
        sys.exit(0)

    # Build per-turn block context for stop_blocks.jsonl diagnostic logging.
    # Encoding raw_input as bytes matches the subprocess-router contract.
    try:
        from __lib.stop_block_log import _extract_block_ctx as _sbl_extract
        _stop_block_ctx = _sbl_extract("Stop", raw_input.encode("utf-8", "replace"))
    except Exception:
        _stop_block_ctx = None

    # CC passes last_assistant_message, not response. Normalize so all
    # downstream gates (anti-sycophancy, overconfidence, lazy closure, etc.)
    # can read data["response"] as they expect.
    if "response" not in data and "last_assistant_message" in data:
        data["response"] = data["last_assistant_message"]

    # Normalize output_text for gates that expect it (fake_done, meta_analysis_trap, etc.)
    # These hooks were written against a different data contract and read output_text
    # instead of response. Alias it here so they work without modification.
    if "output_text" not in data:
        data["output_text"] = data.get("response", "")

    _enrich_user_prompt(data)

    _pin_scope_env(data)

    # Regen cap: a fresh stop (not a stop-hook-driven continuation) resets the
    # circuit-breaker iteration counter, so quality-gate block counts never bleed
    # across unrelated turns. Fail-open. Paired with the cap in _process_gate_result.
    try:
        if not data.get("stop_hook_active", False):
            from __lib.circuit_breaker import reset_iteration
            _cb_key = (
                data.get("terminal_id") or data.get("session_id")
                or data.get("sessionId") or "default"
            )
            reset_iteration(_cb_key)
    except Exception:
        pass

    # user_prompt is used by gate functions inside the loop — extract once here
    user_prompt = data.get("user_prompt", "") or data.get("prompt", "")

    # Classify turn mode once — used for quality gate suppression
    turn_mode = _classify_turn_mode(data)
    quality_mode = os.environ.get("STOP_QUALITY_MODE", "normal")

    system_messages: list[str] = []
    quality_messages: list[str] = []
    # Raw messages for aggregation: (hook_name, severity, message)
    _raw_messages: list[tuple[str, str, str]] = []
    _gate_rollout_override: dict[str, RolloutMode] = {}

    # Post-violation gates: these need all_violations populated from earlier gate results.
    # acknowledgment_loop and repetition_blocker need to know what violations earlier
    # gates detected in this turn. They run late in the list, so by the time they execute,
    # _raw_messages has results from all preceding gates.
    _POST_VIOLATION_GATES = frozenset((
        "acknowledgment_loop", "repetition_blocker",
    ))

    # Phase 1 Step 2: Trivial exchange detection at Stop entry.
    # Short-circuits quality gates before they run when the exchange is low-stakes.
    # Policy gates are NOT suppressible (GATE_METADATA["trivial_suppressible"] == False).
    # Contract completions are NOT trivial — pass contract_active=True.
    _trivial_detected = False
    _trivial_reason = ""
    _response_for_trivial = data.get("response", "") or data.get("last_assistant_message", "")
    if _response_for_trivial:
        _contract = None
        try:
            from __lib.task_contract import load_contract as _load_contract
            _, _tid = _resolve_scope_ids(data)
            if _tid:
                _contract = _load_contract(_tid)
        except Exception:
            pass
        _trivial_detected, _trivial_reason = _is_trivial_exchange(
            context=data,
            response=_response_for_trivial,
            turn_mode=turn_mode,
            contract_active=_contract is not None,
        )
        if _trivial_detected:
            from __lib.trivial_turns import log_trivial_skip
            log_trivial_skip("stop_entry", _trivial_reason, turn_mode, _response_for_trivial)

    # Run all in-process gates
    for name, gate_fn in IN_PROCESS_GATES:
        # Enrich data for post-violation gates with current turn's detected issues
        if name in _POST_VIOLATION_GATES and "all_violations" not in data:
            data["all_violations"] = [
                {"type": hook_name, "message": msg}
                for hook_name, severity, msg in _raw_messages
            ]

        # Phase 2 applicability routing: check turn kind, claim kind, artifact requirements.
        # Maps string turn_mode → TurnKind enum for is_gate_applicable.
        # Session mode: audit/debug_gates → all turns as CONTROL for gate suppression.
        session_mode = get_session_mode(user_prompt)
        effective_mode = get_effective_turn_mode_for_gate(turn_mode, session_mode)
        gate_turn_kind = _turn_mode_to_turn_kind(effective_mode)
        # Simple claim kind from gate's GATE_METADATA — use FACTUAL as safe default
        gate_claim_kind = ClaimKind.FACTUAL

        applicable, skip_reason = is_gate_applicable(
            name, gate_turn_kind, gate_claim_kind, set(),
        )
        if not applicable:
            _log_gate_skip(
                name, skip_reason, gate_turn_kind, gate_claim_kind,
                data, system_messages, quality_messages,
            )
            continue

        # Phase 2 rollout mode handling: downgrades block→warn for ADVISORY.
        # _process_gate_result applies policy block arbitration before this.
        meta = GATE_METADATA.get(name)
        gate_rollout = _get_rollout_mode(name, meta.get("rollout_mode", RolloutMode.BLOCK) if meta else RolloutMode.BLOCK)
        # ADVISORY: convert block to warn after _process_gate_result runs.
        _gate_rollout_override[name] = gate_rollout

        res = _run_gate_safe(name, gate_fn, data)
        # Phase 1 Step 2 (continued): Trivial short-circuit.
        # Quality gates are suppressed on trivial exchanges; policy gates never are.
        if _trivial_detected:
            meta = GATE_METADATA.get(name)
            if meta and meta["trivial_suppressible"]:
                # Quality gate on trivial exchange — skip entirely (allow silently)
                _log_gate_skip(
                    name, "trivial_exchange", gate_turn_kind, gate_claim_kind,
                    data, system_messages, quality_messages,
                )
                continue
        # Always capture result for unverified_stance so telemetry fires on allow.
        # On other gates this is a no-op (value is re-assigned next loop iteration).
        if name == "unverified_stance":
            _unverified_stance_res = res
        blocked = _process_gate_result(
            res, name, system_messages, quality_messages, data,
            effective_mode, quality_mode,
            session_mode=session_mode,
        )

        # Phase 2 ADVISORY rollout: downgrades block→warn after _process_gate_result.
        # Policy block arbitration (higher-priority wins) has already run inside
        # _process_gate_result. Here we handle rollout-mode downgrade.
        if blocked:
            rollout = _gate_rollout_override.get(name, RolloutMode.BLOCK)
            if rollout == RolloutMode.ADVISORY:
                # Convert block to systemMessage warn, suppress exit.
                _raw_messages.append((name, "warn", f"[{name}] block downgraded to warn (ADVISORY rollout)"))
                blocked = False
            elif rollout == RolloutMode.SHADOW:
                # Shadow mode: log but don't block.
                _raw_messages.append((name, "warn", f"[{name}] shadow-mode allow (no block)"))
                blocked = False
            else:
                # Normal BLOCK — exit as usual (sys.exit in telemetry section below).
                pass
        try:
            from __lib.stop_gate_telemetry import log_gate_event

            gate_class = GATE_CLASSES.get(name, "policy")
            critic_profile = res.get("_critic_profile") if res else None
            decision = (
                "block"
                if blocked
                else ("warn" if res and res.get("systemMessage") else "allow")
            )
            extra: dict[str, Any] | None = None
            if name == "phase0_depends_on_skills" and res and "metadata" in res:
                extra = dict(res["metadata"])
            elif name == "unverified_stance" and _unverified_stance_res:
                # Loop-fix monitoring: pass violation metadata for telemetry
                # block_triggered: blocks detected (HIGH PRIORITY signal #2)
                # warn_issued: warnings issued even though response allowed
                #   (potential false positive signal if response is markdown-heavy)
                extra = {
                    "block_triggered": _unverified_stance_res.get("block") is True,
                    "warn_issued": (
                        _unverified_stance_res.get("allow") is True
                        and bool(_unverified_stance_res.get("note", ""))
                    ),
                }
            log_gate_event(
                gate_name=name,
                classification=gate_class,
                profile=critic_profile,
                decision=decision,
                session_id=data.get("session_id") or data.get("sessionId"),
                terminal_id=data.get("terminal_id"),
                # Phase 2 enriched fields
                turn_kind=gate_turn_kind.value,
                claim_kind=gate_claim_kind.value,
                rollout_mode=_gate_rollout_override.get(name, RolloutMode.BLOCK).value,
                visible=bool(res and (res.get("systemMessage") or res.get("decision") == "block")),
                extra=extra,
                # Phase 3: runtime claim artifact enrichment (runtime_claim_enforcement gate)
                artifact_class_required=(
                    res.get("claim_types", [None])[0]
                    if res and name == "runtime_claim_enforcement" and res.get("claim_types")
                    else None
                ),
                artifact_class_observed=(
                    ", ".join(res["messages"])
                    if res and name == "runtime_claim_enforcement" and res.get("messages")
                    else None
                ),
            )
        except Exception:
            pass
        # --- End telemetry ---

        if blocked:
            try:
                from __lib.stop_block_log import _log_stop_block as _sbl_log
                _block_reason = ""
                if res:
                    _block_reason = str(res.get("reason") or res.get("systemMessage") or "")
                _sbl_log(name, _block_reason, "", _stop_block_ctx)
            except Exception:
                pass
            sys.exit(0)
        # Collect raw messages for aggregation: (hook_name, severity, message)
        # systemMessage gates emit warnings by default
        if res and res.get("systemMessage"):
            _raw_messages.append((name, "warn", res["systemMessage"]))

    # Stop-side recommendation closed loop: gate the prior turn and (if it looks like a
    # recommendation) spawn a DETACHED LLM judge subprocess that persists a one-line
    # correction for next turn's UserPromptSubmit. NEVER blocks Stop; fail-open on any error.
    try:
        from UserPromptSubmit_modules.recommendation_loop import record_at_stop
        record_at_stop(data)
    except Exception:
        pass  # Recommendation loop must never disrupt Stop processing

    # Stop-side technical-debt recorder: persist deduped lazy-closure items for the
    # /debt workflow and next-turn review. Fail-open so it never blocks Stop.
    try:
        from Stop_lazy_closure_debt import record_at_stop as record_debt_at_stop
        record_debt_at_stop(data)
    except Exception:
        pass  # Debt recorder must never disrupt Stop processing

    # Merge quality messages based on turn mode and enforcement mode
    _merge_quality_messages(system_messages, quality_messages, turn_mode, quality_mode)

    # Write violation state for cross-turn tracking (repetition detection).
    # The repetition_blocker gate reads this state in subsequent turns to detect
    # repeated violations. Without this write, state is never populated.
    if _raw_messages:
        try:
            from hook_state_manager import set_last_violations
            _tid = data.get("terminal_id") or data.get("terminalId") or os.environ.get("CLAUDE_TERMINAL_ID", "")
            _sid = data.get("session_id") or data.get("sessionId") or os.environ.get("CLAUDE_SESSION_ID", "")
            if _tid:
                _violation_types = [h for h, _, _ in _raw_messages]
                set_last_violations(
                    _tid, _sid,
                    turn_number=int(time.time()),
                    violations=_violation_types,
                    user_corrected=False,
                    acknowledged=False,
                )
        except Exception:
            pass  # Observability must not change hook behavior

    # Process Side Effects (only if not blocked)
    if SIDE_EFFECTS and not os.environ.get("STOP_NO_SIDE_EFFECTS"):
        import concurrent.futures

        input_str = json.dumps(data)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(SIDE_EFFECTS)) as executor:
            for hook in SIDE_EFFECTS:
                executor.submit(run_side_effect, hook, input_str)

    output = {}
    # Apply aggregation to raw messages before rendering
    aggregated = _aggregate_and_render(_raw_messages)
    if aggregated:
        if system_messages:
            system_messages.append(aggregated)
        else:
            system_messages = [aggregated]
    if system_messages:
        output["systemMessage"] = "\n".join(system_messages)

    # Contract System Status — only surface when a gate is already blocking.
    # systemMessage in Stop hooks always triggers a resend regardless of continue,
    # so injecting unconditionally halts the LLM on every turn with telemetry data.
    _is_blocking = output.get("continue") is False or output.get("decision") == "block"
    if _is_blocking:
        _contract_status = _get_contract_status_output()
        if _contract_status:
            if "systemMessage" in output:
                output["systemMessage"] = output["systemMessage"] + "\n\n" + _contract_status
            else:
                output["systemMessage"] = _contract_status


    # Runtime failure alert: inject on blocks if real failures exceeded threshold.
    # Only reads cc_errors.jsonl (runtime telemetry), never hook_health.json (startup data).
    if _is_blocking:
        cc_errors_log = HOOKS_DIR / "logs" / "diagnostics" / "cc_errors.jsonl"
        try:
            errors_last_hour, real_failures_last_hour, expected_ops_last_hour, known_fixed_last_hour = _classify_error_events(
                cc_errors_log
            )
            error_threshold = int(os.environ.get("CC_ERRORS_THRESHOLD", "5"))
            if real_failures_last_hour > error_threshold:
                alert_lines = [
                    "=" * 60,
                    "⚠️  HOOK HEALTH ALERT",
                    "=" * 60,
                    f"Real failures (1h): {real_failures_last_hour}",
                    f"Expected timeouts (1h): {expected_ops_last_hour}",
                    f"Total logged errors: {errors_last_hour}",
                    "",
                    "Next steps:",
                    "  Run: python P:/.claude/hooks/hook_audit_dashboard.py health",
                    "  Or:  python P:/.claude/hooks/hook_diagnostics.py",
                    "=" * 60,
                ]
                alert_message = "\n".join(alert_lines)
                if "systemMessage" in output:
                    output["systemMessage"] = output["systemMessage"] + "\n\n" + alert_message
                else:
                    output["systemMessage"] = alert_message
        except Exception:
            # Fail open — runtime alert injection should never block processing
            pass

    # Stop JSON validation failure guard: warn if the current session has a
    # recent "JSON validation failed" entry in hook_runner_stderr.jsonl.
    # Advisory only — adds a systemMessage warning, never blocks.
    try:
        _apply_json_validation_guard(output, data, HOOKS_DIR)
    except Exception:
        pass

    # Ensure advisory-only responses never misread as blocks.
    # A Stop hook returning {"systemMessage": "..."} with no continue/decision
    # is treated by Claude Code as a soft block, halting the LLM every turn
    # that has contract telemetry. Explicitly approve when no gate fired.
    if "continue" not in output and "decision" not in output:
        output["continue"] = True

    try:
        _run_external_fact_shadow(data)
    except Exception:
        pass

    print(json.dumps(output))


def process_stop(event_data: dict) -> dict:
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
        return {"ok": e.code == 0, "exit_code": e.code}

    except Exception as e:
        return {"ok": False, "diagnostic": str(e)}

    finally:
        # Restore stdin
        sys.stdin = old_stdin


if __name__ == "__main__":
    main()
