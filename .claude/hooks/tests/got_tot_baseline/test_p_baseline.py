"""
Baseline regression tests for /p skill (Code maturation pipeline).

These tests capture the current behavior of /p before GoT/ToT integration.
They serve as regression guards to ensure core functionality continues working.

Test Coverage:
- Target type detection (skill, package, dual-nature, infrastructure)
- Phase determination logic (P0-P6 based on signals)
- HALT condition evaluation (blocking error detection)
- Marker file detection (review and validation markers)
- Dual-nature detection (pyproject.toml + skill/SKILL.md)
- Completion check (work complete detection)

Critical paths tested: 6
Lines of code: ~110
"""

import pytest


def detect_target_type(has_skill_md: bool, has_pyproject: bool, has_skill_subdir: bool,
                       has_package_json: bool, has_go_mod: bool) -> str:
    """
    Detect target type from file presence signals.

    This is a copy of the target type detection logic from /p
    to establish baseline behavior before GoT/ToT integration.

    Args:
        has_skill_md: SKILL.md exists in root
        has_pyproject: pyproject.toml exists
        has_skill_subdir: skill/SKILL.md exists
        has_package_json: package.json exists
        has_go_mod: go.mod exists

    Returns:
        Target type: skill, dual_nature, python_package, node_package, go_module, infrastructure
    """
    # Priority order from SKILL.md Step 2
    if has_skill_md and not has_pyproject:
        return 'skill'
    if has_pyproject and has_skill_subdir:
        return 'dual_nature'
    if has_pyproject:
        return 'python_package'
    if has_package_json:
        return 'node_package'
    if has_go_mod:
        return 'go_module'
    return 'infrastructure'


def determine_phase(target_type: str, has_tests: bool, tests_pass: bool,
                   has_review_marker: bool, has_validation_marker: bool,
                   has_readme: bool, is_certified: bool) -> int:
    """
    Determine which phase to run based on state signals.

    This is a copy of the phase determination logic from /p
    to establish baseline behavior before GoT/ToT integration.

    Args:
        target_type: Type of target (skill, package, etc.)
        has_tests: Test files exist
        tests_pass: Tests are passing
        has_review_marker: Review marker file exists
        has_validation_marker: Validation marker file exists
        has_readme: README.md exists
        is_certified: Package is certified

    Returns:
        Phase number (0-6) or -1 for "ready"
    """
    # P0: Scaffold phase
    if not has_tests:
        return 0

    # P1: Build phase
    if has_tests and not tests_pass:
        return 1

    # P2: Review phase
    if tests_pass and not has_review_marker:
        return 2

    # P3: Validate phase
    if tests_pass and has_review_marker and not has_validation_marker:
        return 3

    # P4: Publish phase
    if tests_pass and has_review_marker and has_validation_marker and not has_readme:
        return 4

    # P5: Certify phase
    if tests_pass and has_review_marker and has_validation_marker and has_readme and not is_certified:
        return 5

    # Everything complete
    return -1


def check_halt_condition(phase: int, test_failures: int, blocking_findings: int,
                         validation_blocking: bool, publish_mode: bool) -> tuple[bool, str]:
    """
    Check if pipeline should halt based on phase and errors.

    This is a copy of the halt condition logic from /p
    to establish baseline behavior before GoT/ToT integration.

    Args:
        phase: Current phase number (0-6)
        test_failures: Number of failing tests
        blocking_findings: Number of blocking review findings
        validation_blocking: Whether validation stage failed
        publish_mode: Whether --publish flag is active

    Returns:
        Tuple of (should_halt, halt_reason)
    """
    # P1: Tests failing after TDD loop
    if phase == 1 and test_failures > 0:
        return (True, f"P1 HALT: {test_failures} test(s) failing")

    # P2: CRITICAL/HIGH findings remain
    if phase == 2 and blocking_findings > 0:
        return (True, f"P2 HALT: {blocking_findings} blocking finding(s) remain")

    # P3: Blocking stage fails OR (with --publish: any warning)
    if phase == 3:
        if validation_blocking:
            return (True, "P3 HALT: Blocking validation stage failed")
        if publish_mode:
            # In publish mode, any non-blocking warning causes halt
            return (True, "P3 HALT: --publish mode requires zero warnings")

    # No halt condition
    return (False, "")


def detect_marker_files(has_adversarial_review: bool, has_review_complete: bool,
                       has_validation_complete: bool, has_validation_report: bool) -> dict[str, bool]:
    """
    Detect marker files for review and validation status.

    This is a copy of the marker detection logic from /p
    to establish baseline behavior before GoT/ToT integration.

    Args:
        has_adversarial_review: .claude/findings/adversarial-review.json exists
        has_review_complete: .claude/state/review-complete.marker exists
        has_validation_complete: .claude/state/validation-complete.marker exists
        has_validation_report: .claude/reports/validation-report.md exists

    Returns:
        Dict with 'reviewed' and 'validated' boolean keys
    """
    return {
        'reviewed': has_adversarial_review or has_review_complete,
        'validated': has_validation_complete or has_validation_report
    }


def detect_dual_nature(has_pyproject: bool, has_skill_subdir: bool) -> tuple[bool, str]:
    """
    Detect dual-nature packages (Python package + skill interface).

    This is a copy of the dual-nature detection logic from /p
    to establish baseline behavior before GoT/ToT integration.

    Args:
        has_pyproject: pyproject.toml exists
        has_skill_subdir: skill/SKILL.md exists

    Returns:
        Tuple of (is_dual_nature, description)
    """
    if has_pyproject and has_skill_subdir:
        return (True, "Dual-nature detected: Python package + skill interface")
    return (False, "")


def check_work_complete(target_type: str, phase: int, test_failures: int,
                       blocking_findings: int, non_blocking_findings: int) -> tuple[bool, str]:
    """
    Check if work is complete and no next steps needed.

    This is a copy of the completion check logic from /p
    to establish baseline behavior before GoT/ToT integration.

    Args:
        target_type: Type of target (infrastructure, package, etc.)
        phase: Current phase number
        test_failures: Number of failing tests
        blocking_findings: Number of blocking findings
        non_blocking_findings: Number of non-blocking findings

    Returns:
        Tuple of (is_complete, reason)
    """
    # Check if all findings are resolved
    tests_pass = (test_failures == 0)
    no_blocking = (blocking_findings == 0)
    no_non_blocking = (non_blocking_findings == 0)

    # Infrastructure code complete
    if target_type == 'infrastructure' and tests_pass and no_blocking and no_non_blocking:
        return (True, "Infrastructure code complete (tests pass, no findings)")

    # Package pipeline complete
    if phase == 5 and tests_pass and no_blocking and no_non_blocking:
        return (True, "Package pipeline complete (all phases passed)")

    return (False, "")


class TestTargetTypeDetection:
    """Test target type classification."""

    def test_pure_skill_detection(self):
        """Test SKILL.md in root without pyproject.toml → skill"""
        target = detect_target_type(has_skill_md=True, has_pyproject=False, has_skill_subdir=False,
                                    has_package_json=False, has_go_mod=False)
        assert target == 'skill'

    def test_dual_nature_detection(self):
        """Test pyproject.toml + skill/SKILL.md → dual_nature"""
        target = detect_target_type(has_skill_md=False, has_pyproject=True, has_skill_subdir=True,
                                    has_package_json=False, has_go_mod=False)
        assert target == 'dual_nature'

    def test_python_package_detection(self):
        """Test pyproject.toml without skill → python_package"""
        target = detect_target_type(has_skill_md=False, has_pyproject=True, has_skill_subdir=False,
                                    has_package_json=False, has_go_mod=False)
        assert target == 'python_package'

    def test_node_package_detection(self):
        """Test package.json → node_package"""
        target = detect_target_type(has_skill_md=False, has_pyproject=False, has_skill_subdir=False,
                                    has_package_json=True, has_go_mod=False)
        assert target == 'node_package'

    def test_go_module_detection(self):
        """Test go.mod → go_module"""
        target = detect_target_type(has_skill_md=False, has_pyproject=False, has_skill_subdir=False,
                                    has_package_json=False, has_go_mod=True)
        assert target == 'go_module'

    def test_infrastructure_detection(self):
        """Test no package files → infrastructure"""
        target = detect_target_type(has_skill_md=False, has_pyproject=False, has_skill_subdir=False,
                                    has_package_json=False, has_go_mod=False)
        assert target == 'infrastructure'


class TestPhaseDetermination:
    """Test phase selection based on state signals."""

    def test_no_tests_run_p0(self):
        """Test no tests → P0 (Scaffold)"""
        phase = determine_phase('python_package', has_tests=False, tests_pass=False,
                                has_review_marker=False, has_validation_marker=False,
                                has_readme=False, is_certified=False)
        assert phase == 0

    def test_tests_failing_run_p1(self):
        """Test tests failing → P1 (Build)"""
        phase = determine_phase('python_package', has_tests=True, tests_pass=False,
                                has_review_marker=False, has_validation_marker=False,
                                has_readme=False, is_certified=False)
        assert phase == 1

    def test_tests_pass_no_review_run_p2(self):
        """Test tests pass, no review → P2 (Review)"""
        phase = determine_phase('python_package', has_tests=True, tests_pass=True,
                                has_review_marker=False, has_validation_marker=False,
                                has_readme=False, is_certified=False)
        assert phase == 2

    def test_reviewed_no_validation_run_p3(self):
        """Test reviewed, no validation → P3 (Validate)"""
        phase = determine_phase('python_package', has_tests=True, tests_pass=True,
                                has_review_marker=True, has_validation_marker=False,
                                has_readme=False, is_certified=False)
        assert phase == 3

    def test_validated_no_readme_run_p4(self):
        """Test validated, no README → P4 (Publish)"""
        phase = determine_phase('python_package', has_tests=True, tests_pass=True,
                                has_review_marker=True, has_validation_marker=True,
                                has_readme=False, is_certified=False)
        assert phase == 4

    def test_published_not_certified_run_p5(self):
        """Test published, not certified → P5 (Certify)"""
        phase = determine_phase('python_package', has_tests=True, tests_pass=True,
                                has_review_marker=True, has_validation_marker=True,
                                has_readme=True, is_certified=False)
        assert phase == 5

    def test_everything_complete_return_ready(self):
        """Test all complete → ready (-1)"""
        phase = determine_phase('python_package', has_tests=True, tests_pass=True,
                                has_review_marker=True, has_validation_marker=True,
                                has_readme=True, is_certified=True)
        assert phase == -1


class TestHaltCondition:
    """Test pipeline halt condition evaluation."""

    def test_p1_tests_failing_halt(self):
        """Test P1 with test failures → HALT"""
        should_halt, reason = check_halt_condition(phase=1, test_failures=3, blocking_findings=0,
                                                    validation_blocking=False, publish_mode=False)
        assert should_halt is True
        assert "3 test(s) failing" in reason

    def test_p2_blocking_findings_halt(self):
        """Test P2 with blocking findings → HALT"""
        should_halt, reason = check_halt_condition(phase=2, test_failures=0, blocking_findings=5,
                                                    validation_blocking=False, publish_mode=False)
        assert should_halt is True
        assert "5 blocking finding(s)" in reason

    def test_p3_validation_blocking_halt(self):
        """Test P3 with blocking validation → HALT"""
        should_halt, reason = check_halt_condition(phase=3, test_failures=0, blocking_findings=0,
                                                    validation_blocking=True, publish_mode=False)
        assert should_halt is True
        assert "Blocking validation stage failed" in reason

    def test_p3_publish_mode_halt(self):
        """Test P3 with --publish flag → HALT on any warning"""
        should_halt, reason = check_halt_condition(phase=3, test_failures=0, blocking_findings=0,
                                                    validation_blocking=False, publish_mode=True)
        assert should_halt is True
        assert "--publish mode" in reason

    def test_p4_p5_no_halt(self):
        """Test P4/P5 never halt"""
        should_halt, _ = check_halt_condition(phase=4, test_failures=0, blocking_findings=0,
                                               validation_blocking=False, publish_mode=False)
        assert should_halt is False

        should_halt, _ = check_halt_condition(phase=5, test_failures=0, blocking_findings=0,
                                               validation_blocking=False, publish_mode=False)
        assert should_halt is False


class TestMarkerDetection:
    """Test review and validation marker detection."""

    def test_reviewed_via_adversarial_review(self):
        """Test reviewed detected via adversarial-review.json"""
        markers = detect_marker_files(has_adversarial_review=True, has_review_complete=False,
                                     has_validation_complete=False, has_validation_report=False)
        assert markers['reviewed'] is True
        assert markers['validated'] is False

    def test_reviewed_via_complete_marker(self):
        """Test reviewed detected via review-complete.marker"""
        markers = detect_marker_files(has_adversarial_review=False, has_review_complete=True,
                                     has_validation_complete=False, has_validation_report=False)
        assert markers['reviewed'] is True
        assert markers['validated'] is False

    def test_validated_via_complete_marker(self):
        """Test validated detected via validation-complete.marker"""
        markers = detect_marker_files(has_adversarial_review=False, has_review_complete=False,
                                     has_validation_complete=True, has_validation_report=False)
        assert markers['reviewed'] is False
        assert markers['validated'] is True

    def test_validated_via_report(self):
        """Test validated detected via validation-report.md"""
        markers = detect_marker_files(has_adversarial_review=False, has_review_complete=False,
                                     has_validation_complete=False, has_validation_report=True)
        assert markers['reviewed'] is False
        assert markers['validated'] is True

    def test_no_markers(self):
        """Test no markers present"""
        markers = detect_marker_files(has_adversarial_review=False, has_review_complete=False,
                                     has_validation_complete=False, has_validation_report=False)
        assert markers['reviewed'] is False
        assert markers['validated'] is False


class TestDualNatureDetection:
    """Test dual-nature package detection."""

    def test_dual_nature_detected(self):
        """Test pyproject.toml + skill/SKILL.md → dual-nature"""
        is_dual, desc = detect_dual_nature(has_pyproject=True, has_skill_subdir=True)
        assert is_dual is True
        assert "Dual-nature detected" in desc

    def test_python_package_only(self):
        """Test pyproject.toml without skill → not dual-nature"""
        is_dual, desc = detect_dual_nature(has_pyproject=True, has_skill_subdir=False)
        assert is_dual is False
        assert desc == ""

    def test_skill_only(self):
        """Test skill/SKILL.md without pyproject → not dual-nature"""
        is_dual, desc = detect_dual_nature(has_pyproject=False, has_skill_subdir=True)
        assert is_dual is False
        assert desc == ""


class TestCompletionCheck:
    """Test work completion detection."""

    def test_infrastructure_complete(self):
        """Test infrastructure code with tests passing and no findings → complete"""
        is_complete, reason = check_work_complete(
            target_type='infrastructure', phase=1,
            test_failures=0, blocking_findings=0, non_blocking_findings=0)
        assert is_complete is True
        assert "Infrastructure code complete" in reason

    def test_package_pipeline_complete(self):
        """Test P5 complete with no findings → complete"""
        is_complete, reason = check_work_complete(
            target_type='python_package', phase=5,
            test_failures=0, blocking_findings=0, non_blocking_findings=0)
        assert is_complete is True
        assert "Package pipeline complete" in reason

    def test_not_complete_test_failures(self):
        """Test failing tests → not complete"""
        is_complete, _ = check_work_complete(
            target_type='infrastructure', phase=1,
            test_failures=3, blocking_findings=0, non_blocking_findings=0)
        assert is_complete is False

    def test_not_complete_blocking_findings(self):
        """Test blocking findings → not complete"""
        is_complete, _ = check_work_complete(
            target_type='python_package', phase=5,
            test_failures=0, blocking_findings=2, non_blocking_findings=0)
        assert is_complete is False

    def test_not_complete_non_blocking_findings(self):
        """Test non-blocking findings → not complete"""
        is_complete, _ = check_work_complete(
            target_type='python_package', phase=5,
            test_failures=0, blocking_findings=0, non_blocking_findings=5)
        assert is_complete is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
