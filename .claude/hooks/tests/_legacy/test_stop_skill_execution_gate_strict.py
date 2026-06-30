import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from StopHook_skill_execution_gate import run


def _write_transcript(path: Path, user_prompt: str, tool_blocks: list[dict] | None = None) -> None:
    entries = [
        {
            "type": "message",
            "role": "user",
            "message": {"content": [{"type": "text", "text": user_prompt}]},
        }
    ]
    if tool_blocks is not None:
        entries.append(
            {
                "type": "message",
                "role": "assistant",
                "message": {"content": tool_blocks},
            }
        )
    path.write_text("\n".join(json.dumps(e) for e in entries), encoding="utf-8")


def test_slash_command_without_skill_now_blocks() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        transcript = tmp_path / "transcript.jsonl"
        _write_transcript(
            transcript,
            "/planning",
            tool_blocks=[{"type": "tool_use", "name": "Read", "input": {"file_path": "P:/foo.txt"}}],
        )

        result = run({"transcript_path": str(transcript)})

        assert result is not None
        assert result.get("block") is True
        reason = result.get("reason", "")
        assert "WORKFLOW_BLOCK_NOT_HOOK_CRASH" in reason
        assert "SLASH COMMAND NOT EXECUTED: /planning" in reason


def test_slash_command_with_skill_and_execution_allows() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        transcript = tmp_path / "transcript.jsonl"
        _write_transcript(
            transcript,
            "/planning",
            tool_blocks=[
                {"type": "tool_use", "name": "Skill", "input": {"skill": "planning"}},
                {"type": "tool_use", "name": "Read", "input": {"file_path": "P:/foo.txt"}},
            ],
        )

        result = run({"transcript_path": str(transcript)})

        assert result is None
