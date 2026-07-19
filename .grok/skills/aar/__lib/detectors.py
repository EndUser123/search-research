"""Deterministic signal detectors over a parsed ``Transcript``.

Each detector is a pure function ``events -> list[Signal]``. Together they
form a registry run by ``run_all_detectors``. The output feeds
``evidence_packet.build_evidence_packet`` and is the LLM-facing evidence base.

Design contract (read before adding a detector)
-----------------------------------------------
1. **Conservative by default.** A detector should favour precision over
   recall. A missed signal is recoverable (the LLM still has the transcript);
   a fabricated signal biases the whole AAR. When uncertain, raise the
   threshold or mark severity ``INFO``.
2. **No causal claims.** A ``Signal`` documents an observed pattern only.
   ``severity`` is *mechanical* strength (how clearly the pattern is present),
   not causal confidence, not "how bad it was". Causal interpretation is the
   LLM's job.
3. **Every signal carries a falsifier.** The ``falsifier`` field states what
   observation would make this signal not-a-real-finding. The LLM (and any
   reviewer) uses it to challenge the signal. A signal without a meaningful
   falsifier is overclaiming.
4. **Deterministic citations.** ``event_indices`` are the canonical 0-based
   ``Event.index`` values. Re-running on the same transcript yields identical
   signals. No wall-clock, no randomness, no external state.
5. **Pure & stateless.** Detectors must not read disk, env, or globals.

Adding a detector
-----------------
* Implement ``detect_<name>(events) -> list[Signal]``.
* Append it to ``ALL_DETECTORS``.
* Add at least one positive and one negative test in ``test_detectors.py``
  plus a check that the signal's ``falsifier`` is non-empty.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Iterable

from event_model import Event, Role

from interaction_quality import (
    EVIDENCE_CEILING_RE,
    PROCEDURE_CITATION_RE,
    USER_PUSHBACK_RE,
    has_evidence_ceiling_phrase,
    has_user_pushback_phrase,
    procedure_citation_count,
)

__all__ = [
    "SignalKind",
    "SignalSeverity",
    "Signal",
    "DetectorResult",
    "ALL_DETECTORS",
    "run_all_detectors",
    "detect_repeated_identical_tool_calls",
    "detect_repeated_tool_name_windows",
    "detect_tool_result_errors",
    "detect_empty_tool_results",
    "detect_repeated_file_edits",
    "detect_file_edit_reversals",
    "detect_assistant_self_corrections",
    "detect_user_corrections",
    "detect_unanswered_user_questions",
    "detect_long_tool_chains",
    "detect_unexpected_role_order",
    "detect_tool_arg_parse_failures",
    "detect_orphaned_tool_results",
]


class SignalKind(str, Enum):
    """Mechanically detectable signal categories.

    Names are stable identifiers that appear in the evidence packet and may
    be referenced by the LLM. Do not rename without bumping
    ``PACKET_SCHEMA_VERSION``.

    The ``OPPORTUNITY_CANDIDATE_*`` kinds (spec Section 19) are deliberately
    separate from the failure-shaped kinds: they emit *candidates* for the
    LLM to interpret as opportunities, never final opportunity decisions.
    """

    REPEATED_IDENTICAL_TOOL_CALL = "repeated_identical_tool_call"
    REPEATED_TOOL_NAME_WINDOW = "repeated_tool_name_window"
    TOOL_RESULT_ERROR = "tool_result_error"
    EMPTY_TOOL_RESULT = "empty_tool_result"
    REPEATED_FILE_EDIT = "repeated_file_edit"
    FILE_EDIT_REVERSAL = "file_edit_reversal"
    ASSISTANT_SELF_CORRECTION = "assistant_self_correction"
    USER_CORRECTION = "user_correction"
    UNANSWERED_USER_QUESTION = "unanswered_user_question"
    LONG_TOOL_CHAIN = "long_tool_chain"
    UNEXPECTED_ROLE_ORDER = "unexpected_role_order"
    TOOL_ARG_PARSE_FAILURE = "tool_arg_parse_failure"
    ORPHANED_TOOL_RESULT = "orphaned_tool_result"
    # Opportunity-candidate signals (spec Section 19). Each is a hint for the
    # LLM; each carries a falsifier and is neutral about whether the candidate
    # is a real opportunity.
    OPPORTUNITY_CANDIDATE_UNCONSUMED_ARTIFACT = "opportunity_candidate_unconsumed_artifact"
    OPPORTUNITY_CANDIDATE_UNUSED_CAPABILITY = "opportunity_candidate_unused_capability"
    OPPORTUNITY_CANDIDATE_DUPLICATE_CAPABILITY = "opportunity_candidate_duplicate_capability"
    OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION = "opportunity_candidate_recommendation_revision"
    OPPORTUNITY_CANDIDATE_SUCCESSFUL_INTERVENTION = "opportunity_candidate_successful_intervention"
    # Interaction-quality patterns — the deeper-failure layer the LLM lenses
    # over. The detector emits candidate signals; the LLM interprets them.
    OPPORTUNITY_CANDIDATE_OBJECTIVE_DRIFT = "opportunity_candidate_objective_drift"
    OPPORTUNITY_CANDIDATE_POST_FAILURE_CONTINUATION = "opportunity_candidate_post_failure_continuation"
    OPPORTUNITY_CANDIDATE_READING_WITHOUT_SYNTHESIS = "opportunity_candidate_reading_without_synthesis"
    # Interaction-quality deeper-failure signals (spec Section 13).
    OPPORTUNITY_CANDIDATE_CONTINUED_AFTER_UNKNOWN = "opportunity_candidate_continued_after_unknown"
    OPPORTUNITY_CANDIDATE_CORRECTION_PROPAGATION_FAILURE = "opportunity_candidate_correction_propagation_failure"
    OPPORTUNITY_CANDIDATE_PROCEDURE_SATURATION = "opportunity_candidate_procedure_saturation"
    # Operational-safety signals (highest-severity; spec Section 6A-B).
    DESTRUCTIVE_WRITE_WITHOUT_READ = "destructive_write_without_read"
    SECRET_EXPOSURE_IN_TOOL_OUTPUT = "secret_exposure_in_tool_output"
    USER_PASTE_SECRET_WARNING = "user_paste_secret_warning"


class SignalSeverity(str, Enum):
    """Mechanical strength of the observed pattern. NOT causal confidence."""

    INFO = "INFO"        #: structural note, no failure implied
    LOW = "LOW"          #: weak / could be benign
    MEDIUM = "MEDIUM"    #: clear pattern, likely meaningful
    HIGH = "HIGH"        #: strong raw pattern


@dataclass(frozen=True)
class Signal:
    """One deterministic observation about the transcript.

    Fields are deliberately minimal and structured so the evidence packet can
    serialise, hash, and account for them deterministically.
    """

    kind: SignalKind
    #: 0-based Event.index values supporting this signal. Always non-empty.
    event_indices: tuple[int, ...]
    #: One-line objective description (no causal claim).
    detail: str
    severity: SignalSeverity
    #: Detector function name (provenance for the packet).
    detector: str
    #: What observation would make this signal NOT a real finding.
    falsifier: str
    #: Optional deterministic key the detector used for grouping (e.g. the
    #: arg-hash for repeated calls, the file_path for repeated edits). Lets
    #: the LLM cluster without re-deriving it. May be None.
    group_key: str | None = None

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "event_indices": list(self.event_indices),
            "detail": self.detail,
            "severity": self.severity.value,
            "detector": self.detector,
            "falsifier": self.falsifier,
            "group_key": self.group_key,
        }


DetectorResult = list[Signal]
Detector = Callable[[Iterable[Event]], DetectorResult]


# ---------------------------------------------------------------------------
# Tunable thresholds (constants — every threshold needs a justification)
# ---------------------------------------------------------------------------

#: Repeated identical tool calls: <2 means "no repeat". Keep at 2 (the minimum
#: evidence of repetition). Higher would hide loops.
_REPEAT_IDENTICAL_MIN = 2

#: Repeated tool name in a sliding window. 3 same-name calls back-to-back is
#: the canonical N+1 / pagination shape. 2 would over-fire on benign pairs.
_REPEAT_TOOL_NAME_WINDOW = 3

#: Window size for the repeated-tool-name detector. Small enough to stay
#: local (genuinely back-to-back), large enough to tolerate interleaved
#: tool_result records between assistant turns.
_REPEAT_TOOL_NAME_WINDOW_SPAN = 6

#: Tools where repetition is a candidate defect (mutating, side-effecting, or
#: expensive). Pure-read tools (read_file, list_dir, grep, web_search, etc.)
#: are excluded because repeating them is normal exploratory behaviour. This
#: list is the precision gate for ``detect_repeated_tool_name_windows``.
_REPEAT_SUSPECT_TOOLS = frozenset(
    {
        "write",
        "edit",
        "search_replace",
        "run_terminal_command",
        "run_command",
        "bash",
    }
)

#: Long tool chain threshold. ≥8 tool calls in one assistant turn is unusual
#: for normal work and worth an INFO flag. Not a defect by itself.
_LONG_TOOL_CHAIN_MIN = 8

#: Repeated file edits to the same path. 3 same-path writes is strong
#: evidence of thrashing; 2 can be legitimate (write then small fix).
_REPEATED_FILE_EDIT_MIN = 3

#: Self-correction text markers. Lowercase, word-boundary matched.
_SELF_CORRECTION_PATTERNS = (
    r"\bwait,",
    r"\bactually,",
    r"\blet me reconsider\b",
    r"\bi was wrong\b",
    r"\bmy mistake\b",
    r"\bignore that\b",
    r"\bthat(?:'s| is) (?:wrong|incorrect|not right)\b",
    r"\bsorry, i (?:made|got) (?:a|an) (?:mistake|error)\b",
)
_SELF_CORRECTION_RE = re.compile(
    "|".join(_SELF_CORRECTION_PATTERNS), re.IGNORECASE
)

#: User correction markers in real (non-synthetic) user messages.
_USER_CORRECTION_PATTERNS = (
    r"^\s*no[,\s]",
    r"^\s*stop\b",
    r"\bnot what i meant\b",
    r"\bthat(?:'s| is) (?:wrong|not what i wanted|not right)\b",
    r"\bundo\b",
    r"\brevert\b",
    r"\bdon't\b.*\binstead\b",
    r"\bi (?:actually|really) wanted\b",
    # Live-eval additions (2026-07-18): imperative corrections and
    # didn't-work reports are real user corrections the original patterns missed.
    r"\bdidn't work\b",
    r"\bdid not work\b",
    r"\bdoesn't work\b",
    r"\bset it back\b",
    r"\bchange it back\b",
    r"\bput it back\b",
    r"\bthat's not\b",
    r"\bnot correct\b",
    r"\bincorrect\b",
)
_USER_CORRECTION_RE = re.compile(
    "|".join(_USER_CORRECTION_PATTERNS), re.IGNORECASE
)

#: Tool-result error markers. Conservative: require an explicit marker, never
#: infer from tone. Bare words like ``fail``/``exception``/``failure`` are
#: intentionally excluded — they match discussion-of-failure (test reports,
#: docs, "fail-fast") rather than the tool itself failing. We require markers
#: that almost always indicate the tool operation did not succeed.
_TOOL_ERROR_PATTERNS = (
    r"(?:^|\n)\s*error:",
    r"traceback \(most recent call last\)",
    r"exit code: ?[1-9]",
    r"exit code [1-9]\b",
    r"\bcommand not found\b",
    r"\bno such file or directory\b",
    r"\bpermission denied\b",
    r"\bnot recognized\b",
    r"\bfatal:\s",
    r"\berrno\b",
    r"\bsegfault\b",
    r"\bcore dumped\b",
)
_TOOL_ERROR_RE = re.compile("|".join(_TOOL_ERROR_PATTERNS), re.IGNORECASE)

#: Tools that target a file path (for repeated-edit detection). Names match
#: the tool names observed in Grok transcripts.
_FILE_TARGETING_TOOLS = ("write", "edit", "search_replace")
#: Argument keys that carry the targeted file path, per tool.
_FILE_PATH_ARG_KEYS = ("file_path", "target_file", "path")

#: Tools that perform destructive git operations on a path.
_GIT_REVERT_COMMAND_RE = re.compile(
    r"\bgit\s+(?:checkout|reset|restore|stash|clean)\b.*?(?:--\s*)?(\S+\.\S+)?",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _arg_hash(name: str, arguments: dict) -> str:
    """Stable hash of a tool call's identity for duplicate detection.

    Includes the tool name so a write and a read with identical args don't
    collapse. Uses sorted JSON for determinism.
    """
    blob = json.dumps({"name": name, "args": arguments}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _file_path_from_call(name: str, arguments: dict) -> str | None:
    """Extract the targeted file path from a tool call, normalised.

    Returns the path with forward slashes only, or None if no recognised key
    is present. Used by repeated-edit and reversal detectors.
    """
    if name not in _FILE_TARGETING_TOOLS:
        return None
    for key in _FILE_PATH_ARG_KEYS:
        if key in arguments and isinstance(arguments[key], str) and arguments[key]:
            return arguments[key].replace("\\", "/").lower()
    return None


def _assistant_turns(events: list[Event]):
    """Yield (event, tool_calls) for each assistant event that emitted calls."""
    for ev in events:
        if ev.role is Role.ASSISTANT and ev.tool_calls:
            yield ev


# ---------------------------------------------------------------------------
# Detectors
# ---------------------------------------------------------------------------


def detect_repeated_identical_tool_calls(events: list[Event]) -> DetectorResult:
    """Flag identical tool calls (same name + same arguments) repeated ≥2 times.

    Strong indicator of a retry loop, a stuck agent, or genuine N+1. The
    falsifier distinguishes legitimate retries (different args) from loops.
    """
    out: list[Signal] = []
    by_hash: dict[str, list[tuple[Event, int]]] = {}
    for ev in _assistant_turns(events):
        for ci, tc in enumerate(ev.tool_calls):
            if tc.parse_error:
                continue  # cannot meaningfully hash; reported elsewhere
            h = _arg_hash(tc.name, tc.arguments)
            by_hash.setdefault(h, []).append((ev, ci))

    for h, occ in by_hash.items():
        if len(occ) < _REPEAT_IDENTICAL_MIN:
            continue
        indices = tuple(e.index for e, _ in occ)
        # Live-eval-fix (2026-07-18): use the Event object we already have rather
        # than `events[ev.index]` lookup — after normalizer sort by sort_key(),
        # list-position != Event.index, which caused IndexError on Session B.
        if occ[0][1] < len(occ[0][0].tool_calls):
            name = occ[0][0].tool_calls[occ[0][1]].name
        else:
            name = None
        name_str = name or "<unknown>"
        out.append(
            Signal(
                kind=SignalKind.REPEATED_IDENTICAL_TOOL_CALL,
                event_indices=indices,
                detail=f"tool {name_str!r} called {len(occ)}x with identical arguments",
                severity=SignalSeverity.MEDIUM,
                detector="detect_repeated_identical_tool_calls",
                group_key=h,
                falsifier=(
                    "the calls differ in arguments the hash does not capture "
                    "(e.g. side-effecting state) or were legitimate retries "
                    "after an externally-cleared failure"
                ),
            )
        )
    return out


def detect_repeated_tool_name_windows(events: list[Event]) -> DetectorResult:
    """Flag the same tool name appearing ≥3 times within a small window.

    Captures pagination / N+1 shapes that identical-args misses (each call
    has slightly different args but the same tool). Window is measured over
    the flat event stream to tolerate interleaved tool_result records.
    """
    out: list[Signal] = []
    # Build a per-event tool-name sequence restricted to mutating/expensive
    # tools. Pure-read tools are excluded because their repetition is normal
    # exploratory behaviour (reading several files, grepping several patterns).
    seq: list[tuple[int, str]] = []
    for ev in _assistant_turns(events):
        for tc in ev.tool_calls:
            if tc.name in _REPEAT_SUSPECT_TOOLS:
                seq.append((ev.index, tc.name))
    # Sliding window over tool-call positions (not raw event positions).
    span = _REPEAT_TOOL_NAME_WINDOW_SPAN
    i = 0
    seen_groups: set[str] = set()
    while i < len(seq):
        window = seq[i : i + span]
        if not window:
            break
        counts: dict[str, list[tuple[int, ...]]] = {}
        for ev_idx, name in window:
            counts.setdefault(name, []).append(ev_idx)
        fired = False
        for name, idx_list in counts.items():
            if len({idx for idx in idx_list}) >= _REPEAT_TOOL_NAME_WINDOW:
                group = f"{name}@{i}"
                if group in seen_groups:
                    continue
                seen_groups.add(group)
                out.append(
                    Signal(
                        kind=SignalKind.REPEATED_TOOL_NAME_WINDOW,
                        event_indices=tuple(dict.fromkeys(idx_list)),
                        detail=(
                            f"tool {name!r} appears {len(idx_list)}x within "
                            f"{span} consecutive tool calls"
                        ),
                        severity=SignalSeverity.LOW,
                        detector="detect_repeated_tool_name_windows",
                        group_key=group,
                        falsifier=(
                            "the calls serve genuinely different purposes "
                            "(e.g. sequential independent reads) rather than "
                            "an iteration/pagination loop"
                        ),
                    )
                )
                fired = True
        if fired:
            i += span  # skip past this window to avoid overlapping duplicates
        else:
            i += 1
    return out


def detect_tool_result_errors(events: list[Event]) -> DetectorResult:
    """Flag tool_result records containing explicit error markers.

    Conservative: requires a literal error pattern (``Error:``, ``Traceback``,
    non-zero exit code, etc.). Does not interpret tone. One signal per
    offending result so the LLM can cite each independently.
    """
    out: list[Signal] = []
    for ev in events:
        if ev.role is not Role.TOOL_RESULT:
            continue
        text = ev.text or ""
        if not text.strip():
            continue  # handled by empty-result detector
        m = _TOOL_ERROR_RE.search(text)
        if not m:
            continue
        snippet = m.group(0).strip()
        out.append(
            Signal(
                kind=SignalKind.TOOL_RESULT_ERROR,
                event_indices=(ev.index,),
                detail=f"tool_result contains error marker {snippet!r}",
                severity=SignalSeverity.MEDIUM,
                detector="detect_tool_result_errors",
                falsifier=(
                    "the marker appears inside quoted/expected output rather "
                    "than indicating the tool itself failed"
                ),
            )
        )
    return out


def detect_empty_tool_results(events: list[Event]) -> DetectorResult:
    """Flag tool_result records with empty/whitespace-only content.

    Empty results frequently indicate silent failure (especially for
    read/grep/list operations). One signal per occurrence.
    """
    out: list[Signal] = []
    for ev in events:
        if ev.role is not Role.TOOL_RESULT:
            continue
        if ev.text is None or not ev.text.strip():
            out.append(
                Signal(
                    kind=SignalKind.EMPTY_TOOL_RESULT,
                    event_indices=(ev.index,),
                    detail="tool_result has empty content",
                    severity=SignalSeverity.LOW,
                    detector="detect_empty_tool_results",
                    falsifier=(
                        "the tool legitimately produced no output (e.g. a "
                        "successful no-op grep with no matches)"
                    ),
                )
            )
    return out


def detect_repeated_file_edits(events: list[Event]) -> DetectorResult:
    """Flag the same file path written/edited ≥3 times.

    Three or more writes to one path is a thrashing signal (write→fail→rewrite
    cycles). Two is allowed because legitimate write-then-small-fix is common.
    Counts every individual tool call (not per-event), so one assistant turn
    that writes the same path 3× still fires — that is genuine thrashing.
    """
    out: list[Signal] = []
    # path -> list of (event_index, call_index_within_event) occurrences.
    by_path: dict[str, list[tuple[int, int]]] = {}
    for ev in _assistant_turns(events):
        for ci, tc in enumerate(ev.tool_calls):
            fp = _file_path_from_call(tc.name, tc.arguments)
            if fp:
                by_path.setdefault(fp, []).append((ev.index, ci))
    for fp, occ in by_path.items():
        if len(occ) < _REPEATED_FILE_EDIT_MIN:
            continue
        # Cite the distinct event indices (deduped, order-preserving).
        ev_indices: list[int] = []
        for e_idx, _ in occ:
            if e_idx not in ev_indices:
                ev_indices.append(e_idx)
        out.append(
            Signal(
                kind=SignalKind.REPEATED_FILE_EDIT,
                event_indices=tuple(ev_indices),
                detail=f"file edited {len(occ)}x: {fp}",
                severity=SignalSeverity.MEDIUM,
                detector="detect_repeated_file_edits",
                group_key=fp,
                falsifier=(
                    "each edit was a distinct, intended change rather than a "
                    "rewrite of the same content after a failure"
                ),
            )
        )
    return out


def detect_file_edit_reversals(events: list[Event]) -> DetectorResult:
    """Flag file edits that were later reverted by a destructive git command.

    Detects the shape: ``write/edit/search_replace`` to path P, followed
    later by ``run_terminal_command`` invoking ``git checkout/reset/restore/
    stash/clean`` mentioning P. Conservative precision gates:

    * the candidate path must be **explicitly extracted** from the command
      (quoted, after ``--``, or as a standalone path token), never inferred
      from substring overlap;
    * matching requires an **exact normalized basename match** (or exact
      full-path match) — substring matching caused mass false positives;
    * one signal per write_path (consolidated), citing the first write and
      the first matching revert — not one signal per (write, revert) pair.
    """
    out: list[Signal] = []
    # Collect (event_index, normalised_path) for every file write, in order.
    writes: list[tuple[int, str]] = []
    for ev in _assistant_turns(events):
        for tc in ev.tool_calls:
            fp = _file_path_from_call(tc.name, tc.arguments)
            if fp:
                writes.append((ev.index, fp))

    if not writes:
        return out

    # Build a map: normalised_basename -> list of (write_index, full_path).
    by_basename: dict[str, list[tuple[int, str]]] = {}
    for w_idx, w_path in writes:
        by_basename.setdefault(w_path.rsplit("/", 1)[-1], []).append((w_idx, w_path))

    # Track which basenames have already fired to consolidate one signal per path.
    fired_paths: set[str] = set()
    for ev in events:
        if ev.role is not Role.ASSISTANT:
            continue
        for tc in ev.tool_calls:
            if tc.name != "run_terminal_command":
                continue
            cmd = tc.arguments.get("command", "") if isinstance(tc.arguments.get("command"), str) else ""
            if not cmd or not _GIT_REVERT_COMMAND_RE.search(cmd):
                continue
            mentioned = _paths_mentioned_in_command(cmd)
            for mentioned_path in mentioned:
                mentioned_base = mentioned_path.rsplit("/", 1)[-1]
                # Skip generic / everything flags ("." or "--all" etc).
                if mentioned_base in (".", "", "all"):
                    continue
                candidates = by_basename.get(mentioned_base, [])
                for w_idx, w_path in candidates:
                    if w_idx >= ev.index:
                        continue  # revert must come after the write
                    if w_path in fired_paths:
                        continue
                    if not _exact_path_match(w_path, mentioned_path):
                        continue
                    fired_paths.add(w_path)
                    out.append(
                        Signal(
                            kind=SignalKind.FILE_EDIT_REVERSAL,
                            event_indices=(w_idx, ev.index),
                            detail=(
                                f"file {w_path} edited then later targeted by "
                                f"a destructive git command"
                            ),
                            severity=SignalSeverity.HIGH,
                            detector="detect_file_edit_reversals",
                            group_key=w_path,
                            falsifier=(
                                "the git command targeted a different file with "
                                "the same basename in another directory, or "
                                "operated on a fresh copy rather than undoing "
                                "the earlier edit"
                            ),
                        )
                    )
    return out


def detect_assistant_self_corrections(events: list[Event]) -> DetectorResult:
    """Flag assistant messages containing self-correction phrases.

    Captures mid-stream model reversals ("wait,", "actually,", "I was wrong").
    These are objective text patterns; their *significance* is the LLM's call.
    """
    out: list[Signal] = []
    for ev in events:
        if ev.role is not Role.ASSISTANT or not ev.text:
            continue
        m = _SELF_CORRECTION_RE.search(ev.text)
        if not m:
            continue
        out.append(
            Signal(
                kind=SignalKind.ASSISTANT_SELF_CORRECTION,
                event_indices=(ev.index,),
                detail=f"assistant self-correction marker {m.group(0).strip()!r}",
                severity=SignalSeverity.LOW,
                detector="detect_assistant_self_corrections",
                falsifier=(
                    "the phrase appears in quoted code/output or describes a "
                    "benign course-correction rather than an error caught"
                ),
            )
        )
    return out


def detect_user_corrections(events: list[Event]) -> DetectorResult:
    """Flag real (non-synthetic) user messages that correct the assistant.

    A user correction is a high-authority signal. We require:

    * the message is from a real user (``synthetic_reason is None``);
    * it follows at least one assistant turn (so it can be a correction);
    * it matches a correction marker pattern.

    Synthetic messages (``compaction_meta``, ``project_instructions``) are
    excluded — they are harness-injected, not user intent.
    """
    out: list[Signal] = []
    saw_assistant = False
    for ev in events:
        if ev.role is Role.ASSISTANT:
            saw_assistant = True
            continue
        if ev.role is not Role.USER:
            continue
        if ev.synthetic_reason:
            continue  # harness-injected, not a real user turn
        if not saw_assistant:
            continue  # nothing to correct yet
        if not ev.text:
            continue
        m = _USER_CORRECTION_RE.search(ev.text)
        if not m:
            continue
        out.append(
            Signal(
                kind=SignalKind.USER_CORRECTION,
                event_indices=(ev.index,),
                detail=f"user correction marker {m.group(0).strip()!r}",
                severity=SignalSeverity.HIGH,
                detector="detect_user_corrections",
                falsifier=(
                    "the user is correcting scope/preference rather than a "
                    "factual error, or the marker appears inside a quote"
                ),
            )
        )
    return out


def detect_unanswered_user_questions(events: list[Event]) -> DetectorResult:
    """Flag real user messages ending in '?' with no subsequent assistant turn.

    Conservative: requires (a) a real user message, (b) the *last non-empty
    line* of the text ends in '?', and (c) the next real user message arrives
    before any assistant response. Tool-result interleaving does not count as
    a response.
    """
    out: list[Signal] = []
    n = len(events)
    for i, ev in enumerate(events):
        if ev.role is not Role.USER or ev.synthetic_reason or not ev.text:
            continue
        last_line = next((ln.strip() for ln in reversed(ev.text.splitlines()) if ln.strip()), "")
        if not last_line.endswith("?"):
            continue
        # Scan forward for either an assistant turn (answered) or another real
        # user message (unanswered).
        answered = False
        for j in range(i + 1, n):
            nxt = events[j]
            if nxt.role is Role.ASSISTANT and nxt.text:
                answered = True
                break
            if nxt.role is Role.USER and not nxt.synthetic_reason:
                # Next real user turn arrived first → question was not addressed.
                break
        if not answered:
            out.append(
                Signal(
                    kind=SignalKind.UNANSWERED_USER_QUESTION,
                    event_indices=(ev.index,),
                    detail="user question not followed by an assistant response",
                    severity=SignalSeverity.MEDIUM,
                    detector="detect_unanswered_user_questions",
                    falsifier=(
                        "the question was rhetorical, answered in a later turn "
                        "after the next user message, or addressed by a tool "
                        "result rather than assistant prose"
                    ),
                )
            )
    return out


def detect_long_tool_chains(events: list[Event]) -> DetectorResult:
    """Flag assistant turns that emit ≥8 tool calls at once.

    INFO only — large batches are legitimate for parallel work but worth
    surfacing so the LLM can decide if the volume indicates thrashing.
    """
    out: list[Signal] = []
    for ev in _assistant_turns(events):
        if len(ev.tool_calls) >= _LONG_TOOL_CHAIN_MIN:
            out.append(
                Signal(
                    kind=SignalKind.LONG_TOOL_CHAIN,
                    event_indices=(ev.index,),
                    detail=(
                        f"assistant turn emitted {len(ev.tool_calls)} tool calls"
                    ),
                    severity=SignalSeverity.INFO,
                    detector="detect_long_tool_chains",
                    falsifier=(
                        "the calls are independent parallel work rather than "
                        "a retry/loop"
                    ),
                )
            )
    return out


def detect_unexpected_role_order(events: list[Event]) -> DetectorResult:
    """Flag structural anomalies in the role sequence.

    Patterns flagged (all conservative, one signal per anomaly):

    * ``tool_result`` whose ``tool_call_id`` has no matching earlier assistant
      tool_call (orphaned result, also counted in ParseStats).
    * two consecutive ``assistant`` turns with no intervening ``user``,
      ``tool_result``, or ``reasoning`` (possible stream duplication).
    """
    out: list[Signal] = []
    produced_ids = {
        tc.id for ev in events if ev.role is Role.ASSISTANT for tc in ev.tool_calls
    }
    for i, ev in enumerate(events):
        if ev.role is Role.TOOL_RESULT and ev.tool_call_id not in produced_ids:
            out.append(
                Signal(
                    kind=SignalKind.UNEXPECTED_ROLE_ORDER,
                    event_indices=(ev.index,),
                    detail="tool_result references unknown tool_call_id",
                    severity=SignalSeverity.LOW,
                    detector="detect_unexpected_role_order",
                    falsifier=(
                        "the producing assistant turn was dropped during "
                        "compaction or truncation rather than corrupted"
                    ),
                )
            )
        if i == 0:
            continue
        prev = events[i - 1]
        if (
            ev.role is Role.ASSISTANT
            and prev.role is Role.ASSISTANT
            and not prev.tool_calls
            and not ev.tool_calls
        ):
            # Two prose-only assistant turns back-to-back with no tool/user
            # between them is structurally odd in Grok transcripts.
            out.append(
                Signal(
                    kind=SignalKind.UNEXPECTED_ROLE_ORDER,
                    event_indices=(prev.index, ev.index),
                    detail="two consecutive assistant turns with no intervening role",
                    severity=SignalSeverity.LOW,
                    detector="detect_unexpected_role_order",
                    falsifier=(
                        "the turns were genuinely separate model responses "
                        "to a hidden event not captured in the transcript"
                    ),
                )
            )
    return out


def detect_tool_arg_parse_failures(events: list[Event]) -> DetectorResult:
    """Surface every tool call whose argument JSON failed to parse.

    These are already counted in ``ParseStats``, but a per-occurrence signal
    lets the LLM cite them individually. Mechanical: no interpretation.
    """
    out: list[Signal] = []
    for ev in _assistant_turns(events):
        for tc in ev.tool_calls:
            if tc.parse_error:
                out.append(
                    Signal(
                        kind=SignalKind.TOOL_ARG_PARSE_FAILURE,
                        event_indices=(ev.index,),
                        detail=(
                            f"tool {tc.name!r} args unparseable: {tc.parse_error}"
                        ),
                        severity=SignalSeverity.LOW,
                        detector="detect_tool_arg_parse_failures",
                        falsifier=(
                            "the call was harmless despite malformed args "
                            "(e.g. an unused demonstration)"
                        ),
                    )
                )
    return out


def detect_orphaned_tool_results(events: list[Event]) -> DetectorResult:
    """Flag each tool_result whose ``tool_call_id`` matches no tool_call.

    Distinct from ``unexpected_role_order``'s bulk view: this detector emits
    one signal per orphan.

    **Source-fidelity fix (empirical validation 2026-07-18):** when a
    transcript has zero structured ``tool_calls`` on any assistant event
    (e.g. converted from Markdown, which loses the call structure), ALL
    tool results will appear orphaned. This is a source-format limitation,
    not a real defect. The detector detects this condition and:
    - emits LOW severity (not HIGH) for each orphan
    - adds a single INFO-level summary signal explaining the source-format gap
    - includes a ``falsifier`` noting the linkage is unknowable

    Severity model:
    - HIGH: when some tool_calls ARE present (proving the format supports
      linkage) but specific results are genuinely orphaned.
    - LOW: when NO tool_calls exist at all (linkage is unknowable from
      this representation).
    """
    out: list[Signal] = []
    produced_ids = {
        tc.id for ev in events if ev.role is Role.ASSISTANT for tc in ev.tool_calls
    }
    total_tool_calls = sum(
        len(ev.tool_calls) for ev in events if ev.role is Role.ASSISTANT
    )
    total_tool_results = sum(1 for ev in events if ev.role is Role.TOOL_RESULT)

    # Source-fidelity check: if there are zero structured tool_calls but
    # tool_results exist, the linkage is unknowable, not proven-orphaned.
    linkage_unavailable = total_tool_calls == 0 and total_tool_results > 0

    if linkage_unavailable:
        # Emit a single summary signal explaining the source-format gap,
        # plus LOW-severity per-orphan signals (not HIGH).
        for ev in events:
            if ev.role is Role.TOOL_RESULT and ev.tool_call_id not in produced_ids:
                out.append(
                    Signal(
                        kind=SignalKind.ORPHANED_TOOL_RESULT,
                        event_indices=(ev.index,),
                        detail=(
                            f"tool_result {ev.tool_call_id!r} appears orphaned "
                            f"but source format has no structured tool_calls "
                            f"(linkage unavailable, not proven orphaned)"
                        ),
                        severity=SignalSeverity.LOW,
                        detector="detect_orphaned_tool_results",
                        falsifier=(
                            "the source transcript (likely Markdown-converted) does "
                            "not preserve tool_call structure; the result may have a "
                            "valid producing call that was lost in conversion"
                        ),
                    )
                )
        return out

    # Normal path: tool_calls exist, so orphaning is structurally meaningful.
    for ev in events:
        if ev.role is Role.TOOL_RESULT and ev.tool_call_id not in produced_ids:
            out.append(
                Signal(
                    kind=SignalKind.ORPHANED_TOOL_RESULT,
                    event_indices=(ev.index,),
                    detail=(
                        f"tool_result {ev.tool_call_id!r} has no producing tool_call"
                    ),
                    severity=SignalSeverity.HIGH,
                    detector="detect_orphaned_tool_results",
                    falsifier=(
                        "the producing assistant turn was compacted out of "
                        "the transcript rather than lost to a real defect"
                    ),
                )
            )
    return out


# ---------------------------------------------------------------------------
# Path helpers for the reversal detector
# ---------------------------------------------------------------------------


def _paths_mentioned_in_command(cmd: str) -> list[str]:
    """Extract path-like tokens from a shell command, normalised.

    Pulls tokens that look like file paths: those inside quotes, after ``--``,
    or containing a slash with a dotted extension. Best-effort — used only as
    a candidate set for the reversal detector, which then applies strict
    exact-basename matching. All returned paths are lower-cased and use
    forward slashes.
    """
    out: list[str] = []
    # 1) Quoted paths (single or double).
    for m in re.finditer(r"""['"]([^'"]+\.\S+)['"]""", cmd):
        out.append(m.group(1).replace("\\", "/").lower())
    # 2) Paths after a bare `--`.
    for m in re.finditer(r"--\s+([^\s|;&]+)", cmd):
        out.append(m.group(1).replace("\\", "/").lower())
    # 3) Tokens that contain a slash and a dotted extension.
    for tok in re.findall(r"[A-Za-z0-9_./\\\-]+\.[A-Za-z][A-Za-z0-9_\-]{0,15}", cmd):
        if "/" in tok or "\\" in tok:
            out.append(tok.replace("\\", "/").lower())
    # Dedup while preserving order.
    seen: set[str] = set()
    uniq: list[str] = []
    for p in out:
        if p and p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def _exact_path_match(write_path: str, candidate: str) -> bool:
    """Strict match: exact normalized equality OR exact basename equality.

    Replaces the previous loose substring matching (which fired on any parent
    directory overlap). Both inputs are already lower-cased and forward-slashed.
    """
    if write_path == candidate:
        return True
    w_base = write_path.rsplit("/", 1)[-1]
    c_base = candidate.rsplit("/", 1)[-1]
    return w_base == c_base and "." in c_base


def _path_matches_any(write_path: str, candidates: list[str]) -> bool:
    """Legacy loose match retained for compatibility; prefer _exact_path_match.

    Kept because the helper is exported in tests. New code should use
    :func:`_exact_path_match` for the precision the reversal detector needs.
    """
    for cand in candidates:
        if not cand:
            continue
        if _exact_path_match(write_path, cand):
            return True
    return False


# ---------------------------------------------------------------------------
# Opportunity-candidate detectors (spec Section 19)
# ---------------------------------------------------------------------------
#
# These detectors emit Signal objects whose kind is one of the
# ``OPPORTUNITY_CANDIDATE_*`` values. They are deliberately *candidate*
# signals, not opportunities: they tell the LLM "here is something that may
# or may not be a worthwhile opportunity; interpret it." Every signal carries
# a falsifier so the LLM can challenge it.
#
# Per spec Section 18: code assists by extracting structural facts; the LLM
# remains responsible for judging strategic value, combinations, tradeoffs,
# and whether an opportunity is worthwhile.


#: Markers that a tool call wrote/created an artifact (file or directory).
_ARTIFACT_CREATING_TOOLS = frozenset({"write", "edit", "search_replace"})

#: Markers that a tool result represents the artifact being *consumed*
#: (read, listed, grepped). We look for the path appearing in a later
#: read/grep/list call.
_ARTIFACT_CONSUMING_TOOLS = frozenset({"read_file", "list_dir", "grep"})

#: Verbs that indicate a "recommendation" in assistant text. Conservative:
#: requires a verb + a noun phrase. The LLM is responsible for confirming
#: semantic recommendation content.
_RECOMMENDATION_VERBS_RE = re.compile(
    r"\b(?:recommend(?:s|ed|ing)?|suggest(?:s|ed|ing)?|propose(?:s|ed|ing)?|"
    r"advise(?:s|d|ing)?|should|ought to|the best (?:approach|option|choice) is)\b",
    re.IGNORECASE,
)

#: Reversal/revision markers near a recommendation.
_REVISION_MARKERS_RE = re.compile(
    r"\b(?:actually|on (?:further )?reflection|having (?:now )?(?:seen|reviewed|checked)|"
    r"this (?:changes?|updates?|reverses?) (?:my|our|the) (?:earlier |prior )?(?:recommendation|suggestion|view)|"
    r"correction:|update:|revised:|i was wrong about)\b",
    re.IGNORECASE,
)

#: Markers that an assistant turn reports a success/fixed/works outcome.
_SUCCESS_MARKER_RE = re.compile(
    r"\b(?:tests? passed|all (?:tests?|checks?) (?:pass(?:ed)?|green)|now works|"
    r"verified working|confirmed (?:working|passing)|succeeded|fixed\.?|"
    r"exit code: ?0|no errors?)\b",
    re.IGNORECASE,
)


def detect_unconsumed_artifacts(events: list[Event]) -> DetectorResult:
    """Spec Section 19 (Unconsumed artifact): flag files created but never
    subsequently read, listed, or grepped.

    Emits a candidate signal per created-but-unconsumed path. The LLM
    decides whether the artifact is genuinely wasted (test case 17: unused
    artifact does not automatically imply waste — it may be a deliberate
    deliverable).
    """
    out: list[Signal] = []
    # path -> (creation_event_index, was_consumed)
    created: dict[str, int] = {}
    for ev in _assistant_turns(events):
        for tc in ev.tool_calls:
            fp = _file_path_from_call(tc.name, tc.arguments)
            if fp and ev.index not in created.values():
                # record first creation index per path
                if fp not in created:
                    created[fp] = ev.index
    # Scan later tool calls for consumption.
    consumed: set[str] = set()
    for ev in _assistant_turns(events):
        for tc in ev.tool_calls:
            if tc.name not in _ARTIFACT_CONSUMING_TOOLS:
                continue
            for arg_val in tc.arguments.values():
                if isinstance(arg_val, str):
                    norm = arg_val.replace("\\", "/").lower()
                    for fp in created:
                        if fp in norm or norm in fp:
                            consumed.add(fp)
    for fp, create_idx in created.items():
        if fp in consumed:
            continue
        out.append(
            Signal(
                kind=SignalKind.OPPORTUNITY_CANDIDATE_UNCONSUMED_ARTIFACT,
                event_indices=(create_idx,),
                detail=f"file created but never subsequently read/listed/grepped: {fp}",
                severity=SignalSeverity.LOW,
                detector="detect_unconsumed_artifacts",
                group_key=fp,
                falsifier=(
                    "the file is a deliberate deliverable (a report, a doc, "
                    "a shipped artifact) rather than an intermediate product; "
                    "or it is consumed by an external process not visible in "
                    "the transcript"
                ),
            )
        )
    return out


def detect_unused_capability(events: list[Event]) -> DetectorResult:
    """Spec Section 19 (Unused capability): flag tool-result content that
    mentions a discovered capability (CLI script, executable) which the
    assistant never subsequently invokes or references.

    Conservative: scans tool_result text for executable-shaped tokens
    (``<name>.py``/``.sh``/``.js``/``.ps1``/``.mjs`` only — *not* bare
    ``def``/``class`` names, which appear in any code reading and would
    over-fire). Emits one candidate per discovered-but-unused capability.
    """
    out: list[Signal] = []
    # Discover executable/script capabilities in tool_result text.
    discovered: dict[str, int] = {}  # token -> first result event index
    cap_re = re.compile(r"\b([A-Za-z_][A-Za-z0-9_-]*\.(?:py|sh|js|ts|ps1|mjs))\b")
    for ev in events:
        if ev.role is not Role.TOOL_RESULT or not ev.text:
            continue
        for m in cap_re.finditer(ev.text):
            token = m.group(1).strip().lower()
            # Skip generic noise.
            base = token.rsplit(".", 1)[0]
            if base in {"setup", "test", "conftest", "__init__", "readme", "license"}:
                continue
            if len(base) < 4:
                continue
            if token not in discovered:
                discovered[token] = ev.index
    if not discovered:
        return out
    # Scan subsequent assistant text + commands for usage.
    used: set[str] = set()
    for ev in events:
        if ev.role is not Role.ASSISTANT:
            continue
        haystack = (ev.text or "")
        for tc in ev.tool_calls:
            if isinstance(tc.arguments.get("command"), str):
                haystack += "\n" + tc.arguments["command"]
        for token in discovered:
            if re.search(r"\b" + re.escape(token) + r"\b", haystack, re.IGNORECASE):
                used.add(token)
    for token, idx in discovered.items():
        if token in used:
            continue
        out.append(
            Signal(
                kind=SignalKind.OPPORTUNITY_CANDIDATE_UNUSED_CAPABILITY,
                event_indices=(idx,),
                detail=f"capability discovered but not subsequently invoked: {token!r}",
                severity=SignalSeverity.LOW,
                detector="detect_unused_capability",
                group_key=token,
                falsifier=(
                    "the capability was intentionally out of scope for this "
                    "session, or was surfaced only as context, or is superseded "
                    "by a better alternative already in use"
                ),
            )
        )
    return out


def detect_duplicate_capability_references(events: list[Event]) -> DetectorResult:
    """Spec Section 19 (Duplicate capability): flag when the assistant
    proposes building/integrating something whose name matches an existing
    tool/script already used in the session.

    Conservative: collects names of tools used and scripts referenced, then
    looks for later "build/add/create" verbs targeting a matching name.
    """
    out: list[Signal] = []
    # Collect existing-capability names: every tool_name invoked.
    existing_caps: set[str] = set()
    for ev in _assistant_turns(events):
        for tc in ev.tool_calls:
            if tc.name:
                existing_caps.add(tc.name.lower())
    # Collect script names mentioned in tool results.
    for ev in events:
        if ev.role is not Role.TOOL_RESULT or not ev.text:
            continue
        for m in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_-]*\.(?:py|sh|js|ts|ps1))\b", ev.text):
            existing_caps.add(m.group(1).lower())
    if not existing_caps:
        return out

    # Look for build/add/create + matching name in later assistant text.
    # The verb phrase may include a leading "a/new" etc.; capture the noun.
    propose_re = re.compile(
        r"\b(?:build|add|create|implement|introduce|set\s+up)\s+"
        r"(?:(?:a|an|the|new)\s+){0,2}"
        r"([A-Za-z_][A-Za-z0-9_\-]{2,40})\b",
        re.IGNORECASE,
    )
    # Build a lookup: capability base name (without extension) -> full cap name.
    cap_base_to_full: dict[str, str] = {}
    for cap in existing_caps:
        cap_base_to_full[cap.rsplit(".", 1)[0]] = cap
    for ev in events:
        if ev.role is not Role.ASSISTANT or not ev.text:
            continue
        for m in propose_re.finditer(ev.text):
            target = m.group(1).lower()
            target_base = target.rsplit(".", 1)[0]
            # Match if target (or target_base) equals an existing capability
            # or its base name.
            matched_cap = None
            for cap_base, cap_full in cap_base_to_full.items():
                if target == cap_base or target_base == cap_base:
                    matched_cap = cap_full
                    break
                if cap_base in target.split("-") or cap_base in target.split("_"):
                    matched_cap = cap_full
                    break
            if matched_cap is None:
                continue
            out.append(
                Signal(
                    kind=SignalKind.OPPORTUNITY_CANDIDATE_DUPLICATE_CAPABILITY,
                    event_indices=(ev.index,),
                    detail=(
                        f"proposed {target!r} may duplicate existing capability {matched_cap!r}"
                    ),
                    severity=SignalSeverity.LOW,
                    detector="detect_duplicate_capability_references",
                    group_key=matched_cap,
                    falsifier=(
                        "the proposed addition has materially different "
                        "scope or behaviour from the existing capability, "
                        "or the existing capability cannot be reused here"
                    ),
                )
            )
    return out


def detect_recommendation_revisions(events: list[Event]) -> DetectorResult:
    """Spec Section 19 (Recommendation revision) + Section 12: flag when an
    assistant turn emits a recommendation after an earlier recommendation,
    AND uses revision/reversal language.

    Emits one candidate per revision event. The LLM classifies the revision
    using ``RevisionClassification`` (HEALTHY_UPDATE_NEW_INFORMATION,
    AVOIDABLE_UPDATE_MISSED_AVAILABLE_EVIDENCE, etc.).
    """
    out: list[Signal] = []
    last_recommendation_index: int | None = None
    for ev in events:
        if ev.role is not Role.ASSISTANT or not ev.text:
            continue
        is_rec = bool(_RECOMMENDATION_VERBS_RE.search(ev.text))
        is_rev = bool(_REVISION_MARKERS_RE.search(ev.text))
        if is_rec and last_recommendation_index is not None and is_rev:
            out.append(
                Signal(
                    kind=SignalKind.OPPORTUNITY_CANDIDATE_RECOMMENDATION_REVISION,
                    event_indices=(last_recommendation_index, ev.index),
                    detail="recommendation revised after the immediately prior recommendation",
                    severity=SignalSeverity.MEDIUM,
                    detector="detect_recommendation_revisions",
                    group_key=f"rev@{ev.index}",
                    falsifier=(
                        "the revision is a healthy update driven by genuinely "
                        "new user information, not avoidable rework"
                    ),
                )
            )
        if is_rec:
            last_recommendation_index = ev.index
    return out


def detect_successful_interventions(events: list[Event]) -> DetectorResult:
    """Spec Section 19 (Successful intervention) + Section 4: flag assistant
    turns that follow an error/tool_result_error and then report success
    markers. These are reuse/amplification candidates — the recovery is
    itself valuable.

    Emits one candidate per success-after-error pair.
    """
    out: list[Signal] = []
    # Find error events.
    error_indices: list[int] = []
    for ev in events:
        if ev.role is not Role.TOOL_RESULT or not ev.text:
            continue
        if _TOOL_ERROR_RE.search(ev.text):
            error_indices.append(ev.index)
    if not error_indices:
        return out
    # Find success markers in assistant turns that follow an error.
    for ev in events:
        if ev.role is not Role.ASSISTANT or not ev.text:
            continue
        if not _SUCCESS_MARKER_RE.search(ev.text):
            continue
        # Find the most recent prior error.
        prior_errors = [i for i in error_indices if i < ev.index]
        if not prior_errors:
            continue
        last_err = prior_errors[-1]
        out.append(
            Signal(
                kind=SignalKind.OPPORTUNITY_CANDIDATE_SUCCESSFUL_INTERVENTION,
                event_indices=(last_err, ev.index),
                detail="intervention followed an error and produced success markers",
                severity=SignalSeverity.MEDIUM,
                detector="detect_successful_interventions",
                group_key=f"success@{ev.index}",
                falsifier=(
                    "the success was unrelated to the prior error (e.g. a "
                    "different test passed for an unrelated reason) or the "
                    "intervention is not reusable outside this session"
                ),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Interaction-quality detectors (deeper-failure lens)
# ---------------------------------------------------------------------------
#
# Per spec, three deterministic detectors cover the 8 deeper interaction-
# quality patterns concretely enough to flag from raw events; the remaining
# patterns (mechanism-object confusion, calibration oscillation, anchoring
# on invalidated evidence, emergent misalignment, success-shape mismatch)
# are lens-only — the LLM uses them during synthesis when reading the
# signal ledger.
#
# Precision is prioritized over recall. Each detector fires LOW with a falsifier
# that explicitly notes "this may be deliberate."


def detect_objective_drift(events: list[Event]) -> DetectorResult:
    """Spec: 'Forcing the user to repeatedly restore the real objective'.

    A user objective-drift signal fires when:
      1. the user has issued ≥2 real (non-synthetic) messages that contain
         explicit objective-correction phrases ("no, I meant", "what I
         actually want", "let me clarify", "stop doing X"), AND
      2. each correction is preceded by an assistant turn that arguably
         drifted from the user's prior statement.

    Conservative: requires ≥2 corrections in the session. A single "let me
    clarify" is normal; a pattern is a candidate.
    """
    out: list[Signal] = []
    correction_phrases = (
        r"\bno,?\s+(?:i|we)\s+meant\b",
        r"\bwhat i (?:actually|really) (?:want|meant|need)\b",
        r"\blet me clarify\b",
        r"\bstop (?:doing|saying)\b",
        r"\bthat's not (?:what|where) (?:i|we)\b",
        r"\bi meant\b",
        r"\bplease (?:just )?do\b",
    )
    correction_re = re.compile("|".join(correction_phrases), re.IGNORECASE)
    drift_indices: list[int] = []
    drift_texts: list[str] = []
    for ev in events:
        if ev.role is not Role.USER or ev.synthetic_reason or not ev.text:
            continue
        m = correction_re.search(ev.text)
        if not m:
            continue
        drift_indices.append(ev.index)
        # Capture first 60 chars of matched text for the falsifier/audit trail
        snippet = ev.text.replace("\n", " ")[:80]
        drift_texts.append(snippet)
    if len(drift_indices) >= 2:
        out.append(
            Signal(
                kind=SignalKind.OPPORTUNITY_CANDIDATE_OBJECTIVE_DRIFT,
                event_indices=tuple(drift_indices),
                detail=(
                    f"user issued {len(drift_indices)} objective-correction messages in this session "
                    f"(examples: {', '.join(repr(t[:30]) for t in drift_texts[:3])}{'...' if len(drift_texts) > 3 else ''})"
                ),
                severity=SignalSeverity.LOW,
                detector="detect_objective_drift",
                group_key=f"drift@{drift_indices[-1]}",
                falsifier=(
                    "these may be normal clarifications on a genuinely ambiguous task; "
                    "or the assistant may have correctly inferred the user's intent "
                    "despite the user's surface wording"
                ),
            )
        )
    return out


def detect_post_failure_continuation(events: list[Event]) -> DetectorResult:
    """Spec: 'Continuing work after the evidence ceiling made the result unavailable'.

    Fires when the assistant produces ≥2 tool results with hard-error markers
    (non-zero exit code + Error: trace) AND THEN continues with another
    assistant tool call cycle despite those errors. The "work past infeasibility"
    pattern is: hit a ceiling, keep going anyway without re-scoping.

    Conservative: requires ≥2 tool_result_error events followed by ≥1 more
    assistant tool call after the last error.
    """
    out: list[Signal] = []
    last_error_idx: int | None = None
    error_count = 0
    for ev in events:
        if ev.role is Role.TOOL_RESULT and ev.text and _TOOL_ERROR_RE.search(ev.text):
            error_count += 1
            last_error_idx = ev.index
            continue
        # Once we have an error followed by a NEW assistant tool call *without*
        # an intervening user message acknowledging the failure, flag.
        if (
            ev.role is Role.ASSISTANT
            and ev.tool_calls
            and last_error_idx is not None
            and ev.index > last_error_idx
            and error_count >= 2
        ):
            # Check no intervening user message between error and this assistant
            intervening_user = any(
                e.role is Role.USER
                and not e.synthetic_reason
                and last_error_idx < e.index < ev.index
                for e in events
            )
            if not intervening_user:
                # De-dupe by group_key tied to the post-error assistant index.
                gk = f"cont@{ev.index}"
                if any(s.group_key == gk for s in out):
                    continue
                out.append(
                    Signal(
                        kind=SignalKind.OPPORTUNITY_CANDIDATE_POST_FAILURE_CONTINUATION,
                        event_indices=(last_error_idx, ev.index),
                        detail=(
                            f"assistant continued tool-use after {error_count} tool errors without "
                            f"intervening user acknowledgement"
                        ),
                        severity=SignalSeverity.LOW,
                        detector="detect_post_failure_continuation",
                        group_key=gk,
                        falsifier=(
                            "the errors may have been transient and the assistant "
                            "correctly retried, or the assistant addressed the failure "
                            "in tool-arguments without surfacing it"
                        ),
                    )
                )
    return out


def detect_reading_without_synthesis(events: list[Event]) -> DetectorResult:
    """Spec: 'Requiring the user to perform the agent's reasoning'.

    Indirect signal: the assistant performed many tool reads/files in a row
    but produced limited visible synthesis. When synthesis volume is much
    smaller than tool-call volume, the user is left to do the reasoning.

    Conservative: requires ≥8 tool calls in the session AND the assistant's
    total text length ≤ 0.2× the tool-result total length. The ratio is the
    'reasoning load' left on the user.
    """
    out: list[Signal] = []
    tool_call_count = 0
    tool_result_text_len = 0
    assistant_text_len = 0
    for ev in events:
        if ev.role is Role.ASSISTANT:
            tool_call_count += len(ev.tool_calls)
            assistant_text_len += len(ev.text or "")
        elif ev.role is Role.TOOL_RESULT:
            tool_result_text_len += len(ev.text or "")
    if tool_call_count < 8:
        return out
    # Watch for the load-shift pattern: agent reads a lot, says little.
    if tool_result_text_len == 0:
        return out
    synthesis_ratio = assistant_text_len / tool_result_text_len
    # Threshold chosen to be precise (per spec priority on precision): only
    # fire if the agent has said less than 1 character of synthesis per 5
    # characters of tool result.
    if synthesis_ratio < 0.2:
        out.append(
            Signal(
                kind=SignalKind.OPPORTUNITY_CANDIDATE_READING_WITHOUT_SYNTHESIS,
                event_indices=(events[0].index, events[-1].index),
                detail=(
                    f"{tool_call_count} tool reads, assistant synthesis only "
                    f"{assistant_text_len} chars vs {tool_result_text_len} chars of tool output "
                    f"(ratio {synthesis_ratio:.3f}) — reasoning load mostly on user"
                ),
                severity=SignalSeverity.LOW,
                detector="detect_reading_without_synthesis",
                group_key=f"synratio@{tool_call_count}",
                falsifier=(
                    "the data may have been self-explanatory (e.g. a code listing "
                    "for review), or the synthesis may have happened via tool-call "
                    "arguments rather than assistant text"
                ),
            )
        )
    return out


# ---------------------------------------------------------------------------
# Deeper interaction-quality detectors (spec Section 13)
# ---------------------------------------------------------------------------


def detect_continued_after_unknown(events: list[Event]) -> DetectorResult:
    """Spec Section 13: 'Continued work after declared unknown'.

    Fires when the assistant acknowledges a blocking unknown (e.g. "I cannot
    verify X") and then continues producing downstream work that depends on
    the unknown — without intervening user direction.

    Uses ``interaction_quality.EVIDENCE_CEILING_RE`` to find the ceiling
    acknowledgement. Conservative: requires the assistant to produce ≥1
    tool call or ≥200 chars of new text after the ceiling phrase without
    an intervening real user message.
    """
    out: list[Signal] = []
    for i, ev in enumerate(events):
        if ev.role is not Role.ASSISTANT or not ev.text:
            continue
        if not has_evidence_ceiling_phrase(ev.text):
            continue
        ceiling_idx = ev.index
        # Case 1: the SAME event has the ceiling phrase AND tool calls.
        if ev.tool_calls:
            out.append(
                Signal(
                    kind=SignalKind.OPPORTUNITY_CANDIDATE_CONTINUED_AFTER_UNKNOWN,
                    event_indices=(ceiling_idx,),
                    detail="assistant acknowledged a blocking unknown and produced tool calls in the same turn",
                    severity=SignalSeverity.LOW,
                    detector="detect_continued_after_unknown",
                    group_key=f"cont_unknown@{ceiling_idx}",
                    falsifier="the tool calls may have been independent of the unknown",
                ),
            )
            continue
        # Case 2: scan forward for continued work without intervening user msg.
        for j in range(i + 1, len(events)):
            nxt = events[j]
            if nxt.role is Role.USER and not nxt.synthetic_reason:
                break  # user intervened — healthy
            if nxt.role is Role.ASSISTANT:
                continued_text_len = len(nxt.text or "")
                has_tool_calls = bool(nxt.tool_calls)
                if continued_text_len >= 200 or has_tool_calls:
                    out.append(
                        Signal(
                            kind=SignalKind.OPPORTUNITY_CANDIDATE_CONTINUED_AFTER_UNKNOWN,
                            event_indices=(ceiling_idx, nxt.index),
                            detail=(
                                "assistant acknowledged a blocking unknown then continued "
                                "producing downstream work without user direction"
                            ),
                            severity=SignalSeverity.LOW,
                            detector="detect_continued_after_unknown",
                            group_key=f"cont_unknown@{nxt.index}",
                            falsifier=(
                                "the continued work may have been independent of the unknown, "
                                "or the agent may have correctly reframed around the ceiling"
                            ),
                        )
                    )
                    break
    return out


def detect_correction_propagation_failure(events: list[Event]) -> DetectorResult:
    """Spec Section 13: 'Correction-with-residual-reference'.

    Fires when a user correction is followed by assistant text that still
    references the corrected claim. Conservative: requires a user_correction
    signal (or pushback phrase) followed by ≥1 assistant turn that re-asserts
    similar language within 5 events.
    """
    out: list[Signal] = []
    # Find user pushback events.
    pushback_events: list[tuple[int, str]] = []
    for ev in events:
        if ev.role is not Role.USER or ev.synthetic_reason or not ev.text:
            continue
        if has_user_pushback_phrase(ev.text):
            pushback_events.append((ev.index, ev.text[:120]))

    if not pushback_events:
        return out

    for pb_idx, pb_text in pushback_events:
        # Scan forward ≤5 events for assistant re-assertion.
        pb_event_pos = next(
            (i for i, e in enumerate(events) if e.index == pb_idx), None
        )
        if pb_event_pos is None:
            continue
        for j in range(pb_event_pos + 1, min(pb_event_pos + 6, len(events))):
            nxt = events[j]
            if nxt.role is not Role.ASSISTANT or not nxt.text:
                continue
            # Check if assistant text still references the corrected topic.
            # Heuristic: the assistant's text contains phrases like "still",
            # "as I said", "my earlier", "confirmed" shortly after a correction.
            if re.search(
                r"\b(?:as i (?:said|mentioned|noted)|my earlier|still (?:valid|correct|true)|"
                r"confirmed|verified|as shown)\b",
                nxt.text,
                re.IGNORECASE,
            ):
                out.append(
                    Signal(
                        kind=SignalKind.OPPORTUNITY_CANDIDATE_CORRECTION_PROPAGATION_FAILURE,
                        event_indices=(pb_idx, nxt.index),
                        detail=(
                            "user pushed back; assistant text shortly after still references "
                            "the prior claim"
                        ),
                        severity=SignalSeverity.LOW,
                        detector="detect_correction_propagation_failure",
                        group_key=f"corr_prop@{nxt.index}",
                        falsifier=(
                            "the assistant may have been correctly re-affirming a different "
                            "aspect of the claim, or the pushback was about a different topic"
                        ),
                    )
                )
                break
    return out


def detect_procedure_saturation(events: list[Event]) -> DetectorResult:
    """Spec Section 13: 'Rule/process saturation'.

    Fires when the assistant cites rules, modes, or workflow mechanics
    disproportionately to the task evidence gathered. Uses
    ``interaction_quality.PROCEDURE_CITATION_RE`` to count procedure
    citations. Conservative: requires ≥5 citations across the session
    AND fewer tool results than citations (the agent is talking about
    process more than doing work).
    """
    out: list[Signal] = []
    total_citations = 0
    tool_result_count = 0
    citation_events: list[int] = []
    for ev in events:
        if ev.role is Role.ASSISTANT and ev.text:
            n = procedure_citation_count(ev.text)
            if n:
                total_citations += n
                citation_events.append(ev.index)
        elif ev.role is Role.TOOL_RESULT:
            tool_result_count += 1
    if total_citations < 5:
        return out
    if tool_result_count >= total_citations:
        return out  # citations are proportionate to work done
    out.append(
        Signal(
            kind=SignalKind.OPPORTUNITY_CANDIDATE_PROCEDURE_SATURATION,
            event_indices=tuple(citation_events[:5]),
            detail=(
                f"{total_citations} procedure/rule citations vs {tool_result_count} tool results "
                f"— process discussion may be displacing task work"
            ),
            severity=SignalSeverity.LOW,
            detector="detect_procedure_saturation",
            group_key=f"proc_sat@{total_citations}",
            falsifier=(
                "the task may genuinely require heavy process reasoning "
                "(e.g. architecture review, compliance audit)"
            ),
        )
    )
    return out


# ---------------------------------------------------------------------------
# Operational-safety detectors (spec Section 6A-B) — HIGH severity
# ---------------------------------------------------------------------------

_HIGH_RISK_WRITE_PATHS = (
    ".env", "settings.json", "config.toml", ".gitignore",
    "credentials", ".npmrc", ".pypirc", ".netrc",
)


def detect_destructive_write_without_read(events: list[Event]) -> DetectorResult:
    """Spec Section 6A: destructive mutation without state-preserving preflight.

    Fires when a high-risk config file (.env, settings.json, etc.) is
    written/overwritten WITHOUT a prior read. HIGH severity — potential
    data loss / secret destruction.
    """
    out: list[Signal] = []
    write_paths: list[tuple[int, str]] = []
    read_paths: set[str] = set()
    for ev in events:
        if ev.role is not Role.ASSISTANT:
            continue
        for tc in ev.tool_calls:
            # Check for write to high-risk path
            if tc.name in ("write", "edit", "search_replace"):
                fp = None
                for key in ("file_path", "target_file", "path"):
                    v = tc.arguments.get(key) if isinstance(tc.arguments, dict) else None
                    if isinstance(v, str) and v:
                        fp = v.replace("\\", "/").lower()
                        break
                if fp and any(hr in fp for hr in _HIGH_RISK_WRITE_PATHS):
                    write_paths.append((ev.index, fp))
            # Check for read of any path (to suppress destructive-write if read first)
            if tc.name in ("read_file", "grep", "list_dir"):
                for key in ("file_path", "target_file", "path"):
                    v = tc.arguments.get(key) if isinstance(tc.arguments, dict) else None
                    if isinstance(v, str) and v:
                        read_paths.add(v.replace("\\", "/").lower())
    for write_idx, write_path in write_paths:
        was_read = any(rp in write_path or write_path in rp for rp in read_paths)
        if not was_read:
            out.append(Signal(
                kind=SignalKind.DESTRUCTIVE_WRITE_WITHOUT_READ,
                event_indices=(write_idx,),
                detail=f"high-risk file overwritten without prior read: {write_path}",
                severity=SignalSeverity.HIGH,
                detector="detect_destructive_write_without_read",
                group_key=write_path,
                falsifier="the file may not have existed previously, or contents were known from earlier context",
            ))
    return out


_SECRET_RE = re.compile(
    r"(?:sk-[a-zA-Z0-9]{20,})|(?:AKIA[A-Z0-9]{16})|(?:ghp_[a-zA-Z0-9]{36})|"
    r"(?:xox[bpoa]-[a-zA-Z0-9-]+)|(?:AIza[a-zA-Z0-9_-]{35})|"
    r"(?:[A-Z_]{3,}_(?:API_KEY|SECRET|TOKEN)\s*=\s*[A-Za-z0-9/+=]{16,})|"
    r"(?:password\s*=\s*[^\s]{8,})|(?:Bearer\s+[a-zA-Z0-9._-]{20,})",
    re.IGNORECASE,
)


def detect_tool_result_secret_exposure(events: list[Event]) -> DetectorResult:
    """Phase 2: tool-result secret exposure.

    Renamed from ``detect_secret_exposure`` in Phase 2 to honestly reflect
    scope. The original name suggested broad secret detection but the
    implementation only scans tool_result text.

    Uses the shared ``secret_engine`` (Phase 2) so all secret-pattern logic
    lives in one authoritative location. Findings carry redacted
    fingerprints; the secret value is never serialized.

    Severity: HIGH — a tool returning a credential is a potential incident.

    The old name ``detect_secret_exposure`` is preserved as an alias below
    for backward compatibility with existing tests that import it.
    """
    out: list[Signal] = []
    try:
        from secret_engine import scan_tool_result
    except ImportError:
        # Fall back to legacy regex if engine unavailable
        scan_tool_result = None
    for ev in events:
        if ev.role is not Role.TOOL_RESULT or not ev.text:
            continue
        if scan_tool_result is not None:
            result = scan_tool_result(ev.text, event_index=ev.index)
            if not result.findings:
                continue
            for f in result.deduplicated:
                out.append(Signal(
                    kind=SignalKind.SECRET_EXPOSURE_IN_TOOL_OUTPUT,
                    event_indices=(ev.index,),
                    detail=(
                        f"tool_result contains credential ({f.fingerprint}) — "
                        f"source=TOOL_RETURNED; may be persisted in transcript/logs"
                    ),
                    severity=SignalSeverity.HIGH,
                    detector="detect_tool_result_secret_exposure",
                    group_key=f"secret@{ev.index}",
                    falsifier=(
                        "the pattern may be a placeholder, example, or "
                        "documentation reference"
                    ),
                ))
        else:
            if _SECRET_RE.search(ev.text):
                out.append(Signal(
                    kind=SignalKind.SECRET_EXPOSURE_IN_TOOL_OUTPUT,
                    event_indices=(ev.index,),
                    detail="tool_result contains a credential-shaped pattern — secret may be persisted in transcript/logs",
                    severity=SignalSeverity.HIGH,
                    detector="detect_tool_result_secret_exposure",
                    group_key=f"secret@{ev.index}",
                    falsifier="the pattern may be a placeholder, example, or documentation reference",
                ))
    return out


# Backward-compat alias. Existing tests that import detect_secret_exposure
# continue to work; the alias points to the renamed detector. New code
# should call detect_tool_result_secret_exposure directly.
detect_secret_exposure = detect_tool_result_secret_exposure


def detect_user_paste_secret_warning(events: list[Event]) -> DetectorResult:
    """Phase 2: user-pasted credential warning.

    Fires when a user message contains a live-credential pattern. This is
    the gap exposed by validation case C04: a user pasted a config.toml
    excerpt containing a live ``sk-...`` API key, and the prior detector
    (which only scanned tool_result text) missed it entirely.

    Severity: HIGH — a live credential in the conversation is an incident
    regardless of who pasted it. The agent should warn the user and
    recommend rotation if the credential is live.

    Uses the shared ``secret_engine``. Findings carry redacted fingerprints
    only; the value is never serialized.

    Falsifier: the pattern may be a placeholder, an example, a documentation
    reference, or a synthetic test credential. The engine suppresses known
    placeholders (sk-test, sk-example, YOUR_API_KEY, etc.).
    """
    out: list[Signal] = []
    try:
        from secret_engine import scan_user_content
    except ImportError:
        return out  # without the engine we cannot scan user content safely
    for ev in events:
        if ev.role is not Role.USER or not ev.text:
            continue
        if getattr(ev, "synthetic_reason", None):
            continue  # harness-injected, not real user content
        result = scan_user_content(ev.text, event_index=ev.index)
        if not result.findings:
            continue
        for f in result.deduplicated:
            out.append(Signal(
                kind=SignalKind.USER_PASTE_SECRET_WARNING,
                event_indices=(ev.index,),
                detail=(
                    f"user message contains credential ({f.fingerprint}) — "
                    f"source=USER_PASTED; warn the user and recommend rotation "
                    f"if the credential is live"
                ),
                severity=SignalSeverity.HIGH,
                detector="detect_user_paste_secret_warning",
                group_key=f"user-secret@{ev.index}",
                falsifier=(
                    "the pattern may be a placeholder, example, documentation "
                    "reference, or synthetic test credential (sk-test* is suppressed)"
                ),
            ))
    return out


# ---------------------------------------------------------------------------
# Registry & runner (defined after all detectors so names resolve at import)
# ---------------------------------------------------------------------------

ALL_DETECTORS: tuple[Detector, ...] = (
    detect_repeated_identical_tool_calls,
    detect_repeated_tool_name_windows,
    detect_tool_result_errors,
    detect_empty_tool_results,
    detect_repeated_file_edits,
    detect_file_edit_reversals,
    detect_assistant_self_corrections,
    detect_user_corrections,
    detect_unanswered_user_questions,
    detect_long_tool_chains,
    detect_unexpected_role_order,
    detect_tool_arg_parse_failures,
    detect_orphaned_tool_results,
    # Opportunity-candidate detectors (spec Section 19). Emitters only.
    detect_unconsumed_artifacts,
    detect_unused_capability,
    detect_duplicate_capability_references,
    detect_recommendation_revisions,
    detect_successful_interventions,
    # Interaction-quality candidate detectors (deeper-failure lens).
    # The other 5 deeper patterns are LLM-lens-only; these 3 are concrete
    # enough to flag from raw events.
    detect_objective_drift,
    detect_post_failure_continuation,
    detect_reading_without_synthesis,
    # Deeper interaction-quality detectors (spec Section 13).
    detect_continued_after_unknown,
    detect_correction_propagation_failure,
    detect_procedure_saturation,
    # Operational-safety detectors (spec Section 6A-B). HIGH severity.
    detect_destructive_write_without_read,
    detect_tool_result_secret_exposure,
    detect_user_paste_secret_warning,
)


def run_all_detectors(events: Iterable[Event]) -> list[Signal]:
    """Run every detector in ``ALL_DETECTORS`` and merge results.

    Detectors are independent; order in the output is stable (detector order,
    then signal order within each detector) so packet hashes are reproducible.
    """
    materialised = list(events)
    out: list[Signal] = []
    for det in ALL_DETECTORS:
        out.extend(det(materialised))
    return out
