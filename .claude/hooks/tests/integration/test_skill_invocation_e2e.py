#!/usr/bin/env python3
"""
Skill invocation E2E tests against the current tracker interfaces.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

hooks_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(hooks_dir))


class TestSkillInvocationE2E:
    def test_userpromptsubmit_to_skill_execution(self, monkeypatch):
        session_id = "test-skill-session"
        prompt = "/arch create-architecture-plan"

        userpromptsubmit_hook = hooks_dir / "UserPromptSubmit.py"
        if userpromptsubmit_hook.exists():
            result = subprocess.run(
                [sys.executable, str(userpromptsubmit_hook)],
                input=json.dumps(
                    {
                        "prompt": prompt,
                        "message": prompt,
                        "session_id": session_id,
                        "terminal_id": "test-terminal",
                    }
                ),
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0

        from posttooluse.e2e_tracker_hook import E2ETrackerHook
        import posttooluse.e2e_tracker_hook as hook_module

        captured: list[dict] = []
        monkeypatch.setattr(
            hook_module,
            "post_tool_use_hook",
            lambda **kwargs: captured.append(kwargs),
        )

        tracker = E2ETrackerHook()
        tracker_result = tracker.process(
            tool_name="Skill",
            tool_input={"skill": "arch", "input": {"target": "create-architecture-plan"}},
            tool_response={
                "success": True,
                "output": "Architecture plan created",
                "context": {"session_id": session_id, "terminal_id": "test-terminal"},
            },
        )

        assert tracker_result["tracked"] is True
        assert tracker_result["workflow_type"] == "skill_invocation"
        assert captured[0]["tool_name"] == "Skill"
        assert captured[0]["context"]["session_id"] == session_id

    def test_skill_invocation_with_error(self, monkeypatch):
        from posttooluse.e2e_tracker_hook import E2ETrackerHook
        import posttooluse.e2e_tracker_hook as hook_module

        monkeypatch.setattr(
            hook_module,
            "post_tool_use_hook",
            lambda **kwargs: (_ for _ in ()).throw(ValueError("Skill not found")),
        )

        tracker = E2ETrackerHook()
        result = tracker.process(
            tool_name="Skill",
            tool_input={"skill": "nonexistent-skill"},
            tool_response={
                "success": False,
                "error": "Skill not found",
                "context": {"session_id": "failed-skill-session", "terminal_id": "test-terminal"},
            },
        )

        assert result["tracked"] is True
        assert result["passed"] is True

    def test_multi_stage_skill_workflow(self, monkeypatch):
        from posttooluse.e2e_tracker_hook import E2ETrackerHook
        import posttooluse.e2e_tracker_hook as hook_module

        captured: list[str] = []
        monkeypatch.setattr(
            hook_module,
            "post_tool_use_hook",
            lambda **kwargs: captured.append(kwargs["tool_name"]),
        )

        tracker = E2ETrackerHook()
        context = {"session_id": "multi-stage-session", "terminal_id": "test-terminal"}
        tracker.process("Read", {"file_path": "SKILL.md"}, {"success": True, "context": context})
        tracker.process("Skill", {"skill": "arch"}, {"success": True, "output": "ok", "context": context})
        tracker.process("Write", {"file_path": "output.md"}, {"success": True, "context": context})

        assert captured == ["Read", "Skill", "Write"]


class TestSkillInvocationBypass:
    def test_bypass_flag_disables_tracking(self, monkeypatch):
        monkeypatch.setenv("E2E_TRACKER_ENABLED", "false")

        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        tracker = E2ETrackerHook()
        assert tracker.enabled is False

        result = tracker.run(
            {
                "tool_name": "Skill",
                "tool_input": {"skill": "test"},
                "tool_response": {"success": True, "context": {"session_id": "bypass-test", "terminal_id": "test-terminal"}},
            }
        )

        assert result["skipped"] is True
        assert result["reason"] == "disabled"

    def test_bypass_flag_with_unverified_stance(self, monkeypatch):
        monkeypatch.setenv("UNVERIFIED_STANCE_ENABLED", "false")

        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        tracker = E2ETrackerHook()
        result = tracker.process(
            tool_name="Skill",
            tool_input={"skill": "arch"},
            tool_response={
                "success": True,
                "output": "Complete without verification",
                "context": {"session_id": "unverified-session", "terminal_id": "test-terminal"},
            },
        )

        assert result["tracked"] is True


class TestSkillInvocationEvidenceCollection:
    def test_evidence_collection_from_userpromptsubmit(self):
        from evidence_store import read_session_context, write_session_context

        session_id = "evidence-collection-session"
        write_session_context(
            session_id=session_id,
            terminal_id="test-terminal",
            metadata={
                "user_prompt": "/arch create-plan",
                "prompt_timestamp": datetime.now(UTC).isoformat(),
            },
        )

        context = read_session_context()
        assert context

    def test_evidence_collection_from_tool_execution(self, tmp_path):
        from PostToolUse_e2e_tracker import track_workflow

        session_id = "tool-evidence-session"
        state_dir = tmp_path / "state"
        track_workflow(
            workflow_type="tool_chain",
            target="pytest tests test_arch py v",
            session_id=session_id,
            terminal_id="test-terminal",
            stages=[{"stage": "run", "status": "passed", "duration_ms": 1}],
            overall="success",
            state_dir=state_dir,
        )

        log_file = state_dir / f"e2e_executions_{session_id}.jsonl"
        assert log_file.exists()
        payload = json.loads(log_file.read_text(encoding="utf-8").splitlines()[0])
        assert "pytest" in payload["target"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
