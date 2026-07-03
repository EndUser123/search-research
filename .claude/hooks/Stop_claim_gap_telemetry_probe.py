#!/usr/bin/env python3
"""Stop probe — claim/validation gap telemetry.

Telemetry-only. Never blocks. Emits to the existing
``__lib/agentic_reliability_telemetry`` sink.

Target claim classes (only these — to keep the probe narrow):
  Structural / registration:
    - registered, wired, dispatched, existing pattern, already exists,
      no existing implementation, safe to delete, unused, no callers
  Validation:
    - tests pass / passed / passing, verified, works / working,
      fixed, validated

Honest-uncertainty rule: if the matched line OR a nearby line contains any of
the explicit hedge terms below, suppress the telemetry event entirely.

Evidence rule: if the matched line contains a path-like token OR a command-like
token OR an explicit "I read/grep/ran" with a concrete object, suppress
telemetry entirely (the claim is anchored).

Emit schema (via existing log_event):
    category = "claim_gap_telemetry"
    gate     = "claim_gap_telemetry_probe"
    decision = "telemetry"
    extra    = {
        "claim_type":          "structural" | "validation",
        "marker":              "<matched phrase>",
        "claim_text":          "<matched line>",
        "evidence_seen_nearby": <bool>,
        "hedge_present":       <bool>,
    }

Removal: delete this file + remove the optional registration.
"""

from __future__ import annotations

import re
import sys
from typing import Any

try:
    from __lib.agentic_reliability_telemetry import log_event
except Exception:  # pragma: no cover - telemetry sink must never break the probe
    def log_event(*_args: Any, **_kwargs: Any) -> None:
        return None


# -----------------------------------------------------------------------------
# Markers — phrase → claim_type. Match is case-insensitive substring on a line.
# -----------------------------------------------------------------------------

_STRUCTURAL_MARKERS: tuple[str, ...] = (
    "is registered",
    "is wired",
    "is dispatched",
    "is an existing pattern",
    "is the existing pattern",
    "already exists",
    "no existing implementation",
    "safe to delete",
    "is unused",
    "are unused",
    "no callers",
)

_VALIDATION_MARKERS: tuple[str, ...] = (
    "tests pass",
    "tests passed",
    "tests passing",
    "is verified",
    "are verified",
    "was verified",
    "has been verified",
    "have been verified",
    "is fixed",
    "are fixed",
    "was fixed",
    "has been fixed",
    "have been fixed",
    "is validated",
    "are validated",
    "works",
    "is working",
    "are working",
)

# Patterns that say "this is a claim about state/registration" even when the
# wording varies slightly (e.g. "X is now registered", "X is fully wired").
_STRUCTURAL_REGEX: list[re.Pattern[str]] = [
    re.compile(r"\bis\s+now\s+registered\b", re.IGNORECASE),
    re.compile(r"\bis\s+fully\s+wired\b", re.IGNORECASE),
    re.compile(r"\bis\s+already\s+wired\b", re.IGNORECASE),
    re.compile(r"\bhas\s+been\s+registered\b", re.IGNORECASE),
    re.compile(r"\bhas\s+been\s+wired\b", re.IGNORECASE),
    re.compile(r"\bwas\s+dispatched\b", re.IGNORECASE),
]

# Honest-uncertainty phrases — presence in the same line OR a +/-2 line window
# suppresses the telemetry event. Calibrated by user spec.
_HEDGE_PHRASES: tuple[str, ...] = (
    "not verified",
    "not run",
    "not checked",
    "not tested",
    "i did not check",
    "i haven't verified",
    "i haven't run",
    "haven't verified",
    "haven't run",
    "haven't checked",
    "assumption",
    "assumed",
    "uncertain",
    "unverified",
    "i did not verify",
    "did not verify",
    "did not run",
    "did not check",
    "did not test",
    "i did not run",
    "i did not test",
    "didn't verify",
    "didn't run",
    "didn't check",
    "didn't test",
    "i didn't",
    "i haven't",
    "tbd",
    "todo",
    "n/a",
    "na",
    "not applicable",
)

# Evidence patterns — if any of these appear in the same line OR in a +/-2 line
# window, the claim is anchored and we suppress telemetry. Patterns are
# intentionally broad so we don't over-fire on the false-positive side.
_PATH_LIKE = re.compile(
    r"(?:[A-Za-z]:[\\/][^\s]+|/[\w./-]+|[\w./-]+\.(?:py|js|ts|md|json|yaml|yml|toml|ini|cfg|txt|sh))\b"
)
_COMMAND_LIKE = re.compile(
    r"(?:^|\s)(?:python|pytest|pip|bash|node|npm|cargo|go run)\s+[\w./=-]+",
    re.IGNORECASE,
)
_CITATION = re.compile(
    r"(?:see\s+(?:[A-Za-z]:[\\/]|/)?\S+|line\s+\d+|\bfile\s*:\s*\S+|`[^`]+`|L\d+\b)",
    re.IGNORECASE,
)
_FIRST_PERSON_ACTION = re.compile(
    r"\bI\s+(?:read|grep|ran|tested|fired|verified|checked)\b",
    re.IGNORECASE,
)

_HEDGE_RE = re.compile("|".join(re.escape(p) for p in _HEDGE_PHRASES), re.IGNORECASE)


# -----------------------------------------------------------------------------
# Core scan
# -----------------------------------------------------------------------------

def _window_lines(text: str, idx: int, before: int = 2, after: int = 2) -> str:
    """Return a +/-N-line window around the line at ``idx`` (0-based)."""
    lines = text.splitlines()
    start = max(0, idx - before)
    end = min(len(lines), idx + after + 1)
    return "\n".join(lines[start:end])


def _line_has_evidence(line: str) -> bool:
    """True if the line itself anchors the claim to concrete evidence."""
    if _PATH_LIKE.search(line):
        return True
    if _COMMAND_LIKE.search(line):
        return True
    if _CITATION.search(line):
        return True
    if _FIRST_PERSON_ACTION.search(line):
        return True
    return False


def _scan_marker(text: str, marker: str, claim_type: str) -> list[dict[str, Any]]:
    """Find every line that contains ``marker`` (case-insensitive substring).
    Returns a list of match dicts; emits nothing here — caller decides.
    """
    hits: list[dict[str, Any]] = []
    for i, raw in enumerate(text.splitlines()):
        line = raw.strip()
        if not line:
            continue
        if marker.lower() not in line.lower():
            continue
        window = _window_lines(text, i, before=2, after=2)
        hedge_present = bool(_HEDGE_RE.search(line) or _HEDGE_RE.search(window))
        evidence_seen = _line_has_evidence(line) or _line_has_evidence(window)
        hits.append({
            "claim_type": claim_type,
            "marker": marker,
            "claim_text": line,
            "hedge_present": hedge_present,
            "evidence_seen_nearby": evidence_seen,
        })
    return hits


def _scan_regex(text: str, pattern: re.Pattern[str], claim_type: str) -> list[dict[str, Any]]:
    """Find every line matching ``pattern``; same output shape as _scan_marker."""
    hits: list[dict[str, Any]] = []
    for i, raw in enumerate(text.splitlines()):
        line = raw.strip()
        if not line:
            continue
        if not pattern.search(line):
            continue
        window = _window_lines(text, i, before=2, after=2)
        hedge_present = bool(_HEDGE_RE.search(line) or _HEDGE_RE.search(window))
        evidence_seen = _line_has_evidence(line) or _line_has_evidence(window)
        hits.append({
            "claim_type": claim_type,
            "marker": pattern.pattern,
            "claim_text": line,
            "hedge_present": hedge_present,
            "evidence_seen_nearby": evidence_seen,
        })
    return hits


def find_claim_gaps(text: str) -> list[dict[str, Any]]:
    """Return every structural/validation claim that is BOTH unhedged AND
    evidence-less. Each entry is a dict suitable for telemetry emission.

    Hedged claims and evidence-anchored claims are filtered out — those are
    acceptable and produce no telemetry. This is the *only* function tests
    need to exercise.
    """
    if not text or not text.strip():
        return []
    candidates: list[dict[str, Any]] = []
    for marker in _STRUCTURAL_MARKERS:
        candidates.extend(_scan_marker(text, marker, "structural"))
    for marker in _VALIDATION_MARKERS:
        candidates.extend(_scan_marker(text, marker, "validation"))
    for pat in _STRUCTURAL_REGEX:
        candidates.extend(_scan_regex(text, pat, "structural"))
    # De-dupe (same line matched by both marker + regex once) — keep first.
    seen: set[tuple[str, str]] = set()
    unique: list[dict[str, Any]] = []
    for c in candidates:
        key = (c["claim_text"].lower(), c["marker"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(c)
    # Filter: emit ONLY unhedged AND evidence-less claims.
    return [c for c in unique if not c["hedge_present"] and not c["evidence_seen_nearby"]]


# -----------------------------------------------------------------------------
# Probe entry point
# -----------------------------------------------------------------------------

def run(data: dict[str, Any]) -> dict[str, Any]:
    """Stop-hook entry. Fail-open: returns allow/empty on any error or
    unknown input shape. Never blocks.
    """
    if not isinstance(data, dict):
        return {}  # fail-open

    response_text = str(
        data.get("response")
        or data.get("assistant_response")
        or data.get("last_assistant_message")
        or ""
    )

    session_id = str(data.get("session_id") or data.get("conversation_id") or "") or None
    terminal_id = str(data.get("terminal_id") or data.get("terminalId") or "") or None

    try:
        gaps = find_claim_gaps(response_text)
    except Exception:
        # Any parsing failure: silently emit nothing, return allow.
        return {}

    for gap in gaps:
        try:
            log_event(
                category="claim_gap_telemetry",
                event=gap["marker"][:64],
                gate="claim_gap_telemetry_probe",
                session_id=session_id,
                terminal_id=terminal_id,
                decision="telemetry",
                extra={
                    "claim_type": gap["claim_type"],
                    "marker": gap["marker"],
                    "claim_text": gap["claim_text"],
                    "evidence_seen_nearby": gap["evidence_seen_nearby"],
                    "hedge_present": gap["hedge_present"],
                },
            )
        except Exception:
            # Telemetry sink failures must never block Stop.
            pass

    # Phase 2 promotion: user-visible warn for high-confidence claim gaps.
    # Validation claims ("tests pass", "verified", etc.) without command evidence
    # and without hedge terms are high-confidence enough to produce a visible
    # warning. Structural claims stay telemetry-only for now.
    has_validation_gap = any(g["claim_type"] == "validation" for g in gaps)
    if has_validation_gap:
        return {
            "decision": "warn",
            "systemMessage": (
                "Claim/validation honesty: found unverified validation claims "
                "(e.g. 'tests pass'/'verified' without command evidence). "
                "Include command evidence or explicitly say 'not run'/'not verified'."
            ),
        }
    return {}  # never block, never warn, never alter existing decision


# -----------------------------------------------------------------------------
# Subprocess fallback (mirrors other Stop hooks)
# -----------------------------------------------------------------------------

def main() -> int:
    """Subprocess entry: read Stop payload from stdin, run, return."""
    raw = sys.stdin.read().strip()
    if not raw:
        # No payload → nothing to probe → empty decision.
        return 0
    try:
        import json
        payload = json.loads(raw)
    except Exception:
        # Malformed payload → fail-open.
        return 0
    run(payload if isinstance(payload, dict) else {})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())