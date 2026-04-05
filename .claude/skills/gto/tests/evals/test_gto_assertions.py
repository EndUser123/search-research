"""Tests for gto_assertions module."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from evals.gto_assertions import GTOAssertions, _get_default_terminal_id


class TestGetDefaultTerminalId:
    """Tests for _get_default_terminal_id function."""

    def test_returns_string(self) -> None:
        """Test that _get_default_terminal_id returns a string."""
        result = _get_default_terminal_id()
        assert isinstance(result, str)
        assert len(result) > 0


class TestGTOAssertions:
    """Smoke tests for GTOAssertions class."""

    def test_class_construction(self, tmp_path: Path) -> None:
        """Test GTOAssertions can be constructed."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        assert assertions.project_root == tmp_path.resolve()
        assert assertions.terminal_id == "test_terminal"

    def test_check_a1_artifacts_exist_no_artifacts(self, tmp_path: Path) -> None:
        """Test A1 check returns False when no artifacts exist."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        passed, msg = assertions.check_a1_artifacts_exist()
        assert passed is False
        assert "No valid GTO artifacts" in msg

    def test_check_a2_health_score_no_artifacts(self, tmp_path: Path) -> None:
        """Test A2 check returns False when no health score exists."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        passed, msg = assertions.check_a2_health_score()
        assert passed is False
        assert "No valid health score" in msg

    def test_check_a3_viability_passed_no_check(self, tmp_path: Path) -> None:
        """Test A3 returns True when no viability check exists."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        passed, msg = assertions.check_a3_viability_passed()
        assert passed is True
        assert "No viability check" in msg

    def test_check_a4_git_repository_no_git(self, tmp_path: Path) -> None:
        """Test A4 returns False when no git repository exists."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        passed, msg = assertions.check_a4_git_repository()
        assert passed is False
        assert "Not a git repository" in msg

    def test_check_a5_state_accessible_no_state(self, tmp_path: Path) -> None:
        """Test A5 returns True when state directory not created."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        passed, msg = assertions.check_a5_state_accessible()
        assert passed is True
        assert "not created" in msg

    def test_run_all_returns_dict(self, tmp_path: Path) -> None:
        """Test run_all returns expected dictionary structure."""
        assertions = GTOAssertions(tmp_path, "test_terminal")
        result = assertions.run_all()
        assert isinstance(result, dict)
        assert "passed" in result
        assert "total" in result
        assert "score" in result
        assert "all_passed" in result
        assert "assertions" in result
