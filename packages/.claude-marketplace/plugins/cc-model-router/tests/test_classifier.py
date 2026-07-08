"""Unit tests for the hierarchical classifier pipeline.

Tests the PIPELINE LOGIC (overrides, deterministic phase-1, fallback, observability).
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

def test_pipeline_no_scorer_uses_phase1():
    """When no scorer is loaded, Phase 1 deterministic rules still fire
    (no fallback needed). Code → local-coding."""
    result = classify_pipeline("def hello(): return 1", None, {})
    assert result.task_type == "local-coding"
    assert result.source == "deterministic"
    assert result.low_confidence is False


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


# --- Phase 1: deterministic task inference (replaces TF-IDF) ---

def test_phase1_code_under_64k_is_local_coding():
    """Code markers + <64k tokens → local-coding (ornith)."""
    result = classify_pipeline("def hello(): return 1", None, {})
    assert result.task_type == "local-coding"
    assert result.source == "deterministic"
    assert result.confidence == 1.0


def test_phase1_reasoning_indicators_is_reasoning():
    """Reasoning vocabulary → reasoning (glm/zai)."""
    result = classify_pipeline("analyze the architecture and tradeoffs", None, {})
    assert result.task_type == "reasoning"
    assert result.source == "deterministic"


def test_phase1_tool_calls_without_reasoning_is_coding():
    """Tool-call patterns without reasoning → coding (sonnet)."""
    result = classify_pipeline("invoke the API to fetch data", None, {})
    assert result.task_type == "coding"
    assert result.source == "deterministic"


def test_phase1_default_is_coding():
    """Plain prose without code/reasoning/tool markers → coding (sonnet default)."""
    result = classify_pipeline("explain how the system works", None, {})
    assert result.task_type == "coding"
    assert result.source == "deterministic"


def test_phase1_code_over_64k_falls_through():
    """Large code prompt (>64k tokens) escapes the local-coding rule."""
    # 50,000-word prompt with code markers
    big_code = ("def func(): pass\n" * 50000).strip()
    result = classify_pipeline(big_code, None, {})
    # It's still code, but >64k → falls through to the tool-call/default branch
    assert result.task_type in ("local-coding", "coding")
    assert result.source == "deterministic"


def test_phase1_reasoning_takes_priority_over_tool_call():
    """When both reasoning and tool-call patterns are present, reasoning wins."""
    result = classify_pipeline(
        "analyze the design and call the api to evaluate tradeoffs", None, {}
    )
    assert result.task_type == "reasoning"


# --- ClassifyResult structure ---

def test_result_has_observability_fields():
    result = classify_pipeline("def func(): return 1", None, {})
    assert hasattr(result, "stage_a")
    assert hasattr(result, "stage_b")
    assert hasattr(result, "source")
    assert hasattr(result, "backend")
    assert hasattr(result, "low_confidence")
    assert hasattr(result, "confidence")
    assert hasattr(result, "margin")
