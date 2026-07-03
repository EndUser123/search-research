#!/usr/bin/env python3
"""Tests for hook_runner stop protocol normalization."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))
import hook_runner  # noqa: E402


def test_normalize_stop_block_exit_code():
    exit_code, stdout_text, stderr_text = hook_runner._normalize_stop_protocol(
        "Stop_bad_hook.py",
        1,
        '{"decision":"block","reason":"violation"}',
        "",
    )
    assert exit_code == 2
    assert '"decision":"block"' in stdout_text
    assert "Normalized Stop protocol" in stderr_text


def test_reject_legacy_hook_specific_output_payload():
    exit_code, stdout_text, _ = hook_runner._normalize_stop_protocol(
        "Stop_legacy_hook.py",
        0,
        '{"hookSpecificOutput":{"additionalContext":"bad payload"}}',
        "",
    )
    assert exit_code == 1
    assert "HOOK_PROTOCOL_ERROR" in stdout_text
