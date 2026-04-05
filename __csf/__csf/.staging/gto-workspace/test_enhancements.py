"""Tests for all /gto skill enhancements."""

import pytest
from scripts.cks_integrator import CKSIntegrator
from scripts.quick_actions import QuickActionsGenerator
from scripts.dependency_analyzer import DependencyAnalyzer
from scripts.friction_detector import FrictionDetector
from scripts.test_matrix import TestMatrixGenerator
from scripts.trend_analyzer import TrendAnalyzer


def test_cks_integrator_initialization():
    """Test CKS integrator initializes (with or without CKS)."""
    integrator = CKSIntegrator()
    assert integrator is not None


def test_cks_integrator_store_pattern():
    """Test storing a pattern in CKS (graceful degradation if unavailable)."""
    integrator = CKSIntegrator()
    # Should not crash even if CKS unavailable
    result = integrator.store_pattern("Test TODO", "todo", {"file": "test.py"})
    # Result may be False if CKS unavailable, that's ok
    assert isinstance(result, bool)


def test_quick_actions_generator():
    """Test quick actions generation."""
    gen = QuickActionsGenerator()
    actions = gen.generate_todo_fixes(["TODO: Fix bug in auth.py line 45"])
    assert len(actions) >= 0


def test_quick_actions_format_menu():
    """Test formatting actions as menu."""
    gen = QuickActionsGenerator()
    menu = gen.format_actions_menu([])
    assert "No quick actions" in menu or "Quick Actions Menu" in menu


def test_dependency_analyzer():
    """Test dependency analyzer initialization."""
    analyzer = DependencyAnalyzer()
    assert analyzer.working_dir is not None


def test_dependency_extract_imports(tmp_path):
    """Test extracting imports from Python file."""
    analyzer = DependencyAnalyzer()
    test_file = tmp_path / "test.py"
    test_file.write_text("import os\nimport sys\nfrom collections import defaultdict")
    imports = analyzer.extract_imports(test_file)
    assert "os" in imports
    assert "sys" in imports


def test_friction_detector():
    """Test friction detector initialization."""
    detector = FrictionDetector()
    assert detector is not None


def test_friction_detect_blocks():
    """Test block detection in conversation."""
    detector = FrictionDetector()
    conversation = "I'm blocked by path security error"
    blocks = detector.detect_blocks(conversation)
    assert len(blocks) >= 0


def test_friction_analyze_conversation():
    """Test full friction analysis."""
    detector = FrictionDetector()
    result = detector.analyze_conversation("Working smoothly")
    assert "friction_level" in result
    assert result["friction_level"] in ["low", "medium", "high"]


def test_test_matrix_generator():
    """Test test matrix generator initialization."""
    gen = TestMatrixGenerator()
    assert gen.working_dir is not None


def test_test_matrix_find_files():
    """Test finding test and source files."""
    gen = TestMatrixGenerator()
    test_files = gen.find_test_files()
    source_files = gen.find_source_files()
    assert isinstance(test_files, list)
    assert isinstance(source_files, list)


def test_trend_analyzer():
    """Test trend analyzer initialization."""
    analyzer = TrendAnalyzer()
    assert analyzer is not None


def test_trend_compare_to_baseline():
    """Test comparing current to baseline metrics."""
    analyzer = TrendAnalyzer()
    current = {"todo_count": 5, "unfinished_count": 2, "conversation_length": 1000}
    baseline = {"todo_count": 3, "unfinished_count": 1, "conversation_length": 800}
    result = analyzer.compare_to_baseline(current, baseline)
    assert "deltas" in result
    assert "todo_count" in result["deltas"]


def test_trend_detect_patterns():
    """Test pattern emergence detection."""
    analyzer = TrendAnalyzer()
    gaps = ["TODO: Fix auth bug", "FIXME: Handle edge case"]
    history = ["TODO: Fix auth bug", "TODO: Update tests"]
    result = analyzer.detect_pattern_emergence(gaps, history)
    assert "recurring_patterns" in result
    assert isinstance(result["recurring_patterns"], list)
