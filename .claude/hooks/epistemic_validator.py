#!/usr/bin/env python3
"""Unified epistemic validator for the Stop pipeline.

Analyzes model responses for structural correctness under the 4-section
contract, FACT support via citations, causal claim constraints, and
comparative judgment constraints. Pure Python — no LLM calls.

Replaces: StopHook_epistemic_contract.py (legacy, kept for reference).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Literal, Optional

Decision = Literal["allow", "warn", "block"]

# ---------------------------------------------------------------------------
# Epistemic policy layer
# ---------------------------------------------------------------------------
# Explicit policy governing epistemic enforcement as a function of turn kind
# and claim kind. Replaces ad-hoc bypass cascades with a readable table.
#
# Policy values:
#   "ignore" — treat as if no issue; do not contribute to decision
#   "allow"  — override to allow even if config says block
#   "warn"   — downgrade block→warn
#   "block"  — enforce block (respects config; this is the default)
#
# Principle: FORMAT_ONLY never blocks CONTROL/DEBUG modes; STANCE/CAUSAL/FACTUAL
# remain strict in ANALYSIS mode.

from enum import Enum


class ClaimKind(Enum):
    FORMAT_ONLY = "format_only"
    FACTUAL = "factual"
    CAUSAL = "causal"
    STANCE = "stance"
    UNKNOWN = "unknown"


class TurnKind(Enum):
    ANALYSIS = "analysis"
    CONTROL = "control"
    EXPLORATION = "exploration"
    DEBUG_META = "debug_meta"
    UNKNOWN = "unknown"


def _classify_claim_kind(issues: List["EpistemicIssue"]) -> ClaimKind:
    """Classify the dominant claim kind from a list of issues.

    Returns the highest-severity claim kind present. The policy table
    handles the case where no issues are present (returns UNKNOWN).
    """
    if not issues:
        return ClaimKind.UNKNOWN

    # Priority: CAUSAL > STANCE > FACTUAL > FORMAT_ONLY
    for issue in issues:
        if issue.type == "format":
            continue
        # unsupported_fact and comparative are factual-level claims
        if issue.type in ("unsupported_fact", "comparative_violation"):
            return ClaimKind.FACTUAL
        if issue.type.startswith("causal"):
            return ClaimKind.CAUSAL
    return ClaimKind.FORMAT_ONLY


# Signals that mark a response as a factual report rather than an analytical argument.
# Conservative: only matches obvious table/numbered-finding/evidence-citation structure.
# Used to reclassify UNKNOWN turns → CONTROL when the response is clearly a report.
_FACTUAL_REPORT_RE = re.compile(
    r"(?im)"
    r"(?:"
    # Markdown table: 4+ pipes, content between. Handles | a | b | c | and | Question | Finding |
    # Content may include spaces, dashes, colons (alignment markers), underscores, etc.
    r"^\s*\|[^|]*\|[^|]*\|[^|]*\|"  # 4+ pipes, content can be any non-| chars
    r"|^\s*\|[-: ]+\|[-: ]+\|"       # markdown separator |---|:---|  (space-tolerable content)
    r"|^\s*\d+\)\s+[A-Z]"        # numbered finding at line start
    r"|^\s*[-*]\s+[A-Z]{2,}-\d+\s*:"  # labeled bullet at line start
    r"|Evidence:\s"                 # evidence citation
    r"|\[FACT\]|\[INFERENCE\]|\[UNKNOWN\]|\[RECOMMENDATION\]"  # STATUS markers
    r"|^#{1,3}\s+Phase\s+\d+\s"  # markdown heading: ## Phase 1 Audit
    r"|^Phase\s+\d+\s+Audit:"       # Phase 1 Audit: at line start
    r"|^Phase\s+\d+\s+Report:"      # Phase 1 Report: at line start
    r"|Gap\s+Summary"                # Gap Summary header
    r")"
)
def _turn_kind_from_context(
    raw_response: str, default: TurnKind
) -> TurnKind:
    """Reclassify UNKNOWN turns based on response structure signals.

    Factual reports (audits, findings, inspection results) are CONTROL turns —
    they present verified findings in structured form, not make open-ended claims
    requiring [FACT]/[INFERENCE]/[RECOMMENDATION] framing.

    This is a second-pass reclassification: it only fires when the first-pass
    derivation returned UNKNOWN, so it cannot override legitimate ANALYSIS or
    CONTROL classifications.

    Substantive issues (FACTUAL, CAUSAL) remain enforceable in CONTROL mode per
    the policy table (CONTROL + FACTUAL = warn, not ignore).
    """
    if default != TurnKind.UNKNOWN:
        return default
    if not raw_response:
        return default
    if _FACTUAL_REPORT_RE.search(raw_response):
        return TurnKind.CONTROL
    return default


def _turn_kind_from_response_type(response_type: str, is_status_report: bool) -> TurnKind:
    """Map response characteristics to a turn kind.

    Status report responses are CONTROL regardless of other indicators —
    they restate known task state and need no evidence framing.
    """
    if is_status_report:
        return TurnKind.CONTROL
    if response_type == "investigation":
        return TurnKind.ANALYSIS
    if response_type == "analytical":
        return TurnKind.ANALYSIS
    return TurnKind.UNKNOWN


# Policy table: (turn_kind, claim_kind) → override Decision or None
# None means "no override — fall through to config-based decide_from_issues"
_POLICY_TABLE: dict[tuple[TurnKind, ClaimKind], Optional[Decision]] = {
    # CONTROL: format never blocks; substantive issues warn (not block)
    (TurnKind.CONTROL, ClaimKind.FORMAT_ONLY): "ignore",
    (TurnKind.CONTROL, ClaimKind.FACTUAL): "warn",
    (TurnKind.CONTROL, ClaimKind.CAUSAL): "warn",
    (TurnKind.CONTROL, ClaimKind.STANCE): "warn",
    (TurnKind.CONTROL, ClaimKind.UNKNOWN): "allow",

    # EXPLORATION: same as CONTROL — format is noise in open-ended turns
    (TurnKind.EXPLORATION, ClaimKind.FORMAT_ONLY): "ignore",
    (TurnKind.EXPLORATION, ClaimKind.FACTUAL): "warn",
    (TurnKind.EXPLORATION, ClaimKind.CAUSAL): "warn",
    (TurnKind.EXPLORATION, ClaimKind.STANCE): "warn",
    (TurnKind.EXPLORATION, ClaimKind.UNKNOWN): "allow",

    # DEBUG_META: no epistemic enforcement — talking about the gate itself
    (TurnKind.DEBUG_META, ClaimKind.FORMAT_ONLY): "ignore",
    (TurnKind.DEBUG_META, ClaimKind.FACTUAL): "ignore",
    (TurnKind.DEBUG_META, ClaimKind.CAUSAL): "ignore",
    (TurnKind.DEBUG_META, ClaimKind.STANCE): "ignore",
    (TurnKind.DEBUG_META, ClaimKind.UNKNOWN): "ignore",

    # ANALYSIS: format may warn but grounded content outside sections is allowed
    # CAUSAL/FACTUAL/STANCE remain strict via config
    (TurnKind.ANALYSIS, ClaimKind.FORMAT_ONLY): None,  # use config (usually warn)
    (TurnKind.ANALYSIS, ClaimKind.FACTUAL): None,  # use config (usually block)
    (TurnKind.ANALYSIS, ClaimKind.CAUSAL): None,  # use config (usually warn)
    (TurnKind.ANALYSIS, ClaimKind.STANCE): None,  # use config
    (TurnKind.ANALYSIS, ClaimKind.UNKNOWN): None,  # no issues — allow

    # UNKNOWN: default to config behavior (no override)
    (TurnKind.UNKNOWN, ClaimKind.FORMAT_ONLY): "warn",
    (TurnKind.UNKNOWN, ClaimKind.FACTUAL): None,
    (TurnKind.UNKNOWN, ClaimKind.CAUSAL): None,
    (TurnKind.UNKNOWN, ClaimKind.STANCE): None,
    (TurnKind.UNKNOWN, ClaimKind.UNKNOWN): "allow",
}


def get_epistemic_policy(
    turn_kind: TurnKind, claim_kind: ClaimKind
) -> Optional[Decision]:
    """Look up the epistemic policy for (turn_kind, claim_kind).

    Returns a Decision override, or None if the config-based logic should
    be used instead.
    """
    return _POLICY_TABLE.get((turn_kind, claim_kind))

# ---------------------------------------------------------------------------
# Regex patterns (originally from StopHook_epistemic_contract.py, now in _legacy/)
# ---------------------------------------------------------------------------

SECTION_ORDER = ["[FACT]", "[INFERENCE]", "[UNKNOWN]", "[RECOMMENDATION]"]
REPORT_SECTION_ORDER = [
    "[STATUS]", "[CHANGES]", "[RESULTS]", "[NEXT]",
    "FILES_CHANGED", "LOGIC_CHANGES", "TESTS", "LIMITATIONS",
    "Part 1", "Part 2", "Part 3", "Part 4", "Part 5", "Part 6",
]
BULLET_RE = re.compile(r"^\s*-\s+")
CITATION_RE = re.compile(r"\(source:\s*[^)]+\)", re.IGNORECASE)
USER_SOURCE_RE = re.compile(
    r"according to the user|user described|user said|user stated|user noted",
    re.IGNORECASE,
)

UNCERTAINTY_WORDS_RE = re.compile(
    r"\b(probably|likely|may|might|could|suspect|infer|seems?|appears?)\b",
    re.IGNORECASE,
)
RATIONALE_WORDS_RE = re.compile(
    r"""\b(
        because\s+(?!of\b)
      | since\s+(?!\d{4}\b|yesterday|last\s+|the\s+(?:last|previous|prior)|earlier|then\b)(?=\w+\s+(?:is|was|being|would|should|has|have|had))
      | so\s+that
      | in\s+order\s+to
      | to\s+ensure
      | to\s+avoid
      | given\s+that
      | for\s+minimal\s+code\s+churn
      | based\s+on\s+the\s+(?:error|logs?|output|results?|above|evidence|test)
      | to\s+minimize\s+
      | to\s+reduce\s+
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)
ASSUMPTION_WORDS_RE = re.compile(
    r"\b(given|assuming|if your goal is|if your priority is)\b",
    re.IGNORECASE,
)
HARD_ASSERTION_VERBS_RE = re.compile(
    r"\b(?:is|are|was|were|means|ensures|guarantees)\b",
    re.IGNORECASE,
)

CAUSAL_PHRASES_RE = re.compile(
    r"""
    \b
    (
        cause[sd]?
      | because\s+of\b
      | due\s+to\b
      | results?\s+in\b
      | result\s+of\b
      | lead[s]?\s+to\b
      | bring[s]?\s+about\b
      | give[s]?\s+rise\s+to\b
      | is\s+why\b
      | the\s+reason\s+is\b
      | the\s+reason\s+for\b
      | happens?\s+when\b
      | occurs?\s+when\b
      | is\s+caused\s+by\b
      | is\s+driven\s+by\b
      | is\s+triggered\s+by\b
    )
    \b
    """,
    re.IGNORECASE | re.VERBOSE,
)

COMPARATIVE_WORDS_RE = re.compile(
    r"""
    \b(
        best
      | better
      | superior
      | preferable
      | preferred
      | optimal
      | optimally
      | ideal
      | most\s+efficient
      | more\s+efficient
      | most\s+robust
      | more\s+robust
      | most\s+reliable
      | more\s+reliable
      | most\s+maintainable
      | more\s+maintainable
      | lowest[-\s]?risk
      | higher[-\s]?risk
      | safer
      | safest
      | more\s+scalable
      | most\s+scalable
      | simpler
      | simplest
      | more\s+complex
      | cleaner
      | cleanest
      | more\s+flexible
      | most\s+flexible
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

SUPERLATIVE_ONLY_RE = re.compile(
    r"\b(?:best|optimal|ideal|lowest[-\s]?risk|safest|most\s+\w+)\b",
    re.IGNORECASE,
)

EXTERNAL_QUOTE_RE = re.compile(
    r"according to|benchmark|documentation|docs|spec|measured|observed",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Response type classification (Evidence-First contract)
# ---------------------------------------------------------------------------

def _has_citation_markers(text: str) -> bool:
    """Check for evidence markers: file paths, line refs, code blocks, URLs, STATUS labels.

    STATUS section labels ([FACT], [INFERENCE], etc.) are included as evidence markers
    because structured responses with section headers indicate analytical/reporting
    mode rather than plain assertion.
    """
    markers = [
        r"P:\/[^\s]+",           # Windows file paths
        r"\/[^\s]+",             # Unix paths
        r"lines?\s+\d+",         # Line number refs
        r"```[\s\S]*?```",       # Code blocks
        r"https?:\/\/",          # URLs
        r"\(source:\s+",         # Citation suffix
        r"see\s+\w+\.py",        # Script references
        r"as\s+shown\s+in",      # Evidence phrase
        r"according\s+to",      # Attribution phrase
        r"[\w\-.\\\/]+\:\d+(?:\-\d+)?(?:\s|$)",  # bare path:line — "filter_models.py:60-67"
    ]
    return any(re.search(m, text, re.IGNORECASE) for m in markers)


def _is_repair_response_in_active_challenge(text: str, word_count: int) -> bool:
    """Check if this is a short repair response in an active challenge/repair context.

    When an epistemic format gate fires, the model tries to repair. Those repair
    attempts are inherently short and lack citation markers. Allow them through
    when: (a) there's an active challenge marker, and (b) the response is short.

    This is NOT based on keywords like 'pattern' or 'regex' — it's based on
    the challenge marker TTL mechanism already in the codebase.
    """
    if word_count > 20:
        return False  # Not a short repair — not our concern

    # Check if challenge marker is active (reuse existing mechanism)
    # Import here to avoid circular imports
    try:
        from StopHook_unverified_stance import _is_challenge_active

        # We need data dict — pass empty for TTL-only check
        # _is_challenge_active reads from state file, so we construct minimal data
        import os
        data = {
            "terminal_id": os.environ.get("CLAUDE_TERMINAL_ID", ""),
            "session_id": os.environ.get("CLAUDE_SESSION_ID", ""),
        }
        return _is_challenge_active(data)
    except Exception:
        return False  # Fail open — don't block on system errors


def _has_inference_marker(text: str) -> bool:
    """Check for explicit inference/uncertainty language."""
    markers = [
        "inferring from", "not verified", "i haven't verified",
        "i would need to", "assuming", "likely", "probably",
        "may be", "might be", "could be", "unverified",
        "would need to verify", "my memory may be stale",
    ]
    return any(m in text.lower() for m in markers)


def _is_direct_answer_to_question(response: str) -> bool:
    """Check if response is a direct answer to a question (not just a short assertion).

    A direct answer: starts with Yes/No, or responds to question content inline.
    A plain assertion: makes a claim without being a direct answer to the question.
    """
    stripped = response.strip().lower()

    # Direct yes/no answers
    if stripped.startswith(("yes,", "no,", "yes.", "no.", "yes ", "no ")):
        return True

    # Starts with a direct answer word (not a claim)
    if re.match(r"^(yes|no|confirm|absolutely|correct|incorrect|right|wrong)\b", stripped):
        return True

    # Question-sensitive direct answers: "is X", "does X", "can X", "will X", "should X"
    # These respond directly to the question without making an unsupported claim.
    # Exclude question-word leads (user input) — only allow actual answer starts.
    if re.match(r"^(is|does|can|will|should|would|has|have|had)\s+", stripped):
        if not re.match(r"^(what|why|how|who|when|where|which|whose|whom)", stripped):
            return True

    return False


# ---------------------------------------------------------------------------
# Grounded status confirmations — ultra-short restatements of recent verified
# output.  These are exempt from the citation/inference requirement because
# the evidence is already visible in the same interaction (e.g. pytest output
# was shown immediately before).  Substantive claims, summaries, and anything
# with implications still require citation.
# ---------------------------------------------------------------------------

# Token-count ceiling: <= 5 tokens keeps "103 passed." / "all passed." / "done."
# Character ceiling (~35 chars) catches bare number+verb combos like "3 failed".
# Minimum: 2 tokens — prevents "confirmed" (1 token) from sneaking through.
_STATUS_MIN_TOKENS = 2
_STATUS_MAX_TOKENS = 5
_STATUS_MAX_CHARS = 35

_STATUS_CONFIRMATION_PATTERNS = (
    # Pure count restatements: "<number> passed/failed/error"
    r"^\s*\d+\s+(?:passed|failed|errors?|ok|error)\s*\.?$",
    # All-clear and done signals
    r"^\s*(?:all\s+passed|all\s+ok|all\s+green|done|confirmed|fixed|complete)\s*\.?$",
    # yes-prefixed count restatements: "yes, 103 passed"
    r"^\s*yes,\s*\d+\s+(?:passed|failed|errors?)\s*\.?$",
    # Status-only lines from test runners: "N passed", "N failures"
    r"^\s*(?:\d+\s+passed|\d+\s+failed|\d+\s+failures?)\s*(?:on\s+.*)?$",
)


def _is_grounded_status_confirmation(text: str) -> bool:
    """Check for ultra-short status restatements that merely confirm fresh
    evidence already visible in the interaction (pytest output, command result,
    etc.).  These need no inline citation because the evidence precedes them.

    Exempts only bare status strings — no interpretation, recommendation,
    causal claim, or summary.  Anything longer or more complex still requires
    citation or uncertainty markers.
    """
    stripped = text.strip()
    if not stripped:
        return False

    # Must be short enough to qualify as a trivial restatement
    if len(stripped) > _STATUS_MAX_CHARS:
        return False

    # Tokenise loosely (whitespace split) — reject single-token responses.
    # "confirmed" alone is too generic to be a grounded restatement
    # (it may reference any prior event without specification).
    tokens = stripped.split()
    if len(tokens) > _STATUS_MAX_TOKENS:
        return False

    # Single-token responses: only "done" qualifies (clear terminal signal).
    # "confirmed"/"fixed"/"complete" as sole words lack grounding specificity.
    if len(tokens) == 1 and not re.match(r"^\s*done\s*\.?$", stripped, re.IGNORECASE):
        return False

    # Match against the confirmation pattern set
    for pattern in _STATUS_CONFIRMATION_PATTERNS:
        if re.match(pattern, stripped, re.IGNORECASE):
            return True

    return False


# ---------------------------------------------------------------------------
# Local tool-grounding helpers — allow short summaries of this turn's own
# tool output without requiring (source: file:line) boilerplate.
# ---------------------------------------------------------------------------

# Linking phrases that explicitly tie a sentence to this turn's tool output.
_LOCAL_TOOL_LINK_PHRASES = (
    r"from the .+ run (we )?(just )?(saw|above|here)",
    r"from the .+ output (we )?(just )?(saw|above|here)",
    r"from pytest( output)?( above| we just saw)?",
    r"from the pytest run( we just saw)?",
    r"based on the .+ (above|we just saw|run)",
    r"according to the .+ (above|we just saw|run)",
    r"the .+ (above|we just saw|run) shows",
    r"as shown (in|by) the .+ (above|above|run)",
    r"source:\s*pytest",  # "(source: pytest output above)"
    r"from the ls output above",
    r"from the ls (run|output)",
    r"from this (ls|grep|find|rg) output",
)

# Minimum linking phrase — sentence must contain at least one of these
# to be considered locally grounded (prevents arbitrary numeric matches).
_LINKING_WORD_RE = re.compile(
    r"\b(from|based on|according to|as shown|above|we just saw|we saw)\b",
    re.IGNORECASE,
)


def _has_local_tool_link(text: str) -> bool:
    """Return True if text contains an explicit link phrase to this turn's tool output."""
    return any(
        re.search(p, text, re.IGNORECASE) for p in _LOCAL_TOOL_LINK_PHRASES
    )


def _has_substantive_overlap(text: str, transcript: str) -> bool:
    """
    Return True if at least 2 substantive (len >= 3, non-stop-word) tokens
    from text are found in the transcript.

    Tokens are lowercased and stripped of trailing punctuation (.,;:!?).
    Filters out generic stop-words so that generic-word overlap alone
    does not falsely suggest grounding. Requires MULTIPLE content matches
    to ensure semantic relevance — a single shared word is not enough.
    """
    stop_words = frozenset({
        "the", "and", "for", "with", "this", "that", "from", "was", "are",
        "been", "have", "has", "had", "but", "not", "all", "can", "will",
        "just", "our", "out", "about", "above", "over", "into", "only",
        "is", "it", "as", "by", "or", "an", "be", "we", "so", "no",
    })
    text_lower = text.lower()
    transcript_lower = transcript.lower()
    substantive_tokens = [
        tok.strip(".,;:!?")  # strip trailing punctuation for fair comparison
        for tok in text_lower.split()
        if len(tok.strip(".,;:!?")) >= 3 and tok.strip(".,;:!?") not in stop_words
    ]
    if not substantive_tokens:
        return False
    overlap_count = sum(1 for tok in substantive_tokens if tok in transcript_lower)
    # Require 2+ substantive tokens so that incidental single-word
    # overlap (e.g. "workaround" from unrelated gate output) is insufficient
    # to create a false local-grounding signal.  Using 2 rather than 3 so that
    # genuinely local summaries (which typically have 3+ overlapping content
    # words) still pass while single-wokrel overlap fails.
    return overlap_count >= 2  # require at least 2 substantive tokens to overlap


def is_locally_grounded_in_this_turn(sentence: str, tool_transcript: str) -> bool:
    """
    Return True if sentence clearly cites/summarises tool output from this turn,
    using both:
      - a lexical linking phrase ("from pytest above", "based on the run we just saw")
      - and content overlap with the tool_transcript string.

    Without the linking phrase, numeric/text overlap alone is insufficient —
    we don't treat bare assertions as tool-grounded just because a similar
    string appears in the tool output.
    """
    if not sentence or not tool_transcript:
        return False
    if not _has_local_tool_link(sentence):
        return False
    return _has_substantive_overlap(sentence, tool_transcript)


def _is_locally_grounded_summary(
    text: str,
    tool_transcript: Optional[str],
    word_count: int,
) -> bool:
    """
    Check whether a response is a locally-grounded summary of this turn's
    tool output.  Used to bypass the citation/inference requirement for
    operator-mode summaries that explicitly link to visible evidence.

    Allow when:
      - Response is short (operator-mode summaries are terse)
      - Contains an explicit link phrase to this turn's tool output
      - Tool transcript is provided and overlaps with the response content.
    """
    # Compute from actual text to avoid stale/bogus word_count from caller.
    actual_word_count = len(text.split())
    if actual_word_count > 80:
        return False  # Not an operator-mode terse summary
    if not tool_transcript:
        return False
    if not _has_local_tool_link(text):
        return False
    return _has_substantive_overlap(text, tool_transcript)


def _classify_response_type(response: str) -> str:
    """Classify response to determine validation requirements.

    Returns: "simple" | "analytical" | "investigation"

    - "simple": short direct answers with citations; section format not mandatory
    - "analytical": longer reasoning, multi-step analysis; structure encouraged
    - "investigation": explicit multi-step with disagreement handling; enforce
    """
    if not response:
        return "simple"
    return _classify_response_type_python(response)


# ---------------------------------------------------------------------------
# Operator / explanation response guidance — optional one-turn coaching for
# investigation/patch/audit responses that would benefit from the 4-section
# format contract without being hard-blocked on first attempt.
# ---------------------------------------------------------------------------

def build_local_summary_guidance(tool_name: str, tool_transcript: str) -> str:
    """
    Build a short inline hint to guide the model toward a passable local-
    tool-summary style.  Used when a block is due to missing citation AND
    tool_transcript is available — the hint tells the model exactly what
    phrase pattern would work.

    The hint is injected as oneTurn guidance and is NOT persisted beyond
    the current turn.
    """
    if not tool_transcript:
        return ""
    preview = tool_transcript[:120].replace("\n", " ").strip()
    return (
        f"Tip for passing the epistemic gate on this turn: "
        f"To summarize \"{tool_name}\" output without a file citation, "
        f"use a linking phrase like \"from the {tool_name} run above\" or "
        f"\"based on the {tool_name} output we just saw\" AND ensure your "
        f"summary includes at least 2 substantive words ({'<word1>, <word2>'} style) "
        f"that overlap with the tool output below. "
        f'Example: "From the {tool_name} run above: {preview}..." '
        f"(keep the summary under 80 words total)."
    )


def validate_local_tool_summary_style(
    response_text: str,
    tool_transcript: str,
) -> dict:
    """
    Validate whether response_text could pass as a locally-grounded summary
    of tool output.  Returns a dict with:
      - pass: bool — True if the response would bypass the citation requirement
      - word_count: int
      - has_link: bool — has a local tool link phrase
      - overlap_count: int — substantive token overlap count
      - blocker: str — empty if passable, else reason for failure
    """
    if not response_text:
        return {"pass": False, "word_count": 0, "has_link": False,
                "overlap_count": 0, "blocker": "empty response"}
    if not tool_transcript:
        return {"pass": False, "word_count": len(response_text.split()),
                "has_link": False, "overlap_count": 0,
                "blocker": "no tool_transcript provided"}

    word_count = len(response_text.split())
    has_link = _has_local_tool_link(response_text)
    # Compute raw integer count (not bool from _has_substantive_overlap)
    stop_words = frozenset({
        "the", "and", "for", "with", "this", "that", "from", "was", "are",
        "been", "have", "has", "had", "but", "not", "all", "can", "will",
        "just", "our", "out", "about", "above", "over", "into", "only",
        "is", "it", "as", "by", "or", "an", "be", "we", "so", "no",
    })
    text_lower = response_text.lower()
    transcript_lower = tool_transcript.lower()
    substantive_tokens = [
        tok.strip(".,;:!?")
        for tok in text_lower.split()
        if len(tok.strip(".,;:!?")) >= 3 and tok.strip(".,;:!?") not in stop_words
    ]
    overlap_count = sum(1 for tok in substantive_tokens if tok in transcript_lower)

    if word_count > 80:
        return {"pass": False, "word_count": word_count, "has_link": has_link,
                "overlap_count": overlap_count,
                "blocker": f"response is {word_count} words (max 80)"}
    if not has_link:
        return {"pass": False, "word_count": word_count, "has_link": False,
                "overlap_count": overlap_count,
                "blocker": "missing linking phrase to tool output"}
    if overlap_count < 2:
        return {"pass": False, "word_count": word_count, "has_link": True,
                "overlap_count": overlap_count,
                "blocker": f"only {overlap_count} substantive token(s) overlap "
                           f"(minimum 2 required)"}
    return {"pass": True, "word_count": word_count, "has_link": True,
            "overlap_count": overlap_count, "blocker": ""}


def _classify_response_type_python(response: str) -> str:

    lines = response.split("\n")
    words = response.split()
    text_lower = response.lower()

    # PLAN-scaffold prefix: unconditionally treated as "investigation" regardless
    # of word count. The prefix is the dominant signal — a plan scaffold with
    # analytical content, not a status report.
    stripped = response.lstrip()
    if stripped.startswith("PLAN MODE"):
        return "investigation"

    # Short responses (under 12 words): check for plan markers first.
    # Plan markers ([PLAN], ## RATIONALE, ## ANALYSIS) are dominant signal
    # even in short responses and must route to investigation, not simple.
    if len(words) < 12:
        if stripped.startswith("[PLAN]"):
            return "investigation"
        if "## RATIONALE" in response or "## ANALYSIS" in response:
            return "investigation"
        # No plan prefix and no analytical signal → simple
        analytical_signal = any(
            p in text_lower for p in (
                "analysis:", "assess:", "investigation:", "assessment:",
                "my conclusion", "in summary", "to summarize",
            )
        )
        if not analytical_signal:
            return "simple"

    # STATUS-labeled responses: check for plan-scaffold mixed-mode.
    # A response that carries plan markers ([PLAN], ## RATIONALE, ## ANALYSIS)
    # alongside [FACT]/[INFERENCE] sections is a mixed-mode response that MUST
    # be routed to investigation validation, not collapsed to simple status.
    if any(s in response for s in ("[FACT]", "[INFERENCE]", "[UNKNOWN]", "[RECOMMENDATION]")):
        has_plan_marker = (
            stripped.startswith("[PLAN]")
            or "## RATIONALE" in response
            or "## ANALYSIS" in response
        )
        if has_plan_marker:
            return "investigation"
        return "simple"

    # Simple responses: short with evidence markers (file paths, line refs, citations)
    if len(lines) <= 5 and (
        _has_citation_markers(response)
        or _has_inference_marker(response)
    ):
        return "simple"

    # Investigation indicators: explicit sequential reasoning, disagreement
    investigation_phrases = [
        "first", "second", "third", "however", "but", "on the other hand",
        "contradiction", "evidence suggests", "root cause", "alternative view",
        "competing hypothesis", "falsifier", "divergence",
    ]
    if any(p in text_lower for p in investigation_phrases):
        return "investigation"

    # Analytical indicators: longer, structured reasoning
    analytical_phrases = [
        "analyze", "compare", "evaluate", "investigate", "explore",
        "assess", "recommend", "suggest", "conclusion", "reasoning",
        "hypothesis", "analysis",
    ]
    if any(p in text_lower for p in analytical_phrases):
        return "analytical"

    # Default to simple if no strong indicators
    return "simple"


def _check_missing_sections(clean: str) -> list[str]:
    """Return list of missing required sections."""
    return [s for s in SECTION_ORDER if s not in clean]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class EpistemicIssue:
    section: str  # "[FACT]", etc., or "__GLOBAL__"
    bullet_index: int  # 0-based, -1 for non-bullet/global
    type: str  # "format", "unsupported_fact", "causal_violation", "comparative_violation"
    message: str
    code: Optional[str] = None  # Structured issue code, e.g. "plan_mixed_substance"


@dataclass
class EpistemicVerdict:
    decision: Decision
    issues: List[EpistemicIssue]


@dataclass
class EpistemicConfig:
    mode: Decision = "warn"
    turn_mode: Optional[str] = None  # Schema-routing axis from Stop.py classification
    responseMode: str = "auto"  # "analysis", "report", or "auto"
    treat_format_violation_as: Decision = "block"
    treat_unsupported_fact_as: Decision = "block"
    treat_causal_violation_as: Decision = "warn"
    treat_comparative_violation_as: Decision = "warn"
    enable_causal_checks: bool = True
    enable_comparative_checks: bool = True
    # Optional tool transcript string from this turn — used to ground
    # local tool-output summaries without requiring (source: file:line).
    tool_transcript: Optional[str] = None


@dataclass
class ParsedBullet:
    section: str
    index: int  # 0-based within section
    text: str  # bullet text without leading "- "
    citations: List[str] = field(default_factory=list)
    has_claim: bool = False
    has_causal: bool = False
    has_comparative: bool = False


@dataclass
class ParsedResponse:
    bullets: List[ParsedBullet] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Schema validators (selected by explicit turn_mode)
# ---------------------------------------------------------------------------


def _has_plan_scaffold(raw_response: str) -> bool:
    """Return True if raw_response carries PLAN-mode scaffold markers.

    Scans ALL lines for unambiguous plan markers (not just first non-empty),
    which handles indented/non-first-line markers that lstrip()-based startswith
    would miss. Also checks for ## RATIONALE/## ANALYSIS body headers.
    """
    for line in raw_response.split("\n"):
        stripped = line.strip()
        if stripped.startswith("PLAN MODE") or stripped.startswith("[PLAN]"):
            return True

    # Check body for ## RATIONALE / ## ANALYSIS headers
    if "## RATIONALE" in raw_response or "## ANALYSIS" in raw_response:
        return True

    return False


def _validate_execution_report_schema(raw_response: str, cfg: EpistemicConfig) -> EpistemicVerdict:
    """Validate EXECUTION-REPORT mode responses.

    Execution reports summarize observable state (files created, tests run,
    commands executed). They are not analytical claims and do not require
    4-section structure. However, completion/fix claims require runtime evidence.
    """
    clean = sanitize_response(raw_response)
    parsed, format_issues = parse_sections(clean)
    issues: List[EpistemicIssue] = list(format_issues)

    # Completion/fix claims in execution reports are substantive assertions
    # that require evidence — block bare "is complete", "is fixed" claims.
    completion_patterns = [
        r"\bis\s+(?:now\s+)?(?:complete|done|fixed|resolved)\b",
        r"\b(?:task|implementation|feature)\s+(?:is\s+)?(?:complete|done)\b",
        r"\ball\s+\d+\s+tests?\s+passed\b",
        r"\bthe\s+bug\s+is\s+(?:fixed|resolved)\b",
    ]
    completion_re = re.compile("|".join(completion_patterns), re.IGNORECASE)
    if completion_re.search(raw_response):
        # Check if there is actual tool evidence in the transcript
        if not cfg.tool_transcript:
            issues.append(EpistemicIssue(
                section="__GLOBAL__", bullet_index=-1,
                type="unsupported_fact",
                message=(
                    "EXECUTION-REPORT contains completion/fix claim "
                    "without tool evidence. Include pytest output, "
                    "file list, or command result as evidence."
                ),
            ))

    if issues:
        decision = decide_from_issues(issues, cfg, response_type="simple", raw_response=raw_response)
        return EpistemicVerdict(decision=decision, issues=issues)
    return EpistemicVerdict(decision="allow", issues=[])


def _validate_report_schema(raw_response: str, cfg: EpistemicConfig) -> EpistemicVerdict:
    """Validate REPORT mode responses.

    Report mode is for status/deliverable summaries (files created, tasks done).
    It does NOT enforce the 4-section analytical contract. However, substantive
    completion claims without any evidence context are flagged.
    """
    issues: List[EpistemicIssue] = []

    # Substantive completion claims in report mode need some grounding.
    # A bare "implementation is complete" with no evidence is a weak claim.
    completion_re = re.compile(
        r"\b(?:implementation|task|feature|migration)\s+is\s+(?:complete|done)\b",
        re.IGNORECASE,
    )
    if completion_re.search(raw_response):
        has_context = (
            cfg.tool_transcript
            or any(s in raw_response for s in ("[FACT]", "source:", "(source:"))
        )
        if not has_context:
            issues.append(EpistemicIssue(
                section="__GLOBAL__", bullet_index=-1,
                type="unsupported_fact",
                message=(
                    "REPORT contains unsubstantiated completion claim. "
                    "Add evidence (file list, test count, command output) "
                    "or use tentative language (appears complete, likely done)."
                ),
            ))

    if issues:
        decision = decide_from_issues(issues, cfg, response_type="simple", raw_response=raw_response)
        return EpistemicVerdict(decision=decision, issues=issues)
    return EpistemicVerdict(decision="allow", issues=[])


def _validate_control_schema(raw_response: str, cfg: EpistemicConfig) -> EpistemicVerdict:
    """Validate CONTROL mode responses.

    CONTROL schema: substantive factual claims are violations.
    Control mode is for directives and system commands, not claims.
    """
    clean = sanitize_response(raw_response)
    parsed, format_issues = parse_sections(clean)
    issues: List[EpistemicIssue] = []

    # Substantive content (diagnosis, causal claim, specific attribution) in prose
    # is a CONTROL violation even when not formatted as a bullet.
    raw_lower = raw_response.lower()
    substantive_patterns = [
        "the bug is", "the issue is", "the problem is",
        "root cause", "caused by", "is due to",
        "at line ", "in file ", "in function ",
        "the fix is to", "should be changed to",
    ]
    if any(p in raw_lower for p in substantive_patterns):
        issues.append(EpistemicIssue(
            section="__GLOBAL__", bullet_index=-1,
            type="unsupported_fact",
            message="CONTROL mode response contains substantive diagnosis. "
                    "Use ANALYSIS mode for claims about root cause, specific locations, or fixes.",
        ))

    issues.extend(check_fact_support(parsed))

    if cfg.enable_causal_checks:
        issues.extend(check_causal_rules(parsed))
    if cfg.enable_comparative_checks:
        issues.extend(check_comparative_rules(parsed))

    if issues:
        decision = decide_from_issues(issues, cfg, response_type="simple", raw_response=raw_response)
        return EpistemicVerdict(decision=decision, issues=issues)
    return EpistemicVerdict(decision="allow", issues=[])


def _validate_plan_schema(raw_response: str, cfg: EpistemicConfig) -> EpistemicVerdict:
    """Validate PLAN mode responses.

    PLAN schema: lighter format requirements, but mixed-substance (plan +
    substantive diagnosis) is a violation. A plan response that contains
    root-cause investigation sections is flagged as mixed_substance, not
    silently reclassified to investigation schema.

    Unlike INVESTIGATION schema, PLAN schema does NOT require 4-section
    structure — only mixed-substance detection applies.
    """
    clean = sanitize_response(raw_response)
    parsed, format_issues = parse_sections(clean)
    # For PLAN schema: filter aggressively:
    # - "Missing required section" → expected (plan responses don't need [FACT] etc.)
    # - "Found N line(s) outside any section" → expected (plan bullets like [PLAN] and
    #   [RATIONALE] are not STATUS_ORDER sections; they are plan structure, not violations)
    issues: List[EpistemicIssue] = [
        issue for issue in format_issues
        if issue.code not in ("missing_section", "outside_section")
    ]

    # Mixed-substance detection: plan marker + RCA sections → violation
    has_rca_schema = any(
        header in raw_response for header in (
            "## Symptom", "## Evidence", "## Root Cause",
            "[FACT]", "[INFERENCE]", "[UNKNOWN]", "[RECOMMENDATION]",
        )
    )
    if has_rca_schema:
        issues.append(EpistemicIssue(
            section="__GLOBAL__", bullet_index=-1,
            type="format",
            message=(
                "PLAN mode response contains substantive diagnosis. "
                "Use ANALYSIS mode for root-cause investigation. "
                "Mixed-substance violation: plan responses must not contain "
                "RCA/section markers."
            ),
            code="plan_mixed_substance",
        ))

    # Substantive prose detection: bare analytical claims in PLAN responses.
    # Even without formal RCA section markers, phrases like "the bug is at line 42"
    # or "caused by X" are substantive diagnosis wrapped in plan camouflage.
    # This catches PLAN MODE + analytical prose that would otherwise slip through
    # the early PLAN gate's marker-only check.
    stripped_lower = raw_response.lower()
    substantive_patterns = [
        "the bug is", "the issue is", "the problem is",
        "root cause", "caused by", "is due to",
        "at line ", "in file ", "in function ",
        "the fix is to", "should be changed to",
    ]
    if any(p in stripped_lower for p in substantive_patterns):
        issues.append(EpistemicIssue(
            section="__GLOBAL__", bullet_index=-1,
            type="format",
            message=(
                "PLAN mode response contains substantive diagnosis. "
                "Use ANALYSIS mode for root-cause investigation. "
                "Mixed-substance violation: plan responses must not contain "
                "unframed analytical claims."
            ),
            code="plan_mixed_substance",
        ))

    # In PLAN schema, [FACT] bullets are assumed premises (not confirmed findings).
    # check_fact_support would flag them for missing citations, but citation
    # requirements are inappropriate for plan-mode assumed content.
    # Similarly, causal claims in PLAN [FACT]/[INFERENCE] sections are
    # hypothetical/assumed, not verified — causal_violation checks don't apply.
    # The only substantive violation in PLAN schema is mixed-substance
    # (plan marker + RCA sections), handled above.
    # NOTE: comparative claims are still substantive even in plan mode.
    if cfg.enable_comparative_checks:
        issues.extend(check_comparative_rules(parsed))

    decision = decide_from_issues(issues, cfg, response_type="analytical", raw_response=raw_response)
    return EpistemicVerdict(decision=decision, issues=issues)


def _validate_meta_schema(raw_response: str, cfg: EpistemicConfig) -> EpistemicVerdict:
    """Validate META mode responses.

    META schema: no structural requirements. Anti-lazy patterns apply
    (lazy_fix, sycophancy_capitulation) but plan_mode_futurizing is suppressed.
    """
    clean = sanitize_response(raw_response)
    parsed, format_issues = parse_sections(clean)
    issues: List[EpistemicIssue] = list(format_issues)

    issues.extend(check_fact_support(parsed))
    if cfg.enable_causal_checks:
        issues.extend(check_causal_rules(parsed))
    if cfg.enable_comparative_checks:
        issues.extend(check_comparative_rules(parsed))

    decision = decide_from_issues(issues, cfg, response_type="analytical", raw_response=raw_response)
    return EpistemicVerdict(decision=decision, issues=issues)


def _validate_investigation_schema(raw_response: str, cfg: EpistemicConfig) -> EpistemicVerdict:
    """Validate INVESTIGATION/ANALYSIS mode responses (full 4-section contract)."""
    clean = sanitize_response(raw_response)
    parsed, format_issues = parse_sections(clean)

    issues: List[EpistemicIssue] = list(format_issues)
    issues.extend(check_fact_support(parsed))
    if cfg.enable_causal_checks:
        issues.extend(check_causal_rules(parsed))
    if cfg.enable_comparative_checks:
        issues.extend(check_comparative_rules(parsed))

    issues = _filter_format_issues_for_response_type(issues, "investigation", _has_citation_markers(raw_response))

    strict_cfg = EpistemicConfig(
        mode="block",
        treat_format_violation_as=cfg.treat_format_violation_as,
        treat_unsupported_fact_as=cfg.treat_unsupported_fact_as,
        treat_causal_violation_as=cfg.treat_causal_violation_as,
        treat_comparative_violation_as=cfg.treat_comparative_violation_as,
        enable_causal_checks=cfg.enable_causal_checks,
        enable_comparative_checks=cfg.enable_comparative_checks,
        tool_transcript=cfg.tool_transcript,
    )
    decision = decide_from_issues(issues, strict_cfg, response_type="investigation", raw_response=raw_response)
    return EpistemicVerdict(decision=decision, issues=issues)


# ---------------------------------------------------------------------------
# Sanitization
# ---------------------------------------------------------------------------


def _strip_scaffolding_blocks(text: str) -> str:
    """Strip internal system scaffolding that should never reach the validator.

    Strips:
    - COGNITIVE GUARDRAILS ACTIVE blocks (ALL-CAPS headers)
    - REASONING CONTRACT blocks (ALL-CAPS headers)
    - RCA Contract Schema Required section headers
    - TEST STRATEGY CONTRACT multi-line blocks
    - [THINK:*] system blocks
    - cognitive-tags trailers (Tags:)

    These are hook-injected scaffolds that pollute classification and should
    not be treated as assistant-authored content.
    """
    if not text:
        return ""

    lines = text.splitlines()
    cleaned = []
    i = 0
    while i < len(lines):
        s = lines[i].strip()

        # Skip COGNITIVE GUARDRAILS ACTIVE block (all-CAPS header)
        if s == "COGNITIVE GUARDRAILS ACTIVE":
            # Skip this line and all subsequent lines until blank line or significant content
            i += 1
            while i < len(lines):
                next_s = lines[i].strip()
                if not next_s or next_s.startswith("**") or next_s.startswith("[") or next_s.startswith("-"):
                    # Stop at blank lines, markdown headers, or list items (content continues)
                    # But only stop at blank lines - the block continues until we hit a blank line
                    if not next_s.strip():
                        i += 1
                        break
                    i += 1
                else:
                    break
            continue

        # Skip REASONING CONTRACT block (all-CAPS header)
        # Fix (G3): `if not next_s:` → `if not next_s.strip():`
        # Whitespace-only lines were treated as blank-line terminators, causing
        # body content to be silently dropped when scaffold headers were
        # directly followed by indented prose.
        if s == "REASONING CONTRACT":
            i += 1
            while i < len(lines):
                next_s = lines[i].strip()
                if not next_s:
                    i += 1
                    break
                i += 1
            continue

        # Skip RCA Contract Schema Required section header (## RCA Contract...)
        # Fix (G1b): Require 'schema' AND ('rca' OR 'contract'). Prevents over-stripping
        # non-scaffold headers like '## Contract Bridge Design' (has 'contract', no 'schema').
        if s.startswith("## "):
            s_lower = s.lower()
            if "schema" in s_lower and ("rca" in s_lower or "contract" in s_lower):
                i += 1
                while i < len(lines):
                    next_s = lines[i].strip()
                    if not next_s or next_s.startswith("## "):
                        break
                    i += 1
                continue

        # Skip lines that are purely a TEST STRATEGY CONTRACT header/marker
        if "**TEST STRATEGY CONTRACT**" in s and len(s) < 200:
            i += 1
            # Skip following content lines until blank line or non-bullet
            while i < len(lines):
                next_s = lines[i].strip()
                if not next_s:
                    i += 1
                    break
                # Continuation lines (indented bullets, dashes)
                if next_s.startswith("-") or next_s.startswith("*"):
                    i += 1
                    continue
                break
            continue

        # Skip lines that are purely [THINK:*] system blocks
        if re.match(r"^\[THINK:[a-z_]+\]$", s, re.IGNORECASE):
            i += 1
            continue

        # Skip cognitive-tags trailers
        if s == "Tags:":
            i += 1
            continue

        cleaned.append(lines[i])
        i += 1

    return "\n".join(cleaned)


def _inline_sanitize(text: str) -> str:
    """Minimal inline sanitization when shared_helpers is unavailable."""
    if not text:
        return ""
    diag_prefixes = (
        "STATUS:", "UNVERIFIED CLAIMS:", "Evidence missing for:",
        "Stop hook error:", "Stop hook feedback:", "Ran ",
    )
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("#"):
            continue
        if s.startswith(">"):
            continue
        if any(s.startswith(p) for p in diag_prefixes):
            continue
        if re.match(r"^[-*_]{3,}\s*$", s):
            continue
        out.append(line)
    return "\n".join(out)


def sanitize_response(raw_response: str) -> str:
    """Strip non-claim lines (headers, quotes, Stop diagnostics) from response.

    Also strips known internal scaffolding that should never reach the validator:
    - TEST STRATEGY CONTRACT blockquotes
    - [THINK:*] system blocks
    - cognitive-tags trailers
    """
    try:
        from __lib.shared_helpers import strip_non_claim_lines
    except ImportError:
        strip_non_claim_lines = None

    # Strip TEST STRATEGY CONTRACT / [THINK:*] / cognitive-tags blocks first
    text = _strip_scaffolding_blocks(raw_response)

    if strip_non_claim_lines is not None:
        return strip_non_claim_lines(text)
    return _inline_sanitize(text)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_sections(clean: str) -> tuple[ParsedResponse, List[EpistemicIssue]]:
    """Parse cleaned text into sections and bullets.

    Returns (ParsedResponse, format_issues).
    """
    issues: List[EpistemicIssue] = []
    normalized = clean.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    # Split lines into sections
    current_section = ""
    section_lines: dict[str, list[str]] = {s: [] for s in SECTION_ORDER}
    global_lines: list[str] = []

    # Build closing tag patterns for stripping during parse
    # e.g. [/FACT] -> [FACT], [/INFERENCE] -> [INFERENCE], etc.
    closing_tags = {f"[/{tag[1:-1]}]" for tag in SECTION_ORDER}

    for line in lines:
        stripped = line.strip()
        # Skip closing tags (e.g. [/FACT], [/INFERENCE])
        if stripped in closing_tags:
            continue
        if stripped in SECTION_ORDER:
            current_section = stripped
            continue
        if current_section:
            section_lines[current_section].append(line)
        elif stripped:
            global_lines.append(line)

    # Check for text outside sections
    if global_lines:
        issues.append(EpistemicIssue(
            section="__GLOBAL__",
            bullet_index=-1,
            type="format",
            message=(
                f"Found {len(global_lines)} line(s) outside any "
                "[FACT]/[INFERENCE]/[UNKNOWN]/[RECOMMENDATION] section."
            ),
            code="outside_section",
        ))

    # Check section presence and order
    positions: dict[str, int] = {}
    for tag in SECTION_ORDER:
        idx = normalized.find(tag)
        if idx >= 0:
            positions[tag] = idx

    # Missing sections
    for tag in SECTION_ORDER:
        if tag not in positions:
            issues.append(EpistemicIssue(
                section=tag, bullet_index=-1, type="format",
                message=f"Missing required section {tag}.",
                code="missing_section",
            ))

    # Wrong order
    found_tags = [t for t in SECTION_ORDER if t in positions]
    for i in range(len(found_tags) - 1):
        if positions[found_tags[i]] > positions[found_tags[i + 1]]:
            issues.append(EpistemicIssue(
                section="__GLOBAL__", bullet_index=-1, type="format",
                message=(
                    f"Section {found_tags[i]} appears after {found_tags[i + 1]}. "
                    f"Order must be: {' '.join(SECTION_ORDER)}."
                ),
            ))

    # Parse bullets
    parsed = ParsedResponse()
    for section in SECTION_ORDER:
        for idx, line in enumerate(section_lines[section]):
            stripped = line.strip()
            if not stripped:
                continue
            if not BULLET_RE.match(stripped):
                issues.append(EpistemicIssue(
                    section=section, bullet_index=idx, type="format",
                    message=f"Line does not start with '- ': {stripped[:60]}",
                ))
                continue

            bullet_text = BULLET_RE.sub("", stripped, count=1)
            citations = CITATION_RE.findall(bullet_text)
            has_causal = bool(CAUSAL_PHRASES_RE.search(bullet_text))
            has_comparative = bool(COMPARATIVE_WORDS_RE.search(bullet_text))
            has_claim = bool(stripped)  # any non-empty bullet is a claim

            parsed.bullets.append(ParsedBullet(
                section=section,
                index=idx,
                text=bullet_text,
                citations=citations,
                has_claim=has_claim,
                has_causal=has_causal,
                has_comparative=has_comparative,
            ))

    return parsed, issues


# ---------------------------------------------------------------------------
# Fact support
# ---------------------------------------------------------------------------


def check_fact_support(parsed: ParsedResponse) -> List[EpistemicIssue]:
    """Flag FACT bullets that assert state without a citation."""
    issues: List[EpistemicIssue] = []
    for b in parsed.bullets:
        if b.section != "[FACT]":
            continue
        if b.text.strip() == "(none)":
            continue
        if b.has_claim and not b.citations and not USER_SOURCE_RE.search(b.text):
            issues.append(EpistemicIssue(
                section=b.section,
                bullet_index=b.index,
                type="unsupported_fact",
                message=(
                    "FACT bullet asserts state but has no explicit citation "
                    "(source: ...). Add a source or rephrase as INFERENCE."
                ),
            ))
    return issues


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------


def check_causal_rules(parsed: ParsedResponse) -> List[EpistemicIssue]:
    """Phase 2: causal language constraints per section."""
    issues: List[EpistemicIssue] = []
    for b in parsed.bullets:
        if not b.has_causal:
            continue

        if b.section == "[UNKNOWN]":
            issues.append(EpistemicIssue(
                section=b.section, bullet_index=b.index,
                type="causal_violation",
                message="UNKNOWN section must not contain causal claims.",
            ))

        elif b.section == "[FACT]":
            # Causal in FACT is OK only with citation
            if not b.citations and not USER_SOURCE_RE.search(b.text):
                issues.append(EpistemicIssue(
                    section=b.section, bullet_index=b.index,
                    type="causal_violation",
                    message=(
                        "FACT contains causal claim without citation. "
                        "Add (source: ...) or move to INFERENCE."
                    ),
                ))

        elif b.section == "[INFERENCE]":
            if not UNCERTAINTY_WORDS_RE.search(b.text):
                issues.append(EpistemicIssue(
                    section=b.section, bullet_index=b.index,
                    type="causal_violation",
                    message=(
                        "INFERENCE with causal claim lacks uncertainty "
                        "markers (may, might, could, seems, etc.)."
                    ),
                ))

        elif b.section == "[RECOMMENDATION]":
            if HARD_ASSERTION_VERBS_RE.search(b.text) and not RATIONALE_WORDS_RE.search(b.text):
                issues.append(EpistemicIssue(
                    section=b.section, bullet_index=b.index,
                    type="causal_violation",
                    message=(
                        "RECOMMENDATION causal claim uses guarantee wording "
                        "without rationale (because, so that, etc.)."
                    ),
                ))

    return issues


# ---------------------------------------------------------------------------
# Comparative rules
# ---------------------------------------------------------------------------


def check_comparative_rules(parsed: ParsedResponse) -> List[EpistemicIssue]:
    """Phase 3: comparative judgment constraints per section."""
    issues: List[EpistemicIssue] = []
    for b in parsed.bullets:
        if not b.has_comparative:
            continue

        if b.section == "[UNKNOWN]":
            issues.append(EpistemicIssue(
                section=b.section, bullet_index=b.index,
                type="comparative_violation",
                message="UNKNOWN section must not contain comparative claims.",
            ))

        elif b.section == "[FACT]":
            if not b.citations and not EXTERNAL_QUOTE_RE.search(b.text):
                issues.append(EpistemicIssue(
                    section=b.section, bullet_index=b.index,
                    type="comparative_violation",
                    message=(
                        "FACT comparative claim without citation or external "
                        "reference. Move to INFERENCE or add source."
                    ),
                ))

        elif b.section == "[INFERENCE]":
            if SUPERLATIVE_ONLY_RE.search(b.text) and not UNCERTAINTY_WORDS_RE.search(b.text):
                issues.append(EpistemicIssue(
                    section=b.section, bullet_index=b.index,
                    type="comparative_violation",
                    message=(
                        "INFERENCE uses superlative without uncertainty "
                        "(best, optimal, etc.). Add 'may be', 'likely', etc."
                    ),
                ))

        elif b.section == "[RECOMMENDATION]":
            if SUPERLATIVE_ONLY_RE.search(b.text):
                if not ASSUMPTION_WORDS_RE.search(b.text) and not RATIONALE_WORDS_RE.search(b.text):
                    issues.append(EpistemicIssue(
                        section=b.section, bullet_index=b.index,
                        type="comparative_violation",
                        message=(
                            "RECOMMENDATION superlative without assumption "
                            "or rationale. State criterion: 'best for ...', "
                            "'optimal given ...'."
                        ),
                    ))
            elif not RATIONALE_WORDS_RE.search(b.text) and not ASSUMPTION_WORDS_RE.search(b.text):
                issues.append(EpistemicIssue(
                    section=b.section, bullet_index=b.index,
                    type="comparative_violation",
                    message=(
                        "RECOMMENDATION comparative without rationale "
                        "or assumption markers."
                    ),
                ))

    return issues


# ---------------------------------------------------------------------------
# Decision logic
# ---------------------------------------------------------------------------


def decide_from_issues(
    issues: List[EpistemicIssue],
    cfg: EpistemicConfig,
    response_type: str = "simple",
    raw_response: str = "",
) -> Decision:
    """Compute the strongest decision from collected issues, then apply policy layer.

    The policy layer (get_epistemic_policy) overrides config-based decisions for
    specific (turn_kind, claim_kind) combinations where format is noise or where
    enforcement should be softer/harder than the config default.
    """
    if not issues:
        return "allow"

    rank: dict[Decision, int] = {"allow": 0, "warn": 1, "block": 2}
    worst: Decision = "allow"

    for issue in issues:
        if issue.type == "format":
            issue_decision = cfg.treat_format_violation_as
        elif issue.type == "unsupported_fact":
            issue_decision = cfg.treat_unsupported_fact_as
        elif issue.type.startswith("causal"):
            issue_decision = cfg.treat_causal_violation_as
        elif issue.type.startswith("comparative"):
            issue_decision = cfg.treat_comparative_violation_as
        else:
            issue_decision = "warn"

        if rank[issue_decision] > rank[worst]:
            worst = issue_decision
            if worst == "block":
                break

    # Global mode override
    if cfg.mode == "allow":
        # PLAN mixed-substance is a minimum safety floor even in allow mode —
        # it must reach the policy layer as warn so guidance is written.
        if any(issue.code == "plan_mixed_substance" for issue in issues):
            return "warn"
        return "allow"
    if cfg.mode == "warn" and worst == "block":
        worst = "warn"

    # Policy-layer override: consult the explicit (turn_kind, claim_kind) table.
    # This fires after config-based ranking so it can selectively override decisions
    # that would otherwise be too strict for specific context combinations.
    if worst != "allow":
        is_status_report = is_status_summary_response(raw_response)
        turn_kind = _turn_kind_from_response_type(response_type, is_status_report)
        # Second-pass: reclassify UNKNOWN → CONTROL for structural factual reports
        turn_kind = _turn_kind_from_context(raw_response, turn_kind)
        claim_kind = _classify_claim_kind(issues)
        policy = get_epistemic_policy(turn_kind, claim_kind)
        if policy is not None:
            if policy == "ignore":
                return "allow"
            return policy

    return worst


# ---------------------------------------------------------------------------
# Policy layer — routes warn decisions to concrete system actions
# ---------------------------------------------------------------------------

# Actions produced by apply_epistemic_policy
PolicyAction = Literal[
    "allow",     # pass through — no special action
    "block",     # hard block — same as current block behavior
    "retry_with_guidance",   # write guidance marker, allow to pass
    "retry_auto_wrap",       # auto-wrap into 4-section, re-validate once
    "log_warn",  # warn-level issue but no behavior change — log only
]


@dataclass
class EpistemicPolicyResult:
    """Result of applying epistemic policy to a verdict."""

    decision: PolicyAction
    actions: dict


# ---------------------------------------------------------------------------
# Retry / escalation classifier
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetryStrategy:
    """Structured retry classification for validator outcomes.

    Produced by ``classify_validator_outcome()`` and consumed by
    ``apply_epistemic_policy()`` and Stop.py retry/escalation logic.
    """

    # One of the four terminal strategies
    strategy: Literal[
        "allow",           # pass through — no retry, no block
        "block_no_retry",  # hard block — no retry available
        "retry_with_guidance",   # repairable via citation/sourcing guidance
        "retry_auto_wrap",       # repairable via section-header reformatting
        "escalate_external_judge",  # ambiguous — external second opinion warranted
    ]

    # Machine-readable reason code for observability and deduplication
    reason_code: str

    # Human-readable one-line summary (not for routing logic)
    summary: str

    # Maximum retries allowed for this failure class before escalating to block.
    # None = no limit / not applicable.
    max_retries: int | None = None

    # True when this case meets the narrow trigger for external-judge escalation.
    # The judge is an advisory secondary reviewer — never overrides a deterministic block.
    escalate_external_judge: bool = False

    # Stable key used to detect repeated failures of the same class so retries
    # can be bounded. Used by Stop.py retry-count state.
    # Format: "reason_code:turn_mode" or similar stable tuple.
    repeat_key: str = ""

    # Issue codes that caused this retry strategy to be selected.
    # Used for telemetry correlation: (reason_code, triggering_codes) uniquely
    # identifies what the classifier acted on.
    triggering_codes: tuple[str, ...] = ()


def classify_validator_outcome(
    verdict: EpistemicVerdict,
    cfg: EpistemicConfig,
    *,
    tool_transcript: str | None = None,
    is_analytical: bool = False,
    turn_mode: str | None = None,
) -> RetryStrategy:
    """Classify a validator verdict into a structured retry strategy.

    This is the single choke point for all retry / escalation decisions
    driven by epistemic validator output.  Stop.py and the policy layer
    both route through here so that retry bounds and escalation predicates
    are enforced consistently and deterministically.

    Parameters
    ----------
    verdict:
        Output of ``validate()``.
    cfg:
        ``EpistemicConfig`` in use for this turn.
    tool_transcript:
        Raw tool output from this turn (for local-summary guidance decisions).
    is_analytical:
        True when the response is analytical (>3 lines, non-trivial content).
    turn_mode:
        Classified turn mode (e.g. "plan", "execution-report").

    Returns
    -------
    RetryStrategy
        ``strategy`` — terminal action to take.
        ``reason_code`` — stable deduplication key for retry counting.
        ``max_retries`` — bound on retries (None = not retryable).
        ``escalate_external_judge`` — True for narrow high-risk ambiguous cases.
        ``summary`` — human-readable summary for observability.
    """
    issue_types = {i.type for i in verdict.issues}
    issue_codes = {i.code for i in verdict.issues if i.code is not None}
    has_format = "format" in issue_types
    has_unsupported_fact = "unsupported_fact" in issue_types
    effective_mode = cfg.turn_mode or turn_mode or "unknown"
    repeat_key = f"{effective_mode}"

    # ── Block decisions ────────────────────────────────────────────────────────

    if verdict.decision == "block":
        # Hard violations: causal, comparative, unsupported_fact, plan_mixed_substance.
        # These are not retryable — retry will not produce a different result.
        if "plan_mixed_substance" in issue_codes:
            return RetryStrategy(
                strategy="block_no_retry",
                reason_code="PLAN_MIXED_SUBSTANCE",
                summary="PLAN mixed-substance — hard block, retry won't change content type",
                max_retries=0,
                escalate_external_judge=False,
                repeat_key=repeat_key,
                triggering_codes=tuple(issue_codes),
            )
        if "causal_violation" in issue_types or "comparative_violation" in issue_types:
            return RetryStrategy(
                strategy="block_no_retry",
                reason_code="CAUSAL_OR_COMPARATIVE_VIOLATION",
                summary="Causal or comparative violation — hard block",
                max_retries=0,
                escalate_external_judge=False,
                repeat_key=repeat_key,
                triggering_codes=tuple(i.type for i in verdict.issues if i.type in ("causal_violation", "comparative_violation")),
            )
        # Generic block: unsupported fact in non-analytical or non-local-summary context.
        if has_unsupported_fact:
            return RetryStrategy(
                strategy="block_no_retry",
                reason_code="UNSUPPORTED_FACT_HARD",
                summary="Unsupported fact — hard block",
                max_retries=0,
                escalate_external_judge=False,
                repeat_key=repeat_key,
                triggering_codes=tuple(i.type for i in verdict.issues if i.type == "unsupported_fact"),
            )
        # Catch-all for other block reasons.
        return RetryStrategy(
            strategy="block_no_retry",
            reason_code="BLOCK_OTHER",
            summary=f"Block decision ({verdict.decision}) — hard block",
            max_retries=0,
            escalate_external_judge=False,
            repeat_key=repeat_key,
            triggering_codes=tuple(i.code for i in verdict.issues if i.code is not None),
        )

    # ── Strict mode: allow is terminal ────────────────────────────────────────

    if cfg.mode == "block":
        # Strict mode: if we reached here, verdict.decision was not "block"
        # so the validator passed. Allow.
        return RetryStrategy(
            strategy="allow",
            reason_code="STRICT_MODE_ALLOW",
            summary="Strict mode — validator passed",
            max_retries=None,
            escalate_external_judge=False,
            repeat_key=repeat_key,
            triggering_codes=(),
        )

    # ── Warn mode: classify retry paths ───────────────────────────────────────

    if verdict.decision == "warn" and verdict.issues:
        # PLAN mixed-substance in warn mode: safety floor fires even in allow mode
        # (handled upstream in decide_from_issues), but also needs retry bounds here.
        if "plan_mixed_substance" in issue_codes:
            return RetryStrategy(
                strategy="retry_with_guidance",
                reason_code="PLAN_MIXED_SUBSTANCE_WARN",
                summary="PLAN mixed-substance — guidance retry, bounded",
                max_retries=1,
                escalate_external_judge=False,
                repeat_key=repeat_key,
                triggering_codes=tuple(issue_codes),
            )

        # Local-summary unsupported_fact: highest-value retry — citation is fixable.
        if (
            has_unsupported_fact
            and bool(tool_transcript)
            and is_analytical
        ):
            return RetryStrategy(
                strategy="retry_with_guidance",
                reason_code="UNSUPPORTED_FACT_LOCAL_SUMMARY",
                summary="Unsupported fact with local summary — retry with guidance",
                max_retries=1,
                escalate_external_judge=False,
                repeat_key=repeat_key,
                triggering_codes=tuple(i.type for i in verdict.issues if i.type == "unsupported_fact"),
            )

        # Pure format-only on analytical responses: section headers can be added.
        all_format = all(i.type == "format" for i in verdict.issues)
        if all_format and is_analytical:
            return RetryStrategy(
                strategy="retry_auto_wrap",
                reason_code="FORMAT_ONLY_ANALYTICAL",
                summary="Format-only issues on analytical response — auto-wrap retry",
                max_retries=1,
                escalate_external_judge=False,
                repeat_key=repeat_key,
                triggering_codes=tuple(i.type for i in verdict.issues),
            )

        # Ambiguous cases: PLAN-adjacent content with mixed signals.
        # These are narrow high-risk cases where deterministic rules are not
        # decisive — external judge may clarify.  Never downgrades block to allow.
        if effective_mode in ("plan", "execution-report"):
            # Content that hovers near mixed-substance but doesn't fully trigger it.
            # e.g. analytical language in plan mode that doesn't quite cross the threshold.
            has_investigation_markers = any(
                i.code in ("missing_section", "outside_section")
                for i in verdict.issues
            )
            if has_investigation_markers:
                return RetryStrategy(
                    strategy="escalate_external_judge",
                    reason_code="PLAN_MIXED_SECTION_AMBIGUOUS",
                    summary="Plan/report with ambiguous section markers — external judge",
                    max_retries=1,
                    escalate_external_judge=True,
                    repeat_key=repeat_key,
                    triggering_codes=tuple(i.code for i in verdict.issues if i.code in ("missing_section", "outside_section")),
                )

        # Warn-mode unsupported_fact without tool_transcript: log only, no retry.
        # (With tool_transcript → retry_with_guidance above.)
        # NOTE: plan-mode with outside_section is handled above and returns early
        # via escalate_external_judge before reaching this branch.
        if has_unsupported_fact and not tool_transcript:
            return RetryStrategy(
                strategy="log_warn",
                reason_code="UNSUPPORTED_FACT_NO_TRANSCRIPT",
                summary="Unsupported fact without tool transcript — log only",
                max_retries=0,
                escalate_external_judge=False,
                repeat_key=repeat_key,
                triggering_codes=tuple(i.type for i in verdict.issues if i.type == "unsupported_fact"),
            )

        # Warn-mode causal/comparative: log only (not block_no_retry).
        # This matches the original apply_epistemic_policy "log_warn" behavior
        # where causal violations in warn mode are advisory, not blocking.
        if (
            ("causal_violation" in issue_types or "comparative_violation" in issue_types)
            and cfg.mode == "warn"
        ):
            return RetryStrategy(
                strategy="log_warn",
                reason_code="CAUSAL_OR_COMPARATIVE_WARN",
                summary="Causal or comparative in warn mode — log only",
                max_retries=0,
                escalate_external_judge=False,
                repeat_key=repeat_key,
                triggering_codes=tuple(i.type for i in verdict.issues if i.type in ("causal_violation", "comparative_violation")),
            )

        # Hard blocks: causal/comparative in block mode stay hard blocks.
        if (
            ("causal_violation" in issue_types or "comparative_violation" in issue_types)
            and cfg.mode == "block"
        ):
            return RetryStrategy(
                strategy="block_no_retry",
                reason_code="CAUSAL_OR_COMPARATIVE_BLOCK",
                summary="Causal or comparative in block mode — hard block",
                max_retries=0,
                escalate_external_judge=False,
                repeat_key=repeat_key,
                triggering_codes=tuple(i.type for i in verdict.issues if i.type in ("causal_violation", "comparative_violation")),
            )

        # Generic warn: log only, no retry.
        return RetryStrategy(
            strategy="allow",
            reason_code="WARN_LOG_ONLY",
            summary="Warn with no retryable failure class — allow",
            max_retries=0,
            escalate_external_judge=False,
            repeat_key=repeat_key,
            triggering_codes=tuple(i.code for i in verdict.issues if i.code is not None),
        )

    # ── Allow: nothing to do ─────────────────────────────────────────────────

    return RetryStrategy(
        strategy="allow",
        reason_code="ALLOW",
        summary="Clean verdict — allow",
        max_retries=None,
        escalate_external_judge=False,
        repeat_key=repeat_key,
        triggering_codes=(),
    )


def apply_epistemic_policy(
    verdict: EpistemicVerdict,
    cfg: EpistemicConfig,
    *,
    tool_transcript: str | None = None,
    is_analytical: bool = False,
    turn_mode: str | None = None,
    verbose_override: bool = False,
) -> EpistemicPolicyResult:
    """Map a validator verdict + context to a concrete system action.

    This is the bridge between the validator's allow/warn/block decision and
    Stop.py's actual behavior.  It decides WHAT HAPPENS at each warn — not
    just that a warn occurred.

    Parameters
    ----------
    verdict:
        Output of ``validate()``.
    cfg:
        EpistemicConfig in use for this turn.
    tool_transcript:
        Raw tool output string from this turn (same as ``cfg.tool_transcript``).
        Used to decide the local-summary retry path.
    is_analytical:
        True when ``detect_response_mode`` returned ``"analysis"``
        (not ``"report"``).  Format-only retries only apply to analytical
        responses.
    turn_mode:
        Classified turn mode from ``_classify_turn_mode`` (e.g. "plan",
        "execution-report").  Plan/execution-report modes suppress blocks
        and format repairs on non-critical issues.
    verbose_override:
        True when ``--epistemic-verbose`` is in the user prompt.
        On-demand verbose makes the full advisory text visible inline.

    Returns
    -------
    EpistemicPolicyResult
        ``decision`` — one of the PolicyAction literals above.
        ``actions``   — dict of side-effects to perform (keys such as
        ``write_guidance_marker``, ``log_advisory``, ``retry_response``).
    """
    strategy = classify_validator_outcome(
        verdict,
        cfg,
        tool_transcript=tool_transcript,
        is_analytical=is_analytical,
        turn_mode=turn_mode,
    )

    # Map RetryStrategy to EpistemicPolicyResult for backward compatibility
    # with Stop.py, which consumes EpistemicPolicyResult.actions.
    if strategy.strategy == "block_no_retry":
        issue_types = {i.type for i in verdict.issues}
        has_unsupported_fact = "unsupported_fact" in issue_types
        return EpistemicPolicyResult(
            decision="block",
            actions={
                "write_guidance_marker": (
                    has_unsupported_fact and bool(tool_transcript)
                ),
                "_strategy": strategy,  # available for Stop.py observability
            },
        )
    if strategy.strategy == "retry_with_guidance":
        return EpistemicPolicyResult(
            decision="retry_with_guidance",
            actions={
                "write_guidance_marker": True,
                "advisory_type": "unsupported_fact_retry",
                "_strategy": strategy,
            },
        )
    if strategy.strategy == "retry_auto_wrap":
        return EpistemicPolicyResult(
            decision="retry_auto_wrap",
            actions={
                "advisory_type": "format_repair",
                "_strategy": strategy,
            },
        )
    if strategy.strategy == "escalate_external_judge":
        return EpistemicPolicyResult(
            decision="log_warn",
            actions={
                "advisory_type": "escalate_external_judge",
                "_strategy": strategy,
            },
        )
    if strategy.strategy == "log_warn":
        return EpistemicPolicyResult(
            decision="log_warn",
            actions={
                "advisory_type": "mixed_advisory",
                "_strategy": strategy,
            },
        )
    # allow
    return EpistemicPolicyResult(
        decision="allow",
        actions={"_strategy": strategy},
    )


# ---------------------------------------------------------------------------
# Response mode detection
# ---------------------------------------------------------------------------


def detect_response_mode(raw_response: str) -> str:
    """Detect whether a response uses the analysis or report schema.

    Checks for explicit report section headers first, then falls back to the
    status-summary heuristic. Returns "analysis" or "report".
    """
    if not raw_response:
        return "analysis"
    report_count = sum(1 for s in REPORT_SECTION_ORDER if s in raw_response)
    if report_count >= 2:
        return "report"
    if is_status_summary_response(raw_response):
        return "report"
    return "analysis"


# ---------------------------------------------------------------------------
# Status-summary bypass
# ---------------------------------------------------------------------------

_STATUS_SUMMARY_RE = re.compile(
    r"""
    (?:
        files?\s*(?:created|modified|written|changed|added)
      | (?:session|deliverable|completion|implementation)\s*(?:summary|report|deliverables)
      | all\s+\d+\s+tests?\s+pass
      | tests?\s+(?:pass|passed)
      | (?:implementation|task|migration|refactor)\s*(?:complete|done|finished)
      | here(?:'s|\s+is)\s+(?:the\s+)?(?:summary|what\s+was\s+done|what\s+i\s+(?:did|changed))
      | (?:changes|files)\s+(?:made|written|created|produced)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Signals that indicate an inference/completion claim appended to a status phrase.
# Used to narrow the report-mode bypass to pure status reports only.
_INFERENCE_SIGNALS_RE = re.compile(
    r"\b(so\s+|therefore|thus|which\s+means|that\s+means|"
    r"indicates?\s+that|suggests?\s+that|proves|confirms|"
    r"the\s+bug\s+is\s+(?:fixed|resolved)|"
    r"is\s+complete|is\s+resolved)\b",
    re.IGNORECASE,
)


def is_status_summary_response(raw_response: str) -> bool:
    """Return True if the response is clearly a status/deliverable report,
    not an analytical answer subject to the 4-section contract.

    Conservative: only matches obvious report patterns. Analytical answers
    that happen to mention "files created" in passing will NOT match because
    the pattern requires the phrase to be a dominant theme (checked by looking
    at the first ~300 chars of the response).

    Report-mode bypass does NOT apply when the response contains inference or
    completion signals (e.g. "so Phase B is complete", "the bug is fixed") —
    those indicate an analytical conclusion, not a pure status restatement.
    """
    if not raw_response:
        return False
    # Only check the beginning of the response where report headers appear.
    head = raw_response[:600]
    matches = _STATUS_SUMMARY_RE.findall(head)
    # Require at least 2 distinct matches OR a very strong single signal
    # (e.g., "Implementation complete." in the first line).
    if len(matches) >= 2:
        # Inference guard: reject if line also contains causal/completion signals.
        # "All tests passed" (pure status) is OK; "All tests passed, so Phase B is complete" is not.
        first_line = raw_response.split("\n", 1)[0].strip()
        if _INFERENCE_SIGNALS_RE.search(first_line):
            return False
        return True
    first_line = raw_response.split("\n", 1)[0].strip()
    if _STATUS_SUMMARY_RE.search(first_line):
        # Same inference guard on single-signal match
        if _INFERENCE_SIGNALS_RE.search(first_line):
            return False
        return True
    return False


def _filter_format_issues_for_response_type(
    issues: List[EpistemicIssue], response_type: str, has_evidence: bool
) -> List[EpistemicIssue]:
    """Filter format issues based on response type.

    - "simple" + evidence: drop global-text issue (citation IS evidence)
    - "analytical": keep missing-section issues but downgrade to warn
    - "investigation": keep all format enforcement but treat section-missing as block
    """
    if response_type == "investigation":
        # For investigation responses, keep all format issues (they are enforced
        # as block via treat_format_violation_as defaulting to "block").
        # The mode=warn downgrade in decide_from_issues only applies to the
        # weakest issue type; format issues at "block" remain block for investigation.
        return issues

    filtered: List[EpistemicIssue] = []
    for issue in issues:
        # Skip global-text format issue when response has citation markers
        # (text outside sections with citations = valid simple answer)
        if issue.type == "format" and issue.section == "__GLOBAL__":
            if has_evidence or response_type == "analytical":
                continue
        # Drop all format issues for analytical responses without evidence
        # (format is encouraged, not mandatory per CLAUDE.md)
        if response_type == "analytical" and not has_evidence:
            continue
        filtered.append(issue)
    return filtered


def validate(raw_response: str, config: Optional[EpistemicConfig] = None) -> EpistemicVerdict:
    """Analyze raw_response for structural, factual, causal, and comparative issues.

    Returns an EpistemicVerdict with decision and issue list.

    Validation rigor depends on response type:
    - "simple": citation OR inference marker OR very short (< 10 words) direct answer
    - "analytical": encourage structure, warn on missing sections
    - "investigation": enforce all 4 sections (full 4-section contract)
    """
    cfg = config or EpistemicConfig()

    # Skip all checks for non-substantive turns (greetings, acknowledgments, etc.)
    try:
        from __lib.shared_helpers import is_non_substantive_turn
        if is_non_substantive_turn(raw_response):
            return EpistemicVerdict(decision="allow", issues=[])
    except ImportError:
        pass

    # ── Schema routing by explicit turn_mode ─────────────────────────────────
    # turn_mode is authoritative when present. Text heuristics are fallback only
    # when metadata is absent. Text heuristics may detect mixed-substance
    # violations WITHIN a chosen schema; they may NOT silently reclassify.
    if cfg.turn_mode is not None:
        if cfg.turn_mode == "control":
            return _validate_control_schema(raw_response, cfg)
        if cfg.turn_mode == "plan":
            return _validate_plan_schema(raw_response, cfg)
        if cfg.turn_mode in ("analysis", "final-answer"):
            return _validate_investigation_schema(raw_response, cfg)
        if cfg.turn_mode == "execution-report":
            return _validate_execution_report_schema(raw_response, cfg)
        if cfg.turn_mode == "meta":
            return _validate_meta_schema(raw_response, cfg)
        # exploration: treat as generic (suppressed by quality gate upstream)

    # ── PLAN prefix routing ─────────────────────────────────────────────────
    # Only reachable when turn_mode is absent. Route plan-prefixed content
    # into _validate_plan_schema() for proper validation — no bypass.
    # The early PLAN gate no longer short-circuits to allow; all plan-prefixed
    # content is now validated via schema-aware logic.
    #
    # Use _has_plan_scaffold() to handle non-first-line / indented markers
    # (lstrip()-based startswith only catches the very first line).
    # Also scan body for ## RATIONALE / ## ANALYSIS which indicate plan-mode
    # intent even when the "[PLAN]" marker appears mid-document.
    if _has_plan_scaffold(raw_response):
        return _validate_plan_schema(raw_response, cfg)

    # Resolve response mode: explicit config overrides auto-detection.
    response_mode = cfg.responseMode
    if response_mode in ("auto", None):
        response_mode = detect_response_mode(raw_response)

    # Report mode does not follow the analytical 4-section contract.
    # Route through lightweight report schema for minimal validation instead
    # of unconditional allow — completion claims without evidence are flagged.
    if response_mode == "report":
        return _validate_report_schema(raw_response, cfg)

    # Mandate 4-section format for final-answer mode when response is substantial.
    # Short final-answers (<=100 words) are direct answers that don't need structure.
    # Substantial final-answers (>100 words) are analytical responses that should
    # use [FACT]/[INFERENCE]/[UNKNOWN]/[RECOMMENDATION] sections.
    word_count = len(raw_response.split())
    if getattr(cfg, "sectional_response_required", False) and word_count > 100:
        cfg = EpistemicConfig(
            mode=cfg.mode,
            responseMode="auto",
            treat_format_violation_as=cfg.treat_format_violation_as,
            treat_unsupported_fact_as=cfg.treat_unsupported_fact_as,
            treat_causal_violation_as=cfg.treat_causal_violation_as,
            treat_comparative_violation_as=cfg.treat_comparative_violation_as,
            enable_causal_checks=cfg.enable_causal_checks,
            enable_comparative_checks=cfg.enable_comparative_checks,
            tool_transcript=cfg.tool_transcript,
        )
        response_type = "investigation"

    # Classify response type to determine validation requirements
    response_type = _classify_response_type(raw_response)
    has_evidence = _has_citation_markers(raw_response)
    word_count = len(raw_response.split())

    # --- Simple responses: evidence OR very short direct answer ---
    if response_type == "simple":
        # Structured responses with STATUS sections: run all checks
        if any(s in raw_response for s in ("[FACT]", "[INFERENCE]", "[UNKNOWN]", "[RECOMMENDATION]")):
            clean = sanitize_response(raw_response)
            parsed, format_issues = parse_sections(clean)
            issues: List[EpistemicIssue] = list(format_issues)
            issues.extend(check_fact_support(parsed))
            if cfg.enable_causal_checks:
                issues.extend(check_causal_rules(parsed))
            if cfg.enable_comparative_checks:
                issues.extend(check_comparative_rules(parsed))
            decision = decide_from_issues(issues, cfg, response_type="simple", raw_response=raw_response)
            return EpistemicVerdict(decision=decision, issues=issues)
        elif has_evidence or _has_inference_marker(raw_response):
            return EpistemicVerdict(decision="allow", issues=[])
        # Short responses that are direct answers to questions (Yes/No, does/is, etc.)
        # need no evidence - the question itself establishes context
        elif _is_direct_answer_to_question(raw_response):
            return EpistemicVerdict(decision="allow", issues=[])
        # Ultra-short grounded status confirmations (e.g. "103 passed.") restate
        # immediately prior evidence (pytest output was just displayed) and
        # need no inline citation.  Substantive claims still require one.
        elif _is_grounded_status_confirmation(raw_response):
            return EpistemicVerdict(decision="allow", issues=[])
        # Short repair responses in active challenge context are allowed through.
        # These are inherently short and lack citation markers — not a quality failure.
        elif _is_repair_response_in_active_challenge(raw_response, word_count):
            return EpistemicVerdict(decision="allow", issues=[])
        # Locally-grounded tool summaries: when the response explicitly links to
        # this turn's tool output (e.g. "from the pytest run above") AND the tool
        # transcript overlaps with the response content, treat it as sufficiently
        # grounded without requiring (source: file:line) boilerplate.
        elif _is_locally_grounded_summary(raw_response, cfg.tool_transcript, word_count):
            return EpistemicVerdict(decision="allow", issues=[])
        # Grounded status confirmations — ultra-short restatements of evidence
        # that was already displayed before the response (pytest output, command
        # result, etc.). These are not epistemic claims; they restate visible state.
        elif _is_grounded_status_confirmation(raw_response):
            return EpistemicVerdict(decision="allow", issues=[])
        else:
            # Route through policy layer: context reclassification may promote
            # UNKNOWN → CONTROL, making FORMAT_ONLY issues ignorable.
            # (e.g. audit-structured reports: tables, numbered findings, evidence markers)
            hard_block_issue = EpistemicIssue(
                section="__GLOBAL__", bullet_index=-1,
                type="format",
                message=(
                    "Simple answer lacks citation or inference marker. "
                    "Add a source citation (source: file:line) or use "
                    "tentative language (likely, may be, I would need to)."
                ),
            )
            decision = decide_from_issues(
                [hard_block_issue], cfg, response_type="simple", raw_response=raw_response
            )
            return EpistemicVerdict(decision=decision, issues=[hard_block_issue])

    # --- Analytical responses: encourage structure, don't hard-block ---
    if response_type == "analytical":
        clean = sanitize_response(raw_response)
        parsed, format_issues = parse_sections(clean)
        issues: List[EpistemicIssue] = list(format_issues)

        # Filter format issues based on evidence
        issues = _filter_format_issues_for_response_type(issues, response_type, has_evidence)
        issues.extend(check_fact_support(parsed))
        if cfg.enable_causal_checks:
            issues.extend(check_causal_rules(parsed))
        if cfg.enable_comparative_checks:
            issues.extend(check_comparative_rules(parsed))

        decision = decide_from_issues(issues, cfg, response_type="analytical", raw_response=raw_response)
        return EpistemicVerdict(decision=decision, issues=issues)

    # --- Investigation responses: enforce full 4-section contract ---
    clean = sanitize_response(raw_response)
    parsed, format_issues = parse_sections(clean)

    issues: List[EpistemicIssue] = list(format_issues)
    issues.extend(check_fact_support(parsed))
    if cfg.enable_causal_checks:
        issues.extend(check_causal_rules(parsed))
    if cfg.enable_comparative_checks:
        issues.extend(check_comparative_rules(parsed))

    # Filter format issues for investigation responses (same logic as simple/analytical)
    issues = _filter_format_issues_for_response_type(issues, response_type, has_evidence)

    # For investigation responses, format enforcement should be strict (block).
    # Override mode to 'block' so that block-ranked format issues stay as block
    # rather than being downgraded to warn by the mode='warn' global override.
    strict_cfg = EpistemicConfig(
        mode="block",
        treat_format_violation_as=cfg.treat_format_violation_as,
        treat_unsupported_fact_as=cfg.treat_unsupported_fact_as,
        treat_causal_violation_as=cfg.treat_causal_violation_as,
        treat_comparative_violation_as=cfg.treat_comparative_violation_as,
        enable_causal_checks=cfg.enable_causal_checks,
        enable_comparative_checks=cfg.enable_comparative_checks,
        tool_transcript=cfg.tool_transcript,
    )
    decision = decide_from_issues(issues, strict_cfg, response_type="investigation", raw_response=raw_response)
    return EpistemicVerdict(decision=decision, issues=issues)
