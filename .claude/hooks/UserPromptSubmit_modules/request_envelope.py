"""Request envelope: quote-aware prompt decomposition + mode classification.

Single shared result that splits a user prompt into:
  - outer_text:  user-authored text with quoted/fenced spans removed
  - quoted_spans: the removed spans (for telemetry/inspection only)
  - mode:        evaluation | implementation | diagnosis | research | status | mixed | ambiguous
  - multiple_requests: True when >=2 distinct request units are present
  - confidence / reason: why the mode was chosen

INVARIANT: quoted/fenced content never contributes intent signals. Detection of
implementation / diagnosis / evaluation modes runs against outer_text only.

Owned by the unified_detection path; other hooks consume the result via
``unified_detection.ensure_request_envelope(context)`` rather than re-implementing
classification. No LLM, pure deterministic regex.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ── Span removal ──────────────────────────────────────────────────────────────
# Order matters: fenced blocks first (they may contain quotes), then inline code,
# then quote pairs (straight + curly), then blockquote lines.

_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
_DQUOTE_RE = re.compile(r'"[^"\n]*"')
# Straight single-quote PAIRS only when boundaries are non-alnum.
# Preserves contractions: What's / user's / John's / don't / can't.
# Still strips real quoted spans: 'Implement the hook.' / 'foo bar' / 'implement the hook'
_SQUOTE_RE = re.compile(r"(?<![A-Za-z])'[^'\n]+'(?![A-Za-z'])", re.VERBOSE)
_CURLY_DQUOTE_RE = re.compile(r"“[^“”\n]*”")
# Curly single-quote PAIRS only (open ‘ ... close ’). Apostrophes (’
# used as contractions) are not opening markers, so "don't" is never stripped.
_CURLY_SQUOTE_RE = re.compile(r"‘[^‘’\n]*’")
_BLOCKQUOTE_RE = re.compile(r"^[ \t]*>.*$", re.MULTILINE)


def strip_quoted_spans(text: str) -> tuple[str, list[str]]:
    """Remove quoted/fenced/blockquote spans, returning (outer_text, spans).

    Removed spans are replaced with a single space so word boundaries on either
    side do not glue together.
    """
    if not text:
        return "", []
    spans: list[str] = []

    def _collect(m: re.Match) -> str:
        spans.append(m.group(0))
        return " "

    outer = _FENCE_RE.sub(_collect, text)
    outer = _INLINE_CODE_RE.sub(_collect, outer)
    outer = _DQUOTE_RE.sub(_collect, outer)
    outer = _SQUOTE_RE.sub(_collect, outer)
    outer = _CURLY_DQUOTE_RE.sub(_collect, outer)
    outer = _CURLY_SQUOTE_RE.sub(_collect, outer)
    outer = _BLOCKQUOTE_RE.sub(_collect, outer)
    return outer, spans


# ── Mode signal patterns (matched against outer_text) ─────────────────────────

# Evaluation / review / appraisal — the user wants an opinion, not an action.
#
# Note: bare `\bdo\s+(?:these|this|that)\b` was removed because it false-positives
# on real implementation requests like "Do this: implement the cache layer"
# (the word "this" in imperative context is not evaluation). The remaining
# `does` / "make sense" / "do these enhancements make sense" / "what do you
# think" arms keep the genuine question signals without the false-negative.
_EVAL_RE = re.compile(
    r"\bmake\s+sense\b"
    r"|\bdo\s+these\s+\w+\s+make\s+sense\b"
    r"|\bdoes\s+(?:this|that|it)\s+(?:work|make|look|sound|seem|seem\s+right)\b"
    r"|\bwhat\s+do\s+you\s+think\b"
    r"|\b(?:your|any)\s+thoughts\b"
    r"|\breview\s+(?:this|that|the|these|those|my|our|proposal|it|a|an)\b"
    r"|\btell\s+me\s+what\s+(?:breaks|break|is\s+wrong|you\s+think)\b"
    r"|\bevaluat(?:e|ion)\b"
    r"|\b(?:sound|look)\s+(?:good|right|correct|ok)\b"
    r"|\bfeedback\b|\bcritique\b|\bsanity\s+check\b",
    re.IGNORECASE,
)

# Exploration / decision — not an action request.
_EXPLORATION_RE = re.compile(
    r"\b(?:should\s+we|alternative|tradeoff|trade-off|pros\s+and\s+cons|versus|vs\.?)\b",
    re.IGNORECASE,
)

# Research / explanation — gather or explain, not change code.
_RESEARCH_RE = re.compile(
    r"\b(?:investigate|explore|examine|research|look\s+into|explain|describe|"
    r"how\s+(?:does|do|can)|tell\s+me\s+about)\b",
    re.IGNORECASE,
)

# Status / summary.
_STATUS_RE = re.compile(
    r"\b(?:what(?:'s|\s+is)\s+the\s+status|status\s+(?:of|update)|"
    r"where\s+(?:are\s+we|do\s+we\s+stand)|summar(?:y|ize))\b",
    re.IGNORECASE,
)

# Implementation / code-action imperative. NOTE: bare "make" deliberately
# excluded — "make sense" / "make sure" must never classify as implementation.
_IMPL_IMPERATIVE_RE = re.compile(
    r"\b(?:implement|build|create|add|write|develop|introduce|refactor|"
    r"fix|patch|resolve|repair|construct|extend)\b",
    re.IGNORECASE,
)

# Diagnosis signals: problem keyword + question/causal indicator.
_DIAG_KW_RE = re.compile(
    r"\b(?:crash|crashes|crashing|error|errors|fail|fails|failing|failed|bug|bugs|"
    r"issue|issues|broken|null|undefined|exception|stack\s+trace|traceback|"
    r"overflow|deadlock|race\s+condition)\b",
    re.IGNORECASE,
)
_DIAG_Q_RE = re.compile(
    r"\b(?:why|what|how|debug|diagnose|investigate|root\s+cause|cause\s+of|"
    r"causing|caused\s+by)\b",
    re.IGNORECASE,
)
_DIAG_QSTART_RE = re.compile(r"^\s*(?:why|what|how|debug|diagnose|investigate)\b", re.IGNORECASE)

# Request sequencers — signal multiple request units.
_SEQUENCER_RE = re.compile(
    r"\b(?:then|after\s+that|next|finally|also|additionally|afterwards|"
    r"if\s+(?:yes|so)|and\s+then)\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RequestEnvelope:
    """Quote-aware decomposition + mode classification of a user prompt."""

    outer_text: str
    quoted_spans: list[str] = field(default_factory=list)
    mode: str = "ambiguous"
    multiple_requests: bool = False
    confidence: str = "low"
    reason: str = ""
    # Raw signal flags for callers that need them.
    has_impl: bool = False
    has_diag: bool = False
    has_eval: bool = False


def _has_diag(outer: str) -> bool:
    if not _DIAG_KW_RE.search(outer):
        return False
    return bool(_DIAG_Q_RE.search(outer)) or bool(_DIAG_QSTART_RE.match(outer.strip()))


def analyze_prompt(prompt: str) -> RequestEnvelope:
    """Decompose *prompt* into a quote-aware request envelope.

    Deterministic, no LLM. Quoted/fenced content is removed before any intent
    signal is evaluated, so a proposal quoted inside an evaluation question can
    never trigger an implementation/diagnosis contract.
    """
    if not prompt or not prompt.strip():
        return RequestEnvelope(outer_text="", mode="ambiguous", reason="empty_prompt")

    outer, spans = strip_quoted_spans(prompt)

    has_eval = bool(_EVAL_RE.search(outer)) or bool(_EXPLORATION_RE.search(outer))
    has_research = bool(_RESEARCH_RE.search(outer))
    has_status = bool(_STATUS_RE.search(outer))
    has_impl = bool(_IMPL_IMPERATIVE_RE.search(outer))
    has_diag = _has_diag(outer)

    action = has_impl or has_diag
    nonaction = has_eval or has_research or has_status

    # Multiple request units: an action coexists with a non-action appraisal,
    # OR a sequencer joins two distinct action kinds.
    sequencer = bool(_SEQUENCER_RE.search(outer))
    multiple = bool((nonaction and action) or (sequencer and has_impl and has_diag))

    if multiple and action and nonaction:
        mode, confidence, reason = "mixed", "high", "action_and_appraisal_coexist"
    elif multiple and has_impl and has_diag:
        mode, confidence, reason = "mixed", "medium", "impl_and_diag_with_sequencer"
    elif has_impl:
        mode, confidence, reason = "implementation", "high", "impl_imperative_in_outer"
    elif has_diag:
        mode, confidence, reason = "diagnosis", "high", "diag_signal_in_outer"
    elif has_eval:
        mode, confidence, reason = "evaluation", "high", "evaluation_signal_in_outer"
    elif has_research:
        mode, confidence, reason = "research", "medium", "research_signal_in_outer"
    elif has_status:
        mode, confidence, reason = "status", "medium", "status_signal_in_outer"
    else:
        mode, confidence, reason = "ambiguous", "low", "no_clear_signal"

    # Detect signals that lived ONLY inside quoted spans (telemetry-only).
    if not action:
        full_impl = bool(_IMPL_IMPERATIVE_RE.search(prompt))
        full_diag = _has_diag(prompt)
        if (full_impl or full_diag) and spans:
            reason = "quoted_signal_ignored"

    return RequestEnvelope(
        outer_text=outer,
        quoted_spans=spans,
        mode=mode,
        multiple_requests=multiple,
        confidence=confidence,
        reason=reason,
        has_impl=has_impl,
        has_diag=has_diag,
        has_eval=has_eval,
    )


if __name__ == "__main__":  # ponytail: one runnable self-check
    cases = [
        ("for the /recap skill, do these enhancements make sense? 'Every handoff must X'", "evaluation"),
        ("Do these changes make sense? 'Implement the hook.'", "evaluation"),
        ("Implement this proposal: 'Add the hook.'", "implementation"),
        ("Review this proposal and tell me what breaks: 'Fix the router.'", "evaluation"),
        ("Diagnose this crash: 'The parser fails.'", "diagnosis"),
        ("Implement the UserPromptSubmit request envelope.", "implementation"),
        ("Fix the task contract false positive.", "implementation"),
        ("Diagnose why the parser crashes.", "diagnosis"),
        ("Refactor task_start_contract_writer.py.", "implementation"),
        ("Review proposal A, then implement proposal B.", "mixed"),
        ("Does this make sense? If yes, implement it.", "mixed"),
        ("Explain the failure, update the docs, and run the tests.", "research"),
        ("Implement a code review system.", "implementation"),
    ]
    bad = 0
    for p, want in cases:
        got = analyze_prompt(p).mode
        ok = got == want
        bad += 0 if ok else 1
        print(f"{'OK' if ok else 'FAIL'} {got:14} want={want:14} :: {p[:50]}")
    print("ALL PASS" if not bad else f"{bad} FAILED")
