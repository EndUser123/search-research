"""Deterministic parser for Grok ``chat_history.jsonl`` transcripts.

Turns raw JSONL into the typed ``Transcript`` defined in ``event_model``. The
parser is intentionally conservative:

* Malformed lines are skipped, not crashed on. Each skip is recorded in
  ``ParseStats`` so accounting stays honest.
* Unknown ``type`` values map to ``Role.UNKNOWN`` and a parse warning — the
  line is kept (so the count reconciles) but flagged.
* Tool-call argument JSON is parsed defensively; failures populate
  ``ToolCall.parse_error`` instead of dropping the call.
* Source completeness is **classified, not guessed**: a co-located
  ``compaction/`` directory with segment files is strong evidence the
  transcript was compacted (early turns lost) → ``SOURCE_PARTIAL``. A file
  with zero recognised roles → ``SOURCE_UNVERIFIED``.
* Timestamps: Grok ``chat_history.jsonl`` carries **no** timestamps. We set
  ``has_timestamps=False`` honestly rather than invent times. If a future
  format adds per-line timestamps, extend ``_extract_timestamp``.

This module performs **no causal interpretation**. It does not decide what
"went wrong"; it only establishes what is on the record.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from event_model import (
    Event,
    ParseStats,
    Role,
    SourceStatus,
    ToolCall,
    Transcript,
)

__all__ = [
    "parse_transcript",
    "parse_transcript_lines",
    "classify_source",
    "extract_session_id_from_path",
    "TranscriptParseError",
]

#: Maximum fraction of lines that may be malformed before the parser downgrades
#: source status to UNVERIFIED. Conservative: 1 in 3 lines garbage is clearly a
#: wrong file. Below that, we keep parsing and let ParseStats carry the detail.
_MAX_MALFORMED_RATIO_FOR_VERIFIED = 0.34

#: Grok session directories are UUID-shaped (v7-ish: 8-4-4-4-12 hex).
_SESSION_ID_RE = re.compile(r"([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})", re.I)

#: Marker files that indicate compaction has occurred (transcript was summarised).
_COMPACTION_MARKERS = ("compaction",)


class TranscriptParseError(Exception):
    """Raised only for unrecoverable input (e.g. path is a directory).

    Per-line malformed JSON is NOT a TranscriptParseError — it is recorded in
    ``ParseStats.skipped_malformed`` and parsing continues.
    """


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_transcript(path: str | Path) -> Transcript:
    """Parse a Grok ``chat_history.jsonl`` file into a ``Transcript``.

    Reads the file as UTF-8, tolerates trailing whitespace/blank lines, and
    classifies source completeness from the directory layout (compaction
    markers) and content (recognised role density).

    Raises ``TranscriptParseError`` if the path does not exist or is not a
    file — those are operator errors worth surfacing immediately rather than
    silently producing an empty transcript.
    """
    p = Path(path)
    if not p.exists():
        raise TranscriptParseError(f"Transcript file does not exist: {p}")
    if not p.is_file():
        raise TranscriptParseError(f"Transcript path is not a regular file: {p}")

    text = p.read_text(encoding="utf-8", errors="replace")
    # Normalise to forward slashes for portable provenance.
    source_path = str(p).replace("\\", "/")
    session_id = extract_session_id_from_path(source_path)
    source_status = classify_source(p)

    transcript = parse_transcript_lines(
        text.splitlines(),
        source_path=source_path,
        source_status=source_status,
        session_id=session_id,
    )
    return transcript


def parse_transcript_lines(
    lines: Iterable[str],
    *,
    source_path: str = "",
    source_status: SourceStatus | None = None,
    session_id: str | None = None,
) -> Transcript:
    """Parse an iterable of raw JSONL lines into a ``Transcript``.

    Pure function over its input (no disk reads). Use this in tests and when
    ingesting transcripts from non-file sources (e.g. exported text).

    ``source_status`` may be passed explicitly to override directory-based
    classification; if omitted, the caller is responsible for classification
    and the resulting transcript retains ``None``-equivalent handling by the
    packet builder (which will mark it UNVERIFIED with a warning).
    """
    if source_status is None:
        source_status = SourceStatus.UNVERIFIED

    events: list[Event] = []
    by_role: Counter[str] = Counter()
    warnings: list[str] = []
    total_lines = 0
    skipped_blank = 0
    skipped_malformed = 0
    synthetic_user = 0
    real_user = 0
    tool_calls_total = 0
    tool_calls_parse_err = 0
    unknown_role = 0
    saw_any_timestamp = False

    idx = 0
    for line_no, raw in enumerate(lines, start=1):
        total_lines += 1
        stripped = raw.strip()
        if not stripped:
            skipped_blank += 1
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError as exc:
            skipped_malformed += 1
            warnings.append(f"line {line_no}: malformed JSON ({exc.msg})")
            continue
        if not isinstance(obj, dict):
            skipped_malformed += 1
            warnings.append(f"line {line_no}: JSON root is not an object")
            continue

        if _extract_timestamp(obj) is not None:
            saw_any_timestamp = True

        role = Role.from_raw(obj.get("type"))
        ev_warnings: list[str] = []
        if role is Role.UNKNOWN:
            unknown_role += 1
            ev_warnings.append(f"unknown role type: {obj.get('type')!r}")

        event = _build_event(
            idx=idx,
            role=role,
            obj=obj,
            line_no=line_no,
            source_path=source_path,
            ev_warnings=ev_warnings,
        )
        events.append(event)
        by_role[role.value] += 1
        idx += 1

        # Role-specific bookkeeping.
        if role is Role.USER:
            if event.synthetic_reason:
                synthetic_user += 1
            else:
                real_user += 1
        if role is Role.ASSISTANT:
            tool_calls_total += len(event.tool_calls)
            tool_calls_parse_err += sum(1 for tc in event.tool_calls if tc.parse_error)

    stats = ParseStats(
        total_lines=total_lines,
        parsed_events=len(events),
        skipped_blank=skipped_blank,
        skipped_malformed=skipped_malformed,
        by_role=dict(by_role),
        synthetic_user_messages=synthetic_user,
        real_user_messages=real_user,
        tool_calls_total=tool_calls_total,
        tool_calls_with_parse_error=tool_calls_parse_err,
        tool_results_orphaned=0,  # filled in after join pass below
        unknown_role_lines=unknown_role,
        has_timestamps=saw_any_timestamp,
        warnings=tuple(warnings),
    )

    events_t, stats = _join_tool_results(tuple(events), stats)
    return Transcript(
        events=events_t,
        source_path=source_path,
        source_status=source_status,
        parse_stats=stats,
        session_id=session_id,
    )


def classify_source(transcript_path: str | Path) -> SourceStatus:
    """Classify completeness from the transcript file's neighbourhood.

    Heuristics (mechanical, no inference):

    * ``SOURCE_PARTIAL``  — a sibling ``compaction/`` directory exists with at
      least one ``segment_*.md`` file. Grok writes these only after
      summarising early turns, so the JSONL cannot represent the full original
      conversation even if it is internally consistent.
    * ``SOURCE_UNVERIFIED`` — the file is empty, or zero recognised roles were
      found, or the malformed-line ratio exceeds
      ``_MAX_MALFORMED_RATIO_FOR_VERIFIED`` (clearly the wrong file/format).
    * ``SOURCE_COMPLETE`` — otherwise. We do not assert "no information was
      lost"; only that no compaction marker is present and the file parses as
      a Grok transcript.
    """
    p = Path(transcript_path)
    if not p.is_file():
        return SourceStatus.UNVERIFIED

    # Compaction marker: PARTIAL regardless of how clean the JSONL looks.
    session_dir = p.parent
    compaction_dir = session_dir / "compaction"
    if compaction_dir.is_dir():
        if any(compaction_dir.glob("segment_*.md")):
            return SourceStatus.PARTIAL
        # compaction/ exists but empty — still suspicious; flag partial.
        return SourceStatus.PARTIAL

    # Content sniff: recognised role density.
    text = p.read_text(encoding="utf-8", errors="replace")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return SourceStatus.UNVERIFIED

    recognised = 0
    malformed = 0
    for ln in lines:
        try:
            obj = json.loads(ln)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if isinstance(obj, dict) and obj.get("type") in {r.value for r in Role if r is not Role.UNKNOWN}:
            recognised += 1

    if recognised == 0:
        return SourceStatus.UNVERIFIED
    if malformed / max(len(lines), 1) > _MAX_MALFORMED_RATIO_FOR_VERIFIED:
        return SourceStatus.UNVERIFIED
    return SourceStatus.COMPLETE


def extract_session_id_from_path(path_str: str) -> str | None:
    """Derive a Grok session id from a transcript path, or return None.

    Grok stores transcripts at
    ``~/.grok/sessions/<encoded-cwd>/<session-id>/chat_history.jsonl`` where
    ``<session-id>`` is a UUID. This is a documented derivation (path stem),
    not an invented identity — safe per the global "never invent provenance
    identity" rule.
    """
    m = _SESSION_ID_RE.search(path_str.replace("\\", "/"))
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Internal builders
# ---------------------------------------------------------------------------


def _build_event(
    *,
    idx: int,
    role: Role,
    obj: dict[str, Any],
    line_no: int,
    source_path: str,
    ev_warnings: list[str],
) -> Event:
    """Construct an Event from one parsed JSONL object.

    Keeps the role-switch in one place so the main loop stays readable. Each
    branch only populates the fields that role actually carries.
    """
    text = _extract_text(role, obj)
    tool_calls: tuple[ToolCall, ...] = ()
    tool_call_id: str | None = None
    synthetic_reason: str | None = None
    prompt_index: int | None = None
    model_id: str | None = None
    reasoning_effort: str | None = None
    reasoning_status: str | None = None

    if role is Role.ASSISTANT:
        tool_calls = _extract_tool_calls(obj.get("tool_calls"), ev_warnings, line_no)
        model_id = obj.get("model_id") if isinstance(obj.get("model_id"), str) else None
        reff = obj.get("reasoning_effort")
        reasoning_effort = reff if isinstance(reff, str) else None
    elif role is Role.TOOL_RESULT:
        tcid = obj.get("tool_call_id")
        tool_call_id = tcid if isinstance(tcid, str) else None
        if tool_call_id is None:
            ev_warnings.append("tool_result missing tool_call_id")
    elif role is Role.USER:
        synthetic_reason = _opt_str(obj.get("synthetic_reason"))
        pi = obj.get("prompt_index")
        prompt_index = pi if isinstance(pi, int) else None
    elif role is Role.REASONING:
        rs = obj.get("status")
        reasoning_status = rs if isinstance(rs, str) else None

    return Event(
        index=idx,
        role=role,
        text=text,
        tool_calls=tool_calls,
        tool_call_id=tool_call_id,
        synthetic_reason=synthetic_reason,
        prompt_index=prompt_index,
        model_id=model_id,
        reasoning_effort=reasoning_effort,
        reasoning_status=reasoning_status,
        source_path=source_path,
        raw_line_number=line_no,
        parse_warnings=tuple(ev_warnings),
    )


def _extract_text(role: Role, obj: dict[str, Any]) -> str | None:
    """Pull the canonical text payload for a role, joining block lists.

    Grok packs user content and reasoning summaries as lists of
    ``{type, text}`` blocks. Assistant content and tool_result content are
    plain strings. This helper normalises both to a single string (or None).
    """
    content = obj.get("content")
    if role is Role.USER or role is Role.REASONING:
        if isinstance(content, list):
            parts: list[str] = []
            for blk in content:
                if isinstance(blk, dict):
                    t = blk.get("text") or blk.get("summary_text")
                    if isinstance(t, str):
                        parts.append(t)
            return "\n".join(parts) if parts else None
        if isinstance(content, str):
            return content
        return None
    # assistant / tool_result / system / unknown — content is a plain string.
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Defensive: some tool_results occasionally wrap content in a list.
        parts = []
        for blk in content:
            if isinstance(blk, dict):
                t = blk.get("text") or blk.get("content")
                if isinstance(t, str):
                    parts.append(t)
            elif isinstance(blk, str):
                parts.append(blk)
        return "\n".join(parts) if parts else None
    return None


def _extract_tool_calls(
    raw: Any, ev_warnings: list[str], line_no: int
) -> tuple[ToolCall, ...]:
    """Normalise the assistant ``tool_calls`` list into ToolCall tuples.

    Each entry should be ``{id, name, arguments}`` with ``arguments`` as a JSON
    string. Malformed entries are kept (with ``parse_error`` set) so the
    evidence trail is complete; we never silently drop a tool call.
    """
    if not isinstance(raw, list) or not raw:
        return ()
    out: list[ToolCall] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, dict):
            ev_warnings.append(f"line {line_no}: tool_calls[{i}] not an object")
            continue
        call_id = entry.get("id")
        name = entry.get("name")
        if not isinstance(call_id, str) or not isinstance(name, str):
            ev_warnings.append(f"line {line_no}: tool_calls[{i}] missing id/name")
            continue
        args_raw = entry.get("arguments")
        if not isinstance(args_raw, str):
            # Some formats may already have parsed arguments; serialise for raw.
            args_raw_str = json.dumps(args_raw, sort_keys=True) if args_raw is not None else ""
            parsed = args_raw if isinstance(args_raw, dict) else {}
            err = None if isinstance(args_raw, dict) else "arguments not a JSON string"
            out.append(
                ToolCall(
                    id=call_id,
                    name=name,
                    arguments=parsed,
                    arguments_raw=args_raw_str,
                    parse_error=err,
                )
            )
            continue
        # arguments is a JSON string — parse defensively.
        try:
            parsed = json.loads(args_raw)
            if not isinstance(parsed, dict):
                raise ValueError("arguments JSON root is not an object")
            out.append(
                ToolCall(
                    id=call_id,
                    name=name,
                    arguments=parsed,
                    arguments_raw=args_raw,
                    parse_error=None,
                )
            )
        except (json.JSONDecodeError, ValueError) as exc:
            out.append(
                ToolCall(
                    id=call_id,
                    name=name,
                    arguments={},
                    arguments_raw=args_raw,
                    parse_error=f"argument parse failed: {exc}",
                )
            )
    return tuple(out)


def _join_tool_results(
    events: tuple[Event, ...], stats: ParseStats
) -> tuple[tuple[Event, ...], ParseStats]:
    """Count orphaned tool_results (no matching tool_call.id).

    We do not mutate events here — joining is the detector layer's job (it may
    want to know which assistant turn produced a result). We only update the
    accounting statistic so the packet can report data quality honestly.
    """
    produced_ids = {
        tc.id for ev in events for tc in ev.tool_calls if ev.role is Role.ASSISTANT
    }
    orphaned = sum(
        1
        for ev in events
        if ev.role is Role.TOOL_RESULT and ev.tool_call_id not in produced_ids
    )
    if orphaned:
        new_warnings = list(stats.warnings) + [
            f"{orphaned} tool_result(s) reference unknown tool_call_id"
        ]
        stats = ParseStats(
            **{**stats.to_dict(), "tool_results_orphaned": orphaned, "warnings": new_warnings}
        )
    return events, stats


def _extract_timestamp(obj: dict[str, Any]) -> str | None:
    """Return a timestamp string if the record carries one, else None.

    Current Grok ``chat_history.jsonl`` records have no timestamp field — this
    function exists so the parser can *detect* a future format change rather
    than silently assume absence forever. ``ParseStats.has_timestamps`` is set
    accordingly.
    """
    for key in ("ts", "timestamp", "time", "created_at"):
        v = obj.get(key)
        if isinstance(v, str) and v:
            return v
    return None


def _opt_str(v: Any) -> str | None:
    return v if isinstance(v, str) else None
