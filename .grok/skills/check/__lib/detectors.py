"""Deterministic signal detectors for the /check transcript preprocessor.

Each detector takes a parsed ``Transcript`` and returns a list of ``Signal``
objects. A signal is an **objective, citable observation** — never a verdict.
The verifier subagents consume these signals to confirm or refute the
session's claims ("did the session actually do what it claims?").

The 10 detectors
----------------
This is a **check-oriented** set, distinct from what an AAR-oriented set
would be. AAR's job is causal synthesis; /check's job is claim verification.
So these detectors emphasise: what was claimed, what was actually done, and
what claims lack supporting evidence.

 1. ``file_edits``                — every tool call that wrote/edited a file
 2. ``command_executions``        — every shell/terminal command + exit code
 3. ``test_runs``                 — command subset that ran a test framework
 4. ``verification_tool_calls``   — read/grep/glob/list inspections
 5. ``claim_verbs``               — assistant text asserting completion
 6. ``failures``                  — non-zero exits, tracebacks, error strings
 7. ``todo_state_changes``        — every todo_write with status transitions
 8. ``scope_files``               — distinct file set the session touched
 9. ``subagent_spawns``           — every spawn_subagent / task dispatch
10. ``unverified_claim_candidates`` — claim_verbs with no nearby verification

Design invariants
-----------------
* **Deterministic.** Pattern matching is anchored (``\b``) and case-sensitive
  unless case-insensitivity is explicitly justified. Re-running on the same
  transcript yields the same signals.
* **Cited.** Every signal carries ``event_indices`` pointing back to the
  parsed events, so a verifier can resolve a signal to exact transcript
  lines without re-reading the file.
* **Honest about heuristic vs observed.** Signals that are direct tool-call
  observations use ``confidence="OBSERVED"``. Pattern-matched text signals
  use ``confidence="INFERRED"`` because a phrase match is not proof of an
  actual claim. The verifier decides whether the inference holds.
* **Cross-harness vocabulary.** Tool-name sets cover Grok Build, Claude
  Code, and common generic names so the detector works on transcripts from
  either harness without configuration.

This module emits NO verdicts. PASS/FAIL is the verifier's job.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from event_model import Event, Role, Transcript, ToolCall

__all__ = [
    "Signal",
    "DETECTOR_NAMES",
    "detect_file_edits",
    "detect_command_executions",
    "detect_test_runs",
    "detect_verification_tool_calls",
    "detect_claim_verbs",
    "detect_failures",
    "detect_todo_state_changes",
    "detect_scope_files",
    "detect_subagent_spawns",
    "detect_unverified_claim_candidates",
    "run_all_detectors",
]

#: Ordered tuple of detector names — order is stable for downstream consumers.
DETECTOR_NAMES: tuple[str, ...] = (
    "file_edits",
    "command_executions",
    "test_runs",
    "verification_tool_calls",
    "claim_verbs",
    "failures",
    "todo_state_changes",
    "scope_files",
    "subagent_spawns",
    "unverified_claim_candidates",
)

#: Window (in events) after a claim within which we look for verification.
#: 5 is a heuristic: large enough to allow a tool-call round-trip, small
#: enough that unrelated later work does not "verify" the claim.
UNVERIFIED_CLAIM_WINDOW = 5

# ---------------------------------------------------------------------------
# Cross-harness tool-name vocabularies
# ---------------------------------------------------------------------------

WRITE_TOOLS: frozenset[str] = frozenset(
    {
        # Grok Build
        "write",
        "search_replace",
        "create_file",
        "multi_or_replace",
        # Claude Code
        "Edit",
        "Write",
        "str_replace_editor",
        "FileEdit",
        # generic
        "create_file_or_dir",
    }
)

COMMAND_TOOLS: frozenset[str] = frozenset(
    {
        # Grok Build
        "run_terminal_command",
        # Claude Code
        "Bash",
        # generic
        "shell",
        "execute_command",
        "terminal",
        "Shell",
        "Terminal",
    }
)

READ_TOOLS: frozenset[str] = frozenset(
    {
        # Grok Build
        "read_file",
        "grep",
        "list_dir",
        # Claude Code
        "Read",
        "Glob",
        "Grep",
        "List",
        # generic
        "ListDir",
    }
)

SUBAGENT_TOOLS: frozenset[str] = frozenset(
    {
        # Grok Build
        "spawn_subagent",
        # Claude Code
        "Task",
        "task",
        # generic
        "SpawnSubagent",
        "dispatch_subagent",
    }
)

TODO_TOOLS: frozenset[str] = frozenset(
    {
        # Grok Build
        "todo_write",
        # Claude Code
        "TodoWrite",
        # generic
        "UpdateTodos",
    }
)

# Path-ish argument keys across harnesses.
WRITE_PATH_KEYS: tuple[str, ...] = (
    "file_path",
    "target_file",
    "path",
    "filepath",
)
COMMAND_ARG_KEYS: tuple[str, ...] = ("command", "cmd", "script")
READ_PATH_KEYS: tuple[str, ...] = ("target_file", "file_path", "path", "pattern", "target_directory")
SUBAGENT_ARG_KEYS: tuple[str, ...] = ("subagent_type", "type", "description", "prompt")


# ---------------------------------------------------------------------------
# Test-framework detection (used by detect_test_runs)
# ---------------------------------------------------------------------------

#: Each entry: (compiled pattern, framework label). Patterns are deliberately
#: anchored on word boundaries to avoid matching substrings like "prepytest".
TEST_FRAMEWORK_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bpytest\b"), "pytest"),
    (re.compile(r"\bpython\s+-m\s+unittest\b"), "unittest"),
    (re.compile(r"\bcargo\s+test\b"), "cargo-test"),
    (re.compile(r"\bgo\s+test\b"), "go-test"),
    (re.compile(r"\bnpm\s+(?:run\s+)?test\b"), "npm-test"),
    (re.compile(r"\bnpx\s+jest\b|\bjest\b"), "jest"),
    (re.compile(r"\bvitest\b"), "vitest"),
    (re.compile(r"\byarn\s+test\b"), "yarn-test"),
    (re.compile(r"\brspec\b"), "rspec"),
    (re.compile(r"\bgradle\s+test\b"), "gradle-test"),
    (re.compile(r"\bmvn\s+test\b"), "maven-test"),
)


# ---------------------------------------------------------------------------
# Claim-verb detection (used by detect_claim_verbs)
# ---------------------------------------------------------------------------

#: Each entry: (compiled pattern, verb label). Patterns are case-insensitive
#: so they catch sentence-initial capitalised forms ("Confirmed.", "Verified.",
#: "Done.") that real assistant text uses. False positives are acceptable
#: because every emitted signal is ``confidence="INFERRED"`` — the verifier
#: subagent inspects flagged claims and discards noise. False negatives
#: (missing real claims) are worse for /check, whose job is "did the session
#: actually do what it claims?".
CLAIM_VERB_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bI(?:'ve| have)? (?:fixed|resolved|patched|repaired)\b", re.IGNORECASE), "fixed"),
    (re.compile(r"\bI(?:'ve| have)? verified\b|\bverification (?:passed|succeeded)\b", re.IGNORECASE), "verified"),
    (re.compile(r"\bI(?:'ve| have)? (?:implemented|added|created|built|introduced)\b", re.IGNORECASE), "implemented"),
    # "done" as a standalone sentence end OR with a be-verb prefix.
    (re.compile(r"\b(?:is|are|was|were) done\b|\bI(?:'ve| have) (?:finished|completed)\b|\bDone[\.\!\)]", re.IGNORECASE), "done"),
    (re.compile(r"\btests? (?:pass(?:ed)?|succeed(?:ed)?)\b|\ball green\b", re.IGNORECASE), "tests_pass"),
    (re.compile(r"\bconfirmed\b", re.IGNORECASE), "confirmed"),
    (re.compile(r"\bI(?:'ve| have)? (?:written|wrote|updated|refactored|migrated)\b", re.IGNORECASE), "wrote_or_changed"),
    (re.compile(r"\bbuild(?:s|ing)? (?:succeed(?:ed|s)?|pass(?:ed|es)?)\b", re.IGNORECASE), "build_pass"),
)


# ---------------------------------------------------------------------------
# Failure detection (used by detect_failures)
# ---------------------------------------------------------------------------

#: ``exit: N`` is the literal prefix Grok emits in tool_result for
#: run_terminal_command. We match N in 1..9 (and multi-digit non-zero).
EXIT_NONZERO_PATTERN = re.compile(r"\bexit(?:\s+code)?:\s*([1-9]\d*)", re.MULTILINE)
TRACEBACK_PATTERN = re.compile(r"Traceback \(most recent call last\)")
EXCEPTION_PATTERN = re.compile(r"\b([A-Z]\w*(?:Error|Exception))\b")
# FAIL must NOT match "FAILED" produced by some tools as a noun; require
# word boundary and not followed by ED.
FAIL_TOKEN_PATTERN = re.compile(r"\bFAIL\b(?!ED)")
ERROR_TOKEN_PATTERN = re.compile(r"\bERROR:\s", re.MULTILINE)


# ---------------------------------------------------------------------------
# Signal dataclass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Signal:
    """One objective observation produced by a detector.

    Fields
    ------
    kind
        The detector name (one of ``DETECTOR_NAMES``). Lets the evidence
        packet bucket signals without parsing ``detail``.
    event_indices
        0-based indices into ``Transcript.events`` that justify this signal.
        Every signal MUST cite at least one event. An empty tuple is a bug.
    summary
        One-line human-readable description. Shown to the verifier subagent.
    detail
        Detector-specific structured payload. Schema is documented per
        detector below. Never contains verdicts.
    confidence
        ``OBSERVED`` for direct tool-call observations; ``INFERRED`` for
        pattern matches. The verifier must treat INFERRED signals as
        candidates, not facts.
    """

    kind: str
    event_indices: tuple[int, ...]
    summary: str
    detail: dict[str, Any] = field(default_factory=dict)
    confidence: str = "OBSERVED"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "event_indices": list(self.event_indices),
            "summary": self.summary,
            "detail": dict(self.detail),
            "confidence": self.confidence,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _first_present(d: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    """Return the first present string value among ``keys`` in ``d``."""
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v:
            return v
    return None


def _normalize_path(p: str) -> str:
    """Normalise a path to forward slashes; never invent."""
    return p.replace("\\", "/")


def _snippet(text: str, max_len: int = 160) -> str:
    """Collapse whitespace and truncate, preserving the lead of the text."""
    if not text:
        return ""
    collapsed = re.sub(r"\s+", " ", text).strip()
    if len(collapsed) <= max_len:
        return collapsed
    return collapsed[: max_len - 1] + "…"


def _assistant_text_events(transcript: Transcript) -> list[tuple[int, Event]]:
    """Return ``[(index, event)]`` for assistant events with non-empty text."""
    out: list[tuple[int, Event]] = []
    for i, ev in enumerate(transcript.events):
        if ev.role is Role.ASSISTANT and ev.text:
            out.append((i, ev))
    return out


def _find_tool_result_for_call(transcript: Transcript, tool_call_id: str) -> tuple[int, Event] | None:
    """Resolve the tool_result event for a given tool_call.id, or None.

    O(log n) is possible with an index, but transcripts are small (max few
    thousand events); linear scan is fine and keeps the parser/detector
    boundary clean.
    """
    for i, ev in enumerate(transcript.events):
        if ev.role is Role.TOOL_RESULT and ev.tool_call_id == tool_call_id:
            return (i, ev)
    return None


# ---------------------------------------------------------------------------
# Detector 1: file_edits
# ---------------------------------------------------------------------------


def detect_file_edits(transcript: Transcript) -> list[Signal]:
    """Every tool call that wrote or edited a file.

    ``detail``: ``{"tool": <name>, "target_path": <str|None>, "op": <label>}``.
    ``target_path`` is None when the call's arguments lacked a path key
    (the verifier should flag this — a write without a target is suspicious).
    """
    signals: list[Signal] = []
    for i, ev in enumerate(transcript.events):
        if ev.role is not Role.ASSISTANT:
            continue
        for tc in ev.tool_calls:
            if tc.name not in WRITE_TOOLS:
                continue
            target = _first_present(tc.arguments, WRITE_PATH_KEYS)
            target_norm = _normalize_path(target) if target else None
            op = "create" if tc.name in {"create_file", "Write", "write", "create_file_or_dir"} else "edit"
            signals.append(
                Signal(
                    kind="file_edits",
                    event_indices=(i,),
                    summary=f"{op} {target_norm or '<no target path in args>'}",
                    detail={
                        "tool": tc.name,
                        "target_path": target_norm,
                        "op": op,
                        "arguments_parse_error": tc.parse_error,
                    },
                )
            )
    return signals


# ---------------------------------------------------------------------------
# Detector 2: command_executions
# ---------------------------------------------------------------------------


def detect_command_executions(transcript: Transcript) -> list[Signal]:
    """Every shell/terminal command plus its exit code (if recoverable).

    ``detail``: ``{"tool": <name>, "command": <str|None>, "exit_code": <int|None>,
    "result_event_index": <int|None>}``. Exit code is parsed from the matching
    tool_result's text via the ``exit: N`` pattern; None if not found.
    """
    signals: list[Signal] = []
    for i, ev in enumerate(transcript.events):
        if ev.role is not Role.ASSISTANT:
            continue
        for tc in ev.tool_calls:
            if tc.name not in COMMAND_TOOLS:
                continue
            command = _first_present(tc.arguments, COMMAND_ARG_KEYS)
            exit_code: int | None = None
            result_idx: int | None = None
            if tc.id:
                pair = _find_tool_result_for_call(transcript, tc.id)
                if pair is not None:
                    result_idx, result_ev = pair
                    if result_ev.text:
                        m = EXIT_NONZERO_PATTERN.search(result_ev.text)
                        if m:
                            exit_code = int(m.group(1))
                        elif re.search(r"\bexit(?:\s+code)?:\s*0\b", result_ev.text):
                            exit_code = 0
            signals.append(
                Signal(
                    kind="command_executions",
                    event_indices=(i,) + ((result_idx,) if result_idx is not None else ()),
                    summary=_snippet(command or "<no command in args>", 120),
                    detail={
                        "tool": tc.name,
                        "command": command,
                        "exit_code": exit_code,
                        "result_event_index": result_idx,
                    },
                )
            )
    return signals


# ---------------------------------------------------------------------------
# Detector 3: test_runs
# ---------------------------------------------------------------------------


def detect_test_runs(transcript: Transcript) -> list[Signal]:
    """Subset of command_executions whose command matches a test framework.

    ``detail``: ``{"framework": <label>, "command": <str>, "exit_code": <int|None>,
    "result_event_index": <int|None>}``. ``framework`` is the matched label
    from ``TEST_FRAMEWORK_PATTERNS``. A run with exit_code=0 is a passing
    candidate (verifier still inspects output); exit_code>=1 is failing.
    """
    signals: list[Signal] = []
    for i, ev in enumerate(transcript.events):
        if ev.role is not Role.ASSISTANT:
            continue
        for tc in ev.tool_calls:
            if tc.name not in COMMAND_TOOLS:
                continue
            command = _first_present(tc.arguments, COMMAND_ARG_KEYS)
            if not command:
                continue
            framework = None
            for pat, label in TEST_FRAMEWORK_PATTERNS:
                if pat.search(command):
                    framework = label
                    break
            if framework is None:
                continue
            exit_code: int | None = None
            result_idx: int | None = None
            if tc.id:
                pair = _find_tool_result_for_call(transcript, tc.id)
                if pair is not None:
                    result_idx, result_ev = pair
                    if result_ev.text:
                        m = EXIT_NONZERO_PATTERN.search(result_ev.text)
                        if m:
                            exit_code = int(m.group(1))
                        elif re.search(r"\bexit(?:\s+code)?:\s*0\b", result_ev.text):
                            exit_code = 0
            signals.append(
                Signal(
                    kind="test_runs",
                    event_indices=(i,) + ((result_idx,) if result_idx is not None else ()),
                    summary=f"{framework}: {_snippet(command, 100)}",
                    detail={
                        "framework": framework,
                        "command": command,
                        "exit_code": exit_code,
                        "result_event_index": result_idx,
                    },
                )
            )
    return signals


# ---------------------------------------------------------------------------
# Detector 4: verification_tool_calls
# ---------------------------------------------------------------------------


def detect_verification_tool_calls(transcript: Transcript) -> list[Signal]:
    """Every read/grep/glob/list call — evidence the agent inspected something.

    ``detail``: ``{"tool": <name>, "target": <str|None>}``. These are the
    calls that *could* substantiate a claim. Detector 10 uses this set to
    find claims with no nearby verification.
    """
    signals: list[Signal] = []
    for i, ev in enumerate(transcript.events):
        if ev.role is not Role.ASSISTANT:
            continue
        for tc in ev.tool_calls:
            if tc.name not in READ_TOOLS:
                continue
            target = _first_present(tc.arguments, READ_PATH_KEYS)
            signals.append(
                Signal(
                    kind="verification_tool_calls",
                    event_indices=(i,),
                    summary=f"{tc.name} {target or ''}".strip(),
                    detail={
                        "tool": tc.name,
                        "target": _normalize_path(target) if target else None,
                    },
                )
            )
    return signals


# ---------------------------------------------------------------------------
# Detector 5: claim_verbs
# ---------------------------------------------------------------------------


def detect_claim_verbs(transcript: Transcript) -> list[Signal]:
    """Assistant text snippets that assert completion/verification.

    ``detail``: ``{"verb": <label>, "snippet": <str>}``. ``confidence`` is
    always ``INFERRED`` — a phrase match is a candidate claim, not proof of
    one. The verifier resolves whether the claim is real and whether it is
    backed by evidence.
    """
    signals: list[Signal] = []
    for i, ev in _assistant_text_events(transcript):
        for pat, verb in CLAIM_VERB_PATTERNS:
            for m in pat.finditer(ev.text or ""):
                start = max(0, m.start() - 30)
                end = min(len(ev.text or ""), m.end() + 60)
                snippet = _snippet(ev.text[start:end])
                signals.append(
                    Signal(
                        kind="claim_verbs",
                        event_indices=(i,),
                        summary=f"{verb}: {snippet}",
                        detail={
                            "verb": verb,
                            "matched_text": m.group(0),
                            "snippet": snippet,
                            "match_start": m.start(),
                        },
                        confidence="INFERRED",
                    )
                )
    return signals


# ---------------------------------------------------------------------------
# Detector 6: failures
# ---------------------------------------------------------------------------


def detect_failures(transcript: Transcript) -> list[Signal]:
    """Objective failure markers: non-zero exits, tracebacks, FAIL/ERROR tokens.

    ``detail``: ``{"kind": <label>, "snippet": <str>}``. ``kind`` is one of
    ``nonzero_exit``, ``traceback``, ``exception_name``, ``fail_token``,
    ``error_token``. Source may be a tool_result text or a command output.

    Failures here are *observations*. A non-zero exit during exploration is
    not a session defect — the verifier decides severity in context.
    """
    signals: list[Signal] = []

    # Non-zero exits and tracebacks from tool_result content.
    for i, ev in enumerate(transcript.events):
        if ev.role is not Role.TOOL_RESULT or not ev.text:
            continue
        for m in EXIT_NONZERO_PATTERN.finditer(ev.text):
            signals.append(
                Signal(
                    kind="failures",
                    event_indices=(i,),
                    summary=f"nonzero_exit code={m.group(1)}",
                    detail={
                        "kind": "nonzero_exit",
                        "exit_code": int(m.group(1)),
                        "snippet": _snippet(ev.text),
                    },
                )
            )
        if TRACEBACK_PATTERN.search(ev.text):
            # Pull the exception line if present.
            exc_match = EXCEPTION_PATTERN.search(ev.text)
            exc_name = exc_match.group(1) if exc_match else None
            signals.append(
                Signal(
                    kind="failures",
                    event_indices=(i,),
                    summary=f"traceback{f' {exc_name}' if exc_name else ''}",
                    detail={
                        "kind": "traceback",
                        "exception_name": exc_name,
                        "snippet": _snippet(ev.text),
                    },
                )
            )
        elif EXCEPTION_PATTERN.search(ev.text):
            # Exception name without a traceback (e.g. logged error).
            exc_match = EXCEPTION_PATTERN.search(ev.text)
            exc_name = exc_match.group(1) if exc_match else None
            signals.append(
                Signal(
                    kind="failures",
                    event_indices=(i,),
                    summary=f"exception {exc_name}",
                    detail={
                        "kind": "exception_name",
                        "exception_name": exc_name,
                        "snippet": _snippet(ev.text),
                    },
                )
            )
        if FAIL_TOKEN_PATTERN.search(ev.text):
            signals.append(
                Signal(
                    kind="failures",
                    event_indices=(i,),
                    summary="FAIL token in output",
                    detail={"kind": "fail_token", "snippet": _snippet(ev.text)},
                )
            )
        if ERROR_TOKEN_PATTERN.search(ev.text):
            signals.append(
                Signal(
                    kind="failures",
                    event_indices=(i,),
                    summary="ERROR: token in output",
                    detail={"kind": "error_token", "snippet": _snippet(ev.text)},
                )
            )
    return signals


# ---------------------------------------------------------------------------
# Detector 7: todo_state_changes
# ---------------------------------------------------------------------------


def detect_todo_state_changes(transcript: Transcript) -> list[Signal]:
    """Every todo_write / TodoWrite call with its resulting state.

    ``detail``: ``{"total": <int>, "by_status": {status: count},
    "completed": <int>, "in_progress": <int>, "pending": <int>,
    "cancelled": <int>}``. This lets a verifier check "agent claimed all
    done" vs "agent actually marked items cancelled or left pending".
    """
    signals: list[Signal] = []
    for i, ev in enumerate(transcript.events):
        if ev.role is not Role.ASSISTANT:
            continue
        for tc in ev.tool_calls:
            if tc.name not in TODO_TOOLS:
                continue
            todos = tc.arguments.get("todos")
            if not isinstance(todos, list):
                continue
            by_status: dict[str, int] = {}
            for item in todos:
                if isinstance(item, dict):
                    st = str(item.get("status", "unknown"))
                    by_status[st] = by_status.get(st, 0) + 1
            signals.append(
                Signal(
                    kind="todo_state_changes",
                    event_indices=(i,),
                    summary=f"todo_write total={len(todos)} statuses={by_status}",
                    detail={
                        "total": len(todos),
                        "by_status": by_status,
                        "completed": by_status.get("completed", 0),
                        "in_progress": by_status.get("in_progress", 0),
                        "pending": by_status.get("pending", 0),
                        "cancelled": by_status.get("cancelled", 0),
                    },
                )
            )
    return signals


# ---------------------------------------------------------------------------
# Detector 8: scope_files
# ---------------------------------------------------------------------------


def detect_scope_files(transcript: Transcript) -> list[Signal]:
    """Distinct set of file paths the session touched.

    Emits a SINGLE aggregation signal (not one per file) so the verifier can
    compare the full set against the stated scope. ``detail``:
    ``{"files": [...], "count": N, "by_source": {"edited": [...],
    "read": [...]}}``.
    """
    edited: dict[str, list[int]] = {}
    read: dict[str, list[int]] = {}
    for i, ev in enumerate(transcript.events):
        if ev.role is not Role.ASSISTANT:
            continue
        for tc in ev.tool_calls:
            if tc.name in WRITE_TOOLS:
                p = _first_present(tc.arguments, WRITE_PATH_KEYS)
                if p:
                    edited.setdefault(_normalize_path(p), []).append(i)
            elif tc.name in READ_TOOLS:
                p = _first_present(tc.arguments, READ_PATH_KEYS)
                if p:
                    read.setdefault(_normalize_path(p), []).append(i)
    all_files = sorted(set(edited) | set(read))
    if not all_files:
        return []
    # Cite up to 8 representative events to keep the signal small.
    cite: list[int] = []
    for bucket in (edited, read):
        for path in sorted(bucket):
            for idx in bucket[path]:
                if idx not in cite:
                    cite.append(idx)
                if len(cite) >= 8:
                    break
            if len(cite) >= 8:
                break
        if len(cite) >= 8:
            break
    return [
        Signal(
            kind="scope_files",
            event_indices=tuple(cite),
            summary=f"{len(all_files)} distinct files touched",
            detail={
                "files": all_files,
                "count": len(all_files),
                "by_source": {
                    "edited": sorted(edited),
                    "read": sorted(read),
                },
            },
        )
    ]


# ---------------------------------------------------------------------------
# Detector 9: subagent_spawns
# ---------------------------------------------------------------------------


def detect_subagent_spawns(transcript: Transcript) -> list[Signal]:
    """Every spawn_subagent / Task dispatch.

    ``detail``: ``{"subagent_type": <str|None>, "description": <str|None>,
    "prompt_present": <bool>}``. Confirms the agent actually dispatched
    subagents (rather than just claiming to).
    """
    signals: list[Signal] = []
    for i, ev in enumerate(transcript.events):
        if ev.role is not Role.ASSISTANT:
            continue
        for tc in ev.tool_calls:
            if tc.name not in SUBAGENT_TOOLS:
                continue
            sub_type = tc.arguments.get("subagent_type") or tc.arguments.get("type")
            desc = tc.arguments.get("description")
            prompt_present = bool(tc.arguments.get("prompt"))
            signals.append(
                Signal(
                    kind="subagent_spawns",
                    event_indices=(i,),
                    summary=f"spawn {sub_type or '<no type>'}: {desc or '<no description>'}",
                    detail={
                        "subagent_type": sub_type if isinstance(sub_type, str) else None,
                        "description": desc if isinstance(desc, str) else None,
                        "prompt_present": prompt_present,
                    },
                )
            )
    return signals


# ---------------------------------------------------------------------------
# Detector 10: unverified_claim_candidates
# ---------------------------------------------------------------------------


def detect_unverified_claim_candidates(transcript: Transcript) -> list[Signal]:
    """claim_verbs with no verification_tool_call within ``UNVERIFIED_CLAIM_WINDOW``.

    This is the highest-value /check signal: claims without nearby evidence.
    ``detail``: ``{"verb": <label>, "snippet": <str>,
    "verification_in_window": <bool>,
    "nearest_verification_distance": <int|None>,
    "window_size": <int>}``. ``confidence="INFERRED"`` — "no nearby
    verification" is not "no verification at all"; the verifier should
    consider the whole session context.
    """
    claims = detect_claim_verbs(transcript)
    if not claims:
        return []
    verifications = detect_verification_tool_calls(transcript)
    verification_indices = [vi for sig in verifications for vi in sig.event_indices]
    if not verification_indices:
        verification_set: set[int] = set()
    else:
        verification_set = set(verification_indices)

    n = len(transcript.events)
    signals: list[Signal] = []
    for claim in claims:
        claim_idx = claim.event_indices[0]
        # Bidirectional window: an agent may verify BEFORE claiming
        # ("I read the file and confirmed X") or AFTER ("X is done" → read
        # to check). Either counts as backing the claim.
        fwd_start = claim_idx + 1
        fwd_end = min(claim_idx + UNVERIFIED_CLAIM_WINDOW + 1, n)
        bwd_start = max(0, claim_idx - UNVERIFIED_CLAIM_WINDOW)
        bwd_end = claim_idx
        nearest_fwd: int | None = next(
            (j for j in range(fwd_start, fwd_end) if j in verification_set), None
        )
        nearest_bwd: int | None = next(
            (j for j in range(bwd_end - 1, bwd_start - 1, -1) if j in verification_set),
            None,
        )
        if nearest_fwd is not None or nearest_bwd is not None:
            # Claim IS backed within the window — skip it.
            continue
        signals.append(
            Signal(
                kind="unverified_claim_candidates",
                event_indices=claim.event_indices,
                summary=f"unverified {claim.detail.get('verb')}: {claim.detail.get('snippet', '')[:80]}",
                detail={
                    "verb": claim.detail.get("verb"),
                    "snippet": claim.detail.get("snippet"),
                    "verification_in_window": False,
                    "nearest_verification_distance": None,
                    "window_size": UNVERIFIED_CLAIM_WINDOW,
                },
                confidence="INFERRED",
            )
        )
    return signals


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------


def run_all_detectors(transcript: Transcript) -> dict[str, list[Signal]]:
    """Run all 10 detectors and bucket their signals by ``kind``.

    Returns a dict keyed by detector name. Every detector is called even if
    one earlier detector returns nothing — detectors are independent.
    Missing keys would be a bug; consumers may assume all 10 are present.
    """
    return {
        "file_edits": detect_file_edits(transcript),
        "command_executions": detect_command_executions(transcript),
        "test_runs": detect_test_runs(transcript),
        "verification_tool_calls": detect_verification_tool_calls(transcript),
        "claim_verbs": detect_claim_verbs(transcript),
        "failures": detect_failures(transcript),
        "todo_state_changes": detect_todo_state_changes(transcript),
        "scope_files": detect_scope_files(transcript),
        "subagent_spawns": detect_subagent_spawns(transcript),
        "unverified_claim_candidates": detect_unverified_claim_candidates(transcript),
    }
