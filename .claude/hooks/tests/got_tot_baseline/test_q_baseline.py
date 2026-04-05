"""
Baseline regression tests for /q skill (Strategic quality check).

These tests capture the current behavior of /q before GoT/ToT integration.
They serve as regression guards to ensure core functionality continues working.

Test Coverage:
- Strategic health assessment (Sound/Concerning/Critical based on findings)
- Scope resolution priority (session → conversation → git)
- Finding normalization (stable schema conversion)
- Solo-dev filtering (enterprise pattern removal)
- Phase completion validation (required output markers)
- Risk categorization (concerning/critical severity)

Critical paths tested: 6
Lines of code: ~100
"""

import pytest


def assess_strategic_health(concerning_count: int, critical_count: int) -> str:
    """
    Assess overall strategic health from findings.

    This is a copy of the strategic health logic from /q
    to establish baseline behavior before GoT/ToT integration.

    Args:
        concerning_count: Number of concerning findings
        critical_count: Number of critical findings

    Returns:
        Health level: sound, concerning, or critical
    """
    # Sound: 0-1 concerning findings, 0 critical
    if concerning_count <= 1 and critical_count == 0:
        return 'sound'

    # Concerning: 2-5 concerning findings OR 1 critical
    if (2 <= concerning_count <= 5) or critical_count == 1:
        return 'concerning'

    # Critical: 6+ concerning findings OR 2+ critical
    if concerning_count >= 6 or critical_count >= 2:
        return 'critical'

    # Default to concerning for edge cases
    return 'concerning'


def resolve_scope_priority(has_session_scope: bool, has_conversation_history: bool,
                          has_git_status: bool) -> str:
    """
    Determine scope source using priority order.

    This is a copy of the scope resolution logic from /q
    to establish baseline behavior before GoT/ToT integration.

    Priority: Session activity → Conversation history → Git status

    Args:
        has_session_scope: Session activity tracker available
        has_conversation_history: Conversation history available
        has_git_status: Git status available

    Returns:
        Scope source: session, conversation, or git
    """
    # Primary: Session activity tracker
    if has_session_scope:
        return 'session'

    # Secondary: Conversation history analysis
    if has_conversation_history:
        return 'conversation'

    # Tertiary: Git status (verification only, cross-reference with session)
    if has_git_status:
        return 'git'

    # Fallback: no scope available
    return 'none'


def normalize_finding(finding_id: str, severity: str, category: str,
                      message: str, file_path: str, line_number: int) -> dict:
    """
    Normalize finding into stable schema.

    This is a copy of the finding normalization logic from /q
    to establish baseline behavior before GoT/ToT integration.

    Args:
        finding_id: Unique identifier (e.g., "Q-ARCH-001")
        severity: Finding severity (concerning/critical/sound)
        category: Finding category (arch/pattern/technology/balance/library)
        message: Finding description
        file_path: Affected file path
        line_number: Line number of issue

    Returns:
        Normalized finding dict with stable schema
    """
    return {
        'id': finding_id,
        'severity': severity,
        'category': category,
        'message': message,
        'file_path': file_path,
        'line_number': line_number
    }


def filter_solo_dev_findings(findings: list[dict]) -> tuple[list[dict], int]:
    """
    Filter out enterprise-style findings for solo-dev context.

    This is a copy of the solo-dev filtering logic from /q
    to establish baseline behavior before GoT/ToT integration.

    Enterprise patterns to filter:
    - Team approval gates
    - Real-time dashboards
    - Self-healing systems
    - Autonomous execution

    Args:
        findings: List of normalized findings

    Returns:
        Tuple of (filtered_findings, filtered_count)
    """
    enterprise_patterns = [
        'team approval',
        'real-time',
        'self-healing',
        'autonomous',
        'multi-person',
        'coordination'
    ]

    filtered = []
    filtered_count = 0

    for finding in findings:
        message_lower = finding['message'].lower()
        is_enterprise = any(pattern in message_lower for pattern in enterprise_patterns)

        if is_enterprise:
            filtered_count += 1
        else:
            filtered.append(finding)

    return (filtered, filtered_count)


def validate_phase_completion(phase_markers: dict[str, bool],
                             has_summary: bool,
                             has_next_steps: bool,
                             has_complete_status: bool) -> tuple[bool, list[str]]:
    """
    Validate required output format markers.

    This is a copy of the phase completion validation logic from /q
    to establish baseline behavior before GoT/ToT integration.

    Required markers:
    1. Phase results: ✅ Q1: ... or ⚠️ Q2: ...
    2. **Summary:** section with strategic health
    3. ## Next Steps section with concrete actions
    4. Final line: Q Pipeline Status: COMPLETE

    Args:
        phase_markers: Dict of phase names to completion status
        has_summary: Whether **Summary:** section exists
        has_next_steps: Whether ## Next Steps section exists
        has_complete_status: Whether final status line exists

    Returns:
        Tuple of (is_valid, missing_markers)
    """
    missing = []

    # Check phase markers (Q1-Q6)
    for phase_num in range(1, 7):
        phase_key = f'q{phase_num}'
        if not phase_markers.get(phase_key, False):
            missing.append(f'Q{phase_num} phase marker')

    # Check required sections
    if not has_summary:
        missing.append('**Summary:** section')

    if not has_next_steps:
        missing.append('## Next Steps section')

    if not has_complete_status:
        missing.append('Q Pipeline Status: COMPLETE')

    is_valid = len(missing) == 0
    return (is_valid, missing)


def categorize_risk(severity: str, impact: str) -> str:
    """
    Categorize risk level from severity and impact.

    This is a copy of the risk categorization logic from /q
    to establish baseline behavior before GoT/ToT integration.

    Args:
        severity: Finding severity (concerning/critical)
        impact: Impact level (high/medium/low)

    Returns:
        Risk category: strategic, operational, or informational
    """
    if severity == 'critical' and impact == 'high':
        return 'strategic'

    if severity == 'concerning' and impact in ('high', 'medium'):
        return 'operational'

    return 'informational'


class TestStrategicHealthAssessment:
    """Test strategic health classification."""

    def test_sound_health_zero_findings(self):
        """Test sound health with no findings"""
        health = assess_strategic_health(concerning_count=0, critical_count=0)
        assert health == 'sound'

    def test_sound_health_one_concerning(self):
        """Test sound health with 1 concerning finding"""
        health = assess_strategic_health(concerning_count=1, critical_count=0)
        assert health == 'sound'

    def test_concerning_health_two_concerning(self):
        """Test concerning health with 2-5 concerning findings"""
        health = assess_strategic_health(concerning_count=2, critical_count=0)
        assert health == 'concerning'

        health = assess_strategic_health(concerning_count=5, critical_count=0)
        assert health == 'concerning'

    def test_concerning_health_one_critical(self):
        """Test concerning health with 1 critical finding"""
        health = assess_strategic_health(concerning_count=0, critical_count=1)
        assert health == 'concerning'

    def test_critical_health_six_concerning(self):
        """Test critical health with 6+ concerning findings"""
        health = assess_strategic_health(concerning_count=6, critical_count=0)
        assert health == 'critical'

    def test_critical_health_two_critical(self):
        """Test critical health with 2+ critical findings"""
        health = assess_strategic_health(concerning_count=0, critical_count=2)
        assert health == 'critical'


class TestScopeResolution:
    """Test scope source priority."""

    def test_session_scope_highest_priority(self):
        """Test session scope takes priority over others"""
        scope = resolve_scope_priority(
            has_session_scope=True,
            has_conversation_history=True,
            has_git_status=True
        )
        assert scope == 'session'

    def test_conversation_scope_secondary(self):
        """Test conversation scope used when session unavailable"""
        scope = resolve_scope_priority(
            has_session_scope=False,
            has_conversation_history=True,
            has_git_status=True
        )
        assert scope == 'conversation'

    def test_git_scope_tertiary(self):
        """Test git scope used when session and conversation unavailable"""
        scope = resolve_scope_priority(
            has_session_scope=False,
            has_conversation_history=False,
            has_git_status=True
        )
        assert scope == 'git'

    def test_no_scope_available(self):
        """Test no scope when all sources unavailable"""
        scope = resolve_scope_priority(
            has_session_scope=False,
            has_conversation_history=False,
            has_git_status=False
        )
        assert scope == 'none'


class TestFindingNormalization:
    """Test finding schema normalization."""

    def test_normalize_arch_finding(self):
        """Test normalizing architectural finding"""
        finding = normalize_finding(
            finding_id='Q-ARCH-001',
            severity='critical',
            category='arch',
            message='Layering violation detected',
            file_path='src/auth.py',
            line_number=42
        )
        assert finding['id'] == 'Q-ARCH-001'
        assert finding['severity'] == 'critical'
        assert finding['category'] == 'arch'
        assert finding['message'] == 'Layering violation detected'
        assert finding['file_path'] == 'src/auth.py'
        assert finding['line_number'] == 42

    def test_normalize_pattern_finding(self):
        """Test normalizing design pattern finding"""
        finding = normalize_finding(
            finding_id='Q-PATTERN-003',
            severity='concerning',
            category='pattern',
            message='Singleton abuse detected',
            file_path='src/database.py',
            line_number=15
        )
        assert finding['category'] == 'pattern'


class TestSoloDevFiltering:
    """Test enterprise pattern filtering."""

    def test_filter_team_approval_finding(self):
        """Test filtering team approval finding"""
        findings = [
            {'id': 'Q-001', 'message': 'Requires team approval gate', 'severity': 'critical'}
        ]
        filtered, count = filter_solo_dev_findings(findings)
        assert len(filtered) == 0
        assert count == 1

    def test_filter_real_time_dashboard_finding(self):
        """Test filtering real-time dashboard finding"""
        findings = [
            {'id': 'Q-002', 'message': 'Add real-time metrics dashboard', 'severity': 'concerning'}
        ]
        filtered, count = filter_solo_dev_findings(findings)
        assert len(filtered) == 0
        assert count == 1

    def test_preserve_valid_finding(self):
        """Test preserving non-enterprise finding"""
        findings = [
            {'id': 'Q-003', 'message': 'Layering violation detected', 'severity': 'critical'}
        ]
        filtered, count = filter_solo_dev_findings(findings)
        assert len(filtered) == 1
        assert count == 0

    def test_filter_multiple_patterns(self):
        """Test filtering multiple enterprise patterns"""
        findings = [
            {'id': 'Q-001', 'message': 'Requires team coordination', 'severity': 'critical'},
            {'id': 'Q-002', 'message': 'Valid architectural issue', 'severity': 'concerning'},
            {'id': 'Q-003', 'message': 'Self-healing system needed', 'severity': 'critical'}
        ]
        filtered, count = filter_solo_dev_findings(findings)
        assert len(filtered) == 1
        assert count == 2


class TestPhaseCompletionValidation:
    """Test phase completion marker validation."""

    def test_all_phases_complete(self):
        """Test validation passes with all markers"""
        phase_markers = {f'q{i}': True for i in range(1, 7)}
        is_valid, missing = validate_phase_completion(
            phase_markers=phase_markers,
            has_summary=True,
            has_next_steps=True,
            has_complete_status=True
        )
        assert is_valid is True
        assert len(missing) == 0

    def test_missing_phase_marker(self):
        """Test validation fails with missing Q3 marker"""
        phase_markers = {f'q{i}': True for i in range(1, 7) if i != 3}
        is_valid, missing = validate_phase_completion(
            phase_markers=phase_markers,
            has_summary=True,
            has_next_steps=True,
            has_complete_status=True
        )
        assert is_valid is False
        assert 'Q3 phase marker' in missing

    def test_missing_summary_section(self):
        """Test validation fails without summary"""
        phase_markers = {f'q{i}': True for i in range(1, 7)}
        is_valid, missing = validate_phase_completion(
            phase_markers=phase_markers,
            has_summary=False,
            has_next_steps=True,
            has_complete_status=True
        )
        assert is_valid is False
        assert '**Summary:** section' in missing

    def test_missing_next_steps_section(self):
        """Test validation fails without next steps"""
        phase_markers = {f'q{i}': True for i in range(1, 7)}
        is_valid, missing = validate_phase_completion(
            phase_markers=phase_markers,
            has_summary=True,
            has_next_steps=False,
            has_complete_status=True
        )
        assert is_valid is False
        assert '## Next Steps section' in missing

    def test_missing_complete_status(self):
        """Test validation fails without final status"""
        phase_markers = {f'q{i}': True for i in range(1, 7)}
        is_valid, missing = validate_phase_completion(
            phase_markers=phase_markers,
            has_summary=True,
            has_next_steps=True,
            has_complete_status=False
        )
        assert is_valid is False
        assert 'Q Pipeline Status: COMPLETE' in missing


class TestRiskCategorization:
    """Test risk categorization logic."""

    def test_critical_high_impact_is_strategic(self):
        """Test critical + high impact = strategic risk"""
        risk = categorize_risk(severity='critical', impact='high')
        assert risk == 'strategic'

    def test_concerning_high_impact_is_operational(self):
        """Test concerning + high impact = operational risk"""
        risk = categorize_risk(severity='concerning', impact='high')
        assert risk == 'operational'

    def test_concerning_medium_impact_is_operational(self):
        """Test concerning + medium impact = operational risk"""
        risk = categorize_risk(severity='concerning', impact='medium')
        assert risk == 'operational'

    def test_concerning_low_impact_is_informational(self):
        """Test concerning + low impact = informational risk"""
        risk = categorize_risk(severity='concerning', impact='low')
        assert risk == 'informational'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
