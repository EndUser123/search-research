#!/usr/bin/env python3
"""Tests for bounded transcript tail extraction in hook_ledger."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
HOOKS_LIB_DIR = HOOKS_DIR / "__lib"
for path in (HOOKS_DIR, HOOKS_LIB_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from hook_ledger import build_response_snapshot  # type: ignore  # noqa: E402


def test_build_response_snapshot_reads_large_transcript_from_tail(tmp_path, monkeypatch):
    transcript_path = tmp_path / "large_transcript.jsonl"
    filler = "x" * 70000
    with transcript_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"role": "assistant", "content": filler}) + "\n")
        fh.write(json.dumps({"role": "user", "content": "Need the latest status"}) + "\n")
        fh.write(json.dumps({
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Latest answer"},
                {"type": "tool_use", "name": "Skill"},
            ],
        }) + "\n")

    monkeypatch.setenv("HOOK_LEDGER_TRANSCRIPT_TAIL_BYTES", "65536")

    snapshot = build_response_snapshot({"transcript_path": str(transcript_path)})

    assert snapshot["user_prompt"] == "Need the latest status"
    assert snapshot["assistant_response"] == "Latest answer"
    assert snapshot["tools_used"] == ["Skill"]


def test_build_response_snapshot_expands_tail_for_large_final_line(tmp_path, monkeypatch):
    transcript_path = tmp_path / "tail_only_assistant.jsonl"
    with transcript_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"role": "user", "content": "Original prompt"}) + "\n")
        fh.write(json.dumps({"role": "assistant", "content": "y" * 70000}) + "\n")

    monkeypatch.setenv("HOOK_LEDGER_TRANSCRIPT_TAIL_BYTES", "65536")

    snapshot = build_response_snapshot(
        {"transcript_path": str(transcript_path)},
        default_prompt="Prompt from ledger",
    )

    assert snapshot["user_prompt"] == "Original prompt"
    assert snapshot["assistant_response"] == "y" * 70000


def test_build_response_snapshot_marks_system_reminder_only_assistant(tmp_path):
    transcript_path = tmp_path / "system_reminder_tail.jsonl"
    with transcript_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"role": "user", "content": "Run /pre-mortem"}) + "\n")
        fh.write(json.dumps({"role": "assistant", "content": "Final pre-mortem report"}) + "\n")
        fh.write(
            json.dumps(
                {
                    "role": "assistant",
                    "content": "<system-reminder>Post-skill reminder only</system-reminder>",
                }
            )
            + "\n"
        )

    snapshot = build_response_snapshot({"transcript_path": str(transcript_path)})

    assert snapshot["user_prompt"] == "Run /pre-mortem"
    assert snapshot["assistant_response"] == ""
    assert snapshot["assistant_message_kind"] == "system_reminder"


def test_build_response_snapshot_strips_system_reminder_wrapper_from_real_response(tmp_path):
    transcript_path = tmp_path / "system_reminder_with_text.jsonl"
    with transcript_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"role": "user", "content": "Status?"}) + "\n")
        fh.write(
            json.dumps(
                {
                    "role": "assistant",
                    "content": (
                        "<system-reminder>Reminder</system-reminder>\n"
                        "The actual answer is ready."
                    ),
                }
            )
            + "\n"
        )

    snapshot = build_response_snapshot({"transcript_path": str(transcript_path)})

    assert snapshot["assistant_response"] == "The actual answer is ready."
    assert snapshot["assistant_message_kind"] == "assistant"


def teardown_module() -> None:
    os.environ.pop("HOOK_LEDGER_TRANSCRIPT_TAIL_BYTES", None)
