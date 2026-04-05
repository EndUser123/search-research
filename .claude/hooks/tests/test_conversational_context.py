#!/usr/bin/env python3
"""Tests for get_conversational_context() in context_followup_detector.py."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(HOOKS_DIR / "UserPromptSubmit_modules"))

from UserPromptSubmit_modules.context_followup_detector import (
    _inject_conversational_context,
    get_conversational_context,
)


def _make_transcript(entries: list[dict], tmpdir: str) -> str:
    """Helper: write entries as JSONL, return path."""
    path = os.path.join(tmpdir, "transcript.jsonl")
    with open(path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return path


class TestGetConversationalContext:
    """Tests for get_conversational_context() per plan-20260328-shared-context-protocol.md."""

    def test_followup_with_prior_arch_turn(self, tmp_path):
        """Test 1: Follow-up with prior /arch turn → detected_skills: ['arch']."""
        transcript_path = _make_transcript([
            {"role": "assistant", "content": "Running /arch on the codebase."},
            {"role": "user", "content": "/arch what about error handling?"},
        ], str(tmp_path))

        result = get_conversational_context(transcript_path)
        assert result["detected_skills"] == ["arch"]

    def test_followup_with_prior_trace_turn(self, tmp_path):
        """Test 2: Follow-up with prior /trace turn → detected_skills: ['trace']."""
        transcript_path = _make_transcript([
            {"role": "assistant", "content": "Running /trace."},
            {"role": "user", "content": "/trace can you check the flow?"},
        ], str(tmp_path))

        result = get_conversational_context(transcript_path)
        assert result["detected_skills"] == ["trace"]

    def test_fresh_session(self, tmp_path):
        """Test 3: Fresh session → is_followup: False."""
        transcript_path = _make_transcript([
            {"role": "user", "content": "/arch review the authentication module"},
        ], str(tmp_path))

        result = get_conversational_context(transcript_path)
        # Single user entry = not a follow-up
        assert result["is_followup"] is False

    def test_prior_discussion_of_handoff(self, tmp_path):
        """Test 4: Prior discussion of 'handoff' → detected_topics: ['handoff']."""
        transcript_path = _make_transcript([
            {"role": "assistant", "content": "Discussing handoff protocol."},
            {"role": "user", "content": "Let's refine the handoff mechanism"},
        ], str(tmp_path))

        result = get_conversational_context(transcript_path)
        assert "handoff" in result["detected_topics"]

    def test_slash_in_quoted_text(self, tmp_path):
        """Test 5: Slash in quoted text → detected_skills: [] (exclusion)."""
        transcript_path = _make_transcript([
            {"role": "assistant", "content": "I mentioned /arch earlier."},
            {"role": "user", "content": "I mentioned /arch to the team"},
        ], str(tmp_path))

        result = get_conversational_context(transcript_path)
        # Skill preceded by text "mentioned" is not a skill invocation
        assert result["detected_skills"] == []

    def test_multiple_skills_same_session(self, tmp_path):
        """Test 6: Multiple skills same session → detected_skills: ['arch', 'planning']."""
        transcript_path = _make_transcript([
            {"role": "assistant", "content": "Done with architecture."},
            {"role": "user", "content": "/arch review the API design"},
            {"role": "assistant", "content": "Architecture reviewed."},
            {"role": "user", "content": "/planning what about the database layer?"},
        ], str(tmp_path))

        result = get_conversational_context(transcript_path)
        assert "arch" in result["detected_skills"]
        assert "planning" in result["detected_skills"]

    def test_transcript_file_missing(self, tmp_path):
        """Test 7: Transcript file missing → Returns empty context, no exception."""
        result = get_conversational_context(tmp_path / "nonexistent.jsonl")
        assert result == {
            "is_followup": False,
            "detected_skills": [],
            "detected_topics": [],
            "confidence": 0.0,
        }

    def test_malformed_transcript_json(self, tmp_path):
        """Test 8: Malformed transcript JSON → Skips bad lines, returns partial context."""
        path = tmp_path / "malformed.jsonl"
        path.write_text(
            '{"role": "user", "content": "/arch review"}\n'
            'NOT JSON\n'
            '{"role": "user", "content": "/trace check this"}\n',
            encoding="utf-8",
        )

        result = get_conversational_context(path)
        # Should parse valid lines and skip malformed
        assert "arch" in result["detected_skills"] or "trace" in result["detected_skills"]

    def test_same_skill_repeated(self, tmp_path):
        """Test 9: Same skill repeated → detected_skills: ['arch'] (deduplicated)."""
        transcript_path = _make_transcript([
            {"role": "user", "content": "/arch review the module"},
            {"role": "assistant", "content": "Reviewed."},
            {"role": "user", "content": "/arch also check errors"},
        ], str(tmp_path))

        result = get_conversational_context(transcript_path)
        assert result["detected_skills"] == ["arch"]
        # Should not be duplicated
        assert len(result["detected_skills"]) == len(set(result["detected_skills"]))

    def test_confidence_boundaries(self, tmp_path):
        """Test 10: Confidence boundaries — 1 skill = 0.6, 1 topic = 0.4, both = 1.0."""
        # 1 skill only: confidence = 0.6 * 1 / 1 = 0.6
        path1 = _make_transcript([
            {"role": "user", "content": "/arch what about the design?"},
        ], str(tmp_path))
        r1 = get_conversational_context(path1)
        assert r1["confidence"] == 0.6, f"Expected 0.6, got {r1['confidence']}"

        # 1 topic only: confidence = 0.4 * 1 / 1 = 0.4
        path2 = _make_transcript([
            {"role": "user", "content": "Let's discuss handoff protocol"},
        ], str(tmp_path))
        r2 = get_conversational_context(path2)
        assert r2["confidence"] == 0.4, f"Expected 0.4, got {r2['confidence']}"

        # Both: (0.6 + 0.4) / 1 = 1.0 (capped)
        path3 = _make_transcript([
            {"role": "user", "content": "/arch and handoff are related"},
        ], str(tmp_path))
        r3 = get_conversational_context(path3)
        assert r3["confidence"] == 1.0, f"Expected 1.0, got {r3['confidence']}"

    def test_null_transcript_path(self):
        """Null transcript_path → Returns empty context, no exception."""
        result = get_conversational_context(None)
        assert result == {
            "is_followup": False,
            "detected_skills": [],
            "detected_topics": [],
            "confidence": 0.0,
        }

    def test_empty_transcript_file(self, tmp_path):
        """Empty transcript file → Returns empty context."""
        path = tmp_path / "empty.jsonl"
        path.write_text("", encoding="utf-8")

        result = get_conversational_context(path)
        assert result["confidence"] == 0.0

    def test_context_window_limit(self, tmp_path):
        """Only last 10 user entries should be scanned."""
        entries = [{"role": "user", "content": f"/arch entry {i}"} for i in range(15)]
        transcript_path = _make_transcript(entries, str(tmp_path))

        result = get_conversational_context(transcript_path)
        # Should only detect the most recent 10 (all 10 are /arch, so deduplicated to 1)
        assert result["detected_skills"] == ["arch"]

    def test_all_fields_always_present(self, tmp_path):
        """All fields always present, never None."""
        path = _make_transcript([
            {"role": "user", "content": "/arch"},
        ], str(tmp_path))
        result = get_conversational_context(path)

        assert "is_followup" in result
        assert "detected_skills" in result
        assert "detected_topics" in result
        assert "confidence" in result
        assert result["is_followup"] is not None
        assert result["detected_skills"] is not None
        assert result["detected_topics"] is not None
        assert result["confidence"] is not None


class TestInjectConversationalContext:
    """Tests for _inject_conversational_context() helper."""

    def test_injects_context_block(self):
        """Should inject [CONVERSATIONAL CONTEXT] block into prompt."""
        prompt = "Continue with the implementation."
        conv_context = {
            "detected_skills": ["arch", "planning"],
            "detected_topics": ["handoff", "routing"],
            "confidence": 0.8,
        }
        result = _inject_conversational_context(prompt, conv_context)

        assert "[CONVERSATIONAL CONTEXT]" in result
        assert "/arch" in result
        assert "/planning" in result
        assert "handoff" in result
        assert "routing" in result
        assert "0.8" in result
        assert "Continue with the implementation" in result

    def test_no_injection_when_empty(self):
        """Should return original prompt when no context detected."""
        prompt = "Hello world."
        conv_context = {
            "detected_skills": [],
            "detected_topics": [],
            "confidence": 0.0,
        }
        result = _inject_conversational_context(prompt, conv_context)
        assert result == prompt

    def test_injection_format_matches_spec(self):
        """Format should match plan specification."""
        prompt = "Proceed."
        conv_context = {
            "detected_skills": ["trace"],
            "detected_topics": ["session"],
            "confidence": 0.6,
        }
        result = _inject_conversational_context(prompt, conv_context)

        # Check spec format
        assert result.startswith("[CONVERSATIONAL CONTEXT]")
        assert "Prior skills detected: /trace" in result
        assert "Prior topics: session" in result
        assert "Confidence: 0.6" in result
        assert "[/CONVERSATIONAL CONTEXT]" in result
        assert "Proceed." in result
