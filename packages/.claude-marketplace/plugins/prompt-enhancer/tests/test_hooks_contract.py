"""
Tests for prompt_enhancer_hook.py entrypoint contract (stdin/stdout JSON).

Validates that each classification path (bypass / clear / ambiguous / confirm /
prohibited) produces the expected stdout JSON structure and, where relevant,
writes or clears the active_enhancement.json artifact.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from conftest import (
    _active_enhancement_path,
    _hook_invoke,
    _seed_enhancement,
)


# Absolute path to the hook script (independent of sys.path during subprocess call).
PLUGIN_ROOT = Path(__file__).parent.parent
HOOK_PATH = PLUGIN_ROOT / "hooks" / "prompt-enhancer_UserPromptSubmit.py"


class TestHookBypass:
    """bypass path: !raw delete everything → {} stdout, no artifact."""

    def test_bypass_raw_prefix_no_artifact(self, _isolated_home):
        tmp_path, terminal_id = _isolated_home
        output = _hook_invoke(HOOK_PATH, {"prompt": "!raw delete everything"})
        assert output == {}, f"bypass stdout should be empty dict, got: {output}"
        artifact_path = _active_enhancement_path(tmp_path, terminal_id)
        assert not artifact_path.exists(), "bypass should not create active_enhancement.json"

    def test_bypass_nope_prefix(self, _isolated_home):
        output = _hook_invoke(HOOK_PATH, {"prompt": "*nope delete the database"})
        assert output == {}

    def test_bypass_prompt_enhancer_off(self, _isolated_home):
        output = _hook_invoke(HOOK_PATH, {"prompt": "prompt-enhancer: off delete everything"})
        assert output == {}


class TestHookClear:
    """clear path: refactor auth.py → {} stdout."""

    def test_clear_stdout_empty(self, _isolated_home):
        output = _hook_invoke(HOOK_PATH, {"prompt": "refactor auth.py for better testability"})
        assert output == {}, f"clear stdout should be empty dict, got: {output}"

    def test_clear_no_artifact(self, _isolated_home):
        tmp_path, terminal_id = _isolated_home
        _hook_invoke(HOOK_PATH, {"prompt": "refactor auth.py for better testability"})
        artifact_path = _active_enhancement_path(tmp_path, terminal_id)
        assert not artifact_path.exists(), "clear should not create active_enhancement.json"


class TestHookProhibited:
    """prohibited path: delete everything → block: true and non-empty stopReason."""

    def test_prohibited_block_flag(self, _isolated_home):
        output = _hook_invoke(HOOK_PATH, {"prompt": "delete everything"})
        hso = output.get("hookSpecificOutput", {})
        assert hso.get("block") is True, f"prohibited should set block=True, got: {hso}"
        stop_reason = hso.get("stopReason", "")
        assert stop_reason, "stopReason should be non-empty"
        assert "prohibited" in stop_reason.lower(), f"stopReason should mention 'prohibited': {stop_reason}"

    def test_prohibited_no_artifact(self, _isolated_home):
        tmp_path, terminal_id = _isolated_home
        _hook_invoke(HOOK_PATH, {"prompt": "delete everything"})
        artifact_path = _active_enhancement_path(tmp_path, terminal_id)
        assert not artifact_path.exists(), "prohibited should clear active_enhancement.json"


class TestHookAmbiguous:
    """ambiguous path: fix it → NO injection (referent inference removed
    2026-07-11); artifact still written for observability."""

    def test_ambiguous_injects_nothing(self, _isolated_home):
        # Regression for the wrong-anchor incident: the hook must NOT guess
        # what "it" means — the model resolves it from conversation history.
        output = _hook_invoke(HOOK_PATH, {"prompt": "fix it"})
        assert output == {}, (
            f"ambiguous prompt must inject nothing (model resolves referents), got: {output}"
        )

    def test_ambiguous_writes_artifact(self, _isolated_home):
        tmp_path, terminal_id = _isolated_home
        _hook_invoke(HOOK_PATH, {"prompt": "fix it"})
        artifact_path = _active_enhancement_path(tmp_path, terminal_id)
        assert artifact_path.exists(), "ambiguous should write active_enhancement.json"

    def test_ambiguous_artifact_has_required_fields(self, _isolated_home):
        tmp_path, terminal_id = _isolated_home
        _hook_invoke(HOOK_PATH, {"prompt": "fix it"})
        artifact_path = _active_enhancement_path(tmp_path, terminal_id)
        data = json.loads(artifact_path.read_text(encoding="utf-8"))
        assert "clarified_intent" in data, "artifact should have clarified_intent"
        assert "missing_details" in data, "artifact should have missing_details"


class TestHookConfirm:
    """confirm path: delete the database → AskUserQuestion + additionalContext."""

    def test_confirm_has_additional_context(self, _isolated_home):
        output = _hook_invoke(HOOK_PATH, {"prompt": "delete the database"})
        hso = output.get("hookSpecificOutput", {})
        ctx = hso.get("additionalContext", "")
        assert ctx, "confirm should produce non-empty additionalContext"
        # The "delete the database" prompt produces missing_details with "confirm target scope",
        # so the context should mention the intent.
        assert "delete" in ctx.lower(), f"additionalContext should mention 'delete': {ctx}"

    def test_confirm_has_ask_user_question(self, _isolated_home):
        output = _hook_invoke(HOOK_PATH, {"prompt": "delete the database"})
        hso = output.get("hookSpecificOutput", {})
        ask = hso.get("AskUserQuestion")
        assert ask is not None, f"confirm should include AskUserQuestion, got: {hso}"
        question = ask.get("question", "")
        assert question, "AskUserQuestion should have a non-empty question"
        assert len(ask.get("options", [])) == 2, "AskUserQuestion should have 2 options"
        # The question should ask for confirmation of the target.
        assert "confirm" in question.lower() or "target" in question.lower(), (
            f"question should mention confirm or target, got: {question}"
        )

    def test_confirm_writes_artifact(self, _isolated_home):
        tmp_path, terminal_id = _isolated_home
        _hook_invoke(HOOK_PATH, {"prompt": "delete the database"})
        artifact_path = _active_enhancement_path(tmp_path, terminal_id)
        assert artifact_path.exists(), "confirm should write active_enhancement.json"


class TestHookConfirmQuestionRegression:
    """Confirm-question regression: question content is sensible for all missing_details shapes."""

    def test_confirm_question_with_standard_detail(self, _isolated_home):
        """The 'delete the database' prompt produces missing_details that do NOT start with
        'confirm ' so they are included verbatim in the question text. No duplication occurs."""
        output = _hook_invoke(HOOK_PATH, {"prompt": "delete the database"})
        hso = output.get("hookSpecificOutput", {})
        question = (hso.get("AskUserQuestion") or {}).get("question", "")
        # "confirm target scope before executing" is the standard detail from enhance().
        # It does not start with "confirm " so it is verbatim in the question.
        assert "confirm target scope" in question.lower(), (
            f"question should include the standard detail: {question}"
        )
        assert "confirm confirm" not in question.lower(), f"no duplication expected: {question}"

    
    def test_delete_database_confirm_question_content(self, _isolated_home):
        """delete the database → confirm question asks to confirm the target scope."""
        output = _hook_invoke(HOOK_PATH, {"prompt": "delete the database"})
        hso = output.get("hookSpecificOutput", {})
        question = (hso.get("AskUserQuestion") or {}).get("question", "")
        assert question, "question must be non-empty"
        # Must confirm the target (not duplicate "confirm confirm").
        assert "confirm" in question.lower(), f"question should ask to confirm: {question}"
        assert "confirm confirm" not in question.lower(), f"no duplication: {question}"