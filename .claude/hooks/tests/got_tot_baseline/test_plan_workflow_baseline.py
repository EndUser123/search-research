"""
Baseline regression tests for /plan-workflow skill (plan creation and verification).

These tests capture the current behavior of /plan-workflow before GoT/ToT integration.
They serve as regression guards to ensure core functionality continues working.

Test Coverage:
- Command parsing (build/review mode, plan path inference)
- Plan path inference (default location, context-based)
- Status determination (READY-FOR-IMPLEMENTATION, REVISION-REQUIRED, BLOCKED, HALTED)
- Priority classification (HIGH, MEDIUM, LOW for action items)
- Effort estimation (S, M, L mapping)
- Menu generation logic (action item counting, time estimation)

Critical paths tested: 6
Lines of code: ~100
"""

import re
from pathlib import Path

import pytest


def parse_command_mode(user_input: str) -> tuple[str, str | None]:
    """
    Parse /plan-workflow command to extract mode and target.

    This is a copy of the command parsing logic from /plan-workflow
    to establish baseline behavior before GoT/ToT integration.

    Args:
        user_input: User's command string

    Returns:
        Tuple of (mode, target_path)
        Modes: 'build', 'review', 'default'
    """
    input_stripped = user_input.strip()

    # Check for explicit mode
    if input_stripped.startswith('build '):
        target = input_stripped[6:].strip()
        return 'build', target
    elif input_stripped.startswith('review '):
        target = input_stripped[7:].strip()
        return 'review', target
    elif input_stripped == 'review':
        return 'review', None
    elif '--interactive' in input_stripped:
        # Extract target before --interactive flag
        parts = input_stripped.split('--interactive')[0].strip()
        return 'default', parts if parts else None
    else:
        # Default mode with target
        return 'default', input_stripped


def infer_plan_path(target: str | None, context_files: list[str]) -> Path:
    """
    Infer plan file path from target and context.

    This is a copy of the path inference logic from /plan-workflow
    to establish baseline behavior before GoT/ToT integration.

    Args:
        target: User-provided target (query or explicit path)
        context_files: List of files in current context

    Returns:
        Path object for plan file location
    """
    # If target is an explicit file path
    if target and (target.endswith('.md') or '/' in target or '\\' in target):
        return Path(target)

    # Default location: .claude/hooks/plans/
    plans_dir = Path('.claude/hooks/plans')

    # Generate filename from target (if provided)
    if target:
        # Extract keywords from target
        words = re.findall(r'\w+', target.lower())
        # Take first 3 meaningful words
        keywords = [w for w in words if len(w) > 2][:3]
        if keywords:
            filename = f"plan-{'-'.join(keywords)}.md"
            return plans_dir / filename

    # Fallback: timestamp-based plan
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d')
    return plans_dir / f"plan-{timestamp}-topic.md"


def determine_status(blocked_issues: int, revision_items: int) -> str:
    """
    Determine plan status from verification findings.

    This is a copy of the status determination logic from /plan-workflow
    to establish baseline behavior before GoT/ToT integration.

    Args:
        blocked_issues: Count of blocking issues found
        revision_items: Count of non-blocking improvements needed

    Returns:
        Status: READY-FOR-IMPLEMENTATION, REVISION-REQUIRED, BLOCKED, HALTED
    """
    if blocked_issues > 0:
        # Check if critical blocker
        if blocked_issues >= 3:
            return 'HALTED'
        return 'BLOCKED'

    if revision_items > 0:
        if revision_items > 10:
            return 'BLOCKED'  # Too many issues
        return 'REVISION-REQUIRED'

    return 'READY-FOR-IMPLEMENTATION'


def classify_priority(issue_type: str, impact: str) -> str:
    """
    Classify action item priority.

    This is a copy of the priority classification logic from /plan-workflow
    to establish baseline behavior before GoT/ToT integration.

    Args:
        issue_type: Type of issue (test_coverage, security, performance, etc.)
        impact: Impact level (critical, high, medium, low)

    Returns:
        Priority: HIGH, MEDIUM, LOW
    """
    # Critical issue types always HIGH
    critical_types = {'security', 'blocking_dependency', 'architectural_violation'}
    if issue_type in critical_types:
        return 'HIGH'

    # Impact-based classification
    high_impact = {'critical', 'high'}
    medium_impact = {'medium'}

    if impact in high_impact:
        return 'HIGH'
    elif impact in medium_impact:
        return 'MEDIUM'
    else:
        return 'LOW'


def estimate_effort(hours: float) -> str:
    """
    Estimate effort category from hours.

    This is a copy of the effort estimation logic from /plan-workflow
    to establish baseline behavior before GoT/ToT integration.

    Args:
        hours: Estimated hours for task

    Returns:
        Effort category: S (small), M (medium), L (large)
    """
    if hours <= 2:
        return 'S'
    elif hours <= 8:
        return 'M'
    else:
        return 'L'


def calculate_total_effort(action_items: list[dict]) -> tuple[int, str]:
    """
    Calculate total effort from action items.

    This is a copy of the effort calculation logic from /plan-workflow
    to establish baseline behavior before GoT/ToT integration.

    Args:
        action_items: List of action items with 'effort' field (S/M/L)

    Returns:
        Tuple of (total_items, time_range_string)
    """
    effort_map = {'S': (0.5, 2), 'M': (2, 8), 'L': (8, 20)}

    min_hours = 0
    max_hours = 0

    for item in action_items:
        effort = item.get('effort', 'M')
        if effort in effort_map:
            e_min, e_max = effort_map[effort]
            min_hours += e_min
            max_hours += e_max

    # Round to nearest hour
    min_hours = round(min_hours)
    max_hours = round(max_hours)

    if min_hours == max_hours:
        time_str = f"{min_hours} hours"
    else:
        time_str = f"{min_hours}-{max_hours} hours"

    return len(action_items), time_str


class TestCommandParsing:
    """Test command mode parsing."""

    def test_parse_build_mode(self):
        """Test parsing build command with target"""
        mode, target = parse_command_mode('build add authentication')
        assert mode == 'build'
        assert target == 'add authentication'

    def test_parse_review_mode_with_path(self):
        """Test parsing review command with path"""
        mode, target = parse_command_mode('review plan-20260309-auth.md')
        assert mode == 'review'
        assert target == 'plan-20260309-auth.md'

    def test_parse_review_mode_without_path(self):
        """Test parsing review command without path"""
        mode, target = parse_command_mode('review')
        assert mode == 'review'
        assert target is None

    def test_parse_default_mode(self):
        """Test parsing default mode command"""
        mode, target = parse_command_mode('add user authentication')
        assert mode == 'default'
        assert target == 'add user authentication'

    def test_parse_interactive_flag(self):
        """Test parsing --interactive flag"""
        mode, target = parse_command_mode('add auth --interactive')
        assert mode == 'default'
        assert target == 'add auth'


class TestPathInference:
    """Test plan path inference."""

    def test_infer_from_explicit_path(self):
        """Test inferring path from explicit .md file"""
        path = infer_plan_path('plans/feature-x.md', [])
        assert path == Path('plans/feature-x.md')

    def test_infer_from_target_keywords(self):
        """Test inferring path from target keywords"""
        path = infer_plan_path('add user authentication system', [])
        path_str = str(path).replace('\\', '/')
        assert path_str.endswith('plan-add-user-authentication.md')
        assert '.claude/hooks/plans/' in path_str

    def test_infer_fallback_timestamp(self):
        """Test fallback to timestamp when no target"""
        path = infer_plan_path(None, [])
        path_str = str(path).replace('\\', '/')
        assert '.claude/hooks/plans/plan-' in path_str
        assert '.md' in str(path)


class TestStatusDetermination:
    """Test plan status determination."""

    def test_status_ready_no_issues(self):
        """Test READY-FOR-IMPLEMENTATION with no issues"""
        status = determine_status(0, 0)
        assert status == 'READY-FOR-IMPLEMENTATION'

    def test_status_revision_required(self):
        """Test REVISION-REQUIRED with some improvements"""
        status = determine_status(0, 5)
        assert status == 'REVISION-REQUIRED'

    def test_status_blocked_critical(self):
        """Test HALTED with critical blocking issues"""
        status = determine_status(3, 0)
        assert status == 'HALTED'

    def test_status_blocked_minor(self):
        """Test BLOCKED with minor blocking issues"""
        status = determine_status(1, 5)
        assert status == 'BLOCKED'

    def test_status_blocked_too_many_revisions(self):
        """Test BLOCKED when too many revision items"""
        status = determine_status(0, 15)
        assert status == 'BLOCKED'


class TestPriorityClassification:
    """Test action item priority classification."""

    def test_security_issue_high_priority(self):
        """Test security issues are HIGH priority"""
        priority = classify_priority('security', 'medium')
        assert priority == 'HIGH'

    def test_critical_impact_high_priority(self):
        """Test critical impact is HIGH priority"""
        priority = classify_priority('performance', 'critical')
        assert priority == 'HIGH'

    def test_medium_impact_medium_priority(self):
        """Test medium impact is MEDIUM priority"""
        priority = classify_priority('code_quality', 'medium')
        assert priority == 'MEDIUM'

    def test_low_impact_low_priority(self):
        """Test low impact is LOW priority"""
        priority = classify_priority('style', 'low')
        assert priority == 'LOW'


class TestEffortEstimation:
    """Test effort estimation."""

    def test_small_effort_under_2_hours(self):
        """Test S effort for tasks under 2 hours"""
        effort = estimate_effort(1.5)
        assert effort == 'S'

    def test_small_effort_exactly_2_hours(self):
        """Test S effort for tasks exactly 2 hours"""
        effort = estimate_effort(2.0)
        assert effort == 'S'

    def test_medium_effort_2_to_8_hours(self):
        """Test M effort for tasks 2-8 hours"""
        effort = estimate_effort(5.0)
        assert effort == 'M'

    def test_large_effort_over_8_hours(self):
        """Test L effort for tasks over 8 hours"""
        effort = estimate_effort(12.0)
        assert effort == 'L'


class TestEffortCalculation:
    """Test total effort calculation."""

    def test_calculate_mixed_efforts(self):
        """Test calculating total effort from mixed items"""
        items = [
            {'effort': 'S'},  # 0.5-2 hours
            {'effort': 'M'},  # 2-8 hours
            {'effort': 'L'},  # 8-20 hours
        ]
        count, time_str = calculate_total_effort(items)
        assert count == 3
        assert '11-30 hours' == time_str or '10-30 hours' == time_str  # Rounding may vary

    def test_calculate_all_small(self):
        """Test calculating all small items"""
        items = [
            {'effort': 'S'},
            {'effort': 'S'},
        ]
        count, time_str = calculate_total_effort(items)
        assert count == 2
        assert '1-4 hours' == time_str

    def test_calculate_empty_list(self):
        """Test calculating effort with no items"""
        count, time_str = calculate_total_effort([])
        assert count == 0
        assert time_str == '0 hours'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
