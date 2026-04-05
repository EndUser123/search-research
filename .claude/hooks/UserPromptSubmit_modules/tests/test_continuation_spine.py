"""Tests for continuation_spine module.

Tests cover:
1. Short affirmative detection
2. Long affirmative rejection (>6 words)
3. Non-affirmative rejection
4. Transcript reading
5. Proposal detection
6. Full hook behavior (spine fires + suppresses enhancers)
7. Dict format with suppress key is processed correctly
8. Integration test: suppression actually skips cognitive enhancers in run_hooks()
"""
from __future__ import annotations

import json
from pathlib import Path

from ..base import HookContext
from ..continuation_spine import (
    continuation_spine,
    get_last_assistant_message,
    is_concrete_proposal,
    is_short_affirmative,
)


class TestShortAffirmative:
    """Test is_short_affirmative detector."""

    def test_yes_variations(self):
        """Accept yes variations."""
        assert is_short_affirmative("yes")
        assert is_short_affirmative("yes.")
        assert is_short_affirmative("YES")
        assert is_short_affirmative("yep")
        assert is_short_affirmative("yeah")
        assert is_short_affirmative("ok")
        assert is_short_affirmative("okay")
        assert is_short_affirmative("sure")
        assert is_short_affirmative("sounds good")
        assert is_short_affirmative("go ahead")
        assert is_short_affirmative("proceed")
        assert is_short_affirmative("do it")
        assert is_short_affirmative("that works")
        assert is_short_affirmative("looks good")

    def test_long_affirmative_rejected(self):
        """Reject affirmatives with >6 words (has own intent signal)."""
        assert not is_short_affirmative("yes please implement all three changes")
        assert not is_short_affirmative("ok let's proceed with the plan")

    def test_non_affirmative_rejected(self):
        """Reject non-affirmative responses."""
        assert not is_short_affirmative("no")
        assert not is_short_affirmative("I think we should")
        assert not is_short_affirmative("what about")
        assert not is_short_affirmative("")

    def test_whitespace_tolerance(self):
        """Tolerate surrounding whitespace."""
        assert is_short_affirmative("  yes  ")
        assert is_short_affirmative("\n\tOK.\n")


class TestTranscriptReader:
    """Test get_last_assistant_message function."""

    def test_read_last_assistant_message(self, tmp_path):
        """Extract last assistant message from JSONL."""
        transcript_file = tmp_path / "transcript.jsonl"
        transcript_file.write_text('{"type": "user", "message": {"content": [{"type": "text", "text": "hello"}]}}\n')
        with transcript_file.open("a") as f:
            f.write('{"type": "assistant", "message": {"content": [{"type": "text", "text": "I can help"}]}}\n')
            f.write('{"type": "user", "message": {"content": [{"type": "text", "text": "thanks"}]}}\n')
            f.write('{"type": "assistant", "message": {"content": [{"type": "text", "text": "Here is a plan:"}]}}\n')

        result = get_last_assistant_message(str(transcript_file))
        assert result == "Here is a plan:"

    def test_missing_file(self):
        """Return None for missing transcript file."""
        assert get_last_assistant_message("/nonexistent/path.json") is None

    def test_no_assistant_messages(self, tmp_path):
        """Return None when no assistant messages exist."""
        transcript_file = tmp_path / "transcript.jsonl"
        transcript_file.write_text('{"type": "user", "message": {"content": [{"type": "text", "text": "hello"}]}}\n')

        result = get_last_assistant_message(str(transcript_file))
        assert result is None

    def test_mixed_content_parts(self, tmp_path):
        """Extract text from mixed content parts."""
        transcript_file = tmp_path / "transcript.jsonl"
        transcript_file.write_text('{"type": "assistant", "message": {"content": [{"type": "tool_use", "id": "123"}, {"type": "text", "text": "Plan:"}]}}\n')

        result = get_last_assistant_message(str(transcript_file))
        assert result == "Plan:"

    def test_malformed_json_skipped(self, tmp_path):
        """Skip malformed JSON lines and continue searching."""
        transcript_file = tmp_path / "transcript.jsonl"
        transcript_file.write_text('{"type": "user", "message": {"content": [{"type": "text", "text": "hello"}]}}\n')
        with transcript_file.open("a") as f:
            f.write('invalid json line\n')
            f.write('{"type": "assistant", "message": {"content": [{"type": "text", "text": "found"}]}}\n')

        result = get_last_assistant_message(str(transcript_file))
        assert result == "found"


class TestProposalDetector:
    """Test is_concrete_proposal function."""

    def test_proposal_markers(self):
        """Detect proposal markers."""
        assert is_concrete_proposal("I'll create a new module")
        assert is_concrete_proposal("I could refactor this code")
        assert is_concrete_proposal("Would you like me to help?")
        assert is_concrete_proposal("We can proceed with the plan")
        assert is_concrete_proposal("Options: A or B")
        assert is_concrete_proposal("Option 1 is better")
        assert is_concrete_proposal("Step 1: Create file")
        assert is_concrete_proposal("Here's a plan:")
        assert is_concrete_proposal("Plan: Implement feature")
        # "I can implement" detected via numbered list, not marker

    def test_numbered_list_fallback(self):
        """Detect numbered/bulleted lists without explicit markers."""
        assert is_concrete_proposal("- First item\n- Second item")
        assert is_concrete_proposal("* Point one\n* Point two")
        assert is_concrete_proposal("1. Create file\n2. Run tests")
        assert is_concrete_proposal("1) First step\n2) Second step")

    def test_non_proposal_rejected(self):
        """Reject non-proposal text."""
        assert not is_concrete_proposal("Here's a summary of the changes")  # "Here's a" is not in our markers
        assert not is_concrete_proposal("")  # Empty
        assert not is_concrete_proposal("Just a question about the code")
        # "I can" removed from markers to avoid false positives
        assert not is_concrete_proposal("I can explain the code structure")  # Informational

    def test_i_can_with_numbered_list_detected(self):
        """'I can' with numbered list IS detected via fallback."""
        assert is_concrete_proposal("I can implement this feature:\n1. Create module\n2. Run tests")


class TestContinuationSpineHook:
    """Test continuation_spine hook function."""

    def test_short_affirmative_with_proposal_fires(self, tmp_path):
        """Spine fires when short affirmative + last assistant was proposal."""
        context = HookContext(
            prompt="yes",
            data={"transcript_path": str(self._create_transcript_with_proposal(tmp_path))},
        )
        result = continuation_spine(context)

        assert not result.is_empty()
        assert isinstance(result.context, dict)
        assert result.context["additionalContext"] == "Restate the goal and planned steps before proceeding."
        assert "assumption_surfacing" in result.context["suppress"]
        assert "outcome_anchoring" in result.context["suppress"]

    def test_long_affirmative_no_spine(self, tmp_path):
        """No spine for long affirmative (>6 words)."""
        context = HookContext(
            prompt="yes please implement all three changes",
            data={"transcript_path": str(self._create_transcript_with_proposal(tmp_path))},
        )
        result = continuation_spine(context)

        assert result.is_empty()

    def test_non_affirmative_no_spine(self, tmp_path):
        """No spine for non-affirmative prompt."""
        context = HookContext(
            prompt="I think we should",
            data={"transcript_path": str(self._create_transcript_with_proposal(tmp_path))},
        )
        result = continuation_spine(context)

        assert result.is_empty()

    def test_no_proposal_no_spine(self, tmp_path):
        """No spine when last assistant was not a proposal."""
        context = HookContext(
            prompt="yes",
            data={"transcript_path": str(self._create_transcript_without_proposal(tmp_path))},
        )
        result = continuation_spine(context)

        assert result.is_empty()

    def test_missing_transcript_no_spine(self):
        """No spine when transcript file is missing."""
        context = HookContext(
            prompt="yes",
            data={"transcript_path": "/nonexistent/transcript.jsonl"},
        )
        result = continuation_spine(context)

        assert result.is_empty()

    def test_all_cognitive_enhancers_suppressed(self, tmp_path):
        """Verify all 6 cognitive enhancers are in suppress list."""
        context = HookContext(
            prompt="ok",
            data={"transcript_path": str(self._create_transcript_with_proposal(tmp_path))},
        )
        result = continuation_spine(context)

        assert not result.is_empty()
        suppress_list = result.context.get("suppress", [])
        assert "assumption_surfacing" in suppress_list
        assert "outcome_anchoring" in suppress_list
        assert "inversion_prompting" in suppress_list
        assert "chestertons_fence" in suppress_list
        assert "calibrated_confidence" in suppress_list
        assert "socratic_decomposition" in suppress_list

    def test_dict_format_preserved(self, tmp_path):
        """Verify dict format is preserved (not normalized to string)."""
        context = HookContext(
            prompt="proceed.",
            data={"transcript_path": str(self._create_transcript_with_proposal(tmp_path))},
        )
        result = continuation_spine(context)

        assert not result.is_empty()
        assert isinstance(result.context, dict)  # Still a dict
        assert "additionalContext" in result.context
        assert "suppress" in result.context

    # Helper methods using pytest tmp_path fixture for auto-cleanup
    def _create_transcript_with_proposal(self, tmp_path: Path) -> Path:
        """Create temporary transcript with proposal."""
        transcript_file = tmp_path / "transcript_with_proposal.jsonl"
        transcript_file.write_text('{"type": "user", "message": {"content": [{"type": "text", "text": "help"}]}}\n')
        entry = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "I'll implement this feature with these steps:\n1. Create module\n2. Run tests"
                    }
                ]
            }
        }
        with transcript_file.open("a") as f:
            f.write(json.dumps(entry) + "\n")
        return transcript_file

    def _create_transcript_without_proposal(self, tmp_path: Path) -> Path:
        """Create temporary transcript without proposal."""
        transcript_file = tmp_path / "transcript_without_proposal.jsonl"
        transcript_file.write_text('{"type": "user", "message": {"content": [{"type": "text", "text": "help"}]}}\n')
        entry = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "Here is a summary of the code"
                    }
                ]
            }
        }
        with transcript_file.open("a") as f:
            f.write(json.dumps(entry) + "\n")
        return transcript_file


class TestSuppressionIntegration:
    """Integration test: verify suppress signal actually skips hooks in run_hooks()."""

    def test_suppression_skips_cognitive_enhancers(self, tmp_path):
        """When spine fires, cognitive enhancers should be skipped in run_hooks()."""
        from .. import registry

        # Track which hook functions were called
        called_hooks = []

        def mock_continuation_spine(ctx):
            called_hooks.append("continuation_spine")
            return continuation_spine(ctx)

        def mock_assumption_surfacing(ctx):
            called_hooks.append("assumption_surfacing")
            from ..base import HookResult
            return HookResult(context={"additionalContext": "test"}, tokens=0, priority=11.2)

        def mock_outcome_anchoring(ctx):
            called_hooks.append("outcome_anchoring")
            from ..base import HookResult
            return HookResult(context={"additionalContext": "test"}, tokens=0, priority=11.3)

        # Patch the registry with our mock functions
        original_hooks = registry.HOOKS.copy()
        try:
            registry.HOOKS["continuation_spine"] = mock_continuation_spine
            registry.HOOKS["assumption_surfacing"] = mock_assumption_surfacing
            registry.HOOKS["outcome_anchoring"] = mock_outcome_anchoring

            # Set priorities: continuation_spine (10.0) runs before enhancers (11.2, 11.3)
            registry.HOOK_PRIORITY["continuation_spine"] = 10.0
            registry.HOOK_PRIORITY["assumption_surfacing"] = 11.2
            registry.HOOK_PRIORITY["outcome_anchoring"] = 11.3

            # Run hooks with short affirmative + proposal transcript
            data = {"transcript_path": str(self._create_transcript_with_proposal(tmp_path))}
            results = registry.run_hooks(data, "yes")

            # Assert continuation_spine was called
            assert "continuation_spine" in called_hooks

            # Assert cognitive enhancers were NOT called (suppressed)
            assert "assumption_surfacing" not in called_hooks
            assert "outcome_anchoring" not in called_hooks

        finally:
            # Restore original hooks
            registry.HOOKS = original_hooks

    def _create_transcript_with_proposal(self, tmp_path: Path) -> Path:
        """Create temporary transcript with proposal."""
        transcript_file = tmp_path / "transcript.jsonl"
        transcript_file.write_text('{"type": "user", "message": {"content": [{"type": "text", "text": "help"}]}}\n')
        entry = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "text",
                        "text": "I'll implement this feature with these steps:\n1. Create module\n2. Run tests"
                    }
                ]
            }
        }
        with transcript_file.open("a") as f:
            f.write(json.dumps(entry) + "\n")
        return transcript_file
