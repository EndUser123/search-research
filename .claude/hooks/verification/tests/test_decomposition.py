"""Tests for verification/decomposition.py — compound claim splitting."""

import sys
from dataclasses import dataclass
from pathlib import Path

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from verification.decomposition import (
    DecompositionResult,
    SubClaim,
    decompose_claim,
    should_decompose,
)


@dataclass
class _FakeClaim:
    """Minimal claim-like object for testing."""
    id: str
    text: str
    targets: list[str]
    type: str = "ABSENCE"
    confidence: float = 0.9
    risk_domain: str = "SYSTEM"
    has_hedge: bool = False
    decomposition_eligible: bool = False


@dataclass
class _FakeVerdict:
    """Minimal verdict-like object for testing."""
    claim_id: str
    status: object
    supporting_evidence: list[str]
    refuting_evidence: list[str]
    confidence: float = 0.9


class _VS:
    """Fake VerificationStatus."""
    SILENT = "SILENT"
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    SELF_VERIFIED = "SELF_VERIFIED"


# --- should_decompose ---

class TestShouldDecompose:
    def test_silent_with_conjunction(self):
        claim = _FakeClaim(id="1", text="tests pass and hooks work", targets=[])
        verdict = _FakeVerdict(claim_id="1", status=_VS.SILENT, supporting_evidence=[], refuting_evidence=[])
        assert should_decompose(claim, verdict) is True

    def test_silent_with_aggregate(self):
        claim = _FakeClaim(id="2", text="all files have been processed", targets=[])
        verdict = _FakeVerdict(claim_id="2", status=_VS.SILENT, supporting_evidence=[], refuting_evidence=[])
        assert should_decompose(claim, verdict) is True

    def test_silent_atomic(self):
        claim = _FakeClaim(id="3", text="file X was created", targets=["X"])
        verdict = _FakeVerdict(claim_id="3", status=_VS.SILENT, supporting_evidence=[], refuting_evidence=[])
        assert should_decompose(claim, verdict) is False

    def test_supported_with_conjunction(self):
        claim = _FakeClaim(id="4", text="tests pass and hooks work", targets=[])
        verdict = _FakeVerdict(claim_id="4", status=_VS.SUPPORTED, supporting_evidence=["ev"], refuting_evidence=[])
        assert should_decompose(claim, verdict) is False

    def test_silent_with_indirect(self):
        claim = _FakeClaim(id="5", text="based on the logs, therefore the fix works", targets=[])
        verdict = _FakeVerdict(claim_id="5", status=_VS.SILENT, supporting_evidence=[], refuting_evidence=[])
        assert should_decompose(claim, verdict) is True


# --- decompose_claim ---

class TestDecomposeClaim:
    def test_conjunction_split(self):
        claim = _FakeClaim(id="10", text="tests pass and hooks work correctly", targets=[])
        result = decompose_claim(claim)
        assert result.is_compound is True
        assert result.trigger_reason == "conjunction"
        assert len(result.sub_claims) == 2
        assert "tests pass" in result.sub_claims[0].text.lower()
        assert "hooks work" in result.sub_claims[1].text.lower()

    def test_aggregate_split(self):
        claim = _FakeClaim(
            id="11",
            text="all of hooks, skills, tests pass",
            targets=["hooks", "skills", "tests"],
        )
        result = decompose_claim(claim)
        # Should detect aggregate or conjunction
        assert result.is_compound is True

    def test_indirect_evidence_split(self):
        claim = _FakeClaim(
            id="12",
            text="based on the output, therefore the fix works",
            targets=[],
        )
        result = decompose_claim(claim)
        assert result.is_compound is True
        assert result.trigger_reason == "indirect"
        assert len(result.sub_claims) == 1

    def test_atomic_claim_no_split(self):
        claim = _FakeClaim(id="13", text="file X was created", targets=["X"])
        result = decompose_claim(claim)
        assert result.is_compound is False
        assert result.sub_claims == ()

    def test_sub_claim_targets_inherited(self):
        claim = _FakeClaim(
            id="14",
            text="hooks pass and tests pass",
            targets=["hooks", "tests"],
        )
        result = decompose_claim(claim)
        assert result.is_compound is True
        # Each sub-claim should inherit parent targets as fallback
        for sc in result.sub_claims:
            assert len(sc.targets) > 0

    def test_empty_claim(self):
        claim = _FakeClaim(id="15", text="", targets=[])
        result = decompose_claim(claim)
        assert result.is_compound is False

    def test_result_is_frozen(self):
        claim = _FakeClaim(id="16", text="X and Y", targets=[])
        result = decompose_claim(claim)
        try:
            result.is_compound = False
            assert False, "Should raise on frozen dataclass"
        except AttributeError:
            pass
