#!/usr/bin/env python3
"""
Unit tests for socratic_prompting_technique module.

Tests for Socratic prompting technique implementation.
"""


from prompting_framework.socratic_prompting_technique import (
    SocraticDialogue,
    SocraticQuestion,
    SocraticQuestionType,
    SocraticStrategy,
)


class TestSocraticQuestionType:
    """Test SocraticQuestionType enum."""

    def test_all_types_defined(self):
        """Verify all expected question types are defined."""
        expected_types = [
            "clarification",
            "assumption_probe",
            "evidence_request",
            "implication_exploration",
            "counter_example",
            "perspective_shift",
            "synthesis",
        ]
        actual_values = [t.value for t in SocraticQuestionType]
        for expected in expected_types:
            assert expected in actual_values


class TestSocraticQuestion:
    """Test SocraticQuestion dataclass."""

    def test_create_question(self):
        """Create a Socratic question."""
        question = SocraticQuestion(
            question_text="What do you mean by that?",
            question_type=SocraticQuestionType.CLARIFICATION,
            context="User made an ambiguous statement",
            expected_outcome="User provides clarification",
            follow_up_questions=["Can you give an example?"],
        )
        assert question.question_type == SocraticQuestionType.CLARIFICATION
        assert "ambiguous" in question.context

    def test_question_with_defaults(self):
        """Create question with default values."""
        question = SocraticQuestion(
            question_text="Why do you think that?",
            question_type=SocraticQuestionType.ASSUMPTION_PROBE,
            context="Testing assumptions",
            expected_outcome="User reveals assumptions",
        )
        assert question.follow_up_questions == []

    def test_all_question_types(self):
        """Create questions for all types."""
        types = list(SocraticQuestionType)
        for qtype in types:
            question = SocraticQuestion(
                question_text=f"Question for {qtype.value}?",
                question_type=qtype,
                context="Test context",
                expected_outcome="Test outcome",
            )
            assert question.question_type == qtype


class TestSocraticDialogue:
    """Test SocraticDialogue dataclass."""

    def test_create_dialogue(self):
        """Create a Socratic dialogue."""
        questions = [
            SocraticQuestion(
                question_text="What is your goal?",
                question_type=SocraticQuestionType.CLARIFICATION,
                context="Initial",
                expected_outcome="Clear goal",
            )
        ]

        dialogue = SocraticDialogue(
            initial_prompt="I want to improve my code",
            questions_asked=questions,
            user_responses=["To make it faster"],
            current_understanding="User wants performance optimization",
            next_question_type=SocraticQuestionType.EVIDENCE_REQUEST,
            dialogue_depth=1,
        )
        assert dialogue.dialogue_depth == 1
        assert len(dialogue.questions_asked) == 1

    def test_dialogue_progression(self):
        """Test dialogue progression through multiple turns."""
        questions = [
            SocraticQuestion(
                question_text=f"Question {i}?",
                question_type=SocraticQuestionType.CLARIFICATION,
                context=f"Turn {i}",
                expected_outcome=f"Response {i}",
            )
            for i in range(1, 4)
        ]

        dialogue = SocraticDialogue(
            initial_prompt="Help me understand",
            questions_asked=questions,
            user_responses=[f"Response {i}" for i in range(1, 4)],
            current_understanding="Deep understanding",
            next_question_type=SocraticQuestionType.SYNTHESIS,
            dialogue_depth=3,
        )
        assert dialogue.dialogue_depth == 3
        assert len(dialogue.user_responses) == 3


class TestSocraticStrategy:
    """Test SocraticStrategy enum."""

    def test_all_strategies_defined(self):
        """Verify all expected strategies are defined."""
        expected_strategies = [
            "guided_discovery",
            "critical_examination",
            "hypothetical_exploration",
            "analogical_reasoning",
        ]
        actual_values = [s.value for s in SocraticStrategy]
        for expected in expected_strategies:
            assert expected in actual_values


class TestSocraticQuestionTypes:
    """Test various Socratic question types."""

    def test_clarification_question(self):
        """Clarification questions seek understanding."""
        question = SocraticQuestion(
            question_text="Could you clarify what you mean?",
            question_type=SocraticQuestionType.CLARIFICATION,
            context="Ambiguous term detected",
            expected_outcome="Precise definition",
        )
        assert question.question_type == SocraticQuestionType.CLARIFICATION

    def test_assumption_probe_question(self):
        """Assumption probe questions uncover beliefs."""
        question = SocraticQuestion(
            question_text="What assumptions are you making?",
            question_type=SocraticQuestionType.ASSUMPTION_PROBE,
            context="Implicit assumptions detected",
            expected_outcome="Explicit assumptions",
        )
        assert question.question_type == SocraticQuestionType.ASSUMPTION_PROBE

    def test_evidence_request_question(self):
        """Evidence request questions ask for support."""
        question = SocraticQuestion(
            question_text="What evidence supports this?",
            question_type=SocraticQuestionType.EVIDENCE_REQUEST,
            context="Claim made without support",
            expected_outcome="Supporting evidence",
        )
        assert question.question_type == SocraticQuestionType.EVIDENCE_REQUEST

    def test_implication_exploration_question(self):
        """Implication exploration questions examine consequences."""
        question = SocraticQuestion(
            question_text="What would follow from this?",
            question_type=SocraticQuestionType.IMPLICATION_EXPLORATION,
            context="Exploring consequences",
            expected_outcome="Implications identified",
        )
        assert question.question_type == SocraticQuestionType.IMPLICATION_EXPLORATION

    def test_counter_example_question(self):
        """Counter-example questions test generalizations."""
        question = SocraticQuestion(
            question_text="Are there cases where this wouldn't hold?",
            question_type=SocraticQuestionType.COUNTER_EXAMPLE,
            context="Overgeneralization detected",
            expected_outcome="Boundary conditions",
        )
        assert question.question_type == SocraticQuestionType.COUNTER_EXAMPLE

    def test_perspective_shift_question(self):
        """Perspective shift questions encourage alternative views."""
        question = SocraticQuestion(
            question_text="How might someone else see this?",
            question_type=SocraticQuestionType.PERSPECTIVE_SHIFT,
            context="Limited perspective",
            expected_outcome="Alternative viewpoint",
        )
        assert question.question_type == SocraticQuestionType.PERSPECTIVE_SHIFT

    def test_synthesis_question(self):
        """Synthesis questions integrate ideas."""
        question = SocraticQuestion(
            question_text="How do these ideas connect?",
            question_type=SocraticQuestionType.SYNTHESIS,
            context="Multiple concepts present",
            expected_outcome="Integrated understanding",
        )
        assert question.question_type == SocraticQuestionType.SYNTHESIS


class TestSocraticDialogueStates:
    """Test dialogue states and progression."""

    def test_initial_dialogue_state(self):
        """Initial dialogue has minimal depth."""
        dialogue = SocraticDialogue(
            initial_prompt="Start",
            questions_asked=[],
            user_responses=[],
            current_understanding="",
            next_question_type=SocraticQuestionType.CLARIFICATION,
            dialogue_depth=0,
        )
        assert dialogue.dialogue_depth == 0
        assert len(dialogue.questions_asked) == 0

    def test_deep_dialogue_state(self):
        """Deep dialogue has accumulated many exchanges."""
        questions = [
            SocraticQuestion(
                question_text=f"Q{i}",
                question_type=SocraticQuestionType.CLARIFICATION,
                context="",
                expected_outcome="",
            )
            for i in range(10)
        ]

        dialogue = SocraticDialogue(
            initial_prompt="Complex topic",
            questions_asked=questions,
            user_responses=[f"A{i}" for i in range(10)],
            current_understanding="Deep insight",
            next_question_type=SocraticQuestionType.SYNTHESIS,
            dialogue_depth=10,
        )
        assert dialogue.dialogue_depth == 10


class TestSocraticStrategies:
    """Test Socratic dialogue strategies."""

    def test_guided_discovery_strategy(self):
        """Guided discovery strategy value."""
        assert SocraticStrategy.GUIDED_DISCOVERY.value == "guided_discovery"

    def test_critical_examination_strategy(self):
        """Critical examination strategy value."""
        assert SocraticStrategy.CRITICAL_EXAMINATION.value == "critical_examination"

    def test_hypothetical_exploration_strategy(self):
        """Hypothetical exploration strategy value."""
        assert SocraticStrategy.HYPOTHETICAL_EXPLORATION.value == "hypothetical_exploration"

    def test_analogical_reasoning_strategy(self):
        """Analogical reasoning strategy value."""
        assert SocraticStrategy.ANALOGICAL_REASONING.value == "analogical_reasoning"


class TestEdgeCases:
    """Test edge cases for Socratic prompting."""

    def test_empty_dialogue(self):
        """Handle dialogue with no questions yet."""
        dialogue = SocraticDialogue(
            initial_prompt="Hello",
            questions_asked=[],
            user_responses=[],
            current_understanding="",
            next_question_type=SocraticQuestionType.CLARIFICATION,
            dialogue_depth=0,
        )
        assert dialogue.dialogue_depth == 0
        assert dialogue.current_understanding == ""

    def test_single_exchange_dialogue(self):
        """Handle dialogue with single exchange."""
        question = SocraticQuestion(
            question_text="What do you mean?",
            question_type=SocraticQuestionType.CLARIFICATION,
            context="",
            expected_outcome="",
        )

        dialogue = SocraticDialogue(
            initial_prompt="I need help",
            questions_asked=[question],
            user_responses=["I need to fix a bug"],
            current_understanding="User has a bug to fix",
            next_question_type=SocraticQuestionType.EVIDENCE_REQUEST,
            dialogue_depth=1,
        )
        assert len(dialogue.questions_asked) == 1

    def test_question_with_multiple_followups(self):
        """Handle question with multiple follow-ups."""
        question = SocraticQuestion(
            question_text="Can you explain?",
            question_type=SocraticQuestionType.CLARIFICATION,
            context="",
            expected_outcome="",
            follow_up_questions=[
                "What specifically?",
                "Can you give an example?",
                "How does it work?",
            ],
        )
        assert len(question.follow_up_questions) == 3

    def test_dialogue_with_no_user_response_yet(self):
        """Handle dialogue before user responds."""
        question = SocraticQuestion(
            question_text="What is your question?",
            question_type=SocraticQuestionType.CLARIFICATION,
            context="",
            expected_outcome="",
        )

        dialogue = SocraticDialogue(
            initial_prompt="I have a question",
            questions_asked=[question],
            user_responses=[],  # No response yet
            current_understanding="Waiting for response",
            next_question_type=SocraticQuestionType.CLARIFICATION,
            dialogue_depth=1,
        )
        assert len(dialogue.user_responses) == 0
        assert dialogue.current_understanding == "Waiting for response"
