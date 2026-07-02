"""Regression: Stop payload user_prompt enrichment from transcript_path.

Root cause fixed (2026-07-02): the real Stop payload contains NO user_prompt /
prompt / transcript fields — user text lives only in the transcript_path JSONL.
Stop_semantic_critic (and every gate reading data["user_prompt"]) therefore ran
prompt-blind, producing advisories like "the original user prompt is empty".

These tests use the REAL payload shape (session_id, transcript_path,
stop_hook_active, last_assistant_message) — not the synthetic transcript-list
shape that let the original bug hide behind green tests.
"""

import json
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import Stop  # noqa: E402

USER_TEXT = "can you determine the root cause for the semantic critic warning?"


def _write_fixture_transcript(tmp_path: Path) -> Path:
    """Real transcript JSONL: user message, tool_result entry, assistant reply."""
    lines = [
        # Real user message (older)
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "text", "text": "earlier unrelated prompt"}]}},
        # The latest real user message
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "text", "text": USER_TEXT}]}},
        # tool_result entry also carries role=user — must NOT be picked up
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "tool_result", "tool_use_id": "t1", "content": "grep output"}]}},
        # Assistant reply
        {"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "Root cause: ..."}]}},
    ]
    p = tmp_path / "transcript.jsonl"
    p.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
    return p


def _real_stop_payload(transcript_path: Path) -> dict:
    """The shape Claude Code actually sends on Stop — nothing else."""
    return {
        "session_id": "test-session",
        "transcript_path": str(transcript_path),
        "hook_event_name": "Stop",
        "stop_hook_active": False,
        "last_assistant_message": "Root cause: ...",
    }


def test_enrichment_fills_user_prompt_from_transcript(tmp_path):
    data = _real_stop_payload(_write_fixture_transcript(tmp_path))
    assert "user_prompt" not in data  # precondition = the real payload gap
    Stop._enrich_user_prompt(data)
    assert data["user_prompt"] == USER_TEXT


def test_enrichment_skips_tool_result_entries(tmp_path):
    """The last role=user JSONL entry is a tool_result; enrichment must return
    the last REAL user message, not "" and not the tool output."""
    data = _real_stop_payload(_write_fixture_transcript(tmp_path))
    Stop._enrich_user_prompt(data)
    assert "grep output" not in data["user_prompt"]


def test_enrichment_preserves_existing_prompt(tmp_path):
    data = _real_stop_payload(_write_fixture_transcript(tmp_path))
    data["user_prompt"] = "explicit prompt"
    Stop._enrich_user_prompt(data)
    assert data["user_prompt"] == "explicit prompt"


def test_enrichment_fails_open_on_missing_transcript():
    data = {
        "session_id": "s",
        "transcript_path": "Z:/does/not/exist.jsonl",
        "stop_hook_active": False,
    }
    Stop._enrich_user_prompt(data)  # must not raise
    assert "user_prompt" not in data


def test_semantic_critic_fallback_sees_enriched_prompt(tmp_path):
    """Integration invariant: the critic's extraction fallback
    (data.get("user_prompt", ...)) now yields the real prompt on the real
    payload shape. Guards against re-introducing the prompt-blind path."""
    data = _real_stop_payload(_write_fixture_transcript(tmp_path))
    Stop._enrich_user_prompt(data)
    # Mirror Stop_semantic_critic.run() extraction (no transcript field present)
    user_prompt = ""
    if not user_prompt:
        user_prompt = data.get("user_prompt", data.get("prompt", ""))
    assert user_prompt == USER_TEXT
