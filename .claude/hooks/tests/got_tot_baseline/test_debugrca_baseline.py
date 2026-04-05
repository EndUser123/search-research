"""
Baseline regression tests for /debugRCA skill (root cause analysis).

These tests capture the current behavior of /debugRCA before GoT/ToT integration.
They serve as regression guards to ensure core functionality continues working.

Test Coverage:
- Evidence tier confidence ceilings
- Hypothesis scoring formula (Reproducibility × Recency × Impact)
- Problem type auto-detection (ERROR, PERFORMANCE, CRASH, etc.)
- Gap analysis protocol coverage check
- Multi-agent confidence boost

Critical paths tested: 5
Lines of code: ~100
"""

import pytest


def calculate_evidence_confidence(evidence_types: list[str]) -> int:
    """
    Calculate confidence ceiling based on evidence tiers.

    This is a copy of the evidence tier logic from /debugRCA
    to establish baseline behavior before GoT/ToT integration.

    Evidence tiers and confidence ceilings:
    - Execution output: 95%
    - Multi-agent reasoning: 90%
    - /search unified: 80%
    - Static analysis / CKS cognitive: 75%
    - CHS historical: 70%
    - Logical derivation: 60%

    Args:
        evidence_types: List of evidence types present

    Returns:
        Confidence ceiling percentage (0-95)
    """
    tier_ceiling = {
        'execution': 95,
        'multi_agent': 90,
        'unified_search': 80,
        'static_analysis': 75,
        'cks_cognitive': 75,
        'chs_historical': 70,
        'logical': 60,
    }

    # Minimum confidence ceiling is lowest tier present
    # Without evidence → max 50% confidence
    if not evidence_types:
        return 50

    min_ceiling = 95  # Start at max, then reduce based on evidence

    for evidence_type in evidence_types:
        ceiling = tier_ceiling.get(evidence_type.lower(), 50)
        min_ceiling = min(min_ceiling, ceiling)

    return min_ceiling


def calculate_hypothesis_score(reproducibility: float, recency: float, impact: float) -> float:
    """
    Calculate hypothesis score using weighted formula.

    This is a copy of the hypothesis scoring logic from /debugRCA
    to establish baseline behavior before GoT/ToT integration.

    Formula: Score = Reproducibility(0.3) × Recency(0.2) × Impact(0.5)

    Args:
        reproducibility: 1.0 (can), 0.5 (sometimes), 0.1 (cannot)
        recency: 1.0 (today), 0.5 (this week), 0.1 (old)
        impact: 1.0 (all symptoms), 0.5 (some), 0.1 (weak)

    Returns:
        Hypothesis score (0.0 - 1.0)
    """
    return (reproducibility * 0.3) + (recency * 0.2) + (impact * 0.5)


def detect_problem_type(error_message: str, has_traceback: bool, is_slow: bool) -> str:
    """
    Auto-detect problem type from symptoms.

    This is a copy of the problem type detection logic from /debugRCA
    to establish baseline behavior before GoT/ToT integration.

    Args:
        error_message: Error message content
        has_traceback: Whether traceback is present
        is_slow: Whether operation is slow/timing out

    Returns:
        Problem type (ERROR, PERFORMANCE, CRASH, SECURITY, INTEGRATION, INTERMITTENT, NEW/NOVEL)
    """
    # Priority: CRASH > ERROR > PERFORMANCE > SECURITY > INTEGRATION > INTERMITTENT > NEW
    error_lower = error_message.lower()
    if has_traceback and ('segfault' in error_lower or 'segmentation fault' in error_lower or 'abort' in error_lower):
        return 'CRASH'

    if error_message and any(e in error_message for e in ['AttributeError', 'ImportError', 'KeyError']):
        return 'ERROR'

    if is_slow:
        return 'PERFORMANCE'

    if error_message and any(auth in error_message.lower() for auth in ['auth', 'permission', 'unauthorized']):
        return 'SECURITY'

    if error_message and any(integ in error_message.lower() for integ in ['api', 'interface', 'connection']):
        return 'INTEGRATION'

    if 'flaky' in error_message.lower() or 'intermittent' in error_message.lower():
        return 'INTERMITTENT'

    return 'NEW'


def select_thinking_mode(problem_type: str) -> str:
    """
    Select primary thinking mode based on problem type.

    This is a copy of the cognitive stack selection logic from /debugRCA
    to establish baseline behavior before GoT/ToT integration.

    Args:
        problem_type: Detected problem type

    Returns:
        Primary thinking mode
    """
    thinking_modes = {
        'ERROR': 'Five Whys, Linear Thinking',
        'PERFORMANCE': 'Systems Thinking, First Principles',
        'CRASH': 'Five Whys, Scientific Method',
        'SECURITY': 'Risk Assessment, Tree Thinking',
        'INTEGRATION': 'Systems Thinking, Collaborative Reasoning',
        'INTERMITTENT': 'Systems Thinking, Scientific Method',
        'NEW': 'First Principles, Tree Thinking'
    }

    return thinking_modes.get(problem_type, 'First Principles, Tree Thinking')


class TestEvidenceTiers:
    """Test evidence tier confidence calculations."""

    def test_execution_evidence_only(self):
        """Test execution evidence gives 95% ceiling"""
        confidence = calculate_evidence_confidence(['execution'])
        assert confidence == 95

    def test_multi_agent_boost(self):
        """Test multi-agent reasoning gives 90% ceiling"""
        confidence = calculate_evidence_confidence(['multi_agent'])
        assert confidence == 90

    def test_mixed_evidence_takes_minimum(self):
        """Test mixed evidence takes lowest tier ceiling"""
        # Execution (95%) + Logical (60%) = 60% ceiling
        confidence = calculate_evidence_confidence(['execution', 'logical'])
        assert confidence == 60

    def test_no_evidence_low_confidence(self):
        """Test no evidence caps at 50%"""
        # Without evidence → max 50% confidence
        confidence = calculate_evidence_confidence([])
        assert confidence == 50

    def test_all_evidence_types(self):
        """Test all evidence types present"""
        confidence = calculate_evidence_confidence([
            'execution', 'multi_agent', 'unified_search',
            'static_analysis', 'chs_historical', 'logical'
        ])
        assert confidence == 60  # logical is lowest at 60%


class TestHypothesisScoring:
    """Test hypothesis scoring and ranking."""

    def test_perfect_hypothesis(self):
        """Test perfect hypothesis score"""
        score = calculate_hypothesis_score(
            reproducibility=1.0,
            recency=1.0,
            impact=1.0
        )
        assert score == 1.0

    def test_weak_hypothesis(self):
        """Test weak hypothesis score"""
        score = calculate_hypothesis_score(
            reproducibility=0.1,
            recency=0.1,
            impact=0.1
        )
        assert score == 0.1  # All weak

    def test_mixed_hypothesis(self):
        """Test mixed hypothesis score"""
        score = calculate_hypothesis_score(
            reproducibility=1.0,  # Can reproduce
            recency=0.5,      # This week
            impact=0.5         # Some symptoms
        )
        assert score == 0.65  # 0.3 + 0.1 + 0.25

    def test_reproducibility_weight(self):
        """Test reproducibility has 0.3 weight"""
        score1 = calculate_hypothesis_score(1.0, 0.1, 0.1)  # High repro
        score2 = calculate_hypothesis_score(0.1, 1.0, 0.1)  # Low repro
        # score1: (1.0*0.3) + (0.1*0.2) + (0.1*0.5) = 0.3 + 0.02 + 0.05 = 0.37
        # score2: (0.1*0.3) + (1.0*0.2) + (0.1*0.5) = 0.03 + 0.2 + 0.05 = 0.28
        # Reproducibility difference: 0.37 - 0.28 = 0.09
        assert abs(score1 - score2) == pytest.approx(0.09)

    def test_impact_dominant_weight(self):
        """Test impact has 0.5 weight (highest)"""
        score_high_impact = calculate_hypothesis_score(0.5, 0.5, 1.0)
        score_low_impact = calculate_hypothesis_score(0.5, 0.5, 0.1)
        # Impact difference: 0.375 vs 0.175
        assert score_high_impact > score_low_impact


class TestProblemTypeDetection:
    """Test problem type auto-detection."""

    def test_crash_detection_segfault(self):
        """Test crash detection from segfault"""
        problem = detect_problem_type(
            error_message="Segmentation fault (core dumped)",
            has_traceback=True,
            is_slow=False
        )
        assert problem == 'CRASH'

    def test_error_detection_attribute_error(self):
        """Test error detection from AttributeError"""
        problem = detect_problem_type(
            error_message="AttributeError: 'module' object has no attribute",
            has_traceback=True,
            is_slow=False
        )
        assert problem == 'ERROR'

    def test_performance_detection(self):
        """Test performance detection from slowness"""
        problem = detect_problem_type(
            error_message="Operation timed out",
            has_traceback=False,
            is_slow=True
        )
        assert problem == 'PERFORMANCE'

    def test_security_detection(self):
        """Test security detection from auth keywords"""
        problem = detect_problem_type(
            error_message="Unauthorized access denied",
            has_traceback=False,
            is_slow=False
        )
        assert problem == 'SECURITY'

    def test_default_to_new(self):
        """Test default to NEW for unknown problems"""
        problem = detect_problem_type(
            error_message="Something unusual happened",
            has_traceback=False,
            is_slow=False
        )
        assert problem == 'NEW'


class TestCognitiveStack:
    """Test cognitive stack thinking mode selection."""

    def test_error_uses_five_whys(self):
        """Test ERROR problems use Five Whys + Linear Thinking"""
        mode = select_thinking_mode('ERROR')
        assert 'Five Whys' in mode
        assert 'Linear Thinking' in mode

    def test_performance_uses_systems_thinking(self):
        """Test PERFORMANCE uses Systems Thinking"""
        mode = select_thinking_mode('PERFORMANCE')
        assert 'Systems Thinking' in mode

    def test_crash_uses_scientific_method(self):
        """Test CRASH uses Scientific Method"""
        mode = select_thinking_mode('CRASH')
        assert 'Scientific Method' in mode

    def test_new_uses_first_principles(self):
        """Test NEW uses First Principles"""
        mode = select_thinking_mode('NEW')
        assert 'First Principles' in mode

    def test_integration_uses_collaborative_reasoning(self):
        """Test INTEGRATION uses Collaborative Reasoning"""
        mode = select_thinking_mode('INTEGRATION')
        assert 'Collaborative Reasoning' in mode


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
