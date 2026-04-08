"""Integration tests for intent detection accuracy (Phase 2).

Tests RuleBasedIntentDetector with a 100-query corpus and measures F1 score.
Target: >70% accuracy.

NOTE: These tests are skipped because RuleBasedIntentDetector API was removed.
The intent detection was refactored to use classify_query_intent() instead.
"""

import pytest

# Skip entire module - API changed, tests need rewrite
pytestmark = pytest.mark.skip(
    reason="RuleBasedIntentDetector API removed - needs rewrite for classify_query_intent()"
)

from collections import defaultdict


class TestIntentDetectionAccuracy:
    """Tests for intent detection accuracy with F1 score measurement."""

    @pytest.fixture
    def detector(self):
        """Create intent detector instance."""
        return RuleBasedIntentDetector()

    @pytest.fixture
    def test_corpus(self):
        """100-query test corpus with expected labels.

        Covers diverse query patterns:
        - Code patterns (LOCAL_ONLY)
        - Learning/research (WEB_ENHANCED)
        - Ambiguous queries (MIXED)
        """
        return [
            # LOCAL_ONLY queries (40) - Code patterns, file paths, API syntax
            ("def async_fetch_data", ModeIntent.LOCAL_ONLY),
            ("class UserService", ModeIntent.LOCAL_ONLY),
            ("import numpy as np", ModeIntent.LOCAL_ONLY),
            ("from flask import Flask", ModeIntent.LOCAL_ONLY),
            ("function fetchData()", ModeIntent.LOCAL_ONLY),
            ("const API_KEY = ", ModeIntent.LOCAL_ONLY),
            ("lambda x: x**2", ModeIntent.LOCAL_ONLY),
            ("async def process()", ModeIntent.LOCAL_ONLY),
            ("file:src/app.py", ModeIntent.LOCAL_ONLY),
            ("file:tests/test_api.py", ModeIntent.LOCAL_ONLY),
            ("src/components/Button.tsx", ModeIntent.LOCAL_ONLY),
            ("lib/utils/helpers.js", ModeIntent.LOCAL_ONLY),
            ("require('axios')", ModeIntent.LOCAL_ONLY),
            ("import React", ModeIntent.LOCAL_ONLY),
            ("export default function", ModeIntent.LOCAL_ONLY),
            ("def main():", ModeIntent.LOCAL_ONLY),
            ("class User(Model):", ModeIntent.LOCAL_ONLY),
            ("@app.route('/api')", ModeIntent.LOCAL_ONLY),
            ("GET /api/users", ModeIntent.LOCAL_ONLY),
            ("POST /auth/login", ModeIntent.LOCAL_ONLY),
            ("function(", ModeIntent.LOCAL_ONLY),
            ("=>", ModeIntent.LOCAL_ONLY),
            ("var data = ", ModeIntent.LOCAL_ONLY),
            ("let result = ", ModeIntent.LOCAL_ONLY),
            ("const config = ", ModeIntent.LOCAL_ONLY),
            ("async function", ModeIntent.LOCAL_ONLY),
            ("await fetch(", ModeIntent.LOCAL_ONLY),
            ("return ", ModeIntent.LOCAL_ONLY),
            ("if __name__", ModeIntent.LOCAL_ONLY),
            ("try:", ModeIntent.LOCAL_ONLY),
            ("except Exception", ModeIntent.LOCAL_ONLY),
            ("raise ValueError", ModeIntent.LOCAL_ONLY),
            ("assert ", ModeIntent.LOCAL_ONLY),
            ("with open(", ModeIntent.LOCAL_ONLY),
            ("src/", ModeIntent.LOCAL_ONLY),
            ("lib/", ModeIntent.LOCAL_ONLY),
            ("tests/", ModeIntent.LOCAL_ONLY),
            ("components/", ModeIntent.LOCAL_ONLY),
            (".py file", ModeIntent.LOCAL_ONLY),
            (".js file", ModeIntent.LOCAL_ONLY),
            (".ts file", ModeIntent.LOCAL_ONLY),
            # WEB_ENHANCED queries (40) - Learning, comparisons, best practices
            ("FastAPI tutorial", ModeIntent.WEB_ENHANCED),
            ("best practices", ModeIntent.WEB_ENHANCED),
            ("Flask vs FastAPI", ModeIntent.WEB_ENHANCED),
            ("how to use API", ModeIntent.WEB_ENHANCED),
            ("latest React patterns", ModeIntent.WEB_ENHANCED),
            ("explain microservices", ModeIntent.WEB_ENHANCED),
            ("introduction to Docker", ModeIntent.WEB_ENHANCED),
            ("overview of Kubernetes", ModeIntent.WEB_ENHANCED),
            ("what is REST API", ModeIntent.WEB_ENHANCED),
            ("what are microservices", ModeIntent.WEB_ENHANCED),
            ("difference between REST and GraphQL", ModeIntent.WEB_ENHANCED),
            ("compare pytest vs unittest", ModeIntent.WEB_ENHANCED),
            ("better approach for state management", ModeIntent.WEB_ENHANCED),
            ("tutorial for machine learning", ModeIntent.WEB_ENHANCED),
            ("guide to database design", ModeIntent.WEB_ENHANCED),
            ("example of async/await", ModeIntent.WEB_ENHANCED),
            ("how do I deploy Flask", ModeIntent.WEB_ENHANCED),
            ("how to optimize queries", ModeIntent.WEB_ENHANCED),
            ("show me authentication", ModeIntent.WEB_ENHANCED),
            ("find the best library", ModeIntent.WEB_ENHANCED),
            ("get the latest version", ModeIntent.WEB_ENHANCED),
            ("versus traditional approach", ModeIntent.WEB_ENHANCED),
            ("compare performance", ModeIntent.WEB_ENHANCED),
            ("comparison of frameworks", ModeIntent.WEB_ENHANCED),
            ("worse option", ModeIntent.WEB_ENHANCED),
            ("recent developments in AI", ModeIntent.WEB_ENHANCED),
            ("current best practices", ModeIntent.WEB_ENHANCED),
            ("up to date with Python", ModeIntent.WEB_ENHANCED),
            ("introduction to testing", ModeIntent.WEB_ENHANCED),
            ("introductory guide", ModeIntent.WEB_ENHANCED),
            ("documentation for React", ModeIntent.WEB_ENHANCED),
            ("learn TypeScript", ModeIntent.WEB_ENHANCED),
            ("understanding design patterns", ModeIntent.WEB_ENHANCED),
            ("describe the architecture", ModeIntent.WEB_ENHANCED),
            ("design principles", ModeIntent.WEB_ENHANCED),
            ("define dependency injection", ModeIntent.WEB_ENHANCED),
            ("definition of monad", ModeIntent.WEB_ENHANCED),
            ("description of event loop", ModeIntent.WEB_ENHANCED),
            # MIXED queries (20) - Ambiguous, short, unclear intent
            ("api", ModeIntent.MIXED),
            ("usage", ModeIntent.MIXED),
            ("data", ModeIntent.MIXED),
            ("pattern", ModeIntent.MIXED),
            ("implementation", ModeIntent.MIXED),
            ("test", ModeIntent.MIXED),
            ("error", ModeIntent.MIXED),
            ("bug", ModeIntent.MIXED),
            ("fix", ModeIntent.MIXED),
            ("help", ModeIntent.MIXED),
            ("search", ModeIntent.MIXED),
            ("find", ModeIntent.MIXED),
            ("get", ModeIntent.MIXED),
            ("show", ModeIntent.MIXED),
            ("code", ModeIntent.MIXED),
            ("function", ModeIntent.MIXED),
            ("class", ModeIntent.MIXED),
            ("method", ModeIntent.MIXED),
            ("endpoint", ModeIntent.MIXED),
            ("config", ModeIntent.MIXED),
        ]

    def test_intent_detection_f1_score(self, detector, test_corpus):
        """Test intent detection accuracy with F1 score measurement.

        Target: F1 score > 70% across all intent categories.
        """
        # Track predictions and ground truth
        predictions = []
        ground_truth = []

        for query, expected_intent in test_corpus:
            detection = detector.detect_intent(query)
            predicted_intent = detection.intent

            predictions.append(predicted_intent)
            ground_truth.append(expected_intent)

        # Calculate per-class metrics
        classes = [ModeIntent.LOCAL_ONLY, ModeIntent.WEB_ENHANCED, ModeIntent.MIXED]
        metrics = {}

        for cls in classes:
            tp = fp = fn = 0

            for pred, true in zip(predictions, ground_truth, strict=False):
                if pred == cls and true == cls:
                    tp += 1
                elif pred == cls and true != cls:
                    fp += 1
                elif pred != cls and true == cls:
                    fn += 1

            # Calculate precision, recall, F1
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (
                (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
            )

            metrics[cls] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "tp": tp,
                "fp": fp,
                "fn": fn,
            }

        # Calculate macro-average F1
        macro_f1 = sum(m["f1"] for m in metrics.values()) / len(metrics)

        # Calculate accuracy
        correct = sum(1 for p, g in zip(predictions, ground_truth, strict=False) if p == g)
        accuracy = correct / len(ground_truth)

        # Print metrics for visibility
        print("\n=== Intent Detection Metrics ===")
        print(f"Overall Accuracy: {accuracy:.2%}")
        print(f"Macro F1 Score: {macro_f1:.2%}")
        print("\nPer-Class Metrics:")
        for cls, cls_metrics in metrics.items():
            print(f"\n{cls.value}:")
            print(f"  Precision: {cls_metrics['precision']:.2%}")
            print(f"  Recall: {cls_metrics['recall']:.2%}")
            print(f"  F1: {cls_metrics['f1']:.2%}")
            print(f"  TP={cls_metrics['tp']}, FP={cls_metrics['fp']}, FN={cls_metrics['fn']}")

        # Assert accuracy target
        assert accuracy >= 0.70, f"Accuracy {accuracy:.2%} is below 70% target"
        assert macro_f1 >= 0.70, f"Macro F1 {macro_f1:.2%} is below 70% target"

    def test_confidence_score_distribution(self, detector, test_corpus):
        """Test that confidence scores are distributed appropriately."""
        confidence_by_intent = defaultdict(list)

        for query, expected_intent in test_corpus:
            detection = detector.detect_intent(query)
            confidence_by_intent[expected_intent].append(detection.confidence)

        # Check that LOCAL_ONLY queries have high confidence
        local_confidences = confidence_by_intent[ModeIntent.LOCAL_ONLY]
        if local_confidences:
            avg_local_conf = sum(local_confidences) / len(local_confidences)
            assert (
                avg_local_conf >= 0.65
            ), f"LOCAL_ONLY queries should have reasonably high confidence (avg={avg_local_conf:.2f})"

        # Check that WEB_ENHANCED queries have high confidence
        web_confidences = confidence_by_intent[ModeIntent.WEB_ENHANCED]
        if web_confidences:
            avg_web_conf = sum(web_confidences) / len(web_confidences)
            assert (
                avg_web_conf >= 0.75
            ), f"WEB_ENHANCED queries should have high confidence (avg={avg_web_conf:.2f})"

        # Check that MIXED queries have lower confidence
        mixed_confidences = confidence_by_intent[ModeIntent.MIXED]
        if mixed_confidences:
            avg_mixed_conf = sum(mixed_confidences) / len(mixed_confidences)
            assert (
                avg_mixed_conf < 0.75
            ), f"MIXED queries should have lower confidence (avg={avg_mixed_conf:.2f})"

    def test_keywords_matched_tracking(self, detector):
        """Test that keyword matching is tracked correctly."""
        # Query with clear LOCAL_ONLY patterns
        detection = detector.detect_intent("def async_fetch_data")

        assert detection.intent == ModeIntent.LOCAL_ONLY
        assert len(detection.keywords_matched) > 0
        assert "def " in detection.keywords_matched or "async def" in detection.keywords_matched

    def test_confusion_matrix(self, detector, test_corpus):
        """Generate and display confusion matrix for intent detection."""
        classes = [ModeIntent.LOCAL_ONLY, ModeIntent.WEB_ENHANCED, ModeIntent.MIXED]
        confusion_matrix = defaultdict(lambda: defaultdict(int))

        for query, expected_intent in test_corpus:
            detection = detector.detect_intent(query)
            predicted_intent = detection.intent

            confusion_matrix[expected_intent][predicted_intent] += 1

        # Print confusion matrix
        print("\n=== Confusion Matrix ===")
        print("                Predicted ->")
        print("                 LOCAL   WEB     MIXED")
        for true_cls in classes:
            row = f"True {true_cls.value[:12]:<12}"
            for pred_cls in classes:
                count = confusion_matrix[true_cls][pred_cls]
                row += f"  {count:3d}   "
            print(row)

        # Verify main diagonal has highest values (good predictions)
        for true_cls in classes:
            true_count = confusion_matrix[true_cls][true_cls]
            for pred_cls in classes:
                if pred_cls != true_cls:
                    off_diagonal = confusion_matrix[true_cls][pred_cls]
                    # Main diagonal should have >= off-diagonal counts
                    assert true_count >= off_diagonal, (
                        f"Confusion matrix issue: {true_cls} -> {pred_cls} "
                        f"({off_diagonal}) >= {true_cls} -> {true_cls} ({true_count})"
                    )


class TestIntentDetectionEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture
    def detector(self):
        """Create intent detector instance."""
        return RuleBasedIntentDetector()

    def test_empty_query(self, detector):
        """Test empty query handling."""
        detection = detector.detect_intent("")

        assert detection.intent == ModeIntent.MIXED
        assert detection.confidence == 0.0
        assert len(detection.keywords_matched) == 0

    def test_whitespace_only_query(self, detector):
        """Test whitespace-only query handling."""
        detection = detector.detect_intent("   ")

        assert detection.intent == ModeIntent.MIXED
        assert detection.confidence == 0.0

    def test_very_short_query(self, detector):
        """Test very short query (1-2 words)."""
        # Short code pattern should still be detected
        detection = detector.detect_intent("def ")
        assert detection.intent == ModeIntent.LOCAL_ONLY
        # Confidence should be reduced for short queries
        assert detection.confidence < 0.95

        # Short ambiguous query
        detection = detector.detect_intent("api")
        assert detection.intent == ModeIntent.MIXED
        assert detection.confidence < 0.70

    def test_case_insensitivity(self, detector):
        """Test that detection is case-insensitive."""
        queries = [
            "DEF FUNCTION",
            "Def Async",
            "def function",
        ]

        for query in queries:
            detection = detector.detect_intent(query)
            assert detection.intent == ModeIntent.LOCAL_ONLY

    def test_multiple_patterns_in_query(self, detector):
        """Test query with multiple matching patterns."""
        detection = detector.detect_intent("def async_fetch_data function")

        assert detection.intent == ModeIntent.LOCAL_ONLY
        # Multiple matches should increase confidence
        assert detection.confidence > 0.85
        assert len(detection.keywords_matched) >= 1

    def test_conflicting_patterns(self, detector):
        """Test query with both LOCAL_ONLY and WEB_ENHANCED patterns."""
        # This is unlikely given the pattern sets, but test the behavior
        detection = detector.detect_intent("def tutorial")

        # Should still make a decision based on confidence comparison
        assert detection.intent in [
            ModeIntent.LOCAL_ONLY,
            ModeIntent.WEB_ENHANCED,
            ModeIntent.MIXED,
        ]
        assert 0.0 <= detection.confidence <= 1.0


class TestIntentDetectionConfidence:
    """Tests for confidence scoring mechanics."""

    @pytest.fixture
    def detector(self):
        """Create intent detector instance."""
        return RuleBasedIntentDetector()

    def test_strong_pattern_high_confidence(self, detector):
        """Test that strong patterns produce high confidence."""
        strong_queries = [
            ("def async_fetch", 0.95),  # Code syntax
            ("file:src/app.py", 0.95),  # File pattern
            ("FastAPI tutorial", 0.95),  # Learning pattern
            ("Flask vs Django", 0.90),  # Comparison pattern
        ]

        for query, min_confidence in strong_queries:
            detection = detector.detect_intent(query)
            assert detection.confidence >= min_confidence, (
                f"Query '{query}' has confidence {detection.confidence:.2f}, "
                f"expected >= {min_confidence:.2f}"
            )

    def test_multiple_matches_bonus(self, detector):
        """Test that multiple pattern matches increase confidence."""
        # Single pattern
        detection1 = detector.detect_intent("def function")
        conf1 = detection1.confidence

        # Multiple patterns (if applicable)
        detection2 = detector.detect_intent("def async function")
        conf2 = detection2.confidence

        # Multiple matches should have equal or higher confidence
        assert conf2 >= conf1, "Multiple pattern matches should increase confidence"

    def test_confidence_bounds(self, detector):
        """Test that confidence is always in [0, 1]."""
        test_queries = [
            "",
            "a",
            "def function",
            "tutorial",
            "api usage",
            "file:test.py",
        ]

        for query in test_queries:
            detection = detector.detect_intent(query)
            assert (
                0.0 <= detection.confidence <= 1.0
            ), f"Query '{query}' has invalid confidence: {detection.confidence}"


class TestModeMapping:
    """Tests for intent to mode mapping."""

    @pytest.fixture
    def detector(self):
        """Create intent detector instance."""
        return RuleBasedIntentDetector()

    def test_local_only_maps_to_fast(self, detector):
        """Test that LOCAL_ONLY intent maps to FAST mode."""
        from search_research import Mode

        detection = detector.detect_intent("def function")
        mode = detector.get_mode_from_intent(detection)

        assert mode == Mode.FAST

    def test_web_enhanced_maps_to_comprehensive(self, detector):
        """Test that WEB_ENHANCED intent maps to COMPREHENSIVE mode."""
        from search_research import Mode

        detection = detector.detect_intent("FastAPI tutorial")
        mode = detector.get_mode_from_intent(detection)

        assert mode == Mode.COMPREHENSIVE

    def test_mixed_maps_to_comprehensive(self, detector):
        """Test that MIXED intent maps to COMPREHENSIVE mode (safe default)."""
        from search_research import Mode

        detection = detector.detect_intent("api")
        mode = detector.get_mode_from_intent(detection)

        assert mode == Mode.COMPREHENSIVE
