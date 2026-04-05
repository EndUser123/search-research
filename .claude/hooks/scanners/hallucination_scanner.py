#!/usr/bin/env python3
"""
Hallucination Detection Scanner
===============================

Detects factual hallucinations using NLI (Natural Language Inference)
principles adapted from FACTSCORE:
https://github.com/linzeyu/FACTSCORE

Architecture:
1. Extract atomic facts from response
2. Verify each fact against knowledge base or context
3. Flag contradictions and ungrounded claims

Returns:
- ENTAILMENT: Fact is supported by context
- CONTRADICTION: Fact contradicts known information
- UNGROUNDED: Fact cannot be verified

Performance target: ~100ms for short responses
"""

import re
from dataclasses import dataclass

from .base_scanner import BaseScanner, ScanResult, ScanStatus


@dataclass
class AtomicFact:
    """An atomic fact extracted from text."""
    text: str
    position: int  # Character position in original text
    confidence: float  # 0.0 to 1.0


class HallucinationScanner(BaseScanner):
    """
    Fast hallucination detection using NLI principles.

    Detects:
    - Factual claims that contradict known context
    - Ungrounded assertions without evidence
    - Implausible claims

    Note: This is a lightweight version. Full FACTSCORE uses DeBERTa-v3-base
    for NLI verification. This version uses rule-based verification.
    """

    # Patterns that suggest ungrounded claims
    UNGROUNDED_PATTERNS = [
        (r"should work\b", 0.7, "Unverified functionality claim"),
        (r"ought to succeed\b", 0.7, "Unverified success prediction"),
        (r"(?:will|should|must) (?:definitely|certainly|surely) work\b", 0.8, "Overconfident prediction"),
        (r"(?:obviously|clearly|naturally)", 0.5, "Assumption without evidence"),
        (r"everyone knows that\b", 0.7, "Unverified generalization"),
        (r"it goes without saying\b", 0.7, "Unverified common knowledge"),
    ]

    # Patterns suggesting code execution evidence
    EXECUTION_EVIDENCE = [
        r"```\w*\n.*?```",  # Code blocks
        r"✅\s*\w+",  # Checkmarks with text
        r"Step\s+\d+:",  # Step-by-step execution
        r"Output:?\s*\n",  # Command output
        r"(?:Created|Wrote|Modified)\s+\S+",  # File operations
        r"Test(?:ing)?\s+(?:passed|succeeded)",  # Test results
    ]

    # File/path references that should be verified
    PATH_REFERENCE = r"(?:[A-Za-z]:[/\\]|/)[\w\-./\\]+\.[\w]+"

    def __init__(self, enabled: bool = True, strict_mode: bool = False):
        """
        Initialize hallucination scanner.

        Args:
            enabled: Whether scanner is active
            strict_mode: If True, flag more potential issues
        """
        super().__init__(enabled)
        self.strict_mode = strict_mode

    def scan(self, text: str, context: dict = None) -> ScanResult:
        """
        Scan text for hallucinations and ungrounded claims.

        Args:
            text: The text to scan
            context: Optional context with known facts, file paths, etc.

        Returns:
            ScanResult with validation outcome
        """
        if not self.enabled:
            return ScanResult(ScanStatus.SKIP, self.name)

        # Extract known facts from context
        known_files = self._extract_known_files(context) if context else []
        known_evidence = self._extract_execution_evidence(context) if context else []

        # Check for ungrounded claims
        for pattern, confidence, description in self.UNGROUNDED_PATTERNS:
            if not self.strict_mode and confidence < 0.7:
                continue

            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Check if there's execution evidence nearby
                has_evidence = self._has_nearby_evidence(text, match.start())

                if not has_evidence:
                    return ScanResult(
                        status=ScanStatus.FAIL,
                        scanner_name=self.name,
                        matched_text=match.group(0),
                        reason=f"{description} (no execution evidence)",
                        severity="MEDIUM",
                        suggestion="Provide execution output or test results",
                    )

        # Check for factual claims about specific files
        file_claims = re.finditer(self.PATH_REFERENCE, text)
        for match in file_claims:
            file_path = match.group(0)
            # Check if file is referenced in context as actually existing/modified
            if file_path not in known_files and self._claims_creation(text, match.start()):
                if not known_evidence:
                    return ScanResult(
                        status=ScanStatus.FAIL,
                        scanner_name=self.name,
                        matched_text=file_path,
                        reason=f"Claim about {file_path} without verification",
                        severity="MEDIUM",
                        suggestion="Verify file existence before claiming operations",
                    )

        # Check for "all X fixed" type scope inflation
        scope_patterns = [
            (r"\ball\s+(?:tests|checks|issues|bugs|problems)\s+(?:pass|fixed|resolved|gone)", 0.9),
            (r"\bfully\s+(?:functional|working|operational)\b", 0.8),
            (r"\bcompletely\s+(?:fixed|resolved|sorted)\b", 0.8),
        ]

        for pattern, confidence in scope_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Check for specific counts (e.g., "5/5 tests passed")
                context_window = text[max(0, match.start() - 50):match.end() + 50]
                if not re.search(r"\d+/\d+", context_window):
                    return ScanResult(
                        status=ScanStatus.FAIL,
                        scanner_name=self.name,
                        matched_text=match.group(0),
                        reason="Scope inflation without specific evidence",
                        severity="HIGH",
                        suggestion="Provide specific counts: 'X of Y items' with evidence",
                    )

        return ScanResult(ScanStatus.PASS, self.name)

    def _extract_known_files(self, context: dict) -> list[str]:
        """Extract list of known files from context."""
        known_files = []

        # From tools used
        tools_used = context.get("tools_used", [])
        for tool in tools_used:
            if tool.get("name") in ("Read", "Edit", "Write"):
                input_data = tool.get("input", {})
                file_path = input_data.get("file_path", "")
                if file_path:
                    known_files.append(file_path)

        # From transcript
        transcript_files = context.get("mentioned_files", [])
        known_files.extend(transcript_files)

        return known_files

    def _extract_execution_evidence(self, context: dict) -> list[str]:
        """Extract execution evidence from context."""
        evidence = []

        # Check for command outputs
        if "command_outputs" in context:
            evidence.extend(context["command_outputs"])

        # Check for test results
        if "test_results" in context:
            evidence.extend(context["test_results"])

        return evidence

    def _has_nearby_evidence(self, text: str, position: int) -> bool:
        """Check if there's execution evidence near a claim."""
        # Look within 200 characters before/after
        window_start = max(0, position - 200)
        window_end = min(len(text), position + 200)
        window = text[window_start:window_end]

        for pattern in self.EXECUTION_EVIDENCE:
            if re.search(pattern, window, re.IGNORECASE | re.DOTALL):
                return True

        return False

    def _claims_creation(self, text: str, position: int) -> bool:
        """Check if text claims to create/modify a file."""
        window_start = max(0, position - 100)
        window_end = min(len(text), position + 100)
        window = text[window_start:window_end].lower()

        creation_patterns = [
            r"(?:created|wrote|modified|updated|generated)\s+\S+",
            r"(?:creating|writing|modifying|updating|generating)\s+\S+",
            r"(?:create|write|modify|update|generate)\s+\S+?\s+file",
        ]

        return any(re.search(pattern, window) for pattern in creation_patterns)

    def extract_facts(self, text: str) -> list[AtomicFact]:
        """
        Extract atomic facts from text (for NLI verification).

        This is a simplified version. Full FACTSCORE uses more sophisticated
        NLP for fact extraction.

        Args:
            text: Text to extract facts from

        Returns:
            List of AtomicFact objects
        """
        facts = []

        # Simple fact extraction: sentences with explicit claims
        sentences = re.split(r'[.!?]+', text)

        fact_indicators = [
            r'\b(is|are|was|were|has|have|will|can|should)\b',
            r'\b(said|stated|claimed|reported|found)\b',
            r'\b(result|output|returned)\b',
        ]

        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip short fragments
                continue

            # Check if sentence looks like a factual claim
            if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in fact_indicators):
                facts.append(AtomicFact(
                    text=sentence,
                    position=text.find(sentence),
                    confidence=0.7,  # Default confidence
                ))

        return facts

    def verify_fact_with_context(
        self, fact: AtomicFact, context: dict
    ) -> tuple[str, float]:
        """
        Verify a fact against available context.

        Returns:
            Tuple of (verdict, confidence) where verdict is:
            - "ENTAILMENT": Fact is supported by context
            - "CONTRADICTION": Fact contradicts context
            - "UNGROUNDED": Cannot be verified
        """
        # This is a simplified rule-based version
        # Full implementation would use NLI model (DeBERTa-v3-base)

        known_files = self._extract_known_files(context)

        # Check if fact mentions a file
        file_mention = re.search(self.PATH_REFERENCE, fact.text)
        if file_mention:
            file_path = file_mention.group(0)
            if file_path in known_files:
                return ("ENTAILMENT", 0.9)
            else:
                return ("UNGROUNDED", 0.7)

        # Default: cannot verify
        return ("UNGROUNDED", 0.5)
