#!/usr/bin/env python3
"""Tests for PreToolUse_import_deletion_guard.py"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
HOOK_FILE = HOOKS_DIR / "PreToolUse_import_deletion_guard.py"
sys.path.insert(0, str(HOOKS_DIR))

from PreToolUse_import_deletion_guard import (
    extract_module_name,
    has_investigation_evidence,
    has_symbol_search_this_turn,
)


def run_hook(
    tool_name: str,
    file_path: str,
    old_string: str = "",
    new_string: str = "",
    *,
    content: str = "",
    edits: list[dict] | None = None,
    user_message: str = "",
    session_id: str = "test-session",
    terminal_id: str = "test-terminal",
) -> dict:
    """Run the hook and return parsed JSON output."""
    tool_input = {"file_path": file_path}
    if old_string:
        tool_input["old_string"] = old_string
    if new_string:
        tool_input["new_string"] = new_string
    if content:
        tool_input["content"] = content
    if edits is not None:
        tool_input["edits"] = edits

    input_data = {
        "tool_name": tool_name,
        "tool_input": tool_input,
        "user_message": user_message,
        "session_id": session_id,
        "terminal_id": terminal_id,
    }

    result = subprocess.run(
        [sys.executable, str(HOOK_FILE)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        cwd=HOOKS_DIR,
    )

    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        return {"raw_stdout": result.stdout, "stderr": result.stderr}


def test_allows_edit_without_import_changes():
    """Edit that doesn't touch imports should be allowed."""
    old = 'def foo():\n    return "bar"'
    new = 'def foo():\n    return "baz"'

    result = run_hook("Edit", "test.py", old, new)
    assert result.get("continue") is True


def test_allows_import_addition():
    """Adding imports should be allowed."""
    old = 'def foo():\n    return "bar"'
    new = 'import os\n\ndef foo():\n    return "bar"'

    result = run_hook("Edit", "test.py", old, new)
    assert result.get("continue") is True


def test_blocks_import_deletion_without_search():
    """Removing import without prior grep should block."""
    old = 'import os\n\ndef foo():\n    return "bar"'
    new = 'def foo():\n    return "bar"'

    result = run_hook("Edit", "test.py", old, new)
    assert result.get("continue") is False
    assert "import" in result.get("reason", "").lower()
    assert "os" in result.get("reason", "")


def test_allows_import_deletion_with_bypass_flag():
    """Bypass flag should allow deletion without search."""
    old = 'import os\n\ndef foo():\n    return "bar"'
    new = 'def foo():\n    return "bar"'

    result = run_hook("Edit", "test.py", old, new, user_message="--allow-import-removal")
    assert result.get("continue") is True


def test_skips_non_python_files():
    """Non-.py files should be skipped."""
    old = 'import os'
    new = ''

    result = run_hook("Edit", "test.md", old, new)
    assert result.get("continue") is True


def test_skips_non_mutation_operations():
    """Non-mutation tools should be skipped."""
    result = run_hook("Bash", "test.py")
    assert result.get("continue") is True


def test_handles_multiline_imports():
    """Multi-line imports with parentheses should be parsed correctly."""
    old = '''from module import (
    Foo,
    Bar,
)'''
    new = ''

    result = run_hook("Edit", "test.py", old, new)
    assert result.get("continue") is False
    assert "Foo" in result.get("reason", "") or "Bar" in result.get("reason", "")


def test_handles_from_import_aliases():
    """Import aliases should extract the base symbol name."""
    old = 'import numpy as np'
    new = ''

    result = run_hook("Edit", "test.py", old, new)
    assert result.get("continue") is False
    # Should search for 'numpy' (the real symbol), not 'np' (the alias)


def test_handles_multiple_imports_on_one_line():
    """Multiple imports on one line should all be detected."""
    old = 'import os, sys, re'
    new = ''

    result = run_hook("Edit", "test.py", old, new)
    assert result.get("continue") is False
    reason = result.get("reason", "")
    # At least one symbol should be mentioned
    assert any(s in reason for s in ["os", "sys", "re"])


def test_fail_closed_on_missing_session_id_with_import_deletion():
    """Missing session_id should fail closed (block) when imports are removed."""
    old = 'import os\n\ndef foo():\n    return "bar"'
    new = 'def foo():\n    return "bar"'

    result = run_hook("Edit", "test.py", old, new, session_id="")
    assert result.get("continue") is False
    assert "os" in result.get("reason", "")


def test_symbol_extraction_from_from_import():
    """'from module import Symbol' should extract 'Symbol'."""
    old = 'from collections import defaultdict'
    new = ''

    result = run_hook("Edit", "test.py", old, new)
    assert result.get("continue") is False
    assert "defaultdict" in result.get("reason", "")


def test_write_existing_file_blocks_import_deletion_without_search(tmp_path):
    """Write that removes imports from an existing file should be blocked."""
    file_path = tmp_path / "test.py"
    file_path.write_text("import os\n\ndef foo():\n    return os.name\n", encoding="utf-8")

    result = run_hook(
        "Write",
        str(file_path),
        content='def foo():\n    return "ok"\n',
        session_id="test-session",
        terminal_id="test-terminal",
    )

    assert result.get("continue") is False
    assert "os" in result.get("reason", "")


def test_multiedit_blocks_import_deletion_without_search():
    """MultiEdit that removes imports should be blocked."""
    edits = [
        {
            "file_path": "test.py",
            "old_string": "from collections import defaultdict\n",
            "new_string": "",
        }
    ]

    result = run_hook(
        "MultiEdit",
        "test.py",
        edits=edits,
        session_id="test-session",
        terminal_id="test-terminal",
    )

    assert result.get("continue") is False
    assert "defaultdict" in result.get("reason", "")


def test_select_string_counts_as_symbol_search():
    """PowerShell Select-String should count as symbol search."""
    tool_events = [
        {
            "name": "Bash",
            "command": 'Select-String -Path P:\\packages\\demo\\test.py -Pattern "os"',
            "ts": "2026-04-11T12:00:00Z",
        }
    ]

    assert has_symbol_search_this_turn("os", tool_events) is True



# --- extract_module_name unit tests ---


def test_extract_module_name_relative_import():
    """'from .tracing import X' → 'tracing'"""
    assert extract_module_name("from .tracing import QueryTracer") == "tracing"


def test_extract_module_name_relative_submodule():
    """'from .sub.tracing import X' → 'sub.tracing'"""
    assert extract_module_name("from .sub.tracing import Foo") == "sub.tracing"


def test_extract_module_name_absolute_from_import():
    """'from collections import X' → 'collections'"""
    assert extract_module_name("from collections import defaultdict") == "collections"


def test_extract_module_name_bare_import():
    """'import os' → 'os'"""
    assert extract_module_name("import os") == "os"


def test_extract_module_name_dotted_import():
    """'import os.path' → 'os.path'"""
    assert extract_module_name("import os.path") == "os.path"


def test_extract_module_name_non_import():
    """Non-import line returns None."""
    assert extract_module_name("def foo():") is None


# --- has_investigation_evidence unit tests ---


def test_investigation_evidence_read_of_module_path():
    """Read tool targeting the module path counts as investigation."""
    old_string = "from .tracing import QueryTracer, QueryTrace"
    events = [
        {"name": "Read", "file_path": "P:/project/core/tracing.py"},
    ]
    assert has_investigation_evidence(old_string, {"QueryTracer", "QueryTrace"}, "core/router.py", events) is True


def test_investigation_evidence_read_attempt_even_if_missing():
    """Read attempt of a missing module path still counts as investigation."""
    old_string = "from .tracing import QueryTracer"
    events = [
        {"name": "Read", "file_path": "P:/project/core/tracing.py"},
    ]
    assert has_investigation_evidence(old_string, {"QueryTracer"}, "core/router.py", events) is True


def test_investigation_evidence_git_log():
    """git log for the module path counts as investigation."""
    old_string = "from .tracing import QueryTracer"
    events = [
        {"name": "Bash", "command": "git log --oneline -- core/tracing.py"},
    ]
    assert has_investigation_evidence(old_string, {"QueryTracer"}, "core/router.py", events) is True


def test_investigation_evidence_git_status():
    """git status check for module counts as investigation."""
    old_string = "from .tracing import QueryTracer"
    events = [
        {"name": "Bash", "command": "git status -- core/tracing.py"},
    ]
    assert has_investigation_evidence(old_string, {"QueryTracer"}, "core/router.py", events) is True


def test_investigation_evidence_grep_of_symbol():
    """Grep for a removed symbol counts as investigation."""
    old_string = "from .tracing import QueryTracer"
    events = [
        {"name": "Grep", "pattern": "QueryTracer"},
    ]
    assert has_investigation_evidence(old_string, {"QueryTracer"}, "core/router.py", events) is True


def test_investigation_evidence_grep_of_module_name():
    """Grep for the module name counts as investigation."""
    old_string = "from .tracing import QueryTracer"
    events = [
        {"name": "Grep", "pattern": "tracing"},
    ]
    assert has_investigation_evidence(old_string, {"QueryTracer"}, "core/router.py", events) is True


def test_investigation_evidence_no_match():
    """Unrelated tool events don't count as investigation."""
    old_string = "from .tracing import QueryTracer"
    events = [
        {"name": "Read", "file_path": "P:/project/core/router.py"},
        {"name": "Bash", "command": "git log -- oneline"},
    ]
    assert has_investigation_evidence(old_string, {"QueryTracer"}, "core/router.py", events) is False


def test_investigation_evidence_empty_events():
    """Empty events list returns False."""
    old_string = "from .tracing import QueryTracer"
    assert has_investigation_evidence(old_string, {"QueryTracer"}, "core/router.py", []) is False


def test_investigation_evidence_bash_grep_for_symbol():
    """Bash grep command for removed symbol counts."""
    old_string = "from .tracing import QueryTracer"
    events = [
        {"name": "Bash", "command": 'grep -r "QueryTracer" --include="*.py" P:/'},
    ]
    assert has_investigation_evidence(old_string, {"QueryTracer"}, "core/router.py", events) is True


# --- Regression test for the original incident ---


def test_regression_import_deletion_without_read_or_grep():
    """Removing import without Read or git log or grep should block.

    This is the exact scenario from the incident:
    core/tracing.py was missing, LLM removed the import line
    without investigating why the file was missing.
    """
    old = "from .tracing import QueryTracer, QueryTrace  # TASK-3: Query tracing"
    new = ""

    result = run_hook("Edit", "core/router_async.py", old, new)
    assert result.get("continue") is False
    assert "tracing" in result.get("reason", "").lower() or "QueryTracer" in result.get("reason", "")


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
