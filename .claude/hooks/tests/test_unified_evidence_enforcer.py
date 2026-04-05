#!/usr/bin/env python3
r"""
Tests for Unified Evidence Enforcer (UEEA)

TDD RED Phase: These tests define desired behavior for the unified evidence enforcement.
Tests should FAIL before implementation, PASS after.

The UEEA consolidates all evidence gates into single validation pass:
- empirical_claims_gate.py (observation required)
- speculation_gate.py (speculative language)
- assumption_audit_v2.py (unverified assumptions)
- StopHook_investigation_required.py (diagnostic without investigation)

Test file: P:\.claude\hooks\tests\test_unified_evidence_enforcer.py
Module: P:\.claude\hooks\__lib\unified_evidence_enforcer.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks dir to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

# Import unified_evidence_enforcer at module level to avoid class-scoped import issues
import importlib.util

spec = importlib.util.spec_from_file_location(
    "unified_evidence_enforcer",
    HOOKS_DIR / "__lib" / "unified_evidence_enforcer.py"
)
ueea_module = importlib.util.module_from_spec(spec)
sys.modules["unified_evidence_enforcer"] = ueea_module
spec.loader.exec_module(ueea_module)


class TestClaimWithoutObservationBlocks:
    """Test that claims without observation tools block."""

    @pytest.fixture
    def ueea_module(self):
        """Return the pre-loaded module."""
        return ueea_module

    def test_claim_without_observation_blocks(self, ueea_module):
        """
        Test that claims about files/paths without observation block.

        Given: Response makes claims about files
        When: No observation tools were used
        Then: Response is blocked with OBSERVATION_REQUIRED
        """
        data = {
            "response": "The plan.md file shows X configuration. " * 10,  # Make it long enough (>200 chars)
            "tools_used": [],
            "terminal_id": "test-terminal"
        }

        result = ueea_module.check_response(data)

        assert result["allowed"] is False
        assert "OBSERVATION_REQUIRED" in result["blocks"]
        assert result["remediation"] is not None
        assert "observation" in result["remediation"].lower()

    def test_path_reference_without_observation_blocks(self, ueea_module):
        """
        Test that path references without observation block.

        Given: Response references Windows paths
        When: No Read/Grep/Glob/Bash tools were used
        Then: Response is blocked
        """
        data = {
            "response": "I'll update P:/test/config.json to fix the issue. " * 10,  # Make it long enough
            "tools_used": [],
            "terminal_id": "test-terminal"
        }

        result = ueea_module.check_response(data)

        assert result["allowed"] is False
        assert "OBSERVATION_REQUIRED" in result["blocks"]


class TestObservationPasses:
    """Test that responses with proper observation pass."""

    @pytest.fixture
    def ueea_module(self):
        """Return the pre-loaded module."""
        return ueea_module

    def test_observation_with_read_passes(self, ueea_module):
        """
        Test that Read tool usage allows claims.

        Given: Response makes claims about files
        When: Read tool was used
        Then: Response is allowed
        """
        data = {
            "response": "The plan file shows X configuration",
            "tools_used": ["Read"],
            "terminal_id": "test-terminal"
        }

        result = ueea_module.check_response(data)

        assert result["allowed"] is True
        assert result["blocks"] == []
        assert result["remediation"] is None

    def test_observation_with_grep_passes(self, ueea_module):
        """
        Test that Grep tool usage allows claims.

        Given: Response makes claims about code
        When: Grep tool was used
        Then: Response is allowed
        """
        data = {
            "response": "Found imports in the module",
            "tools_used": ["Grep"],
            "terminal_id": "test-terminal"
        }

        result = ueea_module.check_response(data)

        assert result["allowed"] is True

    @pytest.mark.parametrize("tool", ["Bash", "Glob", "View", "WebFetch"])
    def test_all_observation_tools_pass(self, ueea_module, tool):
        """
        Test that all observation tools allow claims.

        Given: Response makes claims
        When: Any observation tool was used
        Then: Response is allowed
        """
        data = {
            "response": "The configuration shows X",
            "tools_used": [tool],
            "terminal_id": "test-terminal"
        }

        result = ueea_module.check_response(data)

        assert result["allowed"] is True


class TestSpeculativeLanguageBlocks:
    """Test that speculative language in diagnostic mode blocks."""

    @pytest.fixture
    def ueea_module(self):
        """Return the pre-loaded module."""
        return ueea_module

    @pytest.mark.parametrize("phrase", [
        "appears to be",
        "likely the cause",
        "probably broken",
        "seems like an error",
        "would expect",
    ])
    def test_speculative_language_blocks(self, ueea_module, phrase):
        """
        Test that speculative language in diagnostic claims blocks.

        Given: Response contains speculative language about diagnosis
        When: Without proper evidence context
        Then: Response is blocked with SPECULATION_VIOLATION
        """
        data = {
            "response": f"The root cause {phrase} a race condition",
            "tools_used": [],
            "terminal_id": "test-terminal"
        }

        result = ueea_module.check_response(data)

        assert result["allowed"] is False
        assert "SPECULATION_VIOLATION" in result["blocks"]

    def test_speculative_with_observation_still_blocks(self, ueea_module):
        """
        Test that speculation blocks even with observation if not explicit.

        Given: Response has speculative diagnostic language
        When: Observation tools were used but speculation is unmarked
        Then: Response is blocked
        """
        data = {
            "response": "The root cause appears to be a race condition",
            "tools_used": ["Read"],
            "terminal_id": "test-terminal"
        }

        result = ueea_module.check_response(data)

        # Should block because "appears to be" is speculative
        assert result["allowed"] is False
        assert "SPECULATION_VIOLATION" in result["blocks"]


class TestGracePeriodWorks:
    """Test that grace period allows subsequent turns."""

    @pytest.fixture
    def temp_state_dir(self):
        """Create a temporary state directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def ueea_module_with_temp_state(self, temp_state_dir):
        """Import module with patched state directory."""
        # Patch STATE_DIR and STATE_FILE
        with patch.object(ueea_module, 'STATE_DIR', temp_state_dir):
            with patch.object(ueea_module, 'STATE_FILE', temp_state_dir / 'ueea_state.jsonl'):
                yield ueea_module

    def test_observation_recorded(self, ueea_module_with_temp_state):
        """
        Test that observation is recorded for grace period.

        Given: User makes observation
        When: check_response is called with observation tools
        Then: Observation is recorded in state file
        """
        data = {
            "response": "I'll read the file first",
            "tools_used": ["Read"],
            "terminal_id": "test-terminal"
        }

        result = ueea_module_with_temp_state.check_response(data)

        # Should pass
        assert result["allowed"] is True

        # Check state file was created
        state_file = ueea_module_with_temp_state.STATE_FILE
        assert state_file.exists()

        # Verify state was recorded
        content = state_file.read_text()
        assert "test-terminal" in content
        assert "Read" in content

    def test_grace_period_allows_next_turn(self, ueea_module_with_temp_state):
        """
        Test that grace period allows next turn without new observation.

        Given: Previous turn had observation
        When: Current turn has no new observation but references same terminal
        Then: Response is allowed via grace period
        """
        terminal_id = "grace-test-terminal"

        # First turn: observation
        data1 = {
            "response": "I'll read the file first",
            "tools_used": ["Read"],
            "terminal_id": terminal_id
        }
        result1 = ueea_module_with_temp_state.check_response(data1)
        assert result1["allowed"] is True

        # Second turn: no new observation, but making claim
        data2 = {
            "response": "The file shows the configuration is correct",
            "tools_used": [],  # No new observation
            "terminal_id": terminal_id
        }

        # Check grace first
        has_grace = ueea_module_with_temp_state.check_grace(terminal_id)
        assert has_grace is True

        # Should pass due to grace
        result2 = ueea_module_with_temp_state.check_response(data2)
        assert result2["allowed"] is True

    def test_grace_period_terminal_isolation(self, ueea_module_with_temp_state):
        """
        Test that grace period is terminal-specific.

        Given: Terminal A has observation
        When: Terminal B checks grace without observation
        Then: Terminal B does not get grace
        """
        terminal_a = "terminal-A"
        terminal_b = "terminal-B"

        # Terminal A makes observation
        data_a = {
            "response": "Reading file",
            "tools_used": ["Read"],
            "terminal_id": terminal_a
        }
        ueea_module_with_temp_state.check_response(data_a)

        # Terminal B checks grace
        has_grace_b = ueea_module_with_temp_state.check_grace(terminal_b)
        assert has_grace_b is False

        # Terminal A has grace
        has_grace_a = ueea_module_with_temp_state.check_grace(terminal_a)
        assert has_grace_a is True


class TestMtimeBasedGrace:
    """Test mtime-based cross-turn evidence validity."""

    @pytest.fixture
    def temp_state_dir(self):
        """Create a temporary state directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def ueea_with_temp(self, temp_state_dir):
        """Import module with patched state directory."""
        with patch.object(ueea_module, 'STATE_DIR', temp_state_dir):
            with patch.object(ueea_module, 'STATE_FILE', temp_state_dir / 'ueea_state.jsonl'):
                # Reset cache
                ueea_module._grace_cache["data"] = None
                ueea_module._grace_cache["timestamp"] = 0
                yield ueea_module

    def test_grace_valid_when_files_unchanged(self, ueea_with_temp, tmp_path):
        """Grace holds when observed files haven't been modified."""
        # Create a file to reference
        test_file = tmp_path / "observed.py"
        test_file.write_text("x = 1\n")
        terminal = "mtime-test-1"

        # Observation turn references the file
        data1 = {
            "response": f"Reading {test_file} shows x = 1",
            "tools_used": ["Read"],
            "terminal_id": terminal
        }
        ueea_with_temp.check_response(data1)

        # Reset cache to force re-read
        ueea_with_temp._grace_cache["data"] = None
        ueea_with_temp._grace_cache["timestamp"] = 0

        # Next turn: file unchanged, grace should hold
        assert ueea_with_temp.check_grace(terminal) is True

    def test_grace_invalid_when_file_modified(self, ueea_with_temp, tmp_path):
        """Grace revoked when an observed file's content has changed."""
        test_file = tmp_path / "observed.py"
        test_file.write_text("x = 1\n")
        terminal = "mtime-test-2"

        # Observation turn
        data1 = {
            "response": f"Reading {test_file} shows x = 1",
            "tools_used": ["Read"],
            "terminal_id": terminal
        }
        ueea_with_temp.check_response(data1)

        # Modify the file content (hash changes)
        test_file.write_text("x = 2\n")

        # Reset cache
        ueea_with_temp._grace_cache["data"] = None
        ueea_with_temp._grace_cache["timestamp"] = 0

        # Grace should be revoked because content hash differs
        assert ueea_with_temp.check_grace(terminal) is False

    def test_grace_terminal_isolation_with_mtime(self, ueea_with_temp, tmp_path):
        """Terminal A's observation doesn't grant grace to Terminal B."""
        test_file = tmp_path / "shared.py"
        test_file.write_text("shared = True\n")

        # Terminal A observes
        data_a = {
            "response": f"File {test_file} has shared = True",
            "tools_used": ["Read"],
            "terminal_id": "term-A"
        }
        ueea_with_temp.check_response(data_a)

        # Reset cache
        ueea_with_temp._grace_cache["data"] = None
        ueea_with_temp._grace_cache["timestamp"] = 0

        # Terminal B should NOT have grace
        assert ueea_with_temp.check_grace("term-B") is False
        # Terminal A should have grace
        ueea_with_temp._grace_cache["data"] = None
        ueea_with_temp._grace_cache["timestamp"] = 0
        assert ueea_with_temp.check_grace("term-A") is True

    def test_observation_records_file_hashes(self, ueea_with_temp, tmp_path):
        """Observation record includes observed_files with content hashes."""
        test_file = tmp_path / "tracked.py"
        test_file.write_text("y = 42\n")
        terminal = "hash-test-record"

        data = {
            "response": f"File at {test_file} contains y = 42",
            "tools_used": ["Read"],
            "terminal_id": terminal
        }
        ueea_with_temp.check_response(data)

        # Read state file and verify observed_files contains hash strings
        state_file = ueea_with_temp.STATE_FILE
        content = state_file.read_text()
        import json as _json
        record = _json.loads(content.strip().split("\n")[-1])
        assert "observed_files" in record
        assert len(record["observed_files"]) > 0
        # Values should be hex hash strings, not floats (not mtime)
        for val in record["observed_files"].values():
            assert isinstance(val, str)
            assert len(val) == 16  # SHA-256 truncated to 16 hex chars

    def test_grace_valid_when_no_file_paths_in_response(self, ueea_with_temp):
        """Grace valid when observation had no file paths (no mtime to check)."""
        terminal = "mtime-test-nofiles"

        data = {
            "response": "I checked the configuration and it works",
            "tools_used": ["Bash"],
            "terminal_id": terminal
        }
        ueea_with_temp.check_response(data)

        ueea_with_temp._grace_cache["data"] = None
        ueea_with_temp._grace_cache["timestamp"] = 0

        assert ueea_with_temp.check_grace(terminal) is True


class TestUnifiedEvidenceFields:
    """Test unified evidence format."""

    @pytest.fixture
    def ueea_module(self):
        """Return the pre-loaded module."""
        return ueea_module

    def test_evidence_fields_defined(self, ueea_module):
        """
        Test that unified evidence fields are defined.

        Given: Module is loaded
        When: Checking EVIDENCE_FIELDS constant
        Then: All required fields are present
        """
        expected_fields = {"observed_via", "observed_at", "evidence_type", "source_file", "claim_excerpt"}
        actual_fields = set(ueea_module.EVIDENCE_FIELDS)

        assert actual_fields == expected_fields

    def test_observation_tools_defined(self, ueea_module):
        """
        Test that observation tools are defined.

        Given: Module is loaded
        When: Checking OBSERVATION_TOOLS constant
        Then: All required tools are present
        """
        expected_tools = {"Read", "Grep", "Glob", "Bash", "View", "WebFetch"}
        actual_tools = set(ueea_module.OBSERVATION_TOOLS)

        assert actual_tools == expected_tools


class TestSpeculativePatterns:
    """Test speculative language pattern detection."""

    @pytest.fixture
    def ueea_module(self):
        """Return the pre-loaded module."""
        return ueea_module

    def test_speculative_patterns_defined(self, ueea_module):
        """
        Test that speculative patterns are defined.

        Given: Module is loaded
        When: Checking SPECULATIVE_PATTERNS constant
        Then: Required patterns are present
        """
        required_patterns = [
            r"\bappears to be\b",
            r"\blikely\b",
            r"\bprobably\b",
            r"\bseems like\b",
            r"\bwould expect\b"
        ]

        for pattern in required_patterns:
            assert pattern in ueea_module.SPECULATIVE_PATTERNS


class TestUnverifiedAssumptions:
    """Test unverified assumption detection."""

    @pytest.fixture
    def ueea_module(self):
        """Return the pre-loaded module."""
        return ueea_module

    @pytest.mark.parametrize("phrase", [
        "assuming that the file exists",
        "presuming this works",
        "assuming the configuration is correct",
    ])
    def test_unverified_assumptions_block(self, ueea_module, phrase):
        """
        Test that unverified assumptions block.

        Given: Response contains assumption language
        When: Without verification
        Then: Response is blocked with ASSUMPTION_WITHOUT_EVIDENCE
        """
        data = {
            "response": phrase,
            "tools_used": [],
            "terminal_id": "test-terminal"
        }

        result = ueea_module.check_response(data)

        assert result["allowed"] is False
        assert "ASSUMPTION_WITHOUT_EVIDENCE" in result["blocks"]


class TestReturnFormat:
    """Test that return format matches specification."""

    @pytest.fixture
    def ueea_module(self):
        """Return the pre-loaded module."""
        return ueea_module

    def test_return_format_allowed(self, ueea_module):
        """
        Test return format for allowed response.

        Given: Response passes validation
        When: check_response returns
        Then: Return dict has correct structure
        """
        data = {
            "response": "Just a question?",
            "tools_used": [],
            "terminal_id": "test-terminal"
        }

        result = ueea_module.check_response(data)

        # Check required keys
        assert "allowed" in result
        assert "blocks" in result
        assert "remediation" in result

        # Check types
        assert isinstance(result["allowed"], bool)
        assert isinstance(result["blocks"], list)
        assert result["remediation"] is None or isinstance(result["remediation"], str)

    def test_return_format_blocked(self, ueea_module):
        """
        Test return format for blocked response.

        Given: Response fails validation
        When: check_response returns
        Then: Return dict has correct structure with remediation
        """
        data = {
            "response": "The file at P:/test.py shows the bug. " * 10,  # Make it long enough
            "tools_used": [],
            "terminal_id": "test-terminal"
        }

        result = ueea_module.check_response(data)

        # Check required keys
        assert "allowed" in result
        assert "blocks" in result
        assert "remediation" in result

        # Check values
        assert result["allowed"] is False
        assert len(result["blocks"]) > 0
        assert isinstance(result["remediation"], str)
        assert len(result["remediation"]) > 0


class TestStateFileLocation:
    """Test state file location."""

    @pytest.fixture
    def ueea_module(self):
        """Return the pre-loaded module."""
        return ueea_module

    def test_state_dir_location(self, ueea_module):
        """
        Test that STATE_DIR points to correct location.

        Given: Module is loaded
        When: Checking STATE_DIR constant
        Then: Points to hooks/state directory
        """
        expected_path = HOOKS_DIR / "state"
        assert ueea_module.STATE_DIR == expected_path

    def test_state_file_name(self, ueea_module):
        """
        Test that STATE_FILE has correct name.

        Given: Module is loaded
        When: Checking STATE_FILE constant
        Then: File is named ueea_state.jsonl
        """
        assert ueea_module.STATE_FILE.name == "ueea_state.jsonl"
        assert ueea_module.STATE_FILE.parent == ueea_module.STATE_DIR
