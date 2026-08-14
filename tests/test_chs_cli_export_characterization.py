"""Characterization tests for /chs export functionality.

RED PHASE: These tests MUST FAIL before refactoring. They capture current behavior
to ensure we don't break it during refactoring.

Run: python -m pytest tests/test_chs_cli_export_characterization.py -v
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add skill scripts to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "chs" / "scripts"))
from chs_cli import CHSExporter


class TestExportChainCharacterization:
    """Characterization tests for export_chain() method.

    These tests capture the CURRENT behavior before refactoring.
    After refactoring, these tests should still pass.
    """

    def test_returns_path_to_export_file(self, tmp_path):
        """export_chain returns a Path object pointing to the export file."""
        # This test will FAIL until we implement the fix
        exporter = CHSExporter()

        with patch("pathlib.Path.home", return_value=tmp_path):
            # Mock sessions-index.json
            sessions_dir = tmp_path / ".claude" / "projects" / "P--"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            sessions_index = sessions_dir / "sessions-index.json"

            # Create test session
            test_session_id = "test-session-123"
            test_transcript = sessions_dir / f"{test_session_id}.jsonl"
            test_transcript.write_text('{"type": "user", "message": {"content": [{"text": "test"}]}}\n')

            sessions_index.write_text(json.dumps({
                test_session_id: {
                    "sessionId": test_session_id,
                    "startedAt": 1000,
                    "fullPath": str(test_transcript)
                }
            }))

            result = exporter.export_chain(session_id=test_session_id)

        # Characterization: result should be a Path
        assert isinstance(result, Path)
        # Characterization: file should exist after export
        assert result.exists()

    def test_export_file_contains_session_chain_content(self, tmp_path):
        """Export file contains properly formatted session chain markdown."""
        exporter = CHSExporter()

        with patch("pathlib.Path.home", return_value=tmp_path):
            sessions_dir = tmp_path / ".claude" / "projects" / "P--"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            sessions_index = sessions_dir / "sessions-index.json"

            test_session_id = "test-session-456"
            test_transcript = sessions_dir / f"{test_session_id}.jsonl"
            test_transcript.write_text(json.dumps({
                "type": "user",
                "message": {"content": [{"text": "Hello world"}]}
            }) + "\n")

            sessions_index.write_text(json.dumps({
                test_session_id: {
                    "sessionId": test_session_id,
                    "startedAt": 2000,
                    "fullPath": str(test_transcript)
                }
            }))

            result = exporter.export_chain(session_id=test_session_id)
            content = result.read_text()

        # Characterization: export should contain expected sections
        assert "# Session Chain Export" in content
        assert f"**Root session:** {test_session_id}" in content
        assert "**Sessions in chain:** 1" in content

    def test_handles_missing_sessions_index_gracefully(self, tmp_path):
        """Missing sessions-index.json raises clear error."""
        exporter = CHSExporter()

        with patch("pathlib.Path.home", return_value=tmp_path):
            # Don't create sessions-index.json
            sessions_dir = tmp_path / ".claude" / "projects" / "P--"
            sessions_dir.mkdir(parents=True, exist_ok=True)

            # Characterization: should raise ValueError with clear message
            with pytest.raises(ValueError) as exc_info:
                exporter.export_chain(session_id="nonexistent-session")

            assert "not found in sessions-index.json" in str(exc_info.value)

    def test_validates_paths_from_sessions_index(self, tmp_path):
        """Paths from sessions-index.json are validated before use."""
        exporter = CHSExporter()

        with patch("pathlib.Path.home", return_value=tmp_path):
            sessions_dir = tmp_path / ".claude" / "projects" / "P--"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            sessions_index = sessions_dir / "sessions-index.json"

            # Malicious path entry pointing outside allowed directory
            test_session_id = "test-session-789"
            sessions_index.write_text(json.dumps({
                test_session_id: {
                    "sessionId": test_session_id,
                    "startedAt": 3000,
                    "fullPath": str(tmp_path / ".." / ".." / ".." / "etc" / "passwd")
                }
            }))

            # V2 behavior: writes error to export file instead of raising
            result = exporter.export_chain(session_id=test_session_id)
            content = result.read_text()

            # Should contain error message about invalid path
            assert "Invalid path" in content or "outside" in content

    def test_handles_missing_transcript_files_gracefully(self, tmp_path):
        """Missing transcript files are handled without crashing."""
        exporter = CHSExporter()

        with patch("pathlib.Path.home", return_value=tmp_path):
            sessions_dir = tmp_path / ".claude" / "projects" / "P--"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            sessions_index = sessions_dir / "sessions-index.json"

            # Session entry references non-existent transcript
            test_session_id = "test-session-missing"
            sessions_index.write_text(json.dumps({
                test_session_id: {
                    "sessionId": test_session_id,
                    "startedAt": 4000,
                    "fullPath": str(sessions_dir / "does-not-exist.jsonl")
                }
            }))

            # After refactoring: should handle gracefully with error message in output
            result = exporter.export_chain(session_id=test_session_id)
            content = result.read_text()

            # Should contain error message about missing file
            assert "Error reading" in content or "does-not-exist.jsonl" in content


class TestExportChainErrorHandling:
    """Tests for error handling improvements needed during refactoring."""

    def test_load_sessions_index_error_handling(self, tmp_path):
        """Corrupted sessions-index.json raises clear error."""
        exporter = CHSExporter()

        with patch("pathlib.Path.home", return_value=tmp_path):
            sessions_dir = tmp_path / ".claude" / "projects" / "P--"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            sessions_index = sessions_dir / "sessions-index.json"

            # Write invalid JSON
            sessions_index.write_text("{invalid json")

            # Characterization: should raise clear error about corruption
            with pytest.raises(ValueError) as exc_info:
                exporter.export_chain(session_id="any-session")

            assert "sessions-index" in str(exc_info.value).lower()

    def test_export_directory_creation_error_handling(self, tmp_path):
        """Cannot create exports directory raises clear error."""
        exporter = CHSExporter()

        with patch("pathlib.Path.home", return_value=tmp_path):
            sessions_dir = tmp_path / ".claude" / "projects" / "P--"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            sessions_index = sessions_dir / "sessions-index.json"

            test_session_id = "test-session-perm"
            test_transcript = sessions_dir / f"{test_session_id}.jsonl"
            test_transcript.write_text('{"type": "user", "message": {"content": [{"text": "x"}]}}\n')

            sessions_index.write_text(json.dumps({
                test_session_id: {
                    "sessionId": test_session_id,
                    "startedAt": 5000,
                    "fullPath": str(test_transcript)
                }
            }))

            # Mock mkdir more selectively to only fail for exports directory
            original_mkdir = Path.mkdir
            def selective_mkdir(self, *args, **kwargs):
                # Allow normal mkdir for everything except exports directory
                if "exports" in str(self):
                    raise PermissionError("Access denied")
                return original_mkdir(self, *args, **kwargs)

            with patch.object(Path, "mkdir", selective_mkdir):
                # Characterization: should raise clear error
                with pytest.raises(ValueError) as exc_info:
                    exporter.export_chain(session_id=test_session_id)

                assert "exports" in str(exc_info.value).lower() or "directory" in str(exc_info.value).lower()

    def test_write_operation_error_handling(self, tmp_path):
        """Cannot write export file raises clear error."""
        exporter = CHSExporter()

        with patch("pathlib.Path.home", return_value=tmp_path):
            sessions_dir = tmp_path / ".claude" / "projects" / "P--"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            sessions_index = sessions_dir / "sessions-index.json"

            test_session_id = "test-session-write"
            test_transcript = sessions_dir / f"{test_session_id}.jsonl"
            test_transcript.write_text('{"type": "user", "message": {"content": [{"text": "x"}]}}\n')

            sessions_index.write_text(json.dumps({
                test_session_id: {
                    "sessionId": test_session_id,
                    "startedAt": 6000,
                    "fullPath": str(test_transcript)
                }
            }))

            # Mock open() to raise OSError when writing export file
            original_open = open
            def failing_open(file, *args, **kwargs):
                # Allow normal opens for reading, fail on export write
                if "w" in args and "chain_" in str(file):
                    raise OSError("Disk full")
                return original_open(file, *args, **kwargs)

            with patch("builtins.open", failing_open):
                # Characterization: should raise clear error
                with pytest.raises(ValueError) as exc_info:
                    exporter.export_chain(session_id=test_session_id)

                assert "write" in str(exc_info.value).lower() or "export" in str(exc_info.value).lower()


class TestExportChainDryViolations:
    """Tests for DRY violations found during discovery."""

    def test_duplicate_datetime_now_calls(self, tmp_path):
        """datetime.now() is called multiple times; should be DRYed up."""
        # This is a code smell test - verifying the issue exists
        exporter = CHSExporter()

        with patch("pathlib.Path.home", return_value=tmp_path):
            sessions_dir = tmp_path / ".claude" / "projects" / "P--"
            sessions_dir.mkdir(parents=True, exist_ok=True)
            sessions_index = sessions_dir / "sessions-index.json"

            test_session_id = "test-session-dry"
            test_transcript = sessions_dir / f"{test_session_id}.jsonl"
            test_transcript.write_text('{"type": "user", "message": {"content": [{"text": "x"}]}}\n')

            sessions_index.write_text(json.dumps({
                test_session_id: {
                    "sessionId": test_session_id,
                    "startedAt": 7000,
                    "fullPath": str(test_transcript)
                }
            }))

            # Mock datetime.now to track call count
            with patch("chs_cli.datetime") as mock_dt:
                mock_dt.now.return_value.strftime.side_effect = lambda fmt: f"mock-{fmt}"
                mock_dt.now.return_value.strftime.return_value = "2025-01-21 12:00:00"

                exporter.export_chain(session_id=test_session_id)

                # Characterization: datetime.now() is called 2+ times (DRY violation)
                # This documents the current behavior before fix
                call_count = mock_dt.now.call_count
                assert call_count >= 2, f"Expected 2+ calls to datetime.now(), got {call_count}"
