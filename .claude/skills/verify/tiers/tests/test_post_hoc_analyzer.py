#!/usr/bin/env python3
"""
Tests for PostHocAnalyzer with ImplementationVerifier integration.
"""

import tempfile
from pathlib import Path

from tiers.post_hoc_analyzer import PostHocAnalyzer


class TestPostHocAnalyzerExecutionVerification:
    """Test execution verification integration."""

    def test_verify_execution_with_existing_files(self):
        """Test that verify_execution passes for files that exist."""
        # Create temporary files
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f1:
            f1.write("test content 1")
            file1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f2:
            f2.write("test content 2")
            file2 = f2.name

        try:
            analyzer = PostHocAnalyzer(
                plan_content="# Test Plan\n\n## Tasks\n- [ ] TASK-001: Test task",
                claimed_files=[file1, file2],
            )

            findings = analyzer.verify_execution()

            # Should have INFO findings (files verified)
            assert len(findings) == 2
            assert all(f["severity"] == "INFO" for f in findings)
            assert all(f["category"] == "execution_verification" for f in findings)
            assert all("File verified" in f["description"] for f in findings)

        finally:
            # Cleanup
            Path(file1).unlink(missing_ok=True)
            Path(file2).unlink(missing_ok=True)

    def test_verify_execution_with_missing_files(self):
        """Test that verify_execution detects missing files."""
        missing_file = "P:/nonexistent/path/to/file.py"

        analyzer = PostHocAnalyzer(
            plan_content="# Test Plan\n\n## Tasks\n- [ ] TASK-001: Test task",
            claimed_files=[missing_file],
        )

        findings = analyzer.verify_execution()

        # Should have HIGH severity finding for missing file
        assert len(findings) == 1
        assert findings[0]["severity"] == "HIGH"
        assert findings[0]["category"] == "execution_verification"
        assert (
            "not created" in findings[0]["description"].lower()
            or "does not exist" in findings[0]["description"].lower()
        )

    def test_verify_execution_with_mixed_files(self):
        """Test that verify_execution handles mix of existing and missing files."""
        # Create one existing file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("test content")
            existing_file = f.name

        missing_file = "P:/nonexistent/path/to/file.py"

        try:
            analyzer = PostHocAnalyzer(
                plan_content="# Test Plan\n\n## Tasks\n- [ ] TASK-001: Test task",
                claimed_files=[existing_file, missing_file],
            )

            findings = analyzer.verify_execution()

            # Should have 2 findings: INFO for existing, HIGH for missing
            assert len(findings) == 2

            severities = {f["severity"] for f in findings}
            assert "INFO" in severities
            assert "HIGH" in severities

        finally:
            Path(existing_file).unlink(missing_ok=True)

    def test_verify_execution_with_no_files(self):
        """Test that verify_execution returns empty list when no files claimed."""
        analyzer = PostHocAnalyzer(
            plan_content="# Test Plan\n\n## Tasks\n- [ ] TASK-001: Test task"
        )

        findings = analyzer.verify_execution()

        # Should return empty list
        assert findings == []

    def test_verify_execution_with_custom_files_list(self):
        """Test that verify_execution uses provided files list parameter."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("test content")
            test_file = f.name

        try:
            analyzer = PostHocAnalyzer(
                plan_content="# Test Plan\n\n## Tasks\n- [ ] TASK-001: Test task"
            )

            # Pass custom files list (different from claimed_files)
            findings = analyzer.verify_execution(files=[test_file])

            # Should verify the custom list
            assert len(findings) == 1
            assert findings[0]["severity"] == "INFO"

        finally:
            Path(test_file).unlink(missing_ok=True)

    def test_get_implementation_verifier_lazy_load(self):
        """Test that ImplementationVerifier is lazy-loaded."""
        analyzer = PostHocAnalyzer(
            plan_content="# Test Plan\n\n## Tasks\n- [ ] TASK-001: Test task"
        )

        # First call should load the verifier
        verifier1 = analyzer._get_implementation_verifier()
        assert verifier1 is not None

        # Second call should return cached instance
        verifier2 = analyzer._get_implementation_verifier()
        assert verifier1 is verifier2


class TestPostHocAnalyzerIntegration:
    """Test PostHocAnalyzer run_analysis with execution verification."""

    def test_run_analysis_includes_execution_verification(self):
        """Test that run_analysis includes execution verification by default."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("test content")
            test_file = f.name

        try:
            # Create minimal plan with RTM structure
            plan_content = """# Test Plan

## Requirements
- [REQ-001] Test requirement

## Tasks
- [x] TASK-001: Test task
  - Requirements: REQ-001
  - Acceptance: Tests pass
"""

            analyzer = PostHocAnalyzer(plan_content=plan_content, claimed_files=[test_file])

            report = analyzer.run_analysis(include_execution=True)

            # Should have execution_verification section
            assert "execution_verification" in report
            assert report["execution_verification"]["included"] is True
            assert "findings" in report["execution_verification"]
            assert "score" in report["execution_verification"]

            # Should have execution score in summary
            assert "execution_verification" in report["summary"]

        finally:
            Path(test_file).unlink(missing_ok=True)

    def test_run_analysis_exclude_execution_verification(self):
        """Test that run_analysis can exclude execution verification."""
        analyzer = PostHocAnalyzer(
            plan_content="# Test Plan\n\n## Tasks\n- [x] TASK-001: Test task"
        )

        report = analyzer.run_analysis(include_execution=False)

        # Should NOT have execution_verification section
        assert report["execution_verification"] is None

    def test_run_analysis_execution_failure_causes_fail_status(self):
        """Test that execution verification failure causes overall FAIL status."""
        missing_file = "P:/nonexistent/path/to/file.py"

        plan_content = """# Test Plan

## Requirements
- [REQ-001] Test requirement

## Tasks
- [x] TASK-001: Test task
  - Requirements: REQ-001
  - Acceptance: Tests pass
"""

        analyzer = PostHocAnalyzer(plan_content=plan_content, claimed_files=[missing_file])

        report = analyzer.run_analysis(include_execution=True)

        # Should have FAIL status due to execution verification failure
        assert report["overall_status"] == "FAIL"
        assert report["execution_verification"]["score"] < 100

    def test_evaluate_conversation_completeness_with_execution_findings(self):
        """Test evaluate_conversation_completeness incorporates execution findings."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".py") as f:
            f.write("test content")
            test_file = f.name

        try:
            # Create minimal RTM and TSR
            rtm = {
                "requirements": {},
                "tasks": {},
                "statistics": {
                    "total_requirements": 0,
                    "requirements_with_tasks": 0,
                    "total_tasks": 1,
                    "tasks_with_acceptance_criteria": 1,
                },
            }

            tsr = {"total_attempted": 1, "completed": 1, "failed": 0, "blocked": 0, "tsr": 100.0}

            # Get execution findings (should be INFO for existing file)
            analyzer = PostHocAnalyzer(plan_content="# Test Plan", claimed_files=[test_file])
            execution_findings = analyzer.verify_execution()

            evaluation = analyzer.evaluate_conversation_completeness(rtm, tsr, execution_findings)

            # Should have execution_verification score
            assert "execution_verification" in evaluation
            assert evaluation["execution_verification"] == 100.0

            # Overall score should include execution verification (10% weight)
            expected_score = (
                100.0 * 0.25  # requirements_coverage
                + 100.0 * 0.45  # task_completion
                + 100.0 * 0.2  # evidence_quality
                + 100.0 * 0.1  # execution_verification
            )
            assert evaluation["overall_score"] == expected_score

        finally:
            Path(test_file).unlink(missing_ok=True)


class TestPostHocAnalyzerBackwardCompatibility:
    """Test backward compatibility - existing functionality still works."""

    def test_generate_rtm_still_works(self):
        """Test that generate_rtm still works after changes."""
        plan_content = """# Test Plan

## Requirements
- [REQ-001] Test requirement

## Tasks
- [x] TASK-001: Test task
  - Requirements: REQ-001
"""

        analyzer = PostHocAnalyzer(plan_content=plan_content)

        rtm = analyzer.generate_rtm()

        assert "requirements" in rtm
        assert "tasks" in rtm
        assert "statistics" in rtm

    def test_calculate_tsr_with_no_ledger(self):
        """Test that calculate_tsr handles missing ledger gracefully."""
        analyzer = PostHocAnalyzer(plan_content="# Test Plan")

        tsr = analyzer.calculate_tsr()

        assert tsr["tsr"] == 0.0
        assert "note" in tsr

    def test_evaluate_conversation_completeness_without_execution(self):
        """Test that evaluate_conversation_completeness works without execution findings."""
        rtm = {
            "requirements": {},
            "tasks": {},
            "statistics": {
                "total_requirements": 0,
                "requirements_with_tasks": 0,
                "total_tasks": 1,
                "tasks_with_acceptance_criteria": 1,
            },
        }

        tsr = {"total_attempted": 1, "completed": 1, "failed": 0, "blocked": 0, "tsr": 100.0}

        analyzer = PostHocAnalyzer(plan_content="# Test Plan")
        evaluation = analyzer.evaluate_conversation_completeness(rtm, tsr)

        # Should default execution_verification to 100%
        assert evaluation["execution_verification"] == 100.0
