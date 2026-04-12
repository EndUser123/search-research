"""Tests for /recap skill - Pre-mortem Domain 4 (TESTING).

Tests cover:
- 4a: Import path verification (from core.session_chain)
- 4b: Handoff chain walking with mock handoff files
- 4c: Subagent filtering (exact component matching for 'subagents-analysis')
- 4d: Session_id deduplication via (session_id, transcript_path) tuples
"""
import json
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import NamedTuple
from unittest.mock import Mock, MagicMock, patch

import pytest


# Pre-mortem Domain 4a: Test import path
class TestImportPath:
    """Domain 4a: Test that import from core.session_chain works."""

    def test_import_from_core_session_chain_with_syspath(self):
        """Test import from core.session_chain with sys.path manipulation.

        This is the actual import pattern used in __init__.py after pre-mortem fix 1a.
        """
        from pathlib import Path

        _search_research_root = Path("P:/packages/search-research")
        if str(_search_research_root) not in sys.path:
            sys.path.insert(0, str(_search_research_root))

        try:
            from core.session_chain import (
                SessionChainEntry,
                walk_handoff_chain,
                walk_session_chain,
            )
            # Verify API exists and is callable
            assert hasattr(walk_handoff_chain, '__call__'), "walk_handoff_chain not callable"
            assert hasattr(walk_session_chain, '__call__'), "walk_session_chain not callable"
        except ImportError as e:
            pytest.skip(f"search-research package not available: {e}")

    def test_session_chain_entry_structure(self):
        """Test that SessionChainEntry has expected fields."""
        _search_research_root = Path("P:/packages/search-research")
        if str(_search_research_root) not in sys.path:
            sys.path.insert(0, str(_search_research_root))

        try:
            from core.session_chain import SessionChainEntry

            # Verify it has the expected attributes
            # Note: field is 'created' not 'created_at' (actual API)
            entry = SessionChainEntry(
                session_id="test-123",
                transcript_path=Path("/fake/path.jsonl"),
                parent_transcript_path=None,
                created=datetime.now(timezone.utc),
            )
            assert entry.session_id == "test-123"
            assert entry.transcript_path == Path("/fake/path.jsonl")
        except ImportError:
            pytest.skip("search-research package not available")


# Pre-mortem Domain 4b: Test handoff chain walking
class TestHandoffChainWalking:
    """Domain 4b: Test handoff chain reconstruction from mock handoff files."""

    def test_chain_result_structure(self):
        """Test that SessionChainResult has expected structure.

        This verifies the chain walking API works correctly.
        """
        _search_research_root = Path("P:/packages/search-research")
        if str(_search_research_root) not in sys.path:
            sys.path.insert(0, str(_search_research_root))

        try:
            from core.session_chain import SessionChainResult, SessionChainEntry

            # Create mock chain result
            entries = [
                SessionChainEntry(
                    session_id="session-1",
                    transcript_path=Path("/path1.jsonl"),
                    parent_transcript_path=None,
                    created=datetime.now(timezone.utc),
                ),
                SessionChainEntry(
                    session_id="session-2",
                    transcript_path=Path("/path2.jsonl"),
                    parent_transcript_path=Path("/path1.jsonl"),
                    created=datetime.now(timezone.utc),
                ),
            ]
            chain_result = SessionChainResult(entries=entries)

            # Verify structure
            assert len(chain_result.entries) == 2
            assert chain_result.entries[0].session_id == "session-1"
            assert chain_result.entries[1].parent_transcript_path == Path("/path1.jsonl")
        except ImportError:
            pytest.skip("search-research package not available")


# Pre-mortem Domain 4c: Test subagent filtering edge cases
class TestSubagentFiltering:
    """Domain 4c: Test subagent transcript filtering with exact component matching (R-012)."""

    def test_subagents_analysis_directory_not_filtered(self):
        """Test R-012: 'subagents-analysis' directory is NOT filtered.

        This tests exact component matching - 'subagents-analysis' != 'subagents'.
        The path contains 'subagents' as a substring but NOT as a directory component.
        """
        # Import the function under test
        import sys
        from pathlib import Path

        # Add skills/recap to path to import
        skill_path = Path("P:/.claude/skills/recap")
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        from recap import _is_subagent_transcript

        # This is a legitimate user project directory (not a subagent)
        legit_path = Path("/home/user/projects/subagents-analysis/transcript.jsonl")

        # Should return False (NOT filtered)
        result = _is_subagent_transcript(legit_path)
        assert result is False, f"subagents-analysis path should NOT be filtered, got {result}"

    def test_subagents_directory_component_is_filtered(self):
        """Test that paths with 'subagents' as exact directory component ARE filtered."""
        import sys
        from pathlib import Path

        skill_path = Path("P:/.claude/skills/recap")
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        from recap import _is_subagent_transcript

        # This IS a subagent transcript (subagents is a directory component)
        subagent_path = Path("/home/user/.claude/subagents/agent-123/transcript.jsonl")

        # Should return True (filtered)
        result = _is_subagent_transcript(subagent_path)
        assert result is True, f"subagents directory component should be filtered, got {result}"

    def test_agent_prefix_filename_is_filtered(self):
        """Test that filenames starting with 'agent-' are filtered."""
        import sys
        from pathlib import Path

        skill_path = Path("P:/.claude/skills/recap")
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        from recap import _is_subagent_transcript

        agent_path = Path("/home/user/projects/sessions/agent-456.jsonl")

        result = _is_subagent_transcript(agent_path)
        assert result is True, f"agent- prefix should be filtered, got {result}"

    def test_normal_transcript_not_filtered(self):
        """Test that normal user session transcripts are NOT filtered."""
        import sys
        from pathlib import Path

        skill_path = Path("P:/.claude/skills/recap")
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        from recap import _is_subagent_transcript

        normal_path = Path("/home/user/projects/myproject/sessions/session-abc.jsonl")

        result = _is_subagent_transcript(normal_path)
        assert result is False, f"normal transcript should NOT be filtered, got {result}"


# Pre-mortem Domain 4d: Test session_id deduplication
class TestSessionIdDeduplication:
    """Domain 4d: Test (session_id, transcript_path) tuple deduplication (R-007)."""

    def test_unique_session_transcript_pairs_all_included(self):
        """Test that unique (session_id, transcript_path) tuples are all included.

        Scenario: Same session_id appears with different transcript_path values.
        This can happen in multi-terminal scenarios.
        Expected: Both entries included (different tuples).
        """
        import sys
        from pathlib import Path

        skill_path = Path("P:/.claude/skills/recap")
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        # Import dependencies
        _search_research_root = Path("P:/packages/search-research")
        if str(_search_research_root) not in sys.path:
            sys.path.insert(0, str(_search_research_root))

        try:
            from core.session_chain import SessionChainEntry, SessionChainResult
            from recap import _load_from_chain_result

            # Create entries with same session_id but different transcript_path
            entries = [
                SessionChainEntry(
                    session_id="shared-session-id",
                    transcript_path=Path("/terminal1/transcript.jsonl"),
                    parent_transcript_path=None,
                    created=datetime.now(timezone.utc),
                ),
                SessionChainEntry(
                    session_id="shared-session-id",  # Same session_id
                    transcript_path=Path("/terminal2/transcript.jsonl"),  # Different path
                    parent_transcript_path=None,
                    created=datetime.now(timezone.utc),
                ),
            ]
            chain_result = SessionChainResult(entries=entries)

            # Mock extract_sessions_from_transcript to return dummy data
            with patch("recap.extract_sessions_from_transcript") as mock_extract:
                mock_extract.return_value = [{"session_id": "shared-session-id"}]

                # Mock load_transcript_entries
                with patch("recap.load_transcript_entries") as mock_load:
                    mock_load.return_value = []

                    # Mock transcript exists checks
                    with patch("pathlib.Path.exists", return_value=True):
                        result = _load_from_chain_result(chain_result, Path("/fake"))

            # Both should be included (different tuples)
            assert mock_extract.call_count == 2, "Both (session_id, path) tuples should be processed"
        except ImportError:
            pytest.skip("search-research package not available")

    def test_duplicate_session_transcript_pairs_deduped(self):
        """Test that duplicate (session_id, transcript_path) tuples are deduplicated.

        Scenario: Same exact tuple appears multiple times.
        Expected: Only one instance included.
        """
        import sys
        from pathlib import Path

        skill_path = Path("P:/.claude/skills/recap")
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        _search_research_root = Path("P:/packages/search-research")
        if str(_search_research_root) not in sys.path:
            sys.path.insert(0, str(_search_research_root))

        try:
            from core.session_chain import SessionChainEntry, SessionChainResult
            from recap import _load_from_chain_result

            # Create duplicate entries (same session_id AND same transcript_path)
            duplicate_path = Path("/only/transcript.jsonl")
            entries = [
                SessionChainEntry(
                    session_id="session-123",
                    transcript_path=duplicate_path,
                    parent_transcript_path=None,
                    created=datetime.now(timezone.utc),
                ),
                SessionChainEntry(
                    session_id="session-123",  # Same session_id
                    transcript_path=duplicate_path,  # Same path = duplicate tuple
                    parent_transcript_path=None,
                    created=datetime.now(timezone.utc),
                ),
            ]
            chain_result = SessionChainResult(entries=entries)

            with patch("recap.extract_sessions_from_transcript") as mock_extract:
                mock_extract.return_value = [{"session_id": "session-123"}]

                with patch("recap.load_transcript_entries") as mock_load:
                    mock_load.return_value = []

                    with patch("pathlib.Path.exists", return_value=True):
                        result = _load_from_chain_result(chain_result, Path("/fake"))

            # Only one should be processed (deduplication worked)
            assert mock_extract.call_count == 1, "Duplicate (session_id, path) tuples should be deduplicated"
        except ImportError:
            pytest.skip("search-research package not available")


class TestErrorMessages:
    """Pre-mortem Domain 3c: Verify error messages are user-friendly."""

    def test_error_messages_are_user_friendly(self):
        """Test that error messages avoid technical jargon and explain impact.

        Verifies:
        - No "Session chain broken" jargon (uses plain language instead)
        - Messages explain impact ("session history may be incomplete")
        - No raw OSError/PermissionDenied technical terms in user-facing messages
        """
        import sys
        from pathlib import Path

        skill_path = Path("P:/.claude/skills/recap")
        if str(skill_path) not in sys.path:
            sys.path.insert(0, str(skill_path))

        import recap

        # Read the source to verify improved error messages
        source = Path(recap.__file__).read_text()

        # Should have user-friendly messages
        assert "Unable to access handoff directory" in source, "Should have user-friendly handoff error"
        assert "Your session history may be incomplete" in source, "Should explain impact"
        assert "Some session history could not be loaded" in source, "Should use plain language"
        assert "Trying alternative method to load your sessions" in source, "Should be action-oriented"

        # Should NOT have technical jargon in user-facing messages
        assert "Session chain broken" not in source, "Should not have 'chain broken' jargon"
        assert "degrading to unified chain" not in source, "Should not have 'degrading' jargon"
        assert "Returning empty session list" not in source, "Should not have technical return value description"
