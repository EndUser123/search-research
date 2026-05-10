"""Tests for Stop_approval_gate."""
import importlib
import json
import os
import tempfile
import time
from pathlib import Path

import pytest

import Stop_approval_gate
from Stop_approval_gate import _IMPLEMENT_PATTERNS, _check_approval, run


class TestImplementPatterns:
    """Test pattern matching."""

    def test_patterns_match_implement_intent(self):
        """Responses with implement intent should match patterns."""
        test_cases = [
            "Proceeding to implement the changes now.",
            "I'll implement the fix.",
            "Let's execute the deployment.",
            "Should we proceed with it?",
            "Want me to implement this feature?",
            "i am going to implement the solution",
        ]
        for text in test_cases:
            matched = any(p.search(text) for p in _IMPLEMENT_PATTERNS)
            assert matched, f"Pattern should match: {text}"

    def test_patterns_allow_architecture(self):
        """Architecture descriptions should not match."""
        test_cases = [
            "The architecture consists of three layers.",
            "This implements the specification correctly.",
            "Implementation details follow.",
        ]
        for text in test_cases:
            matched = any(p.search(text) for p in _IMPLEMENT_PATTERNS)
            assert not matched, f"Pattern should not match: {text}"


class TestApprovalGate:
    """Test cases for approval gate logic."""

    @pytest.fixture
    def temp_artifacts(self, tmp_path, monkeypatch):
        artifacts = tmp_path / ".artifacts"
        artifacts.mkdir()
        monkeypatch.setenv("CLAUDE_ARTIFACTS_DIR", str(artifacts))
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test-terminal")
        # Reload module to pick up new env vars
        import Stop_approval_gate
        importlib.reload(Stop_approval_gate)
        return artifacts

    def test_no_approval_blocks_implement(self, temp_artifacts):
        """Response with implement intent without approval should block."""
        tid = "test-terminal"
        (temp_artifacts / tid).mkdir()
        data = {"response": "I'll proceed to implement the changes now."}
        result = run(data)
        assert result is not None
        assert result["decision"] == "block"
        assert "IMPLEMENTATION WITHOUT APPROVAL" in result["reason"]

    def test_with_approval_allows(self, temp_artifacts):
        """Response with implement intent but approved should allow."""
        tid = "test-terminal"
        art_dir = temp_artifacts / tid
        art_dir.mkdir()
        (art_dir / "approval.json").write_text(json.dumps({"approved": True}))
        data = {"response": "Proceeding to implement the changes."}
        result = run(data)
        assert result is None

    def test_expired_approval_blocks(self, temp_artifacts):
        """Expired approval (>1 hour) should be treated as no approval."""
        tid = "test-terminal"
        art_dir = temp_artifacts / tid
        art_dir.mkdir()
        # Approval from 2 hours ago
        (art_dir / "approval.json").write_text(json.dumps({
            "approved": True,
            "ts": time.time() - 7200
        }))
        data = {"response": "Proceeding to implement now."}
        result = run(data)
        assert result is not None
        assert result["decision"] == "block"

    def test_no_implement_intent_allows(self, temp_artifacts):
        """Response without implement intent should pass silently."""
        data = {"response": "The architecture analysis is complete."}
        result = run(data)
        assert result is None

    def test_empty_response_allows(self, temp_artifacts):
        """Empty response should allow."""
        result = run({})
        assert result is None

    def test_no_artifacts_dir_allows(self, temp_artifacts):
        """No artifacts directory should allow (fail-open)."""
        data = {"response": "I'll implement this now."}
        result = run(data)
        assert result is not None  # Pattern matches, blocks despite no approval file


class TestApprovalHandler:
    """Test cases for /approve handler."""

    def test_approve_pattern_matches(self):
        """Test /approve pattern detection."""
        from UserPromptSubmit_approval import process_prompt
        import re

        patterns = [
            ("/approve execute", "execute"),
            ("/approve deploy", "deploy"),
            ("/approve implement myskill", "implement", "myskill"),
        ]
        for case in patterns:
            prompt = case[0]
            expected_phase = case[1]
            expected_skill = case[2] if len(case) > 2 else "design"  # Falls back to design
            m = re.match(r"^/approve\s+(\w+)(?:\s+(\w+))?", prompt, re.I)
            assert m, f"Should match: {prompt}"
            assert m.group(1) == expected_phase
            assert (m.group(2) or "design") == expected_skill


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
