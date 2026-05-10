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
sys.path.insert(0, str(HOOKS_DIR))
ANTI_SYCOPHANCY_LOG = HOOKS_DIR / "logs" / "anti_sycophancy_violations.jsonl"
SKILL_FIRST_LOG = HOOKS_DIR / "logs" / "skill_first_enforcement.jsonl"
SKILL_FIRST_MODES = {"off", "monitor", "soft_block", "hard_block"}

try:
    from cc_diagnostic_logger import log_hook_invocation as _log_hook_invocation
except Exception:  # pragma: no cover - observability must fail open
    _log_hook_invocation = None

from __lib.turn_mode import (
    classify as _classify_turn_mode,
    is_quality_mode_suppressed,
    is_format_required,
    mode_display_label,
    TurnMode,
)

from __lib.claim_type import _read_claim_type

from Stop_aggregator import aggregate_and_render as _aggregate_and_render
from Stop_artifact_enforcement import run as _run_artifact_enforcement
from Stop_approval_gate import run as _run_approval_gate

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
    line = json.dumps(payload, ensure_ascii=True) + "\n"
    for path in (
        SKILL_FIRST_LOG,
        Path(os.environ.get("TEMP", "/tmp"))
        / "claude_hooks"
        / "logs"
        / "skill_first_enforcement.jsonl",
    ):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(line)
            return
        except OSError:
            continue


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
    line = json.dumps(entry, ensure_ascii=True) + "\n"
    for log_path in _anti_sycophancy_log_candidates():
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as f:
                f.write(line)
            return
        except OSError:
            continue
    # Observability should never break hook execution.
    return


# === IN-PROCESS BLOCKING GATES ===
# Each returns: dict with decision/reason/systemMessage, or None to pass through.


def _run_safety_gate(data: dict) -> dict | None:
    """Stop_safety_gate.py logic - regex-based safety checks."""
    try:
        from Stop_safety_gate import check_forbidden, check_protocol, check_secrets

        response = data.get("response", "")
        if not response:
            return None

        secret = check_secrets(response)
        if secret:
            return {
                "decision": "block",
                "reason": f"SAFETY VIOLATION: {secret}",
                "blocking_hook": "Stop.py:safety_gate",
            }

        forbidden = check_forbidden(response)
        if forbidden:
            return {
                "decision": "block",
                "reason": f"POLICY VIOLATION: {forbidden}",
                "blocking_hook": "Stop.py:safety_gate",
            }

        protocol = check_protocol(response, data)
        if protocol:
            return {
                "decision": "block",
                "reason": f"PROTOCOL VIOLATION: {protocol}",
                "blocking_hook": "Stop.py:safety_gate",
            }

        return None
    except Exception as e:
        # Safety gate fails OPEN
        print(f"[Stop] safety_gate error: {e}", file=sys.stderr)
        return None


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


def _run_intent_artifact_alignment(data: dict) -> dict | None:
    """Intent vs Artifacts alignment gate.

    Detects when the assistant did adjacent work instead of modifying
    the requested targets. Quality gate — suppressed on control/exploration/meta turns.
    """
    from intent_artifact_alignment import check_alignment

    prompt = data.get("user_prompt") or data.get("prompt") or ""
    tool_events = data.get("tool_events", [])
    response = data.get("response", "")
    return check_alignment(prompt, tool_events, response)


def _run_semantic_critic(data: dict) -> dict | None:
    """Semantic quality gate for diagnostic/analytical responses.

    Evaluates whether analytical responses adequately address the diagnostic question.
    Uses Haiku for semantic evaluation. Quality gate — suppressed on control/exploration.
    """
    from Stop_semantic_critic import run as _semantic_critic_run

    result = _semantic_critic_run(data)
    # Surface profile in result dict so Stop can log it via telemetry
    if result is not None:
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
            result = dict(result)
            result["_critic_profile"] = profile
        except Exception:
            pass
    return result


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
        from epistemic_validator import EpistemicConfig, validate

        response = data.get("response", "")
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

        # Control and exploration: skip unless --epistemic-strict overrides.
        if not strict_override and is_quality_mode_suppressed(turn_mode, quality_mode):
            return None

        # Determine validator mode: block vs warn
        mode = os.environ.get("EPISTEMIC_CONTRACT_MODE", "warn")
        if strict_override:
            mode = "block"
        elif "--epistemic-warn" in user_prompt:
            mode = "warn"

        cfg = EpistemicConfig(mode=mode)
        verdict = validate(response, cfg)

        # Structured telemetry — one line per validation, all decisions.
        _log_epistemic_telemetry(data, verdict, mode)

        if verdict.decision == "block":
            # Plan/execution-report: suppress blocks on non-critical epistemic
            # violations. These modes produce [PLAN] scaffolding that may not
            # match the analytical 4-section schema.
            if turn_mode in ("plan", "execution-report"):
                return None
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
        if verdict.decision == "warn" and verdict.issues:
            # Plan/execution-report: suppress format repair on warns.
            if turn_mode in ("plan", "execution-report"):
                return None

            # ADVOCATE_PROTOCOL dedup: skip format-only repair when challenge
            # was already injected upstream.
            all_format = all(i.type == "format" for i in verdict.issues)
            if all_format and _challenge_marker_active():
                return None

            # Auto-repair: format-only issues on analytical responses.
            # NON-CRITICAL — log only, no user-visible injection by default.
            if all_format and _is_analytical_response(response):
                missing = [
                    i.section for i in verdict.issues
                    if i.type == "format" and i.section != "__GLOBAL__"
                ]
                sections_hint = ", ".join(sorted(set(missing))) if missing else "all"
                _log_non_critical_advisory(data, "format_repair", verdict.issues)
                # On-demand verbose: surface full repair text for this turn.
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
                    "systemMessage": None,  # silent — logged to diagnostics
                }
            # Mixed or non-format issues: log only, no inline advisory.
            # These are coaching-level (citations missing, minor causal language).
            _log_non_critical_advisory(data, "mixed_advisory", verdict.issues)
            # On-demand verbose: surface full advisory text for this turn.
            if verbose_override:
                parts = [f"EPISTEMIC ADVISORY ({len(verdict.issues)} issue(s)):"]
                for issue in verdict.issues[:3]:
                    parts.append(f"  [{issue.section}] {issue.type}: {issue.message}")
                return {"decision": "warn", "reason": "\n".join(parts), "systemMessage": "\n".join(parts)}
            return {
                "decision": "warn",
                "reason": "epistemic_advisory_logged",
                "systemMessage": None,  # silent — logged to diagnostics
            }
        return None
    except Exception as e:
        print(f"[Stop] epistemic_contract error: {e}", file=sys.stderr)
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
        print(f"[Stop] behavior_audit telemetry error: {e}", file=sys.stderr)
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
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _log_epistemic_telemetry(data: dict, verdict, mode: str) -> None:
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
            "session_id": data.get("session_id", ""),
            "terminal_id": data.get("terminal_id", ""),
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


def _log_non_critical_advisory(data: dict, advisory_type: str, issues) -> None:
    """Append non-critical advisory detail to diagnostics JSONL.

    These advisories (format-only, mixed/coaching) are logged for
    observability but NOT injected into the user-visible response.
    Critical blocks (epistemic violations with unsupported_fact, causal,
    comparative) still surface inline and are already covered by
    _log_epistemic_telemetry.
    """
    try:
        log_path = HOOKS_DIR / "logs" / "diagnostics" / "epistemic_advisories.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        issue_types = sorted({i.type for i in issues})
        entry = {
            "timestamp": time.time(),
            "advisory_type": advisory_type,  # "format_repair" | "mixed_advisory"
            "issue_count": len(issues),
            "issue_types": issue_types,
            "sections": sorted({i.section for i in issues if i.section != "__GLOBAL__"}),
            "messages": [i.message for i in issues[:5]],
            "session_id": data.get("session_id", ""),
            "terminal_id": data.get("terminal_id", ""),
            "response_length": len(data.get("response", "")),
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        pass


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
        print(f"[Stop] cross_validator error: {e}", file=sys.stderr)
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
            }
        )
        if not result:
            return None
        if result.get("block") is True or result.get("allow") is False:
            return {
                "decision": "block",
                "reason": result.get("reason", "Unverified stance detected."),
                "blocking_hook": result.get("blocking_hook", "Stop.py:unverified_stance"),
            }
        return None
    except Exception as e:
        print(f"[Stop] unverified_stance error: {e}", file=sys.stderr)
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
        print(f"[Stop] correction_acknowledgment error: {e}", file=sys.stderr)
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
        print(f"[Stop] cited_content_guard error: {e}", file=sys.stderr)
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
        print(f"[Stop] dependency_chain_guard error: {e}", file=sys.stderr)
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
        print(f"[Stop] comparative_claim_guard error: {e}", file=sys.stderr)
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
        print(f"[Stop] narrative_intent error: {e}", file=sys.stderr)
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
            with open(_pp, "a", encoding="utf-8") as _f:
                _f.write(json.dumps({
                    "ts": _t.time(),
                    "lam_len": len(response),
                    "lam_words": len(response.split()) if response else 0,
                    "first_60": response[:60] if response else "",
                    "last_60": response[-60:] if response else "",
                }) + "\n")
        except Exception:
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
            tool_events = data.get("tool_events", [])
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
                # Also suppress lazy_fix and sycophancy_capitulation for plan/report/exploration turns
                _turn = _classify_turn_mode(data)
                if _turn in ("plan", "execution-report", "exploration"):
                    lazy = [m for m in lazy if m.pattern_type not in ("lazy_fix", "sycophancy_capitulation")]
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
        print(f"[Stop] anti_sycophancy_quality error: {e}", file=sys.stderr)
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
        print(f"[Stop] command_execution_validator error: {e}", file=sys.stderr)
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
        print(f"[Stop] behavior_gates_agreement error: {e}", file=sys.stderr)
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
        print(f"[Stop] behavior_gates_guidance error: {e}", file=sys.stderr)
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
        print(f"[Stop] behavior_gates_blacklist error: {e}", file=sys.stderr)
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
        print(f"[Stop] advisory error: {e}", file=sys.stderr)
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
    # NOTE: UserPromptSubmit writes terminal-scoped files (compact-proof).
    # Format: pending_command_intent_{terminal_id}.json
    # Legacy format with session_id is cleaned up by skill_enforcer.py.
    intent_file = None
    for base_dir in (
        HOOKS_DIR / "state",
        Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state",
    ):
        # Primary: terminal-scoped format (what UserPromptSubmit actually writes)
        candidate = base_dir / f"pending_command_intent_{safe_terminal}.json"
        if candidate.exists():
            intent_file = candidate
            break

    # Fallback: legacy session-scoped format (for backwards compatibility)
    if not intent_file:
        for base_dir in (
            HOOKS_DIR / "state",
            Path(os.environ.get("TEMP", "/tmp")) / "claude_hooks" / "state",
        ):
            candidate = base_dir / f"pending_command_intent_{safe_session}.json"
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

        return {
            "decision": "block",
            "reason": (
                f"[E_SKILL_FIRST_INLINE_BYPASS]\n"
                f"SLASH COMMAND IGNORED\n\n"
                f"You typed /{skill_name} but responded with prose without calling the Skill tool.\n\n"
                f"You MUST:\n"
                f'1. Call Skill(skill="{skill_name}") to load the skill\n'
                f"2. Follow the skill's workflow instructions\n"
                f"3. READ THE LAST 10-20 MESSAGES of conversation to infer context before asking clarifying questions\n\n"
                f"Do NOT read the SKILL.md file manually or improvise your own version.\n"
                f"Do NOT bypass this by returning inline analysis text without Skill(...)."
            ),
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
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
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
        print(f"[Stop] skill_guard import skipped (non-blocking): {e}", file=sys.stderr)
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
        print(f"[Stop] reflect_integration error: {e}", file=sys.stderr)
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
        if _turn in ("plan", "execution-report", "meta"):
            return None
        import Stop_lazy_workaround_gate

        response = data.get("response", "")
        if not response:
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
        print(f"[Stop] recommendation_gate error: {e}", file=sys.stderr)
        return None


def _run_reasoning_quality_gate(data: dict) -> dict | None:
    """Run automatic reasoning quality gate on responses using reasoning package."""
    try:
        hook_path = HOOKS_DIR / "Stop_reasoning_quality_gate.py"
        if not hook_path.exists():
            return None

        response = data.get("response", "")
        if not response or len(response) < 200:
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
        print(f"[Stop] reasoning_quality_gate error: {e}", file=sys.stderr)
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
        print(f"[Stop] reasoning_enhanced error: {e}", file=sys.stderr)
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
            print(f"[Stop] skill_guard import skipped (non-blocking): {e}", file=sys.stderr)
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
    try:
        from Stop_git_diff_reground import check_git_diff_reground
        return check_git_diff_reground(data)
    except Exception as e:
        # Fails open
        print(f"[Stop] git_diff_reground error: {e}", file=sys.stderr)
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


# _run_referent_coverage removed 2026-05-10.
# Reason: Lexical anchor-matching is not a reliable proxy for task completion.
# False positives from stale anchors across topic shifts outweigh the signal.
# The PreToolUse scope gate (PreToolUse_referent_scope_gate.py) still blocks
# off-topic tool calls during active investigations using the same anchors.
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
# ---------------------------------------------------------------------------


def _run_task_contract_fit_gate(data: dict) -> dict | None:
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
        from __lib.task_contract import load_contract, clear_contract

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

        if not response:
            _log_task_contract_telemetry(terminal_id, "silent", {
                "reason": "empty_response",
            })
            return None

        # Only check responses that look like completion attempts.
        if turn_mode in ("control", "exploration", "plan", "meta"):
            _log_task_contract_telemetry(terminal_id, "silent", {
                "reason": f"turn_mode={turn_mode}",
            })
            return None

        # Heuristic: skip very short responses (not a final report).
        # At least ~300 chars suggests a substantive answer.
        if len(response) < 300:
            _log_task_contract_telemetry(terminal_id, "silent", {
                "reason": "response_too_short",
                "response_len": len(response),
            })
            return None

        required = contract.get("required_outputs", [])
        if not required:
            return None

        missing = _check_missing_outputs(response, required)
        if not missing:
            # All required outputs present — contract satisfied, clear it.
            clear_contract(terminal_id)
            _log_task_contract_telemetry(terminal_id, "auto_clear", {
                "required": required,
            })
            return None

        # Telemetry: block
        _log_task_contract_telemetry(terminal_id, "block", {
            "required": required,
            "missing": missing,
        })

        # Build a specific, actionable block message.
        required_str = ", ".join(required)
        missing_str = ", ".join(missing)
        return {
            "decision": "block",
            "reason": (
                f"TASK CONTRACT INCOMPLETE: required outputs [{required_str}], "
                f"missing: [{missing_str}]."
            ),
            "systemMessage": (
                f"The user's task contract requires: {required_str}. "
                f"Your answer is missing: {missing_str}. "
                f"Extend your answer to include those explicitly before responding."
            ),
            "blocking_hook": "Stop.py:task_contract_fit",
        }
    except Exception as e:
        print(f"[Stop] task_contract_fit error: {e}", file=sys.stderr)
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
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=True) + "\n")
    except Exception:
        pass  # Observability must never change hook behavior


# Deterministic pattern checks for required output types.
# v1 uses simple keyword/heading detection — no external calls.

_OUTPUT_PATTERNS: dict[str, list[str]] = {
    "root_cause": [
        r"(?i)\broot\s*cause\b",
        r"(?i)\bcaused\s+by\b",
        r"(?i)\bthe\s+(?:underlying|actual|real)\s+(?:issue|problem|cause|bug)\b",
        r"(?i)\bwhat\s+(?:went\s+wrong|caused|broke)\b",
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
    "task_contract_fit": "quality",
    "phase0_depends_on_skills": "quality",
    "acknowledgment_loop": "policy",
    "repetition_blocker": "policy",
    "fake_done": "policy",
    "meta_analysis_trap": "quality",
    "approval_gate": "policy",
}

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
    ("safety_gate", _run_safety_gate),
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
    ("behavior_gates_agreement", _run_behavior_gates_agreement),
    ("behavior_gates_guidance", _run_behavior_gates_guidance),
    ("behavior_gates_blacklist", _run_behavior_gates_blacklist),
    ("narrative_intent", _run_narrative_intent),
    ("anti_sycophancy_quality", _run_anti_sycophancy_quality),
    ("command_execution_validator", _run_command_execution_validator),
    ("advisory", _run_advisory),
    ("reflect_integration", _run_reflect_integration),
    ("reasoning_quality_gate", _run_reasoning_quality_gate),
    ("lazy_workaround_gate", _run_lazy_workaround_gate),
    ("recommendation_gate", _run_recommendation_gate),
    ("intent_artifact_alignment", _run_intent_artifact_alignment),
    ("semantic_critic", _run_semantic_critic),
    ("task_contract_fit", _run_task_contract_fit_gate),
    (
        "deletion_verification_guard",
        _run_deletion_verification_guard,
    ),  # NEW 2026-03-24: Deletion verification - checks actual file system state
    (
        "artifact_enforcement",
        _run_artifact_enforcement,
    ),  # NEW 2026-05-08: Artifact enforcement for mechanism claims
    ("approval_gate", _run_approval_gate),  # NEW 2026-05-10: Implementation approval gate
    ("git_diff_reground", _run_git_diff_reground),
    ("skill_dir_correlation", _run_skill_dir_correlation_gate),
    ("cks_correction_anchor", _run_cks_correction_anchor),
    ("phase0_depends_on_skills", _run_phase0_depends_on_skills),
    ("tool_sanity", _run_tool_sanity_check),
    ("acknowledgment_loop", _run_acknowledgment_loop),
    ("repetition_blocker", _run_repetition_blocker),
    ("fake_done", _run_fake_done_detector),
    ("meta_analysis_trap", _run_meta_analysis_trap),
]

# Non-Blocking Side Effects (still subprocess for isolation)
SIDE_EFFECTS = [
    "auto_commit_hook.py",
    "Stop_cks_decision_capture.py",
    "Stop_cleanup_verifier.py",
]


def run_side_effect(hook_name: str, input_data: str) -> None:
    """Run a side-effect hook in subprocess (isolated, fire-and-forget)."""
    try:
        hook_path = HOOKS_DIR / hook_name
        if not hook_path.exists():
            return

        # Skip auto_commit_hook if input is invalid (missing prompt/response).
        # The hook does git operations that can hang on malformed session context.
        if "auto_commit" in hook_name:
            try:
                parsed = json.loads(input_data)
                if not parsed.get("prompt") or not parsed.get("response"):
                    return  # Invalid input — skip this side effect
            except json.JSONDecodeError:
                return  # Can't parse input — skip

        # Auto-commit needs more time for multi-repo git operations
        timeout = 30.0 if "auto_commit" in hook_name else 5.0
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
                print(f"[Stop side-effect error] {hook_name}: {stderr}", file=sys.stderr)
    except Exception as e:
        print(f"[Stop side-effect exception] {hook_name}: {e}", file=sys.stderr)


CRITICAL_STOP_GATES = frozenset((
    "destructive_cleanup_detector",  # advisory-only detector, but must not silently fail
))

# Module-level critical gate failure flag for this turn
_critical_gate_failed_this_turn: bool = False


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
        print(f"[Stop] gate {name} crashed: {e}", file=sys.stderr)
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


def _process_gate_result(
    res: dict, name: str, system_messages: list[str],
    quality_messages: list[str], data: dict,
    turn_mode: str, quality_mode: str,
) -> bool:
    """Route a gate result: block exits immediately, otherwise route systemMessage.

    Quality gate blocks are suppressed on control/exploration turns (normal mode)
    or control turns only (strict mode), matching the systemMessage suppression.
    Policy gate blocks always fire regardless of turn mode.

    Returns True if the turn was blocked (caller should exit), False to continue.
    """
    if not res:
        return False
    if res.get("decision") == "block":
        gate_class = GATE_CLASSES.get(name, "policy")
        if gate_class == "quality" and is_quality_mode_suppressed(turn_mode, quality_mode):
            return False
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


def _merge_quality_messages(
    system_messages: list[str], quality_messages: list[str],
    turn_mode: str, quality_mode: str,
) -> None:
    """Append quality messages to system_messages only when not suppressed."""
    if not is_quality_mode_suppressed(turn_mode, quality_mode):
        system_messages.extend(quality_messages)


def get_hook_health_summary(session_id: str | None = None) -> dict | None:
    """Get hook health summary for display.

    Args:
        session_id: Optional session ID for alert deduplication

    Returns:
        Dict with health summary or None if no issues
    """
    hooks_dir = HOOKS_DIR
    health_file = hooks_dir / "logs" / "diagnostics" / "hook_health.json"
    cc_errors_log = hooks_dir / "logs" / "diagnostics" / "cc_errors.jsonl"

    # Check health file for current failures
    failing_hooks = 0
    failures = []
    if health_file.exists():
        try:
            health_data = json.loads(health_file.read_text())
            if health_data.get("status") == "fail":
                failures = health_data.get("failures", [])
                failing_hooks = len(failures)
        except Exception:
            pass

    # Check cc_errors for last hour error count
    errors_last_hour = 0
    if cc_errors_log.exists():
        try:
            one_hour_ago = time.time() - 3600  # 1 hour ago

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
                            # Parse ISO timestamp
                            from datetime import datetime

                            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            ts_epoch = ts.timestamp()
                            if ts_epoch >= one_hour_ago:
                                errors_last_hour += 1
                        except Exception:
                            continue
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    # Return summary if there are issues
    if failing_hooks > 0 or errors_last_hour > 10:
        summary = {
            "failing_hooks": failing_hooks,
            "errors_last_hour": errors_last_hour,
            "alert": True,
            "failures": failures[:3],  # Show first 3 failures
        }

        # Alert deduplication: check if this alert was already shown in session
        if session_id:
            alert_signature = _compute_alert_signature(summary)
            if _was_alert_already_shown(session_id, alert_signature):
                # Alert already shown, suppress it
                return None
            # Mark this alert as shown
            _mark_alert_shown(session_id, alert_signature)

        return summary

    return None


def _compute_alert_signature(summary: dict) -> str:
    """Compute a signature for alert deduplication.

    Args:
        summary: Health summary dict

    Returns:
        Signature string for this alert
    """
    # Signature based on failing hooks and error count
    # Two alerts are identical if they have the same failing hooks and error count
    failures = summary.get("failures", [])
    failures_str = ",".join(sorted(failures))
    errors = summary.get("errors_last_hour", 0)
    return f"{failures_str}|{errors}"


def _get_alert_state_path(session_id: str) -> Path:
    """Get state file path for alert deduplication.

    Args:
        session_id: Session identifier

    Returns:
        Path to state file
    """
    state_dir = HOOKS_DIR / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir / f"shown_health_alerts_{session_id}.json"


def _was_alert_already_shown(session_id: str, alert_signature: str) -> bool:
    """Check if alert was already shown in this session.

    Args:
        session_id: Session identifier
        alert_signature: Alert signature to check

    Returns:
        True if alert was already shown
    """
    state_file = _get_alert_state_path(session_id)
    if not state_file.exists():
        return False

    try:
        state_data = json.loads(state_file.read_text())
        shown_alerts = state_data.get("shown_alerts", [])
        return alert_signature in shown_alerts
    except Exception:
        return False


def _mark_alert_shown(session_id: str, alert_signature: str) -> None:
    """Mark an alert as shown in this session.

    Args:
        session_id: Session identifier
        alert_signature: Alert signature to mark
    """
    state_file = _get_alert_state_path(session_id)
    try:
        if state_file.exists():
            state_data = json.loads(state_file.read_text())
        else:
            state_data = {"shown_alerts": []}

        shown_alerts = state_data.get("shown_alerts", [])
        if alert_signature not in shown_alerts:
            shown_alerts.append(alert_signature)
            state_data["shown_alerts"] = shown_alerts
            state_file.write_text(json.dumps(state_data, indent=2))
    except Exception:
        # Fail silently - state tracking is optional
        pass


def main():
    global _critical_gate_failed_this_turn
    _critical_gate_failed_this_turn = False  # reset per turn
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

    _pin_scope_env(data)

    # Classify turn mode once — used for quality gate suppression
    turn_mode = _classify_turn_mode(data)
    quality_mode = os.environ.get("STOP_QUALITY_MODE", "normal")

    system_messages: list[str] = []
    quality_messages: list[str] = []
    # Raw messages for aggregation: (hook_name, severity, message)
    _raw_messages: list[tuple[str, str, str]] = []

    # Post-violation gates: these need all_violations populated from earlier gate results.
    # acknowledgment_loop and repetition_blocker need to know what violations earlier
    # gates detected in this turn. They run late in the list, so by the time they execute,
    # _raw_messages has results from all preceding gates.
    _POST_VIOLATION_GATES = frozenset((
        "acknowledgment_loop", "repetition_blocker",
    ))

    # Run all in-process gates
    for name, gate_fn in IN_PROCESS_GATES:
        # Enrich data for post-violation gates with current turn's detected issues
        if name in _POST_VIOLATION_GATES and "all_violations" not in data:
            data["all_violations"] = [
                {"type": hook_name, "message": msg}
                for hook_name, severity, msg in _raw_messages
            ]
        res = _run_gate_safe(name, gate_fn, data)
        blocked = _process_gate_result(
            res, name, system_messages, quality_messages, data,
            turn_mode, quality_mode,
        )

        # --- Gate telemetry ---
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
            log_gate_event(
                gate_name=name,
                classification=gate_class,
                profile=critic_profile,
                decision=decision,
                session_id=data.get("session_id") or data.get("sessionId"),
                terminal_id=data.get("terminal_id"),
                extra=extra,
            )
        except Exception:
            pass
        # --- End telemetry ---

        if blocked:
            sys.exit(0)
        # Collect raw messages for aggregation: (hook_name, severity, message)
        # systemMessage gates emit warnings by default
        if res and res.get("systemMessage"):
            _raw_messages.append((name, "warn", res["systemMessage"]))

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

    # Hook Health Summary (NEW)
    session_id = data.get("session_id") or data.get("sessionId") or data.get("CLAUDE_SESSION_ID")
    health_summary = get_hook_health_summary(session_id=session_id)
    if health_summary and health_summary.get("alert"):
        alert_lines = [
            "=" * 60,
            "⚠️  HOOK HEALTH ALERT",
            "=" * 60,
            f"Failing hooks: {health_summary['failing_hooks']}",
            f"Errors in last hour: {health_summary['errors_last_hour']}",
        ]

        if health_summary.get("failures"):
            alert_lines.append("\nFailing hooks:")
            for failure in health_summary["failures"]:
                alert_lines.append(f"  • {failure}")

        alert_lines.extend(
            [
                "\nNext steps:",
                "  Run: python P:/.claude/hooks/hook_audit_dashboard.py health",
                "  Or:  python P:/.claude/hooks/hook_diagnostics.py",
                "=" * 60,
            ]
        )

        alert_message = "\n".join(alert_lines)

        # Append to existing system message or create new one
        if "systemMessage" in output:
            output["systemMessage"] = output["systemMessage"] + "\n\n" + alert_message
        else:
            output["systemMessage"] = alert_message

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
