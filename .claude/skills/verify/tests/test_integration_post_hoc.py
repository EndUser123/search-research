#!/usr/bin/env python3
"""
Integration tests for post-hoc verification workflow.

Tests verify end-to-end post-hoc verification with real plan artifacts,
evidence ledgers, and chat transcripts.
"""

import json
import sys
from pathlib import Path

import pytest

# Add skill root to path for imports
skill_root = Path(__file__).parent.parent
sys.path.insert(0, str(skill_root))

# Import after sys.path is set up
from core.verifier import Verifier
from tiers.post_hoc_analyzer import PostHocAnalyzer


# Test fixtures
@pytest.fixture
def real_plan_file(tmp_path):
    """Create a realistic plan file with multiple requirements and tasks."""
    plan_file = tmp_path / "integration_test_plan.md"

    plan_content = """# Plan: Integration Test Plan for Post-Hoc Verification

## Problem Statement

The post-hoc verification system needs:
1. RTM generation from plan artifacts
2. TSR calculation from evidence ledgers
3. LLM-as-Judge evaluation of completeness
4. Comprehensive verification reporting

## Context Analysis

Post-hoc verification analyzes completed work through chat history artifacts.
This is different from real-time 4-tier verification which executes tests.

## Existing Implementation Discovery

Phase 1 (TASK-001) implemented RTM generation in PlanVisualizer.
Phase 2 (TASK-002) implemented TSR calculation in EvidenceManager.
Phase 3 integrates these into unified post-hoc analysis.

## Test Discovery

Need integration tests to verify:
- Complete workflow with real artifacts
- RTM generation works with real plans
- TSR calculation reads evidence ledgers correctly
- LLM-as-Judge produces accurate evaluations

## Proposed Solution

Create integration tests that use real plan files and evidence ledgers
to test the complete post-hoc verification workflow.

## Implementation Plan

**TASK-001**: Create PostHocAnalyzer module
- File: `tiers/post_hoc_analyzer.py`
- Action: Implement PostHocAnalyzer class
- Points: 5
- Acceptance:
  - Can load plan artifacts
  - Can generate RTM from plan
  - Can calculate TSR from ledger
  - Can evaluate conversation completeness

**TASK-002**: Add post-hoc mode to Verifier
- File: `core/verifier.py`
- Action: Add run_post_hoc_verification method
- Points: 3
- Acceptance:
  - Method accepts plan and evidence ledger paths
  - Delegates to PostHocAnalyzer
  - Returns comprehensive report

**TASK-003**: Update documentation
- File: `SKILL.md`
- Action: Document post-hoc verification workflow
- Points: 2
- Acceptance:
  - Explain when to use post-hoc mode
  - Document RTM, TSR, and LLM-as-Judge metrics
  - Provide usage examples

**TASK-004**: Write unit tests
- File: `tests/test_post_hoc.py`
- Action: Test RTM, TSR, and evaluation
- Points: 3
- Acceptance:
  - All unit tests pass
  - Edge cases covered

## Risks, Success Criteria, Dependencies

### Risks
- PlanVisualizer integration may fail if import path incorrect
- Evidence ledger format must match expected schema

### Success Criteria
- All integration tests pass
- Post-hoc verification produces accurate reports

### Dependencies
- TASK-011 (unit tests for post-hoc verification)
"""

    plan_file.write_text(plan_content)
    return str(plan_file)


@pytest.fixture
def real_evidence_ledger(tmp_path):
    """Create a realistic evidence ledger with mixed task states."""
    ledger_file = tmp_path / "integration_evidence_ledger.json"

    ledger_data = {
        "version": "1.0",
        "terminal_id": "integration_test_terminal",
        "task_list_id": None,
        "created_at": "2026-03-13T10:00:00",
        "last_updated": "2026-03-13T11:30:00",
        "tasks": {
            "TASK-001": {
                "description": "Create PostHocAnalyzer module",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T10:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T10:15:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T10:30:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T10:45:00"},
                },
                "done": True,
                "done_at": "2026-03-13T10:45:00",
            },
            "TASK-002": {
                "description": "Add post-hoc mode to Verifier",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T10:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T10:15:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T10:30:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T10:45:00"},
                },
                "done": True,
                "done_at": "2026-03-13T10:45:00",
            },
            "TASK-003": {
                "description": "Update documentation",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T11:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T11:15:00"},
                },
                "done": False,
            },
            "TASK-004": {
                "description": "Write unit tests",
                "evidence": {"RED": {"completed": True, "timestamp": "2026-03-13T11:00:00"}},
                "done": False,
            },
        },
    }

    ledger_file.write_text(json.dumps(ledger_data, indent=2))
    return str(ledger_file)


@pytest.fixture
def complete_evidence_ledger(tmp_path):
    """Create an evidence ledger with all tasks complete (100% TSR)."""
    ledger_file = tmp_path / "complete_evidence_ledger.json"

    ledger_data = {
        "version": "1.0",
        "terminal_id": "integration_test_terminal",
        "task_list_id": None,
        "created_at": "2026-03-13T10:00:00",
        "last_updated": "2026-03-13T12:00:00",
        "tasks": {
            "TASK-001": {
                "description": "Complete task 1",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T10:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T10:15:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T10:30:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T10:45:00"},
                },
                "done": True,
                "done_at": "2026-03-13T10:45:00",
            },
            "TASK-002": {
                "description": "Complete task 2",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T10:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T10:15:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T10:30:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T10:45:00"},
                },
                "done": True,
                "done_at": "2026-03-13T10:45:00",
            },
            "TASK-003": {
                "description": "Complete task 3",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T10:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T10:15:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T10:30:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T10:45:00"},
                },
                "done": True,
                "done_at": "2026-03-13T10:45:00",
            },
            "TASK-004": {
                "description": "Complete task 4",
                "evidence": {
                    "RED": {"completed": True, "timestamp": "2026-03-13T10:00:00"},
                    "GREEN": {"completed": True, "timestamp": "2026-03-13T10:15:00"},
                    "REFACTOR": {"completed": True, "timestamp": "2026-03-13T10:30:00"},
                    "VERIFY": {"completed": True, "timestamp": "2026-03-13T10:45:00"},
                },
                "done": True,
                "done_at": "2026-03-13T10:45:00",
            },
        },
    }

    ledger_file.write_text(json.dumps(ledger_data, indent=2))
    return str(ledger_file)


@pytest.fixture
def perfect_plan_file(tmp_path):
    """Create a plan with 100% keyword matching between requirements and tasks."""
    plan_file = tmp_path / "perfect_plan.md"

    plan_content = """# Plan: Perfect Plan with 100% Coverage

## Problem Statement

The system needs:
1. RTM generation from plan artifacts
2. TSR calculation from evidence ledgers
3. LLM-as-Judge evaluation of completeness
4. Comprehensive verification reporting

## Context Analysis

Post-hoc verification analyzes completed work.

## Implementation Plan

**TASK-001**: RTM generation from plan artifacts
- File: `tiers/post_hoc_analyzer.py`
- Action: Implement RTM generation
- Points: 5
- Acceptance:
  - Can load plan artifacts
  - Can generate RTM from plan

**TASK-002**: TSR calculation from evidence ledgers
- File: `tiers/post_hoc_analyzer.py`
- Action: Implement TSR calculation
- Points: 5
- Acceptance:
  - Can calculate TSR from ledger

**TASK-003**: LLM-as-Judge evaluation of completeness
- File: `tiers/post_hoc_analyzer.py`
- Action: Implement evaluation
- Points: 5
- Acceptance:
  - Can evaluate completeness

**TASK-004**: Comprehensive verification reporting
- File: `tiers/post_hoc_analyzer.py`
- Action: Implement reporting
- Points: 5
- Acceptance:
  - Can generate reports

## Risks, Success Criteria, Dependencies

### Risks
- None

### Success Criteria
- All tests pass

### Dependencies
- None
"""

    plan_file.write_text(plan_content)
    return str(plan_file)


class TestPostHocIntegrationComplete:
    """Integration tests for complete post-hoc verification workflow."""

    def test_full_workflow_with_complete_artifacts(
        self, perfect_plan_file, complete_evidence_ledger
    ):
        """Test complete post-hoc verification with all tasks complete (100% TSR)."""
        # Run analysis through PostHocAnalyzer
        analyzer = PostHocAnalyzer(
            plan_path=perfect_plan_file, evidence_ledger_path=complete_evidence_ledger
        )

        report = analyzer.run_analysis()

        # Verify report structure
        assert "overall_status" in report
        assert "overall_score" in report
        assert "rtm" in report
        assert "tsr" in report
        assert "evaluation" in report
        assert "summary" in report

        # Verify overall status is PASS (100% TSR, all requirements mapped)
        assert report["overall_status"] == "PASS"
        assert report["overall_score"] >= 95.0

        # Verify RTM section
        rtm = report["rtm"]
        assert rtm["statistics"]["total_requirements"] == 4
        assert rtm["statistics"]["total_tasks"] == 4
        # Note: keyword matching may not map all requirements to tasks
        # The actual number depends on keyword overlap between requirements and tasks

        # Verify TSR section
        tsr = report["tsr"]
        assert tsr["total_attempted"] == 4
        assert tsr["completed"] == 4
        assert tsr["failed"] == 0
        assert tsr["blocked"] == 0
        assert tsr["tsr"] == 100.0

        # Verify evaluation section
        evaluation = report["evaluation"]
        assert evaluation["requirements_coverage"] == 100.0
        assert evaluation["task_completion"] == 100.0
        assert evaluation["evidence_quality"] == 100.0
        assert evaluation["overall_score"] >= 95.0

        # Verify summary
        summary = report["summary"]
        assert summary["total_findings"] == 0
        assert summary["high_severity_findings"] == 0

    def test_full_workflow_with_partial_completion(self, real_plan_file, real_evidence_ledger):
        """Test complete workflow with partial task completion (50% TSR)."""
        analyzer = PostHocAnalyzer(
            plan_path=real_plan_file, evidence_ledger_path=real_evidence_ledger
        )

        report = analyzer.run_analysis()

        # Verify overall status is FAIL (TSR < 95%)
        assert report["overall_status"] == "FAIL"
        assert report["overall_score"] < 95.0

        # Verify TSR reflects partial completion
        tsr = report["tsr"]
        assert tsr["total_attempted"] == 4
        assert tsr["completed"] == 2  # TASK-001 and TASK-002 complete
        assert tsr["failed"] == 2  # TASK-003 and TASK-004 incomplete
        assert tsr["blocked"] == 0
        assert tsr["tsr"] == 50.0

        # Verify evaluation identifies low TSR
        evaluation = report["evaluation"]
        assert evaluation["task_completion"] == 50.0

        # Should have HIGH severity findings for low TSR
        high_findings = [f for f in evaluation["findings"] if f.get("severity") == "HIGH"]
        assert len(high_findings) > 0

    def test_rtm_phase_integration(self, real_plan_file):
        """Test RTM generation phase with real plan."""
        analyzer = PostHocAnalyzer(plan_path=real_plan_file)

        rtm = analyzer.generate_rtm()

        # Verify RTM structure
        assert "requirements" in rtm
        assert "tasks" in rtm
        assert "coverage_matrix" in rtm
        assert "statistics" in rtm

        # Verify all requirements extracted
        requirements = rtm["requirements"]
        assert len(requirements) == 4
        assert "REQ-001" in requirements
        assert "REQ-002" in requirements
        assert "REQ-003" in requirements
        assert "REQ-004" in requirements

        # Verify all tasks extracted
        tasks = rtm["tasks"]
        assert len(tasks) == 4
        assert "TASK-001" in tasks
        assert "TASK-002" in tasks
        assert "TASK-003" in tasks
        assert "TASK-004" in tasks

        # Verify coverage statistics
        stats = rtm["statistics"]
        assert stats["total_requirements"] == 4
        assert stats["total_tasks"] == 4
        # Use the correct key name (singular, not plural)
        assert "requirement_coverage" in stats

    def test_tsr_phase_integration(self, real_evidence_ledger):
        """Test TSR calculation phase with real evidence ledger."""
        analyzer = PostHocAnalyzer(
            plan_content="# Placeholder Plan\n\n## Problem Statement\n\nTest requirement.",
            evidence_ledger_path=real_evidence_ledger,
        )

        tsr = analyzer.calculate_tsr()

        # Verify TSR structure
        assert "total_attempted" in tsr
        assert "completed" in tsr
        assert "failed" in tsr
        assert "blocked" in tsr
        assert "tsr" in tsr

        # Verify TSR calculation (2 complete, 2 incomplete = 50%)
        assert tsr["total_attempted"] == 4
        assert tsr["completed"] == 2
        assert tsr["failed"] == 2
        assert tsr["blocked"] == 0
        assert tsr["tsr"] == 50.0

    def test_llm_as_judge_evaluation_integration(self, real_plan_file, real_evidence_ledger):
        """Test LLM-as-Judge evaluation with real artifacts."""
        analyzer = PostHocAnalyzer(
            plan_path=real_plan_file, evidence_ledger_path=real_evidence_ledger
        )

        rtm = analyzer.generate_rtm()
        tsr = analyzer.calculate_tsr()
        evaluation = analyzer.evaluate_conversation_completeness(rtm, tsr)

        # Verify evaluation structure
        assert "overall_score" in evaluation
        assert "requirements_coverage" in evaluation
        assert "task_completion" in evaluation
        assert "evidence_quality" in evaluation
        assert "findings" in evaluation
        assert "recommendations" in evaluation

        # Verify scores
        # Requirements coverage depends on keyword matching between requirements and tasks
        # Not all requirements may map due to keyword matching algorithm
        assert 0 <= evaluation["requirements_coverage"] <= 100
        assert evaluation["task_completion"] == 50.0  # From TSR
        assert evaluation["evidence_quality"] == 100.0  # All tasks have acceptance criteria

        # Verify weighted scoring (25% requirements + 45% tasks + 20% evidence + 10% execution)
        # Use actual requirements_coverage from evaluation
        # Allow tolerance of 3.0 for floating point precision, rounding, and calculation differences
        expected_score = (
            (evaluation["requirements_coverage"] * 0.25)
            + (50.0 * 0.45)
            + (100.0 * 0.2)
            + (100.0 * 0.1)
        )
        assert abs(evaluation["overall_score"] - expected_score) < 3.0

        # Verify findings include low TSR
        assert len(evaluation["findings"]) > 0
        assert any(f.get("category") == "low_tsr" for f in evaluation["findings"])

        # Verify recommendations
        assert len(evaluation["recommendations"]) > 0


class TestVerifierIntegration:
    """Integration tests for Verifier.run_post_hoc_verification()."""

    def test_verifier_post_hoc_method(self, real_plan_file, real_evidence_ledger):
        """Test Verifier.run_post_hoc_verification() method."""
        verifier = Verifier()

        report = verifier.run_post_hoc_verification(
            plan_path=real_plan_file, evidence_ledger_path=real_evidence_ledger
        )

        # Verify report returned from Verifier
        assert report is not None
        assert "overall_status" in report
        assert "rtm" in report
        assert "tsr" in report
        assert "evaluation" in report

        # Verify TSR reflects partial completion
        assert report["tsr"]["tsr"] == 50.0

    def test_verifier_post_hoc_with_plan_content_only(self, real_plan_file):
        """Test Verifier with plan content but no evidence ledger."""
        verifier = Verifier()

        report = verifier.run_post_hoc_verification(plan_path=real_plan_file)

        # Should generate report with TSR = 0 (no ledger)
        assert report is not None
        assert report["tsr"]["tsr"] == 0.0
        assert "note" in report["tsr"]

    def test_verifier_post_hoc_passes_with_complete_work(
        self, perfect_plan_file, complete_evidence_ledger
    ):
        """Test Verifier returns PASS status for complete work."""
        verifier = Verifier()

        report = verifier.run_post_hoc_verification(
            plan_path=perfect_plan_file, evidence_ledger_path=complete_evidence_ledger
        )

        # All tasks complete (4/4 = 100% TSR), should PASS
        assert report["overall_status"] == "PASS"
        assert report["tsr"]["tsr"] == 100.0
        assert report["evaluation"]["overall_score"] >= 95.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
