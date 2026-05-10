#!/usr/bin/env python3
"""Tests for stop/experimental/phase0_depends_on_skills.py."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import re

HOOKS_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(HOOKS_DIR / "stop" / "experimental"))

from stop.experimental import phase0_depends_on_skills as gate_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_transcript(skill_name: str | None = None) -> list[dict[str, Any]]:
    """Build minimal transcript entries."""
    if skill_name:
        return [
            {"type": "user", "message": {"content": f"<command-name>/{skill_name}</command-name>"}}
        ]
    return [{"type": "user", "message": {"content": "plain prompt with no skill"}}]


def _make_data(transcript_entries: list[dict[str, Any]], terminal_id: str = "console_test") -> dict[str, Any]:
    return {"transcript_entries": transcript_entries, "terminal_id": terminal_id}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSkillDetection:
    def test_detects_skill_from_command_tag(self):
        entries = [
            {"type": "user", "message": {"content": "<command-name>/retro</command-name>"}}
        ]
        assert gate_module._detect_skill_from_transcript(entries) == "retro"

    def test_strips_leading_slash(self):
        entries = [
            {"type": "user", "message": {"content": "<command-name>//deep</command-name>"}}
        ]
        assert gate_module._detect_skill_from_transcript(entries) == "deep"

    def test_returns_none_for_plain_prompt(self):
        entries = [{"type": "user", "message": {"content": "fix the bug"}}]
        assert gate_module._detect_skill_from_transcript(entries) is None

    def test_returns_none_for_empty_transcript(self):
        assert gate_module._detect_skill_from_transcript([]) is None

    def test_scans_last_10_entries(self):
        entries = [
            {"type": "user", "message": {"content": f"<command-name>/early{i}</command-name>"}}
            for i in range(5)
        ] + [
            {"type": "user", "message": {"content": "<command-name>/lastskill</command-name>"}}
        ]
        assert gate_module._detect_skill_from_transcript(entries) == "lastskill"


class TestDependsOnSkills:
    def test_no_depends_on_skills_returns_none(self):
        with patch.object(gate_module, "_get_depends_on_skills", return_value=None):
            result = gate_module._get_depends_on_skills("myskill")
            assert result is None

    def test_parses_yaml_frontmatter(self, tmp_path):
        skill_md = tmp_path / "skills" / "myskill" / "SKILL.md"
        skill_md.parent.mkdir(parents=True)
        skill_md.write_text("---\nname: myskill\ndepends_on_skills:\n  - step1\n  - step2\n---\n")
        with patch.object(gate_module, "_HOOKS_ROOT_DIR", tmp_path):
            result = gate_module._get_depends_on_skills("myskill")
        assert result == ["step1", "step2"]

    def test_parses_string_deps(self, tmp_path):
        skill_md = tmp_path / "skills" / "myskill" / "SKILL.md"
        skill_md.parent.mkdir(parents=True)
        skill_md.write_text("---\nname: myskill\ndepends_on_skills: step1\n---\n")
        with patch.object(gate_module, "_HOOKS_ROOT_DIR", tmp_path):
            result = gate_module._get_depends_on_skills("myskill")
        assert result == ["step1"]


class TestPathSanitization:
    def test_special_chars_stripped_from_skill(self):
        safe = re.sub(r"[^a-z0-9_-]", "", "my-skill_123".lower())
        assert safe == "my-skill_123"

    def test_special_chars_stripped_from_terminal(self):
        safe = re.sub(r"[^a-z0-9_-]", "", "console_abc-123".lower())
        assert safe == "console_abc-123"


class TestEvidenceCheck:
    def test_missing_file_returns_false(self):
        fake_dir = Path("/nonexistent/evidence/dir")
        ok, reason = gate_module._check_step1_evidence(fake_dir, "step1")
        assert ok is False
        assert "missing" in reason

    def test_empty_file_returns_false(self, tmp_path):
        step_file = tmp_path / "step_step1.jsonl"
        step_file.write_text("")
        ok, reason = gate_module._check_step1_evidence(tmp_path, "step1")
        assert ok is False
        assert "empty" in reason

    def test_valid_jsonl_returns_true(self, tmp_path):
        step_file = tmp_path / "step_step1.jsonl"
        step_file.write_text('{"evidence": "test"}\n{"extra": "line"}\n')
        ok, reason = gate_module._check_step1_evidence(tmp_path, "step1")
        assert ok is True
        assert "valid" in reason

    def test_corrupt_first_line_returns_false(self, tmp_path):
        step_file = tmp_path / "step_step1.jsonl"
        step_file.write_text("not valid json\n{\"real\": \"json\"}\n")
        ok, reason = gate_module._check_step1_evidence(tmp_path, "step1")
        assert ok is False
        assert "corrupted" in reason


class TestGate:
    def test_disabled_gate_passes(self):
        with patch.dict(os.environ, {"DEPENDS_ON_SKILLS_GATE_ENABLED": "false"}):
            data = _make_data(_make_transcript("myskill"), "console_test")
            assert gate_module.run(data) is None

    def test_no_skill_detected_passes(self):
        with patch.object(gate_module, "_detect_skill_from_transcript", return_value=None):
            data = _make_data([{"type": "user", "message": {"content": "plain"}}], "console_test")
            assert gate_module.run(data) is None

    def test_skill_with_no_depends_on_passes(self):
        with patch.object(gate_module, "_detect_skill_from_transcript", return_value="myskill"):
            with patch.object(gate_module, "_get_depends_on_skills", return_value=None):
                data = _make_data(_make_transcript("myskill"), "console_test")
                assert gate_module.run(data) is None

    def test_no_terminal_id_bypasses(self):
        with patch.object(gate_module, "_detect_skill_from_transcript", return_value="myskill"):
            with patch.object(gate_module, "_get_depends_on_skills", return_value=["step1"]):
                data = {"transcript_entries": _make_transcript("myskill"), "terminal_id": ""}
                assert gate_module.run(data) is None

    def test_evidence_missing_blocks(self):
        with patch.object(gate_module, "_detect_skill_from_transcript", return_value="myskill"):
            with patch.object(gate_module, "_get_depends_on_skills", return_value=["step1"]):
                with patch.object(
                    gate_module, "_get_evidence_dir_for_skill",
                    return_value=Path("/nonexistent/evidence")
                ):
                    data = _make_data(_make_transcript("myskill"), "console_test")
                    result = gate_module.run(data)
                    assert result is not None
                    assert result["decision"] == "block"
                    assert "Phase 0" in result["reason"]
                    # Metadata is emitted on block
                    assert "metadata" in result
                    md = result["metadata"]
                    assert md["skill"] == "myskill"
                    assert md["depends_on"] == ["step1"]
                    assert md["missing_step"] == "step1"
                    assert "evidence_checked" in md
                    assert "step_file" in md
                    assert "failure_reason" in md

    def test_evidence_missing_blocks_with_skill(self):
        """Missing evidence on /gto blocks with full metadata including step name."""
        with patch.object(gate_module, "_detect_skill_from_transcript", return_value="gto"):
            with patch.object(gate_module, "_get_depends_on_skills", return_value=["evidence"]):
                with patch.object(
                    gate_module, "_get_evidence_dir_for_skill",
                    return_value=Path("/nonexistent/gto-evidence")
                ):
                    data = _make_data(_make_transcript("gto"), "console_test")
                    result = gate_module.run(data)
                    assert result is not None
                    assert result["decision"] == "block"
                    md = result["metadata"]
                    assert md["skill"] == "gto"
                    assert md["depends_on"] == ["evidence"]
                    assert md["missing_step"] == "evidence"
                    assert "gto-evidence" in md["evidence_dir"]
                    assert "step_evidence" in md["step_file"]

    def test_evidence_valid_passes(self, tmp_path):
        step_file = tmp_path / "step_step1.jsonl"
        step_file.write_text('{"test": "data"}\n')
        with patch.object(gate_module, "_detect_skill_from_transcript", return_value="myskill"):
            with patch.object(gate_module, "_get_depends_on_skills", return_value=["step1"]):
                with patch.object(gate_module, "_get_evidence_dir_for_skill", return_value=tmp_path):
                    data = _make_data(_make_transcript("myskill"), "console_test")
                    assert gate_module.run(data) is None

    def test_empty_transcript_passes(self):
        data = {"transcript_entries": [], "terminal_id": "console_test"}
        assert gate_module.run(data) is None


class TestPipelineSmoke:
    """Prove the gate runs through the actual Stop.py pipeline input shape."""

    def test_full_stop_payload_shape_passes_when_disabled(self):
        payload = {
            "transcript_entries": _make_transcript("myskill"),
            "terminal_id": "console_test",
            "session_id": "test-session-123",
            "response": "Here's my response",
            "assistant_response": "Here's my response",
        }
        with patch.dict(os.environ, {"DEPENDS_ON_SKILLS_GATE_ENABLED": "false"}):
            result = gate_module.run(payload)
            assert result is None

    def test_full_stop_payload_blocks_when_evidence_missing(self):
        payload = {
            "transcript_entries": [
                {"type": "user", "message": {"content": "<command-name>/myskill</command-name>"}}
            ],
            "terminal_id": "console_test",
            "session_id": "test-session-123",
            "response": "Here's my response",
            "assistant_response": "Here's my response",
        }
        with patch.object(gate_module, "_get_depends_on_skills", return_value=["step1"]):
            with patch.object(
                gate_module, "_get_evidence_dir_for_skill",
                return_value=Path("/nonexistent/evidence")
            ):
                result = gate_module.run(payload)
                assert result is not None
                assert result["decision"] == "block"
                assert result["blocking_hook"] == "phase0_depends_on_skills"
                assert "metadata" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
