#!/usr/bin/env python3
"""Diagnostic analysis quality gate for the Stop pipeline.

Catches shallow one-story analyses even when they have citations. Fires only
for diagnostic/explanatory turns — root-cause analysis, regression diagnosis,
causal attribution, comparative diagnosis.

Checks (conservative — warn by default):
  1. Competing hypotheses — require ≥2 distinct explanations unless evidence
     is overwhelming and explicitly verified.
  2. Discriminating test / falsification — require ≥1 statement of what
     evidence would separate explanations.
  3. Baseline / null comparison — when metrics are used as diagnostic signals,
     require a comparison (prior run, control, no-change case, etc.).
  4. Mechanism trace — strong causal claims need source trace (file/line/test)
     or explicit uncertainty about the mechanism.

Does NOT fire for: implementation reports, status summaries, short factual
answers, direct file-edit confirmations, control/exploration turns.
"""
from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---




# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

def _normalize_stdout(data: dict) -> dict:
    """Normalize hook output to Claude Code Zod-valid schema."""
    if data.get('decision') == 'allow':
        return {'decision': 'approve'}
    if data.get('decision') == 'block':
        return {'decision': 'block', 'reason': data.get('reason', '')}
    if 'allow' in data:
        if data['allow'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'continue' in data:
        if data['continue'] is False:
            return {'decision': 'block', 'reason': data.get('reason', '')}
        return {'decision': 'approve'}
    if 'ok' in data:
        return {'decision': 'approve'}
    return data






import os
import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _is_enabled() -> bool:
    return os.environ.get("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_ENABLED", "true").lower() in (
        "1", "true", "yes", "on",
    )


def _gate_mode() -> str:
    """Return 'warn' or 'block'."""
    return os.environ.get("DIAGNOSTIC_ANALYSIS_QUALITY_GATE_MODE", "warn").lower()


# ---------------------------------------------------------------------------
# Diagnostic turn detection
# ---------------------------------------------------------------------------

_CAUSAL_PHRASES = re.compile(
    r"""
    \b(
        cause[sd]?
      | because\s+of
      | due\s+to
      | results?\s+in
      | result\s+of
      | lead[s]?\s+to
      | is\s+why
      | the\s+reason\s+(?:is|for)
      | happens?\s+when
      | occurs?\s+when
      | is\s+caused\s+by
      | is\s+driven\s+by
      | is\s+triggered\s+by
      | root\s+cause
      | explains?\s+(?:why|how|the)
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_DIAGNOSTIC_PHRASES = re.compile(
    r"""
    \b(
        root\s+cause
      | regression
      | why\s+did
      | why\s+is
      | why\s+does
      | what\s+caused
      | diagnosing
      | diagnosis
      | attribut(?:ed?|ion)
      | causal\s+(?:chain|mechanism|path)
      | performance\s+(?:regression|degradation)
      | comparative\s+diagnosis
      | investigating\s+(?:why|what|how)
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_METRIC_CLAIM_PHRASES = re.compile(
    r"""
    \b(
        \d+\s*(?:ms|seconds?|minutes?|s\b|percent|%|x\s+(?:faster|slower)|\d+x\b)
      | latency
      | throughput
      | response\s+time
      | memory\s+usage
      | cpu\s+usage
      | idle_wait
      | execution\s+time
      | wall\s+clock
      | (?:high|low|slow|fast|abnormal|elevated)\s+(?:wait|time|latency|usage|load)
      | \d+\s*(?:fold|times?)
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Signals this is NOT a diagnostic turn
_NON_DIAGNOSTIC_PHRASES = re.compile(
    r"""
    ^(?:
        (?:files?\s+)?(?:created|modified|written|changed|added|updated)
      | (?:all\s+)?(?:tests?\s+)?(?:passed|pass|ok|green|done|complete|fixed)
      | implemented
      | here(?:'s|\s+is)\s+(?:the|what\s+I)
      | (?:edit|wrote|added|created|updated)\s+(?:to\s+)?(?:the\s+)?(?:file|hook|module)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Short response threshold (words) — skip analysis for short responses
_MIN_DIAGNOSTIC_WORDS = 40


def _is_diagnostic_turn(response: str) -> bool:
    """Determine if this response is doing diagnosis/causal explanation."""
    if not response:
        return False

    stripped = response.strip()

    # Skip very short responses
    word_count = len(stripped.split())
    if word_count < _MIN_DIAGNOSTIC_WORDS:
        return False

    # Skip implementation reports and status summaries
    first_line = stripped.split("\n", 1)[0].strip()
    if _NON_DIAGNOSTIC_PHRASES.match(first_line):
        return False

    # Must contain BOTH causal language AND diagnostic intent
    has_causal = bool(_CAUSAL_PHRASES.search(stripped))
    has_diagnostic = bool(_DIAGNOSTIC_PHRASES.search(stripped))

    # Also count causal phrases — need at least 2 distinct causal assertions
    causal_matches = _CAUSAL_PHRASES.findall(stripped.lower())

    # Single causal phrase with diagnostic context also qualifies
    if has_causal and has_diagnostic:
        return True
    if len(causal_matches) >= 2:
        return True

    return False


# ---------------------------------------------------------------------------
# Quality checks
# ---------------------------------------------------------------------------

# 1. Competing hypotheses

_HYPOTHESIS_STRUCTURES = re.compile(
    r"""
    (?:
        hypothesis\s+[A-C1-3]
      | (?:two|three|2|3)\s+(?:possible|plausible|main|alternative|likely)\s+(?:causes?|explanations?|theories|accounts|hypotheses)
      | alternative(?:ly|\s+explanation|\s+hypothesis|\s+theory|\s+cause)
      | competing\s+(?:explanation|hypothesis|theory|cause)
      | (?:one|another)\s+(?:possible|plausible|likely)?\s*(?:cause|explanation|theory|hypothesis)\s+(?:is|would\s+be|could\s+be|might\s+be)
      | could\s+also\s+be
      | might\s+instead\s+be
      | on\s+the\s+other\s+hand
      | or\s+(?:possibly|perhaps|alternatively|maybe)
      | another\s+possibility
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Explicit "overwhelming evidence" language — exempts from competing-hypotheses requirement
_OVERWHELMING_EVIDENCE = re.compile(
    r"""
    (?:
        definitively\s+(?:confirmed|verified|proven|established)
      | overwhelming(?:ly)?\s+(?:evidence|support|clear)
      | only\s+possible\s+(?:explanation|cause)
      | (?:conclusively|unambiguously)\s+(?:shows|proves|demonstrates|established)
      | directly\s+observed\s+(?:and\s+)?verified
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _check_competing_hypotheses(response: str) -> str | None:
    """Return finding if no competing hypotheses are present."""
    if _OVERWHELMING_EVIDENCE.search(response):
        return None

    if _HYPOTHESIS_STRUCTURES.search(response):
        return None

    return (
        "DIAGNOSTIC_SINGLE_STORY: Response attributes a cause or explains a mechanism "
        "but presents only one explanation without alternatives. "
        "Add at least one competing hypothesis (e.g., 'Hypothesis A: ... Hypothesis B: ...') "
        "or explicitly state why evidence is overwhelming."
    )


# 2. Discriminating test / falsification condition

_DISCRIMINATING_TEST = re.compile(
    r"""
    (?:
        would\s+be\s+wrong\s+if
      | to\s+distinguish
      | (?:if|when)\s+\w+\s+has\s+(?:X|Y|A|B)
      | (?:supports?|points?\s+to)\s+(?:A|B|hypothesis\s+[A-C1-3])
      | falsif
      | (?:how\s+to\s+)?(?:test|check|verify)\s+(?:this|which|whether|the\s+hypothesis)
      | discriminating\s+(?:test|check|evidence|observation)
      | would\s+(?:rule\s+out|refute|disprove|confirm)
      | differentiates?\s+between
      | tells?\s+us\s+whether
      | (?:if|when)\s+(?:run\d+|check|test|case)\s+has
      | (?:this|the)\s+would\s+(?:support|favor|confirm|refute)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _check_discriminating_test(response: str) -> str | None:
    """Return finding if no falsification/discriminating condition present."""
    if _DISCRIMINATING_TEST.search(response):
        return None

    return (
        "DIAGNOSTIC_NO_FALSIFICATION: Response diagnoses a cause but does not state "
        "what evidence would separate explanations or prove them wrong. "
        "Add a discriminating test (e.g., 'This would be wrong if...', "
        "'To distinguish A vs B, check...')."
    )


# 3. Baseline / null comparison

_BASELINE_COMPARISON = re.compile(
    r"""
    (?:
        baseline
      | prior\s+(?:run|version|build|commit|session|state)
      | previous(?:ly)?\s+(?:run|version|build|commit|measured|observed|recorded|known)
      | before\s+(?:the\s+)?(?:change|update|fix|migration|modification|patch)
      | without\s+(?:auth|the\s+change|the\s+fix|X|this)
      | no-(?:auth|change|baseline|cache|lock)\s+(?:case|run|baseline|scenario)
      | control\s+(?:case|group|run)
      | (?:un)?changed\s+(?:version|case|baseline)
      | normal\s+(?:behavior|case|state|baseline|operation)
      | compared?\s+to\s+(?:baseline|prior|previous|before|control|v1|old)
      | reference\s+(?:value|run|point|case)
      | historical(?:ly)?\s+(?:value|average|norm|baseline)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _check_baseline_comparison(response: str) -> str | None:
    """Return finding if metric claims lack baseline/null comparison."""
    # Only fire when metric claims are present
    if not _METRIC_CLAIM_PHRASES.search(response):
        return None

    if _BASELINE_COMPARISON.search(response):
        return None

    return (
        "DIAGNOSTIC_NO_BASELINE: Response uses metrics as diagnostic signals "
        "without comparing to a baseline (prior run, control case, "
        "no-change scenario, etc.). Add a baseline comparison to support "
        "the metric-based claim."
    )


# 4. Mechanism trace

_FILE_OR_LINE_REF = re.compile(
    r"""
    (?:
        [\w/\\]+\.\w{1,4}(?:\s*:\s*\d+)?   # file.py:123
      | lines?\s+\d+                          # line 42
      | function\s+\w+                        # function foo
      | \b\w+_?\w*\(\)                        # foo()
      | class\s+\w+                           # class Foo
      | module\s+\w+                          # module foo
      | (?:see|check|verify)\s+\S+\.(?:py|js|ts|go|rs|rb)  # see file.py
    )
    """,
    re.VERBOSE,
)

_UNCERTAINTY_LANGUAGE = re.compile(
    r"""
    (?:
        not\s+yet\s+verified
      | mechanism\s+(?:is\s+)?(?:unclear|unverified|unknown|not\s+confirmed)
      | (?:haven't|have\s+not)\s+(?:verified|confirmed|traced)
      | unverified\s+(?:mechanism|path|cause|claim)
      | (?:would\s+)?need\s+to\s+(?:verify|confirm|trace|check)
      | (?:not\s+)?(?:sure|certain)\s+(?:why|whether|how|if)
      | (?:likely|probably|possibly|might|could)\s+(?:the\s+)?(?:mechanism|cause|reason)
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Strong causal claims that need mechanism traces
_STRONG_CAUSAL_CLAIM = re.compile(
    r"""
    \b(?:
        X\s+causes?\s+Y
      | (?:this|the)\s+(?:is\s+)?(?:directly\s+)?(?:why|causes?|triggers?|drives?|explains?)
      | (?:the\s+)?(?:hook|gate|module|function|process|service|system)\s+(?:refreshes?|reloads?|resets?|restarts?|invalidates?|blocks?|triggers?|causes?|handles?)
      | behavior\s+changed\s+(?:because|due\s+to|when|after)
      | (?:this|the)\s+gate\s+(?:is\s+)?(?:why|causes?|the\s+reason)
    )\b
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _check_mechanism_trace(response: str) -> str | None:
    """Return finding if strong causal claims lack mechanism trace or uncertainty."""
    if not _STRONG_CAUSAL_CLAIM.search(response):
        return None

    # Satisfied if file/line references exist
    if _FILE_OR_LINE_REF.search(response):
        return None

    # Satisfied if uncertainty language present
    if _UNCERTAINTY_LANGUAGE.search(response):
        return None

    return (
        "DIAGNOSTIC_NO_MECHANISM_TRACE: Response makes a strong causal claim "
        "without tracing the mechanism to source code, a file path, a line "
        "reference, or a test. Add a source trace (file:line) or explicitly "
        "state the mechanism has not been verified."
    )


# ---------------------------------------------------------------------------
# Shallow compliance detection
# ---------------------------------------------------------------------------

_HYPOTHESIS_BULLET_HEADERS = re.compile(
    r"(?:possible\s+causes?|hypotheses?|explanations?|theories?)\s*:\s*\n",
    re.IGNORECASE,
)

_BULLET_ITEM = re.compile(r"^\s*[-*]\s+(.+)$", re.MULTILINE)


def _is_shallow_compliance(response: str) -> str | None:
    """Detect empty-heading compliance: 'Possible causes:' followed by weak filler."""
    for m in _HYPOTHESIS_BULLET_HEADERS.finditer(response):
        # Find bullets after this header (within next 200 chars)
        after = response[m.end():m.end() + 300]
        bullets = _BULLET_ITEM.findall(after)
        if len(bullets) < 2:
            continue
        # Check if each bullet is substantive (> 15 words and not a restatement)
        substantive = 0
        for bullet in bullets[:4]:
            words = bullet.split()
            if len(words) >= 8:
                substantive += 1
        if substantive < 2:
            return (
                "DIAGNOSTIC_SHALLOW_COMPLIANCE: Response has a 'Possible causes:' "
                "or 'Hypotheses:' heading but the items underneath are too thin "
                "to be distinct explanatory claims. Each hypothesis should be "
                "substantive (at least 8 words with distinct reasoning)."
            )
    return None


# ---------------------------------------------------------------------------
# Gate orchestration
# ---------------------------------------------------------------------------

@dataclass
class DiagnosticFinding:
    check: str
    severity: str  # "warn" or "block"
    message: str


def analyze(response: str) -> list[DiagnosticFinding]:
    """Run all diagnostic quality checks on a response.

    Returns a list of findings (may be empty if response passes all checks).
    """
    findings: list[DiagnosticFinding] = []

    if not _is_diagnostic_turn(response):
        return findings

    # Check 1: competing hypotheses
    result = _check_competing_hypotheses(response)
    if result:
        findings.append(DiagnosticFinding(
            check="competing_hypotheses",
            severity="warn",
            message=result,
        ))

    # Check 2: discriminating test
    result = _check_discriminating_test(response)
    if result:
        findings.append(DiagnosticFinding(
            check="discriminating_test",
            severity="warn",
            message=result,
        ))

    # Check 3: baseline comparison
    result = _check_baseline_comparison(response)
    if result:
        findings.append(DiagnosticFinding(
            check="baseline_comparison",
            severity="warn",
            message=result,
        ))

    # Check 4: mechanism trace
    result = _check_mechanism_trace(response)
    if result:
        findings.append(DiagnosticFinding(
            check="mechanism_trace",
            severity="warn",
            message=result,
        ))

    # Check 5: shallow compliance
    result = _is_shallow_compliance(response)
    if result:
        findings.append(DiagnosticFinding(
            check="shallow_compliance",
            severity="block",
            message=result,
        ))

    return findings


def run(data: dict) -> dict | None:
    """Entry point for Stop_router in-process dispatch."""
    if not _is_enabled():
        return None

    response = data.get("response") or data.get("assistant_response") or ""
    if not response:
        return None

    findings = analyze(response)
    if not findings:
        return None

    mode = _gate_mode()

    # Shallow compliance always blocks regardless of mode
    block_findings = [f for f in findings if f.severity == "block"]
    warn_findings = [f for f in findings if f.severity == "warn"]

    if block_findings and mode in ("block", "warn"):
        return {
            "decision": "block",
            "reason": block_findings[0].message,
            "blocking_hook": "Stop_diagnostic_analysis_quality_gate.py",
        }

    if mode == "block" and warn_findings:
        return {
            "decision": "block",
            "reason": warn_findings[0].message,
            "blocking_hook": "Stop_diagnostic_analysis_quality_gate.py",
        }

    # Warn mode: return advisory systemMessage
    if warn_findings:
        messages = [f.message for f in warn_findings[:3]]
        return {
            "decision": "warn",
            "systemMessage": "\n".join(messages),
            "blocking_hook": "Stop_diagnostic_analysis_quality_gate.py",
        }

    return None
