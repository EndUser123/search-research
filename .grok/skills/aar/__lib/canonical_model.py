"""Canonical event model — the unified type for the reconciled stream.

Per spec Section 6: normalize all usable records into one event model with
rich fields (turn_index, sequence_index, timestamp, actor, branch_status,
tool_name, command, paths, etc.) and four allowed branch statuses.

Design: ``CanonicalEvent`` is a frozen dataclass that **extends** the
existing :class:`event_model.Event`. This means every existing detector
(which accepts ``Iterable[Event]``) continues to work unchanged on canonical
events — the new fields are additive.

The spec also requires deterministic ordering even without timestamps. We
provide ``CanonicalEvent.sort_key()`` which orders by ``(turn_index,
sequence_index, source_file_order, source_line)`` — fully deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any

from event_model import Event, Role

__all__ = [
    "CanonicalEventType",
    "BranchStatus",
    "CanonicalEvent",
    "SOURCE_ORDER",
]


class CanonicalEventType(str, Enum):
    """The 16 event types from spec Section 6.

    Every CanonicalEvent carries one of these. They are stricter/more
    descriptive than the raw ``Role`` values: e.g. a single raw
    ``tool_result`` may normalize to either ``TOOL_RESULT``, ``ERROR``,
    ``TEST_RUN``, ``GIT_OPERATION``, or ``FILE_WRITE`` depending on its
    content. The richer type powers retrieval indexes without losing the
    original role.
    """

    USER_MESSAGE = "USER_MESSAGE"
    ASSISTANT_MESSAGE = "ASSISTANT_MESSAGE"
    TOOL_CALL = "TOOL_CALL"
    TOOL_RESULT = "TOOL_RESULT"
    COMMAND = "COMMAND"
    FILE_READ = "FILE_READ"
    FILE_WRITE = "FILE_WRITE"
    TEST_RUN = "TEST_RUN"
    GIT_OPERATION = "GIT_OPERATION"
    ERROR = "ERROR"
    SESSION_EVENT = "SESSION_EVENT"
    REWIND = "REWIND"
    DECISION_CANDIDATE = "DECISION_CANDIDATE"
    CORRECTION_CANDIDATE = "CORRECTION_CANDIDATE"
    CLAIM_CANDIDATE = "CLAIM_CANDIDATE"
    SYSTEM_METADATA = "SYSTEM_METADATA"


class BranchStatus(str, Enum):
    """Per spec Section 6: allowed branch statuses.

    * ``ACTIVE_HISTORY``       — part of the canonical timeline at cutoff.
    * ``SUPERSEDED_HISTORY``   — overwritten by a later rewind+replay.
    * ``BRANCH_UNKNOWN``       — cannot determine (lowers completeness).
    * ``SYSTEM_METADATA``      — system/instruction records, not user history.
    """

    ACTIVE_HISTORY = "ACTIVE_HISTORY"
    SUPERSEDED_HISTORY = "SUPERSEDED_HISTORY"
    BRANCH_UNKNOWN = "BRANCH_UNKNOWN"
    SYSTEM_METADATA = "SYSTEM_METADATA"


#: Deterministic ordering of source files. When two events share turn+seq,
#: the source with lower index wins. Primary (chat_history) is authoritative.
SOURCE_ORDER: dict[str, int] = {
    "chat_history.jsonl": 0,
    "events.jsonl": 1,
    "rewind_points.jsonl": 2,
    "compaction_checkpoints": 3,
    "compaction": 4,
}


@dataclass(frozen=True)
class CanonicalEvent(Event):
    """A normalized event in the canonical active-session stream.

    Extends :class:`Event` so all existing detectors work unchanged. Adds
    the spec's required fields where mechanically derivable. Fields that
    cannot be derived from any source are ``None`` — we never invent values.

    Construction is via :meth:`from_event` (preferred) or :meth:`from_record`
    (for events.jsonl / rewind_points that don't have an Event counterpart).
    """

    #: Stable identifier across the run. Format: ``<source-stem>-<line>-<seq>``.
    event_id: str = ""
    #: File name within the snapshot (e.g. ``chat_history.jsonl``).
    source_file: str = ""
    #: 1-based line number for JSONL files; byte offset for non-JSONL.
    source_line_or_offset: int = 0
    #: Original record id if present (e.g. reasoning ``id``).
    source_record_id: str | None = None
    #: Turn index — derived from prompt_index where available, else sequence.
    turn_index: int | None = None
    #: Sequence index within a turn (for ordering tool_call→tool_result).
    sequence_index: int = 0
    #: ISO-8601 timestamp from events.jsonl if a matching record was found.
    timestamp: str | None = None
    #: Speaker: ``user`` / ``assistant`` / ``system`` / ``tool`` / ``process``.
    actor: str = ""
    #: Richer type (see CanonicalEventType).
    canonical_type: CanonicalEventType = CanonicalEventType.SESSION_EVENT
    #: Tool name if applicable.
    tool_name: str | None = None
    #: Shell command if this is a COMMAND/GIT_OPERATION event.
    command: str | None = None
    #: Working directory if derivable.
    working_directory: str | None = None
    #: stdout excerpt (tool_result content) — truncated to keep packet bounded.
    stdout_excerpt: str | None = None
    #: stderr excerpt (error markers within tool_result).
    stderr_excerpt: str | None = None
    #: Exit code if derivable from tool_result text (e.g. ``Exit Code: 1``).
    exit_code: int | None = None
    #: Tool duration in ms (from events.jsonl tool_completed.duration_ms).
    duration_ms: int | None = None
    #: File paths referenced (from tool args / git commands).
    paths: tuple[str, ...] = ()
    #: Provider/model id.
    model: str | None = None
    provider: str | None = None
    #: Branch status (see BranchStatus).
    branch_status: BranchStatus = BranchStatus.ACTIVE_HISTORY
    #: Short text excerpt for indexes (kept small; full text stays in `text`).
    raw_excerpt: str | None = None
    #: ``HIGH`` when the event was built from a primary record directly;
    #: ``MEDIUM`` when cross-linked from a secondary source; ``LOW`` when
    #: reconstructed/inferred.
    parse_confidence: str = "HIGH"

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_event(
        cls,
        ev: Event,
        *,
        event_id: str,
        source_file: str,
        canonical_type: CanonicalEventType,
        actor: str,
        branch_status: BranchStatus = BranchStatus.ACTIVE_HISTORY,
        turn_index: int | None = None,
        sequence_index: int = 0,
        timestamp: str | None = None,
        tool_name: str | None = None,
        command: str | None = None,
        working_directory: str | None = None,
        stdout_excerpt: str | None = None,
        stderr_excerpt: str | None = None,
        exit_code: int | None = None,
        duration_ms: int | None = None,
        paths: tuple[str, ...] = (),
        model: str | None = None,
        provider: str | None = None,
        parse_confidence: str = "HIGH",
    ) -> "CanonicalEvent":
        """Build a CanonicalEvent from an existing Event (preserves all
        Event fields and adds canonical metadata)."""
        return cls(
            # Event fields (inherited)
            index=ev.index,
            role=ev.role,
            text=ev.text,
            tool_calls=ev.tool_calls,
            tool_call_id=ev.tool_call_id,
            synthetic_reason=ev.synthetic_reason,
            prompt_index=ev.prompt_index,
            model_id=ev.model_id or model,
            reasoning_effort=ev.reasoning_effort,
            reasoning_status=ev.reasoning_status,
            source_path=ev.source_path,
            raw_line_number=ev.raw_line_number,
            parse_warnings=ev.parse_warnings,
            # Canonical fields
            event_id=event_id,
            source_file=source_file,
            source_line_or_offset=ev.raw_line_number,
            source_record_id=None,
            turn_index=turn_index if turn_index is not None else ev.prompt_index,
            sequence_index=sequence_index,
            timestamp=timestamp,
            actor=actor,
            canonical_type=canonical_type,
            tool_name=tool_name,
            command=command,
            working_directory=working_directory,
            stdout_excerpt=stdout_excerpt,
            stderr_excerpt=stderr_excerpt,
            exit_code=exit_code,
            duration_ms=duration_ms,
            paths=paths,
            model=model or ev.model_id,
            provider=provider,
            branch_status=branch_status,
            raw_excerpt=_excerpt(ev.text),
            parse_confidence=parse_confidence,
        )

    # ------------------------------------------------------------------
    # Ordering
    # ------------------------------------------------------------------

    def sort_key(self) -> tuple[int, int, int, int]:
        """Deterministic ordering key. Used by the normalizer.

        Order: turn_index → sequence_index → source_file rank → source line.
        Events with no turn_index sort last (turn = sys.maxsize).
        """
        import sys

        turn = self.turn_index if self.turn_index is not None else sys.maxsize
        src_rank = SOURCE_ORDER.get(self.source_file, 99)
        return (turn, self.sequence_index, src_rank, self.source_line_or_offset)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_canonical_dict(self) -> dict[str, Any]:
        """Serialise for canonical-events.jsonl. Includes all spec fields."""
        return {
            "event_id": self.event_id,
            "source_file": self.source_file,
            "source_line_or_offset": self.source_line_or_offset,
            "source_record_id": self.source_record_id,
            "turn_index": self.turn_index,
            "sequence_index": self.sequence_index,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "event_type": self.canonical_type.value,
            "tool_name": self.tool_name,
            "command": self.command,
            "working_directory": self.working_directory,
            "arguments": _tool_args_dict(self),
            "stdout_excerpt": self.stdout_excerpt,
            "stderr_excerpt": self.stderr_excerpt,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "paths": list(self.paths),
            "session_id": None,  # filled by normalizer (session-scoped)
            "terminal_id": None,  # filled by normalizer
            "model": self.model,
            "provider": self.provider,
            "branch_status": self.branch_status.value,
            "raw_excerpt": self.raw_excerpt,
            "parse_confidence": self.parse_confidence,
            # Also include the inherited Event index for traceability
            "stream_index": self.index,
            "role": self.role.value,
            "parse_warnings": list(self.parse_warnings),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _excerpt(text: str | None, limit: int = 240) -> str | None:
    if text is None:
        return None
    if len(text) <= limit:
        return text
    return text[:limit] + "...<+" + str(len(text) - limit) + ">"


def _tool_args_dict(ev: CanonicalEvent) -> dict[str, Any]:
    """Flatten tool_call arguments for the canonical record.

    For assistant events with one tool call, returns that call's arguments.
    For multi-call events, returns ``{"_multi": [...]}`` so callers can
    still retrieve every call. For non-assistant events, returns ``{}``.
    """
    if not ev.tool_calls:
        return {}
    if len(ev.tool_calls) == 1:
        return dict(ev.tool_calls[0].arguments)
    return {"_multi": [tc.to_dict() for tc in ev.tool_calls]}
