"""Tests for engine.py EnrichedVerdict and analyze_silent_verdicts()."""

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from verification.engine import (
    EnrichedVerdict,
    VerificationStatus,
    VerificationVerdict,
    analyze_silent_verdicts,
    micro_fallback_verify,
)


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


class TestEnrichedVerdictPassthrough:
    """Non-SILENT verdicts should pass through unchanged."""

    def test_supported_verdict_unchanged(self):
        claim = _FakeClaim(id="1", text="X exists", targets=["X"])
        verdict = VerificationVerdict(
            claim_id="1",
            status=VerificationStatus.SUPPORTED,
            supporting_evidence=["ev"],
            refuting_evidence=[],
            confidence=0.9,
        )
        enriched = analyze_silent_verdicts([verdict], [claim], [])
        assert len(enriched) == 1
        assert enriched[0].final_status == VerificationStatus.SUPPORTED
        assert enriched[0].decomposition is None
        assert enriched[0].coverage is None

    def test_self_verified_verdict_unchanged(self):
        claim = _FakeClaim(id="2", text="verified this session", targets=[])
        verdict = VerificationVerdict(
            claim_id="2",
            status=VerificationStatus.SELF_VERIFIED,
            supporting_evidence=[],
            refuting_evidence=[],
            confidence=0.9,
        )
        enriched = analyze_silent_verdicts([verdict], [claim], [])
        assert enriched[0].final_status == VerificationStatus.SELF_VERIFIED


class TestAnalyzeSilentVerdicts:
    """SILENT verdicts should trigger second-stage analysis."""

    def test_silent_atomic_no_upgrade(self):
        """Atomic SILENT claim with no evidence stays SILENT."""
        claim = _FakeClaim(id="10", text="file X was created", targets=["X"])
        verdict = VerificationVerdict(
            claim_id="10",
            status=VerificationStatus.SILENT,
            supporting_evidence=[],
            refuting_evidence=[],
            confidence=0.9,
        )
        enriched = analyze_silent_verdicts([verdict], [claim], [])
        assert enriched[0].final_status == VerificationStatus.SILENT

    def test_silent_compound_upgrade(self):
        """Compound SILENT claim may be upgraded via decomposition."""
        claim = _FakeClaim(
            id="11",
            text="tests pass and hooks work",
            targets=["tests", "hooks"],
        )
        verdict = VerificationVerdict(
            claim_id="11",
            status=VerificationStatus.SILENT,
            supporting_evidence=[],
            refuting_evidence=[],
            confidence=0.9,
        )
        # Provide tool events that match sub-claim text
        events = [
            {"name": "Bash", "output": "tests pass", "command": "pytest"},
            {"name": "Bash", "output": "hooks work", "command": "python hook.py"},
        ]
        enriched = analyze_silent_verdicts([verdict], [claim], events)
        # Decomposition should have been attempted
        assert enriched[0].decomposition is not None or enriched[0].coverage is not None

    def test_fail_open_on_error(self):
        """If enrichment raises, should return unenriched verdict."""
        claim = _FakeClaim(id="12", text="X and Y", targets=["X"])
        verdict = VerificationVerdict(
            claim_id="12",
            status=VerificationStatus.SILENT,
            supporting_evidence=[],
            refuting_evidence=[],
            confidence=0.9,
        )
        # Pass bad tool_events that might cause issues
        enriched = analyze_silent_verdicts([verdict], [claim], [None])
        assert len(enriched) == 1
        # Should fail-open gracefully
        assert enriched[0].final_status in (VerificationStatus.SILENT, VerificationStatus.SUPPORTED)


class TestMicroFallback:
    def test_file_path_in_glob(self):
        claim = _FakeClaim(id="20", text="file at hooks/test.py exists", targets=["hooks/test.py"])
        events = [{"name": "Glob", "output": "hooks/test.py", "command": "glob hooks/test.py"}]
        result = micro_fallback_verify(claim, events)
        assert result == VerificationStatus.SUPPORTED

    def test_command_in_bash(self):
        # Claim text must contain a command pattern that matches the event command
        claim = _FakeClaim(id="21", text="ran pytest tests/ successfully", targets=[])
        events = [{"name": "Bash", "output": "ok", "command": "pytest tests/"}]
        result = micro_fallback_verify(claim, events)
        assert result == VerificationStatus.SUPPORTED

    def test_no_match_returns_none(self):
        claim = _FakeClaim(id="22", text="the sky is blue", targets=[])
        events = [{"name": "Read", "output": "file contents", "command": "read file.txt"}]
        result = micro_fallback_verify(claim, events)
        assert result is None

    def test_empty_events(self):
        claim = _FakeClaim(id="23", text="file.py exists", targets=["file.py"])
        result = micro_fallback_verify(claim, [])
        assert result is None


class TestEnrichedVerdictDataclass:
    def test_fields_exist(self):
        ev = EnrichedVerdict(
            verdict=VerificationVerdict("1", VerificationStatus.SILENT, [], [], 0.9),
            decomposition=None,
            sub_verdicts=(),
            coverage=None,
            recommendation=None,
            final_status=VerificationStatus.SILENT,
            final_confidence=0.9,
        )
        assert ev.final_status == VerificationStatus.SILENT
        assert ev.final_confidence == 0.9
