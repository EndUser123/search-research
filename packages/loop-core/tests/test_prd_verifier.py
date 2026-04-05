"""Tests for PRD Verifier module.

Tests the verification functionality including PRD coverage, spec compliance,
and implementation quality checks.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.loop_policy import parse_plan_with_cache
from skills.prd_verifier import (
    PRDVerifier,
    VerificationResult,
    run_verification,
)


@pytest.fixture
def temp_plan_file(tmp_path: Path) -> Path:
    """Create a temporary plan file with tasks."""
    plan_content = """# Feature: User Authentication

## Acceptance Criteria
- [x] TASK-001 Design database schema for users table
- [x] TASK-002 Implement password hashing utility
- [ ] TASK-003 Create login endpoint
- [ ] TASK-004 Write unit tests for auth module

## Success Metrics
- [x] TASK-005 Database schema created
- [x] TASK-006 Password hashing implemented
- [ ] TASK-007 All tests passing

## RALPH_STATUS
- EXIT_SIGNAL: false
- completion_indicators: 2
"""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text(plan_content)
    return plan_file


@pytest.fixture
def temp_prd_file(tmp_path: Path) -> Path:
    """Create a temporary PRD file."""
    prd_content = """# Product Requirements Document: User Authentication

## Technical Specifications

The system shall implement secure user authentication with:
- Password hashing using bcrypt
- JWT token-based sessions
- Session expiration after 24 hours

## API Contract

### POST /api/auth/login
- Request: {username, password}
- Response: {token, expires_at}

### POST /api/auth/logout
- Request: {token}
- Response: {success: true}

## Data Model

Users table:
- id: UUID primary key
- username: unique string
- password_hash: bcrypt hash
- created_at: timestamp
"""
    prd_file = tmp_path / "prd.md"
    prd_file.write_text(prd_content)
    return prd_file


@pytest.fixture
def sample_tasks() -> list[dict[str, Any]]:
    """Create sample task list."""
    return [
        {
            "id": "TASK-001",
            "text": "Design database schema for users table",
            "complete": True,
        },
        {
            "id": "TASK-002",
            "text": "Implement password hashing utility",
            "complete": True,
        },
        {"id": "TASK-003", "text": "Create login endpoint", "complete": False},
        {
            "id": "TASK-004",
            "text": "Write unit tests for auth module",
            "complete": False,
        },
    ]


@pytest.fixture
def sample_loop_state(tmp_path: Path) -> dict[str, Any]:
    """Create sample loop state."""
    return {
        "completion_indicators": 2,
        "ralph_status": {"EXIT_SIGNAL": False},
        "metadata": {
            "plan_path": str(tmp_path / "plan.md"),
        },
    }


class TestVerificationResult:
    """Test VerificationResult dataclass."""

    def test_verification_result_creation(self) -> None:
        """Test creating a VerificationResult."""
        result = VerificationResult(
            passed=True,
            report_path=".claude/loop/verification-report.md",
            timestamp="2026-03-15T12:00:00",
        )
        assert result.passed is True
        assert result.report_path == ".claude/loop/verification-report.md"
        assert result.timestamp == "2026-03-15T12:00:00"

    def test_to_dict(self) -> None:
        """Test converting VerificationResult to dictionary."""
        result = VerificationResult(
            passed=False,
            report_path=".claude/loop/verification-report.md",
            timestamp="2026-03-15T12:00:00",
            summary="Verification failed",
        )
        result_dict = result.to_dict()
        assert result_dict["passed"] is False
        assert result_dict["summary"] == "Verification failed"


class TestPRDVerifier:
    """Test PRDVerifier class."""

    def test_initialization_with_paths(
        self, temp_plan_file: Path, temp_prd_file: Path
    ) -> None:
        """Test initializing PRDVerifier with paths."""
        verifier = PRDVerifier(
            prd_path=str(temp_prd_file),
            plan_path=str(temp_plan_file),
            codebase_dir=str(temp_plan_file.parent),
        )
        assert verifier.prd_path == temp_prd_file
        assert verifier.plan_path == temp_plan_file
        assert verifier.codebase_dir == temp_plan_file.parent

    def test_initialization_without_paths(self) -> None:
        """Test initializing PRDVerifier without paths."""
        verifier = PRDVerifier()
        assert verifier.prd_path is None
        assert verifier.plan_path is None
        assert verifier.codebase_dir == Path.cwd()

    def test_default_config_when_config_missing(self, tmp_path: Path) -> None:
        """Test that default config is used when config file is missing."""
        verifier = PRDVerifier(config_path=str(tmp_path / "nonexistent.yaml"))
        config = verifier.config
        assert config["version"] == 1
        assert "exit_policy" in config
        assert "verification" in config

    def test_verify_prd_coverage(
        self, temp_plan_file: Path, sample_tasks: list[dict[str, Any]]
    ) -> None:
        """Test PRD coverage verification."""
        verifier = PRDVerifier(plan_path=str(temp_plan_file))
        result = verifier._verify_prd_coverage(sample_tasks)

        assert "requirements_addressed" in result
        assert "total_requirements" in result
        assert "coverage_percentage" in result
        assert "missing_requirements" in result
        assert "details" in result

    def test_verify_prd_coverage_no_plan(
        self, sample_tasks: list[dict[str, Any]]
    ) -> None:
        """Test PRD coverage verification when no plan exists."""
        verifier = PRDVerifier(plan_path="/nonexistent/plan.md")
        result = verifier._verify_prd_coverage(sample_tasks)

        assert result["total_requirements"] == 0
        assert "No plan file provided" in result["details"]

    def test_verify_spec_compliance(
        self, temp_prd_file: Path, sample_tasks: list[dict[str, Any]]
    ) -> None:
        """Test spec compliance verification."""
        verifier = PRDVerifier(prd_path=str(temp_prd_file))
        result = verifier._verify_spec_compliance(sample_tasks)

        assert "spec_requirements_met" in result
        assert "total_spec_requirements" in result
        assert "compliance_percentage" in result
        assert "deviations" in result
        assert "details" in result

    def test_verify_spec_compliance_no_prd(
        self, sample_tasks: list[dict[str, Any]]
    ) -> None:
        """Test spec compliance verification when no PRD exists."""
        verifier = PRDVerifier(prd_path=None)
        result = verifier._verify_spec_compliance(sample_tasks)

        # Should assume passing when no PRD
        assert result["compliance_percentage"] == 100.0
        assert "No PRD file provided" in result["details"]

    def test_verify_implementation_quality(
        self,
        temp_plan_file: Path,
        sample_tasks: list[dict[str, Any]],
        sample_loop_state: dict[str, Any],
    ) -> None:
        """Test implementation quality verification."""
        verifier = PRDVerifier(plan_path=str(temp_plan_file))
        result = verifier._verify_implementation_quality(
            sample_tasks, sample_loop_state
        )

        assert "code_quality_score" in result
        assert "max_score" in result
        assert "critical_issues" in result
        assert "recommendations" in result
        assert "details" in result

        # Score should be based on completion rate
        assert result["code_quality_score"] >= 0
        assert result["code_quality_score"] <= 10

    def test_determine_pass_status_all_pass(self) -> None:
        """Test pass status determination when all checks pass."""
        verifier = PRDVerifier()
        result = VerificationResult(
            passed=False,
            report_path=".claude/loop/verification-report.md",
            timestamp="2026-03-15T12:00:00",
        )
        result.prd_coverage = {"coverage_percentage": 90.0}
        result.spec_compliance = {"compliance_percentage": 90.0}
        result.implementation_quality = {
            "code_quality_score": 8,
            "critical_issues": [],
        }

        passed = verifier._determine_pass_status(
            result, ["prd_coverage", "spec_compliance", "implementation_quality"]
        )
        assert passed is True

    def test_determine_pass_status_prd_coverage_fails(self) -> None:
        """Test pass status when PRD coverage is below threshold."""
        verifier = PRDVerifier()
        result = VerificationResult(
            passed=False,
            report_path=".claude/loop/verification-report.md",
            timestamp="2026-03-15T12:00:00",
        )
        result.prd_coverage = {"coverage_percentage": 70.0}
        result.spec_compliance = {"compliance_percentage": 90.0}
        result.implementation_quality = {
            "code_quality_score": 8,
            "critical_issues": [],
        }

        passed = verifier._determine_pass_status(
            result, ["prd_coverage", "spec_compliance", "implementation_quality"]
        )
        assert passed is False

    def test_determine_pass_status_critical_issues(self) -> None:
        """Test pass status when critical issues are present."""
        verifier = PRDVerifier()
        result = VerificationResult(
            passed=False,
            report_path=".claude/loop/verification-report.md",
            timestamp="2026-03-15T12:00:00",
        )
        result.prd_coverage = {"coverage_percentage": 90.0}
        result.spec_compliance = {"compliance_percentage": 90.0}
        result.implementation_quality = {
            "code_quality_score": 8,
            "critical_issues": ["User concern: This is wrong"],
        }

        passed = verifier._determine_pass_status(
            result, ["prd_coverage", "spec_compliance", "implementation_quality"]
        )
        assert passed is False

    def test_generate_summary(self) -> None:
        """Test summary generation."""
        verifier = PRDVerifier()
        result = VerificationResult(
            passed=True,
            report_path=".claude/loop/verification-report.md",
            timestamp="2026-03-15T12:00:00",
        )
        result.prd_coverage = {
            "coverage_percentage": 85.0,
            "requirements_addressed": 5,
            "total_requirements": 6,
        }
        result.spec_compliance = {
            "compliance_percentage": 90.0,
            "spec_requirements_met": 9,
            "total_spec_requirements": 10,
        }
        result.implementation_quality = {
            "code_quality_score": 8,
            "max_score": 10,
            "critical_issues": [],
        }

        summary = verifier._generate_summary(
            result, ["prd_coverage", "spec_compliance", "implementation_quality"]
        )

        assert "PASS" in summary
        assert "85.0%" in summary
        assert "90.0%" in summary
        assert "8/10" in summary

    def test_write_report(self, tmp_path: Path) -> None:
        """Test writing verification report."""
        report_path = tmp_path / "verification-report.md"
        verifier = PRDVerifier()
        result = VerificationResult(
            passed=True,
            report_path=str(report_path),
            timestamp="2026-03-15T12:00:00",
            summary="Test summary",
        )
        result.prd_coverage = {
            "coverage_percentage": 100.0,
            "requirements_addressed": 3,
            "total_requirements": 3,
            "missing_requirements": [],
            "details": ["- Task 1: ✓", "- Task 2: ✓", "- Task 3: ✓"],
        }

        verifier._write_report(result)

        assert report_path.exists()
        report_content = report_path.read_text()
        assert "# Verification Report" in report_content
        assert "PASS" in report_content
        assert "PRD Coverage" in report_content


class TestRunVerification:
    """Test run_verification convenience function."""

    def test_run_verification_success(
        self,
        temp_plan_file: Path,
        sample_tasks: list[dict[str, Any]],
        sample_loop_state: dict[str, Any],
        tmp_path: Path,
    ) -> None:
        """Test running verification successfully."""
        report_path = tmp_path / "verification-report.md"

        # Create full config with all required sections
        config = {
            "version": 1,
            "exit_policy": {
                "min_completion_indicators": 2,
                "require_exit_signal": True,
                "require_all_tasks_complete": True,
                "require_verification_pass": True,
            },
            "verification": {
                "enabled": True,
                "skill": "prd-verifier",
                "write_report": str(report_path),
                "fields": ["prd_coverage"],
            },
            "plans": {
                "default_plan": "plan.md",
                "allow_per_terminal_plan": True,
            },
            "logging": {
                "decision_log": "decision.log",
                "verifier_log": "verifier.log",
            },
        }
        config_file = tmp_path / "config.yaml"
        import yaml

        config_file.write_text(yaml.dump(config))

        result = run_verification(
            plan_path=str(temp_plan_file),
            config_path=str(config_file),
            tasks=sample_tasks,
            loop_state=sample_loop_state,
        )

        assert isinstance(result, VerificationResult)
        assert report_path.exists()

    def test_run_verification_parse_tasks_from_plan(
        self, temp_plan_file: Path, tmp_path: Path
    ) -> None:
        """Test that run_verification parses tasks from plan if not provided."""
        config_file = tmp_path / "config.yaml"
        import yaml

        config_file.write_text(
            yaml.dump(
                {
                    "version": 1,
                    "exit_policy": {
                        "min_completion_indicators": 2,
                        "require_exit_signal": True,
                        "require_all_tasks_complete": True,
                        "require_verification_pass": True,
                    },
                    "verification": {
                        "enabled": True,
                        "skill": "prd-verifier",
                        "write_report": str(tmp_path / "verification-report.md"),
                        "fields": ["prd_coverage"],
                    },
                    "plans": {
                        "default_plan": "plan.md",
                        "allow_per_terminal_plan": True,
                    },
                    "logging": {
                        "decision_log": "decision.log",
                        "verifier_log": "verifier.log",
                    },
                }
            )
        )

        result = run_verification(
            plan_path=str(temp_plan_file),
            config_path=str(config_file),
        )

        # Should have parsed tasks from plan
        assert isinstance(result, VerificationResult)


class TestVerificationIntegration:
    """Integration tests for verification with loop policy."""

    def test_verify_with_loop_policy_integration(
        self, temp_plan_file: Path, tmp_path: Path
    ) -> None:
        """Test verification integration with loop policy module."""
        # Parse tasks using loop_policy
        tasks = parse_plan_with_cache(temp_plan_file)

        # Run verification
        verifier = PRDVerifier(plan_path=str(temp_plan_file))
        loop_state = {
            "completion_indicators": 2,
            "ralph_status": {"EXIT_SIGNAL": False},
            "metadata": {"plan_path": str(temp_plan_file)},
        }

        result = verifier.verify(tasks, loop_state)

        assert isinstance(result, VerificationResult)
        assert result.report_path
        assert Path(result.report_path).exists()

    def test_verification_updates_loop_state(
        self, temp_plan_file: Path, sample_loop_state: dict[str, Any]
    ) -> None:
        """Test that verification result can update loop state."""
        verifier = PRDVerifier(plan_path=str(temp_plan_file))
        tasks = parse_plan_with_cache(temp_plan_file)

        result = verifier.verify(tasks, sample_loop_state)

        # Update loop state with verification result
        sample_loop_state["verification_status"] = {
            "passed": result.passed,
            "report_path": result.report_path,
            "timestamp": result.timestamp,
        }

        assert sample_loop_state["verification_status"]["passed"] == result.passed


@pytest.mark.parametrize(
    "coverage_percentage,expected_pass",
    [
        (100.0, True),
        (90.0, True),
        (80.0, True),
        (79.9, False),
        (50.0, False),
        (0.0, False),
    ],
)
def test_prd_coverage_thresholds(
    coverage_percentage: float, expected_pass: bool
) -> None:
    """Test PRD coverage pass thresholds."""
    verifier = PRDVerifier()
    result = VerificationResult(
        passed=False,
        report_path=".claude/loop/verification-report.md",
        timestamp="2026-03-15T12:00:00",
    )
    result.prd_coverage = {"coverage_percentage": coverage_percentage}
    result.spec_compliance = {"compliance_percentage": 100.0}
    result.implementation_quality = {
        "code_quality_score": 10,
        "critical_issues": [],
    }

    passed = verifier._determine_pass_status(
        result, ["prd_coverage", "spec_compliance", "implementation_quality"]
    )
    assert passed is expected_pass


@pytest.mark.parametrize(
    "quality_score,has_issues,expected_pass",
    [
        (10, False, True),
        (9, False, True),
        (8, False, True),
        (7, False, True),
        (6, False, False),
        (10, True, False),  # Critical issues always fail
        (8, True, False),
    ],
)
def test_quality_score_thresholds(
    quality_score: int, has_issues: bool, expected_pass: bool
) -> None:
    """Test implementation quality pass thresholds."""
    verifier = PRDVerifier()
    result = VerificationResult(
        passed=False,
        report_path=".claude/loop/verification-report.md",
        timestamp="2026-03-15T12:00:00",
    )
    result.prd_coverage = {"coverage_percentage": 100.0}
    result.spec_compliance = {"compliance_percentage": 100.0}
    result.implementation_quality = {
        "code_quality_score": quality_score,
        "max_score": 10,
        "critical_issues": ["Issue"] if has_issues else [],
    }

    passed = verifier._determine_pass_status(
        result, ["prd_coverage", "spec_compliance", "implementation_quality"]
    )
    assert passed is expected_pass
