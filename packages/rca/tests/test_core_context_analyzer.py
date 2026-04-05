"""Tests for core.context_analyzer module.

Tests for context analysis and extraction functionality.
"""



from rca.core.context_analyzer import (
    ContextAnalyzer,
)


class TestContextAnalyzerInit:
    """Test ContextAnalyzer initialization."""

    def test_analyzer_creation(self):
        """ContextAnalyzer can be created."""
        analyzer = ContextAnalyzer()

        assert analyzer is not None


class TestAnalyzeContext:
    """Test analyze_context method."""

    def test_analyze_context_basic(self):
        """Basic context analysis works."""
        analyzer = ContextAnalyzer()
        problem_description = "The application crashes when processing user input"

        context = analyzer.analyze_context(problem_description)

        assert context is not None
        assert "problem_type" in context
        assert "complexity_level" in context
        assert "confidence_score" in context
        assert "recommended_strategy" in context

    def test_analyze_context_with_files(self):
        """Context analysis with target files works."""
        analyzer = ContextAnalyzer()
        problem_description = "Performance issue in data processing"
        target_files = ["src/processor.py", "src/handler.py"]

        context = analyzer.analyze_context(problem_description, target_files)

        assert context is not None
        assert context["scope"] in ["specific_file", "module", "system"]


class TestProblemClassifier:
    """Test ProblemClassifier class."""

    def test_classify_bug(self):
        """Bug classification works."""
        from rca.core.context_analyzer import ProblemClassifier

        classifier = ProblemClassifier()
        problem_type, confidence = classifier.classify("The application crashes with an error")

        assert problem_type == "bug"
        assert confidence > 0

    def test_classify_performance(self):
        """Performance classification works."""
        from rca.core.context_analyzer import ProblemClassifier

        classifier = ProblemClassifier()
        problem_type, confidence = classifier.classify("slow performance latency timeout bottleneck")

        assert problem_type == "performance"
        assert confidence > 0

    def test_classify_empty(self):
        """Empty description returns unknown."""
        from rca.core.context_analyzer import ProblemClassifier

        classifier = ProblemClassifier()
        problem_type, confidence = classifier.classify("")

        assert problem_type == "unknown"
        assert confidence == 0.0


class TestComplexityAssessor:
    """Test ComplexityAssessor class."""

    def test_assess_simple(self):
        """Simple complexity assessment works."""
        from rca.core.context_analyzer import ComplexityAssessor

        assessor = ComplexityAssessor()
        complexity = assessor.assess("A simple bug in a single function")

        assert complexity == "simple"

    def test_assess_with_files(self):
        """Complexity assessment with files works."""
        from rca.core.context_analyzer import ComplexityAssessor

        assessor = ComplexityAssessor()
        complexity = assessor.assess("Problem with multiple files", ["file1.py", "file2.py", "file3.py"])

        assert complexity in ["simple", "moderate", "complex"]


class TestSecurityDetector:
    """Test SecurityDetector class."""

    def test_detect_security_issue(self):
        """Security issue detection works."""
        from rca.core.context_analyzer import SecurityDetector

        detector = SecurityDetector()
        result = detector.detect("SQL injection vulnerability in login form")

        assert result is True

    def test_no_security_issue(self):
        """No security issue returns False."""
        from rca.core.context_analyzer import SecurityDetector

        detector = SecurityDetector()
        result = detector.detect("The application is slow")

        assert result is False


class TestPerformanceDetector:
    """Test PerformanceDetector class."""

    def test_detect_performance_issue(self):
        """Performance issue detection works."""
        from rca.core.context_analyzer import PerformanceDetector

        detector = PerformanceDetector()
        result = detector.detect("The application has high memory usage and is slow")

        assert result is True

    def test_no_performance_issue(self):
        """No performance issue returns False."""
        from rca.core.context_analyzer import PerformanceDetector

        detector = PerformanceDetector()
        result = detector.detect("Security vulnerability in authentication")

        assert result is False


class TestGetAnalysisSummary:
    """Test get_analysis_summary method."""

    def test_generate_summary(self):
        """Analysis summary can be generated."""
        analyzer = ContextAnalyzer()
        context = {
            "problem_type": "bug",
            "complexity_level": "simple",
            "recommended_strategy": "systematic",
            "confidence_score": 0.8
        }

        summary = analyzer.get_analysis_summary(context)

        assert summary is not None
        assert len(summary) > 0
        assert "bug" in summary.lower()


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_problem_description(self):
        """Empty problem description is handled."""
        analyzer = ContextAnalyzer()

        context = analyzer.analyze_context("")

        assert context is not None
        assert context["problem_type"] == "unknown"

    def test_malformed_stack_trace(self):
        """Malformed stack trace is handled."""
        analyzer = ContextAnalyzer()

        analysis = analyzer.analyze_stack_trace("This is not a stack trace")

        assert analysis is not None
        assert "frames" in analysis or "error" in analysis

    def test_empty_stack_trace(self):
        """Empty stack trace is handled."""
        analyzer = ContextAnalyzer()

        analysis = analyzer.analyze_stack_trace("")

        assert analysis is not None

    def test_reconstruct_empty_call_chain(self):
        """Empty call chain reconstruction works."""
        analyzer = ContextAnalyzer()

        call_chain = analyzer.reconstruct_call_chain("")

        assert call_chain is not None
        assert len(call_chain) == 0
