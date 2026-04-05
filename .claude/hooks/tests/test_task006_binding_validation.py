#!/usr/bin/env python3
"""
test_task006_binding_validation.py - Tests for TASK-006 Semantic Binding Validation

Tests for TASK-006 semantic binding validation in StopHook_rca_contract.py.
Verifies:
1. Wrong-file evidence blocks - Evidence claims about files not actually read
2. Missing evidence binding blocks - Evidence claims without bindings to tool events
3. Cross-terminal evidence reuse blocks - Evidence from different terminal sessions
4. Stale binding blocks - Bindings marked stale due to mutations
5. Evidence without tool events blocks - Evidence without corresponding tool execution

Acceptance Criteria:
- Wrong-file evidence blocks when artifact path has no binding
- Missing evidence binding blocks when Evidence section has no bindings
- Cross-terminal evidence reuse blocks when binding from different terminal
- Stale binding blocks when binding marked stale
- Evidence without tool events blocks when no tool executed
"""

import sys
from pathlib import Path

# Add hooks dir to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import pytest

# Import evidence_store functions
from evidence_store import (
    create_epistemic_binding,
    init_db,
    load_epistemic_bindings,
    mark_binding_stale,
    write_epistemic_commitment,
)

# Import the module under test
from StopHook_rca_contract import (
    _extract_artifact_paths,
    _validate_evidence_bindings,
    check,
)

# --- Fixtures ---------------------------------------------------------------


@pytest.fixture
def session_data():
    """Test session and terminal IDs."""
    return {
        "session_id": "01234567-89ab-cdef-0123-456789012345",  # UUID-like format (36 chars, hex + hyphens)
        "terminal_id": "test-terminal-xyz789",
    }


@pytest.fixture
def other_session_data():
    """Different session/terminal for cross-terminal tests."""
    return {
        "session_id": "abcdef01-2345-6789-abcd-ef0123456789",  # UUID-like format (36 chars, hex + hyphens)
        "terminal_id": "other-terminal-uvw012",
    }


@pytest.fixture
def rca_response_with_evidence():
    """Sample RCA response with Evidence section."""
    return """
## Symptom
The system crashed with a KeyError.

## Evidence
Read on `config.json` showed missing key 'timeout' (current-state).
Read on `settings.py` showed the function calls dict.get() (current-state).

## Executed Path
config.py:42 - calls dict.get() on config object

## Alternative Hypothesis
The config file is missing the timeout key.

## Falsifier
Adding timeout key to config.json does not fix the crash.

## Root Cause
config.py:42 - Missing null check before dict.get()

## Fix
Add null check: if config and 'timeout' in config:

## Verification
Run pytest tests/test_config.py - all tests pass.
"""


@pytest.fixture
def rca_response_wrong_file():
    """RCA response claiming evidence from file not actually read."""
    return """
## Symptom
The system crashed.

## Evidence
Read on `mystery.py` showed the bug is in the handler function.

## Root Cause
mystery.py:42 - unhandled exception

## Fix
Add exception handler
"""


@pytest.fixture
def tool_events_read():
    """Tool events with Read tool execution."""
    return [
        {
            "id": "tool-123",  # Required for validation
            "name": "Read",
            "tool_name": "Read",
            "command": "config.json",
            "cwd": "/path/to/project",
            "output_excerpt": "Content of config.json",
            "session_id": "test-session-abc123def456789012345678901234",
            "terminal_id": "test-terminal-xyz789",
        }
    ]


# --- Artifact Path Extraction Tests --------------------------------------


class TestArtifactPathExtraction:
    """Tests for _extract_artifact_paths() function."""

    def test_extract_backtick_paths(self):
        """Extract file paths from backtick notation."""
        evidence_text = "Read on `config.json` showed the issue."
        paths = _extract_artifact_paths(evidence_text)
        assert "config.json" in paths

    def test_extract_quote_paths(self):
        """Extract file paths from quote notation."""
        evidence_text = 'Read on "settings.py" showed the function.'
        paths = _extract_artifact_paths(evidence_text)
        assert "settings.py" in paths

    def test_extract_multiple_paths(self):
        """Extract multiple file paths from evidence text."""
        evidence_text = """
        Read on `config.json` showed missing key.
        Read on `settings.py` showed the function call.
        Grep found pattern in `main.py`.
        """
        paths = _extract_artifact_paths(evidence_text)
        assert "config.json" in paths
        assert "settings.py" in paths
        assert "main.py" in paths

    def test_extract_windows_paths(self):
        """Extract Windows-style file paths."""
        evidence_text = "Read on `C:\\\\Users\\\\test\\\\file.py` showed content."
        paths = _extract_artifact_paths(evidence_text)
        assert len(paths) > 0
        # Should normalize to forward slashes
        assert any("file.py" in p for p in paths)

    def test_no_paths_in_text(self):
        """Return empty list when no paths found."""
        evidence_text = "The system crashed with a KeyError."
        paths = _extract_artifact_paths(evidence_text)
        assert paths == []


# --- Semantic Binding Validation Tests --------------------------------------


class TestSemanticBindingValidation:
    """Tests for _validate_evidence_bindings() function."""

    def test_no_evidence_section_skips_validation(self, rca_response_with_evidence):
        """Missing Evidence section should skip binding validation."""
        response_no_evidence = rca_response_with_evidence.replace(
            "## Evidence\n", "## Evidence Section Removed\n"
        )
        sections = {"Symptom": "The system crashed."}

        block_reasons = _validate_evidence_bindings(sections, [], "session-123", "terminal-abc")
        assert block_reasons == []  # No evidence section, no validation

    def test_evidence_without_current_state_indicators_skips(self, rca_response_with_evidence):
        """Evidence without current-state indicators should skip binding validation."""
        response_no_indicators = """
## Evidence
The system crashed.
Read on config.json showed missing key.
"""
        sections = {"Evidence": response_no_indicators}

        block_reasons = _validate_evidence_bindings(sections, [], "session-123", "terminal-abc")
        assert block_reasons == []  # No current-state indicators, skip validation

    def test_empty_evidence_section_allows(self):
        """Empty Evidence section should allow (no validation needed)."""
        sections = {"Evidence": ""}

        block_reasons = _validate_evidence_bindings(sections, [], "session-123", "terminal-abc")
        assert block_reasons == []  # Empty evidence, no blocks

    def test_no_artifact_paths_allows(self):
        """Evidence text without artifact paths should allow."""
        sections = {"Evidence": "The system crashed with a KeyError (current-state)."}

        block_reasons = _validate_evidence_bindings(sections, [], "session-123", "terminal-abc")
        assert block_reasons == []  # No artifact paths, no blocks


# --- Wrong-File Evidence Blocking Tests -------------------------------------


class TestWrongFileEvidenceBlocking:
    """Tests for wrong-file evidence blocking (TASK-006 acceptance criterion 1)."""

    def test_unbound_artifact_blocks(self, session_data):
        """Artifact path in Evidence without binding should block."""
        sections = {"Evidence": "Read on `config.json` showed missing key (current-state)."}

        # Mock load_epistemic_bindings to return empty (no bindings)
        def mock_load_bindings(
            commitment_id=None, session_id=None, terminal_id=None, include_stale=False
        ):
            return []  # No bindings found

        # Temporarily replace the function
        import StopHook_rca_contract as rca_module

        original_load = rca_module.load_epistemic_bindings
        rca_module.load_epistemic_commitments = lambda *args, **kwargs: {}
        rca_module.load_epistemic_bindings = mock_load_bindings

        try:
            # Provide tool_events to avoid early return (evidence-without-tool-events)
            tool_events = [{"id": "tool-123", "name": "Read"}]
            block_reasons = _validate_evidence_bindings(
                sections,
                tool_events,
                session_data["session_id"],
                session_data["terminal_id"],
            )
            assert len(block_reasons) > 0
            assert any("unbound-evidence" in r for r in block_reasons)
        finally:
            # Restore original
            rca_module.load_epistemic_bindings = original_load
            if hasattr(rca_module, "load_epistemic_commitments"):
                delattr(rca_module, "load_epistemic_commitments")

    def test_bound_artifact_allows(self, session_data):
        """Artifact path with valid binding should allow."""
        sections = {"Evidence": "Read on `config.json` showed missing key (current-state)."}

        # Mock load_epistemic_bindings to return binding
        def mock_load_bindings(
            commitment_id=None, session_id=None, terminal_id=None, include_stale=False
        ):
            return [
                {
                    "artifact_path": "config.json",
                    "tool_event_id": "tool-123",
                    "session_id": session_data["session_id"],
                    "terminal_id": session_data["terminal_id"],
                    "stale": 0,
                }
            ]

        # Temporarily replace the function
        import StopHook_rca_contract as rca_module

        original_load = rca_module.load_epistemic_bindings
        rca_module.load_epistemic_commitments = lambda *args, **kwargs: {}
        rca_module.load_epistemic_bindings = mock_load_bindings

        try:
            # Provide tool_events to avoid early return (evidence-without-tool-events)
            tool_events = [{"id": "tool-123", "name": "Read"}]
            block_reasons = _validate_evidence_bindings(
                sections,
                tool_events,
                session_data["session_id"],
                session_data["terminal_id"],
            )
            assert block_reasons == []  # No blocks - binding exists
        finally:
            rca_module.load_epistemic_bindings = original_load
            if hasattr(rca_module, "load_epistemic_commitments"):
                delattr(rca_module, "load_epistemic_commitments")


# --- Cross-Terminal Evidence Reuse Blocking Tests -------------------------


class TestCrossTerminalEvidenceReuseBlocking:
    """Tests for cross-terminal evidence reuse blocking (TASK-006 acceptance criterion 3)."""

    def test_cross_terminal_binding_blocks(self, session_data, other_session_data):
        """Binding from different terminal should block."""
        sections = {"Evidence": "Read on `config.json` showed missing key (current-state)."}

        # Mock load_epistemic_bindings to return binding from different terminal
        # Note: Actual call is load_epistemic_bindings(session_id, terminal_id)
        def mock_load_bindings(session_id, terminal_id, **kwargs):
            return [
                {
                    "artifact_path": "config.json",
                    "tool_event_id": "tool-123",
                    "session_id": other_session_data["session_id"],  # Different session
                    "terminal_id": other_session_data["terminal_id"],  # Different terminal
                    "stale": 0,
                }
            ]

        # Temporarily replace the function
        import StopHook_rca_contract as rca_module

        original_load = rca_module.load_epistemic_bindings
        rca_module.load_epistemic_commitments = lambda *args, **kwargs: {}
        rca_module.load_epistemic_bindings = mock_load_bindings

        try:
            # Provide tool_events that include the binding's tool_event_id
            # (to avoid "evidence-without-tool-events" block)
            tool_events = [{"id": "tool-123", "name": "Read"}]
            block_reasons = _validate_evidence_bindings(
                sections,
                tool_events,
                session_data["session_id"],  # Current session
                session_data["terminal_id"],  # Current terminal
            )
            assert len(block_reasons) > 0
            assert any("cross-terminal-evidence" in r for r in block_reasons)
        finally:
            rca_module.load_epistemic_bindings = original_load
            if hasattr(rca_module, "load_epistemic_commitments"):
                delattr(rca_module, "load_epistemic_commitments")

    def test_same_terminal_binding_allows(self, session_data):
        """Binding from same terminal should allow."""
        sections = {"Evidence": "Read on `config.json` showed missing key (current-state)."}

        # Mock load_epistemic_bindings to return binding from same terminal
        # Note: Actual call is load_epistemic_bindings(session_id, terminal_id)
        def mock_load_bindings(session_id, terminal_id, **kwargs):
            return [
                {
                    "artifact_path": "config.json",
                    "tool_event_id": "tool-123",
                    "session_id": session_data["session_id"],
                    "terminal_id": session_data["terminal_id"],
                    "stale": 0,
                }
            ]

        # Temporarily replace the function
        import StopHook_rca_contract as rca_module

        original_load = rca_module.load_epistemic_bindings
        rca_module.load_epistemic_commitments = lambda *args, **kwargs: {}
        rca_module.load_epistemic_bindings = mock_load_bindings

        try:
            # Provide tool_events that include the binding's tool_event_id
            tool_events = [{"id": "tool-123", "name": "Read"}]
            block_reasons = _validate_evidence_bindings(
                sections,
                tool_events,
                session_data["session_id"],
                session_data["terminal_id"],
            )
            assert block_reasons == []  # No blocks - same terminal
        finally:
            rca_module.load_epistemic_bindings = original_load
            if hasattr(rca_module, "load_epistemic_commitments"):
                delattr(rca_module, "load_epistemic_commitments")


# --- Stale Binding Blocking Tests ----------------------------------------


class TestStaleBindingBlocking:
    """Tests for stale binding blocking (TASK-006 acceptance criterion 4)."""

    def test_stale_binding_blocks(self, session_data):
        """Binding marked as stale should block."""
        sections = {"Evidence": "Read on `config.json` showed missing key (current-state)."}

        # Mock load_epistemic_bindings to return stale binding
        # Note: Actual call is load_epistemic_bindings(session_id, terminal_id)
        def mock_load_bindings(session_id, terminal_id, **kwargs):
            return [
                {
                    "artifact_path": "config.json",
                    "tool_event_id": "tool-123",
                    "session_id": session_data["session_id"],
                    "terminal_id": session_data["terminal_id"],
                    "is_stale": 1,  # Marked stale (note: is_stale, not stale)
                }
            ]

        # Temporarily replace the function
        import StopHook_rca_contract as rca_module

        original_load = rca_module.load_epistemic_bindings
        rca_module.load_epistemic_commitments = lambda *args, **kwargs: {}
        rca_module.load_epistemic_bindings = mock_load_bindings

        try:
            # Provide tool_events that include the binding's tool_event_id
            tool_events = [{"id": "tool-123", "name": "Read"}]
            block_reasons = _validate_evidence_bindings(
                sections,
                tool_events,
                session_data["session_id"],
                session_data["terminal_id"],
            )
            assert len(block_reasons) > 0
            assert any("stale-binding" in r for r in block_reasons)
        finally:
            rca_module.load_epistemic_bindings = original_load
            if hasattr(rca_module, "load_epistemic_commitments"):
                delattr(rca_module, "load_epistemic_commitments")

    def test_fresh_binding_allows(self, session_data):
        """Fresh binding (is_stale=0) should allow."""
        sections = {"Evidence": "Read on `config.json` showed missing key (current-state)."}

        # Mock load_epistemic_bindings to return fresh binding
        # Note: Actual call is load_epistemic_bindings(session_id, terminal_id)
        def mock_load_bindings(session_id, terminal_id, **kwargs):
            return [
                {
                    "artifact_path": "config.json",
                    "tool_event_id": "tool-123",
                    "session_id": session_data["session_id"],
                    "terminal_id": session_data["terminal_id"],
                    "is_stale": 0,  # Fresh (note: is_stale, not stale)
                }
            ]

        # Temporarily replace the function
        import StopHook_rca_contract as rca_module

        original_load = rca_module.load_epistemic_bindings
        rca_module.load_epistemic_commitments = lambda *args, **kwargs: {}
        rca_module.load_epistemic_bindings = mock_load_bindings

        try:
            # Provide tool_events that include the binding's tool_event_id
            tool_events = [{"id": "tool-123", "name": "Read"}]
            block_reasons = _validate_evidence_bindings(
                sections,
                tool_events,
                session_data["session_id"],
                session_data["terminal_id"],
            )
            assert block_reasons == []  # No blocks - fresh binding
        finally:
            rca_module.load_epistemic_bindings = original_load
            if hasattr(rca_module, "load_epistemic_commitments"):
                delattr(rca_module, "load_epistemic_commitments")


# --- Evidence Without Tool Events Blocking Tests ----------------------------


class TestEvidenceWithoutToolEventsBlocking:
    """Tests for evidence without tool events blocking (TASK-006 acceptance criterion 5)."""

    def test_evidence_without_tool_events_blocks(self, session_data):
        """Evidence with binding but no tool events should block."""
        sections = {"Evidence": "Read on `config.json` showed missing key (current-state)."}

        # Mock load_epistemic_bindings to return binding
        def mock_load_bindings(
            commitment_id=None, session_id=None, terminal_id=None, include_stale=False
        ):
            return [
                {
                    "artifact_path": "config.json",
                    "tool_event_id": "tool-123",
                    "session_id": session_data["session_id"],
                    "terminal_id": session_data["terminal_id"],
                    "stale": 0,
                }
            ]

        # Temporarily replace the function
        import StopHook_rca_contract as rca_module

        original_load = rca_module.load_epistemic_bindings
        rca_module.load_epistemic_commitments = lambda *args, **kwargs: {}
        rca_module.load_epistemic_bindings = mock_load_bindings

        try:
            # Pass empty tool_events list - no tools executed this turn
            block_reasons = _validate_evidence_bindings(
                sections,
                [],  # No tool events
                session_data["session_id"],
                session_data["terminal_id"],
            )
            assert len(block_reasons) > 0
            assert any("evidence-without-tool-events" in r for r in block_reasons)
        finally:
            rca_module.load_epistemic_bindings = original_load
            if hasattr(rca_module, "load_epistemic_commitments"):
                delattr(rca_module, "load_epistemic_commitments")

    def test_evidence_with_tool_events_allows(self, session_data, tool_events_read):
        """Evidence with binding and tool events should allow."""
        sections = {"Evidence": "Read on `config.json` showed missing key (current-state)."}

        # Mock load_epistemic_bindings to return binding
        def mock_load_bindings(
            commitment_id=None, session_id=None, terminal_id=None, include_stale=False
        ):
            return [
                {
                    "artifact_path": "config.json",
                    "tool_event_id": "tool-123",
                    "session_id": session_data["session_id"],
                    "terminal_id": session_data["terminal_id"],
                    "stale": 0,
                }
            ]

        # Temporarily replace the function
        import StopHook_rca_contract as rca_module

        original_load = rca_module.load_epistemic_bindings
        rca_module.load_epistemic_commitments = lambda *args, **kwargs: {}
        rca_module.load_epistemic_bindings = mock_load_bindings

        try:
            # Pass tool_events with Read tool
            block_reasons = _validate_evidence_bindings(
                sections,
                tool_events_read,  # Tool events present
                session_data["session_id"],
                session_data["terminal_id"],
            )
            assert block_reasons == []  # No blocks - tool events exist
        finally:
            rca_module.load_epistemic_bindings = original_load
            if hasattr(rca_module, "load_epistemic_commitments"):
                delattr(rca_module, "load_epistemic_commitments")


# --- Integration Tests ---------------------------------------------------


class TestBindingValidationIntegration:
    """Integration tests for complete binding validation workflow."""

    def test_full_validation_passes_with_valid_binding(self, session_data, tool_events_read):
        """Complete validation should pass with valid binding."""
        data = {
            "assistant_response": """
## Symptom
The system crashed.

## Evidence
Read on `config.json` showed missing key (current-state).

## Executed Path
1. Read config.json
2. Read config.py

## Alternative Hypothesis
Maybe the crash is due to memory leak.

## Falsifier
Memory profiling shows normal usage.

## Root Cause
config.py:42 - missing key causes crash.

## Fix
Add default key to config.py:42.

## Verification
Run system test to verify fix.
""",
            "response": "",
            "session_id": session_data["session_id"],
            "terminal_id": session_data["terminal_id"],
            "skill_state": {"skill": "debugrca", "loaded_at": 1234567890.0},
            "rca_turn": True,
            "tool_events": tool_events_read,
        }

        # Mock load_epistemic_bindings to return valid binding
        def mock_load_bindings(session_id, turn_id, commitment_id, tool_event_id, binding_kind):
            return [
                {
                    "artifact_path": "config.json",
                    "tool_event_id": "tool-123",
                    "session_id": session_data["session_id"],
                    "terminal_id": session_data["terminal_id"],
                    "stale": 0,
                }
            ]

        # Temporarily replace the function
        import StopHook_rca_contract as rca_module

        original_load = rca_module.load_epistemic_bindings
        rca_module.load_epistemic_commitments = lambda *args, **kwargs: {}
        rca_module.load_epistemic_bindings = mock_load_bindings

        try:
            result = check(data)
            assert result is None  # None = allow
        finally:
            rca_module.load_epistemic_bindings = original_load
            if hasattr(rca_module, "load_epistemic_commitments"):
                delattr(rca_module, "load_epistemic_commitments")

    def test_full_validation_blocks_with_unbound_evidence(self, session_data):
        """Complete validation should block with unbound evidence."""
        data = {
            "assistant_response": """
## Symptom
The system crashed.

## Evidence
Read on `mystery.py` showed the bug (current-state).

## Executed Path
1. Read mystery.py

## Alternative Hypothesis
Maybe the crash is due to memory leak.

## Falsifier
Memory profiling shows normal usage.

## Root Cause
mystery.py:42 - line causes crash.

## Fix
Add error handling to mystery.py:42.

## Verification
Run unit test to verify fix.
""",
            "response": "",
            "session_id": session_data["session_id"],
            "terminal_id": session_data["terminal_id"],
            "skill_state": {"skill": "debugrca", "loaded_at": 1234567890.0},
            "rca_turn": True,
            "tool_events": [],  # No tools executed
        }

        # Mock load_epistemic_bindings to return empty
        def mock_load_bindings(session_id, turn_id, commitment_id, tool_event_id, binding_kind):
            return []  # No bindings

        # Temporarily replace the function
        import StopHook_rca_contract as rca_module

        original_load = rca_module.load_epistemic_bindings
        rca_module.load_epistemic_commitments = lambda *args, **kwargs: {}
        rca_module.load_epistemic_bindings = mock_load_bindings

        try:
            result = check(data)
            assert result is not None
            assert result.get("decision") == "block"
            # Check for the actual block reason message format
            block_reasons = result.get("block_reasons", [])
            assert any(
                "No current-turn evidence" in r or "evidence-without-tool-events" in r
                for r in block_reasons
            )
        finally:
            rca_module.load_epistemic_bindings = original_load
            if hasattr(rca_module, "load_epistemic_commitments"):
                delattr(rca_module, "load_epistemic_commitments")


# --- Evidence Store Integration Tests --------------------------------------


class TestEvidenceStoreIntegration:
    """Integration tests with evidence_store.py."""

    @pytest.fixture(autouse=True)
    def cleanup_evidence_db(self):
        """Clean up the evidence database before each test."""
        from pathlib import Path

        db_path = Path("session_data/evidence.db")
        if db_path.exists():
            try:
                # Delete and recreate the database
                db_path.unlink()
                # Also delete -wal and -shm files if they exist
                for ext in ["-wal", "-shm"]:
                    wal_file = db_path.with_suffix(ext)
                    if wal_file.exists():
                        wal_file.unlink()
            except Exception:
                pass  # Fail silently if cleanup fails
        yield
        # No teardown needed - init_db() will recreate the database

    def test_create_and_load_binding(self, session_data, cleanup_evidence_db):
        """Test creating and loading epistemic binding."""
        # Initialize database
        init_db()

        # Write commitment
        commitment_id = write_epistemic_commitment(
            session_id=session_data["session_id"],
            terminal_id=session_data["terminal_id"],
            turn_id="turn-001",
            claim_type="evidence",
            content="Read on `config.json` showed missing key",
        )

        # Create binding
        binding_id = create_epistemic_binding(
            commitment_id=commitment_id,
            tool_event_id=123,
            binding_kind="artifact_path",
            state_hash="config.json",
        )

        # Load binding
        bindings = load_epistemic_bindings(
            commitment_id=commitment_id,
            session_id=session_data["session_id"],
            terminal_id=session_data["terminal_id"],
        )

        assert len(bindings) > 0
        assert bindings[0]["binding_value"] == "config.json"

    def test_mark_binding_stale(self, session_data, cleanup_evidence_db):
        """Test marking binding as stale."""
        # Initialize database
        init_db()

        # Write commitment
        commitment_id = write_epistemic_commitment(
            session_id=session_data["session_id"],
            terminal_id=session_data["terminal_id"],
            turn_id="turn-001",
            claim_type="evidence",
            content="Read on `config.json` showed missing key",
        )

        # Create binding (use unique tool_event_id to avoid UNIQUE constraint)
        binding_id = create_epistemic_binding(
            commitment_id=commitment_id,
            tool_event_id=124,  # Different from test_create_and_load_binding
            binding_kind="artifact_path",
            state_hash="config.json",
        )

        # Mark stale (simulating new Write tool event that invalidates)
        mark_binding_stale(binding_id, 456)

        # Load binding with include_stale=True to check stale flag
        bindings = load_epistemic_bindings(
            commitment_id=commitment_id,
            session_id=session_data["session_id"],
            terminal_id=session_data["terminal_id"],
            include_stale=True,  # Need to include stale bindings to verify marking worked
        )

        assert len(bindings) > 0
        assert bindings[0]["is_stale"] == True  # Fixed key name and use boolean


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
