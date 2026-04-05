"""
Baseline regression tests for /r skill (Remember/refine system).

These tests capture the current behavior of /r before GoT/ToT integration.
They serve as regression guards to ensure core functionality continues working.

Test Coverage:
- Context filtering (solo-dev enterprise pattern removal)
- Escalation decision logic (when to escalate to /s)
- Scope classification (trivial/moderate/significant/major)
- Value completeness gate (disclosure rules for excluded items)
- Finding categorization (must_fix_now vs can_do_soon)

Critical paths tested: 5
Lines of code: ~100
"""

import pytest


def apply_context_filter(findings: list[dict], forbidden_patterns: list[str]) -> tuple[list[dict], int]:
    """
    Apply solo-dev context filter to findings.

    This is a copy of the context filtering logic from /r
    to establish baseline behavior before GoT/ToT integration.

    Args:
        findings: List of finding dicts with 'description' field
        forbidden_patterns: List of patterns to filter out

    Returns:
        Tuple of (filtered_findings, filtered_count)
    """
    filtered = []
    count = 0

    for finding in findings:
        description = str(finding.get('description', '')).lower()
        # Check if finding contains any forbidden pattern
        if any(pattern in description for pattern in forbidden_patterns):
            count += 1
        else:
            filtered.append(finding)

    return (filtered, count)


def should_escalate_to_s(is_architecture_scope: bool, high_risk_signals: int,
                          has_low_confidence: bool, has_conflicting_tradeoffs: bool) -> tuple[bool, str]:
    """
    Determine if escalation to /s is warranted.

    This is a copy of the escalation logic from /r
    to establish baseline behavior before GoT/ToT integration.

    Args:
        is_architecture_scope: Architecture/migration/rewrite scope implied
        high_risk_signals: Number of high-risk signals present
        has_low_confidence: Deterministic pass has low confidence
        has_conflicting_tradeoffs: Conflicting tradeoffs detected

    Returns:
        Tuple of (should_escalate, reason)
    """
    reasons = []

    if is_architecture_scope:
        reasons.append("architecture/migration/rewrite scope implied")

    if high_risk_signals >= 2:
        reasons.append(f"{high_risk_signals} high-risk signals present")

    if has_low_confidence:
        reasons.append("deterministic pass has low confidence")

    if has_conflicting_tradeoffs:
        reasons.append("conflicting tradeoffs detected")

    should_escalate = len(reasons) > 0
    reason = "; ".join(reasons) if reasons else ""

    return (should_escalate, reason)


def classify_change_scope(files_changed: int, lines_changed: int,
                          has_breaking_changes: bool, affects_core: bool) -> str:
    """
    Classify change scope from session evidence.

    This is a copy of the scope classification logic from /r
    to establish baseline behavior before GoT/ToT integration.

    Args:
        files_changed: Number of files changed
        lines_changed: Number of lines changed
        has_breaking_changes: Whether breaking changes are present
        affects_core: Whether core functionality is affected

    Returns:
        Scope classification: trivial, moderate, significant, or major
    """
    # Major: Breaking changes OR core affected OR 10+ files
    if has_breaking_changes or affects_core or files_changed >= 10:
        return 'major'

    # Significant: 5-9 files OR 500+ lines
    if files_changed >= 5 or lines_changed >= 500:
        return 'significant'

    # Moderate: 2-4 files OR 100-499 lines
    if files_changed >= 2 or lines_changed >= 100:
        return 'moderate'

    # Trivial: 1 file, < 100 lines
    return 'trivial'


def validate_value_completeness(excluded_items: list[dict]) -> tuple[bool, list[str]]:
    """
    Validate value completeness gate for excluded items.

    This is a copy of the value completeness logic from /r
    to establish baseline behavior before GoT/ToT integration.

    Disclosure rules:
    - HIGH value: Always disclose
    - MEDIUM value: Disclose when 3+ items
    - LOW value: Optional disclosure

    Args:
        excluded_items: List of excluded items with 'value_level' field

    Returns:
        Tuple of (is_valid, missing_disclosures)
    """
    missing = []

    for item in excluded_items:
        value = item.get('value_level', 'LOW').upper()
        disclosed = item.get('disclosed', False)

        # HIGH value must always be disclosed
        if value == 'HIGH' and not disclosed:
            missing.append(f"HIGH value item not disclosed: {item.get('description', 'unknown')}")

        # MEDIUM value must be disclosed when 3+ items
        if value == 'MEDIUM' and len(excluded_items) >= 3 and not disclosed:
            missing.append(f"MEDIUM value item not disclosed (3+ items): {item.get('description', 'unknown')}")

    is_valid = len(missing) == 0
    return (is_valid, missing)


def categorize_finding(severity: str, has_file_reference: bool, is_fixable: bool) -> str:
    """
    Categorize finding into must_fix_now or can_do_soon.

    This is a copy of the finding categorization logic from /r
    to establish baseline behavior before GoT/ToT integration.

    Args:
        severity: Finding severity (critical/high/medium/low)
        has_file_reference: Whether finding has concrete file reference
        is_fixable: Whether finding is fixable with current context

    Returns:
        Category: must_fix_now or can_do_soon
    """
    # Critical or high severity with file reference = must fix now
    if severity in ('critical', 'high') and has_file_reference and is_fixable:
        return 'must_fix_now'

    # Everything else = can do soon
    return 'can_do_soon'


class TestContextFiltering:
    """Test solo-dev context filtering."""

    def test_filter_team_approval_finding(self):
        """Test filtering team approval finding"""
        findings = [
            {'description': 'Requires team approval gate'}
        ]
        forbidden = ['team approval', 'coordination']
        filtered, count = apply_context_filter(findings, forbidden)
        assert len(filtered) == 0
        assert count == 1

    def test_preserve_valid_finding(self):
        """Test preserving non-enterprise finding"""
        findings = [
            {'description': 'Layering violation detected'}
        ]
        forbidden = ['team approval', 'coordination']
        filtered, count = apply_context_filter(findings, forbidden)
        assert len(filtered) == 1
        assert count == 0

    def test_filter_multiple_patterns(self):
        """Test filtering multiple forbidden patterns"""
        findings = [
            {'description': 'Add real-time dashboard'},
            {'description': 'Valid architectural issue'},
            {'description': 'Requires coordination'}
        ]
        forbidden = ['real-time', 'coordination']
        filtered, count = apply_context_filter(findings, forbidden)
        assert len(filtered) == 1
        assert count == 2


class TestEscalationDecision:
    """Test escalation to /s decision logic."""

    def test_escalate_architecture_scope(self):
        """Test escalation for architecture scope"""
        should_escalate, reason = should_escalate_to_s(
            is_architecture_scope=True,
            high_risk_signals=0,
            has_low_confidence=False,
            has_conflicting_tradeoffs=False
        )
        assert should_escalate is True
        assert "architecture" in reason

    def test_escalate_multiple_high_risk_signals(self):
        """Test escalation for 2+ high-risk signals"""
        should_escalate, reason = should_escalate_to_s(
            is_architecture_scope=False,
            high_risk_signals=2,
            has_low_confidence=False,
            has_conflicting_tradeoffs=False
        )
        assert should_escalate is True
        assert "2 high-risk signals" in reason

    def test_escalate_low_confidence(self):
        """Test escalation for low confidence"""
        should_escalate, reason = should_escalate_to_s(
            is_architecture_scope=False,
            high_risk_signals=0,
            has_low_confidence=True,
            has_conflicting_tradeoffs=False
        )
        assert should_escalate is True
        assert "low confidence" in reason

    def test_escalate_conflicting_tradeoffs(self):
        """Test escalation for conflicting tradeoffs"""
        should_escalate, reason = should_escalate_to_s(
            is_architecture_scope=False,
            high_risk_signals=0,
            has_low_confidence=False,
            has_conflicting_tradeoffs=True
        )
        assert should_escalate is True
        assert "conflicting tradeoffs" in reason

    def test_no_escalation_trivial_case(self):
        """Test no escalation for trivial case"""
        should_escalate, reason = should_escalate_to_s(
            is_architecture_scope=False,
            high_risk_signals=0,
            has_low_confidence=False,
            has_conflicting_tradeoffs=False
        )
        assert should_escalate is False
        assert reason == ""


class TestScopeClassification:
    """Test change scope classification."""

    def test_trivial_scope(self):
        """Test trivial scope: 1 file, < 100 lines"""
        scope = classify_change_scope(
            files_changed=1,
            lines_changed=50,
            has_breaking_changes=False,
            affects_core=False
        )
        assert scope == 'trivial'

    def test_moderate_scope(self):
        """Test moderate scope: 2-4 files OR 100-499 lines"""
        scope = classify_change_scope(
            files_changed=3,
            lines_changed=150,
            has_breaking_changes=False,
            affects_core=False
        )
        assert scope == 'moderate'

    def test_significant_scope(self):
        """Test significant scope: 5-9 files OR 500+ lines"""
        scope = classify_change_scope(
            files_changed=6,
            lines_changed=600,
            has_breaking_changes=False,
            affects_core=False
        )
        assert scope == 'significant'

    def test_major_scope_breaking_changes(self):
        """Test major scope with breaking changes"""
        scope = classify_change_scope(
            files_changed=2,
            lines_changed=50,
            has_breaking_changes=True,
            affects_core=False
        )
        assert scope == 'major'

    def test_major_scope_core_affected(self):
        """Test major scope with core affected"""
        scope = classify_change_scope(
            files_changed=5,
            lines_changed=200,
            has_breaking_changes=False,
            affects_core=True
        )
        assert scope == 'major'

    def test_major_scope_many_files(self):
        """Test major scope with 10+ files"""
        scope = classify_change_scope(
            files_changed=12,
            lines_changed=300,
            has_breaking_changes=False,
            affects_core=False
        )
        assert scope == 'major'


class TestValueCompleteness:
    """Test value completeness gate validation."""

    def test_valid_high_disclosed(self):
        """Test valid when HIGH value is disclosed"""
        items = [
            {'value_level': 'HIGH', 'disclosed': True, 'description': 'Complex feature'}
        ]
        is_valid, missing = validate_value_completeness(items)
        assert is_valid is True
        assert len(missing) == 0

    def test_invalid_high_not_disclosed(self):
        """Test invalid when HIGH value is not disclosed"""
        items = [
            {'value_level': 'HIGH', 'disclosed': False, 'description': 'Complex feature'}
        ]
        is_valid, missing = validate_value_completeness(items)
        assert is_valid is False
        assert len(missing) == 1
        assert "HIGH value item not disclosed" in missing[0]

    def test_invalid_medium_not_disclosed_three_items(self):
        """Test invalid when MEDIUM not disclosed with 3+ items"""
        items = [
            {'value_level': 'MEDIUM', 'disclosed': False, 'description': 'Item 1'},
            {'value_level': 'MEDIUM', 'disclosed': False, 'description': 'Item 2'},
            {'value_level': 'MEDIUM', 'disclosed': False, 'description': 'Item 3'}
        ]
        is_valid, missing = validate_value_completeness(items)
        assert is_valid is False
        assert len(missing) == 3
        assert all("MEDIUM value item not disclosed" in m for m in missing)

    def test_valid_medium_not_disclosed_two_items(self):
        """Test valid when MEDIUM not disclosed with < 3 items"""
        items = [
            {'value_level': 'MEDIUM', 'disclosed': False, 'description': 'Item 1'},
            {'value_level': 'MEDIUM', 'disclosed': False, 'description': 'Item 2'}
        ]
        is_valid, missing = validate_value_completeness(items)
        assert is_valid is True
        assert len(missing) == 0

    def test_valid_low_optional(self):
        """Test valid when LOW value is not disclosed (optional)"""
        items = [
            {'value_level': 'LOW', 'disclosed': False, 'description': 'Minor item'}
        ]
        is_valid, missing = validate_value_completeness(items)
        assert is_valid is True
        assert len(missing) == 0


class TestFindingCategorization:
    """Test finding categorization logic."""

    def test_critical_with_reference_must_fix_now(self):
        """Test critical with file reference → must fix now"""
        category = categorize_finding(
            severity='critical',
            has_file_reference=True,
            is_fixable=True
        )
        assert category == 'must_fix_now'

    def test_high_with_reference_must_fix_now(self):
        """Test high with file reference → must fix now"""
        category = categorize_finding(
            severity='high',
            has_file_reference=True,
            is_fixable=True
        )
        assert category == 'must_fix_now'

    def test_critical_no_reference_can_do_soon(self):
        """Test critical without file reference → can do soon"""
        category = categorize_finding(
            severity='critical',
            has_file_reference=False,
            is_fixable=True
        )
        assert category == 'can_do_soon'

    def test_critical_not_fixable_can_do_soon(self):
        """Test critical not fixable → can do soon"""
        category = categorize_finding(
            severity='critical',
            has_file_reference=True,
            is_fixable=False
        )
        assert category == 'can_do_soon'

    def test_medium_can_do_soon(self):
        """Test medium severity → can do soon"""
        category = categorize_finding(
            severity='medium',
            has_file_reference=True,
            is_fixable=True
        )
        assert category == 'can_do_soon'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
