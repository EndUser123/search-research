"""Tests for CHS session resolution via identity.json."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "chs" / "scripts"))
from chs_cli import CHSExporter


def _make_identity(session_id: str, transcript_path: str = "", chain: list | None = None) -> dict:
    return {
        "claude": {
            "session_id": session_id,
            "transcript_path": transcript_path,
            "transcript_chain": chain or [],
        }
    }


class TestResolveFromIdentity:
    def test_returns_none_no_wt_session(self):
        with patch.dict(os.environ, {}, clear=True):
            exporter = CHSExporter()
            result = exporter._resolve_from_identity()
        assert result is None


class TestGetCurrentSessionId:
    def test_returns_session_id_from_identity(self):
        identity = _make_identity("test-session-abc123")
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=identity):
            result = exporter.get_current_session_id()
        assert result == "test-session-abc123"

    def test_returns_none_when_no_identity(self):
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=None):
            result = exporter.get_current_session_id()
        assert result is None

    def test_returns_none_when_identity_has_no_session_id(self):
        identity = _make_identity("")
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=identity):
            result = exporter.get_current_session_id()
        assert result is None


class TestExportChainIdentityOnly:
    def test_exports_from_identity_chain(self, tmp_path):
        transcript = tmp_path / "session-1.jsonl"
        transcript.write_text(
            json.dumps({"type": "user", "message": {"content": [{"text": "hello"}]}}) + "\n",
            encoding="utf-8",
        )
        identity = _make_identity("session-1", str(transcript), chain=[])
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=identity):
            result = exporter.export_chain(session_id="session-1", output_path=tmp_path / "export.md")
        assert isinstance(result, Path)
        assert result.exists()
        content = result.read_text(encoding="utf-8")
        assert "Session Chain Export" in content

    def test_raises_when_no_identity(self):
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=None):
            with pytest.raises(ValueError, match="identity.json not available"):
                exporter.export_chain(session_id="some-session")

    def test_raises_when_no_transcript_path(self):
        identity = _make_identity("session-1", transcript_path="")
        exporter = CHSExporter()
        with patch.object(exporter, "_resolve_from_identity", return_value=identity):
            with pytest.raises(ValueError, match="identity.json not available"):
                exporter.export_chain(session_id="session-1")


class TestShowHandlerContext:
    def test_role_fallback_to_type(self):
        entry = {"type": "summary", "summary": "test"}
        role = entry.get("message", {}).get("role") or entry.get("type", "unknown")
        assert role == "summary"

    def test_role_from_message(self):
        entry = {"type": "message", "message": {"role": "user", "content": "hi"}}
        role = entry.get("message", {}).get("role") or entry.get("type", "unknown")
        assert role == "user"
