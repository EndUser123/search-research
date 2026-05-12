#!/usr/bin/env python3
"""
epistemic_applicability — Authoritative epistemic applicability layer
=====================================================================

Three-layer architecture for Stop-time epistemic enforcement:

  Layer 1: Turn-mode scoping
    - is_substantive_reasoning_turn() — authoritative gate on turn mode
    - Explicit non-analytical modes short-circuit enforcement

  Layer 2: Response classification
    - classify_epistemic_response() — simple/delivery/deep-analysis
    - Deterministic text-shape signals

  Layer 3: Authoritative applicability decision
    - determine_epistemic_applicability() — combines turn mode + classification
    - Returns EpistemicApplicabilityDecision with enforcement_level
    - All Stop gates use this single decision point

Key invariant:
  - Turn semantics take precedence over text heuristics
  - No gate re-decides applicability from scratch
  - Conservative default: uncertain → full enforcement

All existing helpers (is_simple_epistemic_response, is_grounded_delivery_summary)
are thin wrappers over the authoritative layer for backward compatibility.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field

from __lib.turn_mode import TurnMode

# =============================================================================
# Layer 1: Turn-mode scoping
# =============================================================================

# Modes where quality gates should NOT be eligible to speak.
# These are clearly non-substantive or already covered by other gates.
_NON_SUBSTANTIVE_MODES: frozenset = frozenset({
    "control",
    "exploration",
    "meta",
    "plan",
    "execution-report",
})


def is_substantive_reasoning_turn(mode: TurnMode) -> bool:
    """
    Returns True only for modes where epistemic enforcement is appropriate.

    Suppresses on:
    - control: short imperative commands (already suppressed by GATE_CLASSES)
    - exploration: open-ended design discussion
    - meta: system introspection
    - plan: explicit planning
    - execution-report: task completion summaries

    Active on:
    - analysis: causal reasoning, root cause investigation
    - final-answer: direct answers to questions
    """
    return mode not in _NON_SUBSTANTIVE_MODES


# =============================================================================
# Layer 2: Response classification patterns
# =============================================================================

# Diagnosis markers — phrases that signal multi-step reasoning.
_DIAGNOSIS_MARKERS = (
    r"(?:root\s+cause|because|therefore|evidence\s+that|"
    r"caused\s+by|this\s+is\s+a|investigation|diagnos|"
    r"hypothesis|trace[d]?\s+(the\s+)?(source|cause)|"
    r"find(?:ing)?\s+(the\s+)?(root|underlying)|"
    r"(?:the\s+)?problem\s+is\s+(?:that|caused|located)|"
    r"the\s+(?:issue|bug)\s+originates|reason\s+is|"
    r"from\s+the\s+(?:grep|read|logs?|output|evidence)|"
    r"source:\s|as\s+shown|according\s+to|"
    r"this\s+suggests|this\s+indicates|this\s+means|"
    r"my\s+hypothesis|it\s+appears|it\s+seems|"
    r"the\s+system\s+(?:is|does|doesn't|can't|cannot)|"
    r"fixing\s+(?:this|it|the)\s+requires|"
    r"to\s+resolve\s+this|to\s+fix\s+this|"
    r"(?:the\s+)?first\s+step|step\s+(?:1|one|two|three|four)|"
    r"trace\s+(?:to|back\s+to|from)|"
    r"follow(?:ing|s)?\s+the\s+(?:path|chain|stack|import)|"
    r"the\s+call\s+chain|the\s+import\s+chain|the\s+stack\s+trace)"
)

_DIAGNOSIS_RE = re.compile(_DIAGNOSIS_MARKERS, re.IGNORECASE | re.MULTILINE)

# Causal/structural reasoning chains
_CAUSAL_MARKERS_RE = re.compile(
    r"(?:cause[sd]?|because|therefore|so|hence|thus|"
    r"due\s+to|result(?:s|ed|ing)?\s+in|lead(?:s|ing)?\s+to|"
    r"is\s+why|is\s+caused\s+by|is\s+driven\s+by|triggered\s+by)",
    re.IGNORECASE | re.MULTILINE,
)

# Section headers — presence indicates structured analytical response
_SECTION_HEADER_RE = re.compile(
    r"\[[\s]*(?:FACT|INFERENCE|RECOMMENDATION|CONCLUSION|UNKNOWN|RATIONALE|PLAN|STATUS|CHANGES|RESULTS|NEXT)",
    re.IGNORECASE,
)

# Delivery/reporting markers
_DELIVERY_PATTERN = (
    r"(?:^\s*(?:done|complete|finished|implemented|fixed|verified)|"
    r"all\s+(?:tests?\s+)?passed?|"
    r"\d+\s+(?:tests?\s+)?passed|"
    r"^all\s+tests?\s+(?:pass|passing|passed)|"
    r"^tests?\s+(?:are|is)\s+(?:passing|passed|done|complete)|"
    r"^[Ii](?:['\xe2\x80\x99]\s*)?(?:have|ve)\s+(?:fixed|updated|added|created|completed|implemented|finished)|"
    r"^[Ll]imitations?\s*:\s*\n|"
    r"[A-Z][a-z]+\s+(?:file|test|module|hook|gate)\s+(?:created|added|updated|fixed|modified)|"
    r"files?\s+created|files?\s+modified|files?\s+added|"
    r"tests?\s+(?:added|wrote|created|written)|"
    r"implementation\s+complete|code\s+complete|"
    r"(?:yes|no|ok|right|wrong|correct)\s*[.,]?\s*$|"
    r"limitations?\s*\.\s*$|"
    r"deliverables?\s*\.\s*$|"
    r"files?\s+(?:modified|created|added)\s*\.\s*$|"
    r"what\s+(?:was|wasn.t|could|should)\s+(?:done|changed|fixed|improved)\s*\.\s*$)"
)

_DELIVERY_RE = re.compile(_DELIVERY_PATTERN, re.IGNORECASE | re.MULTILINE)

# Ultra-short grounded summaries
_GROUNDED_SHORT_RE = re.compile(
    r"^\s*\d+\s+(?:tests?|files?|modules?|hooks?)\s+(?:passed|created|added|modified)\s*\.\s*$",
    re.IGNORECASE,
)

# =============================================================================
# Layer 3: Unified classifier
# =============================================================================

@dataclass(frozen=True)
class EpistemicClassification:
    """
    Structured classification result for epistemic applicability.

    Attributes:
        is_simple_response: Short/simple conversational responses don't need
                            [FACT]/[INFERENCE] format.
        is_delivery_response: Delivery/completion summaries describe what was done,
                              not why. Used for bypassing lazy-workaround detection.
        is_deep_analysis_candidate: Genuine multi-step reasoning — section format
                                    enforcement should be active.
        matched_signals: Pattern names that matched (for debugging/testing).
        reason: Human-readable summary of the classification decision.
    """

    is_simple_response: bool
    is_delivery_response: bool
    is_deep_analysis_candidate: bool
    matched_signals: tuple[str, ...] = dc_field(default_factory=tuple)
    reason: str = ""


def classify_epistemic_response(response: str) -> EpistemicClassification:
    """
    Classify response content type for epistemic applicability.

    Does NOT consider turn mode — only response text characteristics.
    Turn mode is handled by determine_epistemic_applicability().

    Args:
        response: The assistant's response text

    Returns:
        EpistemicClassification with boolean flags and matched signals
    """
    if not response:
        return EpistemicClassification(
            is_simple_response=True,
            is_delivery_response=False,
            is_deep_analysis_candidate=False,
            matched_signals=("empty",),
            reason="Empty response is trivially simple",
        )

    stripped = response.strip()
    signals: list[str] = []

    # === Check for section headers FIRST ===
    if _SECTION_HEADER_RE.search(stripped) is not None:
        signals.append("section_headers")
        return EpistemicClassification(
            is_simple_response=False,
            is_delivery_response=False,
            is_deep_analysis_candidate=True,
            matched_signals=tuple(signals),
            reason="Section headers ([FACT]/[INFERENCE]/etc) indicate structured analysis",
        )

    # === Check for ultra-short grounded summaries ===
    if _GROUNDED_SHORT_RE.search(stripped):
        signals.append("grounded_short")
        return EpistemicClassification(
            is_simple_response=True,
            is_delivery_response=True,
            is_deep_analysis_candidate=False,
            matched_signals=tuple(signals),
            reason="Ultra-short grounded summary (digit-prefixed)",
        )

    # === Check for delivery patterns at response start ===
    if _DELIVERY_RE.match(stripped):
        signals.append("delivery_pattern")
        return EpistemicClassification(
            is_simple_response=True,
            is_delivery_response=True,
            is_deep_analysis_candidate=False,
            matched_signals=tuple(signals),
            reason="Delivery pattern matched at response start",
        )

    # === Check for multiple causal markers ===
    causal_count = len(_CAUSAL_MARKERS_RE.findall(stripped))
    if causal_count >= 2:
        signals.append(f"causal_markers({causal_count})")
        return EpistemicClassification(
            is_simple_response=False,
            is_delivery_response=False,
            is_deep_analysis_candidate=True,
            matched_signals=tuple(signals),
            reason=f"Multiple causal markers ({causal_count}) indicate multi-step reasoning",
        )

    # === Check for diagnosis markers ===
    has_diagnosis = _DIAGNOSIS_RE.search(stripped) is not None
    if has_diagnosis:
        signals.append("diagnosis_markers")
        return EpistemicClassification(
            is_simple_response=False,
            is_delivery_response=False,
            is_deep_analysis_candidate=True,
            matched_signals=tuple(signals),
            reason="Diagnosis markers indicate root-cause analysis or evidence synthesis",
        )

    # === Long responses without diagnostic markers ===
    if len(stripped) > 300:
        signals.append("long_no_diagnosis")
        return EpistemicClassification(
            is_simple_response=False,
            is_delivery_response=False,
            is_deep_analysis_candidate=True,
            matched_signals=tuple(signals),
            reason="Long response (>300 chars) without diagnostic markers — conservative enforcement",
        )

    # === Short responses (<=80 chars) without diagnosis markers ===
    if len(stripped) <= 80:
        signals.append("short_response")
        return EpistemicClassification(
            is_simple_response=True,
            is_delivery_response=False,
            is_deep_analysis_candidate=False,
            matched_signals=tuple(signals),
            reason="Short response (<=80 chars) without diagnostic markers",
        )

    # === Short responses (<=150 chars) starting with direct answer patterns ===
    if len(stripped) <= 150:
        if re.match(r"^(yes|no|correct|incorrect|right|wrong|absolutely|confirm)[,.\s]", stripped.lower()):
            signals.append("direct_answer_pattern")
            return EpistemicClassification(
                is_simple_response=True,
                is_delivery_response=False,
                is_deep_analysis_candidate=False,
                matched_signals=tuple(signals),
                reason="Short response starting with direct answer pattern",
            )
        if re.match(r"^(is|does|can|will|should|would|has|have)\s+", stripped.lower()):
            if not has_diagnosis:
                signals.append("auxiliary_verb_start")
                return EpistemicClassification(
                    is_simple_response=True,
                    is_delivery_response=False,
                    is_deep_analysis_candidate=False,
                    matched_signals=tuple(signals),
                    reason="Short response starting with auxiliary verb",
                )

    # === Default: conservative ===
    signals.append("default_conservative")
    return EpistemicClassification(
        is_simple_response=False,
        is_delivery_response=False,
        is_deep_analysis_candidate=True,
        matched_signals=tuple(signals),
        reason="Default conservative: uncertain classification → enforce",
    )


# =============================================================================
# Layer 4: Authoritative applicability decision
# =============================================================================

@dataclass(frozen=True)
class EpistemicApplicabilityDecision:
    """
    Authoritative epistemic applicability decision for Stop gates.

    All epistemic gates should use this decision rather than re-computing
    applicability from scratch.

    Attributes:
        applicable: Whether epistemic enforcement is eligible on this turn.
        enforcement_level: "none" | "simple" | "full"
            - "none": No epistemic enforcement (non-analytical turn or trivial)
            - "simple": Light enforcement only (simple/delivery responses)
            - "full": Full analytical enforcement (deep analysis candidates)
        reason: Human-readable explanation of the decision.
        turn_mode: The detected turn mode (for telemetry/debugging).
        classification: The response classification result.
        matched_signals: All signals that contributed to the decision.
    """

    applicable: bool
    enforcement_level: str  # "none" | "simple" | "full"
    reason: str
    turn_mode: str | None
    classification: EpistemicClassification
    matched_signals: tuple[str, ...] = dc_field(default_factory=tuple)

    @property
    def is_simple_response(self) -> bool:
        return self.classification.is_simple_response

    @property
    def is_delivery_response(self) -> bool:
        return self.classification.is_delivery_response

    @property
    def is_deep_analysis_candidate(self) -> bool:
        return self.classification.is_deep_analysis_candidate


def determine_epistemic_applicability(
    response: str,
    *,
    turn_mode: str | None,
) -> EpistemicApplicabilityDecision:
    """
    Authoritative epistemic applicability decision.

    Precedence:
    1. Explicit turn semantics (turn_mode) — non-analytical modes → applicable=False
    2. Response classification (classify_epistemic_response) — maps to enforcement level
    3. Default conservative — uncertain → full enforcement

    Args:
        response: The assistant's response text
        turn_mode: The detected turn mode (control, exploration, analysis, etc.)

    Returns:
        EpistemicApplicabilityDecision with applicable, enforcement_level, and reason
    """
    signals: list[str] = []

    # === Layer 1: Turn-mode authoritative suppression ===
    if turn_mode is not None:
        if not is_substantive_reasoning_turn(turn_mode):
            # Non-analytical turn: suppress enforcement entirely
            # Strip quoted/loop artifacts before classification for accuracy
            stripped_response = strip_for_gate_matching(response)
            classification = classify_epistemic_response(stripped_response)
            return EpistemicApplicabilityDecision(
                applicable=False,
                enforcement_level="none",
                reason=f"Turn mode '{turn_mode}' is non-substantive — epistemic enforcement suppressed",
                turn_mode=turn_mode,
                classification=classification,
                matched_signals=tuple(["turn_mode_suppression", f"mode={turn_mode}"]),
            )

        signals.append(f"mode={turn_mode}")

    # === Layer 2: Response classification ===
    # Strip quoted/loop artifacts before classification
    stripped_response = strip_for_gate_matching(response)
    classification = classify_epistemic_response(stripped_response)
    signals.extend(classification.matched_signals)

    # === Map classification to enforcement level ===
    if classification.is_simple_response or classification.is_delivery_response:
        # Simple/delivery: light enforcement (bypass section format requirement)
        return EpistemicApplicabilityDecision(
            applicable=True,
            enforcement_level="simple",
            reason=f"Simple/delivery response — light enforcement (section format not required)",
            turn_mode=turn_mode,
            classification=classification,
            matched_signals=tuple(signals),
        )

    if classification.is_deep_analysis_candidate:
        # Deep analysis: full enforcement
        return EpistemicApplicabilityDecision(
            applicable=True,
            enforcement_level="full",
            reason=f"Deep analysis candidate — full epistemic enforcement",
            turn_mode=turn_mode,
            classification=classification,
            matched_signals=tuple(signals),
        )

    # === Default conservative ===
    return EpistemicApplicabilityDecision(
        applicable=True,
        enforcement_level="full",
        reason="Default conservative: no clear simple/delivery signals → full enforcement",
        turn_mode=turn_mode,
        classification=classification,
        matched_signals=tuple(signals + ["default_conservative"]),
    )


# =============================================================================
# Backward-compatible wrappers
# =============================================================================

def is_simple_epistemic_response(response: str) -> bool:
    """
    Returns True when a response is simple enough to bypass section-header format.

    Delegates to classify_epistemic_response() for centralized logic.
    Kept for backward compatibility with existing call sites in Stop.py.
    """
    return classify_epistemic_response(response).is_simple_response


def is_grounded_delivery_summary(response: str) -> bool:
    """
    Returns True when a response is a grounded delivery or reporting summary.

    Delegates to classify_epistemic_response() for centralized logic.
    Kept for backward compatibility with existing call sites in Stop.py.
    """
    return classify_epistemic_response(response).is_delivery_response


# =============================================================================
# Quote / loop resistance
# =============================================================================

# Blockquote patterns
_BLOCKQUOTE_RE = re.compile(r"^\s*>\s*")

# Stop hook feedback artifact lines
_STOP_HOOK_FEEDBACK_LINES = (
    "LAZY WORKAROUND", "EPISTEMIC FORMAT REPAIR", "EPISTEMIC VIOLATION",
    "pattern matched:", "required approach:", "remember:",
    "this suggests", "this is a", "⎿",
)


def _strip_quoted_content(response: str) -> str:
    """Remove quoted/attributed content and Stop-hook artifacts."""
    lines = response.split("\n")
    result: list[str] = []
    skip = False

    for line in lines:
        stripped = line.strip()

        if _BLOCKQUOTE_RE.match(line):
            continue

        if any(stripped.startswith(artifact) for artifact in _STOP_HOOK_FEEDBACK_LINES):
            skip = True
            continue

        if skip:
            if not stripped or len(stripped) > 100 or not stripped.startswith(
                ("⚠", "1.", "2.", "3.", "4.", "✓", "✗", "Do NOT", "- ", "* ")
            ):
                skip = False

        if not skip:
            result.append(line)

    return "\n".join(result)


def strip_for_gate_matching(response: str) -> str:
    """Strip quoted/attributed content and Stop-hook artifacts before gate matching."""
    return _strip_quoted_content(response)


# =============================================================================
# Self-test
# =============================================================================

if __name__ == "__main__":
    import sys

    cases = [
        # (response, expected_is_simple, expected_is_delivery)
        ("Yes, the fix is in.", True, False),
        ("Tests are passing.", True, True),
        ("103 passed, 2 failed.", True, True),
        ("All tests pass. Done.", True, True),
        ("I've fixed the import.", True, True),
        ("Files modified: Stop.py, test_stop.py\nTests added: 12 tests", True, True),
        ("Implementation complete. 4 files created, 2 tests written.", True, True),
        ("LIMITATIONS:\n- No graceful degradation for missing config", True, True),
        ("The root cause is that sys.path does not include the hooks directory.", False, False),
        ("This is a lazy workaround because the real fix would require significant refactoring.", False, False),
        ("The problem originates from the import chain — I traced it to line 42.", False, False),
        ("Because the gate fires on every response, it creates a loop.", False, False),
        ("Therefore, the fix requires adding a turn-mode check.", False, False),
        ("[FACT]\n- grep shows the import is missing\n[INFERENCE]\n- the fix is to add the import", False, False),
        ("> The root cause is X", False, False),
    ]

    failed = 0
    for resp, exp_simple, exp_delivery in cases:
        actual_simple = is_simple_epistemic_response(resp)
        actual_delivery = is_grounded_delivery_summary(resp)
        s_ok = actual_simple == exp_simple
        d_ok = actual_delivery == exp_delivery
        status = "✓" if (s_ok and d_ok) else "✗"
        if not (s_ok and d_ok):
            failed += 1
            print(f"{status} resp={resp[:40]:40s}  simple: {actual_simple} (exp {exp_simple})  delivery: {actual_delivery} (exp {exp_delivery})")
        else:
            print(f"{status} {resp[:40]:40s} → simple={actual_simple}, delivery={actual_delivery}")

    # Test determine_epistemic_applicability
    print("\n--- determine_epistemic_applicability tests ---")

    applicability_cases = [
        ("Yes, the fix is in.", "control", False, "none", "Turn mode 'control' is non-substantive"),
        ("Tests are passing.", "analysis", True, "simple", "Simple/delivery"),
        ("The root cause is X.", "analysis", True, "full", "Deep analysis"),
        ("103 passed, 2 failed.", "final-answer", True, "simple", "Simple/delivery"),
        ("[FACT]\n- evidence", "analysis", True, "full", "Deep analysis"),
    ]

    for resp, mode, exp_applicable, exp_level, exp_reason_substr in applicability_cases:
        decision = determine_epistemic_applicability(resp, turn_mode=mode)
        ok_applicable = decision.applicable == exp_applicable
        ok_level = decision.enforcement_level == exp_level
        ok_reason = exp_reason_substr in decision.reason
        status = "✓" if (ok_applicable and ok_level and ok_reason) else "✗"
        if status == "✗":
            failed += 1
            print(f"{status} resp={resp[:30]:30s} mode={mode} applicable={decision.applicable}(exp {exp_applicable}) level={decision.enforcement_level}(exp {exp_level})")
        else:
            print(f"{status} resp={resp[:30]:30s} mode={mode} applicable={decision.applicable} level={decision.enforcement_level}")

    print(f"\n{'All passed' if failed == 0 else f'{failed} FAILED'}")
    sys.exit(failed)