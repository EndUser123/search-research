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
    # Analytical markers signal structured reasoning
    markers = (
        "because", "due to", "is caused by", "the reason is",
        "root cause", "evidence", "source:", "[fact]", "[inference]",
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


def _detect_turn_kind(data: dict) -> str:
    """Classify user message as 'control' vs 'query/plan/report'.

    Control turns (short imperative commands) should bypass quality gates
    so that corrections, overrides, and direct instructions are not derailed
    by format/lazy advisory messages.
    """
    user_prompt = data.get("user_prompt") or data.get("prompt") or ""
    if not user_prompt:
        return "control"  # Empty = continuation turn; suppress quality gates

    stripped = user_prompt.strip()
    if not stripped:
        return "control"  # Whitespace-only = continuation turn

    # Short imperative commands are control turns
    # Heuristic: single sentence, starts with imperative verb, no question mark
    words = stripped.split()
    first_word = words[0].lower() if words else ""

    # Control indicators: direct commands, corrections, overrides
    control_starts = (
        "stop", "don't", "do ", "don't ",  # "do X" is two words
        "use ", "use/",
        "instead", "actually", "wait",
        "no,", "yes,", "yeah,",
        "re-read", "re-read",
        "skip", "bypass",
        "override", "ignore",
        "fix ", "check ",
        "run ", "call ", "invoke ",
        "add ", "remove ", "delete ", "create ",
        "write ", "edit ", "read ",
    )

    # Check if first word signals control intent
    if any(stripped.lower().startswith(s) for s in control_starts):
        return "control"

    # Also check for single-word control signals at start
    if first_word in ("stop", "skip", "bypass", "override", "ignore", "actually", "wait"):
        return "control"

    # Planning-style prompts = plan (not control)
    if _PLANNING_PROMPT_RE.search(stripped):
        return "plan"

    # Short responses to status queries = report
    report_indicators = ("[status]", "[changes]", "[results]", "[next]", "status:")
    if any(stripped.lower().startswith(ri) for ri in report_indicators):
        return "report"

    # Question marks = query (only after control patterns are evaluated)
    if "?" in stripped:
        return "query"

    # Default: query
    return "query"


def _detect_turn_mode(data: dict) -> str:
    """Classify turn as plan, report, or analysis mode.

    Uses user prompt (intent) and response (markers) to determine mode.
    Plan/report modes skip epistemic format repair and lazy_fix gates.
    """
    response = data.get("response", "")

    # Report mode: check for explicit status markers
    report_markers = ("[STATUS]", "[CHANGES]", "[RESULTS]", "[NEXT]")
    if sum(1 for m in report_markers if m in response) >= 2:
        return "report"

    # Plan mode: check response markers first
    if "[PLAN]" in response or "[RATIONALE]" in response:
        return "plan"

    # Plan mode: check user prompt for planning intent
    user_prompt = data.get("user_prompt") or data.get("prompt") or ""
    if user_prompt and _PLANNING_PROMPT_RE.search(user_prompt):
        return "plan"

    return "analysis"


def _run_epistemic_contract(data: dict) -> dict | None:
    """Unified epistemic validator — format, citations, causal, comparative."""
    try:
        from epistemic_validator import EpistemicConfig, validate

        response = data.get("response", "")
        if not response:
            return None

        mode = os.environ.get("EPISTEMIC_CONTRACT_MODE", "warn")

        # CLI flag overrides: --epistemic-strict / --epistemic-warn in user prompt
        user_prompt = (
            data.get("user_prompt") or data.get("prompt") or ""
        )
        if "--epistemic-strict" in user_prompt:
            mode = "block"
        elif "--epistemic-warn" in user_prompt:
            mode = "warn"

        cfg = EpistemicConfig(mode=mode)
        verdict = validate(response, cfg)

        # Structured telemetry — one line per validation, all decisions.
        _log_epistemic_telemetry(data, verdict, mode)

        if verdict.decision == "block":
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
            turn_mode = _detect_turn_mode(data)
            if turn_mode in ("plan", "report"):
                return None  # Skip format enforcement for plan/report turns
            # Auto-repair: if ALL issues are format-only, inject a single
            # repair prompt instead of surfacing the raw advisory.
            # Only demand full schema for clearly analytical responses.
            all_format = all(i.type == "format" for i in verdict.issues)
            if all_format and _is_analytical_response(response):
                missing = [
                    i.section for i in verdict.issues
                    if i.type == "format" and i.section != "__GLOBAL__"
                ]
                sections_hint = ", ".join(sorted(set(missing))) if missing else "all"
                repair = (
                    "EPISTEMIC FORMAT REPAIR: Your response is missing required "
                    "section headers. Reformat your previous answer into the "
                    "required schema only. Do not add or remove substantive "
                    "content. Do not include text outside the required section "
                    f"headers. Missing: {sections_hint}."
                )
                return {
                    "decision": "warn",
                    "reason": repair,
                    "systemMessage": repair,
                }
            # Mixed or non-format issues: surface advisory as before.
            parts = [f"EPISTEMIC ADVISORY ({len(verdict.issues)} issue(s)):"]
            for issue in verdict.issues[:3]:
                parts.append(f"  [{issue.section}] {issue.type}: {issue.message}")
            return {
                "decision": "warn",
                "reason": "\n".join(parts),
                "systemMessage": "\n".join(parts),
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
    try:
        import os

        from anti_sycophancy.affirmation_detector import detect_praise_opener
        from anti_sycophancy.lazy_closure_detector import detect_all_lazy_closure
        from anti_sycophancy.overconfidence_detector import detect_all_overconfidence

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
                # Also suppress lazy_fix for plan/report turns
                turn_mode = _detect_turn_mode(data)
                if turn_mode in ("plan", "report"):
                    lazy = [m for m in lazy if m.pattern_type != "lazy_fix"]
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

        # Extract tools using helper from behavior_gates module
        tools_used = _extract_tools_used(tools_output)

        # v2.1: Get working directory for telemetry (use project_root, not cwd)
        project_root = Path(__file__).resolve().parents[1]  # P:\ from P:\.claude\hooks\
        working_dir = data.get("working_dir", project_root)

        # Run gate check (now with working_dir for telemetry)
        is_violation, reason = check_gate3_agreement(response_text, tools_used, working_dir)

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
    try:
        turn_mode = _detect_turn_mode(data)
        if turn_mode in ("plan", "report"):
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


def _run_frameguard_stop(data: dict) -> dict | None:
    """FrameGuard Stop hook - validates systemic frame handling."""
    try:
        import subprocess

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


def _run_referent_coverage(data: dict) -> dict | None:
    """Advisory check: warn if response mentions zero anchor terms from user's message."""
    try:
        tid = (
            data.get("terminal_id")
            or data.get("terminalId")
            or os.environ.get("CLAUDE_TERMINAL_ID")
            or "unknown"
        )
        state_file = HOOKS_DIR / "state" / f"referent_anchors_{tid}.json"
        if not state_file.exists():
            return None

        state = json.loads(state_file.read_text(encoding="utf-8"))

        if state.get("status") == "no_anchors" or not state.get("anchor_terms"):
            return None

        anchor_terms = state.get("anchor_terms", [])
        if len(anchor_terms) < 3:
            return None

        response = (data.get("response") or "").lower()
        if not response:
            return None

        mentioned = [t for t in anchor_terms if t.lower() in response]

        if not mentioned:
            return {
                "decision": "allow",
                "systemMessage": (
                    f"ADVISORY: Response does not mention any of the {len(anchor_terms)} items "
                    f"from the user's structured list. Consider whether the investigation "
                    f"covered the intended entities."
                ),
            }

        return None

    except Exception:
        return None


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
    "dependency_chain_guard": "policy",
    "comparative_claim_guard": "policy",
    "behavior_gates_agreement": "policy",
    "behavior_gates_guidance": "policy",
    "behavior_gates_blacklist": "policy",
    "command_execution_validator": "policy",
    "recommendation_gate": "policy",
    "deletion_verification_guard": "policy",
    "git_diff_reground": "policy",
    "skill_dir_correlation": "policy",
    "cks_correction_anchor": "policy",
    "referent_coverage": "policy",
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
}

IN_PROCESS_GATES = [
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
    ("correction_acknowledgment", _run_correction_acknowledgment),
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
    ("reasoning_enhanced", _run_reasoning_enhanced),
    ("existence_gate", _run_existence_gate),
    ("lazy_workaround_gate", _run_lazy_workaround_gate),
    ("recommendation_gate", _run_recommendation_gate),
    (
        "deletion_verification_guard",
        _run_deletion_verification_guard,
    ),  # NEW 2026-03-24: Deletion verification - checks actual file system state
    ("git_diff_reground", _run_git_diff_reground),
    ("skill_dir_correlation", _run_skill_dir_correlation_gate),
    ("cks_correction_anchor", _run_cks_correction_anchor),
    ("referent_coverage", _run_referent_coverage),
]

# Non-Blocking Side Effects (still subprocess for isolation)
SIDE_EFFECTS = [
    "auto_commit_hook.py",
    "Stop_cks_decision_capture.py",
]


def run_side_effect(hook_name: str, input_data: str) -> None:
    """Run a side-effect hook in subprocess (isolated, fire-and-forget)."""
    try:
        hook_path = HOOKS_DIR / hook_name
        if not hook_path.exists():
            return

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

    _pin_scope_env(data)

    turn_kind = _detect_turn_kind(data)
    quality_mode = os.environ.get("STOP_QUALITY_MODE", "normal")

    system_messages: list[str] = []
    quality_messages: list[str] = []

    # Process Blocking Gates (in-process, fast)
    for name, gate_fn in IN_PROCESS_GATES:
        try:
            res = gate_fn(data)
        except Exception as e:
            print(f"[Stop] gate {name} crashed: {e}", file=sys.stderr)
            continue

        if not res:
            continue

        if res.get("decision") == "block":
            _log_stop_block_event(data, name, res)
            if "blocking_hook" not in res:
                res["blocking_hook"] = f"Stop.py:{name}"
            print(json.dumps(res))
            sys.exit(0)

        if "systemMessage" in res:
            gate_class = GATE_CLASSES.get(name, "policy")
            if gate_class == "policy":
                system_messages.append(res["systemMessage"])
            else:
                quality_messages.append(res["systemMessage"])

    # Quality gate filtering: suppress quality messages on control turns
    # in normal mode (allow corrections and direct instructions through).
    # Strict mode or non-control turns: include quality messages.
    if quality_mode == "strict" or turn_kind != "control":
        system_messages.extend(quality_messages)

    # Process Side Effects (only if not blocked)
    if SIDE_EFFECTS:
        import concurrent.futures

        input_str = json.dumps(data)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(SIDE_EFFECTS)) as executor:
            for hook in SIDE_EFFECTS:
                executor.submit(run_side_effect, hook, input_str)

    output = {}
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
