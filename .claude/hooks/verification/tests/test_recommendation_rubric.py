"""Tests for verification/recommendation_rubric.py — advisory quality checks."""

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from verification.recommendation_rubric import RecommendationAssessment, assess_recommendation


@dataclass
class _FakeClaim:
    id: str
    text: str
    targets: list[str]
    type: str = "ABSENCE"
    confidence: float = 0.9
    risk_domain: str = "SYSTEM"
    has_hedge: bool = False
    decomposition_eligible: bool = False


class TestGoalDetection:
    def test_goal_present(self):
        claim = _FakeClaim(id="1", text="the goal is to reduce latency", targets=[])
        result = assess_recommendation(claim)
        assert result.has_goal is True
        assert "states goal" in result.notes

    def test_objective_present(self):
        claim = _FakeClaim(id="2", text="our objective is to simplify the API", targets=[])
        result = assess_recommendation(claim)
        assert result.has_goal is True

    def test_no_goal(self):
        claim = _FakeClaim(id="3", text="the file was created successfully", targets=[])
        result = assess_recommendation(claim)
        assert result.has_goal is False


class TestAssumptionDetection:
    def test_assumption_present(self):
        claim = _FakeClaim(id="4", text="assuming the network is reliable, we can proceed", targets=[])
        result = assess_recommendation(claim)
        assert result.has_assumptions is True
        assert "names assumptions" in result.notes

    def test_conditional_present(self):
        claim = _FakeClaim(id="5", text="if the service is up, then restart it", targets=[])
        result = assess_recommendation(claim)
        assert result.has_assumptions is True

    def test_no_assumption(self):
        claim = _FakeClaim(id="6", text="run the tests", targets=[])
        result = assess_recommendation(claim)
        assert result.has_assumptions is False


class TestTradeoffDetection:
    def test_tradeoff_present(self):
        claim = _FakeClaim(id="7", text="this approach has a trade-off: faster but uses more memory", targets=[])
        result = assess_recommendation(claim)
        assert result.has_tradeoffs is True
        assert result.has_downside is True
        assert "acknowledges tradeoffs" in result.notes

    def test_downside_present(self):
        claim = _FakeClaim(id="8", text="the downside is increased complexity", targets=[])
        result = assess_recommendation(claim)
        assert result.has_tradeoffs is True

    def test_no_tradeoff(self):
        claim = _FakeClaim(id="9", text="the tests all pass", targets=[])
        result = assess_recommendation(claim)
        assert result.has_tradeoffs is False


class TestAlternativeDetection:
    def test_alternative_present(self):
        claim = _FakeClaim(id="10", text="an alternative would be to use a cache instead", targets=[])
        result = assess_recommendation(claim)
        assert result.has_alternative_not_chosen is True
        assert "considers alternatives" in result.notes

    def test_instead_present(self):
        claim = _FakeClaim(id="11", text="use Redis instead of memcached", targets=[])
        result = assess_recommendation(claim)
        assert result.has_alternative_not_chosen is True

    def test_no_alternative(self):
        claim = _FakeClaim(id="12", text="the fix is applied", targets=[])
        result = assess_recommendation(claim)
        assert result.has_alternative_not_chosen is False


class TestNotesField:
    def test_no_quality_markers(self):
        claim = _FakeClaim(id="13", text="file.py exists", targets=[])
        result = assess_recommendation(claim)
        assert "lacks" in result.notes

    def test_all_markers(self):
        claim = _FakeClaim(
            id="14",
            text="assuming latency matters, the goal is to optimize. The trade-off is complexity. An alternative is caching.",
            targets=[],
        )
        result = assess_recommendation(claim)
        assert "states goal" in result.notes
        assert "names assumptions" in result.notes
        assert "acknowledges tradeoffs" in result.notes
        assert "considers alternatives" in result.notes


class TestStringInput:
    def test_raw_string_input(self):
        result = assess_recommendation("the goal is to ship faster")
        assert result.has_goal is True
        assert result.claim_id == ""


class TestFrozenAssessment:
    def test_frozen(self):
        assessment = RecommendationAssessment(
            claim_id="1",
            has_goal=False,
            has_assumptions=False,
            has_tradeoffs=False,
            has_downside=False,
            has_alternative_not_chosen=False,
            notes="test",
        )
        try:
            assessment.notes = "modified"
            assert False, "Should raise"
        except AttributeError:
            pass
