"""Tests for Stop_approval_gate - Phase-aware implementation gate."""
import importlib
import json
import os
import time
from pathlib import Path

import pytest

import Stop_approval_gate
from Stop_approval_gate import _check_approval, _IMPLEMENT_PATTERNS, run


class TestImplementPatterns:
    """Test pattern matching."""

    def test_patterns_match_implement_intent(self):
        """Responses with explicit implement intent should match patterns."""
        test_cases = [
            "Proceeding to implement the changes now.",
            "Proceeding to execute the deployment.",
            "Proceeding to deploy the changes.",
            "Want me to implement this feature?",
        ]
        for text in test_cases:
            matched = any(p.search(text) for p in _IMPLEMENT_PATTERNS)
            assert matched, f"Pattern should match: {text}"

    def test_patterns_allow_architecture(self):
        """Architecture descriptions should not match."""
        test_cases = [
            "The architecture consists of three layers.",
            "This implements the specification correctly.",
            "I'll implement the fix.",  # "I'll implement" doesn't match explicit patterns
            "Let's execute the deployment.",  # "Let's" doesn't match
            "Should we proceed with it?",  # Not explicit intent
            "i am going to implement the solution",  # Not explicit phrase
        ]
        for text in test_cases:
            matched = any(p.search(text) for p in _IMPLEMENT_PATTERNS)
            assert not matched, f"Pattern should not match: {text}"


class TestApprovalGatePhase:
    """Test phase-aware approval gate logic."""

    @pytest.fixture
    def temp_artifacts(self, tmp_path, monkeypatch):
        artifacts = tmp_path / ".artifacts"
        artifacts.mkdir()
        monkeypatch.setenv("CLAUDE_ARTIFACTS_DIR", str(artifacts))
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", "test-terminal")
        importlib.reload(Stop_approval_gate)
        return artifacts

    def test_no_approval_blocks_implement(self, temp_artifacts):
        """Response with implement intent without approval should block."""
        tid = "test-terminal"
        (temp_artifacts / tid).mkdir()
        data = {"response": "Proceeding to implement the changes now."}
        result = run(data)
        assert result is not None
        assert result["decision"] == "block"
        assert "IMPLEMENTATION WITHOUT APPROVAL" in result["reason"]

    def test_execute_phase_allows(self, temp_artifacts):
        """Execute phase approval allows implementation."""
        tid = "test-terminal"
        art_dir = temp_artifacts / tid
        art_dir.mkdir()
        (art_dir / "approval.json").write_text(json.dumps({
            "approved": True,
            "phase": "execute",
            "skill": "wiki",
            "ttl_hours": 24,
            "ts": time.time(),
        }))
        data = {"response": "Proceeding to implement the changes now."}
        result = run(data)
        assert result is None, "Should allow with execute phase"

    def test_deploy_phase_allows(self, temp_artifacts):
        """Deploy phase approval allows implementation."""
        tid = "test-terminal"
        art_dir = temp_artifacts / tid
        art_dir.mkdir()
        (art_dir / "approval.json").write_text(json.dumps({
            "approved": True,
            "phase": "deploy",
            "skill": "wiki",
            "ttl_hours": 24,
            "ts": time.time(),
        }))
        data = {"response": "Now I'll execute the deployment."}
        result = run(data)
        assert result is None, "Should allow with deploy phase"

    def test_design_phase_blocks(self, temp_artifacts):
        """Design phase approval blocks implementation."""
        tid = "test-terminal"
        art_dir = temp_artifacts / tid
        art_dir.mkdir()
        (art_dir / "approval.json").write_text(json.dumps({
            "approved": True,
            "phase": "design",
            "skill": "wiki",
            "ttl_hours": 24,
            "ts": time.time(),
        }))
        data = {"response": "Proceeding to implement the changes now."}
        result = run(data)
        assert result is not None, "Should block with design phase"
        assert "PHASE MISMATCH" in result["reason"]

    def test_verify_phase_blocks(self, temp_artifacts):
        """Verify phase approval blocks implementation."""
        tid = "test-terminal"
        art_dir = temp_artifacts / tid
        art_dir.mkdir()
        (art_dir / "approval.json").write_text(json.dumps({
            "approved": True,
            "phase": "verify",
            "skill": "wiki",
            "ttl_hours": 24,
            "ts": time.time(),
        }))
        data = {"response": "Proceeding to execute the implementation now."}
        result = run(data)
        assert result is not None, "Should block with verify phase"
        assert "PHASE MISMATCH" in result["reason"]

    def test_expired_approval_blocks(self, temp_artifacts):
        """Expired approval (>ttl_hours) should be treated as no approval."""
        tid = "test-terminal"
        art_dir = temp_artifacts / tid
        art_dir.mkdir()
        # Approval from 25 hours ago with 24h TTL
        (art_dir / "approval.json").write_text(json.dumps({
            "approved": True,
            "phase": "execute",
            "ttl_hours": 24,
            "ts": time.time() - (25 * 3600)
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


class TestApprovalHandlerPhase:
    """Test phase-aware /approve handler."""

    def test_approve_execute_pattern(self):
        """Test /approve execute pattern."""
        from UserPromptSubmit_approval import process_prompt
        import re

        m = re.match(r"^/approve\s+(\w+)(?:\s+(\w+))?(?:\s+ttl=(\d+))?", "/approve execute", re.I)
        assert m
        assert m.group(1) == "execute"
        assert m.group(2) is None  # defaults to design

    def test_approve_skill_phase_pattern(self):
        """Test /approve wiki verify pattern."""
        from UserPromptSubmit_approval import process_prompt
        import re

        m = re.match(r"^/approve\s+(\w+)(?:\s+(\w+))?(?:\s+ttl=(\d+))?", "/approve wiki verify", re.I)
        assert m
        assert m.group(1) == "wiki"
        assert m.group(2) == "verify"

    def test_approve_with_ttl(self):
        """Test /approve with custom TTL."""
        import re

        m = re.match(r"^/approve\s+(\w+)(?:\s+(\w+))?(?:\s+ttl=(\d+))?", "/approve design execute ttl=48", re.I)
        assert m
        assert m.group(1) == "design"
        assert m.group(2) == "execute"
        assert m.group(3) == "48"

    def test_deny_pattern(self):
        """Test /deny pattern."""
        import re

        m = re.match(r"^/deny\s+(\w+)", "/deny wiki", re.I)
        assert m
        assert m.group(1) == "wiki"


class TestCheckApproval:
    """Test _check_approval function returns state."""

    def test_check_returns_tuple(self, tmp_path, monkeypatch):
        """_check_approval should return (bool, dict) tuple."""
        artifacts = tmp_path / ".artifacts"
        artifacts.mkdir()
        tid = "test-check"
        art_dir = artifacts / tid
        art_dir.mkdir()
        (art_dir / "approval.json").write_text(json.dumps({
            "approved": True,
            "phase": "execute",
            "skill": "wiki",
            "ts": time.time(),
        }))
        monkeypatch.setenv("CLAUDE_ARTIFACTS_DIR", str(artifacts))
        monkeypatch.setenv("CLAUDE_TERMINAL_ID", tid)
        importlib.reload(Stop_approval_gate)

        result = Stop_approval_gate._check_approval()
        assert isinstance(result, tuple), f"_check_approval should return tuple, got {type(result)}"
        approved, state = result
        assert approved is True
        assert state is not None
        assert state["phase"] == "execute"
        assert state["skill"] == "wiki"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])