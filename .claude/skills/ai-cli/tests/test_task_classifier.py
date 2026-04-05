"""Unit tests for task_classifier module.

Tests task classification accuracy, confidence scoring, and edge cases.
"""

from task_classifier import TaskType, classify_task


class TestTaskClassification:
    """Test task classification functionality."""

    def test_code_review_classification(self):
        """Test code review queries are classified correctly."""
        result = classify_task("review this code for bugs")
        assert result.task_type == TaskType.CODE_REVIEW
        assert result.confidence > 0
        assert "review" in result.matched_keywords

    def test_planning_classification(self):
        """Test planning queries are classified correctly."""
        result = classify_task("create a plan for implementing X")
        assert result.task_type == TaskType.PLANNING
        assert result.confidence > 0

    def test_brainstorm_classification(self):
        """Test brainstorm queries are classified correctly."""
        result = classify_task("brainstorm ideas for feature Y")
        assert result.task_type == TaskType.BRAINSTORM
        assert result.confidence > 0

    def test_research_classification(self):
        """Test research queries are classified correctly."""
        result = classify_task("research best practices for Z")
        assert result.task_type == TaskType.RESEARCH
        assert result.confidence > 0

    def test_debug_classification(self):
        """Test debug queries are classified correctly."""
        result = classify_task("debug this error in module.py")
        assert result.task_type == TaskType.DEBUG
        assert result.confidence > 0

    def test_refactor_classification(self):
        """Test refactor queries are classified correctly."""
        result = classify_task("refactor this function for clarity")
        assert result.task_type == TaskType.REFACTOR
        assert result.confidence > 0

    def test_general_classification(self):
        """Test general queries (no keywords) default to general."""
        result = classify_task("hello world")
        assert result.task_type == TaskType.GENERAL
        # General queries have 0.0 confidence when no keywords match
        assert result.confidence == 0.0
        assert len(result.matched_keywords) == 0


class TestConfidenceScoring:
    """Test confidence scoring algorithm."""

    def test_single_keyword_20_percent(self):
        """Test single keyword match gives 20% confidence."""
        result = classify_task("review")
        assert result.confidence == 0.2

    def test_two_keywords_40_percent(self):
        """Test two keyword matches give 40% confidence."""
        result = classify_task("review and analyze this code")
        # "review" and "analyze" both match code_review
        assert result.task_type == TaskType.CODE_REVIEW
        assert result.confidence == 0.4
        assert len(result.matched_keywords) == 2

    def test_five_keywords_100_percent(self):
        """Test five+ keyword matches cap at 100% confidence."""
        # "debug error bug failure issue" - all debug keywords
        result = classify_task("debug error bug failure issue")
        assert result.confidence == 1.0

    def test_confidence_never_exceeds_1(self):
        """Test confidence is capped at 1.0 (100%)."""
        result = classify_task("review analyze audit assess evaluate code")
        assert result.confidence == 1.0  # Should cap, not exceed


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_empty_query(self):
        """Test empty query returns general type."""
        result = classify_task("")
        assert result.task_type == TaskType.GENERAL
        assert result.confidence == 0.0

    def test_case_insensitive(self):
        """Test classification is case-insensitive."""
        result_upper = classify_task("REVIEW THIS CODE")
        result_lower = classify_task("review this code")
        assert result_upper.task_type == result_lower.task_type
        assert result_upper.confidence == result_lower.confidence

    def test_multiple_task_types(self):
        """Test query with keywords from multiple task types."""
        # "review plan" has both review (code_review) and plan (planning)
        result = classify_task("review the implementation plan")
        # Should return the highest-scoring type
        assert result.task_type in [TaskType.CODE_REVIEW, TaskType.PLANNING]
        assert result.confidence > 0

    def test_long_query(self):
        """Test long query is handled correctly."""
        long_query = " ".join(["debug"] * 100)
        result = classify_task(long_query)
        assert result.task_type == TaskType.DEBUG

    def test_special_characters(self):
        """Test query with special characters."""
        result = classify_task("debug: error?! @#$%")
        assert result.task_type == TaskType.DEBUG


class TestClassificationResult:
    """Test ClassificationResult data structure."""

    def test_result_has_all_fields(self):
        """Test result contains all expected fields."""
        result = classify_task("test query")
        assert hasattr(result, "task_type")
        assert hasattr(result, "confidence")
        assert hasattr(result, "matched_keywords")
        assert hasattr(result, "reasoning")

    def test_reasoning_is_string(self):
        """Test reasoning field is a string."""
        result = classify_task("test")
        assert isinstance(result.reasoning, str)
        assert len(result.reasoning) > 0

    def test_matched_keywords_is_list(self):
        """Test matched_keywords is a list."""
        result = classify_task("test")
        assert isinstance(result.matched_keywords, list)


class TestTaskPatterns:
    """Test that TASK_PATTERNS cover expected keywords."""

    def test_code_review_keywords(self):
        """Test code review pattern has expected keywords."""
        from task_classifier import TASK_PATTERNS

        keywords = TASK_PATTERNS[TaskType.CODE_REVIEW]
        assert "review" in keywords
        assert "analyze" in keywords
        assert "audit" in keywords

    def test_all_task_types_have_patterns(self):
        """Test all task types have keyword patterns defined."""
        from task_classifier import TASK_PATTERNS

        for task_type in TaskType:
            if task_type == TaskType.GENERAL:
                continue  # GENERAL has no patterns by design
            assert task_type in TASK_PATTERNS
            assert len(TASK_PATTERNS[task_type]) > 0
