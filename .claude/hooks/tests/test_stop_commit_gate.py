#!/usr/bin/env python3
"""Tests for Stop_commit_gate.py - Git commit approval gate."""
import importlib
import json
import os
import sys
import time
from pathlib import Path

import pytest

# Add hooks dir to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import Stop_commit_gate


class TestCommitGatePatternMatching:
    """Test git action pattern detection."""

    def test_git_commit_blocks(self):
        """Git commit without approval is blocked."""
        importlib.reload(Stop_commit_gate)
        data = {"response": "I'll run git commit -m 'fix: update API endpoints' now"}
        result = Stop_commit_gate.run(data)
        assert result is not None, "Should block git commit"
        assert result["decision"] == "block"

    def test_git_push_blocks(self):
        """Git push without approval is blocked."""
        importlib.reload(Stop_commit_gate)
        data = {"response": "Executing git push to remote"}
        result = Stop_commit_gate.run(data)
        assert result is not None, "Should block git push"
        assert result["decision"] == "block"

    def test_git_merge_blocks(self):
        """Git merge without approval is blocked."""
        importlib.reload(Stop_commit_gate)
        data = {"response": "Let me git merge feature-branch into main"}
        result = Stop_commit_gate.run(data)
        assert result is not None, "Should block git merge"
        assert result["decision"] == "block"

    def test_git_rebase_blocks(self):
        """Git rebase without approval is blocked."""
        importlib.reload(Stop_commit_gate)
        data = {"response": "I'll proceed with git rebase -i HEAD~3"}
        result = Stop_commit_gate.run(data)
        assert result is not None, "Should block git rebase"
        assert result["decision"] == "block"

    def test_no_git_action_allowed(self):
        """Non-git actions are allowed."""
        importlib.reload(Stop_commit_gate)
        data = {"response": "I'll run pytest and verify the tests pass"}
        result = Stop_commit_gate.run(data)
        assert result is None, "Should not block non-git actions"

    def test_empty_response_allowed(self):
        """Empty response is allowed."""
        importlib.reload(Stop_commit_gate)
        data = {"response": ""}
        result = Stop_commit_gate.run(data)
        assert result is None, "Should not block empty response"

    def test_no_response_allowed(self):
        """No response key is allowed."""
        importlib.reload(Stop_commit_gate)
        data = {}
        result = Stop_commit_gate.run(data)
        assert result is None, "Should not block when no response"


class TestCommitGateApproval:
    """Test approval state checking."""

    @pytest.fixture
    def setup_artifacts(self, tmp_path, monkeypatch):
        """Set up test artifacts directory."""
        artifacts = tmp_path / ".artifacts"
        artifacts.mkdir()
        terminal_id = "test_commit_terminal"

        monkeypatch.setenv("CLAUDE_TERMINAL_ID", terminal_id)
        monkeypatch.setenv("CLAUDE_ARTIFACTS_DIR", str(artifacts))

        # Reload module to pick up env vars
        importlib.reload(Stop_commit_gate)

        return {"artifacts": artifacts, "terminal_id": terminal_id}

    def test_commit_with_approval_allowed(self, setup_artifacts):
        """Git commit with approval is allowed."""
        tid = setup_artifacts["terminal_id"]
        artifacts = setup_artifacts["artifacts"]
        approval_file = artifacts / tid / "approval.json"
        approval_file.parent.mkdir(parents=True, exist_ok=True)
        approval_file.write_text(json.dumps({
            "skill": "hooks",
            "phase": "commit",
            "approved": True,
            "ttl_hours": 24,
            "ts": time.time(),
        }))

        importlib.reload(Stop_commit_gate)
        data = {"response": "Executing git commit -m 'feat: add approval gate'"}
        result = Stop_commit_gate.run(data)
        assert result is None, "Should allow commit with approval"

    def test_wrong_phase_blocked(self, setup_artifacts):
        """Commit approval with wrong phase is blocked."""
        tid = setup_artifacts["terminal_id"]
        artifacts = setup_artifacts["artifacts"]
        approval_file = artifacts / tid / "approval.json"
        approval_file.parent.mkdir(parents=True, exist_ok=True)
        approval_file.write_text(json.dumps({
            "skill": "hooks",
            "phase": "execute",  # Wrong phase for commit
            "approved": True,
            "ttl_hours": 24,
            "ts": time.time(),
        }))

        importlib.reload(Stop_commit_gate)
        data = {"response": "Executing git commit now"}
        result = Stop_commit_gate.run(data)
        assert result is not None, "Should block when phase is not 'commit'"
        assert "PHASE MISMATCH" in result["reason"]

    def test_deploy_phase_allowed(self, setup_artifacts):
        """Commit with 'deploy' phase is allowed."""
        tid = setup_artifacts["terminal_id"]
        artifacts = setup_artifacts["artifacts"]
        approval_file = artifacts / tid / "approval.json"
        approval_file.parent.mkdir(parents=True, exist_ok=True)
        approval_file.write_text(json.dumps({
            "skill": "ci",
            "phase": "deploy",
            "approved": True,
            "ttl_hours": 24,
            "ts": time.time(),
        }))

        importlib.reload(Stop_commit_gate)
        data = {"response": "Now I'll git push to deploy"}
        result = Stop_commit_gate.run(data)
        assert result is None, "Should allow git push with deploy phase"


class TestCommitGateTTL:
    """Test TTL expiry behavior."""

    def test_expired_approval_blocked(self, monkeypatch, tmp_path):
        """Expired approval is blocked."""
        artifacts = tmp_path / ".artifacts"
        artifacts.mkdir()
        terminal_id = "test_terminal_expired"
        approval_file = artifacts / terminal_id / "approval.json"
        approval_file.parent.mkdir(parents=True, exist_ok=True)
        # Create approval that expired 25 hours ago
        approval_file.write_text(json.dumps({
            "skill": "hooks",
            "phase": "commit",
            "approved": True,
            "ttl_hours": 24,
            "ts": time.time() - (25 * 3600),
        }))

        monkeypatch.setenv("CLAUDE_TERMINAL_ID", terminal_id)
        monkeypatch.setenv("CLAUDE_ARTIFACTS_DIR", str(artifacts))

        importlib.reload(Stop_commit_gate)
        data = {"response": "Executing git commit now"}
        result = Stop_commit_gate.run(data)
        assert result is not None, "Should block when approval expired"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])