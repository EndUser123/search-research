"""Tests for verification/engine.py - RED PHASE

Characterization tests for verification engine behavior.

These tests CAPTURE CURRENT BEHAVIOR before implementing the verification engine.
Run with: pytest packages/loop-code/tests/test_verification_engine.py -v
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ClaimType(Enum):
    """Type of verification claim."""
    ABSENCE = "absence"
    RULE = "rule"
    PRESENCE = "presence"


class VerdictStatus(Enum):
    """Status of a verification verdict."""
    SUPPORTED = "supported"
    REFUTED = "refuted"
    SILENT = "silent"


@dataclass
class VerificationClaim:
    """A claim to be verified."""
    claim_type: ClaimType
    target: str
    facts: dict[str, Any]


@dataclass
class ToolEventView:
    """Wrapper over evidence_store events with normalized target and facts."""
    tool_name: str
    target: str
    facts: dict[str, Any]


@dataclass
class VerificationVerdict:
    """Result of verifying a claim against events."""
    claim: VerificationClaim
    status: VerdictStatus
    evidence: list[ToolEventView]


class TestToolEventViewWrapper:
    """Tests for ToolEventView wrapper over evidence_store events."""

    def test_tool_event_view_has_required_fields(self):
        """Characterization: ToolEventView requires tool_name, target, facts."""
        # Arrange
        view = ToolEventView(
            tool_name="Read",
            target="/path/to/file.py",
            facts={"exists": True, "line_count": 100}
        )

        # Assert
        assert view.tool_name == "Read"
        assert view.target == "/path/to/file.py"
        assert view.facts == {"exists": True, "line_count": 100}

    def test_tool_event_view_normalizes_target(self):
        """Characterization: ToolEventView normalizes target path."""
        # Arrange & Act
        view = ToolEventView(
            tool_name="Glob",
            target="**/*.py",
            facts={"matches": ["file1.py", "file2.py"]}
        )

        # Assert
        assert view.target == "**/*.py"
        assert view.facts["matches"] == ["file1.py", "file2.py"]


class TestBuildVerdicts:
    """Tests for build_verdicts() function."""

    def test_build_verdicts_returns_list_of_verification_verdict(self):
        """Characterization: build_verdicts() returns list[VerificationVerdict]."""
        # This test will FAIL until implementation exists
        from scripts.verification.engine import build_verdicts

        # Arrange
        claims = [
            VerificationClaim(
                claim_type=ClaimType.ABSENCE,
                target="/nonexistent.py",
                facts={"expected_absence": True}
            )
        ]
        events = []

        # Act
        verdicts = build_verdicts(claims, events)

        # Assert
        assert isinstance(verdicts, list)
        assert len(verdicts) == 1
        assert isinstance(verdicts[0], VerificationVerdict)
        assert verdicts[0].claim == claims[0]

    def test_build_verdicts_with_multiple_claims(self):
        """Characterization: build_verdicts() handles multiple claims."""
        from scripts.verification.engine import build_verdicts

        # Arrange
        claims = [
            VerificationClaim(
                claim_type=ClaimType.ABSENCE,
                target="/absent.py",
                facts={}
            ),
            VerificationClaim(
                claim_type=ClaimType.RULE,
                target="*.txt",
                facts={"pattern": "README"}
            )
        ]
        events = []

        # Act
        verdicts = build_verdicts(claims, events)

        # Assert
        assert len(verdicts) == 2
        assert all(isinstance(v, VerificationVerdict) for v in verdicts)

    def test_build_verdicts_includes_evidence_in_verdict(self):
        """Characterization: build_verdicts() includes matching evidence in verdict."""
        from scripts.verification.engine import build_verdicts

        # Arrange
        claims = [
            VerificationClaim(
                claim_type=ClaimType.PRESENCE,
                target="/present.py",
                facts={}
            )
        ]
        events = [
            ToolEventView(
                tool_name="Read",
                target="/present.py",
                facts={"exists": True}
            )
        ]

        # Act
        verdicts = build_verdicts(claims, events)

        # Assert
        assert len(verdicts) == 1
        assert len(verdicts[0].evidence) == 1
        assert verdicts[0].evidence[0].target == "/present.py"


class TestMatchClaimToEvents:
    """Tests for match_claim_to_events() function."""

    def test_absence_claim_with_matching_ls_output_returns_supported(self):
        """Characterization: Absence claim with matching ls output returns SUPPORTED."""
        from scripts.verification.engine import match_claim_to_events

        # Arrange
        claim = VerificationClaim(
            claim_type=ClaimType.ABSENCE,
            target="/tmp/nonexistent_file.py",
            facts={}
        )
        events = [
            ToolEventView(
                tool_name="Bash",
                target="ls /tmp/",
                facts={"exit_code": 0, "files": ["other.py", "data.txt"]}
            )
        ]

        # Act
        status = match_claim_to_events(claim, events)

        # Assert
        assert status == VerdictStatus.SUPPORTED

    def test_absence_claim_with_matching_glob_output_returns_supported(self):
        """Characterization: Absence claim with matching glob output returns SUPPORTED."""
        from scripts.verification.engine import match_claim_to_events

        # Arrange
        claim = VerificationClaim(
            claim_type=ClaimType.ABSENCE,
            target="**/*_deleted.py",
            facts={}
        )
        events = [
            ToolEventView(
                tool_name="Glob",
                pattern="**/*_deleted.py",
                facts={"matches": []}
            )
        ]

        # Act
        status = match_claim_to_events(claim, events)

        # Assert
        assert status == VerdictStatus.SUPPORTED

    def test_silent_claim_for_unrelated_paths(self):
        """Characterization: Claims for unrelated paths return SILENT."""
        from scripts.verification.engine import match_claim_to_events

        # Arrange
        claim = VerificationClaim(
            claim_type=ClaimType.ABSENCE,
            target="/src/feature.py",
            facts={}
        )
        events = [
            ToolEventView(
                tool_name="Read",
                target="/docs/readme.md",
                facts={"exists": True}
            )
        ]

        # Act
        status = match_claim_to_events(claim, events)

        # Assert
        assert status == VerdictStatus.SILENT

    def test_rule_claim_requires_read_or_glob_of_relevant_file(self):
        """Characterization: Rule claim requires Read or Glob of relevant file."""
        from scripts.verification.engine import match_claim_to_events

        # Arrange
        claim = VerificationClaim(
            claim_type=ClaimType.RULE,
            target="test_*.py",
            facts={"assertion": "has pytest imports"}
        )
        events = [
            ToolEventView(
                tool_name="Read",
                target="test_main.py",
                facts={"content": "import pytest"}
            )
        ]

        # Act
        status = match_claim_to_events(claim, events)

        # Assert
        assert status == VerdictStatus.SUPPORTED

    def test_rule_claim_without_relevant_events_returns_refuted(self):
        """Characterization: Rule claim without Read/Glob returns REFUTED."""
        from scripts.verification.engine import match_claim_to_events

        # Arrange
        claim = VerificationClaim(
            claim_type=ClaimType.RULE,
            target="*.py",
            facts={"assertion": "has type hints"}
        )
        events = [
            ToolEventView(
                tool_name="Bash",
                target="pwd",
                facts={"exit_code": 0}
            )
        ]

        # Act
        status = match_claim_to_events(claim, events)

        # Assert
        assert status == VerdictStatus.REFUTED

    def test_absence_claim_refuted_when_file_found(self):
        """Characterization: Absence claim returns REFUTED when file is found."""
        from scripts.verification.engine import match_claim_to_events

        # Arrange
        claim = VerificationClaim(
            claim_type=ClaimType.ABSENCE,
            target="/tmp/secret.py",
            facts={}
        )
        events = [
            ToolEventView(
                tool_name="Glob",
                pattern="**/secret.py",
                facts={"matches": ["/tmp/secret.py"]}
            )
        ]

        # Act
        status = match_claim_to_events(claim, events)

        # Assert
        assert status == VerdictStatus.REFUTED


class TestVerificationEngineIntegration:
    """Integration tests for complete verification workflow."""

    def test_complete_workflow_absence_verified(self):
        """Characterization: Complete workflow for verified absence claim."""
        from scripts.verification.engine import build_verdicts

        # Arrange
        claims = [
            VerificationClaim(
                claim_type=ClaimType.ABSENCE,
                target="**/deprecated.py",
                facts={}
            )
        ]
        events = [
            ToolEventView(
                tool_name="Glob",
                pattern="**/deprecated.py",
                facts={"matches": []}
            )
        ]

        # Act
        verdicts = build_verdicts(claims, events)

        # Assert
        assert len(verdicts) == 1
        assert verdicts[0].status == VerdictStatus.SUPPORTED
        assert len(verdicts[0].evidence) == 1

    def test_complete_workflow_rule_verified(self):
        """Characterization: Complete workflow for verified rule claim."""
        from scripts.verification.engine import build_verdicts

        # Arrange
        claims = [
            VerificationClaim(
                claim_type=ClaimType.RULE,
                target="tests/test_*.py",
                facts={"assertion": "has pytest imports"}
            )
        ]
        events = [
            ToolEventView(
                tool_name="Glob",
                pattern="tests/test_*.py",
                facts={"matches": ["tests/test_main.py"]}
            ),
            ToolEventView(
                tool_name="Read",
                target="tests/test_main.py",
                facts={"content": "import pytest\ndef test_something():\n    pass"}
            )
        ]

        # Act
        verdicts = build_verdicts(claims, events)

        # Assert
        assert len(verdicts) == 1
        assert verdicts[0].status == VerdictStatus.SUPPORTED
        assert len(verdicts[0].evidence) == 2

    def test_complete_workflow_silent_claim(self):
        """Characterization: Complete workflow for silent claim (unrelated)."""
        from scripts.verification.engine import build_verdicts

        # Arrange
        claims = [
            VerificationClaim(
                claim_type=ClaimType.ABSENCE,
                target="/src/legacy.py",
                facts={}
            )
        ]
        events = [
            ToolEventView(
                tool_name="Read",
                target="/docs/api.md",
                facts={"exists": True}
            )
        ]

        # Act
        verdicts = build_verdicts(claims, events)

        # Assert
        assert len(verdicts) == 1
        assert verdicts[0].status == VerdictStatus.SILENT
        assert len(verdicts[0].evidence) == 0
