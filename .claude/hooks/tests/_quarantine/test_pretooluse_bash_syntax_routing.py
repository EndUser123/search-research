#!/usr/bin/env python3
"""Routing tests for bash syntax normalization through PreToolUse."""

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "__lib"))

import PreToolUse
from __lib.hook_importer import HookImporter


def test_bash_hook_list_includes_bash_syntax_validator():
    """The active Bash hook list should run the syntax validator first."""
    assert PreToolUse.TOOL_HOOKS["Bash"][0] == "PreToolUse_bash_syntax_validator.py"


def test_pretouluse_importer_normalizes_drive_paths_for_python_scripts():
    """PreToolUse should rewrite safe Windows drive paths before Bash execution."""
    input_data = {
        "tool_name": "Bash",
        "tool_input": {
            "command": 'python "P:\\.claude\\hooks\\PreToolUse.py"',
            "terminal_id": "bash-syntax-routing-1",
        },
    }

    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO(json.dumps(input_data))
        importer = HookImporter(Path(__file__).resolve().parent.parent)
        result = importer.execute_hook("PreToolUse")
    finally:
        sys.stdin = old_stdin

    assert result.get("ok") is True
    payload = json.loads(result.get("output", "{}"))
    assert payload.get("continue") is True
    assert payload.get("tool_input", {}).get("command") == 'python "P:/.claude/hooks/PreToolUse.py"'


def test_pretouluse_importer_blocks_missing_python_script_path():
    """Missing Python script paths should be blocked by PreToolUse before execution."""
    input_data = {
        "tool_name": "Bash",
        "tool_input": {
            "command": 'python "P:\\.claude\\skills\\plan-workflow\\lib\\plan_builder.py"',
            "terminal_id": "bash-syntax-routing-2",
        },
    }

    old_stdin = sys.stdin
    try:
        sys.stdin = io.StringIO(json.dumps(input_data))
        importer = HookImporter(Path(__file__).resolve().parent.parent)
        result = importer.execute_hook("PreToolUse")
    finally:
        sys.stdin = old_stdin

    assert result.get("ok") is True
    payload = json.loads(result.get("output", "{}"))
    assert payload.get("decision") == "block"
    assert payload.get("blocking_hook") == "PreToolUse_bash_syntax_validator.py"
    assert "plan_builder.py" in payload.get("reason", "")
