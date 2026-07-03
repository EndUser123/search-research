"""Test that _run_unverified_stance emits telemetry on allow (not just block)."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure we use the local Stop module
sys.path.insert(0, str(Path(__file__).parent))


class TestRunUnverifiedStanceObservability:
    """Regression test: unverified_stance must emit telemetry on allow, not only on block."""

    def test_clean_response_returns_allow_dict(self):
        """Clean response should return a dict so telemetry fires, not None."""
        from Stop import _run_unverified_stance

        result = _run_unverified_stance({
            "response": "Here is a clear answer with no system claims.",
            "session_id": "test_obs_clean",
            "terminal_id": "test_term",
            "tool_events": [],
            "tool_calls": [],
        })
        # Must return a non-None dict on allow path
        assert result is not None, "Clean response must return a dict, not None"
        assert result.get("decision") == "allow", f"Expected decision=allow, got {result.get('decision')}"
        assert result.get("allow") is True

    def test_unverified_claim_returns_block_dict(self):
        """Unverified system claim should return a block dict."""
        from Stop import _run_unverified_stance

        result = _run_unverified_stance({
            "response": "The system guarantees all hooks run synchronously.",
            "session_id": "test_obs_block",
            "terminal_id": "test_term",
            "tool_events": [],
            "tool_calls": [],
        })
        assert result is not None, "Block response must return a dict"
        assert result.get("decision") == "block", f"Expected decision=block, got {result.get('decision')}"

    def test_gate_result_contract_unchanged(self):
        """The block dict returned on blocked path must match the original contract."""
        from Stop import _run_unverified_stance

        result = _run_unverified_stance({
            "response": "The system guarantees all hooks run synchronously.",
            "session_id": "test_obs_contract",
            "terminal_id": "test_term",
            "tool_events": [],
            "tool_calls": [],
        })
        assert result is not None
        assert "decision" in result
        assert "reason" in result
        assert "blocking_hook" in result

    def test_extra_fields_populated_on_block(self):
        """When gate blocks, block_triggered should be True in telemetry extra."""
        from Stop import _run_unverified_stance

        result = _run_unverified_stance({
            "response": "The system guarantees all hooks run synchronously.",
            "session_id": "test_obs_extra",
            "terminal_id": "test_term",
            "tool_events": [],
            "tool_calls": [],
        })
        assert result is not None
        # block_triggered should be True when gate blocks
        assert result.get("block") is True, "Expected block=True on blocked response"
        assert result.get("allow") is not True, "Should not have allow=True when blocked"

    def test_allow_path_has_no_block(self):
        """Allow path must not have block=True."""
        from Stop import _run_unverified_stance

        result = _run_unverified_stance({
            "response": "Here is a straightforward answer.",
            "session_id": "test_obs_allow_no_block",
            "terminal_id": "test_term",
            "tool_events": [],
            "tool_calls": [],
        })
        assert result is not None
        assert result.get("block") is not True, "Allow path should not have block=True"
        assert result.get("allow") is True, "Allow path should have allow=True"
