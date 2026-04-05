from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .modules.orchestration.react_evidence_collector import EvidenceItem

"""Verification-Specific ReAct Action Patterns for Fact-Checking.

This module defines specialized ReAct action patterns optimized for Chain-of-Verification
fact-checking workflows. These actions are designed specifically for verification tasks
like factual accuracy validation, source validation, and logical consistency checking.

Key Features:
- Specialized action types for verification tasks
- Optimized evidence collection for fact-checking
- Source credibility assessment capabilities
- Efficient pattern matching for verification queries
- Performance-optimized verification actions

Algorithm Approach:
1. Map verification strategies to optimized ReAct actions
2. Execute verification-specific evidence collection
3. Assess source credibility and fact accuracy
4. Provide structured verification results

Time Complexity: O(n) where n is the size of the evidence space
Space Complexity: O(m) where m is the evidence collected
Performance: Optimized for <1s per verification action
"""





class VerificationActionType(Enum):
    """Specialized action types for verification tasks."""

    FACT_CHECK_SEARCH = "fact_check_search"
    SOURCE_CREDIBILITY_CHECK = "source_credibility_check"
    CLAIM_PATTERN_MATCH = "claim_pattern_match"
    NUMERICAL_VERIFICATION = "numerical_verification"
    CITATION_VALIDATION = "citation_validation"
    CONTEXT_ANALYSIS = "context_analysis"
    CONTRADICTION_DETECTION = "contradiction_detection"
    EXPERT_CONSENSUS_CHECK = "expert_consensus_check"


class VerificationStrategy(Enum):
    """Verification strategies mapping to action patterns."""

    FACTUAL_ACCURACY = "factual_accuracy"
    LOGICAL_CONSISTENCY = "logical_consistency"
    SOURCE_VALIDATION = "source_validation"
    COMPLETENESS_CHECK = "completeness_check"
    NUMERICAL_PRECISION = "numerical_precision"


@dataclass
class VerificationAction:
    """Represents a verification-specific ReAct action."""

    action_type: VerificationActionType
    verification_query: str
    target_sources: list[str]
    search_patterns: list[str]
    credibility_requirements: dict[str, float] = field(default_factory=dict)
    expected_evidence_types: list[str] = field(default_factory=list)
    confidence_threshold: float = 0.7


@dataclass
class VerificationActionResult:
    """Result of a verification action execution."""

    action_type: VerificationActionType
    verification_query: str
    success: bool
    verification_evidence: list[EvidenceItem]
    confidence_score: float
    credibility_assessment: float
    fact_check_result: str  # "VERIFIED", "DISPUTED", "UNVERIFIED", "FAILED"
    processing_time: float
    source_quality_scores: dict[str, float] = field(default_factory=dict)
    identified_claims: list[str] = field(default_factory=list)


class VerificationReActActions:
    """
    Specialized ReAct actions for verification workflows.

    This class provides optimized action patterns for Chain-of-Verification
    integration with ReAct evidence collection.
    """

    def __init__(self, performance_mode: bool = True):
        """
        Initialize verification action system.

        Args:
        ----
            performance_mode: Enable performance optimizations for faster verification

        """
        self.performance_mode = performance_mode
        self.logger = logging.getLogger(__name__)

        # Initialize verification patterns and caches
        self.verification_patterns = self._initialize_verification_patterns()
        self.source_credibility_cache = {}
        self.claim_pattern_cache = {}

        # Performance tracking
        self.action_performance_history = []

    async def execute_verification_action(
        self,
        verification_action: VerificationAction,
    ) -> VerificationActionResult:
        """
        Execute a verification-specific ReAct action.

        Args:
        ----
            verification_action: The verification action to execute

        Returns:
        -------
            Comprehensive verification action result with evidence and assessment

        """
        start_time = time.time()

        try:
            # Route to appropriate action handler
            if verification_action.action_type == VerificationActionType.FACT_CHECK_SEARCH:
                result = await self._execute_fact_check_search(verification_action)
            elif verification_action.action_type == VerificationActionType.SOURCE_CREDIBILITY_CHECK:
                result = await self._execute_source_credibility_check(verification_action)
            elif verification_action.action_type == VerificationActionType.CLAIM_PATTERN_MATCH:
                result = await self._execute_claim_pattern_match(verification_action)
            elif verification_action.action_type == VerificationActionType.NUMERICAL_VERIFICATION:
                result = await self._execute_numerical_verification(verification_action)
            elif verification_action.action_type == VerificationActionType.CITATION_VALIDATION:
                result = await self._execute_citation_validation(verification_action)
            elif verification_action.action_type == VerificationActionType.CONTEXT_ANALYSIS:
                result = await self._execute_context_analysis(verification_action)
            elif verification_action.action_type == VerificationActionType.CONTRADICTION_DETECTION:
                result = await self._execute_contradiction_detection(verification_action)
            elif verification_action.action_type == VerificationActionType.EXPERT_CONSENSUS_CHECK:
                result = await self._execute_expert_consensus_check(verification_action)
            else:
                raise ValueError(f"Unsupported verification action type: {verification_action.action_type}")

            processing_time = time.time() - start_time
            result.processing_time = processing_time

            # Track performance
            await self._track_action_performance(result)

            self.logger.info(
                f"Verification action {verification_action.action_type.value} completed in {processing_time:.3f}s "
                f"with confidence {result.confidence_score:.3f}",
            )

            return result

        except Exception as e:
            self.logger.error(f"Verification action execution failed: {e!s}")
            processing_time = time.time() - start_time
            return VerificationActionResult(
                action_type=verification_action.action_type,
                verification_query=verification_action.verification_query,
                success=False,
                verification_evidence=[],
                confidence_score=0.0,
                credibility_assessment=0.0,
                fact_check_result="FAILED",
                processing_time=processing_time,
            )

    async def _execute_fact_check_search(
        self,
        verification_action: VerificationAction,
    ) -> VerificationActionResult:
        """Execute fact-check search action."""
        # Perform targeted search for factual evidence
        evidence_items = []
        identified_claims = []

        # Extract claims from verification query
        claims = self._extract_claims_from_query(verification_action.verification_query)
        identified_claims.extend(claims)

        # Search for supporting or contradicting evidence
        for claim in claims:
            for source in verification_action.target_sources:
                # Simulate targeted search (in production would use actual search)
                search_result = await self._search_claim_evidence(claim, source)

                if search_result["found"]:
                    evidence_item = EvidenceItem(
                        evidence_id=f"fact_check_{len(evidence_items)}",
                        source=source,
                        evidence_type="factual_evidence",
                        data=search_result,
                        confidence=search_result["confidence"],
                        metadata={
                            "claim": claim,
                            "source_type": search_result["source_type"],
                            "verification_timestamp": time.time(),
                        },
                    )
                    evidence_items.append(evidence_item)

        # Assess credibility of sources
        credibility_scores = self._assess_source_credibility(verification_action.target_sources)

        # Calculate overall confidence
        confidence_score = self._calculate_fact_check_confidence(evidence_items, credibility_scores)
        credibility_assessment = (
            sum(credibility_scores.values()) / len(credibility_scores) if credibility_scores else 0.5
        )

        # Determine fact-check result
        fact_check_result = self._determine_fact_check_result(evidence_items, confidence_score)

        return VerificationActionResult(
            action_type=VerificationActionType.FACT_CHECK_SEARCH,
            verification_query=verification_action.verification_query,
            success=len(evidence_items) > 0,
            verification_evidence=evidence_items,
            confidence_score=confidence_score,
            credibility_assessment=credibility_assessment,
            fact_check_result=fact_check_result,
            source_quality_scores=credibility_scores,
            identified_claims=identified_claims,
        )

    async def _execute_source_credibility_check(
        self,
        verification_action: VerificationAction,
    ) -> VerificationActionResult:
        """Execute source credibility assessment."""
        evidence_items = []
        credibility_scores = {}

        # Check each target source for credibility indicators
        for source in verification_action.target_sources:
            credibility_result = await self._assess_single_source_credibility(source)

            credibility_scores[source] = credibility_result["credibility_score"]

            # Create evidence item
            evidence_item = EvidenceItem(
                evidence_id=f"source_cred_{len(evidence_items)}",
                source=source,
                evidence_type="source_credibility",
                data=credibility_result,
                confidence=credibility_result["confidence"],
                metadata={
                    "credibility_indicators": credibility_result["indicators"],
                    "assessment_timestamp": time.time(),
                },
            )
            evidence_items.append(evidence_item)

        # Calculate overall credibility
        overall_credibility = sum(credibility_scores.values()) / len(credibility_scores) if credibility_scores else 0.0

        # Determine fact-check result based on credibility
        if overall_credibility >= 0.8:
            fact_check_result = "VERIFIED"
        elif overall_credibility >= 0.6:
            fact_check_result = "DISPUTED"
        else:
            fact_check_result = "FAILED"

        return VerificationActionResult(
            action_type=VerificationActionType.SOURCE_CREDIBILITY_CHECK,
            verification_query=verification_action.verification_query,
            success=len(evidence_items) > 0,
            verification_evidence=evidence_items,
            confidence_score=overall_credibility,
            credibility_assessment=overall_credibility,
            fact_check_result=fact_check_result,
            source_quality_scores=credibility_scores,
        )

    async def _execute_claim_pattern_match(
        self,
        verification_action: VerificationAction,
    ) -> VerificationActionResult:
        """Execute claim pattern matching for verification."""
        evidence_items = []
        identified_claims = []
        pattern_matches = []

        # Use verification patterns to find claims
        for pattern in verification_action.search_patterns:
            matches = self._find_pattern_matches(
                pattern,
                verification_action.verification_query,
            )

            for match in matches:
                identified_claims.append(match["claim"])
                pattern_matches.append(match)

                # Create evidence item
                evidence_item = EvidenceItem(
                    evidence_id=f"pattern_match_{len(evidence_items)}",
                    source="pattern_analysis",
                    evidence_type="claim_pattern",
                    data=match,
                    confidence=match["confidence"],
                    metadata={
                        "pattern": pattern,
                        "match_type": match["type"],
                        "extraction_timestamp": time.time(),
                    },
                )
                evidence_items.append(evidence_item)

        # Calculate confidence based on pattern match quality
        confidence_score = self._calculate_pattern_confidence(pattern_matches)
        credibility_assessment = min(confidence_score + 0.1, 1.0)  # Pattern matching is generally reliable

        # Determine fact-check result
        if len(pattern_matches) > 0 and confidence_score >= verification_action.confidence_threshold:
            fact_check_result = "VERIFIED"
        else:
            fact_check_result = "UNVERIFIED"

        return VerificationActionResult(
            action_type=VerificationActionType.CLAIM_PATTERN_MATCH,
            verification_query=verification_action.verification_query,
            success=len(pattern_matches) > 0,
            verification_evidence=evidence_items,
            confidence_score=confidence_score,
            credibility_assessment=credibility_assessment,
            fact_check_result=fact_check_result,
            identified_claims=identified_claims,
        )

    async def _execute_numerical_verification(
        self,
        verification_action: VerificationAction,
    ) -> VerificationActionResult:
        """Execute numerical claim verification."""
        evidence_items = []
        identified_claims = []
        numerical_claims = []

        # Extract numerical claims from verification query
        numerical_patterns = [
            r"(\d+(?:\.\d+)?(?:%|percent|times|more|less|greater|fewer))",
            r"(\d+(?:\.\d+)?\s*(?:million|billion|thousand|trillion))",
            r"(\d+(?:\.\d+)?\s*(?:gb|mb|kb|tb))",
        ]

        for pattern in numerical_patterns:
            matches = re.finditer(pattern, verification_action.verification_query, re.IGNORECASE)
            for match in matches:
                numerical_claim = match.group(1)
                numerical_claims.append(numerical_claim)
                identified_claims.append(f"Numerical claim: {numerical_claim}")

        # Verify numerical claims against sources
        for claim in numerical_claims:
            verification_result = await self._verify_numerical_claim(claim, verification_action.target_sources)

            evidence_item = EvidenceItem(
                evidence_id=f"numerical_{len(evidence_items)}",
                source="numerical_verification",
                evidence_type="numerical_claim",
                data=verification_result,
                confidence=verification_result["confidence"],
                metadata={
                    "original_claim": claim,
                    "verification_method": verification_result["method"],
                    "verification_timestamp": time.time(),
                },
            )
            evidence_items.append(evidence_item)

        # Calculate numerical verification confidence
        confidence_score = self._calculate_numerical_confidence(evidence_items)
        credibility_assessment = confidence_score  # Numerical verification is typically reliable

        # Determine fact-check result
        if confidence_score >= verification_action.confidence_threshold:
            fact_check_result = "VERIFIED"
        else:
            fact_check_result = "DISPUTED"

        return VerificationActionResult(
            action_type=VerificationActionType.NUMERICAL_VERIFICATION,
            verification_query=verification_action.verification_query,
            success=len(evidence_items) > 0,
            verification_evidence=evidence_items,
            confidence_score=confidence_score,
            credibility_assessment=credibility_assessment,
            fact_check_result=fact_check_result,
            identified_claims=identified_claims,
        )

    # Helper methods for verification actions

    def _initialize_verification_patterns(self) -> dict[str, list[str]]:
        """Initialize verification patterns for claim extraction."""
        return {
            "factual_patterns": [
                r"(?:according to|research shows|studies indicate|experts agree)\s+([^\.!?]+)",
                r"(?:proven|demonstrated|established)\s+([^\.!?]+)",
                r"(?:typically|generally|usually|often)\s+([^\.!?]+)",
            ],
            "numerical_patterns": [
                r"(\d+(?:\.\d+)?(?:%|percent|times|more|less|greater|fewer))",
                r"(\d+(?:\.\d+)?\s*(?:million|billion|thousand))",
                r"(\d+(?:\.\d+)?\s*(?:gb|mb|kb|tb))",
            ],
            "source_patterns": [
                r"(?:the study|research|experts|scientists)\s+([^\.!?]*)(?:found|concluded|reported)",
                r"(?:according to|based on)\s+([^\.!?]*?)(?:study|research|paper)",
            ],
        }

    def _extract_claims_from_query(self, query: str) -> list[str]:
        """Extract verifiable claims from verification query."""
        claims = []

        # Use cached patterns for performance
        for _pattern_type, patterns in self.verification_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, query, re.IGNORECASE)
                for match in matches:
                    claim = match.group(1).strip() if match.groups() else match.group(0).strip()
                    if claim and len(claim) > 10:  # Filter out very short matches
                        claims.append(claim)

        return list(set(claims))  # Remove duplicates

    async def _search_claim_evidence(self, claim: str, source: str) -> dict[str, Any]:
        """Search for evidence supporting or contradicting a claim."""
        # Simulate evidence search (in production would use actual search mechanisms)
        # This is a mock implementation for demonstration

        # Mock search results with confidence scores
        if "documentation" in source.lower() or "official" in source.lower():
            return {
                "found": True,
                "confidence": 0.85,
                "source_type": "official_documentation",
                "evidence_type": "supporting",
                "excerpt": f"Found supporting evidence in {source}",
            }
        if "expert" in source.lower() or "research" in source.lower():
            return {
                "found": True,
                "confidence": 0.75,
                "source_type": "expert_opinion",
                "evidence_type": "supporting",
                "excerpt": f"Expert consensus supports claim in {source}",
            }
        return {
            "found": False,
            "confidence": 0.3,
            "source_type": "unknown",
            "evidence_type": "none",
            "excerpt": f"No evidence found in {source}",
        }

    def _assess_source_credibility(self, sources: list[str]) -> dict[str, float]:
        """Assess credibility of verification sources."""
        credibility_scores = {}

        for source in sources:
            # Use cache for performance
            if source in self.source_credibility_cache:
                credibility_scores[source] = self.source_credibility_cache[source]
                continue

            # Assess credibility based on source characteristics
            score = 0.5  # Base score

            # Higher credibility for official sources
            if any(indicator in source.lower() for indicator in ["official", "documentation", "api"]):
                score += 0.3

            # Higher credibility for established sources
            if any(indicator in source.lower() for indicator in ["github", "stackoverflow", "research"]):
                score += 0.2

            # Lower credibility for user-generated content
            if any(indicator in source.lower() for indicator in ["blog", "forum", "comment"]):
                score -= 0.2

            credibility_scores[source] = max(0.0, min(1.0, score))
            self.source_credibility_cache[source] = credibility_scores[source]

        return credibility_scores

    async def _assess_single_source_credibility(self, source: str) -> dict[str, Any]:
        """Assess credibility of a single source in detail."""
        base_score = self._assess_source_credibility([source]).get(source, 0.5)

        # Analyze credibility indicators
        indicators = {
            "official_source": any(ind in source.lower() for ind in ["official", "docs", "api"]),
            "peer_reviewed": any(ind in source.lower() for ind in ["research", "paper", "journal"]),
            "community_trusted": any(ind in source.lower() for ind in ["github", "stackoverflow"]),
            "recent_update": True,  # Would check actual timestamp in production
            "authoritative": any(ind in source.lower() for ind in ["expert", "official"]),
        }

        # Calculate indicator score
        indicator_score = sum(indicators.values()) / len(indicators)
        final_score = (base_score + indicator_score) / 2

        return {
            "credibility_score": final_score,
            "confidence": 0.8,
            "indicators": indicators,
            "source_type": self._classify_source_type(source),
        }

    def _classify_source_type(self, source: str) -> str:
        """Classify the type of source."""
        source_lower = source.lower()
        if "official" in source_lower or "docs" in source_lower:
            return "official_documentation"
        if "github" in source_lower or "code" in source_lower:
            return "code_repository"
        if "research" in source_lower or "paper" in source_lower:
            return "academic_research"
        if "stackoverflow" in source_lower or "forum" in source_lower:
            return "community_qa"
        return "general_web"

    def _calculate_fact_check_confidence(
        self,
        evidence_items: list[EvidenceItem],
        credibility_scores: dict[str, float],
    ) -> float:
        """Calculate overall confidence for fact-check verification."""
        if not evidence_items:
            return 0.0

        # Weight evidence by source credibility
        weighted_confidence = 0.0
        total_weight = 0.0

        for evidence in evidence_items:
            source_credibility = credibility_scores.get(evidence.source, 0.5)
            weight = evidence.confidence * source_credibility
            weighted_confidence += weight
            total_weight += source_credibility

        return weighted_confidence / total_weight if total_weight > 0 else 0.0

    def _determine_fact_check_result(
        self,
        evidence_items: list[EvidenceItem],
        confidence_score: float,
    ) -> str:
        """Determine overall fact-check result."""
        if not evidence_items:
            return "UNVERIFIED"

        if confidence_score >= 0.8:
            return "VERIFIED"
        if confidence_score >= 0.6:
            return "DISPUTED"
        return "FAILED"

    def _find_pattern_matches(self, pattern: str, text: str) -> list[dict[str, Any]]:
        """Find pattern matches in text with confidence scoring."""
        matches = []
        regex_matches = re.finditer(pattern, text, re.IGNORECASE)

        for match in regex_matches:
            claim_text = match.group(0).strip()

            # Calculate confidence based on pattern specificity and match quality
            confidence = self._calculate_match_confidence(claim_text, pattern)

            matches.append(
                {
                    "claim": claim_text,
                    "pattern": pattern,
                    "confidence": confidence,
                    "type": "pattern_match",
                    "position": match.start(),
                },
            )

        return matches

    def _calculate_match_confidence(self, claim: str, pattern: str) -> float:
        """Calculate confidence score for a pattern match."""
        base_confidence = 0.7

        # Higher confidence for longer, more specific claims
        if len(claim) > 50:
            base_confidence += 0.1
        elif len(claim) < 20:
            base_confidence -= 0.1

        # Higher confidence for specific patterns
        if "according to" in pattern.lower() or "research shows" in pattern.lower():
            base_confidence += 0.1

        return min(1.0, max(0.0, base_confidence))

    def _calculate_pattern_confidence(self, pattern_matches: list[dict[str, Any]]) -> float:
        """Calculate overall confidence from pattern matches."""
        if not pattern_matches:
            return 0.0

        confidences = [match["confidence"] for match in pattern_matches]
        return sum(confidences) / len(confidences)

    async def _verify_numerical_claim(self, claim: str, sources: list[str]) -> dict[str, Any]:
        """Verify a numerical claim against sources."""
        # Mock numerical verification
        # In production, this would cross-reference numerical data

        # Extract numerical value and unit
        numerical_match = re.search(r"(\d+(?:\.\d+)?)\s*(\w+)", claim)
        if numerical_match:
            value = float(numerical_match.group(1))
            unit = numerical_match.group(2)

            # Mock verification result
            return {
                "confidence": 0.8,
                "method": "cross_reference",
                "verified_value": value,
                "verified_unit": unit,
                "sources_checked": len(sources),
                "consensus_found": True,
            }
        return {
            "confidence": 0.3,
            "method": "pattern_extraction_failed",
            "error": "Could not extract numerical value",
        }

    def _calculate_numerical_confidence(self, evidence_items: list[EvidenceItem]) -> float:
        """Calculate confidence for numerical verification."""
        if not evidence_items:
            return 0.0

        confidences = [item.confidence for item in evidence_items]
        return sum(confidences) / len(confidences)

    async def _track_action_performance(self, result: VerificationActionResult) -> None:
        """Track performance of verification actions for optimization."""
        performance_record = {
            "timestamp": time.time(),
            "action_type": result.action_type.value,
            "success": result.success,
            "confidence_score": result.confidence_score,
            "processing_time": result.processing_time,
            "evidence_count": len(result.verification_evidence),
        }

        self.action_performance_history.append(performance_record)

        # Keep only recent history
        if len(self.action_performance_history) > 1000:
            self.action_performance_history = self.action_performance_history[-500:]

    # Placeholder methods for additional verification actions
    async def _execute_citation_validation(self, verification_action: VerificationAction) -> VerificationActionResult:
        """Execute citation validation action."""
        # Mock implementation
        return VerificationActionResult(
            action_type=VerificationActionType.CITATION_VALIDATION,
            verification_query=verification_action.verification_query,
            success=True,
            verification_evidence=[],
            confidence_score=0.8,
            credibility_assessment=0.8,
            fact_check_result="VERIFIED",
            processing_time=0.1,
        )

    async def _execute_context_analysis(self, verification_action: VerificationAction) -> VerificationActionResult:
        """Execute context analysis action."""
        # Mock implementation
        return VerificationActionResult(
            action_type=VerificationActionType.CONTEXT_ANALYSIS,
            verification_query=verification_action.verification_query,
            success=True,
            verification_evidence=[],
            confidence_score=0.7,
            credibility_assessment=0.7,
            fact_check_result="VERIFIED",
            processing_time=0.1,
        )

    async def _execute_contradiction_detection(
        self,
        verification_action: VerificationAction,
    ) -> VerificationActionResult:
        """Execute contradiction detection action."""
        # Mock implementation
        return VerificationActionResult(
            action_type=VerificationActionType.CONTRADICTION_DETECTION,
            verification_query=verification_action.verification_query,
            success=True,
            verification_evidence=[],
            confidence_score=0.8,
            credibility_assessment=0.8,
            fact_check_result="VERIFIED",
            processing_time=0.1,
        )

    async def _execute_expert_consensus_check(
        self,
        verification_action: VerificationAction,
    ) -> VerificationActionResult:
        """Execute expert consensus check action."""
        # Mock implementation
        return VerificationActionResult(
            action_type=VerificationActionType.EXPERT_CONSENSUS_CHECK,
            verification_query=verification_action.verification_query,
            success=True,
            verification_evidence=[],
            confidence_score=0.85,
            credibility_assessment=0.85,
            fact_check_result="VERIFIED",
            processing_time=0.1,
        )

    # Factory and utility methods

    def create_verification_action(
        self,
        strategy: VerificationStrategy,
        verification_query: str,
        target_sources: list[str],
        confidence_threshold: float = 0.7,
    ) -> VerificationAction:
        """Create a verification action based on strategy."""
        strategy_action_mapping = {
            VerificationStrategy.FACTUAL_ACCURACY: VerificationActionType.FACT_CHECK_SEARCH,
            VerificationStrategy.SOURCE_VALIDATION: VerificationActionType.SOURCE_CREDIBILITY_CHECK,
            VerificationStrategy.LOGICAL_CONSISTENCY: VerificationActionType.CONTRADICTION_DETECTION,
            VerificationStrategy.COMPLETENESS_CHECK: VerificationActionType.CONTEXT_ANALYSIS,
            VerificationStrategy.NUMERICAL_PRECISION: VerificationActionType.NUMERICAL_VERIFICATION,
        }

        action_type = strategy_action_mapping.get(strategy, VerificationActionType.FACT_CHECK_SEARCH)
        search_patterns = self.verification_patterns.get("factual_patterns", [])

        return VerificationAction(
            action_type=action_type,
            verification_query=verification_query,
            target_sources=target_sources,
            search_patterns=search_patterns,
            confidence_threshold=confidence_threshold,
        )

    async def get_performance_summary(self) -> dict[str, Any]:
        """Get performance summary of verification actions."""
        if not self.action_performance_history:
            return {"status": "No performance data available"}

        recent_history = self.action_performance_history[-100:]  # Last 100 actions

        # Calculate metrics by action type
        action_type_metrics = {}
        for action_type in VerificationActionType:
            type_actions = [a for a in recent_history if a["action_type"] == action_type.value]
            if type_actions:
                action_type_metrics[action_type.value] = {
                    "count": len(type_actions),
                    "avg_confidence": sum(a["confidence_score"] for a in type_actions) / len(type_actions),
                    "avg_processing_time": sum(a["processing_time"] for a in type_actions) / len(type_actions),
                    "success_rate": sum(1 for a in type_actions if a["success"]) / len(type_actions),
                }

        return {
            "total_actions": len(self.action_performance_history),
            "recent_actions": len(recent_history),
            "action_type_metrics": action_type_metrics,
            "overall_avg_confidence": sum(a["confidence_score"] for a in recent_history) / len(recent_history),
            "overall_avg_processing_time": sum(a["processing_time"] for a in recent_history) / len(recent_history),
            "overall_success_rate": sum(1 for a in recent_history if a["success"]) / len(recent_history),
        }


# Factory function for easy initialization
def create_verification_react_actions(performance_mode: bool = True) -> VerificationReActActions:
    """Create verification action system with specified configuration."""
    return VerificationReActActions(performance_mode=performance_mode)
