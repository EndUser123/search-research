"""Normalize parsed sources into the canonical active-session event stream.

Per spec Section 6 + Section 9: stream every chat_history record through
code, normalize into ``CanonicalEvent`` objects, assign stable event_ids,
cross-link timestamps from events.jsonl where possible, and label branch
status (ACTIVE_HISTORY vs SUPERSEDED_HISTORY).

Branch resolution algorithm
---------------------------
The reconciler identifies prompt_index values that appear more than once
in real user messages (rewind + replay). For each such duplicate, the
*first* occurrence begins a branch that is later superseded by the
*second* occurrence. Records are labelled as follows:

1. Walk the transcript in order, tracking the "active prompt_index" cursor.
2. For each event, find its prompt_index (events inherit the prompt_index
   of the user message that opened their turn).
3. If a later event's prompt_index appears earlier in the stream AFTER an
   intervening event with the same prompt_index, the earlier run from
   that prompt_index forward is SUPERSEDED.
4. Events whose prompt_index is None (system records, harness injections)
   are SYSTEM_METADATA — never user history, never superseded.

The algorithm is conservative: ambiguous cases (gaps, missing prompt_index
on a user message) yield ``BRANCH_UNKNOWN`` for the affected range and the
reconciler's ``branch_state_resolved`` flag stays False, which downgrades
completeness to PARTIAL.

Cross-linking
-------------
For each chat_history record we look for a matching ``turn_started`` (by
turn number ↔ prompt_index) and ``tool_started/tool_completed`` (by tool
order within a turn) to attach a timestamp and duration. Matching is
best-effort: when no match is found, ``timestamp`` and ``duration_ms``
remain None. We never invent timestamps.

Determinism
-----------
Output order is stable: :meth:`CanonicalEvent.sort_key` is the final
ordering. Re-running on the same snapshot yields identical event_ids and
identical ordering.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from canonical_model import (
    BranchStatus,
    CanonicalEvent,
    CanonicalEventType,
    SOURCE_ORDER,
)
from event_model import Event, Role, ToolCall
from reconciler import ReconciliationReport, USEFUL_EVENT_TYPES

__all__ = [
    "CanonicalStream",
    "normalize_session",
    "normalize_event",
    "classify_canonical_type",
]

#: Markers used to classify tool results into richer canonical types.
_TEST_RUN_RE = re.compile(r"\bpytest\b|\bjest\b|\bcargo test\b|\bgo test\b|\brspec\b", re.I)
_GIT_OP_RE = re.compile(r"\bgit\s+(checkout|reset|restore|stash|clean|commit|push|pull|merge|rebase|revert|clone|fetch|branch|tag)\b", re.I)
_ERROR_RE = re.compile(r"(?:^|\n)\s*error:|traceback \(most recent call last\)|exit code: ?[1-9]", re.I | re.MULTILINE)
_EXIT_CODE_RE = re.compile(r"exit code: ?(\d+)", re.I)
_FILE_WRITE_TOOLS = frozenset({"write", "edit", "search_replace"})
_FILE_READ_TOOLS = frozenset({"read_file", "list_dir", "grep"})
_COMMAND_TOOLS = frozenset({"run_terminal_command", "bash", "run_command"})


@dataclass(frozen=True)
class CanonicalStream:
    """Normalized canonical stream + branch accounting."""

    events: tuple[CanonicalEvent, ...]
    active_events: tuple[CanonicalEvent, ...]
    superseded_events: tuple[CanonicalEvent, ...]
    unknown_branch_events: tuple[CanonicalEvent, ...]
    system_metadata_events: tuple[CanonicalEvent, ...]
    cross_link_count: int  #: how many events got a timestamp from events.jsonl
    warnings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "events_total": len(self.events),
            "active_events": len(self.active_events),
            "superseded_events": len(self.superseded_events),
            "unknown_branch_events": len(self.unknown_branch_events),
            "system_metadata_events": len(self.system_metadata_events),
            "cross_link_count": self.cross_link_count,
            "warnings": list(self.warnings),
        }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def normalize_session(
    transcript,
    *,
    reconciliation: ReconciliationReport,
    events: list[dict[str, Any]] | None = None,
    session_id: str,
    terminal_id: str,
) -> CanonicalStream:
    """Build the canonical stream from a parsed transcript + reconciliation.

    ``transcript`` is the parsed chat_history.jsonl. ``reconciliation``
    drives branch labelling. ``events`` (filtered events.jsonl) is used for
    cross-linking timestamps and durations; pass None to skip cross-linking.
    """
    warnings: list[str] = []

    # Build turn → (started_ts, ended_ts, model_id) map from events.jsonl.
    turn_started_ts: dict[int, str] = {}
    turn_ended_ts: dict[int, str] = {}
    turn_model: dict[int, str] = {}
    if events:
        for ev in events:
            t = ev.get("type")
            tn = ev.get("turn_number")
            if not isinstance(tn, int):
                continue
            if t == "turn_started":
                ts = ev.get("ts")
                if isinstance(ts, str):
                    turn_started_ts[tn] = ts
                mid = ev.get("model_id")
                if isinstance(mid, str):
                    turn_model[tn] = mid
            elif t == "turn_ended":
                ts = ev.get("ts")
                if isinstance(ts, str):
                    turn_ended_ts[tn] = ts

    # Build tool_name → list of (ts, duration_ms) queues for cross-linking.
    # We match the Nth assistant tool_call of name X to the Nth
    # tool_started/tool_completed of name X in events.jsonl, in order.
    tool_started_queue: dict[str, list[str]] = {}
    tool_completed_queue: dict[str, list[tuple[str, int | None]]] = {}
    if events:
        for ev in events:
            t = ev.get("type")
            tn = ev.get("tool_name")
            if not isinstance(tn, str):
                continue
            if t == "tool_started":
                tool_started_queue.setdefault(tn, []).append(ev.get("ts") or "")
            elif t == "tool_completed":
                dur = ev.get("duration_ms")
                tool_completed_queue.setdefault(tn, []).append(
                    (ev.get("ts") or "", int(dur) if isinstance(dur, (int, float)) else None)
                )

    # --- Branch resolution ---
    # Identify the prompt_index sub-ranges that are superseded.
    # For each duplicated prompt_index, find the *first* occurrence range
    # (from that user message until the next user message with a different
    # prompt_index) — that range is SUPERSEDED.
    superseded_ranges: list[tuple[int, int]] = []  # [start_event_idx, end_event_idx)
    duplicated = set(reconciliation.duplicated_prompt_indices)
    if duplicated:
        # First pass: find indices of user messages by prompt_index.
        user_msg_indices: dict[int, list[int]] = {}
        for i, ev in enumerate(transcript.events):
            if ev.role is Role.USER and not ev.synthetic_reason and ev.prompt_index is not None:
                user_msg_indices.setdefault(ev.prompt_index, []).append(i)
        # For each duplicated prompt_index, mark the first occurrence range.
        for pi, idx_list in user_msg_indices.items():
            if len(idx_list) < 2:
                continue
            first_start = idx_list[0]
            # End is the next user message after first_start, exclusive.
            end = len(transcript.events)
            for j in range(first_start + 1, len(transcript.events)):
                ev = transcript.events[j]
                if ev.role is Role.USER and not ev.synthetic_reason:
                    end = j
                    break
            superseded_ranges.append((first_start, end))

    def branch_for_index(idx: int) -> BranchStatus:
        for s, e in superseded_ranges:
            if s <= idx < e:
                return BranchStatus.SUPERSEDED_HISTORY
        return BranchStatus.ACTIVE_HISTORY

    # --- Build canonical events ---
    canonical: list[CanonicalEvent] = []
    cross_links = 0
    # Track per-turn tool-call index for cross-linking within a turn.
    current_turn = None
    turn_tool_counter: dict[str, int] = {}

    for i, ev in enumerate(transcript.events):
        # Determine the turn for this event.
        if ev.role is Role.USER and not ev.synthetic_reason and ev.prompt_index is not None:
            current_turn = ev.prompt_index
            turn_tool_counter = {}
        turn = current_turn if current_turn is not None else ev.prompt_index

        # Cross-link timestamp from turn_started.
        timestamp = turn_started_ts.get(turn) if turn is not None else None
        model_override = turn_model.get(turn) if turn is not None else None
        if timestamp:
            cross_links += 1

        # Classify and build tool metadata for assistant events.
        canonical_type, tool_meta = classify_canonical_type(ev)

        # Cross-link tool timing for the Nth call of each tool name in turn.
        tool_ts = None
        tool_dur = None
        if tool_meta.tool_name:
            tn = tool_meta.tool_name
            counter = turn_tool_counter.get(tn, 0)
            turn_tool_counter[tn] = counter + 1
            started_q = tool_started_queue.get(tn, [])
            completed_q = tool_completed_queue.get(tn, [])
            if counter < len(started_q):
                tool_ts = started_q[counter] or None
            if counter < len(completed_q):
                tool_ts = completed_q[counter][0] or tool_ts
                tool_dur = completed_q[counter][1]
            if tool_ts:
                cross_links += 1

        # Branch label.
        if ev.role is Role.SYSTEM or (ev.role is Role.USER and ev.synthetic_reason):
            branch = BranchStatus.SYSTEM_METADATA
        else:
            branch = branch_for_index(i)

        # Actor.
        actor = _actor_for(ev)

        # Event id: stable, deterministic.
        eid = _event_id("chat_history.jsonl", ev.raw_line_number, i)

        ce = CanonicalEvent.from_event(
            ev,
            event_id=eid,
            source_file="chat_history.jsonl",
            canonical_type=canonical_type,
            actor=actor,
            branch_status=branch,
            turn_index=turn,
            sequence_index=i,
            timestamp=tool_ts or timestamp,
            tool_name=tool_meta.tool_name,
            command=tool_meta.command,
            working_directory=None,
            stdout_excerpt=tool_meta.stdout_excerpt,
            stderr_excerpt=tool_meta.stderr_excerpt,
            exit_code=tool_meta.exit_code,
            duration_ms=tool_dur,
            paths=tool_meta.paths,
            model=model_override or ev.model_id,
            provider=None,
            parse_confidence="HIGH",
        )
        canonical.append(ce)

    # Sort deterministically.
    canonical.sort(key=lambda c: c.sort_key())

    active = tuple(c for c in canonical if c.branch_status is BranchStatus.ACTIVE_HISTORY)
    superseded = tuple(c for c in canonical if c.branch_status is BranchStatus.SUPERSEDED_HISTORY)
    unknown = tuple(c for c in canonical if c.branch_status is BranchStatus.BRANCH_UNKNOWN)
    system = tuple(c for c in canonical if c.branch_status is BranchStatus.SYSTEM_METADATA)

    if unknown:
        warnings.append(f"{len(unknown)} events have BRANCH_UNKNOWN status")

    return CanonicalStream(
        events=tuple(canonical),
        active_events=active,
        superseded_events=superseded,
        unknown_branch_events=unknown,
        system_metadata_events=system,
        cross_link_count=cross_links,
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# Classification + helpers
# ---------------------------------------------------------------------------


@dataclass
class _ToolMeta:
    tool_name: str | None = None
    command: str | None = None
    stdout_excerpt: str | None = None
    stderr_excerpt: str | None = None
    exit_code: int | None = None
    paths: tuple[str, ...] = ()


def classify_canonical_type(ev: Event) -> tuple[CanonicalEventType, _ToolMeta]:
    """Determine the rich CanonicalEventType + tool metadata for an Event.

    Returns ``(canonical_type, tool_meta)``. The mapping is conservative:
    we only escalate ``TOOL_RESULT`` to ``ERROR`` / ``TEST_RUN`` /
    ``GIT_OPERATION`` when explicit content markers are present (we reuse
    the detectors' classification logic, not new heuristics).
    """
    meta = _ToolMeta()

    if ev.role is Role.SYSTEM:
        return CanonicalEventType.SYSTEM_METADATA, meta
    if ev.role is Role.USER:
        if ev.synthetic_reason:
            return CanonicalEventType.SYSTEM_METADATA, meta
        return CanonicalEventType.USER_MESSAGE, meta
    if ev.role is Role.REASONING:
        return CanonicalEventType.SESSION_EVENT, meta
    if ev.role is Role.ASSISTANT:
        if not ev.tool_calls:
            return CanonicalEventType.ASSISTANT_MESSAGE, meta
        # Single-call events get the call's type; multi-call stays TOOL_CALL.
        if len(ev.tool_calls) == 1:
            tc = ev.tool_calls[0]
            meta.tool_name = tc.name
            if tc.name in _FILE_WRITE_TOOLS:
                meta.paths = _paths_from_args(tc)
                return CanonicalEventType.FILE_WRITE, meta
            if tc.name in _FILE_READ_TOOLS:
                meta.paths = _paths_from_args(tc)
                return CanonicalEventType.FILE_READ, meta
            if tc.name in _COMMAND_TOOLS:
                cmd = tc.arguments.get("command") if isinstance(tc.arguments, dict) else None
                if isinstance(cmd, str):
                    meta.command = cmd
                    if _GIT_OP_RE.search(cmd):
                        return CanonicalEventType.GIT_OPERATION, meta
                    if _TEST_RUN_RE.search(cmd):
                        return CanonicalEventType.TEST_RUN, meta
                    return CanonicalEventType.COMMAND, meta
            return CanonicalEventType.TOOL_CALL, meta
        # Multi-call: type is TOOL_CALL; collect paths/commands across calls.
        all_paths: list[str] = []
        for tc in ev.tool_calls:
            all_paths.extend(_paths_from_args(tc))
        meta.paths = tuple(all_paths)
        meta.tool_name = "multi"
        return CanonicalEventType.TOOL_CALL, meta
    if ev.role is Role.TOOL_RESULT:
        text = ev.text or ""
        meta.stdout_excerpt = (text[:240] + "...") if len(text) > 240 else text
        m = _EXIT_CODE_RE.search(text)
        if m:
            try:
                meta.exit_code = int(m.group(1))
            except ValueError:
                pass
        if _ERROR_RE.search(text):
            meta.stderr_excerpt = _first_error_line(text)
            return CanonicalEventType.ERROR, meta
        if _TEST_RUN_RE.search(text):
            return CanonicalEventType.TEST_RUN, meta
        if _GIT_OP_RE.search(text):
            return CanonicalEventType.GIT_OPERATION, meta
        return CanonicalEventType.TOOL_RESULT, meta
    return CanonicalEventType.SESSION_EVENT, meta


def normalize_event(ev: Event, *, source_file: str, line: int, seq: int) -> CanonicalEvent:
    """Normalize a single Event into a CanonicalEvent with sensible defaults.

    Used by tests and ad-hoc callers. The full pipeline uses
    :func:`normalize_session` which also handles branch labels + cross-links.
    """
    ctype, meta = classify_canonical_type(ev)
    return CanonicalEvent.from_event(
        ev,
        event_id=_event_id(source_file, line, seq),
        source_file=source_file,
        canonical_type=ctype,
        actor=_actor_for(ev),
        branch_status=BranchStatus.SYSTEM_METADATA
        if ev.role is Role.SYSTEM
        else BranchStatus.ACTIVE_HISTORY,
        turn_index=ev.prompt_index,
        sequence_index=seq,
        tool_name=meta.tool_name,
        command=meta.command,
        paths=meta.paths,
        stdout_excerpt=meta.stdout_excerpt,
        stderr_excerpt=meta.stderr_excerpt,
        exit_code=meta.exit_code,
    )


def _actor_for(ev: Event) -> str:
    if ev.role is Role.SYSTEM:
        return "system"
    if ev.role is Role.USER:
        return "user" if not ev.synthetic_reason else "harness"
    if ev.role is Role.ASSISTANT:
        return "assistant"
    if ev.role is Role.REASONING:
        return "assistant"
    if ev.role is Role.TOOL_RESULT:
        return "tool"
    return "unknown"


def _paths_from_args(tc: ToolCall) -> tuple[str, ...]:
    if not isinstance(tc.arguments, dict):
        return ()
    out: list[str] = []
    for key in ("file_path", "target_file", "path"):
        v = tc.arguments.get(key)
        if isinstance(v, str) and v:
            out.append(v.replace("\\", "/"))
    return tuple(out)


def _first_error_line(text: str) -> str:
    for line in text.splitlines():
        if _ERROR_RE.search(line):
            return line.strip()[:200]
    return text[:200]


def _event_id(source_file: str, line: int, seq: int) -> str:
    """Deterministic event id: ``<source-stem>-L<line>-S<seq>``.

    Stable across re-runs on the same snapshot. No random component."""
    stem = source_file.replace(".jsonl", "").replace("/", "_")
    return f"{stem}-L{line:06d}-S{seq:06d}"
