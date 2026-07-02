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


def test_enrichment_skipped_on_stop_hook_continuation(tmp_path):
    """Regen turns: the latest transcript user entry is hook feedback, not the
    user's prompt — enrichment must preserve pre-fix behavior (no prompt)."""
    data = _real_stop_payload(_write_fixture_transcript(tmp_path))
    data["stop_hook_active"] = True
    Stop._enrich_user_prompt(data)
    assert "user_prompt" not in data


def test_enrichment_tolerates_non_dict_message(tmp_path):
    """A malformed entry with a string message must not crash the reader."""
    p = tmp_path / "t.jsonl"
    lines = [
        {"type": "user", "message": "not a dict"},
        {"type": "user", "message": {"role": "user", "content": [
            {"type": "text", "text": USER_TEXT}]}},
    ]
    p.write_text("\n".join(json.dumps(x) for x in lines), encoding="utf-8")
    data = _real_stop_payload(p)
    Stop._enrich_user_prompt(data)
    assert data.get("user_prompt") == USER_TEXT


def test_tail_read_returns_latest_user_text_on_large_transcript(tmp_path):
    """Transcripts grow unbounded (285MB observed); the enrichment tail-read
    must still find the last user message without a full-file read."""
    from __lib.transcript_reader import get_latest_user_text
    p = tmp_path / "big.jsonl"
    filler = {"type": "assistant", "message": {"role": "assistant", "content": [
        {"type": "text", "text": "x" * 500}]}}
    lines = [json.dumps(filler)] * 50
    lines.append(json.dumps({"type": "user", "message": {"role": "user", "content": [
        {"type": "text", "text": USER_TEXT}]}}))
    p.write_text("\n".join(lines), encoding="utf-8")
    # tail_bytes far smaller than the file forces the seek path
    assert get_latest_user_text({"transcript_path": str(p)}, tail_bytes=2048) == USER_TEXT


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
