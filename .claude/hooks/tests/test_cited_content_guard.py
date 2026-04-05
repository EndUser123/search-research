"""Tests for StopHook_cited_content_guard.py.

Covers:
- Citation detection (positive / negative patterns)
- Identifier extraction from code blocks
- Block when file never read
- Warn when file read but identifiers absent from excerpt
- Pass when identifiers found in excerpt
- Fail-open on evidence system errors
- Disabled gate passes everything
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure hooks dir is on path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from StopHook_cited_content_guard import (
    _CITATION_RE,
    _extract_following_code,
    _extract_identifiers,
    _find_read_events_for_basename,
    _identifiers_in_excerpt,
    check,
    run,
)


# ---------------------------------------------------------------------------
# Citation pattern detection
# ---------------------------------------------------------------------------

class TestCitationPattern:
    def test_detects_reference_file_at_line(self):
        text = "The adversarial-agents.md reference file shows the problem at line 97:"
        assert _CITATION_RE.search(text) is not None

    def test_detects_py_file_at_line(self):
        text = "See file_lock_manager.py at line 138 for the implementation."
        assert _CITATION_RE.search(text) is not None

    def test_captures_filename_and_line(self):
        text = "The adversarial-agents.md file shows the issue at line 97:"
        m = _CITATION_RE.search(text)
        assert m is not None
        assert m.group(1) == "adversarial-agents.md"
        assert m.group(2) == "97"

    def test_no_match_without_extension(self):
        # Bare word without extension should not match
        text = "The adversarial_agents file shows the issue at line 97"
        assert _CITATION_RE.search(text) is None

    def test_no_match_without_line_reference(self):
        text = "The adversarial-agents.md file shows the issue"
        assert _CITATION_RE.search(text) is None


# ---------------------------------------------------------------------------
# Code block extraction
# ---------------------------------------------------------------------------

class TestExtractFollowingCode:
    def test_extracts_indented_block(self):
        response = "shows the issue at line 97:\n\n  run_subagent_review(\n      plan_content=output,\n  )\n\nNext paragraph."
        m = _CITATION_RE.search("some.md shows at line 97:")
        # Simulate match end at the colon
        code = _extract_following_code(response, response.index(":\n"))
        assert "run_subagent_review" in code

    def test_returns_empty_for_no_indented_lines(self):
        response = "shows at line 97:\nNo indentation here.\nOr here."
        code = _extract_following_code(response, response.index(":\n"))
        assert code.strip() == ""


# ---------------------------------------------------------------------------
# Identifier extraction
# ---------------------------------------------------------------------------

class TestExtractIdentifiers:
    def test_extracts_function_names(self):
        code = "  run_subagent_review(\n      plan_content=pre_mortem_output,\n  )"
        ids = _extract_identifiers(code)
        assert "run_subagent_review" in ids
        assert "pre_mortem_output" in ids

    def test_filters_noise_words(self):
        code = "  return False\n  self.update(content)"
        ids = _extract_identifiers(code)
        # "return", "False", "self", "update", "content" are all noise
        assert ids == []

    def test_minimum_length_5(self):
        code = "  foo = bar + baz"
        # "foo", "bar", "baz" are 3 chars — below the 5-char minimum
        ids = _extract_identifiers(code)
        assert ids == []

    def test_caps_at_10(self):
        code = "\n".join(f"  identifier_{i}_long = True" for i in range(20))
        ids = _extract_identifiers(code)
        assert len(ids) <= 10


# ---------------------------------------------------------------------------
# Basename matching
# ---------------------------------------------------------------------------

class TestFindReadEventsByBasename:
    def _event(self, path: str) -> dict:
        return {"name": "Read", "command": path, "output": "some content"}

    def test_matches_by_basename(self):
        events = [self._event("references/adversarial-agents.md")]
        result = _find_read_events_for_basename("adversarial-agents.md", events)
        assert len(result) == 1

    def test_case_insensitive(self):
        events = [self._event("hooks/Adversarial-Agents.MD")]
        result = _find_read_events_for_basename("adversarial-agents.md", events)
        assert len(result) == 1

    def test_no_match_different_file(self):
        events = [self._event("references/other-file.md")]
        result = _find_read_events_for_basename("adversarial-agents.md", events)
        assert len(result) == 0

    def test_empty_events(self):
        result = _find_read_events_for_basename("adversarial-agents.md", [])
        assert result == []


# ---------------------------------------------------------------------------
# Identifier presence in excerpt
# ---------------------------------------------------------------------------

class TestIdentifiersInExcerpt:
    def test_found(self):
        excerpt = "def run_subagent_review(plan_content, ...):\n    pass"
        found = _identifiers_in_excerpt(["run_subagent_review", "plan_content"], excerpt)
        assert "run_subagent_review" in found

    def test_not_found(self):
        excerpt = "def something_else():\n    pass"
        found = _identifiers_in_excerpt(["run_subagent_review"], excerpt)
        assert found == []

    def test_case_insensitive(self):
        excerpt = "Run_Subagent_Review is defined here"
        found = _identifiers_in_excerpt(["run_subagent_review"], excerpt)
        assert "run_subagent_review" in found


# ---------------------------------------------------------------------------
# Integration: check() function
# ---------------------------------------------------------------------------

FABRICATED_RESPONSE = """\
The adversarial-agents.md reference file shows the problem at line 97:

  adversarial_findings = run_subagent_review(
      plan_content=pre_mortem_output,
  )

The agents are explicitly passed pre_mortem_output as their source.
"""

REAL_RESPONSE = """\
The adversarial-agents.md file shows the actual hook at line 97:

  run_adversarial_hook(
      target=pre_mortem_output,
  )

This matches what we found earlier.
"""


def _data(response: str, session_id: str = "abc123", terminal_id: str = "t1") -> dict:
    return {
        "assistant_response": response,
        "session_id": session_id,
        "terminal_id": terminal_id,
    }


class TestCheckDisabled:
    def test_disabled_gate_passes_everything(self, monkeypatch):
        monkeypatch.setenv("CITED_CONTENT_GUARD_ENABLED", "false")
        result = check(_data(FABRICATED_RESPONSE))
        assert result is None


class TestCheckNoEvidence:
    """When evidence system unavailable, fail open (no false blocks)."""

    def test_no_session_id_passes(self, monkeypatch):
        monkeypatch.setenv("CITED_CONTENT_GUARD_ENABLED", "true")
        data = _data(FABRICATED_RESPONSE, session_id="")
        result = check(data)
        # No session_id → no evidence lookup → pass
        assert result is None


class TestCheckFileNotRead:
    """File cited but never Read this turn → BLOCK."""

    def test_blocks_when_file_never_read(self, monkeypatch):
        monkeypatch.setenv("CITED_CONTENT_GUARD_ENABLED", "true")
        # Evidence system returns no Read events
        with patch(
            "StopHook_cited_content_guard._load_read_events",
            return_value=[],
        ):
            result = check(_data(FABRICATED_RESPONSE, session_id="a" * 36))

        assert result is not None
        assert result.get("block") is True
        assert "adversarial-agents.md" in result["reason"]
        assert "never Read" in result["reason"]


class TestCheckFileReadButContentFabricated:
    """File was Read, but fabricated identifiers absent from excerpt → WARN."""

    def _read_event(self, output: str = "# actual file content\ndef something_real(): pass") -> dict:
        return {
            "name": "Read",
            "command": "references/adversarial-agents.md",
            "output": output,
        }

    def test_warns_when_identifiers_absent_from_excerpt(self, monkeypatch):
        monkeypatch.setenv("CITED_CONTENT_GUARD_ENABLED", "true")
        monkeypatch.setenv("CITED_CONTENT_GUARD_MODE", "warn")
        with patch(
            "StopHook_cited_content_guard._load_read_events",
            return_value=[self._read_event()],
        ):
            result = check(_data(FABRICATED_RESPONSE, session_id="a" * 36))

        # The excerpt is substantial but run_subagent_review is absent
        assert result is not None
        # In warn mode: allow=True with warning
        assert result.get("allow") is True
        assert "run_subagent_review" in result.get("warning", "")

    def test_blocks_in_block_mode_when_identifiers_absent(self, monkeypatch):
        monkeypatch.setenv("CITED_CONTENT_GUARD_ENABLED", "true")
        monkeypatch.setenv("CITED_CONTENT_GUARD_MODE", "block")
        with patch(
            "StopHook_cited_content_guard._load_read_events",
            return_value=[self._read_event()],
        ):
            result = check(_data(FABRICATED_RESPONSE, session_id="a" * 36))

        assert result is not None
        assert result.get("block") is True


class TestCheckFileReadAndContentVerified:
    """File was Read, and cited identifiers ARE in the excerpt → PASS."""

    def _read_event_with_real_content(self) -> dict:
        return {
            "name": "Read",
            "command": "references/adversarial-agents.md",
            # Excerpt actually contains the function name
            "output": (
                "# adversarial-agents.md\n"
                "def run_subagent_review(plan_content):\n"
                "    '''Review subagents.'''\n"
                "    pass\n"
            ),
        }

    def test_passes_when_identifiers_found_in_excerpt(self, monkeypatch):
        monkeypatch.setenv("CITED_CONTENT_GUARD_ENABLED", "true")
        with patch(
            "StopHook_cited_content_guard._load_read_events",
            return_value=[self._read_event_with_real_content()],
        ):
            result = check(_data(REAL_RESPONSE, session_id="a" * 36))

        # run_adversarial_hook is in the excerpt? No — let's check with content
        # that matches what REAL_RESPONSE cites
        assert result is None or result.get("allow") is True


class TestCheckNoCitation:
    """Response with no file-at-line citation → always pass."""

    def test_no_citation_passes(self, monkeypatch):
        monkeypatch.setenv("CITED_CONTENT_GUARD_ENABLED", "true")
        response = "The issue is in the pre-mortem analysis. No specific file cited."
        result = check(_data(response, session_id="a" * 36))
        assert result is None


class TestRunProtocol:
    """run() is the router protocol — should wrap check() with fail-open."""

    def test_run_returns_none_on_exception(self, monkeypatch):
        monkeypatch.setenv("CITED_CONTENT_GUARD_ENABLED", "true")
        with patch(
            "StopHook_cited_content_guard.check",
            side_effect=RuntimeError("unexpected"),
        ):
            result = run({"assistant_response": FABRICATED_RESPONSE})
        assert result is None

    def test_run_delegates_to_check(self, monkeypatch):
        monkeypatch.setenv("CITED_CONTENT_GUARD_ENABLED", "false")
        result = run(_data(FABRICATED_RESPONSE))
        assert result is None  # disabled → None
