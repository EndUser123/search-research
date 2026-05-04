from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from UserPromptSubmit_modules import slash_command_observability as slash_audit


class _Context:
    def __init__(
        self,
        prompt: str,
        session_id: str = "12345678-1234-1234-1234-123456789abc",
        terminal_id: str = "term-1",
    ):
        self.prompt = prompt
        self.session_id = session_id
        self.terminal_id = terminal_id
        self.data = {
            "session_id": session_id,
            "terminal_id": terminal_id,
            "turn_id": "turn-abc",
            "transcript_path": "P:/fake/transcript.jsonl",
        }


def test_classify_local_command_frontend():
    info = slash_audit.classify_slash_command("arch")

    assert info["command_family"] == "local_command"
    assert info["command_name"] == "arch"
    assert info["command_path"].endswith(r".claude\commands\arch.md")
    assert info["backing_target"] == "arch"


def test_classify_skill_command():
    info = slash_audit.classify_slash_command("recap")

    assert info["command_family"] == "skill"
    assert info["command_name"] == "recap"
    assert info["command_path"].endswith(r".claude\skills\recap\SKILL.md")
    assert info["backing_target"] == "recap"


def test_classify_builtin_command():
    info = slash_audit.classify_slash_command("status")

    assert info["command_family"] == "builtin"
    assert info["command_name"] == "status"
    assert info["command_path"] == ""
    assert info["backing_target"] == ""


def test_request_and_resolution_logging(monkeypatch):
    calls: list[dict] = []

    def fake_append_tool_event(**kwargs):
        calls.append(kwargs)
        return True

    monkeypatch.setattr(slash_audit, "append_tool_event", fake_append_tool_event)

    context = _Context("/arch find the architecture boundary")
    assert slash_audit.record_slash_request(context, "arch", "find the architecture boundary")
    assert slash_audit.record_slash_resolution(context, "arch", "find the architecture boundary")

    assert len(calls) == 2
    assert calls[0]["tool_name"] == "SlashCommandRequested"
    assert calls[0]["command"] == "/arch find the architecture boundary"
    assert calls[0]["metadata"]["slash_event_type"] == "requested"
    assert calls[0]["metadata"]["command_family"] == "local_command"
    assert calls[0]["metadata"]["backing_target"] == "arch"
    assert calls[1]["tool_name"] == "SlashCommandResolved"
    assert calls[1]["metadata"]["slash_event_type"] == "resolved"


def test_hook_skips_topic_inquiry(monkeypatch):
    fake_append = Mock(return_value=True)
    monkeypatch.setattr(slash_audit, "append_tool_event", fake_append)

    context = _Context("tell me about /arch")
    result = slash_audit.slash_command_observability_hook(context)

    assert result.is_empty()
    fake_append.assert_not_called()
