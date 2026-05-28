"""Tests for CHS export via identity.json (no fallbacks)."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "chs" / "scripts"))
from chs_cli import CHSExporter


def _make_identity(session_id: str, transcript_path: str, chain: list | None = None) -> dict:
    return {
        "claude": {
            "session_id": session_id,
            "transcript_path": transcript_path,
            "transcript_chain": chain or [],
        }
    }


class TestExportChainFromIdentity:
    def test_returns_path_to_export_file(self, tmp_path):
        transcript = tmp_path / "test-session-123.jsonl"
        transcript.write_text(
            json.dumps({"type": "user", "message": {"content": [{"text": "test"}]}}) + "\n"
        )
        identity = _make_identity("test-session-123", str(transcript))
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=identity):
            result = exporter.export_chain(session_id="test-session-123")
        assert isinstance(result, Path)
        assert result.exists()

    def test_export_file_contains_chain_content(self, tmp_path):
        transcript = tmp_path / "test-session-456.jsonl"
        transcript.write_text(
            json.dumps({"type": "user", "message": {"content": [{"text": "Hello world"}]}}) + "\n"
        )
        identity = _make_identity("test-session-456", str(transcript))
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=identity):
            result = exporter.export_chain(session_id="test-session-456")
        content = result.read_text(encoding="utf-8")
        assert "Session Chain Export" in content
        assert "test-session-456" in content

    def test_raises_when_no_identity(self):
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=None):
            with pytest.raises(ValueError, match="identity.json not available"):
                exporter.export_chain(session_id="nonexistent-session")

    def test_handles_missing_transcript_gracefully(self, tmp_path):
        identity = _make_identity("session-missing", str(tmp_path / "does-not-exist.jsonl"))
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=identity):
            result = exporter.export_chain(session_id="session-missing", output_path=tmp_path / "export.md")
        content = result.read_text(encoding="utf-8")
        assert "Error reading" in content or "does-not-exist" in content

    def test_export_with_chain(self, tmp_path):
        t1 = tmp_path / "older.jsonl"
        t1.write_text(json.dumps({"type": "user", "message": {"content": [{"text": "old"}]}}) + "\n")
        t2 = tmp_path / "newer.jsonl"
        t2.write_text(json.dumps({"type": "user", "message": {"content": [{"text": "new"}]}}) + "\n")
        identity = _make_identity("newer", str(t2), chain=[str(t1)])
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=identity):
            result = exporter.export_chain(session_id="newer", output_path=tmp_path / "export.md")
        content = result.read_text(encoding="utf-8")
        assert "older" in content
        assert "newer" in content
