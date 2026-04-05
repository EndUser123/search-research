#!/usr/bin/env python3
"""
Unit tests for cold_code_review_dispatch.py

Tests:
- Dispatches adversarial review after GREEN phase
- Blinds reviewer from spec/plan
- Includes impl.py and test files in context
- Excludes spec.md from context
- Returns review result with findings
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


def test_detects_green_phase_for_review():
    """Test that GREEN phase triggers review dispatch detection."""
    from tdd.cold_code_review_dispatch import should_dispatch_review
    from tdd.tdd_phase_state import TDDPhaseState

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): return 1")

        # GREEN phase should trigger review
        result = should_dispatch_review(
            str(impl_path),
            TDDPhaseState.GREEN,
            state_dir=Path(tmpdir) / "state",
        )
        assert result is True, "GREEN phase should dispatch review"


def test_skips_review_for_red_phase():
    """Test that RED phase does not trigger review."""
    from tdd.cold_code_review_dispatch import should_dispatch_review
    from tdd.tdd_phase_state import TDDPhaseState

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): return 1")

        result = should_dispatch_review(
            str(impl_path),
            TDDPhaseState.RED,
            state_dir=Path(tmpdir) / "state",
        )
        assert result is False, "RED phase should not dispatch review"


def test_skips_review_for_refactor_phase():
    """Test that REFACTOR phase does not trigger review."""
    from tdd.cold_code_review_dispatch import should_dispatch_review
    from tdd.tdd_phase_state import TDDPhaseState

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): return 1")

        result = should_dispatch_review(
            str(impl_path),
            TDDPhaseState.REFACTOR,
            state_dir=Path(tmpdir) / "state",
        )
        assert result is False, "REFACTOR phase should not dispatch review"


def test_skips_review_for_complete_phase():
    """Test that COMPLETE phase does not trigger review."""
    from tdd.cold_code_review_dispatch import should_dispatch_review
    from tdd.tdd_phase_state import TDDPhaseState

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        impl_path.write_text("def foo(): return 1")

        result = should_dispatch_review(
            str(impl_path),
            TDDPhaseState.COMPLETE,
            state_dir=Path(tmpdir) / "state",
        )
        assert result is False, "COMPLETE phase should not dispatch review"


def test_blinds_reviewer_from_spec():
    """Test that spec.md is excluded from review context."""
    from tdd.cold_code_review_dispatch import build_review_context

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        spec_path = Path(tmpdir) / "spec.md"
        test_path = Path(tmpdir) / "test_impl.py"

        impl_path.write_text("def foo(): return 1")
        spec_path.write_text("# Specification\n\nFeature X should do Y.")
        test_path.write_text("def test_foo(): pass")

        context = build_review_context(
            impl_path=str(impl_path),
            test_paths=[str(test_path)],
            spec_path=str(spec_path),
        )

        # Spec should NOT be in context
        assert "spec.md" not in str(context).lower()
        assert "Specification" not in context.get("impl_content", "")
        assert "Feature X" not in context.get("impl_content", "")


def test_includes_impl_in_context():
    """Test that impl.py is included in review context."""
    from tdd.cold_code_review_dispatch import build_review_context

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"

        impl_path.write_text("def calculate(x): return x * 2")
        test_path.write_text("def test_calculate(): pass")

        context = build_review_context(
            impl_path=str(impl_path),
            test_paths=[str(test_path)],
            spec_path=None,
        )

        # Impl content should be included
        assert "impl.py" in context.get("impl_path", "")
        assert "calculate" in context.get("impl_content", "")


def test_includes_tests_in_context():
    """Test that test files are included in review context."""
    from tdd.cold_code_review_dispatch import build_review_context

    with tempfile.TemporaryDirectory() as tmpdir:
        impl_path = Path(tmpdir) / "impl.py"
        test_path = Path(tmpdir) / "test_impl.py"

        impl_path.write_text("def foo(): pass")
        test_path.write_text("def test_foo_edge_case(): assert True")

        context = build_review_context(
            impl_path=str(impl_path),
            test_paths=[str(test_path)],
            spec_path=None,
        )

        # Test content should be included
        assert "test_impl.py" in str(context.get("test_paths", []))
        assert "edge_case" in context.get("test_content", "")


def test_review_result_has_findings():
    """Test that review result includes findings structure."""
    from tdd.cold_code_review_dispatch import ColdReviewResult

    result = ColdReviewResult(
        passed=True,
        findings=["No issues found"],
        severity="none",
        reviewer_notes="Clean implementation",
    )

    assert result.passed is True
    assert len(result.findings) == 1
    assert result.severity == "none"


def test_review_result_tracks_blindness():
    """Test that review result tracks blindness verification."""
    from tdd.cold_code_review_dispatch import ColdReviewResult

    result = ColdReviewResult(
        passed=True,
        findings=[],
        severity="none",
        reviewer_notes="Reviewed without spec access",
        blindness_verified=True,
    )

    assert result.blindness_verified is True


def main():
    """Run all tests."""
    import pytest

    exit_code = pytest.main([__file__, "-v"])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
