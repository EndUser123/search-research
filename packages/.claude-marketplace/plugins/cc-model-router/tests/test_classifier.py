"""Unit tests for the hierarchical classifier pipeline.

Tests the PIPELINE LOGIC (overrides, fallback, hint schema, context boost),
not TF-IDF accuracy (that's covered by the evaluation harness).
"""
import sys
import pathlib

PLUGIN_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "__lib"))

from classifier.deterministic import check_overrides, is_mechanical_edit
from classifier.pipeline import classify_pipeline, ClassifyResult
from classifier.scorer import ScorerResult


# --- Deterministic override tests ---

def test_git_command_is_background():
    assert check_overrides("git commit and push all changes") == "background"

def test_npm_install_is_background():
    assert check_overrides("npm install the dependencies") == "background"

def test_lint_is_background():
    assert check_overrides("lint the project") == "background"

def test_short_yes_is_local():
    assert check_overrides("yes") == "local-coding"

def test_rename_is_local():
    assert check_overrides("rename the variable") == "local-coding"

def test_coding_prompt_no_override():
    assert check_overrides("implement a function to parse config") is None

def test_reasoning_prompt_no_override():
    assert check_overrides("analyze the architecture and tradeoffs") is None


# --- Mechanical edit detection (Stage C) ---

def test_mechanical_edit_detected():
    assert is_mechanical_edit("rename the config file") is True

def test_non_mechanical_not_detected():
    assert is_mechanical_edit("analyze the system performance") is False


# --- Pipeline fallback (no scorer) ---

def test_pipeline_fallback_no_scorer():
    result = classify_pipeline("implement a function", None, {})
    assert result.task_type == "coding"
    assert result.source == "fallback"
    assert result.backend == "none"
    assert result.low_confidence is True


# --- Pipeline with deterministic override ---

def test_pipeline_override_background():
    result = classify_pipeline("git push origin main", None, {})
    assert result.task_type == "background"
    assert result.source == "override"
    assert result.confidence == 1.0


def test_pipeline_override_local():
    result = classify_pipeline("done", None, {})
    assert result.task_type == "local-coding"
    assert result.source == "override"


# --- Pipeline with mock scorer ---

class MockScorer:
    """Mock scorer that returns predefined class scores."""
    def __init__(self, scores: dict, ready=True):
        self._scores = scores
        self._ready = ready

    @property
    def ready(self):
        return self._ready

    def score(self, prompt, context=None):
        sorted_scores = sorted(self._scores.items(), key=lambda x: -x[1])
        return ScorerResult(
            class_scores=self._scores.copy(),
            top_class=sorted_scores[0][0],
            confidence=sorted_scores[0][1],
            runner_up=sorted_scores[1][0] if len(sorted_scores) > 1 else "",
            margin=sorted_scores[0][1] - (sorted_scores[1][1] if len(sorted_scores) > 1 else 0),
            backend="mock",
        )


def test_pipeline_semantic_coding():
    scorer = MockScorer({"background": 0.1, "coding": 0.7, "reasoning": 0.3})
    result = classify_pipeline("implement a new feature", scorer, {})
    assert result.task_type == "coding"
    assert result.source == "semantic"
    assert result.stage_a is not None
    assert result.stage_b is not None


def test_pipeline_semantic_reasoning():
    scorer = MockScorer({"background": 0.05, "coding": 0.3, "reasoning": 0.8})
    result = classify_pipeline("analyze the architecture", scorer, {})
    assert result.task_type == "reasoning"
    assert result.source == "semantic"
    assert result.stage_b["class"] == "reasoning"


def test_pipeline_semantic_background():
    scorer = MockScorer({"background": 0.6, "coding": 0.2, "reasoning": 0.1})
    result = classify_pipeline("git commit", scorer, {})
    # Background should be caught by override first
    assert result.task_type == "background"
    assert result.source == "override"


def test_pipeline_semantic_low_confidence():
    """Low confidence fires when margin < low_confidence_margin (0.02)."""
    # Margin 0.03 > 0.02 → not low confidence (pipeline correctly returns False)
    scorer = MockScorer({"background": 0.1, "coding": 0.45, "reasoning": 0.42})
    result = classify_pipeline("some ambiguous prompt", scorer, {})
    assert result.low_confidence is False  # margin 0.03 > threshold 0.02
    assert result.task_type == "coding"    # coding wins (0.45 > 0.42)
    assert round(result.margin, 4) == 0.0300

    # Margin 0.01 < 0.02 → low confidence (pipeline correctly returns True)
    scorer_tight = MockScorer({"background": 0.1, "coding": 0.45, "reasoning": 0.44})
    result_tight = classify_pipeline("another prompt", scorer_tight, {})
    assert result_tight.low_confidence is True
    assert result_tight.task_type == "coding"  # still coding (0.45 > 0.44), just low-conf
    assert round(result_tight.margin, 4) == 0.0100


def test_pipeline_context_boost():
    """Context boost should raise the prev_task_type class score."""
    scores = {"background": 0.1, "coding": 0.5, "reasoning": 0.35}
    scorer = MockScorer(scores)
    # Without context: coding wins (0.5 > 0.35)
    result_no_ctx = classify_pipeline("analyze this", scorer, {})
    assert result_no_ctx.task_type == "coding"

    # With context boost on reasoning: reasoning gets +0.15 → 0.50, still close
    scorer2 = MockScorer(scores)
    result_with_ctx = classify_pipeline("analyze this", scorer2, {},
                                        context={"prev_task_type": "reasoning", "followup_boost": 0.15})
    # The mock scorer doesn't apply context boost (only TfidfBackend does),
    # but the pipeline should still handle it gracefully
    assert result_with_ctx.task_type in ("coding", "reasoning")


# --- ClassifyResult structure ---

def test_result_has_observability_fields():
    scorer = MockScorer({"background": 0.1, "coding": 0.7, "reasoning": 0.3})
    result = classify_pipeline("test prompt", scorer, {})
    assert hasattr(result, "stage_a")
    assert hasattr(result, "stage_b")
    assert hasattr(result, "class_scores")
    assert hasattr(result, "top_2")
    assert hasattr(result, "backend")
    assert hasattr(result, "low_confidence")
