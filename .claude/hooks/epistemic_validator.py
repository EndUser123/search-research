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
# Regex patterns (originally from StopHook_epistemic_contract.py, now in _legacy/)
# ---------------------------------------------------------------------------

SECTION_ORDER = ["[FACT]", "[INFERENCE]", "[UNKNOWN]", "[RECOMMENDATION]"]
REPORT_SECTION_ORDER = ["[STATUS]", "[CHANGES]", "[RESULTS]", "[NEXT]"]
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
      | since\s+(?=\w+\s+(?:is|was|being|would|should|has|have|had))
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
# Data model
# ---------------------------------------------------------------------------


@dataclass
class EpistemicIssue:
    section: str  # "[FACT]", etc., or "__GLOBAL__"
    bullet_index: int  # 0-based, -1 for non-bullet/global
    type: str  # "format", "unsupported_fact", "causal_violation", "comparative_violation"
    message: str


@dataclass
class EpistemicVerdict:
    decision: Decision
    issues: List[EpistemicIssue]


@dataclass
class EpistemicConfig:
    mode: Decision = "warn"
    responseMode: str = "auto"  # "analysis", "report", or "auto"
    treat_format_violation_as: Decision = "block"
    treat_unsupported_fact_as: Decision = "block"
    treat_causal_violation_as: Decision = "warn"
    treat_comparative_violation_as: Decision = "warn"
    enable_causal_checks: bool = True
    enable_comparative_checks: bool = True


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
# Sanitization
# ---------------------------------------------------------------------------


def sanitize_response(raw_response: str) -> str:
    """Strip non-claim lines (headers, quotes, Stop diagnostics) from response."""
    try:
        from __lib.shared_helpers import strip_non_claim_lines
    except ImportError:
        # Fallback: minimal inline stripping if shared_helpers unavailable
        def strip_non_claim_lines(text: str) -> str:  # type: ignore[misc]
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

    return strip_non_claim_lines(raw_response)


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

    for line in lines:
        stripped = line.strip()
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


def decide_from_issues(issues: List[EpistemicIssue], cfg: EpistemicConfig) -> Decision:
    """Compute the strongest decision from collected issues."""
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
        return "allow"
    if cfg.mode == "warn" and worst == "block":
        return "warn"
    return worst


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


def is_status_summary_response(raw_response: str) -> bool:
    """Return True if the response is clearly a status/deliverable report,
    not an analytical answer subject to the 4-section contract.

    Conservative: only matches obvious report patterns. Analytical answers
    that happen to mention "files created" in passing will NOT match because
    the pattern requires the phrase to be a dominant theme (checked by looking
    at the first ~300 chars of the response).
    """
    if not raw_response:
        return False
    # Only check the beginning of the response where report headers appear.
    head = raw_response[:600]
    matches = _STATUS_SUMMARY_RE.findall(head)
    # Require at least 2 distinct matches OR a very strong single signal
    # (e.g., "Implementation complete." in the first line).
    if len(matches) >= 2:
        return True
    first_line = raw_response.split("\n", 1)[0].strip()
    if _STATUS_SUMMARY_RE.search(first_line):
        return True
    return False


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate(raw_response: str, config: Optional[EpistemicConfig] = None) -> EpistemicVerdict:
    """Analyze raw_response for structural, factual, causal, and comparative issues.

    Returns an EpistemicVerdict with decision and issue list.
    """
    cfg = config or EpistemicConfig()

    # Resolve response mode: explicit config overrides auto-detection.
    response_mode = cfg.responseMode
    if response_mode in ("auto", None):
        response_mode = detect_response_mode(raw_response)

    # Report mode does not follow the analytical 4-section contract.
    if response_mode == "report":
        return EpistemicVerdict(decision="allow", issues=[])

    clean = sanitize_response(raw_response)
    parsed, format_issues = parse_sections(clean)

    issues: List[EpistemicIssue] = list(format_issues)
    issues.extend(check_fact_support(parsed))
    if cfg.enable_causal_checks:
        issues.extend(check_causal_rules(parsed))
    if cfg.enable_comparative_checks:
        issues.extend(check_comparative_rules(parsed))

    decision = decide_from_issues(issues, cfg)
    return EpistemicVerdict(decision=decision, issues=issues)
