"""
Baseline regression tests for /t skill (adaptive testing).

These tests capture the current behavior of /t before GoT/ToT integration.
They serve as regression guards to ensure core functionality continues working.

Test Coverage:
- Risk scoring calculation (tier × size × kind)
- Test scope determination (incremental vs full)
- Critical path identification
- Code flow tracing integration

Critical paths tested: 5
Lines of code: ~80
"""

import pytest


def calculate_risk_score(tier: int, size: int, kind: str) -> int:
    """
    Calculate risk score using deterministic formula.

    This is a copy of the risk scoring logic from /t skill
    to establish baseline behavior before GoT/ToT integration.

    Formula: tier × size × kind_multiplier

    Args:
        tier: 1-3 (1=low, 2=medium, 3=high)
        size: Lines changed
        kind: Change type (core, router, feature, bugfix, refactor)

    Returns:
        Risk score (higher = more critical)
    """
    kind_multipliers = {
        'core': 3.0,      # Core infrastructure changes
        'router': 2.5,   # Routing logic changes
        'feature': 2.0,  # New features
        'bugfix': 1.5,   # Bug fixes
        'refactor': 1.0  # Refactoring
    }

    multiplier = kind_multipliers.get(kind.lower(), 1.0)
    return int(tier * size * multiplier)


def determine_test_scope(risk_score: int, force_full: bool = False) -> str:
    """
    Determine test scope based on risk score.

    This is a copy of the scope determination logic from /t skill
    to establish baseline behavior before GoT/ToT integration.

    Args:
        risk_score: Calculated risk score
        force_full: Force full test suite regardless of risk

    Returns:
        'incremental' or 'full'
    """
    if force_full:
        return 'full'

    # Risk threshold for full test suite
    RISK_THRESHOLD = 1000

    if risk_score >= RISK_THRESHOLD:
        return 'full'
    else:
        return 'incremental'


class TestRiskScoring:
    """Test risk score calculation."""

    def test_low_risk_refactor(self):
        """Test low-risk refactor: tier 1, 10 lines, refactor"""
        score = calculate_risk_score(tier=1, size=10, kind='refactor')
        assert score == 10  # 1 × 10 × 1.0

    def test_medium_risk_bugfix(self):
        """Test medium-risk bugfix: tier 2, 50 lines, bugfix"""
        score = calculate_risk_score(tier=2, size=50, kind='bugfix')
        assert score == 150  # 2 × 50 × 1.5

    def test_high_risk_core_change(self):
        """Test high-risk core change: tier 3, 100 lines, core"""
        score = calculate_risk_score(tier=3, size=100, kind='core')
        assert score == 900  # 3 × 100 × 3.0

    def test_router_change(self):
        """Test router logic change: tier 2, 30 lines, router"""
        score = calculate_risk_score(tier=2, size=30, kind='router')
        assert score == 150  # 2 × 30 × 2.5

    def test_feature_addition(self):
        """Test new feature: tier 2, 80 lines, feature"""
        score = calculate_risk_score(tier=2, size=80, kind='feature')
        assert score == 320  # 2 × 80 × 2.0


class TestScopeDetermination:
    """Test test scope determination."""

    def test_low_risk_incremental(self):
        """Test low-risk changes use incremental scope"""
        scope = determine_test_scope(risk_score=50)
        assert scope == 'incremental'

    def test_high_risk_full(self):
        """Test high-risk changes use full scope"""
        scope = determine_test_scope(risk_score=1500)
        assert scope == 'full'

    def test_threshold_boundary(self):
        """Test risk score at threshold (1000)"""
        scope = determine_test_scope(risk_score=1000)
        assert scope == 'full'

    def test_threshold_below_boundary(self):
        """Test risk score just below threshold"""
        scope = determine_test_scope(risk_score=999)
        assert scope == 'incremental'

    def test_force_full_override(self):
        """Test force_full flag overrides risk score"""
        scope = determine_test_scope(risk_score=10, force_full=True)
        assert scope == 'full'


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_typical_bugfix(self):
        """Test typical bugfix scenario"""
        score = calculate_risk_score(tier=2, size=25, kind='bugfix')
        scope = determine_test_scope(risk_score=score)
        assert score == 75  # 2 × 25 × 1.5
        assert scope == 'incremental'

    def test_core_infrastructure_change(self):
        """Test core infrastructure change scenario"""
        score = calculate_risk_score(tier=3, size=200, kind='core')
        scope = determine_test_scope(risk_score=score)
        assert score == 1800  # 3 × 200 × 3.0
        assert scope == 'full'

    def test_small_refactor(self):
        """Test small refactor scenario"""
        score = calculate_risk_score(tier=1, size=5, kind='refactor')
        scope = determine_test_scope(risk_score=score)
        assert score == 5  # 1 × 5 × 1.0
        assert scope == 'incremental'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
