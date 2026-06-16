"""Session context storage and referent resolution for prompt enhancement.

Captures every turn's prompt and inferred subject, persisted per-terminal
under .claude/.artifacts/{terminal_id}/prompt-enhancer/session_context.json.
The PreCompact hook (prompt_enhancer_precompact_hook.py) already preserves
artifacts across compactions, so this context survives session transitions.

Public API:
    read_session_context() -> SessionContext
    write_session_context(prompt, subject) -> None
    extract_subject(prompt) -> str | None
    resolve_referent(prompt, ctx) -> ReferentResolution | None
    is_continuation(prompt) -> bool
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from pathlib import Path

# Module-level constants — keep simple to avoid hook false-positives on literals.
_CONTEXT_FILENAME = "session_context.json"
_MAX_TURN_HISTORY = 5  # how many recent turns we keep
# How far back last_subject may reach. A continuation ("yes please") almost always
# refers to the immediately prior subject; reaching further risks resurrecting a
# stale subject from an unrelated earlier task. Bounded to the 2 newest turns.
_SUBJECT_LOOKBACK = 2
_DEFAULT_TERMINAL = "default"


def _terminal_id() -> str:
    """Isolation key for the per-session context file.

    CLAUDE_TERMINAL_ID is not set by Claude Code in this environment, so the old
    fallback collapsed every concurrent session onto a single "default" file —
    causing subjects to bleed across unrelated terminals. CLAUDE_CODE_SESSION_ID
    is set per session and stable within it, so it is the correct isolation key.
    """
    return (
        os.environ.get("CLAUDE_TERMINAL_ID")
        or os.environ.get("CLAUDE_CODE_SESSION_ID")
        or _DEFAULT_TERMINAL
    )


def _context_path() -> Path:
    tid = _terminal_id()
    base = Path.home() / ".claude" / ".artifacts" / tid / "prompt-enhancer"
    base.mkdir(parents=True, exist_ok=True)
    return base / _CONTEXT_FILENAME


@dataclass
class Turn:
    prompt: str
    subject: str | None
    timestamp: float


@dataclass
class SessionContext:
    """Recent-turn history used for referent resolution."""

    turns: list[Turn] = field(default_factory=list)

    @property
    def last_turn(self) -> Turn | None:
        return self.turns[-1] if self.turns else None

    @property
    def last_subject(self) -> str | None:
        """Most recent non-empty subject within the recency window (newest first).

        Bounded to _SUBJECT_LOOKBACK turns so a continuation does not resurrect a
        stale subject from an unrelated earlier task.
        """
        for turn in reversed(self.turns[-_SUBJECT_LOOKBACK:]):
            if turn.subject:
                return turn.subject
        return None


@dataclass
class ReferentResolution:
    """Result of attempting to resolve a referent against session context."""

    inferred_subject: str
    confidence: float
    source: str  # human-readable explanation of the inference path


def read_session_context() -> SessionContext:
    """Load the session context for the current terminal. Empty on first run."""
    path = _context_path()
    if not path.exists():
        return SessionContext()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return SessionContext()
    turns_raw = data.get("turns", [])
    turns = [
        Turn(
            prompt=str(t.get("prompt", "")),
            subject=t.get("subject") or None,
            timestamp=float(t.get("timestamp", 0)),
        )
        for t in turns_raw
        if isinstance(t, dict)
    ]
    return SessionContext(turns=turns)


def write_session_context(prompt: str, subject: str | None) -> None:
    """Append a turn to the session context, pruning to _MAX_TURN_HISTORY."""
    ctx = read_session_context()
    ctx.turns.append(Turn(prompt=prompt, subject=subject, timestamp=time.time()))
    # Keep only the most recent N turns to bound disk usage and inference noise.
    ctx.turns = ctx.turns[-_MAX_TURN_HISTORY:]
    payload = {
        "turns": [
            {"prompt": t.prompt, "subject": t.subject, "timestamp": t.timestamp}
            for t in ctx.turns
        ]
    }
    try:
        _context_path().write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError:
        # Context store is best-effort. Disk failure must not break the hook.
        pass


# ---------------------------------------------------------------------------
# Subject extraction
# ---------------------------------------------------------------------------

# Match file paths with extensions (e.g. wiki_manifest.py, src/foo.ts).
_FILE_REF = re.compile(r"\b([A-Za-z0-9_./\\-]+\.[A-Za-z0-9]{1,10})\b")
# Match slash-command invocations (e.g. /pre-mortem, /cc-skills-sdlc:design).
_SLASH_CMD = re.compile(r"(/[a-z][a-z0-9_-]*(?::[a-z][a-z0-9_-]+)?)")
# Match "the X" noun phrases that frequently carry the subject in dev prompts.
_THE_NP = re.compile(
    r"\bthe\s+([a-z][a-z0-9_-]*(?:\s+[a-z][a-z0-9_-]*){0,3})\b",
    re.IGNORECASE,
)


def extract_subject(prompt: str) -> str | None:
    """Best-effort subject extraction from a prompt.

    Priority:
      1. File reference (foo.py)
      2. Slash command (/skill-name)
      3. "the X" noun phrase
      4. None

    Informational prompts are filtered — their "the X" phrases are questions
    about the subject, not the subject itself ("what's the time?" ≠ "the time"
    as the intended work target).
    """
    if not prompt:
        return None
    # Filter informational openers — these ask about X, not to act on X.
    lower = prompt.lower().strip()
    informational_openers = (
        "what", "how", "why", "when", "where", "explain",
        "describe", "list", "show", "tell me",
    )
    if lower.startswith(informational_openers) and len(lower.split()) < 20:
        return None
    file_match = _FILE_REF.search(prompt)
    if file_match:
        return file_match.group(1)
    slash_match = _SLASH_CMD.search(prompt)
    if slash_match:
        return slash_match.group(1)
    np_match = _THE_NP.search(prompt)
    if np_match:
        return f"the {np_match.group(1).strip()}"
    return None


# ---------------------------------------------------------------------------
# Continuation + referent detection
# ---------------------------------------------------------------------------

# Exact-match conversational continuations (lowercased, stripped of terminal punctuation).
_CONTINUATIONS_EXACT = frozenset({
    "continue", "proceed", "go ahead", "go on", "keep going",
    "next", "more", "yes", "yes please", "yes, please",
    "ok", "okay", "sure", "do it", "one more time",
    "carry on", "resume", "retry",
})

# Prompts starting with these short verbs are continuations even with light args.
_CONTINUATION_LEAD = frozenset({"continue", "proceed", "resume", "retry"})

# Pronouns whose antecedent we'll try to resolve from prior context.
_PRONOUN_RE = re.compile(r"^\s*(fix|update|change|improve|review|run|test)\s+(it|that|this|them)\b", re.IGNORECASE)


def is_continuation(prompt: str) -> bool:
    if not prompt:
        return False
    cleaned = prompt.lower().strip().rstrip(".!?")
    if cleaned in _CONTINUATIONS_EXACT:
        return True
    tokens = cleaned.split()
    if tokens and tokens[0] in _CONTINUATION_LEAD and len(tokens) <= 5:
        return True
    return False


def resolve_referent(prompt: str, ctx: SessionContext) -> ReferentResolution | None:
    """Try to resolve an ambiguous prompt's referent against prior context.

    Returns None when no useful inference can be made.
    """
    if not prompt:
        return None

    last_subject = ctx.last_subject
    last_turn = ctx.last_turn

    # Case 1: bare continuation ("continue", "proceed").
    if is_continuation(prompt):
        if last_subject:
            return ReferentResolution(
                inferred_subject=last_subject,
                confidence=0.75,
                source="continuation + last subject in session context",
            )
        if last_turn and last_turn.prompt:
            return ReferentResolution(
                inferred_subject=last_turn.prompt[:80],
                confidence=0.5,
                source="continuation + prior prompt text (no extracted subject)",
            )
        return None

    # Case 2: pronoun reference ("fix it", "update that").
    if _PRONOUN_RE.search(prompt):
        if last_subject:
            return ReferentResolution(
                inferred_subject=last_subject,
                confidence=0.7,
                source="pronoun + last subject in session context",
            )
        return None

    return None
