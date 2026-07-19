"""Typed event primitives for the /check deterministic transcript preprocessor.

This module is the foundation of the preprocessor. It defines the canonical,
immutable representation of a parsed transcript that every other module
(``transcript_parser``, ``detectors``, ``evidence_packet``,
``output_validator``) consumes.

Scope
-----
This module is **check-local and self-contained**. It does NOT import from
``aar/__lib/`` so that ``/check`` keeps working regardless of any parallel
work on ``/aar``. The design is informed by the prior session's
``aar/__lib/event_model.py`` (frozen dataclasses, honest absence, forward-
slash paths) but scoped to what ``/check`` needs: claim verification, not
causal synthesis.

Design invariants
-----------------
* **Determinism.** Every field that influences a downstream signal is either
  copied verbatim from the source transcript or derived deterministically
  from line order. Nothing here depends on wall-clock time, randomness, or
  external state. The LLM is responsible for verdicts; this module only
  carries objective structure that a verifier subagent can cite.
* **Honesty about absence.** Grok ``chat_history.jsonl`` records do not carry
  timestamps (verified against a real 1197-line session: 0 records with a
  timestamp field). We expose ``has_timestamps`` as an explicit boolean
  rather than fabricating times.
* **Immutability (shallow).** ``Event``, ``ToolCall``, ``Transcript`` are
  frozen dataclasses — field reassignment is blocked. Nested mutable values
  (notably ``ToolCall.arguments: dict``) are NOT deep-frozen; a consumer
  that mutates ``tc.arguments["x"] = 1`` would change the parsed data.
  Detectors must treat these values as read-only by convention. If true
  deep-immutability is ever required, wrap with ``types.MappingProxyType``.
* **Forward-slash paths only.** All ``source_path`` values use ``/`` to
  avoid Windows backslash corruption at JSON boundaries (per repo
  windows-filesystem rule).

This module intentionally does **not** parse transcripts or detect signals —
see ``transcript_parser`` and ``detectors`` respectively.

Verified JSONL contract (from session 019f6c3b-*, 1197 lines)
-------------------------------------------------------------
| type        | count | keys                                                       |
|-------------|-------|------------------------------------------------------------|
| system      |     1 | type, content (String)                                     |
| user        |    86 | type, content (String OR list[{type:"text",text}])         |
| assistant   |   451 | type, content, tool_calls?, model_id, reasoning_effort     |
| tool_result |   542 | type, tool_call_id, content (String)                       |
| reasoning   |   117 | type, id, summary, encrypted_content, status?              |

Reasoning records have **no** ``content`` field — ``Event.text`` for
reasoning events is sourced from ``summary``. Only 55/117 reasoning records
carry a ``status`` field.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any

__all__ = [
    "Role",
    "SourceStatus",
    "ToolCall",
    "Event",
    "ParseStats",
    "Transcript",
    "PACKET_SCHEMA_VERSION",
    "CHECK_VERDICTS",
    "CHECK_ISSUE_SEVERITIES",
]

# Bumped whenever the on-disk evidence-packet schema changes in a way that
# breaks consumers. Consumers MUST refuse packets with an unknown schema.
PACKET_SCHEMA_VERSION = "1.0"

# --- /check contract vocabulary (mirrors of check/SKILL.md) ---
# These are the authoritative value sets the output_validator enforces for
# any verifier-subagent output that the packet references. They are
# duplicated here (not imported from SKILL.md, which is markdown) so the
# validator has a single executable source of truth.

#: Verifier verdicts from check/SKILL.md VERDICT section.
CHECK_VERDICTS: tuple[str, ...] = ("PASS", "FAIL")

#: Issue severities from check/SKILL.md Issue section.
CHECK_ISSUE_SEVERITIES: tuple[str, ...] = (
    "bug",
    "gap",
    "regression",
    "suggestion",
)


class Role(str, Enum):
    """Canonical speaker role for a transcript line.

    Values are the literal strings used in Grok ``chat_history.jsonl`` so
    that ``Role(raw_type)`` succeeds for well-formed input. ``REASONING`` is
    distinct from ``ASSISTANT`` because Grok emits chain-of-thought as a
    separate record type (verified: 117 reasoning records vs 451 assistant).
    """

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    REASONING = "reasoning"
    TOOL_RESULT = "tool_result"
    #: Used when a line has an unrecognised ``type`` field. The line is kept
    #: (so accounting stays honest) but flagged via ``parse_warnings``.
    UNKNOWN = "unknown"

    @classmethod
    def from_raw(cls, raw: Any) -> "Role":
        """Map a raw ``type`` value to a Role, falling back to UNKNOWN.

        Returns ``Role.UNKNOWN`` for ``None`` or unrecognised strings; never
        raises. Callers should treat UNKNOWN as a parse-quality signal.
        """
        if isinstance(raw, str):
            try:
                return cls(raw)
            except ValueError:
                return cls.UNKNOWN
        return cls.UNKNOWN


class SourceStatus(str, Enum):
    """How complete is the transcript evidence?

    /check consumes the same three-way classification as /aar Step 0.2 so a
    verifier subagent can be told "this transcript is partial — do not claim
    exhaustive trace coverage."

    * ``COMPLETE``   — full transcript, clear boundaries, no gaps.
    * ``PARTIAL``    — compacted/truncated/missing segments. Verifiable, but
      the verifier must NOT claim exhaustive trace review.
    * ``UNVERIFIED`` — cannot confirm what the source represents.
    """

    COMPLETE = "SOURCE_COMPLETE"
    PARTIAL = "SOURCE_PARTIAL"
    UNVERIFIED = "SOURCE_UNVERIFIED"


@dataclass(frozen=True)
class ToolCall:
    """A single tool invocation issued by the assistant.

    ``arguments`` is the parsed JSON dict (empty dict if unparseable). We
    retain ``arguments_raw`` verbatim so detectors and reviewers can cite
    the exact input the model produced, and ``parse_error`` records any JSON
    failure honestly rather than silently dropping the call.
    """

    id: str
    name: str
    arguments: dict[str, Any]
    arguments_raw: str
    parse_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "arguments": self.arguments,
            "arguments_raw": self.arguments_raw,
            "parse_error": self.parse_error,
        }


@dataclass(frozen=True)
class Event:
    """One transcript line, normalised.

    Exactly the fields the preprocessor can establish mechanically. No
    inferred fields (no severity, no verdict, no claim) — those belong to
    the LLM verifier stage.

    The ``index`` field is the canonical 0-based position of the event in
    the parsed stream and is the value detectors cite in
    ``Signal.event_indices``. It is stable: re-parsing the same file yields
    the same indices.
    """

    index: int
    role: Role
    #: Populated for assistant text, user text, tool_result content, and the
    #: reasoning summary. ``None`` only when the source had no textual
    #: payload at all.
    text: str | None
    #: Assistant only. Tuple so the event stays hashable/frozen.
    tool_calls: tuple[ToolCall, ...] = ()
    #: tool_result only — joins to ``ToolCall.id`` on the producing assistant
    #: event.
    tool_call_id: str | None = None
    #: user only — set when the record was synthetically injected by the
    #: harness (e.g. ``<system-reminder>``, ``<user_info>``,
    #: ``<git_status>``). Real user prompts have ``synthetic_reason is None``.
    synthetic_reason: str | None = None
    #: assistant only — model id (e.g. ``grok-4.5``).
    model_id: str | None = None
    #: assistant only — reasoning effort if recorded.
    reasoning_effort: str | None = None
    #: reasoning only — terminal status (e.g. ``completed``). Often absent.
    reasoning_status: str | None = None
    #: Provenance — forward-slash path of the source file.
    source_path: str = ""
    #: 1-based line number in the source file (matches editor conventions).
    raw_line_number: int = 0
    #: Non-fatal issues discovered while building this event (e.g. unknown
    #: role, malformed tool args). Each detector/consumer may consult this.
    parse_warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "role": self.role.value,
            "text": self.text,
            "tool_calls": [tc.to_dict() for tc in self.tool_calls],
            "tool_call_id": self.tool_call_id,
            "synthetic_reason": self.synthetic_reason,
            "model_id": self.model_id,
            "reasoning_effort": self.reasoning_effort,
            "reasoning_status": self.reasoning_status,
            "source_path": self.source_path,
            "raw_line_number": self.raw_line_number,
            "parse_warnings": list(self.parse_warnings),
        }


@dataclass(frozen=True)
class ParseStats:
    """Honest accounting of what the parser saw.

    A reconciled ``ParseStats`` proves only that the parser counted lines
    consistently — not that classification was correct, not that signals
    are valid. Mirrors the AAR accounting disclaimer: arithmetic
    consistency is not analytical correctness.
    """

    total_lines: int = 0
    parsed_events: int = 0
    skipped_blank: int = 0
    skipped_malformed: int = 0
    by_role: dict[str, int] = field(default_factory=dict)
    synthetic_user_messages: int = 0
    real_user_messages: int = 0
    tool_calls_total: int = 0
    tool_calls_with_parse_error: int = 0
    tool_results_orphaned: int = 0  #: tool_result with no matching tool_call.id
    unknown_role_lines: int = 0
    has_timestamps: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_lines": self.total_lines,
            "parsed_events": self.parsed_events,
            "skipped_blank": self.skipped_blank,
            "skipped_malformed": self.skipped_malformed,
            "by_role": dict(self.by_role),
            "synthetic_user_messages": self.synthetic_user_messages,
            "real_user_messages": self.real_user_messages,
            "tool_calls_total": self.tool_calls_total,
            "tool_calls_with_parse_error": self.tool_calls_with_parse_error,
            "tool_results_orphaned": self.tool_results_orphaned,
            "unknown_role_lines": self.unknown_role_lines,
            "has_timestamps": self.has_timestamps,
            "warnings": list(self.warnings),
        }

    def reconciles(self) -> bool:
        """Arithmetic check: parsed + skipped_malformed == total non-blank input.

        ``skipped_blank`` is excluded because blank lines are file
        formatting, not transcript events.
        """
        return self.parsed_events + self.skipped_malformed == (
            self.total_lines - self.skipped_blank
        )


@dataclass(frozen=True)
class Transcript:
    """A fully parsed transcript ready for deterministic signal extraction.

    Frozen and tuple-backed so it can be safely shared across detectors
    without copying. Provenance (``source_path``, ``source_status``) travels
    with the data so the evidence packet can cite it without re-reading disk.
    """

    events: tuple[Event, ...]
    source_path: str
    source_status: SourceStatus
    parse_stats: ParseStats
    #: Identity derived from the transcript path, not invented. ``None`` when
    #: the path did not encode a session id (e.g. ad-hoc fixture).
    session_id: str | None = None

    def event_by_index(self, index: int) -> Event | None:
        """Fetch an event by its canonical index, or ``None`` if out of range.

        Events are stored in index order, so this is a direct lookup. Used
        by consumers that need to resolve ``Signal.event_indices`` back to
        text.
        """
        if 0 <= index < len(self.events):
            return self.events[index]
        return None

    def replace(
        self,
        *,
        events: tuple[Event, ...] | None = None,
        source_path: str | None = None,
        source_status: SourceStatus | None = None,
        parse_stats: ParseStats | None = None,
        session_id: str | None = None,
    ) -> "Transcript":
        """Return a copy with selected fields replaced (frozen-friendly)."""
        return replace(
            self,
            events=events if events is not None else self.events,
            source_path=source_path if source_path is not None else self.source_path,
            source_status=source_status if source_status is not None else self.source_status,
            parse_stats=parse_stats if parse_stats is not None else self.parse_stats,
            session_id=session_id if session_id is not None else self.session_id,
        )
