#!/usr/bin/env python3
"""
Unit tests for chain_of_verification_technique module.

Tests for Chain of Verification technique including verification types,
strategies, and data structures.
"""


from prompting_framework.chain_of_verification_technique import (
    VerificationPlan,
    VerificationQuestion,
    VerificationResult,
    VerificationStrategy,
    VerificationType,
)


class TestVerificationType:
    """Test VerificationType enum."""

    def test_all_types_defined(self):
        """Verify all expected verification types are defined."""
        expected_types = ["joint", "factored", "two_step"]
        actual_values = [v.value for v in VerificationType]
        for expected in expected_types:
            assert expected in actual_values

    def test_joint_value(self):
        """Joint verification has correct value."""
        assert VerificationType.JOINT.value == "joint"

    def test_factored_value(self):
        """Factored verification has correct value."""
        assert VerificationType.FACTORED.value == "factored"

    def test_two_step_value(self):
        """Two-step verification has correct value."""
        assert VerificationType.TWO_STEP.value == "two_step"


class TestVerificationStrategy:
    """Test VerificationStrategy enum."""

    def test_all_strategies_defined(self):
        """Verify all expected verification strategies are defined."""
        expected_strategies = [
            "factual_accuracy",
            "logical_consistency",
            "source_validation",
            "completeness_check",
        ]
        actual_values = [s.value for s in VerificationStrategy]
        for expected in expected_strategies:
            assert expected in actual_values

    def test_factual_accuracy_value(self):
        """Factual accuracy has correct value."""
        assert VerificationStrategy.FACTUAL_ACCURACY.value == "factual_accuracy"

    def test_logical_consistency_value(self):
        """Logical consistency has correct value."""
        assert VerificationStrategy.LOGICAL_CONSISTENCY.value == "logical_consistency"

    def test_source_validation_value(self):
        """Source validation has correct value."""
        assert VerificationStrategy.SOURCE_VALIDATION.value == "source_validation"

    def test_completeness_check_value(self):
        """Completeness check has correct value."""
        assert VerificationStrategy.COMPLETENESS_CHECK.value == "completeness_check"


class TestVerificationQuestion:
    """Test VerificationQuestion dataclass."""

    def test_create_question(self):
        """Create a verification question."""
        question = VerificationQuestion(
            question="Is this claim accurate?",
            claim_id="claim_1",
            strategy=VerificationStrategy.FACTUAL_ACCURACY,
            expected_answer_type="yes_no",
            context_requirements=["source_documents"],
            verification_sources=["doc1", "doc2"],
            priority="high",
        )
        assert question.question == "Is this claim accurate?"
        assert question.claim_id == "claim_1"
        assert question.strategy == VerificationStrategy.FACTUAL_ACCURACY
        assert question.priority == "high"

    def test_question_with_defaults(self):
        """Create question with default values."""
        question = VerificationQuestion(
            question="Test question?",
            claim_id="claim_2",
            strategy=VerificationStrategy.LOGICAL_CONSISTENCY,
            expected_answer_type="explanation",
        )
        assert question.context_requirements == []
        assert question.verification_sources == []
        assert question.priority == "medium"

    def test_all_priorities(self):
        """Test all priority levels."""
        priorities = ["low", "medium", "high", "critical"]
        for priority in priorities:
            question = VerificationQuestion(
                question="Test?",
                claim_id="test",
                strategy=VerificationStrategy.FACTUAL_ACCURACY,
                expected_answer_type="yes_no",
                priority=priority,
            )
            assert question.priority == priority


class TestVerificationResult:
    """Test VerificationResult dataclass."""

    def test_create_result_passing(self):
        """Create a passing verification result."""
        question = VerificationQuestion(
            question="Is this correct?",
            claim_id="claim_1",
            strategy=VerificationStrategy.FACTUAL_ACCURACY,
            expected_answer_type="yes_no",
        )

        result = VerificationResult(
            question=question,
            answer="Yes, the claim is accurate",
            confidence=0.95,
            sources_used=["source1.pdf"],
            verification_passed=True,
            correction_needed=False,
            identified_issues=[],
            processing_time=1.5,
        )
        assert result.verification_passed is True
        assert result.correction_needed is False
        assert result.confidence == 0.95
        assert len(result.identified_issues) == 0

    def test_create_result_failing(self):
        """Create a failing verification result."""
        question = VerificationQuestion(
            question="Is this correct?",
            claim_id="claim_1",
            strategy=VerificationStrategy.FACTUAL_ACCURACY,
            expected_answer_type="yes_no",
        )

        result = VerificationResult(
            question=question,
            answer="No, inaccuracies found",
            confidence=0.7,
            sources_used=["source1.pdf"],
            verification_passed=False,
            correction_needed=True,
            identified_issues=["Incorrect date", "Missing attribution"],
            processing_time=2.0,
        )
        assert result.verification_passed is False
        assert result.correction_needed is True
        assert len(result.identified_issues) == 2
        assert "Incorrect date" in result.identified_issues

    def test_confidence_range(self):
        """Confidence should be between 0 and 1."""
        question = VerificationQuestion(
            question="Test?",
            claim_id="test",
            strategy=VerificationStrategy.FACTUAL_ACCURACY,
            expected_answer_type="yes_no",
        )

        result = VerificationResult(
            question=question,
            answer="Test answer",
            confidence=0.85,
            sources_used=[],
            verification_passed=True,
            correction_needed=False,
            identified_issues=[],
        )
        assert 0.0 <= result.confidence <= 1.0

    def test_processing_time_non_negative(self):
        """Processing time should be non-negative."""
        question = VerificationQuestion(
            question="Test?",
            claim_id="test",
            strategy=VerificationStrategy.FACTUAL_ACCURACY,
            expected_answer_type="yes_no",
        )

        result = VerificationResult(
            question=question,
            answer="Test",
            confidence=0.8,
            sources_used=[],
            verification_passed=True,
            correction_needed=False,
            identified_issues=[],
            processing_time=0.0,
        )
        assert result.processing_time >= 0


class TestVerificationPlan:
    """Test VerificationPlan dataclass."""

    def test_create_plan(self):
        """Create a verification plan."""
        questions = [
            VerificationQuestion(
                question="Is claim 1 accurate?",
                claim_id="claim_1",
                strategy=VerificationStrategy.FACTUAL_ACCURACY,
                expected_answer_type="yes_no",
            ),
            VerificationQuestion(
                question="Is claim 2 consistent?",
                claim_id="claim_2",
                strategy=VerificationStrategy.LOGICAL_CONSISTENCY,
                expected_answer_type="explanation",
            ),
        ]

        plan = VerificationPlan(
            baseline_response="The system works well",
            identified_claims=[{"id": "claim_1", "text": "System works"}, {"id": "claim_2", "text": "No errors"}],
            verification_questions=questions,
            verification_type=VerificationType.TWO_STEP,
            estimated_processing_time=3.0,
            evidence_requirements=["source_documents", "test_results"],
        )
        assert len(plan.verification_questions) == 2
        assert plan.verification_type == VerificationType.TWO_STEP
        assert plan.estimated_processing_time == 3.0

    def test_plan_with_joint_verification(self):
        """Create plan with joint verification type."""
        plan = VerificationPlan(
            baseline_response="Response",
            identified_claims=[],
            verification_questions=[],
            verification_type=VerificationType.JOINT,
            estimated_processing_time=1.0,
            evidence_requirements=[],
        )
        assert plan.verification_type == VerificationType.JOINT

    def test_plan_with_factored_verification(self):
        """Create plan with factored verification type."""
        plan = VerificationPlan(
            baseline_response="Response",
            identified_claims=[],
            verification_questions=[],
            verification_type=VerificationType.FACTORED,
            estimated_processing_time=2.0,
            evidence_requirements=[],
        )
        assert plan.verification_type == VerificationType.FACTORED


class TestVerificationStrategies:
    """Test different verification strategies."""

    def test_factual_accuracy_strategy(self):
        """Factual accuracy strategy configuration."""
        question = VerificationQuestion(
            question="Verify this fact",
            claim_id="fact_1",
            strategy=VerificationStrategy.FACTUAL_ACCURACY,
            expected_answer_type="yes_no_with_confidence",
            verification_sources=["encyclopedia", "textbook"],
        )
        assert question.strategy == VerificationStrategy.FACTUAL_ACCURACY
        assert "encyclopedia" in question.verification_sources

    def test_logical_consistency_strategy(self):
        """Logical consistency strategy configuration."""
        question = VerificationQuestion(
            question="Check logic",
            claim_id="logic_1",
            strategy=VerificationStrategy.LOGICAL_CONSISTENCY,
            expected_answer_type="explanation",
        )
        assert question.strategy == VerificationStrategy.LOGICAL_CONSISTENCY

    def test_source_validation_strategy(self):
        """Source validation strategy configuration."""
        question = VerificationQuestion(
            question="Validate sources",
            claim_id="source_1",
            strategy=VerificationStrategy.SOURCE_VALIDATION,
            expected_answer_type="source_list",
            verification_sources=["original_source"],
        )
        assert question.strategy == VerificationStrategy.SOURCE_VALIDATION

    def test_completeness_check_strategy(self):
        """Completeness check strategy configuration."""
        question = VerificationQuestion(
            question="Check completeness",
            claim_id="complete_1",
            strategy=VerificationStrategy.COMPLETENESS_CHECK,
            expected_answer_type="checklist",
            context_requirements=["requirements_doc"],
        )
        assert question.strategy == VerificationStrategy.COMPLETENESS_CHECK
        assert "requirements_doc" in question.context_requirements


class TestVerificationResultAnalysis:
    """Test verification result analysis."""

    def test_high_confidence_pass(self):
        """High confidence results should pass."""
        question = VerificationQuestion(
            question="Test?",
            claim_id="test",
            strategy=VerificationStrategy.FACTUAL_ACCURACY,
            expected_answer_type="yes_no",
        )

        result = VerificationResult(
            question=question,
            answer="Yes",
            confidence=0.95,
            sources_used=["reliable_source"],
            verification_passed=True,
            correction_needed=False,
            identified_issues=[],
        )
        assert result.confidence > 0.9
        assert result.verification_passed is True

    def test_low_confidence_fail(self):
        """Low confidence results might fail verification."""
        question = VerificationQuestion(
            question="Test?",
            claim_id="test",
            strategy=VerificationStrategy.FACTUAL_ACCURACY,
            expected_answer_type="yes_no",
        )

        result = VerificationResult(
            question=question,
            answer="Maybe",
            confidence=0.4,
            sources_used=[],
            verification_passed=False,
            correction_needed=True,
            identified_issues=["Uncertain claim"],
        )
        assert result.confidence < 0.5
        assert result.verification_passed is False

    def test_result_with_multiple_issues(self):
        """Result with multiple identified issues."""
        question = VerificationQuestion(
            question="Verify complex claim",
            claim_id="complex",
            strategy=VerificationStrategy.COMPLETENESS_CHECK,
            expected_answer_type="checklist",
        )

        result = VerificationResult(
            question=question,
            answer="Multiple issues found",
            confidence=0.3,
            sources_used=[],
            verification_passed=False,
            correction_needed=True,
            identified_issues=["Missing section A", "Incomplete data B", "No reference C"],
            processing_time=5.0,
        )
        assert len(result.identified_issues) == 3


class TestVerificationPlanExecution:
    """Test verification plan execution scenarios."""

    def test_simple_plan_single_question(self):
        """Simple plan with single verification question."""
        questions = [
            VerificationQuestion(
                question="Is this correct?",
                claim_id="claim_1",
                strategy=VerificationStrategy.FACTUAL_ACCURACY,
                expected_answer_type="yes_no",
                priority="high",
            )
        ]

        plan = VerificationPlan(
            baseline_response="Simple response",
            identified_claims=[{"id": "claim_1", "text": "Single claim"}],
            verification_questions=questions,
            verification_type=VerificationType.JOINT,
            estimated_processing_time=1.0,
            evidence_requirements=[],
        )
        assert len(plan.verification_questions) == 1

    def test_complex_plan_multiple_questions(self):
        """Complex plan with multiple verification questions."""
        questions = [
            VerificationQuestion(
                question=f"Verify claim {i}?",
                claim_id=f"claim_{i}",
                strategy=VerificationStrategy.FACTUAL_ACCURACY if i % 2 == 0 else VerificationStrategy.LOGICAL_CONSISTENCY,
                expected_answer_type="yes_no",
                priority="high" if i < 3 else "medium",
            )
            for i in range(1, 6)
        ]

        plan = VerificationPlan(
            baseline_response="Complex response with multiple claims",
            identified_claims=[{"id": f"claim_{i}", "text": f"Claim {i}"} for i in range(1, 6)],
            verification_questions=questions,
            verification_type=VerificationType.FACTORED,
            estimated_processing_time=10.0,
            evidence_requirements=["sources", "references"],
        )
        assert len(plan.verification_questions) == 5
        assert plan.estimated_processing_time == 10.0


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_empty_verification_plan(self):
        """Handle plan with no verification questions."""
        plan = VerificationPlan(
            baseline_response="No claims to verify",
            identified_claims=[],
            verification_questions=[],
            verification_type=VerificationType.JOINT,
            estimated_processing_time=0.0,
            evidence_requirements=[],
        )
        assert len(plan.verification_questions) == 0

    def test_verification_result_no_issues(self):
        """Result with no identified issues."""
        question = VerificationQuestion(
            question="Perfect claim?",
            claim_id="perfect",
            strategy=VerificationStrategy.FACTUAL_ACCURACY,
            expected_answer_type="yes_no",
        )

        result = VerificationResult(
            question=question,
            answer="Yes, perfect",
            confidence=1.0,
            sources_used=["authoritative_source"],
            verification_passed=True,
            correction_needed=False,
            identified_issues=[],
        )
        assert len(result.identified_issues) == 0

    def test_verification_result_zero_processing_time(self):
        """Handle zero processing time (cached result)."""
        question = VerificationQuestion(
            question="Cached verification?",
            claim_id="cached",
            strategy=VerificationStrategy.FACTUAL_ACCURACY,
            expected_answer_type="yes_no",
        )

        result = VerificationResult(
            question=question,
            answer="From cache",
            confidence=0.9,
            sources_used=[],
            verification_passed=True,
            correction_needed=False,
            identified_issues=[],
            processing_time=0.0,
        )
        assert result.processing_time == 0.0

    def test_question_no_sources(self):
        """Question with no verification sources."""
        question = VerificationQuestion(
            question="Logic check",
            claim_id="logic",
            strategy=VerificationStrategy.LOGICAL_CONSISTENCY,
            expected_answer_type="explanation",
            verification_sources=[],
        )
        assert len(question.verification_sources) == 0

    def test_result_no_sources_used(self):
        """Result with no sources used."""
        question = VerificationQuestion(
            question="Test?",
            claim_id="test",
            strategy=VerificationStrategy.LOGICAL_CONSISTENCY,
            expected_answer_type="explanation",
        )

        result = VerificationResult(
            question=question,
            answer="Logical analysis",
            confidence=0.8,
            sources_used=[],
            verification_passed=True,
            correction_needed=False,
            identified_issues=[],
        )
        assert len(result.sources_used) == 0
