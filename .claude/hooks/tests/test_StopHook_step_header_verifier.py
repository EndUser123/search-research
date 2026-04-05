#!/usr/bin/env python3
"""Tests for StopHook_step_header_verifier.py."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from StopHook_step_header_verifier import (
    _normalize_step_name,
    _verify_step_headers,
    _extract_skill_name,
    _parse_workflow_steps,
    run,
)


class TestNormalizeStepName:
    """Tests for _normalize_step_name helper."""

    def test_hyphenated_step(self):
        """Hyphenated steps are converted to uppercase with underscores."""
        assert _normalize_step_name("tier-evidence-tagging") == "TIER_EVIDENCE_TAGGING"

    def test_space_separated_step(self):
        """Space-separated steps are converted to uppercase with underscores."""
        assert _normalize_step_name("tier evidence tagging") == "TIER_EVIDENCE_TAGGING"

    def test_already_uppercase(self):
        """Already uppercase steps remain unchanged."""
        assert _normalize_step_name("TIER_EVIDENCE_TAGGING") == "TIER_EVIDENCE_TAGGING"

    def test_mixed_case(self):
        """Mixed case steps are normalized to uppercase."""
        assert _normalize_step_name("Tier_Evidence_Tagging") == "TIER_EVIDENCE_TAGGING"


class TestExtractSkillName:
    """Tests for _extract_skill_name helper."""

    def test_invoking_pattern(self):
        """'Invoking {skill} skill' pattern extracts skill name."""
        response = "Invoking debugRCA skill to analyze the issue..."
        assert _extract_skill_name(response) == "debugRCA"

    def test_skill_invoked_pattern(self):
        """'Skill {skill} invoked' pattern extracts skill name."""
        response = "Skill code invoked for implementation."
        assert _extract_skill_name(response) == "code"

    def test_calling_pattern(self):
        """'Calling /{skill}' pattern extracts skill name."""
        response = "Calling /search to find relevant files"
        assert _extract_skill_name(response) == "search"

    def test_no_skill_detected(self):
        """No pattern match returns None."""
        response = "Running some analysis on the codebase."
        assert _extract_skill_name(response) is None


class TestVerifyStepHeaders:
    """Tests for _verify_step_headers helper."""

    def test_all_steps_found(self):
        """All required steps found in response returns complete=True."""
        response = "[STEP_ONE] completed.\n## STEP_TWO done."
        required = ["STEP_ONE", "STEP_TWO"]
        complete, missing, extra = _verify_step_headers(response, required)
        assert complete is True
        assert missing == []
        assert extra == []

    def test_missing_steps(self):
        """Missing required steps returns complete=False with missing list."""
        response = "[STEP_ONE] completed."
        required = ["STEP_ONE", "STEP_TWO", "STEP_THREE"]
        complete, missing, extra = _verify_step_headers(response, required)
        assert complete is False
        assert "STEP_TWO" in missing
        assert "STEP_THREE" in missing
        assert len(missing) == 2

    def test_extra_steps_detected(self):
        """Extra steps found but not required are detected."""
        response = "[STEP_ONE] [EXTRA_STEP] completed."
        required = ["STEP_ONE"]
        complete, missing, extra = _verify_step_headers(response, required)
        assert complete is True  # Required step is present
        # Extra steps are tracked separately

    def test_normalized_step_matching(self):
        """Steps match regardless of hyphen/underscore format."""
        response = "[TIER_EVIDENCE_TAGGING] completed."
        required = ["tier-evidence-tagging"]
        complete, missing, extra = _verify_step_headers(response, required)
        assert complete is True
        assert missing == []

    def test_no_required_steps(self):
        """Empty required steps list always returns complete."""
        response = "[SOME_STEP] found."
        complete, missing, extra = _verify_step_headers(response, [])
        assert complete is True

    def test_no_headers_found(self):
        """No headers in response returns complete=False for any required."""
        response = "Just some regular text without step markers."
        required = ["STEP_ONE"]
        complete, missing, extra = _verify_step_headers(response, required)
        assert complete is False
        assert "STEP_ONE" in missing


class TestParseWorkflowSteps:
    """Tests for _parse_workflow_steps helper."""

    def test_parse_workflow_steps_from_content(self, monkeypatch, tmp_path):
        """Parses workflow_steps from YAML frontmatter."""
        skill_file = tmp_path / "test_skill" / "SKILL.md"
        skill_file.parent.mkdir()
        skill_file.write_text("""---
name: test-skill
workflow_steps:
  - analyze
  - implement
  - verify
---
# Skill content
""")
        steps = _parse_workflow_steps(skill_file)
        assert steps == ["analyze", "implement", "verify"]

    def test_no_frontmatter(self, tmp_path):
        """No YAML frontmatter returns empty list."""
        skill_file = tmp_path / "test.md"
        skill_file.write_text("# No frontmatter here")
        steps = _parse_workflow_steps(skill_file)
        assert steps == []

    def test_no_workflow_steps(self, tmp_path):
        """Frontmatter without workflow_steps returns empty list."""
        skill_file = tmp_path / "test.md"
        skill_file.write_text("""---
name: test-skill
description: Just a skill
---
""")
        steps = _parse_workflow_steps(skill_file)
        assert steps == []


class TestRun:
    """Tests for run() entry point."""

    def test_disabled_returns_allow(self, monkeypatch):
        """When ENABLED=false, returns allow."""
        monkeypatch.setenv("STEP_HEADER_VERIFIER_ENABLED", "false")
        data = {"assistant_response": "Some response."}
        result = run(data)
        assert result is not None
        assert result.get("allow") is True

    def test_empty_response_returns_allow(self):
        """Empty response is allowed through."""
        data = {"assistant_response": ""}
        result = run(data)
        assert result is not None
        assert result.get("allow") is True

    def test_no_skill_detected_returns_allow(self):
        """Response without skill invocation is allowed."""
        data = {"assistant_response": "Just doing some work here."}
        result = run(data)
        assert result is not None
        assert result.get("allow") is True

    def test_no_matching_skill_file_returns_allow(self, monkeypatch):
        """Skill detected but no SKILL.md found - allowed."""
        # Mock _find_skill_file to return None
        monkeypatch.setattr(
            "StopHook_step_header_verifier._find_skill_file",
            lambda name: None,
        )
        data = {"assistant_response": "Invoking unknown-skill skill..."}
        result = run(data)
        assert result is not None
        assert result.get("allow") is True

    def test_all_steps_complete_returns_allow(self, monkeypatch, tmp_path):
        """All documented steps found - returns allow."""
        # Create a mock skill file
        skill_file = tmp_path / "skills" / "testskill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("""---
name: test-skill
workflow_steps:
  - analyze
  - implement
---
""")
        monkeypatch.setattr(
            "StopHook_step_header_verifier._find_skill_file",
            lambda name: skill_file if name == "testskill" else None,
        )
        data = {
            "assistant_response": "Invoking testskill skill...\n[ANALYZE] done.\n[IMPLEMENT] done."
        }
        result = run(data)
        assert result is not None
        assert result.get("allow") is True

    def test_missing_steps_returns_warning_in_warn_mode(self, monkeypatch, tmp_path):
        """Missing steps in warn mode returns allow with warning."""
        monkeypatch.setenv("STEP_HEADER_VERIFIER_MODE", "warn")
        skill_file = tmp_path / "skills" / "testskill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("""---
name: test-skill
workflow_steps:
  - analyze
  - implement
  - verify
---
""")
        monkeypatch.setattr(
            "StopHook_step_header_verifier._find_skill_file",
            lambda name: skill_file if name == "testskill" else None,
        )
        data = {
            "assistant_response": "Invoking testskill skill...\n[ANALYZE] done."
        }
        result = run(data)
        assert result is not None
        assert result.get("allow") is True
        assert "Missing" in result.get("reason", "")

    def test_missing_steps_returns_block_in_block_mode(self, monkeypatch, tmp_path):
        """Missing steps in block mode returns allow=False."""
        # Reset the module-level MODE variable and set env
        import StopHook_step_header_verifier
        monkeypatch.setenv("STEP_HEADER_VERIFIER_MODE", "block", prepend=False)
        StopHook_step_header_verifier.MODE = "block"
        skill_file = tmp_path / "skills" / "testskill" / "SKILL.md"
        skill_file.parent.mkdir(parents=True)
        skill_file.write_text("""---
name: test-skill
workflow_steps:
  - analyze
  - implement
---
""")
        monkeypatch.setattr(
            "StopHook_step_header_verifier._find_skill_file",
            lambda name: skill_file if name == "testskill" else None,
        )
        data = {
            "assistant_response": "Invoking testskill skill...\n[ANALYZE] done."
        }
        result = run(data)
        assert result is not None
        assert result.get("allow") is False
        assert "Missing" in result.get("reason", "")
