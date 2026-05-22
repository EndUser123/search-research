"""
Tests for prompt_enhancer_precompact_hook.py entrypoint contract.

Validates:
- PreCompact with no active_enhancement.json → fixed approve + empty additionalContext
- PreCompact with a seeded active_enhancement.json → decision=approve + preserved lines
- Full reinjection chain: hook writes artifact → PreCompact reads it back
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from conftest import _active_enhancement_path, _hook_invoke, _seed_enhancement


PLUGIN_ROOT = Path(__file__).parent.parent
HOOK_PATH = PLUGIN_ROOT / "scripts" / "hooks" / "prompt_enhancer_hook.py"
PRECOMPACT_PATH = PLUGIN_ROOT / "scripts" / "hooks" / "prompt_enhancer_precompact_hook.py"


class TestPreCompactNoState:
    """PreCompact with no active_enhancement.json → approve, no block."""

    def test_no_state_approves(self, _isolated_home):
        output = _hook_invoke(PRECOMPACT_PATH, {})
        assert output["decision"] == "approve"
        assert output["reason"] == "No active enhancement to preserve"
        # additionalContext is omitted when there is nothing to preserve.
        assert "additionalContext" not in output or output.get("additionalContext") == ""


class TestPreCompactWithState:
    """PreCompact with a seeded active_enhancement.json → decision=approve + preserved lines."""

    def test_with_state_preserves_intent(self, _isolated_home):
        tmp_path, terminal_id = _isolated_home
        _seed_enhancement(
            tmp_path,
            terminal_id,
            missing_details=["target database name"],
            clarified_intent="delete the database",
            inferred_subject="the database",
        )
        output = _hook_invoke(PRECOMPACT_PATH, {})
        assert output["decision"] == "approve"
        ctx = output["additionalContext"]
        assert "delete the database" in ctx, f"additionalContext should contain clarified_intent: {ctx}"
        assert "target database name" in ctx, f"additionalContext should contain missing_details: {ctx}"
        assert "Prompt Clarification (preserved from prior turn)" in ctx

    def test_with_state_preserves_flags(self, _isolated_home):
        tmp_path, terminal_id = _isolated_home
        _seed_enhancement(
            tmp_path,
            terminal_id,
            missing_details=[],
            safety_flags=["high-impact verb: delete database"],
        )
        output = _hook_invoke(PRECOMPACT_PATH, {})
        ctx = output["additionalContext"]
        assert "high-impact verb" in ctx, f"additionalContext should contain safety_flags: {ctx}"

    def test_with_state_preserves_tokens(self, _isolated_home):
        tmp_path, terminal_id = _isolated_home
        _seed_enhancement(
            tmp_path,
            terminal_id,
            missing_details=[],
            estimated_tokens=42,
        )
        output = _hook_invoke(PRECOMPACT_PATH, {})
        ctx = output["additionalContext"]
        assert "~42" in ctx, f"additionalContext should contain estimated_tokens: {ctx}"


class TestPreCompactReinjectIntegration:
    """Full chain: hook writes artifact → PreCompact reads it back and emits clarification."""

    def test_reinject_integration(self, _isolated_home):
        tmp_path, terminal_id = _isolated_home
        # Step 1: invoke the main hook with a confirm-classified prompt.
        hook_output = _hook_invoke(HOOK_PATH, {"prompt": "delete the database"})
        # The hook should have written the artifact.
        artifact_path = _active_enhancement_path(tmp_path, terminal_id)
        assert artifact_path.exists(), "hook should write active_enhancement.json"

        # Step 2: invoke PreCompact against the same isolated HOME.
        compact_output = _hook_invoke(PRECOMPACT_PATH, {})
        assert compact_output["decision"] == "approve"
        ctx = compact_output["additionalContext"]
        # The preserved clarification should appear in PreCompact's additionalContext.
        assert "delete the database" in ctx, (
            f"PreCompact additionalContext should contain the clarified intent, got: {ctx}"
        )
        # PreCompact should also include the preserved header.
        assert "Prompt Clarification (preserved from prior turn)" in ctx