#!/usr/bin/env python3
"""Routing tests for dependency verification through PreToolUse."""

import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import PreToolUse
import PreToolUse_dependency_verification_gate
from __lib.hook_importer import HookImporter


def test_bash_hook_list_includes_dependency_verification_gate():
    """Bash tool routing should include dependency verification in the main router."""
    assert "PreToolUse_dependency_verification_gate.py" in PreToolUse.TOOL_HOOKS["Bash"]


def test_pretouluse_run_hook_uses_dependency_gate():
    """PreToolUse.run_hook should execute the dependency gate in-process for Bash installs."""
    data = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "uv pip install mcp fastmcp",
            "terminal_id": "routing-test-terminal",
        },
    }

    result = PreToolUse.run_hook("PreToolUse_dependency_verification_gate.py", data)

    assert result is not None
    assert result.get("decision") == "block"
    assert result.get("packages") == ["mcp", "fastmcp"]
    assert (
        PreToolUse.IN_PROCESS_HOOKS["PreToolUse_dependency_verification_gate.py"]
        is PreToolUse_dependency_verification_gate.run
    )


def test_pretouluse_importer_output_includes_explicit_block_decision():
    """Importer-driven PreToolUse blocks should expose a normal block payload."""
    input_data = {
        "tool_name": "Bash",
        "tool_input": {
            "command": "uv pip install mcp fastmcp",
            "terminal_id": "routing-test-terminal-2",
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
    assert payload.get("continue") is False
    assert payload.get("blocking_hook") == "PreToolUse_dependency_verification_gate.py"
