#!/usr/bin/env python3
"""
DEPRECATED — Do not import. Retained for reference only.

Superseded by: epistemic_validator.py (unified, used by Stop.py).
This module is NOT in the Stop.py dispatch chain and is never executed.

Phase 1 Epistemic Contract Validator.

Enforces structured output format:
- [FACT] grounded statements with evidence source
- [INFERENCE] reasoning with explicit uncertainty markers
- [UNKNOWN] explicit ignorance admissions
- [RECOMMENDATION] proposals with goal/assumption/rationale

Each section must be present (even if empty), bullets must start with '- ',
and each tag has semantic rules enforced by regex checks.

Mode: Controlled by EPISTEMIC_CONTRACT_MODE env var.
  - "strict" (default): block non-compliant responses
  - "warn": collect violations without blocking (advisory)

Note on evidence: The gate treats prior tool outputs as valid evidence only when
they are explicitly quoted or restated in the current response (e.g. "pytest output
above shows 49 passed"). Vague references like "we saw earlier" are not sufficient.
Each [FACT] bullet must identify the source: (source: filename) or (source: filename:line).
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Optional


SECTION_ORDER = ["[FACT]", "[INFERENCE]", "[UNKNOWN]", "[RECOMMENDATION]"]

BULLET_RE = re.compile(r"^\s*-\s+")
WHITESPACE_RE = re.compile(r"\s+")

# Hard assertion signals: words that turn inference into asserted fact
HARD_ASSERTION_SIGNALS_RE = re.compile(
    r"\b(is|are|was|were|does|do|did|will|can|has|have|had|should|must|"
    r"causes|leads to|resulted in|proves|demonstrates|confirms|shows that|"
    r"the reason|the cause|because)\b",
    re.IGNORECASE,
)

UNCERTAINTY_WORDS_RE = re.compile(
    r"\b(probably|likely|may|might|could|suspect|infer|seems?|appears?)\b",
    re.IGNORECASE,
)
RECOMMENDATION_WORDS_RE = re.compile(
    r"\b(should|recommend|best|optimal|lowest[-\s]?risk|cleanest|simplest)\b",
    re.IGNORECASE,
)
RATIONALE_WORDS_RE = re.compile(
    r"\b(because|since|so that|in order to|so you can|so we can|to ensure|to avoid)\b",
    re.IGNORECASE,
)
ASSUMPTION_WORDS_RE = re.compile(
    r"\b(given|assuming|if your goal is|if your priority is)\b",
    re.IGNORECASE,
)
# Phase 2: Causal claim detector patterns
CAUSAL_PHRASES_RE = re.compile(
    r"""
    \b
    (
        cause[sd]?           # cause, causes, caused
      | because
      | due\s+to
      | results?\s+in
      | result\s+of
      | lead[s]?\s+to
      | bring[s]?\s+about
      | give[s]?\s+rise\s+to
      | is\s+why
      | the\s+reason\s+is
      | the\s+reason\s+for
      | happens?\s+when
      | occurs?\s+when
      | occurs?\s+because
      | is\s+caused\s+by
      | is\s+driven\s+by
      | is\s+triggered\s+by
    )
    \b
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Structured source suffix pattern: (source: filename:line) or (source: filename)
SOURCE_SUFFIX_RE = re.compile(r"\(source:\s*[\w./\\-]+(:\d+)?\)\s*$", re.IGNORECASE)
# Phrases that indicate user-sourced facts without code references
USER_SOURCE_RE = re.compile(
    r"according to the user|user described|user said|user stated|user noted",
    re.IGNORECASE,
)
# Phase 3: Comparative judgment detector patterns
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

# Hard assertion verbs — used to flag guarantee-style language in RECOMMENDATION
HARD_ASSERTION_VERBS_RE = re.compile(
    r"\b(?:is|are|was|were|means|ensures|guarantees)\b",
    re.IGNORECASE,
)


@dataclass
class ValidationIssue:
    section: str  # "[FACT]", "[INFERENCE]", etc.
    bullet_index: int  # 0-based within section, -1 for section-level
    message: str


@dataclass
class ValidationResult:
    ok: bool
    issues: List[ValidationIssue]

    def to_reason(self) -> str:
        """Format issues into a single diagnostic string."""
        if not self.issues:
            return ""
        parts = []
        for issue in self.issues:
            if issue.bullet_index < 0:
                loc = issue.section
            else:
                loc = f"{issue.section} bullet {issue.bullet_index + 1}"
            parts.append(f"{loc}: {issue.message}")
        return "Epistemic validation failed:\n" + "\n".join(parts)


def validate_epistemic_answer(text: str) -> ValidationResult:
    """
    Validate that `text` follows the Phase 1 epistemic tagging contract.

    Expected structure::

        [FACT]
        - ...
        [INFERENCE]
        - ...
        [UNKNOWN]
        - ...
        [RECOMMENDATION]
        - ...

    Rules (per the Phase 1 spec):
    - All four sections must be present in order.
    - Each bullet must start with '- '.
    - [FACT]: no uncertainty words; code refs need a source hint.
    - [INFERENCE]: must have at least one uncertainty marker per bullet.
    - [UNKNOWN]: must not contain recommendation words.
    - [RECOMMENDATION]: must have rationale OR assumption markers.
    """
    issues: List[ValidationIssue] = []

    if not text or not text.strip():
        # Empty response — let other gates handle it
        return ValidationResult(ok=True, issues=[])

    # Normalize line endings
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = normalized.split("\n")

    # Parse sections
    sections, global_lines = _split_into_sections(lines, text)

    # 1. Check for text outside all sections (global errors)
    if global_lines:
        issues.append(
            ValidationIssue(
                section="__GLOBAL__",
                bullet_index=-1,
                message=(
                    f"Found {len(global_lines)} line(s) outside any "
                    "[FACT]/[INFERENCE]/[UNKNOWN]/[RECOMMENDATION] section. "
                    "All content must be inside those sections."
                ),
            )
        )

    # 2. Check section presence and order using character positions from original text
    order_issues = _check_section_order(text)
    issues.extend(order_issues)

    # If structure is totally broken, bail early
    if any(i.section == "__GLOBAL__" for i in issues):
        return ValidationResult(ok=False, issues=issues)

    # 3. Validate each section's bullets and semantics
    for section in SECTION_ORDER:
        bullets = sections.get(section, [])
        # Basic bullet format check
        issues.extend(_check_bullet_format(section, bullets))
        # Semantic checks per section
        if section == "[FACT]":
            issues.extend(_check_fact_bullets(bullets))
        elif section == "[INFERENCE]":
            issues.extend(_check_inference_bullets(bullets))
        elif section == "[UNKNOWN]":
            issues.extend(_check_unknown_bullets(bullets))
        elif section == "[RECOMMENDATION]":
            issues.extend(_check_recommendation_bullets(bullets))

        # Phase 2: causal checks for all sections
        issues.extend(_check_causal_bullets(section, bullets))

        # Phase 3: comparative judgment checks for all sections
        issues.extend(_check_comparative_bullets(section, bullets))

    return ValidationResult(ok=len(issues) == 0, issues=issues)


def _split_into_sections(lines: List[str], text: str) -> tuple:
    """
    Parse lines into sections.

    Returns:
        tuple: (sections_dict, global_lines)
    """
    sections = {key: [] for key in SECTION_ORDER}
    current: Optional[str] = None
    global_lines: List[str] = []

    for raw_line in lines:
        line = raw_line.rstrip()
        stripped = line.strip()

        # Section heading?
        if stripped in SECTION_ORDER:
            current = stripped
            continue

        # Empty line — skip
        if not stripped:
            continue

        # Non-empty line before first section = global error
        if current is None:
            global_lines.append(line)
            continue

        # Record line under current section
        sections[current].append(line)

    return sections, global_lines


def _check_section_order(text: str) -> List[ValidationIssue]:
    """Check all four sections are present and in correct character order."""
    issues: List[ValidationIssue] = []

    # Find character position of each header in original text
    header_positions: dict = {}
    for section in SECTION_ORDER:
        pos = text.find(section)
        if pos >= 0:
            header_positions[section] = pos

    # Check all four sections are present
    present = [s for s in SECTION_ORDER if s in header_positions]
    if len(present) < len(SECTION_ORDER):
        missing = [s for s in SECTION_ORDER if s not in header_positions]
        for m in missing:
            issues.append(
                ValidationIssue(
                    section="__GLOBAL__",
                    bullet_index=-1,
                    message=f"Missing section heading {m}.",
                )
            )

    # Check order
    if len(present) == len(SECTION_ORDER):
        last_pos = -1
        for section in present:
            pos = header_positions[section]
            if pos < last_pos:
                issues.append(
                    ValidationIssue(
                        section="__GLOBAL__",
                        bullet_index=-1,
                        message=(
                            "Sections must appear in order: "
                            "[FACT], [INFERENCE], [UNKNOWN], [RECOMMENDATION]."
                        ),
                    )
                )
                break
            last_pos = pos

    return issues


def _check_bullet_format(section: str, bullets: List[str]) -> List[ValidationIssue]:
    """Check each bullet starts with '- '."""
    issues: List[ValidationIssue] = []

    # Empty section — must have at least "- (none)"
    if not bullets:
        issues.append(
            ValidationIssue(
                section=section,
                bullet_index=-1,
                message=f"{section} section is empty. Include at least one bullet, e.g. '- (none)'.",
            )
        )
        return issues

    for i, line in enumerate(bullets):
        if not BULLET_RE.match(line):
            issues.append(
                ValidationIssue(
                    section=section,
                    bullet_index=i,
                    message="Bullet must start with '- ' (dash + space).",
                )
            )
    return issues


def _strip_bullet(line: str) -> str:
    return BULLET_RE.sub("", line, count=1).strip()


def _is_code_related(text: str) -> bool:
    """Heuristic: does this bullet talk about code?"""
    code_keywords = (
        ".py", ".ts", ".js", ".go", ".java", ".rs",
        "file", "function", "class", "method", "module",
        "line ", "lines ", "code", "import", "def ", "const ",
        "gate", "verifier", "hook", "call", "invoke",
    )
    text_lower = text.lower()
    return any(kw in text_lower for kw in code_keywords)


def _check_fact_bullets(bullets: List[str]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    for i, line in enumerate(bullets):
        text = _strip_bullet(line)
        if text == "(none)":
            continue

        # No uncertainty language in FACT
        if UNCERTAINTY_WORDS_RE.search(text):
            issues.append(
                ValidationIssue(
                    section="[FACT]",
                    bullet_index=i,
                    message=(
                        "FACT bullet contains uncertainty language; "
                        "move to [INFERENCE] or remove: "
                        "'probably', 'likely', 'may', 'might', 'could', 'suspect', 'infer', 'seems', 'appears'."
                    ),
                )
            )

        # Require structured source suffix: (source: filename) or (source: filename:line)
        # Exempt: user attribution, (none) placeholder
        has_user_ref = bool(USER_SOURCE_RE.search(text))
        has_source_suffix = bool(SOURCE_SUFFIX_RE.search(text))
        if not (has_user_ref or has_source_suffix):
            issues.append(
                ValidationIssue(
                    section="[FACT]",
                    bullet_index=i,
                    message=(
                        "FACT bullet requires structured source suffix. "
                        "Add '(source: filename)' or '(source: filename:line)' at the end of the bullet. "
                        "E.g.: 'Stop.py line 236 sets response (source: Stop.py:236)'"
                    ),
                )
            )

    return issues


def _check_inference_bullets(bullets: List[str]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    for i, line in enumerate(bullets):
        text = _strip_bullet(line)
        if text == "(none)":
            continue

        # Only flag if the bullet reads as a hard assertion:
        # has hard assertion signal but NO uncertainty marker
        has_assertion = bool(HARD_ASSERTION_SIGNALS_RE.search(text))
        has_uncertainty = bool(UNCERTAINTY_WORDS_RE.search(text))
        if has_assertion and not has_uncertainty:
            issues.append(
                ValidationIssue(
                    section="[INFERENCE]",
                    bullet_index=i,
                    message=(
                        "INFERENCE bullet reads as a hard assertion. "
                        "Add uncertainty marker: 'may', 'might', 'could', 'I infer', 'I suspect', "
                        "'this suggests', 'this may indicate'."
                    ),
                )
            )
    return issues


def _check_unknown_bullets(bullets: List[str]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    for i, line in enumerate(bullets):
        text = _strip_bullet(line)
        if text == "(none)":
            continue

        # Must not smuggle in recommendations
        if RECOMMENDATION_WORDS_RE.search(text):
            issues.append(
                ValidationIssue(
                    section="[UNKNOWN]",
                    bullet_index=i,
                    message=(
                        "UNKNOWN bullet contains recommendation language "
                        "(e.g., 'should', 'best', 'recommend'). "
                        "Move that to [RECOMMENDATION]."
                    ),
                )
            )
    return issues


def _check_recommendation_bullets(bullets: List[str]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    for i, line in enumerate(bullets):
        text = _strip_bullet(line)
        if text == "(none)":
            continue

        # Require goal/assumption cue OR explicit rationale
        has_rationale = bool(RATIONALE_WORDS_RE.search(text))
        has_assumption = bool(ASSUMPTION_WORDS_RE.search(text))

        if not (has_rationale or has_assumption):
            issues.append(
                ValidationIssue(
                    section="[RECOMMENDATION]",
                    bullet_index=i,
                    message=(
                        "RECOMMENDATION bullet lacks goal/assumption or rationale. "
                        "Add one of: 'given', 'assuming', 'because', 'so that', 'if your goal is'."
                    ),
                )
            )
    return issues


# --------------------------------------------------------------------
# Phase 2: Causal claim detector
# --------------------------------------------------------------------

def _check_causal_bullets(section: str, bullets: List[str]) -> List[ValidationIssue]:
    """
    Phase 2: causal claim detector.

    We are conservative: we only react when we see explicit causal phrases.
    Rules by section:
      [UNKNOWN]: causal language is forbidden — move to INFERENCE with uncertainty
      [FACT]: causal is only allowed if directly quoted/observed; otherwise move to INFERENCE
      [INFERENCE]: causal allowed only if hedged with uncertainty markers
      [RECOMMENDATION]: causal allowed, but strong guarantees nudge toward rephrase
    """
    issues: List[ValidationIssue] = []
    for i, line in enumerate(bullets):
        text = _strip_bullet(line)
        if text == "(none)":
            continue

        has_causal = bool(CAUSAL_PHRASES_RE.search(text))
        if not has_causal:
            continue

        # 1) UNKNOWN: causal language is forbidden
        if section == "[UNKNOWN]":
            issues.append(
                ValidationIssue(
                    section=section,
                    bullet_index=i,
                    message=(
                        "UNKNOWN bullet contains causal language (e.g. 'because', 'causes', "
                        "'the reason is'). UNKNOWN is for admitting you do not know the cause; "
                        "move the causal hypothesis to [INFERENCE] with uncertainty."
                    ),
                )
            )
            continue

        # 2) FACT: require explicit strong evidence or downgrade to INFERENCE
        if section == "[FACT]":
            if "according to" in text.lower() or "log shows" in text.lower() or "trace shows" in text.lower():
                # Directly observed or quoted causal statement — acceptable
                continue

            issues.append(
                ValidationIssue(
                    section=section,
                    bullet_index=i,
                    message=(
                        "FACT bullet contains causal language but is not clearly presented as a "
                        "directly observed or quoted mechanism. Treat this as inference: move it "
                        "to [INFERENCE] and add uncertainty markers."
                    ),
                )
            )
            continue

        # 3) INFERENCE: require explicit uncertainty markers for causal claims
        if section == "[INFERENCE]":
            if UNCERTAINTY_WORDS_RE.search(text) is None:
                issues.append(
                    ValidationIssue(
                        section=section,
                        bullet_index=i,
                        message=(
                            "INFERENCE bullet contains causal language but lacks explicit "
                            "uncertainty (e.g., 'may', 'might', 'could', 'I infer', 'I suspect', "
                            "'this suggests'). Add uncertainty wording or rephrase."
                        ),
                    )
                )
            continue

        # 4) RECOMMENDATION: allow causal language, but discourage guarantees
        if section == "[RECOMMENDATION]":
            if HARD_ASSERTION_VERBS_RE.search(text):
                issues.append(
                    ValidationIssue(
                        section=section,
                        bullet_index=i,
                        message=(
                            "RECOMMENDATION bullet uses strong causal language that reads "
                            "like a guarantee (e.g., 'X is caused by Y', 'X guarantees Y'). "
                            "Rephrase to avoid guarantees, e.g., 'is likely to', 'may reduce'."
                        ),
                    )
                )
            # Otherwise, allow causal phrasing in recommendations.
            continue

    return issues


# --------------------------------------------------------------------
# Phase 3: Comparative judgment detector
# --------------------------------------------------------------------

def _check_comparative_bullets(section: str, bullets: List[str]) -> List[ValidationIssue]:
    """
    Phase 3: comparative judgment detector.

    We focus on obvious comparative/evaluative language.
    Rules by section:
      [UNKNOWN]: comparative language forbidden
      [FACT]: no internal comparative claims unless clearly quoted/external
      [INFERENCE]: strong comparatives (best/optimal/lowest risk) require uncertainty + fact reference
      [RECOMMENDATION]: comparative language requires explicit goal/assumption + rationale
    """
    issues: List[ValidationIssue] = []
    for i, line in enumerate(bullets):
        text = _strip_bullet(line)
        if text == "(none)":
            continue

        has_comp = bool(COMPARATIVE_WORDS_RE.search(text))
        if not has_comp:
            continue

        lower = text.lower()

        # 1) UNKNOWN: comparative language forbidden
        if section == "[UNKNOWN]":
            issues.append(
                ValidationIssue(
                    section=section,
                    bullet_index=i,
                    message=(
                        "UNKNOWN bullet contains comparative language (e.g., 'best', 'better', "
                        "'more robust'). UNKNOWN is only for stating what is not known; move "
                        "comparative judgments to [INFERENCE] or [RECOMMENDATION]."
                    ),
                )
            )
            continue

        # 2) FACT: forbid internal comparative claims unless clearly quoted/external
        if section == "[FACT]":
            if "according to" in lower or "docs say" in lower or "benchmark" in lower:
                continue

            issues.append(
                ValidationIssue(
                    section=section,
                    bullet_index=i,
                    message=(
                        "FACT bullet uses comparative language (e.g., 'best', 'optimal', "
                        "'most efficient') without clear external attribution. "
                        "Move this judgment to [INFERENCE] or [RECOMMENDATION], and keep "
                        "FACT for grounded observations."
                    ),
                )
            )
            continue

        # 3) INFERENCE: require uncertainty for strong comparatives
        if section == "[INFERENCE]":
            if SUPERLATIVE_ONLY_RE.search(text):
                if UNCERTAINTY_WORDS_RE.search(text) is None:
                    issues.append(
                        ValidationIssue(
                            section=section,
                            bullet_index=i,
                            message=(
                                "INFERENCE bullet makes a strong comparative claim "
                                "('best', 'optimal', 'lowest risk') without explicit "
                                "uncertainty (e.g., 'likely', 'may', 'could', 'I suspect'). "
                                "Add uncertainty wording and reference the facts it is based on."
                            ),
                        )
                    )
            continue

        # 4) RECOMMENDATION: require assumptions + goal/rationale for comparative claims
        if section == "[RECOMMENDATION]":
            has_assumption = bool(ASSUMPTION_WORDS_RE.search(text))
            has_rationale = bool(RATIONALE_WORDS_RE.search(text))
            has_superlative = bool(SUPERLATIVE_ONLY_RE.search(text))

            if has_superlative and not has_assumption:
                issues.append(
                    ValidationIssue(
                        section=section,
                        bullet_index=i,
                        message=(
                            "RECOMMENDATION bullet uses strong comparative language "
                            "('best', 'optimal', 'lowest risk') but does not state the "
                            "assumptions or goal (e.g., 'for minimal code churn', "
                            "'if your priority is performance'). Add an explicit assumption clause."
                        ),
                    )
                )
            elif not (has_assumption or has_rationale):
                issues.append(
                    ValidationIssue(
                        section=section,
                        bullet_index=i,
                        message=(
                            "RECOMMENDATION bullet uses comparative language but lacks "
                            "an explicit goal/assumption or rationale. Clarify what "
                            "criterion it is 'better' or 'simpler' for (e.g., maintenance, "
                            "performance, cognitive load)."
                        ),
                    )
                )
            continue

    return issues


# --------------------------------------------------------------------
# Stop gate function
# --------------------------------------------------------------------

def run(data: dict) -> dict | None:
    """
    Phase 1 & 2 & 3 epistemic contract gate.

    Phase 1 (format + basic semantics): controlled by EPISTEMIC_CONTRACT_MODE.
    Phase 2 (causal claim detector): controlled by EPISTEMIC_CAUSAL_MODE.
    Phase 3 (comparative judgment): controlled by EPISTEMIC_COMPARATIVE_MODE.

    Modes for each:
      - "off": checks run but never block/warn
      - "warn" (default for P2/P3): violations reported as advisory
      - "strict" (default for P1): violations can block

    Returns None (allow) if:
    - Response is empty
    - Response passes all validation checks

    Returns block dict if validation fails.
    """
    response = data.get("response", "")
    if not response:
        return None

    contract_mode = os.environ.get("EPISTEMIC_CONTRACT_MODE", "strict")
    causal_mode = os.environ.get("EPISTEMIC_CAUSAL_MODE", "warn")
    comparative_mode = os.environ.get("EPISTEMIC_COMPARATIVE_MODE", "warn")
    is_warn = contract_mode == "warn"

    result = validate_epistemic_answer(response)

    if result.ok:
        return None

    # Separate issue types by phase
    phase1_issues = [i for i in result.issues if not _is_causal_issue(i) and not _is_comparative_issue(i)]
    causal_issues = [i for i in result.issues if _is_causal_issue(i)]
    comparative_issues = [i for i in result.issues if _is_comparative_issue(i)]

    # Phase 1: always enforced, strict overrides warn
    if phase1_issues:
        if is_warn:
            return {"decision": "warn", "reason": _format_issues(phase1_issues), "blocking_hook": "Stop.py:epistemic_contract"}
        return {"decision": "block", "reason": _format_issues(phase1_issues), "blocking_hook": "Stop.py:epistemic_contract"}

    # Phase 2: causal issues
    if causal_issues and causal_mode != "off":
        if causal_mode == "warn":
            return {"decision": "warn", "reason": _format_issues(causal_issues), "blocking_hook": "Stop.py:epistemic_contract"}
        elif causal_mode == "strict":
            return {"decision": "block", "reason": _format_issues(causal_issues), "blocking_hook": "Stop.py:epistemic_contract"}

    # Phase 3: comparative issues
    if comparative_issues and comparative_mode != "off":
        if comparative_mode == "warn":
            return {"decision": "warn", "reason": _format_issues(comparative_issues), "blocking_hook": "Stop.py:epistemic_contract"}
        elif comparative_mode == "strict":
            return {"decision": "block", "reason": _format_issues(comparative_issues), "blocking_hook": "Stop.py:epistemic_contract"}

    return None


def _is_causal_issue(issue: ValidationIssue) -> bool:
    """Check if an issue was raised by Phase 2 causal detector."""
    return (
        "causal" in issue.message.lower()
        or "because" in issue.message.lower()
        or "causes" in issue.message.lower()
        or "the reason" in issue.message.lower()
        or "guarantee" in issue.message.lower()
    )


def _is_comparative_issue(issue: ValidationIssue) -> bool:
    """Check if an issue was raised by Phase 3 comparative detector."""
    return (
        "comparative" in issue.message.lower()
        or "best" in issue.message.lower()
        or "optimal" in issue.message.lower()
        or "lowest risk" in issue.message.lower()
        or "more robust" in issue.message.lower()
        or "simpler" in issue.message.lower()
        or "better" in issue.message.lower()
    )


def _format_issues(issues: List[ValidationIssue]) -> str:
    """Format a list of issues into a single diagnostic string."""
    parts = []
    for issue in issues:
        if issue.bullet_index < 0:
            loc = issue.section
        else:
            loc = f"{issue.section} bullet {issue.bullet_index + 1}"
        parts.append(f"{loc}: {issue.message}")
    return "Epistemic validation failed:\n" + "\n".join(parts)
