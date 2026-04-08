#!/usr/bin/env python3
"""Tests for Stop_hypothesis_as_fact_gate.py

These tests verify TASK-004 implementation:
1. Blocks ungrounded confident claims
2. Allows hedged claims without evidence
3. Allows confident claims grounded in tool events
4. Respects HYPOTHESIS_AS_FACT_GATE_ENABLED and HYPOTHESIS_AS_FACT_GATE_MODE
5. Path normalization unit test confirms C:\foo\bar matches C:/foo/bar in tool events
6. Terminal-scoped isolation (Phase 1)

SCOPING NOTE: Phase 1 gate is terminal-scoped, not turn-scoped.
Tests must not assume turn isolation.
"""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Import gate under test
# NOTE: _entity_in_tool_events and _normalize_path were removed in the Phase 2
# refactor (TASK-008) that delegated entity matching to the verification engine.
# Tests using those symbols (TestPathNormalization, TestEntityMatching) fail with
# NameError — they test the pre-refactor gate and are kept for historical reference
# but are no longer exercising live code.
try:
    from Stop_hypothesis_as_fact_gate import (
        _entity_in_tool_events,
        _normalize_path,
        _should_block_claim,
        run,
    )
except ImportError:
    # Phase 2 refactored gate: _entity_in_tool_events and _normalize_path removed.
    # Import only the functions that still exist.
    try:
        from Stop_hypothesis_as_fact_gate import (
            _should_block_claim,
            load_tool_events_for_context,
            run,
        )  # type: ignore
    except ImportError:
        skip = True  # type: ignore


@unittest.skip(
    "Phase 2 refactor removed _normalize_path - entity matching delegated to verification engine"
)
class TestPathNormalization(unittest.TestCase):
    """Test path normalization for cross-platform comparison.

    CRITICAL REQUIREMENT: Path normalization MUST normalize separators
    (convert \\ to /) and resolve relative paths to absolute before comparison.
    This prevents Windows vs Unix path false-negatives.

    Example: C:\foo\bar should match C:/foo/bar in tool events.

    NOTE: These tests are skipped because _normalize_path was removed in Phase 2
    refactor (TASK-008). Path normalization is now handled internally by the
    verification engine's build_verdicts() function.
    """

    def test_windows_backslashes_normalized(self):
        """Test that Windows backslashes are converted to forward slashes."""
        result = _normalize_path(r"C:\foo\bar\baz.txt")
        assert result == "C:/foo/bar/baz.txt", f"Expected 'C:/foo/bar/baz.txt', got '{result}'"

    def test_mixed_slash_normalization(self):
        """Test that mixed slashes are normalized."""
        result = _normalize_path(r"C:\foo/bar\baz.txt")
        assert result == "C:/foo/bar/baz.txt", f"Expected 'C:/foo/bar/baz.txt', got '{result}'"

    def test_redundant_slashes_removed(self):
        """Test that redundant slashes are removed."""
        result = _normalize_path("C://foo///bar")
        assert result == "C:/foo/bar", f"Expected 'C:/foo/bar', got '{result}'"

    def test_empty_path_returns_empty(self):
        """Test that empty path returns empty string."""
        result = _normalize_path("")
        assert result == "", f"Expected '', got '{result}'"

    def test_relative_paths_preserved(self):
        """Test that relative paths are preserved (Phase 1 limitation)."""
        result = _normalize_path("relative/path/to/file.txt")
        assert (
            result == "relative/path/to/file.txt"
        ), f"Expected 'relative/path/to/file.txt', got '{result}'"


@unittest.skip(
    "Phase 2 refactor removed _entity_in_tool_events - entity matching delegated to verification engine"
)
class TestEntityMatching(unittest.TestCase):
    """Test entity matching against tool events.

    Phase 1: Simple string matching after path normalization.
    Future: Enhanced matching with entity type awareness.

    NOTE: These tests are skipped because _entity_in_tool_events was removed in
    Phase 2 refactor (TASK-008). Entity matching is now handled by the verification
    engine's build_verdicts() function which returns VerificationVerdict objects.
    """

    def test_entity_found_in_command(self):
        """Test that entity is found in tool command."""
        tool_events = [
            {
                "id": 1,
                "command": "ls packages/Package/skills/",
                "cwd": "/path",
                "output": "",
            }
        ]
        assert _entity_in_tool_events("packages/Package/skills/", tool_events) is True

    def test_entity_found_in_output(self):
        """Test that entity is found in tool output."""
        tool_events = [
            {
                "id": 1,
                "command": "",
                "cwd": "/path",
                "output": "Found file: packages/Package/skills/README.md",
            }
        ]
        assert _entity_in_tool_events("packages/Package/skills/", tool_events) is True

    def test_entity_not_found(self):
        """Test that entity is not found when absent."""
        tool_events = [
            {
                "id": 1,
                "command": "ls other/location/",
                "cwd": "/path",
                "output": "",
            }
        ]
        assert _entity_in_tool_events("packages/Package/skills/", tool_events) is False

    def test_windows_path_matches_unix_path(self):
        """Test CRITICAL: C:\foo\bar matches C:/foo/bar in tool events.

        This is the core path normalization test case from TASK-004 acceptance criteria.
        """
        tool_events = [
            {
                "id": 1,
                "command": "ls C:/foo/bar",
                "cwd": "/path",
                "output": "",
            }
        ]
        # Claim uses Windows backslashes
        assert _entity_in_tool_events(r"C:\foo\bar", tool_events) is True

    def test_case_insensitive_matching(self):
        """Test that matching is case-insensitive."""
        tool_events = [
            {
                "id": 1,
                "command": "ls packages/package/skills/",
                "cwd": "/path",
                "output": "",
            }
        ]
        # Different case should still match
        assert _entity_in_tool_events("packages/Package/skills/", tool_events) is True

    def test_empty_events_returns_false(self):
        """Test that empty tool events return False."""
        assert _entity_in_tool_events("any/entity", []) is False

    def test_none_entity_returns_false(self):
        """Test that None entity returns False."""
        tool_events = [{"id": 1, "command": "ls", "cwd": "/path", "output": ""}]
        assert _entity_in_tool_events("", tool_events) is False


class TestClaimBlocking(unittest.TestCase):
    """Test claim blocking logic.

    NOTE: Phase 2 refactor changed _should_block_claim signature from
    (claim, tool_events) to (claim, verdict). Tests updated to use mock verdicts.
    """

    def setUp(self):
        """Set up test fixtures."""
        # Mock RawClaim for testing
        self.RawClaim = Mock
        self.RawClaim.has_hedge = False
        self.RawClaim.confidence = 0.8
        self.RawClaim.subject_entity = "packages/Package/skills/"
        self.RawClaim.risk_domain = "FS_CRITICAL"

        # Create mock verdict factory
        self.MockVerdict = Mock
        self.MockVerdict.status = None  # Will be set per test

    def _make_verdict(self, status):
        """Create a mock verdict with given status.

        Args:
            status: String like "SUPPORTED", "SILENT", or "REFUTED"
        """
        from verification.engine import VerificationStatus

        verdict = Mock()
        verdict.status = VerificationStatus[status]
        # Add serializable attributes for JSON logging
        verdict.claim_id = "test-claim-id"
        verdict.supporting_evidence = []
        verdict.refuting_evidence = []
        verdict.confidence = 0.8
        return verdict

    def test_hedged_claim_passes_without_evidence(self):
        """Test that hedged claims pass without evidence."""
        claim = self.RawClaim()
        claim.has_hedge = True
        claim.confidence = 0.8
        claim.subject_entity = "any/entity"

        # SILENT verdict = no evidence, but hedged claims pass anyway
        result = _should_block_claim(claim, self._make_verdict("SILENT"))
        assert result is False, "Hedged claims should pass without evidence"

    def test_low_confidence_claim_passes(self):
        """Test that low confidence claims pass."""
        claim = self.RawClaim()
        claim.has_hedge = False
        claim.confidence = 0.5
        claim.subject_entity = "any/entity"

        # SILENT verdict = no evidence, but low confidence claims pass anyway
        result = _should_block_claim(claim, self._make_verdict("SILENT"))
        assert result is False, "Low confidence claims should pass"

    def test_grounded_claim_passes(self):
        """Test that claims grounded in tool events pass."""
        claim = self.RawClaim()
        claim.has_hedge = False
        claim.confidence = 0.8
        claim.subject_entity = "packages/Package/skills/"

        # SUPPORTED verdict = evidence found
        result = _should_block_claim(claim, self._make_verdict("SUPPORTED"))
        assert result is False, "Grounded claims should pass"

    def test_ungrounded_confident_claim_blocked(self):
        """Test that ungrounded confident claims are blocked."""
        claim = self.RawClaim()
        claim.has_hedge = False
        claim.confidence = 0.8
        claim.subject_entity = "packages/Package/skills/"

        # SILENT verdict = no evidence found
        result = _should_block_claim(claim, self._make_verdict("SILENT"))
        assert result is True, "Ungrounded confident claims should be blocked"

    def test_claim_with_empty_entity(self):
        """Test claim with empty entity subject."""
        claim = self.RawClaim()
        claim.has_hedge = False
        claim.confidence = 0.8
        claim.subject_entity = ""

        # SILENT verdict = no evidence, empty entity = ungrounded
        result = _should_block_claim(claim, self._make_verdict("SILENT"))
        assert result is True, "Confident claim with empty entity should be blocked"


class TestGateIntegration(unittest.TestCase):
    """Integration tests for Stop_hypothesis_as_fact_gate.py

    NOTE: Phase 2 refactor replaced HypothesisAsFactDetector with verification module.
    Tests now mock extract_claims and build_verdicts instead.
    """

    def setUp(self):
        """Set up test environment."""
        # Create temporary directory for logs
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"

        # Create mock claim factory
        self.MockClaim = Mock
        self.MockClaim.text = ""
        self.MockClaim.subject_entity = ""
        self.MockClaim.confidence = 0.8
        self.MockClaim.has_hedge = False
        self.MockClaim.type = "ENTITY_ABSENCE"

    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary files
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _make_claim(self, **kwargs):
        """Create a mock claim with given attributes.

        Note: Claim objects from verification module have:
        - text: str
        - targets: list[str] (not subject_entity)
        - confidence: float
        - has_hedge: bool
        - type: str (ABSENCE, PRESENCE, RULE, CONVENTION, etc.)
        - id: str
        - risk_domain: str
        """
        claim = Mock()
        claim.text = kwargs.get("text", "Test claim")
        claim.targets = kwargs.get("targets", ["test/entity/"])
        claim.confidence = kwargs.get("confidence", 0.8)
        claim.has_hedge = kwargs.get("has_hedge", False)
        claim.type = kwargs.get("type", "ABSENCE")
        claim.id = kwargs.get("id", "test-id-123")
        claim.risk_domain = kwargs.get("risk_domain", "FS_CRITICAL")
        return claim

    def _make_verdict(self, status):
        """Create a mock verdict with given status.

        Note: Verdict objects need serializable attributes for JSON logging
        in _log_decision() - claim_id, supporting_evidence, refuting_evidence.
        """
        from verification.engine import VerificationStatus

        verdict = Mock()
        verdict.status = VerificationStatus[status]
        # Add serializable attributes for JSON logging
        verdict.claim_id = "test-claim-id"
        verdict.supporting_evidence = []
        verdict.refuting_evidence = []
        verdict.confidence = 0.8
        return verdict

    @patch.dict(os.environ, {"HYPOTHESIS_AS_FACT_GATE_ENABLED": "false"})
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    def test_gate_disabled_allows_stop(self, mock_load_events):
        """Test that gate allows stop when disabled."""
        mock_load_events.return_value = []

        data = {
            "session_id": "test-session-id",
            "terminal_id": "test-terminal-id",
            "response_text": "Package has no skill/ directory",
        }

        result = run(data)
        assert result.get("allow") is True, "Gate should allow when disabled"
        assert "disabled" in result.get("reason", "").lower()

    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    def test_no_session_id_allows_stop(self, mock_load_events):
        """Test that missing session_id allows stop."""
        data = {
            "session_id": "",
            "terminal_id": "test-terminal-id",
            "response_text": "Package has no skill/ directory",
        }

        result = run(data)
        assert result.get("allow") is True, "Gate should allow without session_id"

    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    def test_short_response_allows_stop(self, mock_load_events):
        """Test that short responses allow stop."""
        data = {
            "session_id": "test-session-id",
            "terminal_id": "test-terminal-id",
            "response_text": "OK",
        }

        result = run(data)
        assert result.get("allow") is True, "Gate should allow short responses"

    @patch("os.fdopen")
    @patch("Stop_hypothesis_as_fact_gate.build_verdicts")
    @patch("Stop_hypothesis_as_fact_gate.extract_claims")
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    @patch.dict(
        os.environ,
        {
            "HYPOTHESIS_AS_FACT_GATE_ENABLED": "true",
            "HYPOTHESIS_AS_FACT_GATE_MODE": "warn",
        },
    )
    def test_warn_mode_issues_warning(
        self, mock_load_events, mock_extract, mock_verdicts, mock_fdopen
    ):
        """Test that warn mode issues warning but allows stop."""
        # Mock fdopen to avoid actual file descriptor operations in tests
        mock_fdopen.return_value.__enter__ = lambda self: self
        mock_fdopen.return_value.__exit__ = lambda self, *args: None
        mock_fdopen.return_value.write = lambda s: None

        # Mock extract_claims to return ungrounded claim
        mock_claim = self._make_claim(
            text="Package has no skill/ directory",
            targets=["Package/skill/"],
            confidence=0.8,
            has_hedge=False,
        )
        mock_extract.return_value = [mock_claim]

        # Mock build_verdicts to return SILENT verdict (no evidence)
        mock_verdict = self._make_verdict("SILENT")
        mock_verdicts.return_value = [mock_verdict]

        # Mock empty tool events (no evidence)
        mock_load_events.return_value = []

        data = {
            "session_id": "test-session-id",
            "terminal_id": "test-terminal-id",
            "response_text": "Package has no skill/ directory",
        }

        result = run(data)
        assert result.get("allow") is True, "Warn mode should allow stop"
        assert "warn" in result.get("reason", "").lower()

    @patch("Stop_hypothesis_as_fact_gate.build_verdicts")
    @patch("Stop_hypothesis_as_fact_gate.extract_claims")
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    @patch.dict(
        os.environ,
        {
            "HYPOTHESIS_AS_FACT_GATE_ENABLED": "true",
            "HYPOTHESIS_AS_FACT_GATE_MODE": "block",
        },
    )
    def test_block_mode_blocks_stop(self, mock_load_events, mock_extract, mock_verdicts):
        """Test that block mode blocks stop."""
        # Mock extract_claims to return ungrounded claim
        mock_claim = self._make_claim(
            text="Package has no skill/ directory",
            targets=["Package/skill/"],
            confidence=0.8,
            has_hedge=False,
        )
        mock_extract.return_value = [mock_claim]

        # Mock build_verdicts to return SILENT verdict (no evidence)
        mock_verdict = self._make_verdict("SILENT")
        mock_verdicts.return_value = [mock_verdict]

        # Mock empty tool events (no evidence)
        mock_load_events.return_value = []

        data = {
            "session_id": "test-session-id",
            "terminal_id": "test-terminal-id",
            "response_text": "Package has no skill/ directory",
        }

        result = run(data)
        assert result.get("allow") is False, "Block mode should block stop"
        assert "ungrounded" in result.get("reason", "").lower()

    @patch("Stop_hypothesis_as_fact_gate.build_verdicts")
    @patch("Stop_hypothesis_as_fact_gate.extract_claims")
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    @patch.dict(os.environ, {"HYPOTHESIS_AS_FACT_GATE_ENABLED": "true"})
    def test_grounded_claim_allows_stop(self, mock_load_events, mock_extract, mock_verdicts):
        """Test that grounded claims allow stop."""
        # Mock extract_claims to return claim
        mock_claim = self._make_claim(
            text="Package has no skill/ directory",
            targets=["Package/skill/"],
            confidence=0.8,
            has_hedge=False,
        )
        mock_extract.return_value = [mock_claim]

        # Mock build_verdicts to return SUPPORTED verdict (evidence found)
        mock_verdict = self._make_verdict("SUPPORTED")
        mock_verdicts.return_value = [mock_verdict]

        # Mock tool events with matching entity
        mock_load_events.return_value = [
            {
                "id": 1,
                "command": "ls Package/skill/",
                "cwd": "/path",
                "output": "",
            }
        ]

        data = {
            "session_id": "test-session-id",
            "terminal_id": "test-terminal-id",
            "response_text": "Package has no skill/ directory",
        }

        result = run(data)
        assert result.get("allow") is True, "Grounded claims should allow stop"

    @patch("Stop_hypothesis_as_fact_gate.build_verdicts")
    @patch("Stop_hypothesis_as_fact_gate.extract_claims")
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    @patch.dict(os.environ, {"HYPOTHESIS_AS_FACT_GATE_ENABLED": "true"})
    def test_hedged_claim_allows_stop(self, mock_load_events, mock_extract, mock_verdicts):
        """Test that hedged claims allow stop without evidence."""
        # Mock extract_claims to return hedged claim
        mock_claim = self._make_claim(
            text="Package might not have skill/ directory",
            targets=["Package/skill/"],
            confidence=0.8,
            has_hedge=True,  # Hedged
        )
        mock_extract.return_value = [mock_claim]

        # Mock build_verdicts to return SILENT verdict (no evidence)
        mock_verdict = self._make_verdict("SILENT")
        mock_verdicts.return_value = [mock_verdict]

        # Mock empty tool events (no evidence needed for hedged claims)
        mock_load_events.return_value = []

        data = {
            "session_id": "test-session-id",
            "terminal_id": "test-terminal-id",
            "response_text": "Package might not have skill/ directory",
        }

        result = run(data)
        assert result.get("allow") is True, "Hedged claims should allow stop"


class TestEvidenceScopeAdapter(unittest.TestCase):
    @patch("Stop_hypothesis_as_fact_gate.load_scoped_tool_events")
    def test_load_tool_events_for_context_uses_session_fresh_scope(self, mock_load_scoped):
        mock_load_scoped.return_value = [{"id": 1, "name": "Read", "command": "foo.py"}]

        result = load_tool_events_for_context(
            session_id="test-session-id",
            terminal_id="test-terminal-id",
            limit=123,
        )

        self.assertEqual(result, [{"id": 1, "name": "Read", "command": "foo.py"}])
        mock_load_scoped.assert_called_once_with(
            session_id="test-session-id",
            terminal_id="test-terminal-id",
            scope="session_fresh",
            limit=123,
        )

    @patch("Stop_hypothesis_as_fact_gate.extract_claims")
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    @patch.dict(os.environ, {"HYPOTHESIS_AS_FACT_GATE_ENABLED": "true"})
    def test_no_claims_allows_stop(self, mock_load_events, mock_extract):
        """Test that no claims allows stop."""
        # Mock extract_claims to return no claims
        mock_extract.return_value = []

        data = {
            "session_id": "test-session-id",
            "terminal_id": "test-terminal-id",
            "response_text": "This response has no claims",
        }

        result = run(data)
        assert result.get("allow") is True, "No claims should allow stop"
        assert "no claims" in result.get("reason", "").lower()

    @patch("Stop_hypothesis_as_fact_gate.extract_claims")
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    @patch.dict(os.environ, {"HYPOTHESIS_AS_FACT_GATE_ENABLED": "true"})
    def test_fail_open_on_errors(self, mock_load_events, mock_extract):
        """Test that gate fails open on extraction errors."""
        # Mock extract_claims to raise exception
        mock_extract.side_effect = Exception("Extraction error")

        data = {
            "session_id": "test-session-id",
            "terminal_id": "test-terminal-id",
            "response_text": "Package has no skill/ directory",
        }

        result = run(data)
        assert result.get("allow") is True, "Gate should fail open on errors"
        assert "error" in result.get("reason", "").lower()


class TestTerminalScoping(unittest.TestCase):
    """Test terminal-scoped isolation (Phase 1).

    SCOPING NOTE: Phase 1 gate is terminal-scoped, not turn-scoped.
    These tests verify terminal isolation only.

    NOTE: Phase 2 refactor replaced HypothesisAsFactDetector with verification module.
    """

    @patch("Stop_hypothesis_as_fact_gate.build_verdicts")
    @patch("Stop_hypothesis_as_fact_gate.extract_claims")
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    @patch.dict(
        os.environ,
        {
            "HYPOTHESIS_AS_FACT_GATE_ENABLED": "true",
            "HYPOTHESIS_AS_FACT_GATE_MODE": "block",
        },
    )
    def test_terminal_scoped_isolation(self, mock_load_events, mock_extract, mock_verdicts):
        """Test that terminal_id filters tool events correctly."""
        # Mock extract_claims to return claim
        mock_claim = Mock()
        mock_claim.text = "Package has no skill/ directory"
        mock_claim.targets = ["Package/skill/"]  # Note: targets, not subject_entity
        mock_claim.confidence = 0.8
        mock_claim.has_hedge = False
        mock_claim.type = "ABSENCE"
        mock_claim.id = "test-id-123"
        mock_claim.risk_domain = "FS_CRITICAL"

        mock_extract.return_value = [mock_claim]

        # Mock build_verdicts to return SILENT verdict (no evidence)
        from verification.engine import VerificationStatus

        mock_verdict = Mock()
        mock_verdict.status = VerificationStatus.SILENT
        # Add serializable attributes for JSON logging
        mock_verdict.claim_id = "test-claim-id"
        mock_verdict.supporting_evidence = []
        mock_verdict.refuting_evidence = []
        mock_verdict.confidence = 0.8
        mock_verdicts.return_value = [mock_verdict]

        # Mock load_tool_events_for_context to verify it's called with terminal_id
        mock_load_events.return_value = []  # No evidence in this terminal

        data = {
            "session_id": "test-session-id",
            "terminal_id": "terminal-abc123",  # Specific terminal
            "response_text": "Package has no skill/ directory",
        }

        result = run(data)

        # Verify load_tool_events_for_context was called with correct terminal_id
        mock_load_events.assert_called_once()
        call_args = mock_load_events.call_args
        assert call_args[1]["terminal_id"] == "terminal-abc123", "Should filter by terminal_id"
        assert call_args[1]["session_id"] == "test-session-id", "Should filter by session_id"

        # Result should be block (no evidence in this terminal)
        assert result.get("allow") is False, "Should block without evidence in this terminal"


class TestMakeRealClaimFixture(unittest.TestCase):
    """Verify the make_real_claim conftest fixture exercises the real claims.py pipeline.

    These tests document the cross-module contract at the claims.py boundary:
      - .type is uppercased by _raw_claim_to_claim() in claims.py
      - .confidence includes hedge penalty (-0.2) from _calculate_confidence()

    If these tests fail, check:
      1. verification/claims.py _raw_claim_to_claim() — still uppercases .type?
      2. hypothesis_as_fact_detector.py _calculate_confidence() — still applies hedge penalty?
    """

    FABRICATION_TEXT = "hooks typically go undocumented"

    def _get_real_claim(self, text: str):
        """Build a real Claim via the full extract_claims() pipeline (no mocks)."""
        import sys
        from pathlib import Path

        hooks_dir = Path(__file__).resolve().parent.parent
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))
        from verification import extract_claims

        claims = extract_claims(text)
        self.assertTrue(claims, f"extract_claims produced no claims for: {text!r}")
        return claims[0]

    def test_make_real_claim_returns_convention_type_uppercase(self):
        """Pipeline returns Claim with type == CONVENTION (uppercase from claims.py)."""
        claim = self._get_real_claim(self.FABRICATION_TEXT)
        self.assertEqual(
            claim.type,
            "CONVENTION",
            f"Expected type='CONVENTION' (uppercase from claims.py pipeline), got {claim.type!r}. "
            "Check _raw_claim_to_claim() in verification/claims.py",
        )

    def test_make_real_claim_has_hedge_true(self):
        """Pipeline returns Claim with has_hedge=True for fabrication phrase with 'typically'."""
        claim = self._get_real_claim(self.FABRICATION_TEXT)
        self.assertTrue(
            claim.has_hedge,
            f"Expected has_hedge=True for '{self.FABRICATION_TEXT}', got {claim.has_hedge!r}. "
            "Check HEDGE_WORDS in hypothesis_as_fact_detector.py includes 'typically'",
        )


class TestConventionGateEndToEnd(unittest.TestCase):
    """Integration-boundary tests: fabrication text → extract_claims() → gate.run() → blocked.

    These tests use the REAL extract_claims() pipeline (not mocks of Claim fields).
    Only load_tool_events_for_context and build_verdicts are mocked (I/O boundary).

    WHY THIS CLASS EXISTS:
    Both bugs that slipped through during the original CONVENTION implementation
    were invisible to mock-based unit tests:
      - Bug 1: gate checked claim.type == "convention" but real Claim.type is "CONVENTION"
               (mock set .type directly, bypassing claims.py uppercasing)
      - Bug 2: gate checked confidence < 0.7 without CONVENTION exemption; real confidence
               is 0.5 for longer hedged text (mock set confidence=0.8, hiding the penalty)

    These tests exercise the full pipeline, making both bugs visible as RED tests.
    """

    FABRICATION_TEXT = "hooks typically go undocumented"

    def _make_silent_verdict(self, claims):
        """Build a list of SILENT verdicts (one per claim) for mocking build_verdicts."""
        from verification.engine import VerificationStatus, VerificationVerdict

        return [
            VerificationVerdict(
                claim_id=getattr(c, "id", f"claim-{i}"),
                status=VerificationStatus.SILENT,
                supporting_evidence=[],
                refuting_evidence=[],
                confidence=0.0,
            )
            for i, c in enumerate(claims)
        ]

    @patch("Stop_hypothesis_as_fact_gate.build_verdicts")
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    @patch.dict(
        os.environ,
        {
            "HYPOTHESIS_AS_FACT_GATE_ENABLED": "true",
            "HYPOTHESIS_AS_FACT_GATE_MODE": "block",
        },
    )
    def test_convention_fabrication_blocked_end_to_end(self, mock_load_events, mock_build_verdicts):
        """Fabrication text reaches gate.run() and is BLOCKED (block mode).

        Uses real extract_claims() — no mock of Claim.type or Claim.confidence.
        This test would be RED if:
          - _should_block_claim() compared claim.type == "convention" (lowercase)
          - _should_block_claim() bypassed on confidence < 0.7 without is_convention guard
        """
        # Mock only I/O boundary — extract_claims() runs real
        mock_load_events.return_value = []

        # Build verdicts dynamically using real claims from extract_claims
        from verification import extract_claims

        real_claims = extract_claims(self.FABRICATION_TEXT)
        assert real_claims, f"extract_claims produced no claims for: {self.FABRICATION_TEXT!r}"
        mock_build_verdicts.return_value = self._make_silent_verdict(real_claims)

        data = {
            "session_id": "test-session-e2e",
            "terminal_id": "test-terminal-e2e",
            "response_text": self.FABRICATION_TEXT,
        }

        result = run(data)

        assert result.get("allow") is False, (
            f"Expected gate to BLOCK fabrication text in block mode, got allow={result.get('allow')!r}. "
            f"reason={result.get('reason')!r}. "
            "Check _should_block_claim() CONVENTION bypass exemption."
        )

    @patch("Stop_hypothesis_as_fact_gate.build_verdicts")
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    @patch.dict(
        os.environ,
        {
            "HYPOTHESIS_AS_FACT_GATE_ENABLED": "true",
            "HYPOTHESIS_AS_FACT_GATE_MODE": "warn",
        },
    )
    def test_convention_fabrication_warned_end_to_end(self, mock_load_events, mock_build_verdicts):
        """Fabrication text reaches gate.run() and issues WARNING (warn mode, allow=True).

        Uses real extract_claims() — no mock of Claim fields.
        Warn mode should allow the stop but issue a warning.
        """
        mock_load_events.return_value = []

        from verification import extract_claims

        real_claims = extract_claims(self.FABRICATION_TEXT)
        assert real_claims
        mock_build_verdicts.return_value = self._make_silent_verdict(real_claims)

        data = {
            "session_id": "test-session-e2e",
            "terminal_id": "test-terminal-e2e",
            "response_text": self.FABRICATION_TEXT,
        }

        result = run(data)

        assert result.get("allow") is True, (
            f"Expected gate to ALLOW in warn mode, got allow={result.get('allow')!r}. "
            f"reason={result.get('reason')!r}"
        )

    @patch("Stop_hypothesis_as_fact_gate.build_verdicts")
    @patch("Stop_hypothesis_as_fact_gate.load_tool_events_for_context")
    @patch.dict(
        os.environ,
        {
            "HYPOTHESIS_AS_FACT_GATE_ENABLED": "true",
            "HYPOTHESIS_AS_FACT_GATE_MODE": "block",
        },
    )
    def test_non_convention_hedged_claim_still_passes(self, mock_load_events, mock_build_verdicts):
        """Non-CONVENTION hedged claims still bypass the gate (regression check).

        The is_convention guard must NOT affect other claim types with hedge words.
        """
        from verification import extract_claims
        from verification.engine import VerificationStatus, VerificationVerdict

        mock_load_events.return_value = []
        # Use a hedged RULE-type phrase that does NOT match CONVENTION patterns
        hedged_rule_text = "The system might require additional configuration."
        real_claims = extract_claims(hedged_rule_text)

        if not real_claims:
            # If no claims extracted, gate returns "No claims detected" → allow
            mock_build_verdicts.return_value = []
        else:
            # All non-CONVENTION claims with hedge should pass via hedge bypass
            mock_build_verdicts.return_value = [
                VerificationVerdict(
                    status=VerificationStatus.SILENT,
                    supporting_evidence=[],
                    refuting_evidence=[],
                )
                for _ in real_claims
            ]

        data = {
            "session_id": "test-session-e2e",
            "terminal_id": "test-terminal-e2e",
            "response_text": hedged_rule_text,
        }

        result = run(data)

        assert result.get("allow") is True, (
            f"Expected hedged non-CONVENTION claim to PASS, got allow={result.get('allow')!r}. "
            "is_convention guard must not affect non-CONVENTION hedged claims."
        )


if __name__ == "__main__":
    unittest.main()
