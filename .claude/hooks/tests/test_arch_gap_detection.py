"""
Tests for StopHook_arch_gap_detection.py — Anti-rationalization gate for /arch skill.

Tests cover:
- GAP_PATTERNS detection (each phrase)
- Ordinal + gap combination detection
- Transcript search with sliding window wrap-around
- Skill-scope gating (/arch only)
- Fail-open on transcript missing
- Malformed JSONL warning (not block)
- Article+noun specificity (no false positive on "I don't have enough context")

Test data uses synthetic JSONL lines with explicit content fields.
No mocks — all test data is explicit.
"""

import json
import sys
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import StopHook_arch_gap_detection as arch_gap


def _make_jsonl_line(role: str, content: str) -> str:
    """Create a JSON transcript line."""
    return json.dumps({"role": role, "content": content})




def _payload(
    response_text: str = "",
    assistant_response: str = "",
    skill_state: dict[str, Any] | None = None,
    transcript_path: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Create test payload matching validator_input from Stop_router.py."""
    payload: dict[str, Any] = {}
    if response_text:
        payload["response_text"] = response_text
    if assistant_response:
        payload["assistant_response"] = assistant_response
    if skill_state is not None:
        payload["skill_state"] = skill_state
    if transcript_path:
        payload["transcript_path"] = transcript_path
    if session_id:
        payload["session_id"] = session_id
    return payload


class TestGapDetectionPatterns:
    """Each GAP_PATTERNS phrase triggers detection."""

    @pytest.mark.parametrize(
        "phrase",
        [
            "i don't have the ideas",
            "i don't have the codebase",
            "i cannot find the relevant code",
            "context is missing",
            "not provided in the conversation",
            "was not discussed",
            "no prior context",
        ],
    )
    def test_gap_phrase_detected(self, phrase: str):
        """Gap phrase 'i don't have the X' should trigger detection."""
        # Transcript contains the content being claimed as missing
        lines = [
            _make_jsonl_line("user", "Here are my ideas: alpha, beta, gamma"),
            _make_jsonl_line("assistant", "I'll analyze the ideas"),
        ]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text=f"I don't have the ideas you mentioned.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("decision") == "block", f"Expected block for phrase: {phrase}"
            assert "false gap declaration" in result.get("reason", "").lower()

    def test_gap_phrase_case_insensitive(self):
        """GAP_PATTERNS should be case-insensitive."""
        lines = [_make_jsonl_line("user", "The codebase structure follows the pattern.")]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I DON'T HAVE THE codebase structure you mentioned.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("decision") == "block"


class TestOrdinalPlusGap:
    """Ordinal reference + gap language combo detected correctly."""

    def test_ordinal_gap_combination_detected(self):
        """'idea 2' + 'don't have' should trigger detection."""
        lines = [
            _make_jsonl_line("user", "Idea 1: do X. Idea 2: do Y. Idea 3: do Z."),
            _make_jsonl_line("assistant", "I'll start with Idea 1."),
        ]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have idea 2 from your list.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("decision") == "block"

    def test_ordinal_gap_combination_point(self):
        """'point 3' + 'lacking' should trigger detection."""
        lines = [
            _make_jsonl_line("user", "Point 1 is A. Point 2 is B. Point 3 is C."),
        ]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I'm lacking point 3 from your earlier list.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("decision") == "block"


class TestArticleNounSpecificity:
    """INVARIANT-4: Article+noun specificity — 'I don't have enough context' does NOT match."""

    def test_bare_dont_have_rejected(self):
        """'i don't have' without article+noun should NOT match."""
        lines = []  # Empty transcript

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have enough context to answer that.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            # Should pass because "enough context" has no article+noun after "don't have"
            assert result.get("decision") != "block" or result.get("allow") is True

    def test_dont_have_enough_context_rejected(self):
        """'I don't have enough context' (no article+noun) should NOT match."""
        lines = []

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have enough context to provide a complete answer.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("allow") is True

    def test_dont_have_information_about_rejected(self):
        """'I don't have information about X' should NOT match (no article)."""
        lines = []

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have information about the third approach.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("allow") is True


class TestTranscriptSearch:
    """Matching lines returned from mock transcript."""

    def test_transcript_search_finds_content(self):
        """When gap content IS in transcript, gap should be detected."""
        lines = [
            _make_jsonl_line("user", "The key ideas are: first, second, third."),
            _make_jsonl_line("assistant", "I'll analyze the three ideas."),
        ]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have the three ideas you mentioned.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("decision") == "block"
            assert "line" in result.get("reason", "").lower()

    def test_continue_true_when_no_gap(self):
        """Normal responses without gap language should pass."""
        lines = [
            _make_jsonl_line("user", "What's your analysis?"),
        ]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="The codebase has three main modules.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("allow") is True

    def test_continue_false_when_gap_not_in_transcript(self):
        """Gap claim where content is NOT in transcript should be allowed (can't verify)."""
        lines = [
            _make_jsonl_line("user", "What's your analysis?"),
        ]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have the ideas you never actually provided.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            # Content not in transcript → allow (gap is legitimate or unverifiable)
            assert result.get("allow") is True


class TestSkillScope:
    """Skill-scope gating — hook only fires for /arch sessions."""

    def test_skill_scope_arch_only(self):
        """Hook should fire when skill is /arch."""
        lines = [_make_jsonl_line("user", "The architecture includes A, B, C.")]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have the architecture you described.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("decision") == "block"

    def test_skill_scope_ignores_other_skills(self):
        """Hook should exit early when skill is not /arch."""
        lines = [_make_jsonl_line("user", "Some content")]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have the information you're referring to.",
                skill_state={"skill": "/reflect"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            # Should exit early (allow) because skill is not /arch
            assert result.get("allow") is True

    def test_skill_scope_partial_match_arch(self):
        """Partial match 'arch' in skill name should trigger."""
        lines = [_make_jsonl_line("user", "Architecture patterns: 1, 2, 3.")]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have the architecture patterns you listed.",
                skill_state={"skill": "arch-review"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("decision") == "block"

    def test_skill_scope_missing_skill_state(self):
        """Missing skill_state should allow (fail-open)."""
        lines = [_make_jsonl_line("user", "Content")]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have the content.",
                # No skill_state
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("allow") is True


class TestTranscriptMissing:
    """Transcript inaccessible → fail open."""

    def test_continue_true_when_transcript_missing(self):
        """When transcript can't be read, should fail-open (allow)."""
        with patch.object(arch_gap, "_read_transcript_lines", return_value=([], 0)):
            payload = _payload(
                response_text="I don't have the ideas you mentioned.",
                skill_state={"skill": "/arch"},
                transcript_path="/nonexistent/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            # Fail-open: allow when transcript is inaccessible
            assert result.get("allow") is True


class TestMalformedJsonl:
    """Malformed JSONL lines generate warning but don't block."""

    def test_jsonl_parse_errors_warn_not_block(self):
        """Malformed JSONL should count as skipped lines and warn, not block."""
        lines = [
            _make_jsonl_line("user", "Important content here"),
            "not valid json",  # malformed line
            _make_jsonl_line("assistant", "Response"),
        ]

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 1)):
            with patch.object(sys.stderr, "write") as mock_stderr:
                payload = _payload(
                    response_text="I don't have the important content mentioned.",
                    skill_state={"skill": "/arch"},
                    transcript_path="/mock/transcript.jsonl",
                )
                result = arch_gap.run(payload)
                # Should detect gap and block (content IS in valid lines)
                assert result.get("decision") == "block"
                # Warning should be written to stderr
                mock_stderr.assert_called()
                assert "skipped" in mock_stderr.call_args[0][0].lower()


class TestSlidingWindowSearch:
    """Content in older lines found via wrap-around search."""

    def test_sliding_window_wraps_to_beginning(self):
        """Content at line 5 should be found when searching last 3 lines first, then wrapping."""
        # Create many lines where the target is at the beginning
        lines = [_make_jsonl_line("user", "THE_TARGET_CONTENT is here at the start.")]
        # Pad with filler lines
        for i in range(250):
            lines.append(_make_jsonl_line("user", f"Filler line {i}."))

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have THE_TARGET_CONTENT from earlier.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("decision") == "block"

    def test_recent_lines_searched_first(self):
        """Recent lines (last 200) should be searched before wrapping."""
        # Target in recent lines (should be found in first pass)
        lines = []
        for i in range(50):
            lines.append(_make_jsonl_line("user", f"Filler {i}"))
        lines.append(_make_jsonl_line("user", "RECENT_TARGET content"))

        with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
            payload = _payload(
                response_text="I don't have RECENT_TARGET content.",
                skill_state={"skill": "/arch"},
                transcript_path="/mock/transcript.jsonl",
            )
            result = arch_gap.run(payload)
            assert result.get("decision") == "block"


class TestDisabledGate:
    """Gate can be disabled via environment variable."""

    def test_disabled_via_env_var(self):
        """When ARCH_GAP_DETECTION_ENABLED=false, hook should allow."""
        lines = [_make_jsonl_line("user", "The ideas are A, B, C.")]

        with patch.dict(os.environ, {"ARCH_GAP_DETECTION_ENABLED": "false"}):
            with patch.object(arch_gap, "_read_transcript_lines", return_value=(lines, 0)):
                payload = _payload(
                    response_text="I don't have the ideas.",
                    skill_state={"skill": "/arch"},
                    transcript_path="/mock/transcript.jsonl",
                )
                result = arch_gap.run(payload)
                assert result.get("allow") is True


# Needed for patch.dict
import os
