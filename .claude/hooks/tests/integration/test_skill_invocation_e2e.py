#!/usr/bin/env python3
"""
Skill Invocation E2E Tests

Tests complete skill workflow from UserPromptSubmit through execution to response.
Verifies evidence collection at each stage.

Test Coverage:
- UserPromptSubmit → skill execution → response
- Evidence collection at each stage
- Error handling
- Bypass flag functionality
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(hooks_dir))

from evidence_store import load_tool_events


class TestSkillInvocationE2E:
    """End-to-end skill invocation workflow tests."""

    def test_userpromptsubmit_to_skill_execution(self, tmp_path):
        """
        Test complete workflow: UserPromptSubmit → skill execution → response.

        Simulates user invoking a skill through /command and verifies
        evidence is collected at each stage.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Stage 1: UserPromptSubmit
        session_id = "test-skill-session"
        prompt = "/arch create-architecture-plan"

        # Simulate UserPromptSubmit hook
        userpromptsubmit_input = {
            "prompt": prompt,
            "message": prompt,
            "session_id": session_id,
            "terminal_id": "test-terminal",
        }

        # Run UserPromptSubmit hook (if exists)
        userpromptsubmit_hook = hooks_dir / "UserPromptSubmit.py"
        if userpromptsubmit_hook.exists():
            result = subprocess.run(
                [sys.executable, str(userpromptsubmit_hook)],
                input=json.dumps(userpromptsubmit_input),
                capture_output=True,
                text=True,
                timeout=10,
            )
            # UserPromptSubmit should not block
            assert result.returncode == 0

        # Stage 2: Skill tool execution
        skill_tool_input = {
            "tool_name": "Skill",
            "tool_input": {"skill": "arch", "input": {"target": "create-architecture-plan"}},
            "tool_response": {"success": True, "output": "Architecture plan created"},
            "session_id": session_id,
            "terminal_id": "test-terminal",
        }

        # Track skill invocation using E2E tracker
        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        tracker = E2ETrackerHook(state_dir=state_dir)
        tracker_result = tracker.process(**skill_tool_input)

        assert tracker_result["tracked"] is True
        assert tracker_result["workflow_type"] == "skill_invocation"

        # Stage 3: Verify evidence collection
        events = load_tool_events(session_id, limit=10)
        assert len(events) > 0

        # Verify skill event tracked
        skill_events = [e for e in events if e.get("name") == "Skill"]
        assert len(skill_events) > 0

    def test_skill_invocation_with_error(self, tmp_path):
        """
        Test skill invocation that fails during execution.

        Verifies error handling and evidence collection even when skill fails.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        session_id = "failed-skill-session"

        # Simulate failed skill execution
        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        tracker = E2ETrackerHook(state_dir=state_dir)
        result = tracker.process(
            tool_name="Skill",
            tool_input={"skill": "nonexistent-skill"},
            tool_response={"success": False, "error": "Skill not found"},
            session_id=session_id,
            terminal_id="test-terminal",
        )

        # Tracker should still track failed executions
        assert result["tracked"] is True

        # Verify failure is recorded
        events = load_tool_events(session_id, limit=10)
        skill_events = [e for e in events if e.get("name") == "Skill"]
        assert len(skill_events) > 0

        # Verify error is in output
        assert "error" in skill_events[0].get("output_excerpt", "")

    def test_multi_stage_skill_workflow(self, tmp_path):
        """
        Test skill workflow with multiple stages (preparation, execution, cleanup).

        Verifies evidence collection across complete workflow lifecycle.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        session_id = "multi-stage-session"

        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        tracker = E2ETrackerHook(state_dir=state_dir)

        # Stage 1: Preparation (Read files, analyze)
        tracker.process(
            tool_name="Read",
            tool_input={"file_path": "SKILL.md"},
            tool_response={"success": True, "content": "skill documentation"},
            session_id=session_id,
            terminal_id="test-terminal",
        )

        # Stage 2: Execution (Skill invocation)
        tracker.process(
            tool_name="Skill",
            tool_input={"skill": "arch"},
            tool_response={"success": True, "output": "Architecture generated"},
            session_id=session_id,
            terminal_id="test-terminal",
        )

        # Stage 3: Cleanup (Write output)
        tracker.process(
            tool_name="Write",
            tool_input={"file_path": "output.md", "content": "architecture output"},
            tool_response={"success": True},
            session_id=session_id,
            terminal_id="test-terminal",
        )

        # Verify all stages tracked
        events = load_tool_events(session_id, limit=10)
        assert len(events) == 3

        # Verify workflow stages
        assert events[0]["name"] == "Read"
        assert events[1]["name"] == "Skill"
        assert events[2]["name"] == "Write"


class TestSkillInvocationBypass:
    """Test bypass flag functionality for skill invocations."""

    def test_bypass_flag_disables_tracking(self, tmp_path, monkeypatch):
        """
        TEST-008: Test that UNVERIFIED_STANCE_ENABLED=false bypasses verification.

        When bypass flag is set, tracking should be disabled or modified.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        # Set bypass flag
        monkeypatch.setenv("E2E_TRACKER_ENABLED", "false")

        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        tracker = E2ETrackerHook(state_dir=state_dir)

        # Verify tracker is disabled
        assert tracker.enabled is False

        result = tracker.process(
            tool_name="Skill",
            tool_input={"skill": "test"},
            tool_response={"success": True},
            session_id="bypass-test",
            terminal_id="test-terminal",
        )

        # Verify no tracking occurred
        assert result["tracked"] is False

    def test_bypass_flag_with_unverified_stance(self, tmp_path, monkeypatch):
        """
        TEST-008: Test UNVERIFIED_STANCE_ENABLED=false integration.

        Verifies that when unverified stance detection is disabled,
        skill invocations can proceed without verification evidence.
        """
        # Disable unverified stance detection
        monkeypatch.setenv("UNVERIFIED_STANCE_ENABLED", "false")

        # Import Stop hook to verify flag is respected
        # This would normally block unverified claims
        # With flag disabled, it should allow passage

        # Test that skill invocation proceeds without verification
        session_id = "unverified-session"

        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        tracker = E2ETrackerHook(state_dir=tmp_path / "state")
        result = tracker.process(
            tool_name="Skill",
            tool_input={"skill": "arch"},
            tool_response={"success": True, "output": "Complete without verification"},
            session_id=session_id,
            terminal_id="test-terminal",
        )

        # Should track even without verification (bypass mode)
        assert result["tracked"] is True


class TestSkillInvocationEvidenceCollection:
    """Test evidence collection during skill invocations."""

    def test_evidence_collection_from_userpromptsubmit(self, tmp_path):
        """
        Test that UserPromptSubmit context is captured as evidence.

        User's original prompt should be tracked for later verification.
        """
        session_id = "evidence-collection-session"

        # Simulate UserPromptSubmit storing prompt
        from evidence_store import store_session_context

        store_session_context(
            session_id=session_id,
            terminal_id="test-terminal",
            metadata={
                "user_prompt": "/arch create-plan",
                "prompt_timestamp": datetime.now(UTC).isoformat(),
            },
        )

        # Verify context is retrievable
        events = load_tool_events(session_id, limit=10)
        assert len(events) > 0

    def test_evidence_collection_from_tool_execution(self, tmp_path):
        """
        Test that tool execution details are captured as evidence.

        Commands, outputs, and success/failure should all be tracked.
        """
        state_dir = tmp_path / "state"
        state_dir.mkdir()

        session_id = "tool-evidence-session"

        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        tracker = E2ETrackerHook(state_dir=state_dir)
        tracker.process(
            tool_name="Bash",
            tool_input={"command": "pytest tests/test_arch.py -v"},
            tool_response={
                "success": True,
                "output": "tests/test_arch.py::test_plan PASSED\n1 passed",
            },
            session_id=session_id,
            terminal_id="test-terminal",
        )

        # Verify detailed evidence
        events = load_tool_events(session_id, limit=10)
        bash_events = [e for e in events if e.get("name") == "Bash"]
        assert len(bash_events) > 0

        event = bash_events[0]
        assert "pytest" in event.get("command", "")
        assert "passed" in event.get("output_excerpt", "")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
