"""Decision extraction from Claude Code transcripts - Oppia 5-Step Structure.

This module extracts structured decisions from session transcripts using
Oppia's proven 5-step investigation methodology:

1. Problem Definition
2. Code Investigation
3. Hypothesis Testing
4. Solution Documentation
5. Outcome Verification

Extracted decisions are stored in CKS as 'decision' or 'learning' entries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ExtractedDecision:
    """A decision extracted from a transcript using Oppia structure."""

    # Oppia Step 1: Problem Definition
    problem_statement: str
    problem_context: str | None = None

    # Oppia Step 2: Code Investigation
    affected_code: str | None = None
    investigation_findings: str | None = None

    # Oppia Step 3: Hypothesis Testing
    hypotheses_tested: list[str] = field(default_factory=list)
    confirmed_hypothesis: str | None = None
    hypothesis_confidence: float = 0.0

    # Oppia Step 4: Solution Documentation
    title: str = ""
    selected_option: str = ""
    alternatives: list[str] = field(default_factory=list)
    rationale: str = ""
    solution_details: str | None = None

    # Oppia Step 5: Outcome Verification
    outcome_verified: bool = False
    outcome_notes: str | None = None

    # Additional metadata
    decision_type: str = (
        "EXPLORATION"  # ARCHITECTURAL, DEBUGGING, IMPLEMENTATION, PROCESS, EXPLORATION
    )
    reversibility: str | None = None  # R:0, R:1, R:2
    confidence: float = 0.5  # Extraction confidence
    source_line: int = 0

    def to_cks_content(self) -> str:
        """Format as CKS decision entry content."""
        parts = []

        if self.problem_statement:
            parts.append(f"**Problem:** {self.problem_statement}")

        if self.hypotheses_tested:
            parts.append("**Hypotheses Tested:**")
            for i, h in enumerate(self.hypotheses_tested, 1):
                marker = " ✓" if h == self.confirmed_hypothesis else ""
                parts.append(f"  {i}. {h}{marker}")

        if self.selected_option:
            parts.append(f"**Decision:** {self.selected_option}")

        if self.alternatives:
            parts.append("**Alternatives Considered:**")
            for alt in self.alternatives:
                parts.append(f"  - {alt}")

        if self.rationale:
            parts.append(f"**Rationale:** {self.rationale}")

        if self.outcome_verified:
            parts.append("**Outcome:** ✓ Verified")
            if self.outcome_notes:
                parts.append(f"  {self.outcome_notes}")

        if self.investigation_findings:
            parts.append(f"**Investigation:** {self.investigation_findings}")

        return "\n\n".join(parts)

    def to_cks_metadata(self) -> dict:
        """Extract as CKS metadata dict."""
        return {
            "hypotheses_count": len(self.hypotheses_tested),
            "hypothesis_confidence": self.hypothesis_confidence,
            "outcome_verified": self.outcome_verified,
            "decision_type": self.decision_type,
            "reversibility": self.reversibility,
            "extraction_confidence": self.confidence,
            "oppia_complete": self._oppia_completeness(),
        }

    def _oppia_completeness(self) -> float:
        """Calculate % of Oppia 5-step fields filled."""
        fields = [
            bool(self.problem_statement),
            bool(self.hypotheses_tested),
            bool(self.selected_option),
            bool(self.rationale),
            self.outcome_verified is not False,  # Explicit check
        ]
        return sum(fields) / len(fields)


class DecisionExtractor:
    """Extract decisions from transcripts using Oppia 5-step patterns."""

    # Oppia-enhanced patterns with word boundaries
    PATTERNS = {
        "problem": [
            r"##?\s*Problem\s+(?:Definition|:).*?\n+(.+?)(?:\n\n|\n(?=##)|$)",
            r"\bProblem:?\s+(.+?)(?:\n\n|\n(?=[A-Z])|$)",
            r"##?\s*Issue.*?\n+(.+?)(?:\n\n|\n(?=##)|$)",
        ],
        "hypotheses": [
            r"##?\s*Hypothesis(?:s|\s+Testing)?:?\s*\n+(.+?)(?:\n\n|\n(?=##?\s+[A-Z])|$)",
            r"\bHypothes(?:is|es):?\s*\n+(.+?)(?:\n\n|\n(?=[A-Z][^a-z])|$)",
            r"\bCould\s+be:?\s*\n+(.+?)(?:\n\n|\n(?=[A-Z][^a-z])|$)",
            r"\bPossible\s+causes?:?\s*\n+(.+?)(?:\n\n|\n(?=[A-Z][^a-z])|$)",
        ],
        "decision": [
            r"\bRecommend:?\s+(.+?)(?:\n|$)",
            r"\bDecision:?\s+(.+?)(?:\n|$)",
            r"\bChoose:?\s+(.+?)(?:\n|$)",
            r"\bGoing\s+with:?\s+(.+?)(?:\n|$)",
        ],
        "alternatives": [
            r"\bOption\s+([A-Z]):\s+(.+?)(?:\n|$)",
            r"\bAlternative:?\s+(.+?)(?:\n|$)",
        ],
        "rationale": [
            r"\bRationale:?\s*(.+?)(?:\n\n|\n(?=[A-Z])|$)",
            r"\bBecause:?\s+(.+?)(?:\n|$)",
        ],
        "outcome": [
            r"\bVerif(?:ied|ication):?\s+(.+?)(?:\n|$)",
            r"\bOutcome:?\s+(.+?)(?:\n|$)",
        ],
        "reversibility": [
            r"\bR:?([0-2])",
        ],
    }

    DECISION_TYPE_KEYWORDS = {
        "ARCHITECTURAL": ["architect", "design", "pattern", "structure", "schema"],
        "DEBUGGING": ["debug", "fix", "error", "bug", "broken", "fail", "crash"],
        "IMPLEMENTATION": ["implement", "build", "create", "write", "add", "use"],
        "PROCESS": ["test", "verify", "workflow", "process", "workflow"],
    }

    def __init__(self, min_confidence: float = 0.60):
        self.min_confidence = min_confidence

    def extract_from_transcript(self, transcript: str) -> list[ExtractedDecision]:
        """Extract all decisions from a transcript."""
        if not transcript or len(transcript) < 100:
            return []

        decisions = []
        blocks = self._find_decision_blocks(transcript)

        for block_text, line_num in blocks:
            decision = self._extract_from_block(block_text, line_num)
            if decision and decision.confidence >= self.min_confidence:
                decisions.append(decision)

        return decisions

    def _find_decision_blocks(self, transcript: str) -> list[tuple[str, int]]:
        """Find blocks of text that contain decision markers."""
        # Simple approach: return entire transcript as one block
        # The extraction will parse all fields from it
        if len(transcript) > 100:
            return [(transcript, 1)]
        return []

    def _extract_from_block(self, block: str, line_num: int) -> ExtractedDecision | None:
        """Extract a single decision from a text block."""
        # Step 1: Problem
        problem = self._match_first("problem", block)

        # Step 3: Hypotheses
        hypotheses = self._extract_hypotheses(block)
        confirmed = self._extract_confirmed_hypothesis(block, hypotheses)

        # Step 4: Decision
        decision = self._match_first("decision", block)
        if not decision and not problem:
            return None

        title = decision or (problem[:60] + "..." if problem else "Decision")
        alternatives = self._extract_alternatives(block)
        rationale = self._match_first("rationale", block)

        # Step 5: Outcome
        outcome = self._match_first("outcome", block)
        # Check entire block for "Verified:" marker, not just outcome field
        verified = (
            "Verified:" in block
            or "outcome verified" in block.lower()
            or (
                outcome
                and any(w in outcome.lower() for w in ["verified", "yes", "true", "✓", "worked"])
            )
        )

        # Metadata
        reversibility = self._extract_reversibility(block)
        decision_type = self._infer_decision_type(title + " " + (problem or ""))

        # Calculate confidence
        confidence = self._calculate_confidence(
            problem=bool(problem),
            hypotheses=bool(hypotheses),
            decision=bool(decision),
            rationale=bool(rationale),
            verified=verified,
            reversibility=bool(reversibility),
        )

        return ExtractedDecision(
            problem_statement=problem or title,
            hypotheses_tested=hypotheses,
            confirmed_hypothesis=confirmed,
            hypothesis_confidence=0.8 if confirmed else 0.0,
            title=title,
            selected_option=decision or title,
            alternatives=alternatives or ["(not stated)"],
            rationale=rationale or "(not stated)",
            outcome_verified=verified,
            outcome_notes=outcome if verified else None,
            decision_type=decision_type,
            reversibility=reversibility,
            confidence=confidence,
            source_line=line_num,
        )

    def _match_first(self, pattern_type: str, text: str) -> str | None:
        """Match first pattern of a type and return capture group."""
        for pattern in self.PATTERNS.get(pattern_type, []):
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                result = match.group(1).strip()
                # Clean up artifacts
                # Remove leading/trailing section headers that got captured
                result = re.sub(
                    r"^##?\s*(Problem|Issue|Context|Hypothesis|Outcome|Solution).*?:?\s*",
                    "",
                    result,
                    flags=re.IGNORECASE,
                )
                # Take first line only (for multi-line captures)
                result = result.split("\n")[0].strip()
                return result if result else None
        return None

    def _extract_hypotheses(self, text: str) -> list[str]:
        """Extract hypothesis list from text."""
        for pattern in self.PATTERNS["hypotheses"]:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1)
                # Split by common delimiters
                items = re.split(r"\n\s*[-•*]\s*|\n\s*\d+[\.)]\s*", content)
                hypotheses = [h.strip() for h in items if h.strip()]
                return hypotheses[:7]  # Max 7 hypotheses
        return []

    def _extract_confirmed_hypothesis(self, text: str, hypotheses: list[str]) -> str | None:
        """Find which hypothesis was confirmed."""
        # Look for markers like "(CONFIRMED)" or "✓"
        for i, h in enumerate(hypotheses):
            if "(CONFIRMED)" in h or "✓" in h or "confirmed" in h.lower():
                return h
        # Also check the text for confirmation patterns
        if hypotheses:
            confirmed_match = re.search(
                r"confirmed[:\s]+(?:hypothesis\s+)?(\d+)",
                text,
                re.IGNORECASE,
            )
            if confirmed_match:
                idx = int(confirmed_match.group(1)) - 1
                if 0 <= idx < len(hypotheses):
                    return hypotheses[idx]
        return None

    def _extract_alternatives(self, text: str) -> list[str]:
        """Extract alternative options."""
        alternatives = []
        for pattern in self.PATTERNS["alternatives"]:
            matches = re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                alt = match.group(2) if match.lastindex >= 2 else match.group(1)
                alternatives.append(alt.strip())
        return list(set(alternatives))

    def _extract_reversibility(self, text: str) -> str | None:
        """Extract reversibility score."""
        match = re.search(self.PATTERNS["reversibility"][0], text)
        if match:
            return f"R:{match.group(1)}"
        return None

    def _infer_decision_type(self, text: str) -> str:
        """Infer decision type from keywords."""
        text_lower = text.lower()
        scores = {}
        for dtype, keywords in self.DECISION_TYPE_KEYWORDS.items():
            scores[dtype] = sum(1 for kw in keywords if kw in text_lower)

        if scores:
            return max(scores, key=scores.get)
        return "EXPLORATION"

    def _calculate_confidence(
        self,
        problem: bool,
        hypotheses: bool,
        decision: bool,
        rationale: bool,
        verified: bool,
        reversibility: bool,
    ) -> float:
        """Calculate extraction confidence score."""
        score = 0.4  # Base score

        if problem:
            score += 0.15
        if hypotheses:
            score += 0.15  # Strong signal
        if decision:
            score += 0.15
        if rationale:
            score += 0.10
        if verified:
            score += 0.05
        if reversibility:
            score += 0.05

        return min(1.0, score)


def extract_decisions_from_transcript(
    transcript: str, min_confidence: float = 0.60
) -> list[ExtractedDecision]:
    """Convenience function to extract decisions from a transcript.

    Args:
        transcript: Full session transcript text
        min_confidence: Minimum confidence threshold (0.0-1.0)

    Returns:
        List of ExtractedDecision objects

    """
    extractor = DecisionExtractor(min_confidence=min_confidence)
    return extractor.extract_from_transcript(transcript)
