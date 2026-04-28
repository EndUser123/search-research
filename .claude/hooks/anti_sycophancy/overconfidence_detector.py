"""
Overconfidence Detector - Catches unverified causal assertions and catastrophizing.

Detects patterns where the LLM makes confident causal claims without evidence:
- "This explains why..." (causal assertion)
- "This is why..." (causal assertion)
- "...is broken" (catastrophizing)
- "...completely fails" (catastrophizing)

PRINCIPLE: The LLM knows if it verified causation or just pattern-matched.
           It just doesn't say so unless caught.

Usage:
    from anti_sycophancy.overconfidence_detector import detect_overconfidence
    
    result = detect_overconfidence(response_text)
    if result:
        print(f"Detected: {result.pattern_type} -> {result.suggestion}")
"""

import re
from typing import List, NamedTuple, Optional

__all__ = ["detect_overconfidence", "detect_all_overconfidence", "OverconfidenceMatch"]


def _infer_structural_subject(response: str) -> str | None:
    """
    Extract the target subject family from a structural assessment claim.

    Scans for directory-prefixed structural claims:
      "refactor/ structure is optimal"  -> "refactor"
      "skills/ pattern is correct"       -> "skills"
      "plugin/ design is intentional"   -> "plugin"

    Also handles bare structural claims without directory prefix
    (returns None — fallback to current scoping logic):
      "Optimal structure — one exception"  -> None

    Returns the subject string or None if the claim has no
    directory-prefixed subject (triggers fallback to general scope check).
    """
    if not response:
        return None

    text_lower = response.lower()

    # Pattern: subject/ followed by structural keyword
    # e.g. "refactor/ structure" -> captures "refactor"
    # Handles multi-segment paths like "skills/code/structure"
    # Pattern: subject/ followed by structural keyword
    # e.g. "refactor/ structure" -> captures "refactor"
    # Allows path segments and whitespace between / and keyword
    patterns = [
        r'(\w+)/(?:[\w/]*\s*)*(?:structure|pattern|design|architecture|organization)\b',
        r'(?:the\s+)?(\w+)/(?:[\w/]*\s*)*(?:structure|pattern|design)\b',
    ]

    for pattern in patterns:
        m = re.search(pattern, text_lower)
        if m:
            return m.group(1)

    return None


def _has_comparison_evidence(
    tool_events: list[dict],
    response: str = "",
) -> bool:
    """
    Check if tool_events contain quality comparison evidence for structural claims.

    Requires meaningful comparison work — not just counts or repeated access
    to the same file, and not just distinctness without shared comparison set.

    Decision rule:
      - enumeration + ≥2 distinct inspected peers FROM THE SAME SCOPE ROOT -> True
      - ≥3 distinct inspected peers ALL FROM THE SAME ROOT (no enumeration) -> True
      - enumeration-only, no inspection -> False
      - all reads of same file, or single peer -> False
      - inspected peers from MIXED (unrelated) roots -> False

    "enumeration" = ls/find/grep/fd commands that list or search across
    multiple peer targets (glob pattern, multiple path args, find-style search).
    "inspection" = Read events on distinct file paths.
    "scope root" = the parent directory/group under which compared peers live
      (e.g., "skills" from "ls skills/*/"; "src" from "find src -name '*.rs'").

    Does NOT hardcode any specific path patterns (skills/, src/, etc.).
    """
    if not tool_events:
        return False

    comparison_commands = frozenset([
        "ls", "find", "grep", "rg", "fd", "bat",
        "Get-ChildItem", "gci", "dir", "Select-String",
    ])

    # ---------- helpers ----------

    def _normalize_path(path: str) -> str:
        """
        Normalize a file path to its meaningful relative component.

        Repeated reads of the same file produce the same normalized string.
        Reads of sibling files produce distinct normalized strings.

        Examples:
          skills/code/SKILL.md   ->  code/SKILL.md   (strips top-level dir)
          src/lib/module_a.rs    ->  lib/module_a.rs
          .claude/hooks/foo.py   ->  hooks/foo.py
        """
        if not path:
            return path
        normalized = path.replace("\\", "/").replace("//", "/")
        if normalized.startswith("./"):
            normalized = normalized[2:]

        parts = normalized.split("/")
        if len(parts) <= 1:
            return normalized
        return "/".join(parts[1:])

    def _scope_root_of(path: str) -> str:
        """
        Return the scope root of an original (non-normalized) path.

        The scope root is the first directory segment of the ORIGINAL path,
        NOT the normalized path. This preserves cross-reference with
        enumeration scope roots which are derived from original command paths.

        Examples:
          skills/foo/SKILL.md  ->  skills     (not 'foo')
          src/lib/module_a.rs   ->  src
          .claude/hooks/foo.py ->  .claude
        """
        normalized = path.replace("\\", "/").replace("//", "/")
        if normalized.startswith("./"):
            normalized = normalized[2:]
        parts = normalized.split("/")
        return parts[0] if parts else normalized

    def _infer_enum_scope_roots(command: str) -> frozenset[str]:
        """
        Infer the scope roots targeted by an enumeration Bash command.

        Scans non-flag positional arguments for directory paths and glob
        patterns to determine which directory trees were being enumerated.
        Skips quoted strings (pattern arguments to grep/find).

        Returns a frozenset of scope root strings.

        Examples:
          ls skills/*/            -> {'skills'}
          ls skills/ packages/    -> {'skills', 'packages'}
          find src -name "*.rs"   -> {'src'}
          grep -r "pattern" skills/  -> {'skills'}
        """
        if not command:
            return frozenset()

        tokens = command.lower().split()
        if not tokens:
            return frozenset()

        cmd_base = tokens[0]
        roots: set[str] = set()

        # All non-flag positional args
        non_flag = [t for t in tokens[1:] if not t.startswith("-")]

        for arg in non_flag:
            arg_clean = arg.rstrip("/")
            # Skip quoted strings (pattern args to grep/find/-name)
            if arg_clean.startswith('"') and arg_clean.endswith('"'):
                continue
            if arg_clean.startswith("'") and arg_clean.endswith("'"):
                continue
            if not arg_clean or arg_clean == "*":
                continue

            if "*" in arg:
                # Glob: extract the directory root before the first * segment
                # e.g. "skills/*/" -> "skills"; "skills/*/SKILL.md" -> "skills"
                before_star = arg.split("*")[0].rstrip("/")
                if before_star:
                    segments = before_star.split("/")
                    roots.add(segments[0] if segments[0] else (segments[1] if len(segments) > 1 else before_star))
            else:
                # Plain path: first segment is the scope root
                segments = arg_clean.split("/")
                roots.add(segments[0] if segments[0] else arg_clean)

        return frozenset(roots)

    # ---------- classify events ----------

    has_enumeration = False
    enumeration_scope_roots: set[str] = set()  # roots inferred from enum commands
    inspected_paths: set[str] = set()  # distinct normalized file paths read
    inspected_original_paths: list[str] = []  # original paths for scope root computation

    for event in tool_events:
        tool_name = event.get("name", "")
        command = event.get("command", "")
        output_excerpt = event.get("output_excerpt", "")

        # Bash: detect enumeration commands and infer scope roots
        if tool_name == "Bash" and command:
            cmd_lower = command.lower()
            tokens = cmd_lower.split()
            if tokens:
                cmd_base = tokens[0]
            else:
                cmd_base = ""

            if cmd_base not in comparison_commands:
                continue

            enumeration_signals = [
                "*",
                "-o", "-a", "-and", "-or",
                "|",
                "-name", "-path", "-prune", "-type",
                "-maxdepth", "-mindepth",
            ]

            is_enumeration = any(sig in cmd_lower for sig in enumeration_signals)

            non_flag_args = [t for t in tokens[1:] if not t.startswith("-")]
            if len(non_flag_args) >= 2:
                is_enumeration = True

            if is_enumeration:
                has_enumeration = True
                scope_roots = _infer_enum_scope_roots(command)
                enumeration_scope_roots.update(scope_roots)

        # Read: track distinct files (normalize preserving sibling context)
        if tool_name == "Read":
            path = command.get("file_path") if isinstance(command, dict) else ""
            if not path and output_excerpt:
                path = output_excerpt
            if path:
                normalized = _normalize_path(path)
                inspected_paths.add(normalized)
                inspected_original_paths.append(path)

    distinct_peers = len(inspected_paths)

    # ---------- scope-consistency check ----------
    # Compute scope root for each inspected path
    # Use ORIGINAL paths (not normalized) so scope roots align with enum roots
    inspected_scope_roots = {_scope_root_of(p) for p in inspected_original_paths}

    # ---------- subject-awareness check ----------
    # If the response has a directory-prefixed structural claim,
    # require that the evidence target matches that subject.
    # e.g. "refactor/ structure is optimal" + ls skills/*/ -> BLOCK (wrong subject)
    # e.g. "refactor/ structure is optimal" + ls refactor/*/ + reads refactor/*.md -> ALLOW
    subject = _infer_structural_subject(response) if response else None

    if has_enumeration:
        # With enumeration: all inspected roots must be among enum roots.
        # If subject is known, further filter enum roots to the subject.
        # e.g. subject="refactor", enum roots={"refactor","skills"} -> filter to {"refactor"}
        # If subject not in any enum root -> BLOCK (wrong subject)
        # e.g. subject="refactor", enum roots={"skills"} -> BLOCK
        if subject:
            subject_roots = {r for r in enumeration_scope_roots if r == subject}
            if not subject_roots:
                return False  # subject not among enumerated roots -> wrong subject
            enumeration_scope_roots = subject_roots
        # Now apply the subset check with the filtered roots
        if not inspected_scope_roots:
            return False
        mixed_scope = bool(inspected_scope_roots - enumeration_scope_roots)
        if mixed_scope:
            return False
        if distinct_peers >= 2:
            return True
        return False
    else:
        # No enumeration: all inspected paths must share ONE scope root.
        # If subject is known, require that root to match the subject.
        # e.g. subject="refactor", inspected roots={"refactor"} -> ALLOW
        # e.g. subject="refactor", inspected roots={"skills"} -> BLOCK
        if subject:
            if subject not in inspected_scope_roots:
                return False  # inspected a different scope than the claim subject
        if distinct_peers >= 3 and len(inspected_scope_roots) == 1:
            return True
        return False


class OverconfidenceMatch(NamedTuple):
    """Detection result with remediation guidance."""
    matched: str           # The problematic phrase
    pattern_type: str      # "causal_assertion" | "catastrophizing" | "unverified_attribution" | "structural_assessment" | "overconfident_intensifier" | "outcome_attribution"
    suggestion: str        # How to fix it
    severity: str          # "flag" (warn) or "block" (reject)


# === WORD SETS (structural detection, not brittle regex) ===

# Causal assertion without evidence - pattern-matching from error to cause
CAUSAL_WORDS = frozenset([
    "explains",      # "this explains why"
    "proves",        # "this proves that"
    "confirms",      # "this confirms"
    "demonstrates",  # "this demonstrates"
    "shows",         # "this shows that" (when followed by causation)
    "indicates",     # "this indicates"
    "reveals",       # "this reveals"
    "establishes",   # "this establishes"
])

CAUSAL_PHRASES = [
    r"\bthis\s+explains\b",
    r"\bwhich\s+explains\b",
    r"\bthat\s+explains\b",
    r"\bthis\s+is\s+why\b",
    r"\bthis\s+is\s+the\s+reason\b",
    r"\bthe\s+reason\s+is\b",
    r"\bcaused\s+by\b",
    r"\bbecause\s+of\s+this\b",
    r"\bdue\s+to\s+this\b",
    r"\bthis\s+proves\b",
    r"\bthis\s+indicates\b",
    r"\bthis\s+confirms\b",
    r"\bthis\s+demonstrates\b",
]

# Catastrophizing - absolute statements about system state
CATASTROPHE_PHRASES = [
    r"\bis\s+broken\b",
    r"\bare\s+broken\b",
    r"\bcompletely\s+fails\b",
    r"\bcompletely\s+broken\b",
    r"\btotally\s+fails\b",
    r"\btotally\s+broken\b",
    r"\bdoesn't\s+work\s+at\s+all\b",
    r"\bcan't\s+work\b",
    r"\bwill\s+never\s+work\b",
    r"\bis\s+unusable\b",
    r"\bis\s+fundamentally\s+flawed\b",
    r"\bthe\s+system\s+is\s+broken\b",
]

# Overconfident intensifiers - certainty without evidence
INTENSIFIER_PHRASES = [
    r"\bdefinitely\s+explains\b",
    r"\bdefinitely\s+proves\b",
    r"\bdefinitely\s+shows\b",
    r"\bdefinitely\s+indicates\b",
    r"\bdefinitely\s+appropriate\b",
    r"\bdefinitely\s+correct\b",
    r"\bdefinitely\s+the\s+(?:cause|reason|problem)\b",
    r"\bclearly\s+the\s+(?:cause|reason|problem)\b",
    r"\bobviously\s+the\s+(?:cause|reason|problem)\b",
]

# Unverified attribution - claiming to know root cause
ATTRIBUTION_PHRASES = [
    r"\bthe\s+root\s+cause\s+is\b",
    r"\bthe\s+underlying\s+issue\s+is\b",
    r"\bthe\s+real\s+problem\s+is\b",
    r"\bthe\s+actual\s+issue\s+is\b",
]

# Outcome attribution - claiming X caused/handled outcome without tracing
# Pattern: Testing X, Y happened, therefore X caused Y (post-hoc fallacy)
OUTCOME_ATTRIBUTION_PHRASES = [
    r"\bcorrectly\s+(?:blocked|handled|triggered|prevented|caught)\b",
    r"\bsuccessfully\s+(?:blocked|handled|triggered|prevented|caught)\b",
    r"\b(?:blocked|handled|triggered|prevented|caught)\s+by\b",
    r"\bis\s+responsible\s+for\b",
    r"\bis\s+(?:what|why)\s+(?:blocked|caused|triggered|prevented)\b",
]

# Structural assessment - confident claim about code/architecture structure without evidence
# "optimal structure", "correct by design", "intentional exception", "deliberate pattern"
STRUCTURAL_ASSESSMENT_PHRASES = [
    r"\boptimal\s+(?:structure|architecture|design|organization)\b",
    r"\bcorrect\s+by\s+(?:its\s+)?design\b",
    r"\bintentional\s+(?:exception|omission|design|pattern)\b",
    r"\bdeliberate\s+(?:pattern|exception|design|choice)\b",
    r"\bproper\s+structure\b",
    r"\bcorrect\s+structure\b",
    r"\bappropriate\s+structure\b",
    r"\bthat's?\s+(?:a\s+)?(?:deliberate|intentional)\s+(?:pattern|choice|design)\b",
    r"\bcorrect\s+—\s*(?:it's\s+)?(?:the\s+)?optimal\b",
    r"\boptimal\s+—\s*(?:one\s+)?(?:intentional|deliberate)\s+exception\b",
    # Directory-prefixed structural claims with em-dash exception format
    r"\b(?:[\w/]+/\s*)?(?:architecture|structure|design|pattern)\s+—\s*(?:one\s+)?(?:intentional|deliberate)\s+exception\b",
    r"\b(?:[\w/]+/\s*)?(?:architecture|structure|design|pattern)\s+—\s*(?:intentional|deliberate)\b",
    # Passive-voice forms: "architecture is optimal", "pattern is intentional"
    # Keyword appears AFTER the structure noun (is KEYWORD, not KEYWORD noun)
    r"\b(?:architecture|structure|design|pattern)\s+is\s+(?:optimal|intentional|deliberate|correct)\b",
    r"\b(?:architecture|structure|design|organization)\s+is\s+(?:optimal|proper|correct)\b",
]

# Evidence markers that make causal claims acceptable
# NOTE: Current mode is lenient (accepts any marker).
# Future: Add STRICT_EVIDENCE_MODE env var requiring explicit "[Tier X]:" format
# Rationale: Staged adoption - start lenient, tighten based on effectiveness data
EVIDENCE_MARKERS = frozenset([
    "tier 1", "tier 2", "tier1", "tier2",
    "verified", "confirmed by", "test output shows",
    "logs show", "execution shows", "evidence:",
    "[supported]", "[verified]",
    "compared against", "compared across", "after comparing", "comparing against",
    "verified across", "verified against",
])

# Regex evidence patterns — catch count-specific comparisons substring matching misses
# e.g. "reviewed 36 files", "checked 12 instances", "enumerated all skills"
EVIDENCE_MARKER_PATTERNS = [
    r'(?:checked|examined|reviewed)\s+\d+\s+(?:files?|instances?|examples?|cases?|skills|items)',
    r'(?:enumerated|listed)\s+(?:all|every)\b',
    r'after\s+(?:checking|reviewing|examining|comparing)\s+(?:all|every|\d+)\b',
    r'(?:inspected|scanned)\s+(?:all|every|\d+)\s+(?:files?|instances?|examples?|cases?|skills)',
]
_EVIDENCE_MARKER_PATTERNS = [re.compile(p, re.IGNORECASE) for p in EVIDENCE_MARKER_PATTERNS]

# Explanatory prose detection patterns
# Used by _is_explanatory_prose() to distinguish explanatory prose from technical assertions
DATA_INDICATORS = [
    r'\d+[,\d]*\s*(?:chars?|bytes?|lines?|items?|files?|results?|entries?)',  # "3,000+ chars"
    r'\d+%',  # percentages
    r'\d+\s*(?:seconds?|minutes?|hours?|ms)\b',  # time measurements
    r'\b(?:roughly|approximately|about|around|~)\s*\d+',  # approximate numbers
    r'\d+\+\s*(?:chars?|bytes?|lines?)',  # "3000+ chars"
]

EXPLANATORY_CONTEXT_PATTERNS = [
    r'\bbased\s+on\b',
    r'\baccording\s+to\b',
    r'\bfrom\s+the\b',
    r'\bin\s+the\s+(?:output|result|response)\b',
    r'\bthe\s+(?:output|result|response)\b',
]


# Compile patterns for efficiency
_CAUSAL_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CAUSAL_PHRASES]
_CATASTROPHE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in CATASTROPHE_PHRASES]
_ATTRIBUTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ATTRIBUTION_PHRASES]
_INTENSIFIER_PATTERNS = [re.compile(p, re.IGNORECASE) for p in INTENSIFIER_PHRASES]
_OUTCOME_ATTRIBUTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in OUTCOME_ATTRIBUTION_PHRASES]
_STRUCTURAL_ASSESSMENT_PATTERNS = [re.compile(p, re.IGNORECASE) for p in STRUCTURAL_ASSESSMENT_PHRASES]
_DATA_INDICATOR_PATTERNS = [re.compile(p, re.IGNORECASE) for p in DATA_INDICATORS]
_EXPLANATORY_CONTEXT_PATTERNS = [re.compile(p, re.IGNORECASE) for p in EXPLANATORY_CONTEXT_PATTERNS]


def _has_evidence_marker(text: str) -> bool:
    """Check if text contains evidence tier citation or count-specific comparison."""
    text_lower = text.lower()
    if any(marker in text_lower for marker in EVIDENCE_MARKERS):
        return True
    return any(p.search(text) for p in _EVIDENCE_MARKER_PATTERNS)


def _is_explanatory_prose(response: str, user_prompt: str) -> bool:
    """
    Detect if response is explanatory prose answering user's explanatory question.

    Explanatory prose should be allowed even if it contains causal assertion phrases.
    This reduces false positives when the AI is genuinely explaining its reasoning.

    Indicators of explanatory prose:
    1. User asked an explanatory question ("why", "explain", "clarify", "reason for")
    2. Response contains data indicators (numbers, measurements, specific details)
    3. Response has explanatory context words (e.g., "based on", "according to")

    Returns:
        True if response appears to be explanatory prose (allow it)
        False if response appears to be technical causal assertion (flag it)
    """
    # Check 1: User asked an explanatory question
    if not user_prompt:
        return False
    user_prompt_lower = user_prompt.lower()

    # Detect explanatory question patterns
    has_why_question = re.search(r'\bwhy\b', user_prompt_lower)

    # Detect synonym patterns: "explain X", "clarify X", "what's the reason for X"
    has_explain_synonym = re.search(
        r'\b(explain|clarify|describe|detail|elaborate)\b\s+(this|the|that|what|how|why)',
        user_prompt_lower
    )
    has_reason_synonym = re.search(
        r"\bwhat'?s\s+(the\s+)?reason\s+(for|behind|that)\b",
        user_prompt_lower
    )

    if not (has_why_question or has_explain_synonym or has_reason_synonym):
        return False  # Not explanatory prose if user didn't ask for explanation

    # Check 2: Response contains data indicators
    # Numbers, measurements, specific details suggest explanation with evidence
    response_lower = response.lower()
    has_data_indicator = any(pattern.search(response_lower) for pattern in _DATA_INDICATOR_PATTERNS)

    # Check 3: Response has explanatory context words
    has_explanatory_context = any(pattern.search(response_lower) for pattern in _EXPLANATORY_CONTEXT_PATTERNS)

    # Allow if response has data OR explanatory context
    return has_data_indicator or has_explanatory_context


def _find_pattern(text: str, patterns: List[re.Pattern]) -> Optional[re.Match]:
    """Find first matching pattern in text."""
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return match
    return None


def detect_overconfidence(
    response: str,
    user_prompt: str = "",
    tool_events: list[dict] | None = None,
) -> Optional[OverconfidenceMatch]:
    """
    Detect overconfident assertions without evidence.

    Returns None if clean, OverconfidenceMatch if problematic.

    Strategy:
    1. Check for causal assertion patterns
    2. Check for catastrophizing patterns
    3. Check for unverified attribution
    4. If found, check if evidence marker present (makes it acceptable)

    Context-aware filtering:
    - Explanatory prose answering user's "why" question with data is allowed
    - Technical causal assertions without evidence are flagged
    """
    if not response:
        return None

    # Normalize whitespace for matching
    text = ' '.join(response.split())

    # 1. Check for catastrophizing FIRST - catastrophic phrases should NEVER be allowed,
    #    even in explanatory prose (pre-mortem finding 1.2)
    catastrophe_match = _find_pattern(text, _CATASTROPHE_PATTERNS)
    if catastrophe_match and not _has_evidence_marker(text):
        return OverconfidenceMatch(
            matched=catastrophe_match.group(0),
            pattern_type="catastrophizing",
            suggestion="Specify scope: 'X functionality is not working' instead of 'system is broken'",
            severity="flag"
        )

    # 2. Check for causal assertions
    causal_match = _find_pattern(text, _CAUSAL_PATTERNS)
    if causal_match and not _has_evidence_marker(text):
        # Context-aware filtering: Allow explanatory prose answering user's "why" question
        if _is_explanatory_prose(text, user_prompt):
            return None  # Allow explanatory prose even with causal assertion phrase
        return OverconfidenceMatch(
            matched=causal_match.group(0),
            pattern_type="causal_assertion",
            suggestion="Add evidence tier: '[Tier X]: This explains...' or reframe as hypothesis: 'This MAY explain...'",
            severity="flag"
        )

    # 3. Check for unverified attribution (root cause claims)
    attribution_match = _find_pattern(text, _ATTRIBUTION_PATTERNS)
    if attribution_match and not _has_evidence_marker(text):
        return OverconfidenceMatch(
            matched=attribution_match.group(0),
            pattern_type="unverified_attribution",
            suggestion="Root cause claims require Tier 1/2 evidence. Add verification or use 'Hypothesis:' prefix",
            severity="flag"  # Could be "block" for high-stakes contexts
        )

    # 4. Check for overconfident intensifiers
    intensifier_match = _find_pattern(text, _INTENSIFIER_PATTERNS)
    if intensifier_match and not _has_evidence_marker(text):
        return OverconfidenceMatch(
            matched=intensifier_match.group(0),
            pattern_type="overconfident_intensifier",
            suggestion="'Definitely/clearly/obviously' claims need evidence. Remove intensifier or add tier citation",
            severity="flag"
        )

    # 5. Check for outcome attribution (post-hoc causation claims)
    outcome_match = _find_pattern(text, _OUTCOME_ATTRIBUTION_PATTERNS)
    if outcome_match and not _has_evidence_marker(text):
        return OverconfidenceMatch(
            matched=outcome_match.group(0),
            pattern_type="outcome_attribution",
            suggestion="Trace which component caused outcome (logs, hook output). Context ≠ causation. Use [INFERRED] if untraced",
            severity="flag"
        )

    # 6. Check for structural assessment — confident claim about code/architecture
    #    structure without quantified evidence or tool-based comparison
    structural_match = _find_pattern(text, _STRUCTURAL_ASSESSMENT_PATTERNS)
    if structural_match and not _has_evidence_marker(text):
        # If structural claim detected, allow only if tool_events show actual comparison work
        if tool_events and _has_comparison_evidence(tool_events, text):
            return None  # Allow: comparison evidence exists
        return OverconfidenceMatch(
            matched=structural_match.group(0),
            pattern_type="structural_assessment",
            suggestion="Structural claims need quantification. Add: 'After reviewing N files/skills', 'Compared against all N peers', or '[Tier X]'",
            severity="flag"
        )

    return None


def detect_all_overconfidence(
    response: str,
    tool_events: list[dict] | None = None,
) -> List[OverconfidenceMatch]:
    """
    Detect ALL overconfidence patterns (not just first).
    
    Useful for comprehensive analysis.
    """
    if not response:
        return []

    results = []
    text = ' '.join(response.split())
    has_evidence = _has_evidence_marker(text)

    if not has_evidence:
        # Collect all causal matches
        for pattern in _CAUSAL_PATTERNS:
            for match in pattern.finditer(text):
                results.append(OverconfidenceMatch(
                    matched=match.group(0),
                    pattern_type="causal_assertion",
                    suggestion="Add evidence tier or reframe as hypothesis",
                    severity="flag"
                ))

        # Collect all catastrophe matches
        for pattern in _CATASTROPHE_PATTERNS:
            for match in pattern.finditer(text):
                results.append(OverconfidenceMatch(
                    matched=match.group(0),
                    pattern_type="catastrophizing",
                    suggestion="Specify scope instead of absolute statements",
                    severity="flag"
                ))

        # Collect all attribution matches
        for pattern in _ATTRIBUTION_PATTERNS:
            for match in pattern.finditer(text):
                results.append(OverconfidenceMatch(
                    matched=match.group(0),
                    pattern_type="unverified_attribution",
                    suggestion="Root cause claims require evidence tier",
                    severity="flag"
                ))

        # Collect all intensifier matches
        for pattern in _INTENSIFIER_PATTERNS:
            for match in pattern.finditer(text):
                results.append(OverconfidenceMatch(
                    matched=match.group(0),
                    pattern_type="overconfident_intensifier",
                    suggestion="Remove intensifier or add evidence",
                    severity="flag"
                ))

        # Collect all outcome attribution matches
        for pattern in _OUTCOME_ATTRIBUTION_PATTERNS:
            for match in pattern.finditer(text):
                results.append(OverconfidenceMatch(
                    matched=match.group(0),
                    pattern_type="outcome_attribution",
                    suggestion="Trace which component caused outcome. Context ≠ causation",
                    severity="flag"
                ))

        # Collect all structural assessment matches
        # Only collect if NO evidence marker AND no comparison tool events
        for pattern in _STRUCTURAL_ASSESSMENT_PATTERNS:
            for match in pattern.finditer(text):
                if not (tool_events and _has_comparison_evidence(tool_events, text)):
                    results.append(OverconfidenceMatch(
                        matched=match.group(0),
                        pattern_type="structural_assessment",
                        suggestion="Add quantification or [Tier X] evidence",
                        severity="flag"
                    ))

    return results


# === Inline tests (run with: python -m anti_sycophancy.overconfidence_detector) ===
if __name__ == "__main__":
    # Should detect (overconfident)
    assert detect_overconfidence("This explains why the tests failed") is not None
    assert detect_overconfidence("The system is broken") is not None
    assert detect_overconfidence("The root cause is the missing import") is not None
    assert detect_overconfidence("This is why the API returns errors") is not None
    assert detect_overconfidence("Due to this, everything fails") is not None
    assert detect_overconfidence("The code completely fails under load") is not None

    # Outcome attribution tests (post-hoc causation)
    assert detect_overconfidence("The hook correctly blocked the command") is not None
    assert detect_overconfidence("This was handled by the validator") is not None
    assert detect_overconfidence("The gate successfully prevented execution") is not None
    assert detect_overconfidence("blocked by the safety hook") is not None
    assert detect_overconfidence("The TDD hook caught the violation") is None

    # Should pass (has evidence or acceptable)
    assert detect_overconfidence("[Tier 1]: This explains the failure") is None
    assert detect_overconfidence("Verified: The root cause is X") is None
    assert detect_overconfidence("Test output shows this is why it fails") is None
    assert detect_overconfidence("The import statement is missing") is None  # No causal claim
    assert detect_overconfidence("I need to investigate further") is None
    assert detect_overconfidence("") is None
    # Evidence markers make outcome attribution acceptable
    assert detect_overconfidence("Logs show: The hook correctly blocked it") is None
    assert detect_overconfidence("[Tier 1]: blocked by the safety hook") is None

    # Pattern type checks
    causal = detect_overconfidence("This explains the error")
    assert causal and causal.pattern_type == "causal_assertion"

    catastrophe = detect_overconfidence("The entire system is broken")
    assert catastrophe and catastrophe.pattern_type == "catastrophizing"

    attribution = detect_overconfidence("The root cause is the config")
    assert attribution and attribution.pattern_type == "unverified_attribution"

    outcome = detect_overconfidence("The hook correctly blocked the command")
    assert outcome and outcome.pattern_type == "outcome_attribution"

    # Multi-detection
    multi_text = "This explains why the system is broken. The root cause is X."
    all_matches = detect_all_overconfidence(multi_text)
    assert len(all_matches) >= 3, f"Expected 3+ matches, got {len(all_matches)}"

    # Multi-detection with outcome attribution
    multi_outcome = "The hook correctly blocked this. It was handled by the validator."
    outcome_matches = detect_all_overconfidence(multi_outcome)
    assert len(outcome_matches) >= 2, f"Expected 2+ outcome matches, got {len(outcome_matches)}"

    # Structural assessment — should detect
    structural = detect_overconfidence("Optimal structure, one intentional exception.")
    assert structural is not None, "Structural claim without evidence should be flagged"
    assert structural.pattern_type == "structural_assessment", f"Expected structural_assessment, got {structural.pattern_type}"
    assert structural.severity == "flag"

    # Structural variants — all should detect
    assert detect_overconfidence("That's a deliberate pattern, not an error.") is not None
    assert detect_overconfidence("This is intentional design.") is not None
    assert detect_overconfidence("Correct by design — it's optimal.") is not None
    assert detect_overconfidence("The proper structure is correct — here's why:") is not None

    # Structural with evidence — substring markers (should pass/allow)
    assert detect_overconfidence("[Tier 1]: intentional exception per ADR-002") is None
    assert detect_overconfidence("Compared against all 36 peers: optimal structure.") is None
    assert detect_overconfidence("compared across all skills: optimal structure") is None
    assert detect_overconfidence("verified across 37 packages: optimal structure") is None

    # Structural with evidence — regex count patterns (should pass/allow)
    assert detect_overconfidence("After reviewing 36 files: optimal structure.") is None
    assert detect_overconfidence("Checked 12 instances — intentional design.") is None
    assert detect_overconfidence("Enumerated all skills: deliberate exception here.") is None
    assert detect_overconfidence("I reviewed 37 skills — optimal structure.") is None
    assert detect_overconfidence("Examined 24 cases: intentional pattern.") is None
    assert detect_overconfidence("after reviewing all 36 peers") is None

    # I don't know — should pass (no confident claim)
    assert detect_overconfidence("I don't know if this is intentional.") is None

    print("✅ All tests passed")
