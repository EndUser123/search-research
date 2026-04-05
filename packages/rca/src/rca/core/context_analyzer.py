"""
Context Analyzer for RCA Enhancement

Intelligent analysis of problem descriptions to determine optimal RCA approach.
Provides automatic problem classification, complexity assessment, and strategy recommendation.
"""
from __future__ import annotations

import re
import time
from datetime import datetime


class ProblemClassifier:
    """
    Problem classification with keyword and pattern analysis.

    This class analyzes problem descriptions to classify them into categories
    such as bug, performance, security, or architectural issues. It uses both
    keyword matching and regex pattern matching with weighted scoring.
    """

    # Default confidence threshold for classification
    CONFIDENCE_THRESHOLD = 0.3

    # Scoring weights
    KEYWORD_WEIGHT = 0.4
    PATTERN_WEIGHT = 0.6

    def __init__(self) -> None:
        """Initialize the ProblemClassifier with default patterns."""
        self.patterns: dict[str, dict[str, list[str]]] = {
            "bug": {
                "keywords": ["crash", "error", "exception", "bug", "broken", "fail", "incorrect", "wrong", "invalid"],
                "patterns": [
                    r"\b(crashes?|crashed?)\b",
                    r"\b(error|exception|failure)\b",
                    r"\b(broken|not working|doesn\'t work)\b",
                    r"\b(incorrect|wrong|invalid)\b"
                ]
            },
            "performance": {
                "keywords": ["slow", "performance", "latency", "timeout", "bottleneck", "delay", "lag"],
                "patterns": [
                    r"\b(slow|slower|slowly)\b",
                    r"\b(performance|optimization)\b",
                    r"\b(timeout|time out)\b",
                    r"\b(bottleneck|constraint)\b"
                ]
            },
            "security": {
                "keywords": ["security", "vulnerability", "attack", "breach", "injection", "auth", "permission"],
                "patterns": [
                    r"\b(security vulnerability|security issue)\b",
                    r"\b(sql injection|xss|csrf)\b",
                    r"\b(unauthorized|forbidden|permission)\b",
                    r"\b(attack|breach|exploit)\b"
                ]
            },
            "architectural": {
                "keywords": ["architecture", "design", "structure", "refactor", "pattern", "scalability"],
                "patterns": [
                    r"\b(architecture|design pattern)\b",
                    r"\b(structure|organization)\b",
                    r"\b(refactor|restructure)\b",
                    r"\b(scalability|scalable)\b"
                ]
            }
        }

    def classify(self, problem_description: str) -> tuple[str, float]:
        """
        Classify problem type with confidence score.

        Analyzes the problem description using keyword and pattern matching
        to determine the most likely problem category and confidence score.

        Args:
            problem_description: Text description of the problem to classify

        Returns:
            A tuple of (problem_type, confidence_score) where:
            - problem_type: One of 'bug', 'performance', 'security', 'architectural', or 'unknown'
            - confidence_score: Float between 0.0 and 1.0 indicating classification confidence

        Examples:
            >>> classifier = ProblemClassifier()
            >>> classifier.classify("The application crashes with an error")
            ('bug', 0.35)
        """
        if not problem_description:
            return "unknown", 0.0

        description_lower = problem_description.lower()
        scores: dict[str, float] = {}

        for problem_type, config in self.patterns.items():
            score = self._calculate_type_score(description_lower, config)
            scores[problem_type] = score

        # Find the best match
        best_type = max(scores, key=scores.get)
        confidence = scores[best_type]

        # Only return classification if confidence is high enough
        if confidence < self.CONFIDENCE_THRESHOLD:
            return "unknown", confidence

        return best_type, confidence

    def _calculate_type_score(self, description_lower: str, config: dict[str, list[str]]) -> float:
        """
        Calculate score for a specific problem type.

        Args:
            description_lower: Lowercase problem description
            config: Configuration dict with 'keywords' and 'patterns' keys

        Returns:
            Score between 0.0 and 1.0
        """
        score = 0.0

        # Keyword matching (40% weight)
        keyword_matches = sum(1 for keyword in config["keywords"] if keyword in description_lower)
        keyword_score = (keyword_matches / len(config["keywords"])) * self.KEYWORD_WEIGHT
        score += keyword_score

        # Pattern matching (60% weight)
        pattern_matches = sum(
            1 for pattern in config["patterns"]
            if re.search(pattern, description_lower, re.IGNORECASE)
        )
        pattern_score = (pattern_matches / len(config["patterns"])) * self.PATTERN_WEIGHT
        score += pattern_score

        return score


class ComplexityAssessor:
    """
    Complexity assessment based on description and scope.

    Evaluates problem complexity by analyzing description keywords and
    the number of target files involved in the issue.
    """

    # File count thresholds for complexity assessment
    SINGLE_FILE_THRESHOLD = 1
    FEW_FILES_THRESHOLD = 3
    MODERATE_FILES_THRESHOLD = 10

    def __init__(self) -> None:
        """Initialize the ComplexityAssessor with default indicators."""
        self.complexity_indicators: dict[str, list[str]] = {
            "simple": ["single", "simple", "basic", "minor", "small", "one", "specific"],
            "moderate": ["multiple", "several", "some", "various", "different", "related"],
            "complex": ["complex", "distributed", "multiple systems", "interconnected", "cascading", "systemic"]
        }

    def assess(self, problem_description: str, target_files: list[str] | None = None) -> str:
        """
        Assess complexity level of the problem.

        Evaluates complexity based on keyword indicators in the description
        and the number of target files involved.

        Args:
            problem_description: Text description of the problem
            target_files: Optional list of file paths involved in the problem

        Returns:
            One of 'simple', 'moderate', 'complex', or 'unknown'

        Examples:
            >>> assessor = ComplexityAssessor()
            >>> assessor.assess("A simple bug in one function")
            'simple'
        """
        if not problem_description:
            return "unknown"

        description_lower = problem_description.lower()
        complexity_scores: dict[str, int] = {"simple": 0, "moderate": 0, "complex": 0}

        # Check complexity indicators
        for level, indicators in self.complexity_indicators.items():
            complexity_scores[level] = sum(
                1 for indicator in indicators
                if indicator in description_lower
            )

        # Assess file count complexity
        if target_files:
            self._assess_file_complexity(len(target_files), complexity_scores)

        # Determine complexity level
        return self._determine_complexity_level(complexity_scores)

    def _assess_file_complexity(self, file_count: int, scores: dict[str, int]) -> None:
        """
        Adjust complexity scores based on file count.

        Args:
            file_count: Number of files involved
            scores: Complexity scores dict to modify in place
        """
        if file_count == self.SINGLE_FILE_THRESHOLD:
            scores["simple"] += 2
        elif file_count <= self.FEW_FILES_THRESHOLD:
            scores["moderate"] += 2
        elif file_count <= self.MODERATE_FILES_THRESHOLD:
            scores["moderate"] += 1
        else:
            scores["complex"] += 2

    def _determine_complexity_level(self, scores: dict[str, int]) -> str:
        """
        Determine final complexity level from scores.

        Args:
            scores: Dictionary with complexity level scores

        Returns:
            Complexity level string
        """
        if scores["complex"] > 0:
            return "complex"
        if scores["moderate"] > 0:
            return "moderate"
        if scores["simple"] > 0:
            return "simple"
        return "moderate"  # Default to moderate


class SecurityDetector:
    """
    Security concern detection in problem descriptions.

    Identifies potential security issues by analyzing problem descriptions
    for security-related keywords and patterns.
    """

    def __init__(self) -> None:
        """Initialize the SecurityDetector with security indicators."""
        self.security_keywords: list[str] = [
            "security", "vulnerability", "attack", "breach", "injection",
            "exploit", "malicious", "unauthorized", "forbidden", "csrf", "xss",
            "authentication", "authorization", "permission", "access control",
            "encryption", "certificate", "ssl", "tls", "hash", "password"
        ]

        self.security_patterns: list[str] = [
            r"\b(sql injection|command injection)\b",
            r"\b(cross[-\s]?site scripting|xss)\b",
            r"\b(cross[-\s]?site request forgery|csrf)\b",
            r"\b(buffer overflow|heap overflow)\b",
            r"\b(denial of service|dos|ddos)\b",
            r"\b(man[-\s]?in[-\s]?the[-\s]?middle)\b"
        ]

    def detect(self, problem_description: str) -> bool:
        """
        Detect if problem has security implications.

        Args:
            problem_description: Text description of the problem

        Returns:
            True if security concerns are detected, False otherwise

        Examples:
            >>> detector = SecurityDetector()
            >>> detector.detect("SQL injection vulnerability in login form")
            True
        """
        if not problem_description:
            return False

        description_lower = problem_description.lower()

        # Keyword detection
        keyword_match = any(
            keyword in description_lower
            for keyword in self.security_keywords
        )

        # Pattern detection
        pattern_match = any(
            re.search(pattern, description_lower, re.IGNORECASE)
            for pattern in self.security_patterns
        )

        return keyword_match or pattern_match


class PerformanceDetector:
    """
    Performance issue detection in problem descriptions.

    Identifies potential performance problems by analyzing descriptions
    for performance-related keywords and patterns.
    """

    def __init__(self) -> None:
        """Initialize the PerformanceDetector with performance indicators."""
        self.performance_keywords: list[str] = [
            "slow", "slowly", "performance", "latency", "timeout", "bottleneck",
            "delay", "lag", "unresponsive", "hang", "freeze", "memory leak",
            "cpu usage", "memory usage", "disk io", "network latency",
            "scalability", "throughput", "optimization", "inefficient"
        ]

        self.performance_patterns: list[str] = [
            r"\b(takes too long|takes.*time|too slow)\b",
            r"\b(high cpu|high memory|high disk)\b",
            r"\b(memory leak|resource leak)\b",
            r"\b(performance degradation|degraded performance)\b",
            r"\b(slow query|slow response)\b",
            r"\b(timeout|time out)\b"
        ]

    def detect(self, problem_description: str) -> bool:
        """
        Detect if problem has performance implications.

        Args:
            problem_description: Text description of the problem

        Returns:
            True if performance issues are detected, False otherwise

        Examples:
            >>> detector = PerformanceDetector()
            >>> detector.detect("The application is very slow and has high memory usage")
            True
        """
        if not problem_description:
            return False

        description_lower = problem_description.lower()

        # Keyword detection
        keyword_match = any(
            keyword in description_lower
            for keyword in self.performance_keywords
        )

        # Pattern detection
        pattern_match = any(
            re.search(pattern, description_lower, re.IGNORECASE)
            for pattern in self.performance_patterns
        )

        return keyword_match or pattern_match


class ContextAnalyzer:
    """
    Intelligent context analysis for optimal RCA strategy selection.

    This is the main analyzer that orchestrates multiple specialized analyzers
    to provide comprehensive context analysis for Root Cause Analysis (RCA).
    It combines problem classification, complexity assessment, and specialized
    detection to recommend the most effective RCA strategy.

    Attributes:
        problem_classifier: Classifies problems into categories (bug, performance, etc.)
        complexity_assessor: Evaluates problem complexity (simple, moderate, complex)
        security_detector: Detects security-related concerns
        performance_detector: Detects performance-related issues
    """

    # Strategy recommendations
    STRATEGY_COUNCIL = "council"
    STRATEGY_DEEP_SCAN = "deep_scan"
    STRATEGY_SYSTEMATIC = "systematic"
    STRATEGY_EXPLORATORY = "exploratory"

    # Confidence calculation weights
    CLASSIFICATION_WEIGHT = 0.4
    COMPLEXITY_WEIGHT = 0.3
    SCOPE_WEIGHT = 0.15
    INDICATOR_WEIGHT = 0.15

    def __init__(self) -> None:
        """Initialize the ContextAnalyzer with all sub-analyzers."""
        self.problem_classifier = ProblemClassifier()
        self.complexity_assessor = ComplexityAssessor()
        self.security_detector = SecurityDetector()
        self.performance_detector = PerformanceDetector()

    def analyze_context(
        self,
        problem_description: str,
        target_files: list[str] | None = None
    ) -> dict:
        """
        Analyze problem context to determine optimal RCA approach.

        This is the main analysis method that orchestrates all sub-analyzers
        to provide a comprehensive context assessment and strategy recommendation.

        Args:
            problem_description: Description of the problem to analyze
            target_files: Optional list of target files involved

        Returns:
            Dictionary containing context analysis results:
            {
                'problem_type': 'bug|performance|security|architectural|unknown',
                'complexity_level': 'simple|moderate|complex|unknown',
                'scope': 'specific_file|module|system|unknown',
                'security_indicators': bool,
                'performance_indicators': bool,
                'confidence_score': float,
                'recommended_strategy': str,
                'classification_confidence': float,
                'analysis_timestamp': str,
                'processing_time_ms': float
            }

        Examples:
            >>> analyzer = ContextAnalyzer()
            >>> result = analyzer.analyze_context("Application crashes on startup")
            >>> result['problem_type']
            'bug'
        """
        start_time = time.time()

        # Perform analysis components
        problem_type, classification_confidence = self.problem_classifier.classify(
            problem_description
        )
        complexity_level = self.complexity_assessor.assess(
            problem_description, target_files
        )
        security_indicators = self.security_detector.detect(problem_description)
        performance_indicators = self.performance_detector.detect(problem_description)
        scope = self._analyze_scope(target_files)

        # Calculate overall confidence
        context = {
            "problem_type": problem_type,
            "complexity_level": complexity_level,
            "scope": scope,
            "security_indicators": security_indicators,
            "performance_indicators": performance_indicators,
            "classification_confidence": classification_confidence
        }

        confidence_score = self._calculate_confidence(context)
        recommended_strategy = self._recommend_strategy(context)

        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000

        return {
            "problem_type": problem_type,
            "complexity_level": complexity_level,
            "scope": scope,
            "security_indicators": security_indicators,
            "performance_indicators": performance_indicators,
            "confidence_score": confidence_score,
            "recommended_strategy": recommended_strategy,
            "classification_confidence": classification_confidence,
            "analysis_timestamp": datetime.now().isoformat(),
            "processing_time_ms": processing_time
        }

    def _analyze_scope(self, target_files: list[str] | None) -> str:
        """
        Analyze scope of the problem based on target files.

        Args:
            target_files: List of file paths involved in the problem

        Returns:
            One of 'specific_file', 'module', 'system', or 'unknown'
        """
        if not target_files:
            return "unknown"

        file_count = len(target_files)
        if file_count == 1:
            return "specific_file"
        if file_count <= 5:
            return "module"
        return "system"

    def _calculate_confidence(self, context: dict) -> float:
        """
        Calculate confidence score for context analysis.

        Combines multiple factors to determine overall confidence in the analysis.

        Args:
            context: Dictionary containing analysis components

        Returns:
            Float between 0.0 and 1.0 representing overall confidence
        """
        confidence = 0.0

        # Problem classification confidence (40% weight)
        if context["problem_type"] != "unknown":
            confidence += self.CLASSIFICATION_WEIGHT * context["classification_confidence"]

        # Complexity assessment confidence (30% weight)
        if context["complexity_level"] != "unknown":
            confidence += self.COMPLEXITY_WEIGHT

        # Scope analysis confidence (15% weight)
        if context["scope"] != "unknown":
            confidence += self.SCOPE_WEIGHT

        # Indicator detection confidence (15% weight)
        if context["security_indicators"] or context["performance_indicators"]:
            confidence += self.INDICATOR_WEIGHT

        return min(confidence, 1.0)

    def _recommend_strategy(self, context: dict) -> str:
        """
        Recommend optimal RCA strategy based on context.

        Uses a decision tree to select the most appropriate analysis strategy
        based on problem characteristics.

        Args:
            context: Dictionary containing analysis results

        Returns:
            One of 'council', 'deep_scan', 'systematic', or 'exploratory'
        """
        # Security concerns always get council strategy
        if context["security_indicators"]:
            return self.STRATEGY_COUNCIL

        # Performance issues get deep_scan for architectural analysis
        if context["performance_indicators"]:
            return self.STRATEGY_DEEP_SCAN

        # Complex problems get council strategy for multi-agent analysis
        if context["complexity_level"] == "complex":
            return self.STRATEGY_COUNCIL

        # Simple problems get systematic approach
        if context["complexity_level"] == "simple":
            return self.STRATEGY_SYSTEMATIC

        # Unknown scope gets exploratory approach
        if context["scope"] == "unknown":
            return self.STRATEGY_EXPLORATORY

        # Default to systematic
        return self.STRATEGY_SYSTEMATIC

    def get_analysis_summary(self, context: dict) -> str:
        """
        Get human-readable summary of context analysis.

        Args:
            context: Dictionary containing analysis results

        Returns:
            Human-readable summary string

        Examples:
            >>> analyzer = ContextAnalyzer()
            >>> context = analyzer.analyze_context("Bug in login")
            >>> analyzer.get_analysis_summary(context)
            'Detected bug problem, assessed as simple complexity, recommending systematic strategy with 75% confidence'
        """
        problem_type = context["problem_type"]
        complexity = context["complexity_level"]
        strategy = context["recommended_strategy"]
        confidence = context["confidence_score"]

        summary_parts = []

        if problem_type != "unknown":
            summary_parts.append(f"Detected {problem_type} problem")

        if complexity != "unknown":
            summary_parts.append(f"assessed as {complexity} complexity")

        summary_parts.append(f"recommending {strategy} strategy")

        if confidence > 0:
            summary_parts.append(f"with {confidence:.0%} confidence")

        return ", ".join(summary_parts)

    def extract_context(self, state: dict) -> dict:
        """
        Extract context from execution state.

        Args:
            state: Execution state dictionary containing variables, function info, etc.

        Returns:
            Context dictionary with extracted information and timestamp

        Examples:
            >>> analyzer = ContextAnalyzer()
            >>> state = {"variables": {"x": 10}, "function": "process"}
            >>> context = analyzer.extract_context(state)
            >>> "variables" in context
            True
        """
        context: dict = {
            "timestamp": datetime.now().isoformat()
        }

        if not state:
            return context

        # Extract variables if present
        if "variables" in state:
            context["variables"] = state["variables"]

        # Extract function information
        if "function" in state:
            context["function"] = state["function"]

        # Extract line number if present
        if "line_number" in state:
            context["line_number"] = state["line_number"]

        return context

    def capture_environment(
        self,
        filters: list[str] | None = None,
        prefix: str = ""
    ) -> dict:
        """
        Capture environment variables with optional filtering.

        Args:
            filters: Optional list of sensitive variable names to redact
            prefix: Optional prefix to filter variables by

        Returns:
            Dictionary of captured environment variables with sensitive data redacted

        Examples:
            >>> analyzer = ContextAnalyzer()
            >>> env = analyzer.capture_environment(prefix="APP_")
            >>> "APP_DEBUG" in env
            True
        """
        import os

        # Default sensitive filters
        if filters is None:
            filters = ["SECRET_KEY", "API_TOKEN", "PASSWORD", "TOKEN", "KEY", "CREDENTIALS"]

        env_context: dict[str, str] = {}

        for key, value in os.environ.items():
            # Apply prefix filter if specified
            if prefix and not key.startswith(prefix):
                continue

            # Check if this is a sensitive variable
            is_sensitive = any(
                sensitive in key.upper()
                for sensitive in filters
            )

            if is_sensitive:
                env_context[key] = "***REDACTED***"
            else:
                env_context[key] = value

        return env_context

    def analyze_stack_trace(
        self,
        stack_trace: str,
        include_locals: bool = False
    ) -> dict:
        """
        Parse and analyze Python stack traces.

        Args:
            stack_trace: Stack trace string to analyze
            include_locals: Whether to include local variable information

        Returns:
            Dictionary with analysis results including:
            - frames: List of frame dictionaries with file, line, function
            - exception_type: Type of exception (if found)
            - exception_message: Exception message (if found)
            - locals: Local variables (if include_locals=True)
            - error: Error message (if parsing failed)

        Examples:
            >>> analyzer = ContextAnalyzer()
            >>> trace = 'Traceback...\\n  File "test.py", line 10, in <module>\\nValueError: test'
            >>> result = analyzer.analyze_stack_trace(trace)
            >>> len(result["frames"]) > 0
            True
        """
        analysis: dict = {
            "frames": []
        }

        if not stack_trace or not isinstance(stack_trace, str):
            analysis["error"] = "Invalid stack trace input"
            return analysis

        # Parse stack trace frames
        frame_pattern = r'File "([^"]+)", line (\d+), in (\S+)'
        frames = re.findall(frame_pattern, stack_trace)

        for frame in frames:
            analysis["frames"].append({
                "file": frame[0],
                "line": int(frame[1]),
                "function": frame[2]
            })

        # Extract exception type
        exception_pattern = r'(\w+Error|[\w.]+Exception):\s*(.+)'
        exception_match = re.search(exception_pattern, stack_trace)
        if exception_match:
            analysis["exception_type"] = exception_match.group(1)
            analysis["exception_message"] = exception_match.group(2)

        # Include locals if requested (placeholder for actual implementation)
        if include_locals:
            analysis["locals"] = {}

        # If no frames found, mark as error
        if not analysis["frames"] and "error" not in analysis:
            analysis["error"] = "No valid frames found"

        return analysis

    def reconstruct_call_chain(
        self,
        stack_trace: str,
        include_context: bool = False
    ) -> list:
        """
        Reconstruct call chain from stack trace.

        Args:
            stack_trace: Stack trace string to reconstruct chain from
            include_context: Whether to include additional context like arguments

        Returns:
            List of call chain entries in execution order. Each entry is a dict
            with 'file', 'line', 'function' keys, and optionally 'context'
            and 'recursion_detected' keys.

        Examples:
            >>> analyzer = ContextAnalyzer()
            >>> trace = 'Traceback...\\n  File "a.py", line 1, in f1\\n  File "b.py", line 2, in f2'
            >>> chain = analyzer.reconstruct_call_chain(trace)
            >>> len(chain) == 2
            True
        """
        if not stack_trace or not isinstance(stack_trace, str):
            return []

        # Parse stack trace frames
        frame_pattern = r'File "([^"]+)", line (\d+), in (\S+)'
        frames = re.findall(frame_pattern, stack_trace)

        call_chain: list[dict] = []

        for frame in frames:
            entry: dict = {
                "file": frame[0],
                "line": int(frame[1]),
                "function": frame[2]
            }

            # Add context if requested
            if include_context:
                entry["context"] = {}

            call_chain.append(entry)

        # Detect recursion (check if same function appears multiple times)
        if len(call_chain) > 2:
            self._detect_recursion(call_chain)

        return call_chain

    def _detect_recursion(self, call_chain: list[dict]) -> None:
        """
        Detect and mark recursive patterns in call chain.

        Args:
            call_chain: List of call chain entries to modify in place
        """
        function_counts: dict[str, int] = {}
        for entry in call_chain:
            func = entry["function"]
            function_counts[func] = function_counts.get(func, 0) + 1

        if any(count > 2 for count in function_counts.values()):
            call_chain[0]["recursion_detected"] = True


# Performance monitoring for the context analyzer
class ContextAnalyzerMetrics:
    """
    Metrics collection for context analyzer performance.

    Tracks processing times and classification accuracy to monitor
    the effectiveness and efficiency of context analysis operations.
    """

    def __init__(self) -> None:
        """Initialize metrics tracking."""
        self.analysis_count: int = 0
        self.total_processing_time: float = 0.0
        self.classification_accuracy: dict[str, dict[str, int]] = {}

    def record_analysis(
        self,
        context_result: dict,
        actual_problem_type: str | None = None
    ) -> None:
        """
        Record metrics for context analysis.

        Args:
            context_result: Analysis result dictionary from analyze_context()
            actual_problem_type: Optional actual problem type for accuracy tracking

        Examples:
            >>> metrics = ContextAnalyzerMetrics()
            >>> result = {"processing_time_ms": 100, "problem_type": "bug"}
            >>> metrics.record_analysis(result, actual_problem_type="bug")
        """
        self.analysis_count += 1
        self.total_processing_time += context_result["processing_time_ms"]

        # Track classification accuracy if actual type provided
        if actual_problem_type:
            predicted_type = context_result["problem_type"]
            if actual_problem_type not in self.classification_accuracy:
                self.classification_accuracy[actual_problem_type] = {
                    "correct": 0,
                    "total": 0
                }

            self.classification_accuracy[actual_problem_type]["total"] += 1
            if predicted_type == actual_problem_type:
                self.classification_accuracy[actual_problem_type]["correct"] += 1

    def get_average_processing_time(self) -> float:
        """
        Get average processing time in milliseconds.

        Returns:
            Average processing time across all recorded analyses, or 0.0 if no analyses
        """
        if self.analysis_count == 0:
            return 0.0
        return self.total_processing_time / self.analysis_count

    def get_classification_accuracy(self, problem_type: str) -> float:
        """
        Get classification accuracy for specific problem type.

        Args:
            problem_type: The problem type to get accuracy for

        Returns:
            Accuracy ratio between 0.0 and 1.0, or 0.0 if no data available
        """
        if problem_type not in self.classification_accuracy:
            return 0.0

        stats = self.classification_accuracy[problem_type]
        if stats["total"] == 0:
            return 0.0

        return stats["correct"] / stats["total"]
