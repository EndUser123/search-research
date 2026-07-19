"""Deterministic parser: Grok chat_history.jsonl -> Transcript.

Single responsibility: read a JSONL transcript file and produce an immutable
``Transcript`` of typed ``Event`` objects. No signal extraction, no judgment.

Verified against real Grok session 019f6c3b-* (1197 lines):
* Five record types: system, user, assistant, tool_result, reasoning.
* ``user.content`` may be a String OR a list of ``{type:"text", text}`` blocks
  (the harness injects system-reminders / user-info / git-status as user-role
  messages with list content).
* ``assistant.content`` is always a String (possibly empty when only
  tool_calls are present).
* ``assistant.tool_calls[*].arguments`` is a JSON STRING that must be parsed.
* ``reasoning`` records have NO ``content`` field — ``summary`` holds the
  human-readable text. ``status`` is present on ~47% of reasoning records.
* No record carries a timestamp.

Honesty rules
-------------
* Blank lines are skipped (counted in ``ParseStats.skipped_blank``).
* Lines that fail JSON parse are skipped (counted in
  ``ParseStats.skipped_malformed``) with a warning.
* tool_result records whose ``tool_call_id`` has no matching earlier
  ``tool_call.id`` are KEPT (they carry real text) but counted in
  ``tool_results_orphaned``.
* Synthetic user messages (harness-injected) are flagged via
  ``Event.synthetic_reason`` and counted in ``synthetic_user_messages``.

The parser NEVER raises on a malformed line; it records the failure and
continues. A transcript with malformed lines is still analysable, the
parser just refuses to pretend the malformed content was valid.
"""

from __future__ import annotations

import json
import re
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

__all__ = ["parse_jsonl", "parse_file", "infer_source_status", "extract_session_id"]

#: Regex fragments used to detect harness-injected user messages. We use a
#: regex, not a substring match, so we identify the *outermost* injection
#: (some real prompts quote these tags inside <user_query>). Each entry
#: pairs the compiled pattern with a stable human-readable tag so the
#: detector does not have to derive a tag from the regex source (which
#: produced nonsense like ``"system>$*$"`` for the ``<system>\s*$`` pattern).
_SYNTHETIC_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"<system-reminder>", re.IGNORECASE), "system-reminder"),
    (re.compile(r"<user_info>", re.IGNORECASE), "user_info"),
    (re.compile(r"<git_status>", re.IGNORECASE), "git_status"),
    (re.compile(r"<system>\s*$", re.IGNORECASE | re.MULTILINE), "system"),
)

#: A real user prompt is wrapped in <user_query>...</user_query>. We treat a
#: user record as REAL if it contains that wrapper, otherwise we apply the
#: synthetic-pattern test.
_USER_QUERY_TAG = re.compile(r"<user_query>", re.IGNORECASE)


def extract_session_id(source_path: str) -> str | None:
    """Best-effort session id extraction from a Grok sessions path.

    Grok stores transcripts at:
        ``~/.grok/sessions/<encoded-cwd>/<session-uuid>/chat_history.jsonl``

    The session id is the UUID-shaped directory name immediately above the
    JSONL file. Returns ``None`` for paths that do not match this layout
    (e.g. ad-hoc test fixtures).

    This is mechanical path derivation, not invented identity — see global
    rule "Never invent provenance identity". If we cannot derive the id, we
    return None and let the packet carry an explicit absence.
    """
    if not source_path:
        return None
    p = Path(source_path)
    # Look for a UUID-shaped parent dir (8-4-4-4-12 hex).
    uuid_re = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE)
    for parent in p.parents:
        if uuid_re.match(parent.name):
            return parent.name
    return None


def infer_source_status(
    source_path: str,
    total_lines: int,
    skipped_malformed: int,
    parsed_events: int = 0,
) -> SourceStatus:
    """Classify the transcript's completeness.

    * ``UNVERIFIED`` if the path is empty, no lines were read, or zero events
      were successfully parsed (e.g. an all-blank file).
    * ``PARTIAL`` if any lines failed JSON parse (the stream is incomplete
      or corrupted) — analyse but flag.
    * ``COMPLETE`` otherwise.

    Note: this cannot detect compaction. Grok's compaction produces separate
    ``compaction/segment_*.md`` files, not a modified JSONL. A caller that
    knows compaction occurred should override this via ``Transcript.replace``.
    """
    if not source_path or total_lines == 0 or parsed_events == 0:
        return SourceStatus.UNVERIFIED
    if skipped_malformed > 0:
        return SourceStatus.PARTIAL
    return SourceStatus.COMPLETE


def _coerce_text(content: Any) -> str | None:
    """Normalise a record's ``content`` field to a single string (or None).

    Grok uses two shapes:
    * String  -> returned as-is.
    * List of blocks -> concatenate block.text fields (skip non-text blocks).

    Returns ``None`` only when content is absent or empty after normalisation.
    """
    if content is None:
        return None
    if isinstance(content, str):
        return content if content else None
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                t = block.get("text")
                if isinstance(t, str):
                    parts.append(t)
                elif t is not None:
                    parts.append(str(t))
            elif isinstance(block, str):
                parts.append(block)
        joined = "".join(parts)
        return joined if joined else None
    # Unknown shape (number, bool, dict) — stringify defensively.
    return str(content) if content != "" else None


def _detect_synthetic_reason(text: str | None) -> str | None:
    """Return the synthetic-injection tag found in a user message, or None.

    A real user prompt contains ``<user_query>``. If that tag is present, the
    message is real even if it also quotes ``<system-reminder>`` (e.g. the
    user pasted session context). Otherwise, presence of any injection tag
    marks the message as synthetic.
    """
    if text is None:
        return None
    if _USER_QUERY_TAG.search(text):
        return None
    for pat, tag in _SYNTHETIC_PATTERNS:
        if pat.search(text):
            return tag
    return None


def _parse_tool_calls(raw_calls: Any) -> tuple[tuple[ToolCall, ...], tuple[str, ...]]:
    """Build ToolCall tuples from a raw assistant.tool_calls array.

    Returns ``(calls, warnings)``. Each malformed call produces a ToolCall
    with ``parse_error`` set rather than being dropped — verifiers need to
    see that a call was attempted even if its arguments were unparseable.
    """
    if not raw_calls or not isinstance(raw_calls, list):
        return (), ()
    calls: list[ToolCall] = []
    warnings: list[str] = []
    for rc in raw_calls:
        if not isinstance(rc, dict):
            warnings.append(f"tool_call entry not an object: {type(rc).__name__}")
            continue
        call_id = rc.get("id") or ""
        name = rc.get("name") or ""
        raw_args = rc.get("arguments")
        # Arguments may already be a dict (defensive) or a JSON string.
        if isinstance(raw_args, dict):
            args = raw_args
            args_raw = json.dumps(raw_args, ensure_ascii=False)
            parse_error: str | None = None
        elif isinstance(raw_args, str):
            args_raw = raw_args
            try:
                parsed = json.loads(raw_args)
                if isinstance(parsed, dict):
                    args = parsed
                    parse_error = None
                else:
                    # JSON parsed but not an object (list, scalar). Tool-call
                    # arguments are conventionally a JSON object; anything else
                    # is a producer-side anomaly we surface as a parse-quality
                    # signal rather than silently wrapping under a synthetic
                    # "__value__" key (which detectors would never find).
                    args = {}
                    parse_error = f"arguments_not_object: got {type(parsed).__name__}"
                    warnings.append(
                        f"tool_call {call_id} ({name}) args parsed to "
                        f"{type(parsed).__name__}, expected JSON object"
                    )
            except json.JSONDecodeError as e:
                args = {}
                parse_error = f"json_decode_error: {e.msg}"
                warnings.append(f"tool_call {call_id} ({name}) args parse error: {e.msg}")
        else:
            args_raw = "" if raw_args is None else str(raw_args)
            args = {}
            parse_error = f"unexpected_arguments_type: {type(raw_args).__name__}"
            warnings.append(f"tool_call {call_id} ({name}) args type {type(raw_args).__name__}")
        calls.append(
            ToolCall(
                id=str(call_id),
                name=str(name),
                arguments=args,
                arguments_raw=args_raw,
                parse_error=parse_error,
            )
        )
    return tuple(calls), tuple(warnings)


def parse_jsonl(
    records: Iterable[str | bytes | dict],
    source_path: str = "",
) -> Transcript:
    """Parse an iterable of JSONL records into a ``Transcript``.

    Accepts either pre-decoded dicts (for tests) or raw JSON strings/bytes
    (for file reads). Mixing is allowed; each item is decoded only if needed.

    The resulting ``Transcript.source_status`` is inferred from line/parse
    counts. Override by ``transcript.replace(source_status=...)`` if the
    caller has external knowledge (e.g. compaction occurred).
    """
    fwd_path = source_path.replace("\\", "/")
    events: list[Event] = []
    by_role: dict[str, int] = {}
    warnings: list[str] = []
    synthetic_user = 0
    real_user = 0
    tool_calls_total = 0
    tool_calls_with_err = 0
    tool_results_orphaned = 0
    unknown_role = 0
    total_lines = 0
    skipped_blank = 0
    skipped_malformed = 0

    # Track every tool_call.id we have seen so we can flag orphaned results.
    seen_tool_call_ids: set[str] = set()

    for raw in records:
        total_lines += 1
        if raw is None:
            skipped_blank += 1
            continue
        if isinstance(raw, (str, bytes)):
            text_raw = raw.decode("utf-8") if isinstance(raw, bytes) else raw
            if text_raw.strip() == "":
                skipped_blank += 1
                continue
            try:
                obj = json.loads(text_raw)
            except json.JSONDecodeError as e:
                skipped_malformed += 1
                warnings.append(f"line {total_lines}: json decode error: {e.msg}")
                continue
        elif isinstance(raw, dict):
            obj = raw
        else:
            skipped_malformed += 1
            warnings.append(f"line {total_lines}: unexpected record type {type(raw).__name__}")
            continue

        if not isinstance(obj, dict):
            skipped_malformed += 1
            warnings.append(f"line {total_lines}: record is not an object")
            continue

        rec_type = obj.get("type")
        role = Role.from_raw(rec_type)
        index = len(events)
        line_warnings: list[str] = []

        text: str | None = None
        tool_calls: tuple[ToolCall, ...] = ()
        tool_call_id: str | None = None
        synthetic_reason: str | None = None
        model_id: str | None = None
        reasoning_effort: str | None = None
        reasoning_status: str | None = None

        if role is Role.UNKNOWN:
            unknown_role += 1
            line_warnings.append(f"unknown_record_type: {rec_type!r}")

        if role is Role.ASSISTANT:
            text = _coerce_text(obj.get("content"))
            tc_raw = obj.get("tool_calls")
            tool_calls, tc_warns = _parse_tool_calls(tc_raw)
            line_warnings.extend(tc_warns)
            for tc in tool_calls:
                seen_tool_call_ids.add(tc.id)
                tool_calls_total += 1
                if tc.parse_error is not None:
                    tool_calls_with_err += 1
            mid = obj.get("model_id")
            if isinstance(mid, str) and mid:
                model_id = mid
            reff = obj.get("reasoning_effort")
            if isinstance(reff, str) and reff:
                reasoning_effort = reff

        elif role is Role.USER:
            text = _coerce_text(obj.get("content"))
            synthetic_reason = _detect_synthetic_reason(text)
            if synthetic_reason is not None:
                synthetic_user += 1
            else:
                real_user += 1

        elif role is Role.TOOL_RESULT:
            text = _coerce_text(obj.get("content"))
            tcid = obj.get("tool_call_id")
            if isinstance(tcid, str) and tcid:
                tool_call_id = tcid
                if tcid not in seen_tool_call_ids:
                    tool_results_orphaned += 1
                    line_warnings.append(f"orphaned_tool_result: id={tcid}")
            else:
                tool_results_orphaned += 1
                line_warnings.append("tool_result_missing_tool_call_id")

        elif role is Role.REASONING:
            # Reasoning records have NO content field. Use summary.
            summary = obj.get("summary")
            text = summary if isinstance(summary, str) and summary else None
            status = obj.get("status")
            if isinstance(status, str) and status:
                reasoning_status = status

        elif role is Role.SYSTEM:
            text = _coerce_text(obj.get("content"))

        by_role[role.value] = by_role.get(role.value, 0) + 1

        events.append(
            Event(
                index=index,
                role=role,
                text=text,
                tool_calls=tool_calls,
                tool_call_id=tool_call_id,
                synthetic_reason=synthetic_reason,
                model_id=model_id,
                reasoning_effort=reasoning_effort,
                reasoning_status=reasoning_status,
                source_path=fwd_path,
                raw_line_number=total_lines,
                parse_warnings=tuple(line_warnings),
            )
        )

    stats = ParseStats(
        total_lines=total_lines,
        parsed_events=len(events),
        skipped_blank=skipped_blank,
        skipped_malformed=skipped_malformed,
        by_role=by_role,
        synthetic_user_messages=synthetic_user,
        real_user_messages=real_user,
        tool_calls_total=tool_calls_total,
        tool_calls_with_parse_error=tool_calls_with_err,
        tool_results_orphaned=tool_results_orphaned,
        unknown_role_lines=unknown_role,
        has_timestamps=False,  # Verified: Grok JSONL has no timestamps.
        warnings=tuple(warnings),
    )
    status = infer_source_status(fwd_path, total_lines, skipped_malformed, parsed_events=len(events))
    session_id = extract_session_id(fwd_path)
    return Transcript(
        events=tuple(events),
        source_path=fwd_path,
        source_status=status,
        parse_stats=stats,
        session_id=session_id,
    )


def parse_file(path: str | Path) -> Transcript:
    """Parse a JSONL file from disk into a ``Transcript``.

    Reads lazily (line by line) so very large transcripts do not need to fit
    in memory twice.
    """
    p = Path(path)
    fwd = str(p).replace("\\", "/")

    def _iter() -> Iterable[str]:
        with p.open("r", encoding="utf-8") as fh:
            for line in fh:
                # Strip the trailing newline; keep the raw payload otherwise.
                yield line.rstrip("\n")

    return parse_jsonl(_iter(), source_path=fwd)
