"""Validate evidence packets and verifier output.

Two responsibilities, kept strictly separate:

1. ``validate_packet(packet_dict)`` — structural / range / reconciliation
   checks on an EvidencePacket dict (the deterministic preprocessor's
   output). Returns a list of errors; empty == valid.
2. ``validate_verifier_output(output_dict)`` — checks a verifier subagent's
   structured response against the /check contract (PASS/FAIL verdict and
   allowed issue severities). Used by the /check orchestrator after
   subagents return.

Both validators are **non-raising**: they collect errors and return them so
the caller (preprocessor, orchestrator, or test) can decide whether to
abort, warn, or proceed. A validator that raised would let malformed input
crash the pipeline silently.
"""

from __future__ import annotations

from typing import Any

from event_model import (
    CHECK_ISSUE_SEVERITIES,
    CHECK_VERDICTS,
    PACKET_SCHEMA_VERSION,
    SourceStatus,
)
from detectors import DETECTOR_NAMES

__all__ = [
    "ValidationError",
    "PacketErrors",
    "validate_packet",
    "validate_verifier_output",
    "assert_valid_packet",
]

#: Known packet schema versions this validator accepts. Bumping
#: PACKET_SCHEMA_VERSION requires adding the new version here AND ensuring
#: every check still applies.
_KNOWN_SCHEMA_VERSIONS: frozenset[str] = frozenset({PACKET_SCHEMA_VERSION})

_REQUIRED_PACKET_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "producer",
        "produced_at",
        "source",
        "parse_stats",
        "signal_counts",
        "signals",
        "warnings",
    }
)

_REQUIRED_SOURCE_KEYS: frozenset[str] = frozenset(
    {"path", "status", "session_id", "line_count", "has_timestamps"}
)

_REQUIRED_SIGNAL_FIELDS: frozenset[str] = frozenset(
    {"kind", "event_indices", "summary", "detail", "confidence"}
)

_ALLOWED_CONFIDENCE: frozenset[str] = frozenset({"OBSERVED", "INFERRED"})

#: Required fields for a verifier-subagent issue block.
_REQUIRED_ISSUE_FIELDS: frozenset[str] = frozenset(
    {"severity", "description", "evidence", "suggestion"}
)


class ValidationError(Exception):
    """Raised by ``assert_valid_packet`` when validation fails.

    The non-raising validators return error lists; this is only for callers
    that want a hard-stop (e.g. the preprocessor asserting its own output).
    """


class PacketErrors:
    """Container for accumulated validation errors with severity buckets.

    ``errors`` block acceptance; ``warnings`` are advisory. A packet with
    zero errors is structurally valid; warnings do not change that.
    """

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, list[str]]:
        return {"errors": list(self.errors), "warnings": list(self.warnings)}

    def __repr__(self) -> str:
        return (
            f"PacketErrors(ok={self.ok}, "
            f"errors={len(self.errors)}, "
            f"warnings={len(self.warnings)})"
        )


# ---------------------------------------------------------------------------
# Packet validation
# ---------------------------------------------------------------------------


def validate_packet(packet: dict[str, Any]) -> PacketErrors:
    """Validate an EvidencePacket dict. Returns accumulated errors.

    Checks:
      1. Required top-level keys present.
      2. Schema version is known.
      3. Source block has required keys and an allowed status value.
      4. parse_stats block reconciles arithmetically.
      5. signal_counts reconcile with len(signals[kind]) for every detector.
      6. Every detector kind is present in ``signals``.
      7. Every signal has required fields, non-empty event_indices, and
         indices in range [0, parse_stats.parsed_events).
      8. Every signal's ``confidence`` is in the allowed set.
      9. Every signal's ``kind`` matches its bucket key (defensive).
    """
    errs = PacketErrors()

    # 1. Top-level keys
    if not isinstance(packet, dict):
        errs.error("packet is not a dict")
        return errs
    missing = _REQUIRED_PACKET_KEYS - set(packet.keys())
    if missing:
        errs.error(f"missing top-level keys: {sorted(missing)}")
    extra = set(packet.keys()) - _REQUIRED_PACKET_KEYS
    if extra:
        errs.warn(f"unexpected top-level keys (ignored): {sorted(extra)}")

    # 2. Schema version
    sv = packet.get("schema_version")
    if not isinstance(sv, str):
        errs.error(f"schema_version is not a string: {sv!r}")
    elif sv not in _KNOWN_SCHEMA_VERSIONS:
        errs.error(
            f"unknown schema_version {sv!r}; known: {sorted(_KNOWN_SCHEMA_VERSIONS)}"
        )

    # 3. Source block
    source = packet.get("source")
    if not isinstance(source, dict):
        errs.error("source is not a dict")
    else:
        s_missing = _REQUIRED_SOURCE_KEYS - set(source.keys())
        if s_missing:
            errs.error(f"source missing keys: {sorted(s_missing)}")
        status = source.get("status")
        allowed_status = {s.value for s in SourceStatus}
        if status not in allowed_status:
            errs.error(f"source.status {status!r} not in {sorted(allowed_status)}")
        lc = source.get("line_count")
        if not isinstance(lc, int) or lc < 0:
            errs.error(f"source.line_count not a non-negative int: {lc!r}")
        if not isinstance(source.get("has_timestamps"), bool):
            errs.error("source.has_timestamps is not a bool")

    # 4. parse_stats reconciliation
    stats = packet.get("parse_stats")
    if not isinstance(stats, dict):
        errs.error("parse_stats is not a dict")
    else:
        parsed = stats.get("parsed_events", 0)
        total = stats.get("total_lines", 0)
        blank = stats.get("skipped_blank", 0)
        malformed = stats.get("skipped_malformed", 0)
        if not all(isinstance(x, int) for x in (parsed, total, blank, malformed)):
            errs.error("parse_stats count fields must be ints")
        elif parsed + malformed != total - blank:
            errs.error(
                f"parse_stats does not reconcile: "
                f"parsed({parsed}) + malformed({malformed}) "
                f"!= total({total}) - blank({blank})"
            )

    # 5 + 6. signal_counts and detector coverage
    counts = packet.get("signal_counts")
    signals = packet.get("signals")
    if not isinstance(counts, dict):
        errs.error("signal_counts is not a dict")
    if not isinstance(signals, dict):
        errs.error("signals is not a dict")
    else:
        parsed_events = stats.get("parsed_events", 0) if isinstance(stats, dict) else 0
        for name in DETECTOR_NAMES:
            if name not in signals:
                errs.error(f"signals missing detector bucket: {name}")
                continue
            bucket = signals[name]
            if not isinstance(bucket, list):
                errs.error(f"signals[{name!r}] is not a list")
                continue
            # Count reconciliation
            if isinstance(counts, dict) and counts.get(name) != len(bucket):
                errs.error(
                    f"signal_counts[{name!r}]={counts.get(name)!r} != "
                    f"len(signals[{name!r}])={len(bucket)}"
                )
            # 7 + 8. Per-signal field checks
            for i, sig in enumerate(bucket):
                if not isinstance(sig, dict):
                    errs.error(f"signals[{name}][{i}] is not a dict")
                    continue
                sig_missing = _REQUIRED_SIGNAL_FIELDS - set(sig.keys())
                if sig_missing:
                    errs.error(
                        f"signals[{name}][{i}] missing fields: {sorted(sig_missing)}"
                    )
                # kind matches bucket
                if sig.get("kind") != name:
                    errs.error(
                        f"signals[{name}][{i}].kind={sig.get('kind')!r} "
                        f"!= bucket {name!r}"
                    )
                # event_indices non-empty and in range
                ei = sig.get("event_indices")
                if not isinstance(ei, list) or not ei:
                    errs.error(
                        f"signals[{name}][{i}].event_indices must be a non-empty list"
                    )
                elif not all(isinstance(x, int) and x >= 0 for x in ei):
                    errs.error(
                        f"signals[{name}][{i}].event_indices "
                        f"has non-int/negative: {ei!r}"
                    )
                elif parsed_events and any(x >= parsed_events for x in ei):
                    errs.error(
                        f"signals[{name}][{i}].event_indices out of range "
                        f"(max {max(ei)} >= parsed_events {parsed_events})"
                    )
                # confidence value
                conf = sig.get("confidence")
                if conf not in _ALLOWED_CONFIDENCE:
                    errs.error(
                        f"signals[{name}][{i}].confidence={conf!r} not in "
                        f"{sorted(_ALLOWED_CONFIDENCE)}"
                    )
        # Unknown detector buckets
        unknown = set(signals.keys()) - set(DETECTOR_NAMES)
        if unknown:
            errs.warn(
                f"signals has unknown detector buckets (ignored): {sorted(unknown)}"
            )

    return errs


def assert_valid_packet(packet: dict[str, Any]) -> None:
    """Validate and raise ``ValidationError`` if any errors.

    Used by the preprocessor to assert its own output before writing.
    """
    errs = validate_packet(packet)
    if not errs.ok:
        raise ValidationError(
            f"packet validation failed with {len(errs.errors)} error(s):\n  - "
            + "\n  - ".join(errs.errors)
        )


# ---------------------------------------------------------------------------
# Verifier-output validation
# ---------------------------------------------------------------------------


def validate_verifier_output(output: dict[str, Any]) -> PacketErrors:
    """Validate a verifier subagent's structured response.

    /check verifier subagents are prompted to emit:
      * ``verdict`` ∈ {"PASS", "FAIL"}
      * ``checklist``, ``action_trace``, ``evaluation``, ``issues`` (sections)
      * each issue has ``severity`` ∈ CHECK_ISSUE_SEVERITIES plus
        ``description``, ``evidence``, ``suggestion``.

    Checks (advisory unless noted):
      * ``verdict`` present and in CHECK_VERDICTS — ERROR if not.
      * FAIL verdict with zero issues — ERROR (FAIL must justify itself).
      * PASS verdict with issues — WARN (issues contradict PASS).
      * Each issue has required fields — ERROR per missing field.
      * Each issue.severity ∈ CHECK_ISSUE_SEVERITIES — ERROR if not.
      * Issue severities marked "bug"/"regression" on a PASS verdict — ERROR.

    Returns PacketErrors so the orchestrator can decide whether to accept,
    re-prompt the subagent, or flag for human review.
    """
    errs = PacketErrors()
    if not isinstance(output, dict):
        errs.error("verifier output is not a dict")
        return errs

    verdict = output.get("verdict")
    if verdict not in CHECK_VERDICTS:
        errs.error(f"verdict {verdict!r} not in {list(CHECK_VERDICTS)}")

    issues = output.get("issues", [])
    if not isinstance(issues, list):
        errs.error("verifier output 'issues' is not a list")
        issues = []

    if verdict == "FAIL" and not issues:
        errs.error("FAIL verdict with zero issues — FAIL must justify itself")

    if verdict == "PASS" and issues:
        errs.warn("PASS verdict with issues — contradicts the PASS")

    for i, issue in enumerate(issues):
        if not isinstance(issue, dict):
            errs.error(f"issues[{i}] is not a dict")
            continue
        missing = _REQUIRED_ISSUE_FIELDS - set(issue.keys())
        if missing:
            errs.error(f"issues[{i}] missing fields: {sorted(missing)}")
        sev = issue.get("severity")
        if sev not in CHECK_ISSUE_SEVERITIES:
            errs.error(
                f"issues[{i}].severity={sev!r} not in {list(CHECK_ISSUE_SEVERITIES)}"
            )
        # PASS + bug/regression is contradictory
        if verdict == "PASS" and sev in {"bug", "regression"}:
            errs.error(f"issues[{i}].severity={sev!r} contradicts PASS verdict")

    return errs
