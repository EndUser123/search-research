#!/usr/bin/env python3
"""
Unit tests for post-hoc verification analyzer.

Tests verify that PostHocAnalyzer correctly:
- Generates RTM from plan
- Calculates TSR from evidence ledger
- Evaluates conversation completeness
- Returns comprehensive verification reports
"""

import json
import sys
from pathlib import Path

import pytest

# Add skill root to path for imports
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))

# Import after sys.path is set up
from tiers.post_hoc_analyzer import PostHocAnalyzer


# Test fixtures
@pytest.fixture
def complete_plan():
    """Plan with complete requirements and tasks."""
    return """# Plan: Complete Implementation Plan

## Problem Statement

The system needs:
1. User authentication
2. Data persistence
3. API endpoints

## Context Analysis

None needed for this test.

## Existing Implementation Discovery

None needed for this test.

## Test Discovery

None needed for this test.

## Proposed Solution

Implement authentication, persistence, and API.

## Implementation Plan

**TASK-001**: Add user authentication
- File: `src/auth.py`
- Action: Implement JWT authentication
- Points: 5
- Acceptance:
  - Users can log in with valid credentials
  - Invalid credentials are rejected

**TASK-002**: Add data persistence
- File: `src/database.py`
- Action: Implement SQLite database
- Points: 3
- Acceptance:
  - Database schema is created
  - Data can be saved and retrieved

**TASK-003**: Add API endpoints
- File: `src/api.py`
- Action: Implement REST API
- Points: 5
- Acceptance:
  - API endpoints respond correctly
  - Error handling is implemented

## Risks, Success Criteria, Dependencies

### Risks
- None

### Success Criteria
- All tests pass

### Dependencies
- None
"""


@pytest.fixture
def plan_with_orphan_requirements():
    """Plan with orphan requirements (requirements not mapped to tasks)."""
    return """# Plan: Plan with Orphan Requirements

## Problem Statement

The system needs:
1. User authentication
2. Data encryption
3. Audit logging

## Context Analysis

None needed for this test.

## Existing Implementation Discovery

None needed for this test.

## Test Discovery

None needed for this test.

## Proposed Solution

Implement authentication.

## Implementation Plan

**TASK-001**: Add user authentication
- File: `src/auth.py`
- Action: Implement JWT authentication
- Points: 5
- Acceptance:
  - Users can log in

## Risks, Success Criteria, Dependencies

### Risks
- None

### Success Criteria
- All tests pass

### Dependencies
- None
"""


@pytest.fixture
def complete_evidence_ledger(tmp_path):
    """Evidence ledger with all tasks complete (100% TSR)."""
    ledger_file = tmp_path / "evidence_ledger.json"

    ledger_data = {
        "version": "1.0",
        "terminal_id": "test_terminal",
        "task_list_id": None,
        "created_at": "2026-03-13T00:00:00",
        "last_updated": "2026-03-13T00:00:00",
        "tasks": {
            "TASK-001": {
                "description": "Add user authentication",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T00:00:00"}
                },
                "done": True,
                "done_at": "2026-03-13T00:00:00"
            },
            "TASK-002": {
                "description": "Add data persistence",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T00:00:00"}
                },
                "done": True,
                "done_at": "2026-03-13T00:00:00"
            },
            "TASK-003": {
                "description": "Add API endpoints",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T00:00:00"}
                },
                "done": True,
                "done_at": "2026-03-13T00:00:00"
            }
        }
    }

    ledger_file.write_text(json.dumps(ledger_data, indent=2))
    return str(ledger_file)


@pytest.fixture
def partial_evidence_ledger(tmp_path):
    """Evidence ledger with partial completion (66.7% TSR = 2/3)."""
    ledger_file = tmp_path / "evidence_ledger.json"

    ledger_data = {
        "version": "1.0",
        "terminal_id": "test_terminal",
        "task_list_id": None,
        "created_at": "2026-03-13T00:00:00",
        "last_updated": "2026-03-13T00:00:00",
        "tasks": {
            "TASK-001": {
                "description": "Complete task",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T00:00:00"}
                },
                "done": True,
                "done_at": "2026-03-13T00:00:00"
            },
            "TASK-002": {
                "description": "Complete task",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T00:00:00"}
                },
                "done": True,
                "done_at": "2026-03-13T00:00:00"
            },
            "TASK-003": {
                "description": "Incomplete task",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "GREEN": {"completed": False, "timestamp": "2026-03-13T00:00:00"}
                },
                "done": False
            }
        }
    }

    ledger_file.write_text(json.dumps(ledger_data, indent=2))
    return str(ledger_file)


@pytest.fixture
def low_tsr_evidence_ledger(tmp_path):
    """Evidence ledger with low TSR (50% = 1/2 complete, 1 blocked)."""
    ledger_file = tmp_path / "evidence_ledger.json"

    ledger_data = {
        "version": "1.0",
        "terminal_id": "test_terminal",
        "task_list_id": None,
        "created_at": "2026-03-13T00:00:00",
        "last_updated": "2026-03-13T00:00:00",
        "tasks": {
            "TASK-001": {
                "description": "Complete task",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T00:00:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T00:00:00"}
                },
                "done": True,
                "done_at": "2026-03-13T00:00:00"
            },
            "TASK-002": {
                "description": "Blocked task",
                "evidence": {},
                "done": False
            }
        }
    }

    ledger_file.write_text(json.dumps(ledger_data, indent=2))
    return str(ledger_file)


class TestPostHocAnalyzerRTM:
    """Test RTM generation in PostHocAnalyzer."""

    def test_generate_rtm_with_complete_plan(self, complete_plan):
        """Test RTM generation from plan with all requirements mapped."""
        analyzer = PostHocAnalyzer(plan_content=complete_plan)

        rtm = analyzer.generate_rtm()

        # Verify structure
        assert "requirements" in rtm
        assert "tasks" in rtm
        assert "statistics" in rtm
        assert "coverage_matrix" in rtm

        # Verify statistics
        stats = rtm["statistics"]
        assert stats["total_requirements"] == 3
        assert stats["total_tasks"] == 3
        assert stats["requirements_with_tasks"] == 3
        assert stats["requirements_without_tasks"] == 0
        assert stats["requirement_coverage"] == 100.0
        assert stats["task_coverage"] == 100.0
        assert stats["acceptance_coverage"] == 100.0

    def test_generate_rtm_with_orphan_requirements(self, plan_with_orphan_requirements):
        """Test RTM detects orphan requirements."""
        analyzer = PostHocAnalyzer(plan_content=plan_with_orphan_requirements)

        rtm = analyzer.generate_rtm()

        # Verify orphan requirements detected
        stats = rtm["statistics"]
        assert stats["total_requirements"] == 3
        assert stats["requirements_with_tasks"] == 1
        assert stats["requirements_without_tasks"] == 2
        assert stats["requirement_coverage"] == 33.3  # 1/3


class TestPostHocAnalyzerTSR:
    """Test TSR calculation in PostHocAnalyzer."""

    def test_calculate_tsr_all_complete(self, complete_plan, complete_evidence_ledger):
        """Test TSR calculation when all tasks are complete (100%)."""
        analyzer = PostHocAnalyzer(
            plan_content=complete_plan,
            evidence_ledger_path=complete_evidence_ledger
        )

        tsr = analyzer.calculate_tsr()

        assert tsr["total_attempted"] == 3
        assert tsr["completed"] == 3
        assert tsr["failed"] == 0
        assert tsr["blocked"] == 0
        assert tsr["tsr"] == 100.0

    def test_calculate_tsr_partial_completion(self, complete_plan, partial_evidence_ledger):
        """Test TSR calculation with partial completion (66.7%)."""
        analyzer = PostHocAnalyzer(
            plan_content=complete_plan,
            evidence_ledger_path=partial_evidence_ledger
        )

        tsr = analyzer.calculate_tsr()

        assert tsr["total_attempted"] == 3
        assert tsr["completed"] == 2
        assert tsr["failed"] == 1
        assert tsr["blocked"] == 0
        assert tsr["tsr"] == 66.67

    def test_calculate_tsr_low_completion(self, complete_plan, low_tsr_evidence_ledger):
        """Test TSR calculation with low completion (50%)."""
        analyzer = PostHocAnalyzer(
            plan_content=complete_plan,
            evidence_ledger_path=low_tsr_evidence_ledger
        )

        tsr = analyzer.calculate_tsr()

        assert tsr["total_attempted"] == 2
        assert tsr["completed"] == 1
        assert tsr["failed"] == 0
        assert tsr["blocked"] == 1
        assert tsr["tsr"] == 50.0

    def test_calculate_tsr_no_evidence_ledger(self, complete_plan):
        """Test TSR calculation when evidence ledger is not provided."""
        analyzer = PostHocAnalyzer(plan_content=complete_plan)

        tsr = analyzer.calculate_tsr()

        assert tsr["total_attempted"] == 0
        assert tsr["completed"] == 0
        assert tsr["failed"] == 0
        assert tsr["blocked"] == 0
        assert tsr["tsr"] == 0.0
        assert "note" in tsr


class TestPostHocAnalyzerEvaluation:
    """Test conversation completeness evaluation in PostHocAnalyzer."""

    def test_evaluate_completeness_all_complete(self, complete_plan, complete_evidence_ledger):
        """Test evaluation with complete work (100% TSR, 100% RTM)."""
        analyzer = PostHocAnalyzer(
            plan_content=complete_plan,
            evidence_ledger_path=complete_evidence_ledger
        )

        rtm = analyzer.generate_rtm()
        tsr = analyzer.calculate_tsr()

        evaluation = analyzer.evaluate_conversation_completeness(rtm, tsr)

        assert evaluation["overall_score"] == 100.0
        assert evaluation["requirements_coverage"] == 100.0
        assert evaluation["task_completion"] == 100.0
        assert evaluation["evidence_quality"] == 100.0
        assert len(evaluation["findings"]) == 0
        assert len(evaluation["recommendations"]) == 1
        assert "All verification checks passed" in evaluation["recommendations"][0]

    def test_evaluate_completeness_partial_tsr(self, complete_plan, partial_evidence_ledger):
        """Test evaluation with partial TSR (66.7%)."""
        analyzer = PostHocAnalyzer(
            plan_content=complete_plan,
            evidence_ledger_path=partial_evidence_ledger
        )

        rtm = analyzer.generate_rtm()
        tsr = analyzer.calculate_tsr()

        evaluation = analyzer.evaluate_conversation_completeness(rtm, tsr)

        assert evaluation["task_completion"] == 66.67
        assert evaluation["overall_score"] < 95.0

        # Should have HIGH severity finding for low TSR
        high_findings = [f for f in evaluation["findings"] if f.get("severity") == "HIGH"]
        assert len(high_findings) > 0
        assert any("low_tsr" in f.get("category", "") for f in high_findings)

    def test_evaluate_completeness_orphan_requirements(self, plan_with_orphan_requirements, complete_evidence_ledger):
        """Test evaluation with orphan requirements."""
        analyzer = PostHocAnalyzer(
            plan_content=plan_with_orphan_requirements,
            evidence_ledger_path=complete_evidence_ledger
        )

        rtm = analyzer.generate_rtm()
        tsr = analyzer.calculate_tsr()

        evaluation = analyzer.evaluate_conversation_completeness(rtm, tsr)

        # 1/3 = 33.333...%, check approximate value
        assert abs(evaluation["requirements_coverage"] - 33.33) < 0.01

        # Should have HIGH severity finding for orphan requirements
        high_findings = [f for f in evaluation["findings"] if f.get("severity") == "HIGH"]
        assert len(high_findings) > 0
        assert any("orphan_requirements" in f.get("category", "") for f in high_findings)


class TestPostHocAnalyzerRunAnalysis:
    """Test complete post-hoc analysis workflow."""

    def test_run_analysis_complete_work(self, complete_plan, complete_evidence_ledger):
        """Test complete analysis with all work done."""
        analyzer = PostHocAnalyzer(
            plan_content=complete_plan,
            evidence_ledger_path=complete_evidence_ledger
        )

        report = analyzer.run_analysis()

        # Verify overall status
        assert report["overall_status"] == "PASS"
        assert report["overall_score"] == 100.0

        # Verify summary
        summary = report["summary"]
        assert summary["requirements_coverage"] == 100.0
        assert summary["task_completion"] == 100.0
        assert summary["evidence_quality"] == 100.0
        assert summary["total_findings"] == 0
        assert summary["high_severity_findings"] == 0

        # Verify RTM, TSR, and evaluation present
        assert "rtm" in report
        assert "tsr" in report
        assert "evaluation" in report

    def test_run_analysis_incomplete_work(self, plan_with_orphan_requirements, partial_evidence_ledger):
        """Test complete analysis with incomplete work."""
        analyzer = PostHocAnalyzer(
            plan_content=plan_with_orphan_requirements,
            evidence_ledger_path=partial_evidence_ledger
        )

        report = analyzer.run_analysis()

        # Verify overall status FAIL
        assert report["overall_status"] == "FAIL"
        assert report["overall_score"] < 95.0

        # Verify summary shows failures
        summary = report["summary"]
        assert summary["total_findings"] > 0
        assert summary["high_severity_findings"] > 0

    def test_run_analysis_without_evidence_ledger(self, complete_plan):
        """Test complete analysis without evidence ledger."""
        analyzer = PostHocAnalyzer(plan_content=complete_plan)

        report = analyzer.run_analysis()

        # Should still generate report but TSR will be 0
        assert report["tsr"]["tsr"] == 0.0
        assert report["overall_status"] == "FAIL"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
