#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

# Import auto-logging decorator
from __lib.hook_base import hook_main

# Add hooks directory to path BEFORE importing local modules
_hooks_dir = Path(__file__).resolve().parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

try:
    from session_file_cache import SessionFileCache

    _session_cache = SessionFileCache()
except ImportError as e:
    # Fallback: disable caching if module unavailable
    _session_cache = None
    import logging

    logging.warning(f"SessionFileCache unavailable: {e}")

# Import block_protocol for correct Stop hook output format
try:
    from block_protocol import allow_response, block_response

    BLOCK_PROTOCOL_AVAILABLE = True
except ImportError:
    BLOCK_PROTOCOL_AVAILABLE = False

"""
Constitutional Enforcer Hook v2.1 - Unified Stop Event Validation
================================================================

Consolidates rule validation from multiple Stop hooks into a single
source of truth with clear violation attribution.

Replaces:
- constitution_guard.py (FORBIDDEN rules from CLAUDE.md)
- response_quality_gate.py (TRUTH rules: sycophancy, excuse patterns)
- success_validator.py (SUCCESS rules: hyperbole, scope inflation)

Categories:
- FORBIDDEN: Enterprise patterns, background services, autonomous execution
- TRUTH: Sycophancy, excuse patterns, belief without evidence
- SUCCESS: Hyperbole, scope inflation, unverified claims
- EVIDENCE: Weak evidence patterns, premature conclusions, unverified assumptions

Enhanced with:
- PII Scanner: Detects credentials and personal data leakage
- Reflexion Validator: Multi-round validation to reduce false positives
- Hallucination Scanner: Detects ungrounded claims
- Intent Drift Scanner: Validates actions stay aligned with goals
- Weak Evidence Detector: Catches confident conclusions from insufficient evidence

Performance target: <3s total (vs 23s for 5 separate hooks)

Author: CSF NIP
Version: 2.4.0 (Migrated to block_protocol.py for correct Stop hook format)
"""

import json
import os
import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

hooks_dir = Path(__file__).resolve().parent

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

try:
    from cc_diagnostic_logger import log as hook_log
except ImportError:

    def hook_log(*args, **kwargs):
        pass


# =============================================================================
# NEW: Scanner imports
# =============================================================================

try:
    from scanners import (
        AgreementConsistencyScanner,
        HallucinationScanner,
        IntentDriftScanner,
        PIIScanner,
        ReflexionValidator,
    )

    SCANNERS_AVAILABLE = True
except ImportError:
    SCANNERS_AVAILABLE = False
    PIIScanner = None
    ReflexionValidator = None
    HallucinationScanner = None
    IntentDriftScanner = None
    AgreementConsistencyScanner = None

# =============================================================================
# CONFIGURATION
# =============================================================================

ENABLED = os.environ.get("CONSTITUTIONAL_ENFORCER_ENABLED", "true").lower() == "true"

# Individual category controls
FORBIDDEN_ENABLED = os.environ.get("ENFORCER_FORBIDDEN", "true").lower() == "true"
TRUTH_ENABLED = os.environ.get("ENFORCER_TRUTH", "true").lower() == "true"
SUCCESS_ENABLED = os.environ.get("ENFORCER_SUCCESS", "true").lower() == "true"
EVIDENCE_ENABLED = os.environ.get("ENFORCER_EVIDENCE", "true").lower() == "true"
COMMITMENT_ENABLED = (
    os.environ.get("ENFORCER_COMMITMENT", "true").lower() == "true"
)  # NEW: v2.2

# NEW: Scanner controls (Phase 2 enhancements)
PII_SCANNER_ENABLED = os.environ.get("PII_SCANNER_ENABLED", "true").lower() == "true"
REFLEXION_VALIDATOR_ENABLED = (
    os.environ.get("REFLEXION_VALIDATOR_ENABLED", "true").lower() == "true"
)
HALLUCINATION_SCANNER_ENABLED = (
    os.environ.get("HALLUCINATION_SCANNER_ENABLED", "true").lower() == "true"
)
INTENT_DRIFT_SCANNER_ENABLED = (
    os.environ.get("INTENT_DRIFT_SCANNER_ENABLED", "false").lower() == "true"
)  # Off by default
AGREEMENT_CONSISTENCY_SCANNER_ENABLED = (
    os.environ.get("AGREEMENT_CONSISTENCY_SCANNER_ENABLED", "true").lower() == "true"
)


# =============================================================================
# DATA STRUCTURES
# =============================================================================


class Severity(Enum):
    """Violation severity levels."""

    HIGH = "HIGH"  # Blocks response
    MEDIUM = "MEDIUM"  # Warning only
    LOW = "LOW"  # Informational


class RuleCategory(Enum):
    """Rule categories for clear attribution."""

    FORBIDDEN = "FORBIDDEN"  # Part C.1 prohibitions
    TRUTH = "TRUTH"  # Part C: sycophancy, excuses
    SUCCESS = "SUCCESS"  # Part L: hyperbole, scope inflation
    EVIDENCE = "EVIDENCE"  # Weak evidence, premature conclusions
    COMMITMENT = "COMMITMENT"  # Commitment pattern: explicit YES/NO with evidence


@dataclass
class Violation:
    """A detected constitutional violation."""

    rule_id: str
    category: RuleCategory
    severity: Severity
    source_section: str
    matched_text: str
    message: str
    guidance: str


# =============================================================================
# RULE DEFINITIONS
# =============================================================================

# 1. FORBIDDEN RULES (Part C.1)
# These use constitution_cache.py for authoritative rules from CLAUDE.md

# Try to import constitution_cache for authoritative FORBIDDEN rules
try:
    from constitution_cache import ConstitutionalRule, load_constitution

    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    ConstitutionalRule = None

# Fallback FORBIDDEN patterns if cache unavailable
FALLBACK_FORBIDDEN_PATTERNS = [
    # Background services
    (
        r"background.*(?:service|process|task|job)",
        "FORBIDDEN-001",
        "Background service pattern",
    ),
    (
        r"daemon|persistent.*process|always.*running",
        "FORBIDDEN-002",
        "Persistent process pattern",
    ),
    (r"health.*(?:monitor|check|status)", "FORBIDDEN-003", "Health monitoring pattern"),
    (r"continuous.*monitoring", "FORBIDDEN-004", "Continuous monitoring pattern"),
    # Autonomous execution
    (
        r"self.?healing|auto.?correct|autonomous.*fix",
        "FORBIDDEN-005",
        "Autonomous execution pattern",
    ),
    (
        r"automatic.*(?:remediat|fix|repair)",
        "FORBIDDEN-006",
        "Automatic remediation pattern",
    ),
    # Enterprise patterns
    (r"dependency.?injection|DI.?container", "FORBIDDEN-007", "Enterprise DI pattern"),
    (
        r"abstract.?factory|factory.?pattern",
        "FORBIDDEN-008",
        "Enterprise factory pattern",
    ),
    (r"plugin.?system|extension.?system", "FORBIDDEN-009", "Enterprise plugin pattern"),
    # Required consensus
    (
        r"(?:team|stakeholder).*(?:approval|consensus|review)",
        "FORBIDDEN-010",
        "Required consensus pattern",
    ),
    (r"mandatory.*review.*process", "FORBIDDEN-011", "Mandatory review pattern"),
    (r"cross.?team.*coordination", "FORBIDDEN-012", "Cross-team coordination pattern"),
]


# 2. TRUTH RULES (Part C)
# Sycophancy detection via structural analysis (v2.4 - replaces brittle regex)

# Word sets for structural sycophancy detection
# These are checked against the FIRST SENTENCE only
AGREEMENT_SIGNALS = {
    "right",
    "correct",
    "exactly",
    "absolutely",
    "definitely",
    "agree",
    "certainly",
    "precisely",
    "indeed",
    "true",
    "yes",
    "totally",
    "completely",
}

PRAISE_SIGNALS = {
    "great",
    "excellent",
    "wonderful",
    "perfect",
    "good",
    "fantastic",
    "brilliant",
    "insightful",
    "smart",
    "clever",
    "amazing",
    "awesome",
    "outstanding",
    "superb",
}

# Phrases that indicate praise (checked as substrings, not just words)
PRAISE_PHRASES = [
    "great question",
    "great point",
    "great observation",
    "great catch",
    "excellent question",
    "excellent point",
    "excellent observation",
    "good question",
    "good point",
    "good catch",
    "that's a great",
    "that's an excellent",
    "that's a good",
    "wonderful idea",
    "perfect solution",
    "brilliant insight",
]

# Evidence/analysis signals that LEGITIMIZE agreement in the same sentence
EVIDENCE_SIGNALS = {
    "because",
    "since",
    "given",
    "considering",
    "however",
    "but",
    "although",
    "specifically",
    "evidence",
    "shows",
    "demonstrates",
    "indicates",
    "suggests",
    "according",
    "analysis",
    "looking",
    "examining",
    "reviewing",
    "based",
}

# Capitulation without explanation (anywhere in response)
CAPITULATION_PATTERNS = [
    (
        r"\bi\s+(?:was|am)\s+(?:wrong|mistaken)\s+(?:about\s+)?that(?!\s+(?:because|since|as|given|,\s*(?:because|since)))",
        "TRUTH-004",
        "Admits error without explanation",
    ),
    (
        r"\byou(?:'re|\s+are)\s+(?:totally|completely|absolutely)\s+right(?!\s+(?:that|about|,\s*(?:and|but)))",
        "TRUTH-005",
        "Complete capitulation without analysis",
    ),
]

EXCUSE_PATTERNS = [
    # Temporal
    (
        r"\b(?:evolving|timing\s+mismatch|moving\s+target|in\s+flux)\b",
        "TRUTH-005",
        "Temporal excuse",
    ),
    # Environmental
    (
        r"\b(?:works?\s+locally|on\s+my\s+machine|environment-?specific)\b",
        "TRUTH-006",
        "Environmental excuse",
    ),
    # Probabilistic
    (
        r"\b(?:should\s+work|ought\s+to|expected\s+to|supposed\s+to)\b",
        "TRUTH-007",
        "Probabilistic hedging",
    ),
    # Belief without evidence (but allow "I believe X because Y")
    (
        r"\b(?:i\s+believe|i\s+think|probably|most\s+likely)\b(?!\s+(?:because|since|as|given))",
        "TRUTH-008",
        "Belief without evidence",
    ),
]

# Deflection/Dismissal patterns (NEW - Issue 2)
# Detects patterns like "I don't have context, so I can't assess. Proceeding..."
DEFLECTION_DISMISSAL_PATTERNS = [
    (
        r"\b(?:i\s+don't|i\s+do\s+not|no)\s+(?:have|have\s+enough|have\s+sufficient)\s+context(?!\s+(?:so\s+let\s+me|,\s+so\s+i'll|,\s+letting\s+me))",
        "TRUTH-009",
        "Deflection: No context claim without investigation",
    ),
    (
        r"\bcan't\s+(?:assess|determine|verify)(?!\s+(?:without|because|due\s+to|as|since))",
        "TRUTH-010",
        "Deflection: Can't assess without explaining why",
    ),
    (
        r"\bunable\s+to\s+(?:verify|confirm|assess)(?!\s+(?:without|due\s+to|because))",
        "TRUTH-011",
        "Deflection: Unable to verify without exploration",
    ),
    (
        r"\bnot\s+able\s+to\s+(?:determine|assess|verify)(?!\s+(?:without|so|because))",
        "TRUTH-012",
        "Deflection: Not able to determine without follow-up",
    ),
    (
        r"\b(?:i\s+don't|i\s+do\s+not)\s+have\s+(?:the\s+)?(?:context|info|information)(?!\s+(?:so|,|letting))",
        "TRUTH-013",
        "Deflection: Missing info claim without action",
    ),
]


# 3. SUCCESS RULES (Part L)
# Hyperbole and scope inflation patterns

SUCCESS_EMOJI_PATTERNS = [r"✅", r"🎉", r"🚀", r"✓", r"\[x\]"]

SUCCESS_KEYWORDS = [
    r"\bfixed\b",
    r"\bworking\b",
    r"\bsuccess(?:ful|fully)?\b",
    r"\bcompleted?\b",
    r"\bresolved\b",
    r"\brestored\b",
    r"\bdone\b",
    r"\bpassing\b",
]

SCOPE_INFLATION_PATTERNS = [
    (
        r"\b(?:all|both)\s+(?:issues?|problems?|errors?)\s+(?:fixed|resolved)",
        "SUCCESS-001",
        "Scope inflation: all/both claims",
    ),
    (
        r"\bfully\s+(?:fixed|working|restored)",
        "SUCCESS-002",
        "Scope inflation: fully claims",
    ),
    (
        r"\b(?:massive|complete|full)\s+success",
        "SUCCESS-003",
        "Scope inflation: massive success",
    ),
    (
        r"\bpipeline\s+(?:fixed|working|restored)",
        "SUCCESS-004",
        "Scope inflation: pipeline claims",
    ),
    (
        r"\beverything\s+(?:works?|fixed)",
        "SUCCESS-005",
        "Scope inflation: everything claims",
    ),
]

HYPERBOLE_PATTERNS = [
    (r"MASSIVE\s+SUCCESS", "SUCCESS-006", "Hyperbolic success claim"),
    (r"🎉.*SUCCESS", "SUCCESS-007", "Emoji + success hyperbole"),
    (r"PERFECT(?:LY)?\s+(?:WORKING|FIXED)", "SUCCESS-008", "Perfectly working claim"),
]

EVIDENCE_PATTERNS = [
    r"```(?:bash|shell|console|output)?\n.*?```",  # Code blocks with output
    r"\$\s+\w+.*\n",  # Command line with output
    r">>>.*\n",  # Python REPL
    r"Output:\s*\n",  # Explicit output section
    r"Result:\s*\n",
    r"pytest.*(?:passed|failed)",  # Test output
]

STRONG_EVIDENCE_PATTERNS = [
    r"python\s+-[cm]\s+[\"']?(?:import|from)",  # Import test
    r"pytest\s+",  # Test execution
    r"--help\b",  # CLI verification
    r"curl\s+",  # API test
    r"git\s+(?:status|diff|log)",  # Git verification
]


# 4. WEAK EVIDENCE RULES (NEW)
# Patterns that indicate confident conclusions from insufficient evidence

# Unverified numeric claims (NEW - Issue 6)
UNVERIFIED_NUMERIC_CLAIM_PATTERNS = [
    (
        r"[+-]?\d+\s+(?:lines?|files?)",
        "EVIDENCE-NUM-001",
        "Line/file count claim without evidence",
    ),
    (
        r"\b\d+\s+additions?",
        "EVIDENCE-NUM-002",
        "Additions claim without git diff",
    ),
    (
        r"\b\d+\s+deletions?",
        "EVIDENCE-NUM-003",
        "Deletions claim without git diff",
    ),
    (
        r"\b[+-]?\d+(?:\.\d+)?\s*(?:%|percent)",
        "EVIDENCE-NUM-004",
        "Percentage claim without benchmark",
    ),
    (
        r"\b\d+(?:\.\d+)?\s*(?:ms|seconds?|minutes?)",
        "EVIDENCE-NUM-005",
        "Performance/time claim without measurement",
    ),
]

# Evidence patterns for numeric claims (git output, benchmarks, etc.)
NUMERIC_EVIDENCE_PATTERNS = [
    r"git\s+diff\s+.*\n",  # Git diff output
    r"```\n.*?\+\d+.*?\n.*?-\d+",  # Diff style in code block
    r"Benchmark|benchmarking|profiling",
    r"pytest\s+.*\n.*\d+\s+passed",  # Test counts
    r"(?:file|files?)\s+found:\s*\d+",  # Search results
]


# 4. WEAK EVIDENCE RULES (NEW)
# Patterns that indicate confident conclusions from insufficient evidence

ABSENCE_CLAIM_PATTERNS = [
    # Claims that something is missing/lost without verification
    (
        r"\b(?:was|were|got)\s+(?:lost|removed|deleted)",
        "EVIDENCE-001",
        "Claim of loss without verification",
    ),
    (
        r"\bcode\s+(?:was|is)\s+(?:lost|removed|gone)",
        "EVIDENCE-002",
        "Claim code was lost",
    ),
    (
        r"\b(?:doesn't|does\s+not|don't)\s+exist",
        "EVIDENCE-003",
        "Claim of non-existence",
    ),
    (
        r"\b(?:no\s+longer|not\s+(?:there|present|available))",
        "EVIDENCE-004",
        "Claim of absence",
    ),
    (
        r"\b(?:missing|disappeared|vanished)",
        "EVIDENCE-005",
        "Claim something is missing",
    ),
    (
        r"\bwasn't\s+(?:saved|applied|written)",
        "EVIDENCE-006",
        "Claim change wasn't saved",
    ),
]

PREMATURE_CONCLUSION_PATTERNS = [
    # Conclusions from single failed attempt
    (
        r"(?:the|my)\s+(?:fix|change|edit)(?:es)?\s+didn't\s+(?:take\s+effect|apply|work)",
        "EVIDENCE-007",
        "Concluded fix didn't work without verification",
    ),
    (
        r"\bdidn't\s+(?:work|help|fix)",
        "EVIDENCE-008",
        "Single attempt failure conclusion",
    ),
    (
        r"\b(?:still|keeps?)\s+(?:failing|broken|not\s+working)",
        "EVIDENCE-009",
        "Persistent failure claim without cause analysis",
    ),
]

UNVERIFIED_PATH_PATTERNS = [
    # Path assumptions that should be verified
    (
        r"(?:wrong|incorrect|bad)\s+(?:path|directory|location)",
        "EVIDENCE-010",
        "Path claim without showing correct path",
    ),
    (
        r"(?:pointed|pointing)\s+to\s+(?:a\s+)?(?:different|wrong)",
        "EVIDENCE-011",
        "Wrong pointer claim",
    ),
]

# Patterns that MITIGATE weak evidence violations (show verification was done)
VERIFICATION_EVIDENCE = [
    r"let\s+me\s+(?:check|verify|confirm|read)",
    r"reading\s+(?:the\s+)?(?:file|source|code)",
    r"checking\s+(?:the\s+)?(?:actual|source)",
    r"cat\s+[\"']?[^\s]+",  # cat command
    r"head\s+-?\d*\s+[\"']?[^\s]+",  # head command
    r"grep\s+",  # grep search
    r"git\s+(?:show|log|diff)",  # git history check
    r"```\n.*(?:class|def|function|import).*\n```",  # Actual code shown
    r"Found\s+\d+\s+(?:result|match|line)",  # Search results
]

ALTERNATIVE_ATTEMPT_EVIDENCE = [
    r"(?:let\s+me\s+)?try(?:ing)?\s+(?:a\s+)?(?:different|another|alternative)",
    r"(?:instead|alternatively),?\s+(?:let's|I'll|we\s+(?:can|could))",
    r"(?:different|broader|narrower)\s+(?:search|query|pattern)",
]


# =============================================================================
# VALIDATORS
# =============================================================================


class ForbiddenValidator:
    """Validates against FORBIDDEN rules (Part C.1)."""

    def __init__(self):
        self.rules = []
        self._load_rules()

    def _load_rules(self):
        """Load rules from constitution cache or fallback patterns."""
        if CACHE_AVAILABLE:
            try:
                constitution = load_constitution()
                self.rules = constitution["by_type"].get("FORBIDDEN", [])
            except Exception:
                self.rules = []

    def validate(self, response: str) -> list[Violation]:
        """Check response against FORBIDDEN rules."""
        if not FORBIDDEN_ENABLED:
            return []

        violations = []
        response_lower = response.lower()

        # ALWAYS check fallback patterns (they cover general patterns not in cache)
        for pattern, rule_id, description in FALLBACK_FORBIDDEN_PATTERNS:
            if re.search(pattern, response_lower, re.IGNORECASE):
                violations.append(
                    Violation(
                        rule_id=rule_id,
                        category=RuleCategory.FORBIDDEN,
                        severity=Severity.HIGH,
                        source_section="Part C.1",
                        matched_text=pattern,
                        message=description,
                        guidance="Replace with direct execution pattern suitable for singular dev environment.",
                    )
                )

        # Also check cached rules for specific violations
        if self.rules:
            for rule in self.rules:
                phrases = self._extract_phrases(rule.content)
                for phrase in phrases:
                    # Use word boundary matching to avoid false positives
                    pattern = r"\b" + re.escape(phrase) + r"\b"
                    if re.search(pattern, response_lower, re.IGNORECASE):
                        # Check if not already caught by fallback
                        if not any(v.rule_id == rule_id for v in violations):
                            violations.append(
                                Violation(
                                    rule_id=f"FORBIDDEN-{hash(rule.content) % 1000:03d}",
                                    category=RuleCategory.FORBIDDEN,
                                    severity=Severity.HIGH,
                                    source_section="Part C.1",
                                    matched_text=phrase,
                                    message=f"Prohibited pattern: {rule.content}",
                                    guidance="This pattern violates singular dev authority. Use direct execution instead.",
                                )
                            )
                        break

        return violations

    def _extract_phrases(self, rule: str) -> list[str]:
        """Extract only meaningful multi-word phrases from a rule."""
        phrases = []

        # Extract quoted phrases first - these are the most reliable
        for match in re.finditer(r'"([^"]{6,})"', rule):
            phrase = match.group(1).lower().strip()
            if len(phrase.split()) >= 2:
                phrases.append(phrase)

        if phrases:
            return phrases

        # Only extract 3-word phrases (more specific, less false positives)
        words = re.findall(r"\b[a-z][a-z0-9_]{2,}\b", rule.lower())

        for i in range(len(words) - 2):
            three_word = f"{words[i]} {words[i+1]} {words[i+2]}"
            if three_word not in {
                "the user to",
                "to the user",
                "in the system",
                "of the system",
                "for the user",
                "with the user",
                "from the user",
                "is not to",
            }:
                phrases.append(three_word)

        return phrases


class TruthValidator:
    """
    Validates against TRUTH rules (Part C) using structural analysis.

    v2.4: Replaced brittle regex patterns with word-set based detection.

    Detection logic:
    1. Extract first sentence (where sycophancy manifests)
    2. Check for agreement/praise signals
    3. If found, check if SAME sentence contains evidence/analysis signals
    4. Praise/agreement WITHOUT evidence in opener = sycophantic

    This catches paraphrases and novel constructions that regex misses.
    """

    def _extract_first_sentence(self, text: str) -> str:
        """
        Extract first meaningful sentence, handling markdown/formatting.

        Skips:
        - Markdown headers (#)
        - Code blocks (```)
        - Blank lines
        - Tool output markers
        """
        lines = text.strip().split("\n")
        for line in lines:
            line = line.strip()
            # Skip empty, headers, code blocks, tool markers
            if not line:
                continue
            if line.startswith("#") or line.startswith("```"):
                continue
            if line.startswith("⎿") or line.startswith(">"):
                continue

            # Find sentence boundary
            for end in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
                if end.strip() in line:
                    idx = line.index(end.strip())
                    return line[: idx + 1]

            # No boundary found - return first 200 chars
            return line[:200]

        return text[:200]

    def _tokenize(self, text: str) -> set[str]:
        """Extract words from text, lowercased."""
        # Remove punctuation and split
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return set(cleaned.split())

    def _check_sycophancy(self, response: str) -> Violation | None:
        """
        Structural sycophancy detection.

        Returns Violation if opener contains praise/agreement without evidence.
        """
        first_sentence = self._extract_first_sentence(response)
        first_lower = first_sentence.lower()
        words = self._tokenize(first_sentence)

        # Check for praise phrases first (more specific)
        has_praise_phrase = any(phrase in first_lower for phrase in PRAISE_PHRASES)

        # Check for agreement/praise signal words
        has_agreement = bool(words & AGREEMENT_SIGNALS)
        has_praise = bool(words & PRAISE_SIGNALS)

        # Check for evidence/analysis signals that legitimize agreement
        has_evidence = bool(words & EVIDENCE_SIGNALS)

        # Sycophancy = (praise phrase OR praise/agreement words) WITHOUT evidence
        if has_praise_phrase:
            matched = next(
                (p for p in PRAISE_PHRASES if p in first_lower), "praise phrase"
            )
            return Violation(
                rule_id="TRUTH-001",
                category=RuleCategory.TRUTH,
                severity=Severity.HIGH,
                source_section="Part A",
                matched_text=first_sentence[:60],
                message=f"Opens with sycophantic phrase: '{matched}'",
                guidance="Start with analysis, not praise. State your position with evidence.",
            )

        if (has_agreement or has_praise) and not has_evidence:
            signal_word = (words & AGREEMENT_SIGNALS) or (words & PRAISE_SIGNALS)
            signal = signal_word.pop() if signal_word else "agreement"
            return Violation(
                rule_id="TRUTH-002",
                category=RuleCategory.TRUTH,
                severity=Severity.HIGH,
                source_section="Part A",
                matched_text=first_sentence[:60],
                message=f"Opens with '{signal}' without supporting analysis",
                guidance="Before agreeing, provide analysis. Use 'because', 'however', or show evidence.",
            )

        return None

    def _check_capitulation(self, response: str) -> Violation | None:
        """Check for wholesale capitulation patterns anywhere in response."""
        response_lower = response.lower()

        for pattern, rule_id, description in CAPITULATION_PATTERNS:
            match = re.search(pattern, response_lower, re.IGNORECASE)
            if match:
                matched_text = response[match.start() : match.end()]
                return Violation(
                    rule_id=rule_id,
                    category=RuleCategory.TRUTH,
                    severity=Severity.HIGH,
                    source_section="Part A",
                    matched_text=matched_text[:60],
                    message=description,
                    guidance="When changing position, explain WHY with evidence.",
                )

        return None

    def _check_excuses(self, response: str) -> Violation | None:
        """Check for excuse patterns."""
        response_lower = response.lower()

        for pattern, rule_id, description in EXCUSE_PATTERNS:
            if re.search(pattern, response_lower, re.IGNORECASE):
                return Violation(
                    rule_id=rule_id,
                    category=RuleCategory.TRUTH,
                    severity=Severity.HIGH,
                    source_section="Part C",
                    matched_text=pattern,
                    message=description,
                    guidance="Replace hedging with concrete evidence or explicit uncertainty tagging.",
                )

        return None

    def _check_deflection_dismissal(self, response: str) -> Violation | None:
        """Check for deflection/dismissal patterns (NEW - Issue 2)."""
        response_lower = response.lower()

        for pattern, rule_id, description in DEFLECTION_DISMISSAL_PATTERNS:
            match = re.search(pattern, response_lower, re.IGNORECASE)
            if match:
                # Check if followed by "proceeding" or "moving on" without investigation
                full_context = response_lower[max(0, match.start() - 50):match.end() + 100]
                if any(phrase in full_context for phrase in [
                    "proceeding", "proceed", "moving on", "continuing",
                    "let's continue", "i'll proceed"
                ]):
                    matched_text = response[match.start() : match.end()]
                    return Violation(
                        rule_id=rule_id,
                        category=RuleCategory.TRUTH,
                        severity=Severity.MEDIUM,  # MEDIUM = warn
                        source_section="Part A",
                        matched_text=matched_text[:80],
                        message=f"Deflection detected: {description}",
                        guidance="You dismissed an unknown without investigating. REQUIRED: Read/Grep to establish context, ask user, or explicitly note limitation.",
                    )

        return None

    def validate(self, response: str) -> list[Violation]:
        """
        Check response against TRUTH rules.

        Order of checks:
        1. Sycophancy (opener praise/agreement without evidence)
        2. Capitulation (wholesale agreement change without explanation)
        3. Excuse patterns (probabilistic hedging)
        4. Deflection/dismissal (NEW - Issue 2)
        """
        if not TRUTH_ENABLED:
            return []

        violations = []

        # 1. Check sycophancy in opener
        syco_violation = self._check_sycophancy(response)
        if syco_violation:
            # Log for observability
            hook_log(
                "truth_validator",
                "sycophancy_detected",
                {
                    "rule_id": syco_violation.rule_id,
                    "matched": syco_violation.matched_text[:50],
                },
            )
            violations.append(syco_violation)
            return violations  # Early exit - sycophancy is blocking

        # 2. Check capitulation patterns
        cap_violation = self._check_capitulation(response)
        if cap_violation:
            hook_log(
                "truth_validator",
                "capitulation_detected",
                {
                    "rule_id": cap_violation.rule_id,
                },
            )
            violations.append(cap_violation)
            return violations

        # 3. Check excuse patterns
        excuse_violation = self._check_excuses(response)
        if excuse_violation:
            hook_log(
                "truth_validator",
                "excuse_detected",
                {
                    "rule_id": excuse_violation.rule_id,
                },
            )
            violations.append(excuse_violation)

        # 4. Check deflection/dismissal patterns (NEW)
        deflection_violation = self._check_deflection_dismissal(response)
        if deflection_violation:
            hook_log(
                "truth_validator",
                "deflection_detected",
                {
                    "rule_id": deflection_violation.rule_id,
                },
            )
            violations.append(deflection_violation)
        if excuse_violation:
            hook_log(
                "truth_validator",
                "excuse_detected",
                {
                    "rule_id": excuse_violation.rule_id,
                },
            )
            violations.append(excuse_violation)

        return violations


class SuccessValidator:
    """Validates against SUCCESS rules (Part L)."""

    def validate(self, response: str) -> list[Violation]:
        """Check response against SUCCESS rules."""
        if not SUCCESS_ENABLED:
            return []

        violations = []
        lines = response.split("\n")

        # Check for hyperbolic patterns first
        for line in lines:
            for pattern, rule_id, description in HYPERBOLE_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(
                        Violation(
                            rule_id=rule_id,
                            category=RuleCategory.SUCCESS,
                            severity=Severity.HIGH,
                            source_section="Part L",
                            matched_text=line.strip()[:60],
                            message=description,
                            guidance="Reframe as specific, scoped progress with execution evidence.",
                        )
                    )
                    return violations

        # Check for scope inflation
        for i, line in enumerate(lines):
            for pattern, rule_id, description in SCOPE_INFLATION_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    has_evidence = self._check_evidence(lines, i)
                    if not has_evidence:
                        violations.append(
                            Violation(
                                rule_id=rule_id,
                                category=RuleCategory.SUCCESS,
                                severity=Severity.HIGH,
                                source_section="Part L",
                                matched_text=line.strip()[:60],
                                message=description,
                                guidance="Itemize each component's actual verified status.",
                            )
                        )
                        return violations

        # Check for multiple unverified emoji claims
        emoji_claims = 0
        for i, line in enumerate(lines):
            has_emoji = any(re.search(p, line) for p in SUCCESS_EMOJI_PATTERNS)
            has_keyword = any(
                re.search(p, line, re.IGNORECASE) for p in SUCCESS_KEYWORDS
            )

            if has_emoji and has_keyword:
                has_evidence = self._check_evidence(lines, i)
                if not has_evidence:
                    emoji_claims += 1

        if emoji_claims >= 3:
            violations.append(
                Violation(
                    rule_id="SUCCESS-009",
                    category=RuleCategory.SUCCESS,
                    severity=Severity.HIGH,
                    source_section="Part L",
                    matched_text=f"{emoji_claims} emoji claims",
                    message=f"Multiple success claims ({emoji_claims}) without evidence",
                    guidance="Show actual command output after each claim.",
                )
            )

        return violations

    def _check_evidence(self, lines: list[str], line_num: int) -> bool:
        """Check if there's evidence within 5 lines after the claim."""
        start = line_num
        end = min(len(lines), line_num + 6)
        context = "\n".join(lines[start:end])

        for pattern in STRONG_EVIDENCE_PATTERNS:
            if re.search(pattern, context, re.IGNORECASE | re.MULTILINE):
                return True

        for pattern in EVIDENCE_PATTERNS:
            if re.search(pattern, context, re.DOTALL):
                return True

        return False


class WeakEvidenceValidator:
    """
    Validates against WEAK EVIDENCE patterns (NEW in v2.1).

    Catches:
    - Claims of absence without verification ("was lost", "doesn't exist")
    - Confident conclusions from single failed attempts
    - Unverified path/state assumptions
    - Unverified numeric claims (NEW - Issue 6)

    General pattern: Confident conclusion + insufficient verification = violation
    """

    def _check_numeric_claim_within_range(self, response: str, match_start: int) -> bool:
        """Check if numeric claim has evidence within 5 lines."""
        lines = response.split("\n")
        line_num = response[:match_start].count("\n")

        # Check 5 lines before and after
        start = max(0, line_num - 5)
        end = min(len(lines), line_num + 6)
        context = "\n".join(lines[start:end])

        # Check for numeric evidence patterns
        for pattern in NUMERIC_EVIDENCE_PATTERNS:
            if re.search(pattern, context, re.IGNORECASE | re.MULTILINE):
                return True

        return False

    def validate(self, response: str, context: dict = None) -> list[Violation]:
        """Check response against weak evidence patterns."""
        if not EVIDENCE_ENABLED:
            return []

        violations = []
        response_lower = response.lower()

        # Check if response contains verification evidence (mitigates violations)
        has_verification = any(
            re.search(p, response_lower, re.IGNORECASE) for p in VERIFICATION_EVIDENCE
        )

        has_alternative_attempts = any(
            re.search(p, response_lower, re.IGNORECASE)
            for p in ALTERNATIVE_ATTEMPT_EVIDENCE
        )

        # 1. Check for absence claims without verification
        if not has_verification:
            for pattern, rule_id, description in ABSENCE_CLAIM_PATTERNS:
                match = re.search(pattern, response_lower, re.IGNORECASE)
                if match:
                    # Find the sentence containing the match for context
                    matched_text = self._extract_sentence(response, match.start())
                    violations.append(
                        Violation(
                            rule_id=rule_id,
                            category=RuleCategory.EVIDENCE,
                            severity=Severity.HIGH,
                            source_section="Evidence Standards",
                            matched_text=matched_text[:80],
                            message=f"Weak evidence: {description}",
                            guidance="Before claiming absence, READ the actual file/source. Try alternative search terms. Show verification evidence.",
                        )
                    )
                    return violations  # One violation is enough

        # 2. Check for premature conclusions without alternative attempts
        if not has_alternative_attempts and not has_verification:
            for pattern, rule_id, description in PREMATURE_CONCLUSION_PATTERNS:
                match = re.search(pattern, response_lower, re.IGNORECASE)
                if match:
                    matched_text = self._extract_sentence(response, match.start())
                    violations.append(
                        Violation(
                            rule_id=rule_id,
                            category=RuleCategory.EVIDENCE,
                            severity=Severity.MEDIUM,  # Medium because might be valid after attempts
                            source_section="Evidence Standards",
                            matched_text=matched_text[:80],
                            message=f"Premature conclusion: {description}",
                            guidance="Try different approaches before concluding failure. Verify with actual file reads.",
                        )
                    )
                    return violations

        # 3. Check for path claims without showing evidence
        for pattern, rule_id, description in UNVERIFIED_PATH_PATTERNS:
            match = re.search(pattern, response_lower, re.IGNORECASE)
            if match:
                # Check if the response shows the correct path
                has_path_evidence = re.search(
                    r"(?:correct|actual|right)\s+path\s*(?:is|:|=)\s*[\"'`]?[\w/\\\.]+",
                    response_lower,
                )
                if not has_path_evidence:
                    matched_text = self._extract_sentence(response, match.start())
                    violations.append(
                        Violation(
                            rule_id=rule_id,
                            category=RuleCategory.EVIDENCE,
                            severity=Severity.MEDIUM,
                            source_section="Evidence Standards",
                            matched_text=matched_text[:80],
                            message=f"Unverified claim: {description}",
                            guidance="Show the correct path/value alongside the incorrect one.",
                        )
                    )
                    return violations

        # 4. Check for unverified numeric claims (NEW - Issue 6)
        for pattern, rule_id, description in UNVERIFIED_NUMERIC_CLAIM_PATTERNS:
            match = re.search(pattern, response)
            if match:
                # Check if evidence is within range
                if not self._check_numeric_claim_within_range(response, match.start()):
                    matched_text = response[match.start():match.end()]
                    violations.append(
                        Violation(
                            rule_id=rule_id,
                            category=RuleCategory.EVIDENCE,
                            severity=Severity.MEDIUM,  # MEDIUM = warn
                            source_section="Evidence Standards",
                            matched_text=matched_text,
                            message=f"Unverified numeric claim: {description}",
                            guidance="Show actual command output (git diff, benchmark, ls) within 5 lines of the claim.",
                        )
                    )
                    return violations
                    matched_text = self._extract_sentence(response, match.start())
                    violations.append(
                        Violation(
                            rule_id=rule_id,
                            category=RuleCategory.EVIDENCE,
                            severity=Severity.MEDIUM,  # Medium because might be valid after attempts
                            source_section="Evidence Standards",
                            matched_text=matched_text[:80],
                            message=f"Premature conclusion: {description}",
                            guidance="Try different approaches before concluding failure. Verify with actual file reads.",
                        )
                    )
                    return violations

        # 3. Check for path claims without showing evidence
        for pattern, rule_id, description in UNVERIFIED_PATH_PATTERNS:
            match = re.search(pattern, response_lower, re.IGNORECASE)
            if match:
                # Check if the response shows the correct path
                has_path_evidence = re.search(
                    r"(?:correct|actual|right)\s+path\s*(?:is|:|=)\s*[\"'`]?[\w/\\\.]+",
                    response_lower,
                )
                if not has_path_evidence:
                    matched_text = self._extract_sentence(response, match.start())
                    violations.append(
                        Violation(
                            rule_id=rule_id,
                            category=RuleCategory.EVIDENCE,
                            severity=Severity.MEDIUM,
                            source_section="Evidence Standards",
                            matched_text=matched_text[:80],
                            message=f"Unverified claim: {description}",
                            guidance="Show the correct path/value alongside the incorrect one.",
                        )
                    )
                    return violations

        # 4. Check tool sequence for zero-result patterns (if context available)
        if context:
            tool_results = context.get("tool_results", [])
            recent_search_zero = self._check_zero_result_pattern(tool_results)

            if recent_search_zero and not has_verification:
                # Check if response makes confident claims about the search subject
                search_subject = recent_search_zero.get("search_term", "")
                if search_subject and search_subject.lower() in response_lower:
                    # Check for confident claims about the searched item
                    confident_patterns = [
                        rf"{re.escape(search_subject)}.*(?:doesn't|does\s+not|isn't|is\s+not)",
                        rf"(?:no|none|nothing).*{re.escape(search_subject)}",
                        rf"{re.escape(search_subject)}.*(?:lost|missing|gone|removed)",
                    ]
                    for cp in confident_patterns:
                        if re.search(cp, response_lower, re.IGNORECASE):
                            violations.append(
                                Violation(
                                    rule_id="EVIDENCE-020",
                                    category=RuleCategory.EVIDENCE,
                                    severity=Severity.HIGH,
                                    source_section="Evidence Standards",
                                    matched_text=f"Search for '{search_subject}' returned 0 results",
                                    message="Confident conclusion from zero search results",
                                    guidance="Zero results ≠ absence. Try broader search terms, READ the actual file, check git history.",
                                )
                            )
                            return violations

        return violations

    def _extract_sentence(self, text: str, position: int) -> str:
        """Extract the sentence containing the given position."""
        # Find sentence boundaries
        start = text.rfind(".", 0, position)
        start = start + 1 if start >= 0 else 0

        end = text.find(".", position)
        end = end + 1 if end >= 0 else len(text)

        sentence = text[start:end].strip()
        return sentence if sentence else text[max(0, position - 40) : position + 40]

    def _check_zero_result_pattern(self, tool_results: list) -> dict | None:
        """Check if recent tool results show a zero-result search pattern."""
        if not tool_results:
            return None

        # Look at last 3 tool results
        for result in reversed(tool_results[-3:]):
            tool_name = result.get("tool_name", "")
            output = str(result.get("output", ""))

            if tool_name in ("Search", "Grep", "Glob"):
                # Check for zero results
                if any(
                    marker in output.lower()
                    for marker in [
                        "found 0",
                        "no matches",
                        "no results",
                        "0 lines",
                        "0 files",
                        "nothing found",
                    ]
                ):
                    # Try to extract what was searched for
                    input_data = result.get("input", {})
                    search_term = input_data.get("pattern", input_data.get("query", ""))
                    return {
                        "tool": tool_name,
                        "search_term": search_term,
                        "output": output[:200],
                    }

        return None


# Commitment Validator (NEW in v2.2)
# =============================================


class CommitmentValidator:
    """
    Validates that commitment questions were answered when injected.

    When error_attribution_validator.py injects a commitment question,
    this validator ensures CC actually answered it before allowing
    external blame or premature conclusions.

    Pattern: External blame is ONLY allowed if commitment was fulfilled.
    """

    COMMITMENT_FLAG_FILE = hooks_dir / "session_data/commitment_pending.json"

    def __init__(self):
        self.had_error_injection = self._check_error_injection()
        self.error_context = self._get_error_context()

    def _check_error_injection(self) -> bool:
        """Check if error attribution hook injected a commitment question."""
        try:
            if not self.COMMITMENT_FLAG_FILE.exists():
                return False

            data = json.loads(self.COMMITMENT_FLAG_FILE.read_text(encoding="utf-8"))
            return data.get("pending", False)
        except Exception:
            return False

    def _get_error_context(self) -> dict:
        """Get context about what files were flagged."""
        try:
            if not self.COMMITMENT_FLAG_FILE.exists():
                return {}

            data = json.loads(self.COMMITMENT_FLAG_FILE.read_text(encoding="utf-8"))
            return {
                "error_type": data.get("error_type", ""),
                "files": data.get("files", []),
            }
        except Exception:
            return {}

    def _clear_flag(self):
        """Clear the commitment flag after validation."""
        try:
            if self.COMMITMENT_FLAG_FILE.exists():
                self.COMMITMENT_FLAG_FILE.unlink()
        except Exception:
            pass

    def validate(self, response: str, context: dict = None) -> list:
        """
        Validate response against commitment patterns.

        If a commitment was injected, checks:
        1. Did CC answer with explicit YES/NO and evidence?
        2. If not, does CC blame external factors anyway?
        """
        if not COMMITMENT_ENABLED:
            return []

        if not self.had_error_injection:
            return []  # No commitment was required, nothing to validate

        violations = []
        response_lower = response.lower()

        # Patterns that show CC fulfilled the commitment requirement
        bypass_patterns = [
            r"(?:YES|NO)\s*[-–:—]\s*.{10,}",  # "YES - I checked and..."
            r"(?:YES|NO)\s*,\s*.{10,}",  # "NO, because..."
            r"my (?:change|edit|modification).*(?:caused|didn't cause)",
            r"reading (?:the file|my change|what I wrote)",
            r"the code I (?:wrote|added|modified)",
            r"checked (?:the file|my code|the implementation)",
            r"let me (?:check|verify|read)",  # Shows intent to verify
            r"looking at (?:the|my) (?:code|change|file)",  # Verification behavior
        ]

        # Check if commitment was fulfilled
        commitment_fulfilled = False
        for pattern in bypass_patterns:
            if re.search(pattern, response_lower, re.IGNORECASE):
                commitment_fulfilled = True
                break

        if commitment_fulfilled:
            self._clear_flag()  # Clear flag on success
            return []  # CC answered the commitment, allow response

        # Commitment was NOT fulfilled - check for external blame patterns
        external_blame_patterns = [
            (
                r"git (?:checkout|reset|pull|revert).*(?:restored|overwrote|reverted)",
                "COMMITMENT-001",
            ),
            (
                r"(?:older|previous|different) version.*(?:doesn't have|missing)",
                "COMMITMENT-002",
            ),
            (
                r"file was (?:modified|changed|overwritten) (?:by|externally)",
                "COMMITMENT-003",
            ),
            (r"environment.*(?:different|changed|reset)", "COMMITMENT-004"),
            (r"python\s*.*cache", "COMMITMENT-005"),
            (r"(?:something|someone)\s+(?:else|external)", "COMMITMENT-006"),
        ]

        for pattern, rule_id in external_blame_patterns:
            if re.search(pattern, response_lower, re.IGNORECASE):
                files_str = (
                    ", ".join(self.error_context.get("files", [])[:3])
                    or "recent changes"
                )
                violations.append(
                    Violation(
                        rule_id=rule_id,
                        category=RuleCategory.COMMITMENT,
                        severity=Severity.HIGH,
                        source_section="Error Attribution",
                        matched_text=pattern,
                        message=f"External blame without answering commitment question about {files_str}",
                        guidance="Answer: Q: Did YOUR change cause this? [YES/NO] Evidence: [Quote your code]",
                    )
                )
                break  # One violation is enough

        # Clear flag after validation attempt (whether pass or fail)
        if violations:
            self._clear_flag()

        return violations


# =============================================================================
# NEW: Fabricated Verification Validator (v2.3)
# =============================================================================


class FabricatedVerificationValidator:
    """
    Detects checkmark tables and verification claims without execution evidence.

    Problem: CC generates nice-looking verification tables with ✅ checkmarks
    that LOOK like verification but have no actual execution behind them.

    Pattern detected:
    1. Table with checkmarks (✅, [x], ✓)
    2. Claims like "Verified working", "All X work", "should work"
    3. NO execution evidence (no bash output, no actual command results)

    Signal: "should work" (probabilistic hedging) + checkmarks = fabricated verification
    """

    # Patterns indicating verification CLAIMS (need evidence to back them up)
    VERIFICATION_CLAIM_PATTERNS = [
        (r"verified\s+working", "FABRICATION-001", "Claimed 'verified working'"),
        (
            r"all\s+(?:commands?|tests?|checks?)\s+(?:should\s+)?work",
            "FABRICATION-002",
            "Claimed all items work",
        ),
        (
            r"should\s+(?:work|pass|succeed)",
            "FABRICATION-003",
            "Probabilistic 'should work'",
        ),
        (
            r"(?:verified|confirmed|checked):\s*\n.*[✅✓\[x\]]",
            "FABRICATION-004",
            "Verification list with checkmarks",
        ),
        (
            r"\|\s*(?:Result|Status|Check)\s*\|.*\n.*[✅✓]",
            "FABRICATION-005",
            "Verification table with checkmarks",
        ),
    ]

    # Patterns indicating ACTUAL execution evidence
    EXECUTION_EVIDENCE_PATTERNS = [
        r"```(?:bash|shell|console|output)\n",  # Code block with execution
        r"\$\s+(?:python|pytest|npm|node|bash)",  # Command execution
        r">>>",  # Python REPL
        r"(?:PASSED|FAILED|ERROR)\s+[\w/]+\.py",  # Test output
        r"(?:exit code|returned|exited with)\s*:?\s*\d+",  # Exit codes
        r"(?:Running|Executing).*\n.*(?:Output|Result):",  # Actual execution
        r"Bash\(.*\)\s*\n\s*⎿",  # Claude Code tool output format
    ]

    # Count thresholds
    MIN_CHECKMARKS_WITHOUT_EVIDENCE = 3  # 3+ checkmarks without evidence = suspicious

    def validate(self, response: str, context: dict = None) -> list[Violation]:
        """Check for fabricated verification patterns."""
        violations = []
        response_lower = response.lower()

        # Check if response has execution evidence
        has_execution_evidence = any(
            re.search(p, response, re.IGNORECASE | re.MULTILINE)
            for p in self.EXECUTION_EVIDENCE_PATTERNS
        )

        # If we have execution evidence, likely not fabricated
        if has_execution_evidence:
            return []

        # Count checkmarks in response
        checkmark_count = len(re.findall(r"[✅✓]|\[x\]", response, re.IGNORECASE))

        # Check for verification claim patterns
        for pattern, rule_id, description in self.VERIFICATION_CLAIM_PATTERNS:
            if re.search(pattern, response_lower, re.IGNORECASE | re.MULTILINE):
                # Found a verification claim without execution evidence
                violations.append(
                    Violation(
                        rule_id=rule_id,
                        category=RuleCategory.EVIDENCE,
                        severity=Severity.HIGH,
                        source_section="Success Validation",
                        matched_text=pattern,
                        message=f"Fabricated verification: {description} without execution evidence",
                        guidance="EXECUTE the verification. Show actual command output, not just checkmarks.",
                    )
                )
                return violations  # One is enough

        # Check for checkmark overload without evidence
        if checkmark_count >= self.MIN_CHECKMARKS_WITHOUT_EVIDENCE:
            # Check if it's a table pattern
            has_table = bool(re.search(r"\|.*\|.*\n.*\|.*\|", response))
            if has_table:
                violations.append(
                    Violation(
                        rule_id="FABRICATION-006",
                        category=RuleCategory.EVIDENCE,
                        severity=Severity.HIGH,
                        source_section="Success Validation",
                        matched_text=f"{checkmark_count} checkmarks in table without execution",
                        message=f"Verification table with {checkmark_count} claims but no execution evidence",
                        guidance="Show actual execution output for each claim, not just checkmarks.",
                    )
                )

        return violations


# =============================================================================
# NEW: Scanner Validator (Phase 2 Enhancements)
# =============================================================================


class ScannerValidator:
    """
    Fast scanner validation layer.

    Runs Tier 1 scanners (<1ms each) before main validation.
    Based on patterns from LLM Guard, FACTSCORE, Reflexion, and Voyager.
    """

    def __init__(self):
        """Initialize scanners based on availability and configuration."""
        self.scanners = []

        if SCANNERS_AVAILABLE:
            if PII_SCANNER_ENABLED:
                try:
                    self.scanners.append(
                        ("PII", PIIScanner(enabled=True, exclude_low_severity=True))
                    )
                except Exception:
                    pass

            if HALLUCINATION_SCANNER_ENABLED:
                try:
                    self.scanners.append(
                        (
                            "Hallucination",
                            HallucinationScanner(enabled=True, strict_mode=False),
                        )
                    )
                except Exception:
                    pass

            if INTENT_DRIFT_SCANNER_ENABLED:
                try:
                    self.scanners.append(
                        ("IntentDrift", IntentDriftScanner(enabled=True, threshold=0.6))
                    )
                except Exception:
                    pass

            if AGREEMENT_CONSISTENCY_SCANNER_ENABLED:
                try:
                    self.scanners.append(
                        ("AgreementConsistency", AgreementConsistencyScanner(enabled=True))
                    )
                except Exception:
                    pass

        if SCANNERS_AVAILABLE and REFLEXION_VALIDATOR_ENABLED:
            try:
                self.reflexion_validator = ReflexionValidator(
                    enabled=True, max_rounds=2
                )
            except Exception:
                self.reflexion_validator = None
        else:
            self.reflexion_validator = None

    def validate_fast_scanners(self, response: str, context: dict = None) -> list[dict]:
        """Run all fast scanners."""
        violations = []

        for scanner_name, scanner in self.scanners:
            try:
                result = scanner.scan(response, context)
                if not result.is_valid():
                    violations.append(
                        {
                            "scanner": scanner_name,
                            "rule_id": f"SCANNER-{scanner_name}",
                            "category": "SCANNER",
                            "severity": result.severity,
                            "matched_text": result.matched_text,
                            "message": result.reason,
                            "guidance": result.suggestion,
                        }
                    )
            except Exception as e:
                _logger.warning("Scanner %s error: %s", scanner_name, e)

        return violations

    def validate_reflexion_rounds(
        self, response: str, context: dict = None
    ) -> list[dict]:
        """Run Reflexion multi-round validation."""
        if not self.reflexion_validator:
            return []

        try:
            result = self.reflexion_validator.scan(response, context)
            if not result.is_valid():
                return [
                    {
                        "scanner": "Reflexion",
                        "rule_id": f"SCANNER-Reflexion-R{result.status.value}",
                        "category": "REFLEXION",
                        "severity": result.severity,
                        "matched_text": result.matched_text,
                        "message": result.reason,
                        "guidance": result.suggestion,
                    }
                ]
        except Exception as e:
            _logger.warning("Reflexion validator error: %s", e)

        return []


# =============================================================================
# MAIN ENGINE
# =============================================================================


class ConstitutionalEnforcer:
    """Main validation engine combining all rule categories and scanners."""

    def __init__(self):
        self.forbidden_validator = ForbiddenValidator()
        self.truth_validator = TruthValidator()
        self.success_validator = SuccessValidator()
        self.evidence_validator = WeakEvidenceValidator()
        self.commitment_validator = CommitmentValidator()
        self.fabrication_validator = FabricatedVerificationValidator()
        self.scanner_validator = ScannerValidator()

    def validate(self, response: str, context: dict = None) -> tuple[bool, list]:
        """
        Validate response against all constitutional rules.

        6-Tier Validation Architecture:
        1. Fast Scanners (<1ms each) - PII, Hallucination, Intent Drift
        2. Reflexion Rounds (~100ms) - Multi-round oversight
        3. Constitutional Rules (~3s) - FORBIDDEN/TRUTH/SUCCESS
        4. Weak Evidence Detection - Claims without verification
        5. Commitment Validation (v2.2) - Error attribution accountability
        6. Fabricated Verification (v2.3) - Blocks fake checkmark tables

        Args:
            response: The response text to validate
            context: Optional context dict

        Returns:
            Tuple of (is_valid, violations)
        """
        violations = []

        # Tier 1: Fast scanners
        scanner_violations = self.scanner_validator.validate_fast_scanners(
            response, context
        )
        if scanner_violations:
            is_pii = any(v.get("scanner") == "PII" for v in scanner_violations)
            if is_pii:
                return False, scanner_violations
            violations.extend(scanner_violations)

        # Tier 2: Reflexion
        reflexion_violations = self.scanner_validator.validate_reflexion_rounds(
            response, context
        )
        if reflexion_violations:
            if any(v.get("severity") == "HIGH" for v in reflexion_violations):
                return False, violations + reflexion_violations
            violations.extend(reflexion_violations)

        # Tier 3: Constitutional rules (FORBIDDEN, TRUTH, SUCCESS)
        forbidden_violations = self.forbidden_validator.validate(response)
        if forbidden_violations:
            violations.extend(forbidden_violations)
            return False, violations

        truth_violations = self.truth_validator.validate(response)
        if truth_violations:
            violations.extend(truth_violations)
            return False, violations

        success_violations = self.success_validator.validate(response)
        if success_violations:
            violations.extend(success_violations)
            return False, violations

        # Tier 4: Weak evidence detection
        evidence_violations = self.evidence_validator.validate(response, context)
        if evidence_violations:
            # HIGH severity evidence violations block
            high_severity = [
                v for v in evidence_violations if v.severity == Severity.HIGH
            ]
            if high_severity:
                violations.extend(evidence_violations)
                return False, violations
            # MEDIUM severity just warns but doesn't block
            violations.extend(evidence_violations)

        # Tier 5: Commitment validation (NEW in v2.2)
        commitment_violations = self.commitment_validator.validate(response, context)
        if commitment_violations:
            # All commitment violations block
            violations.extend(commitment_violations)
            return False, violations

        # Tier 6: Fabricated verification detection (NEW in v2.3)
        fabrication_violations = self.fabrication_validator.validate(response, context)
        if fabrication_violations:
            # All fabrication violations block
            violations.extend(fabrication_violations)
            return False, violations

        # Final check for any HIGH severity violations (including dictionary-based scanner results)
        has_high_severity = False
        for v in violations:
            if isinstance(v, dict):
                if v.get("severity") == "HIGH" or v.get("severity") == Severity.HIGH:
                    has_high_severity = True
                    break
            elif isinstance(v, Violation):
                if v.severity == Severity.HIGH:
                    has_high_severity = True
                    break

        return not has_high_severity, violations

    def format_violations(self, violations: list) -> str:
        """Format violations for display."""
        if not violations:
            return ""

        lines = ["⛔ CONSTITUTIONAL VIOLATIONS DETECTED\n"]
        lines.append(f"Found {len(violations)} violation(s):\n")

        for i, v in enumerate(violations, 1):
            if isinstance(v, dict):
                category = v.get("category", "UNKNOWN")
                message = v.get("message", "")
                matched_text = v.get("matched_text", "")
                source = v.get("scanner", "Scanner")
                guidance = v.get("guidance", "")

                lines.append(f"{i}. [{category}] {message}")
                lines.append(f'   Matched: "{matched_text[:50]}..."')
                lines.append(f"   Source: {source}")
                lines.append(f"   Guidance: {guidance}")
            else:
                lines.append(f"{i}. [{v.category.value}] {v.message}")
                lines.append(f'   Matched: "{v.matched_text[:50]}..."')
                lines.append(f"   Source: {v.source_section}")
                lines.append(f"   Guidance: {v.guidance}")
            lines.append("")

        return "\n".join(lines)


# =============================================================================
# HOOK ENTRY POINT
# =============================================================================


def read_transcript_response(transcript_path: str) -> str:
    """Read the most recent assistant response from transcript."""
    try:
        transcript = Path(transcript_path)
        if not transcript.exists():
            return ""

        content = transcript.read_text(encoding="utf-8").strip()
        if not content:
            return ""

        lines = content.split("\n")

        for line in reversed(lines):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                if entry.get("role") == "assistant":
                    msg_content = entry.get("content", "")
                    if isinstance(msg_content, list):
                        text_parts = [
                            block.get("text", "")
                            for block in msg_content
                            if block.get("type") == "text"
                        ]
                        return " ".join(text_parts)
                    return str(msg_content)
            except json.JSONDecodeError:
                continue

        return ""
    except Exception:
        return ""


def load_tool_sequence() -> list[dict]:
    """Load recent tool calls from session tracking using thread-safe manager."""
    try:
        from tool_sequence_manager import load_tool_sequence as load_tools

        return load_tools()
    except Exception:
        return []


@hook_main
def main():
    """Main hook execution."""
    if not ENABLED:
        sys.exit(0)

    input_data = json.loads(sys.stdin.read())

    # Get response text
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        response = read_transcript_response(transcript_path)
    else:
        conversation = input_data.get("conversation", "") or input_data.get(
            "messages", ""
        )
        if isinstance(conversation, list):
            conversation = "\n".join([m.get("content", "") for m in conversation])
        response = str(conversation)

    if not response or len(response) < 20:
        sys.exit(0)

    # Build context including tool sequence for weak evidence detection
    tool_sequence = load_tool_sequence()

    # Convert tool sequence to tool_results format for evidence validator
    tool_results = []
    for tool in tool_sequence[-5:]:  # Last 5 tools
        tool_results.append(
            {
                "tool_name": tool.get("name", ""),
                "input": {
                    "pattern": tool.get("command", ""),
                    "query": tool.get("command", ""),
                },
                "output": tool.get("output", ""),
            }
        )

    context = {
        "prompt": input_data.get("prompt", ""),
        "primary_goal": input_data.get("primary_goal", input_data.get("goal", "")),
        "tools_used": input_data.get("tools_used", []),
        "mentioned_files": input_data.get("mentioned_files", []),
        "command_outputs": input_data.get("command_outputs", []),
        "test_results": input_data.get("test_results", []),
        "tool_results": tool_results,  # NEW: for weak evidence detection
    }

    # Validate
    enforcer = ConstitutionalEnforcer()
    is_valid, violations = enforcer.validate(response, context)

    # Format output
    formatted_violations = []
    for v in violations:
        if isinstance(v, dict):
            formatted_violations.append(
                {
                    "rule_id": v.get("rule_id", "SCANNER"),
                    "category": v.get("category", "SCANNER"),
                    "severity": v.get("severity", "MEDIUM"),
                    "source_section": v.get("scanner", "Scanner"),
                    "matched_text": v.get("matched_text", ""),
                    "message": v.get("message", ""),
                    "guidance": v.get("guidance", ""),
                }
            )
        else:
            formatted_violations.append(
                {
                    "rule_id": v.rule_id,
                    "category": v.category.value,
                    "severity": v.severity.value,
                    "source_section": v.source_section,
                    "matched_text": v.matched_text,
                    "message": v.message,
                    "guidance": v.guidance,
                }
            )

    # Log the validation result
    hook_log(
        "constitutional_enforcer",
        "validation_complete",
        {
            "passed": is_valid,
            "violation_count": len(violations),
            "violations": [
                v.get("rule_id") if isinstance(v, dict) else v.rule_id
                for v in violations
            ],
        },
    )

    # Use block_protocol for correct Stop hook output format
    if not is_valid:
        hook_log(
            "constitutional_enforcer",
            "response_blocked",
            {
                "violations": formatted_violations,
            },
        )

        # Format violation message for Claude to see
        violation_msg = enforcer.format_violations(violations)

        if BLOCK_PROTOCOL_AVAILABLE:
            block_response(reason=violation_msg, hook="constitutional_enforcer")
        else:
            # Fallback to manual format if block_protocol unavailable
            _logger.warning("%s", violation_msg)
            sys.exit(2)

    # Valid response - allow stop
    if BLOCK_PROTOCOL_AVAILABLE:
        allow_response()
    else:
        print(json.dumps({}))
        sys.exit(0)

if __name__ == "__main__":
    main()
