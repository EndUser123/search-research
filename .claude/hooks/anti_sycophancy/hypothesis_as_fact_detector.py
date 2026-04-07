"""
Hypothesis-as-Fact Detector for Anti-Sycophancy System

Detects when LLM responses present unverified hypotheses as factual claims.
This is Phase 1 of the anti-sycophancy system, focusing on pattern-based detection.

Phase 1 Scope:
- Path/filesystem entity claims
- Rule and system assertions
- Epistemic hedge detection

Phase 2 (future):
- Full claim normalization
- External verification
- Source attribution tracking
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class ClaimType(Enum):
    """Types of claims that can be detected."""

    ENTITY_ABSENCE = "entity_absence"  # Claims that something doesn't exist
    ENTITY_PRESENCE = "entity_presence"  # Claims that something exists
    RULE = "rule"  # Claims about rules or requirements
    SYSTEM = "system"  # Claims about system behavior
    CONVENTION = "convention"  # Claims about org norms/policies (no hedge bypass)
    MECHANISM = "mechanism"  # Claims about internal code mechanism/behavior without reading code
    ANALYSIS = "analysis"  # Value judgments and architectural opinions (no verification required)


class RiskDomain(Enum):
    """Risk domains for claims based on verification difficulty."""

    FS_CRITICAL = "FS_CRITICAL"  # Filesystem claims requiring verification
    EXTERNAL = "EXTERNAL"  # External resource claims
    SYSTEM = "SYSTEM"  # System behavior claims
    OTHER = "OTHER"  # Other claims


@dataclass
class RawClaim:
    """
    Raw claim extracted from LLM response.

    FIELD ALIGNMENT CRITICAL:
    These fields are intentionally 1:1 with future Claim dataclass in TASK-007:
    - text → text (same)
    - subject_entity → targets[0] (rename+move)
    - claim_type → type (rename)
    - confidence → confidence (same)
    - has_hedge → has_hedge (same)
    - risk_domain → risk_domain (same)

    This alignment ensures Phase 2 is a rename+move operation, not a redesign.
    """

    text: str
    subject_entity: str
    claim_type: str  # Values from ClaimType enum
    confidence: float  # 0.0 to 1.0
    has_hedge: bool
    risk_domain: str  # Values from RiskDomain enum


class HypothesisAsFactDetector:
    """
    Detects when hypotheses are presented as facts in LLM responses.

    Phase 1 focuses on pattern-based detection of:
    1. Entity claims (filesystem/docs)
    2. Rule claims
    3. Epistemic hedging
    """

    # Entity claim patterns (Phase 1: path/filesystem focused)
    ENTITY_ABSENCE_PATTERNS = [
        r"(\S+(?:/\S+)*)\s+(?:has no|does not have|lacks|is missing|lacks the|might not have|could not have)\s+(skill/|hooks/|README|\.md|pyproject\.toml|setup\.py)",
        r"(?:there is no|no)\s+(skill/|hooks/|README|\.md|pyproject\.toml|setup\.py)\s+(?:in|at|for)\s+(\S+)",
        r"(\S+(?:/\S+)*)\s+(?:doesn't have|does not have|lacking)\s+(?:a\s+)?(?:skill/|hooks/|README)",
        r"(?:file|directory|path)\s+(\S+(?:/\S+)*)\s+(?:does not exist|doesn't exist|is not present|missing)",
        r"(\S+(?:/\S+)*)\s+(?:is not a|isn't a|doesn't contain)\s+(?:valid\s+)?(?:skill|package|plugin)",
        r"(?:the\s+)?(\S+(?:/\S+)*)\s+(?:might not|could not)\s+(?:have|contain)\s+(?:a\s+)?(?:skill/|hooks/|README)",
    ]

    ENTITY_PRESENCE_PATTERNS = [
        r"(\S+(?:/\S+)*)\s+(?:has|contains|includes)\s+(?:a\s+)?(?:skill/|hooks/|README)",
        r"(?:there is|found)\s+(?:a\s+)?(?:skill/|hooks/|README)\s+(?:in|at)\s+(\S+)",
        r"(?:package|module)\s+(\S+)\s+(?:exists|is present|has)",
        r"per\s+(?:the\s+)?(?:documentation|README|SKILL\.md)\s+(?:in\s+)?(\S+)",
    ]

    # Rule claim patterns
    RULE_PATTERNS = [
        r"(?:according to|based on|per|as stated in)\s+(?:the\s+)?(?:documentation|README|SKILL\.md|docs)",
        r"the\s+(?:system|framework|architecture)\s+(?:requires|mandates|expects|demands)",
        r"(?:module|function|class|hook|skill)\s+(\w+)\s+(?:always|must|should|will)\s+(?:do|perform|return|handle|initializes?|executes?)",
        r"the\s+(?:rule|principle|pattern|guideline)\s+is\s+(?:to\s+)?that?",
        r"by\s+(?:definition|design|convention|default)",
        r"(\w+(?:hook|skill|module))?\s+(?:always|consistently|invariably)\s+(?:initializes?|executes?|does|performs?)",
    ]

    # Mechanism claim patterns — internal code behavior described without reading the code.
    # Motivating incident: Claude said "The _session_goal_detector reads the JSONL transcript.
    # When it can't complete within the timeout window, it marks session context as degraded."
    # None of this was verified by reading the code; it was fabricated to explain a symptom.
    MECHANISM_CLAIM_PATTERNS = [
        # Conditional system behavior: "when it can't/fails/times out, it marks/sets/returns X"
        r"when\s+(?:it|the\s+\w+)\s+(?:can'?t|cannot|fails?\s+to|times?\s+out|doesn'?t|doesn\u2019t|is\s+unable\s+to)\s*,?\s*it\s+(?:marks?|sets?|flags?|returns?|leaves?|logs?|stores?|raises?|throws?)",
        # Named internal/private component behavior: "The _func reads/writes/marks X"
        r"(?:the\s+)?_\w+\s+(?:reads?|writes?|marks?|sets?|returns?|calls?|handles?|processes?|checks?|scans?|detects?|logs?|stores?|fetches?)",
        # Mechanism attribution: "it's a [type] issue/problem/bug"
        # Handles compound forms like "performance/timeout issue"
        r"\bit['\u2019]?s?\s+(?:not\s+)?a\s+(?:performance|timeout|race\s+condition|memory|latency|concurrency|timing|code)(?:[/\-]\w+)*\s+(?:issue|problem|bug|defect|concern)\b",
        # Component reads/processes transcript/file without verification
        r"(?:reads?|parses?|scans?)\s+the\s+(?:current\s+)?(?:session'?s?\s+)?(?:JSONL|JSON|transcript|log|state)\s+(?:file\s+)?(?:to|and|for)",
        # Confidence/degradation mechanism claims: "marks X as degraded/failed with confidence Y%"
        r"marks?\s+\w+(?:\s+\w+)?\s+(?:context|state|session|result)\s+as\s+(?:degraded|failed|invalid|stale|incomplete)",
    ]

    # Convention/policy fabrication patterns (no hedge bypass — hedge words are part of the fabrication)
    CONVENTION_PATTERNS = [
        r"(?:hooks?|scripts?|fixes?)\s+(?:typically|often|usually|generally)\s+(?:go|are)\s+(?:undocumented|skipped|optional|informal)",
        r"(?:micro[-\s]?fix|quick[-\s]?fix|patch)\s+policy",
        r"by\s+(?:our|the|this|project|team)\s+(?:convention|practice|policy|standard|norm)",
        r"the\s+(?:convention|policy|practice|norm|standard)\s+(?:is|here\s+is|for\s+this\s+(?:project|codebase|repo))",
        r"(?:skip|omit|leave out|skip\s+the)\s+(?:if|when)\s+(?:micro|small|tiny|quick|minor)",
        r"(?:we|the team|this project)\s+(?:typically|usually|often|generally)\s+(?:don't|do not|skip|omit|leave)\s+(?:document|commit|test|write)",
    ]

    # Analysis/value judgment patterns — architectural opinions that don't require tool verification
    # These are subjective assessments about software design, not factual claims about filesystem/code
    ANALYSIS_PATTERNS = [
        r"(\S+(?:/\S+)*)\s+(?:is valuable for|provides value to|is useful for|has value for)\s+(\S+)",
        r"(?:right idea|wrong contract|correct approach|appropriate for|best fit for)",
        r"(?:should|should not)\s+(?:be used|be applied|inform|guide)\s+(?:the\s+)?(?:design|architecture|implementation)",
        r"(?:valuable|useful|appropriate|suitable)\s+(?:for|to|in)\s+(?:this\s+)?(?:context|scenario|use case)",
        r"(?:better|worse|preferable)\s+(?:than|to)\s+(?:alternative|option|approach)",
        r"(?:doesn't apply|not applicable)\s+(?:to|for)\s+(?:this\s+)?(?:audit|question|scenario)",
        r"(?:pure\s+)?(?:prose|markdown)\s+(?:framework|artifact|document)",
    ]

    # Skip patterns — markdown structural elements that are conventional format, not verification claims
    SKIP_PATTERNS = [
        re.compile(r"^\s*##\s+\w"),  # Markdown headers: ## Header
        re.compile(r"^\s*\*\s+"),  # Bullet lists: * item
        re.compile(r"^\s*-\s+"),  # Bullet lists: - item
        re.compile(r"^\s*\d+\.\s+"),  # Numbered lists: 1. item
        re.compile(r"^\s*>\s+"),  # Block quotes: > quote
        re.compile(r"^\s*```"),  # Code blocks: ```code
        re.compile(r"^\s*\|"),  # Tables: | col |
        re.compile(r"^\s*\*\*.*:.*\*\*\s*$"),  # Bold labels: **Summary:** (markdown label lines)
        re.compile(r"^\s*---+\s*$"),  # Horizontal rules: ---
    ]

    # Epistemic hedge words
    HEDGE_WORDS = {
        "might",
        "could",
        "possibly",
        "perhaps",
        "maybe",
        "appears to",
        "seems to",
        "seems like",
        "likely",
        "probably",
        "suggests",
        "indicates",
        "may",
        "might be",
        "could be",
        "tends to",
        "typically",
        "generally",
        "usually",
        "often",
        "sometimes",
    }

    # Strong assertion words (unhedged)
    STRONG_ASSERTION_WORDS = {
        "is",
        "has",
        "does",
        "will",
        "must",
        "certainly",
        "definitely",
        "undoubtedly",
        "clearly",
        "obviously",
        "always",
        "never",
    }

    def __init__(self) -> None:
        """Initialize the detector with compiled regex patterns."""
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile all regex patterns for efficiency."""
        self.compiled_entity_absence = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.ENTITY_ABSENCE_PATTERNS
        ]
        self.compiled_entity_presence = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.ENTITY_PRESENCE_PATTERNS
        ]
        self.compiled_rules = [re.compile(pattern, re.IGNORECASE) for pattern in self.RULE_PATTERNS]
        self.compiled_conventions = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.CONVENTION_PATTERNS
        ]
        self.compiled_mechanisms = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.MECHANISM_CLAIM_PATTERNS
        ]
        self.compiled_analysis = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.ANALYSIS_PATTERNS
        ]
        self.compiled_skip = [re.compile(pattern) for pattern in self.SKIP_PATTERNS]

    def _is_structural_format(self, sentence: str) -> bool:
        """Check if sentence is a markdown structural element to skip.

        Structural elements like ## Headers, - bullets, and **bold** labels
        are conventional format markers, not verification claims.
        """
        for pattern in self.compiled_skip:
            if pattern.search(sentence):
                return True
        return False

    def detect_claims(self, response_text: str) -> list[RawClaim]:
        """
        Detect claims in LLM response text.

        Args:
            response_text: The LLM response to analyze

        Returns:
            List of RawClaim objects representing detected claims
        """
        claims: list[RawClaim] = []

        # Split response into sentences for better context
        sentences = self._split_sentences(response_text)

        for sentence in sentences:
            # Skip very short sentences
            if len(sentence.strip()) < 10:
                continue

            # Skip markdown structural elements (headers, bullets, etc.)
            if self._is_structural_format(sentence):
                continue

            # Detect different claim types
            claims.extend(self._detect_entity_absence(sentence))
            claims.extend(self._detect_entity_presence(sentence))
            claims.extend(self._detect_rule_claims(sentence))
            claims.extend(self._detect_convention_claims(sentence))
            claims.extend(self._detect_mechanism_claims(sentence))
            claims.extend(self._detect_analysis_claims(sentence))

        return claims

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting on common delimiters
        # This is Phase 1 - could be enhanced with NLP in Phase 2
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _detect_entity_absence(self, sentence: str) -> list[RawClaim]:
        """Detect entity absence claims."""
        claims: list[RawClaim] = []

        for pattern in self.compiled_entity_absence:
            match = pattern.search(sentence)
            if match:
                entity = match.group(1)
                claim = RawClaim(
                    text=sentence,
                    subject_entity=entity,
                    claim_type=ClaimType.ENTITY_ABSENCE.value,
                    confidence=self._calculate_confidence(sentence, pattern),
                    has_hedge=self._detect_hedge(sentence),
                    risk_domain=RiskDomain.FS_CRITICAL.value,
                )
                claims.append(claim)
                break  # Only match first pattern per sentence

        return claims

    def _detect_entity_presence(self, sentence: str) -> list[RawClaim]:
        """Detect entity presence claims."""
        claims: list[RawClaim] = []

        for pattern in self.compiled_entity_presence:
            match = pattern.search(sentence)
            if match:
                entity = match.group(1)
                claim = RawClaim(
                    text=sentence,
                    subject_entity=entity,
                    claim_type=ClaimType.ENTITY_PRESENCE.value,
                    confidence=self._calculate_confidence(sentence, pattern),
                    has_hedge=self._detect_hedge(sentence),
                    risk_domain=RiskDomain.FS_CRITICAL.value,
                )
                claims.append(claim)
                break  # Only match first pattern per sentence

        return claims

    def _detect_rule_claims(self, sentence: str) -> list[RawClaim]:
        """Detect rule and system claims."""
        claims: list[RawClaim] = []

        for pattern in self.compiled_rules:
            match = pattern.search(sentence)
            if match:
                # Try to extract subject entity
                entity = match.group(1) if match.lastindex and match.group(1) else "system"

                claim = RawClaim(
                    text=sentence,
                    subject_entity=entity,
                    claim_type=ClaimType.RULE.value,
                    confidence=self._calculate_confidence(sentence, pattern),
                    has_hedge=self._detect_hedge(sentence),
                    risk_domain=RiskDomain.SYSTEM.value,
                )
                claims.append(claim)
                break  # Only match first pattern per sentence

        return claims

    def _detect_convention_claims(self, sentence: str) -> list[RawClaim]:
        """Detect organizational convention/policy fabrication claims.

        IMPORTANT: CONVENTION claims must NOT bypass the gate even if has_hedge=True,
        because fabricated norms deliberately use hedge words ("typically", "often")
        as part of the invention pattern. The gate is responsible for not bypassing
        CONVENTION claims via the hedge exemption.
        """
        claims: list[RawClaim] = []

        for pattern in self.compiled_conventions:
            match = pattern.search(sentence)
            if match:
                # Try to extract subject entity, fall back to "convention"
                entity = match.group(1) if match.lastindex and match.group(1) else "convention"

                claim = RawClaim(
                    text=sentence,
                    subject_entity=entity,
                    claim_type=ClaimType.CONVENTION.value,
                    confidence=self._calculate_confidence(sentence, pattern),
                    has_hedge=self._detect_hedge(sentence),
                    risk_domain=RiskDomain.OTHER.value,
                )
                claims.append(claim)
                break  # Only match first pattern per sentence

        return claims

    def _detect_mechanism_claims(self, sentence: str) -> list[RawClaim]:
        """Detect internal mechanism/behavior claims without code-reading evidence.

        Catches the pattern where the LLM explains HOW code works internally
        (private function behavior, conditional state transitions, causal attribution)
        without any Read/Grep evidence showing it actually read that code.

        Motivating incident: Claude described _session_goal_detector behavior and
        a "timeout window" without reading gto_orchestrator.py.
        """
        claims: list[RawClaim] = []

        for pattern in self.compiled_mechanisms:
            match = pattern.search(sentence)
            if match:
                entity = match.group(1) if match.lastindex and match.group(1) else "mechanism"

                claim = RawClaim(
                    text=sentence,
                    subject_entity=entity,
                    claim_type=ClaimType.MECHANISM.value,
                    confidence=self._calculate_confidence(sentence, pattern),
                    has_hedge=self._detect_hedge(sentence),
                    risk_domain=RiskDomain.SYSTEM.value,
                )
                claims.append(claim)
                break  # Only match first pattern per sentence

        return claims

    def _detect_analysis_claims(self, sentence: str) -> list[RawClaim]:
        """Detect analysis/value judgment claims.

        These are subjective assessments about software design, architecture,
        or appropriateness that don't require tool verification (unlike
        filesystem or code behavior claims).

        Examples: "X is valuable for Y", "right idea, wrong contract"
        """
        claims: list[RawClaim] = []

        for pattern in self.compiled_analysis:
            match = pattern.search(sentence)
            if match:
                # Try to extract subject entity, fall back to "analysis"
                entity = match.group(1) if match.lastindex and match.group(1) else "analysis"

                claim = RawClaim(
                    text=sentence,
                    subject_entity=entity,
                    claim_type=ClaimType.ANALYSIS.value,
                    confidence=self._calculate_confidence(sentence, pattern),
                    has_hedge=self._detect_hedge(sentence),
                    risk_domain=RiskDomain.OTHER.value,  # Analysis is not a verification risk domain
                )
                claims.append(claim)
                break  # Only match first pattern per sentence

        return claims

    def _detect_hedge(self, sentence: str) -> bool:
        """
        Detect if sentence contains epistemic hedging.

        Args:
            sentence: Sentence to check

        Returns:
            True if hedge detected, False otherwise
        """
        sentence_lower = sentence.lower()

        # Check for hedge words
        for hedge_word in self.HEDGE_WORDS:
            if hedge_word in sentence_lower:
                return True

        # Check for strong assertions
        for strong_word in self.STRONG_ASSERTION_WORDS:
            if strong_word in sentence_lower:
                # If we find strong assertion words without hedge words, it's unhedged
                return False

        return False

    def _calculate_confidence(self, sentence: str, pattern: re.Pattern) -> float:
        """
        Calculate confidence score for a claim.

        Args:
            sentence: The claim sentence
            pattern: The matched pattern

        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.7

        # Higher confidence if pattern matches cleanly
        if pattern.fullmatch(sentence):
            base_confidence = 0.9

        # Adjust based on hedging
        if self._detect_hedge(sentence):
            base_confidence -= 0.2

        # Adjust based on specificity
        if len(sentence) > 100:
            base_confidence += 0.1

        return max(0.0, min(1.0, base_confidence))
