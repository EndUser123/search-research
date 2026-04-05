"""
Integration tests for anti_lazy_diff_nudge.py PostToolUse hook.

Tests the template visibility enforcement hook that nudges for diffs and explanations
when arch/ files are edited.
"""

import json
import sys
from pathlib import Path

# Add hooks directory to path for imports
hooks_dir = Path(__file__).parent.parent
sys.path.insert(0, str(hooks_dir))


def _run_hook(tool_name: str, tool_input: dict, tool_response: dict = None) -> dict:
    """Helper to run the hook and parse JSON output."""
    from anti_lazy_diff_nudge import main as hook_main

    input_data = {
        "tool_name": tool_name,
        "tool_input": tool_input,
        "tool_response": tool_response or {},
    }

    # Monkey stdin
    import io

    old_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps(input_data))

    # Monkey stdout - use TextIOWrapper for Python 3.14 compatibility
    old_stdout = sys.stdout
    buffer = io.BytesIO()
    new_stdout = io.TextIOWrapper(buffer, encoding="utf-8")

    sys.stdout = new_stdout

    try:
        hook_main()
    except SystemExit:
        # Hook calls sys.exit(0) - this is expected behavior
        pass
    finally:
        sys.stdin = old_stdin
        # Restore stdout BEFORE flushing to avoid I/O on closed file
        sys.stdout = old_stdout
        # Now flush the TextIOWrapper which writes to the buffer
        if not new_stdout.closed:
            new_stdout.flush()

    output = buffer.getvalue().decode("utf-8")

    # Return empty dict if no output
    if not output.strip():
        return {}

    return json.loads(output)


def test_non_arch_files_pass_through():
    """Non-arch files should return empty output (no nudge)."""
    result = _run_hook(tool_name="Write", tool_input={"path": "src/app.py", "content": "code"})

    assert result == {}, f"Expected empty output, got: {result}"


def test_edit_non_arch_skips():
    """Edit operations on non-arch files should not trigger nudge."""
    result = _run_hook(
        tool_name="Edit",
        tool_input={"path": "tests/test_example.py", "old_string": "old", "new_string": "new"},
    )

    assert result == {}, f"Expected empty output for non-arch Edit, got: {result}"


def test_arch_file_write_triggers_nudge():
    """Write operations on arch/ files should trigger visibility nudge."""
    result = _run_hook(
        tool_name="Write", tool_input={"path": "arch/behavior-template.md", "content": "# Template"}
    )

    assert "hookSpecificOutput" in result
    assert "additionalContext" in result["hookSpecificOutput"]

    context = result["hookSpecificOutput"]["additionalContext"]
    assert "TEMPLATE UPDATE VISIBILITY REQUIRED" in context
    assert "arch/behavior-template.md" in context
    assert "Unified diff" in context
    assert "recurring mistake" in context.lower() or "failure mode" in context.lower()


def test_claude_arch_file_triggers_nudge():
    """Files in .claude/arch/ should trigger nudge."""
    result = _run_hook(
        tool_name="Edit",
        tool_input={
            "path": ".claude/arch/base.md",
            "old_string": "old pattern",
            "new_string": "new pattern",
        },
    )

    assert "hookSpecificOutput" in result
    context = result["hookSpecificOutput"]["additionalContext"]
    assert ".claude/arch/base.md" in context


def test_skill_md_files_trigger_nudge():
    """SKILL.md files should trigger nudge as behavior templates."""
    result = _run_hook(
        tool_name="Edit",
        tool_input={
            "path": "packages/arch/skill/SKILL.md",
            "old_string": "old",
            "new_string": "new",
        },
    )

    assert "hookSpecificOutput" in result
    context = result["hookSpecificOutput"]["additionalContext"]
    assert "SKILL.md" in context or "template-like" in context


def test_nested_arch_path_detection():
    """Nested arch/ paths should be detected."""
    result = _run_hook(
        tool_name="Write", tool_input={"path": "some/deep/arch/behavior.md", "content": "x"}
    )

    assert "hookSpecificOutput" in result


def test_windows_path_normalization():
    """Windows backslash paths should be normalized correctly."""
    result = _run_hook(
        tool_name="Write", tool_input={"path": r"arch\behavior-template.md", "content": "x"}
    )

    assert "hookSpecificOutput" in result
    # Path should be normalized in output
    context = result["hookSpecificOutput"]["additionalContext"]
    assert "arch/" in context or "behavior-template.md" in context


def test_non_write_edit_tools_skipped():
    """Non-Write/Edit tools should return empty output."""
    for tool in ["Bash", "Read", "Grep", "Glob"]:
        result = _run_hook(tool_name=tool, tool_input={"path": "arch/anything.md"})

        assert result == {}, f"{tool} should pass through, got: {result}"


def test_empty_path_returns_empty():
    """Empty or missing path should return empty output."""
    result = _run_hook(tool_name="Write", tool_input={"path": "", "content": "x"})

    assert result == {}


def test_nudge_message_quality():
    """The nudge message should contain all required elements."""
    result = _run_hook(
        tool_name="Edit",
        tool_input={"path": "arch/base.md", "old_string": "pattern", "new_string": "improved"},
    )

    context = result["hookSpecificOutput"]["additionalContext"]

    # Required elements (case-insensitive matching)
    required_phrases = [
        "TEMPLATE UPDATE VISIBILITY REQUIRED",
        "Unified diff",
        "1–2 sentences",
        "recurring mistake",
        "Why this matters",
    ]

    for phrase in required_phrases:
        assert phrase in context, f"Missing required phrase: '{phrase}'"


def test_path_with_claude_arch_prefix():
    """Files with .claude/arch/ prefix should be detected."""
    result = _run_hook(
        tool_name="Write",
        tool_input={"path": ".claude/skills/arch/resources/base.md", "content": "x"},
    )

    assert "hookSpecificOutput" in result


def test_packages_arch_skill_pattern():
    """packages/arch/skill/ pattern should trigger nudge."""
    result = _run_hook(
        tool_name="Edit",
        tool_input={
            "path": "packages/arch/skill/resources/base.md",
            "old_string": "old",
            "new_string": "new",
        },
    )

    assert "hookSpecificOutput" in result


def test_claude_skills_arch_pattern():
    """.claude/skills/arch/ pattern should trigger nudge."""
    result = _run_hook(
        tool_name="Write", tool_input={"path": ".claude/skills/arch/test.md", "content": "x"}
    )

    assert "hookSpecificOutput" in result


def test_hooks_import():
    """Verify the hook module can be imported."""
    from anti_lazy_diff_nudge import _generate_nudge, _is_arch_file, main

    assert callable(main)
    assert callable(_is_arch_file)
    assert callable(_generate_nudge)


def test_is_arch_file_function():
    """Direct unit test of _is_arch_file function."""
    from anti_lazy_diff_nudge import _is_arch_file

    # Positive cases
    assert _is_arch_file("arch/base.md") == True
    assert _is_arch_file(".claude/arch/base.md") == True
    assert _is_arch_file("some/path/arch/file.md") == True
    assert _is_arch_file("packages/arch/skill/test.md") == True
    assert _is_arch_file(".claude/skills/arch/test.md") == True
    assert _is_arch_file("path/SKILL.md") == True
    assert _is_arch_file(r"arch\template.md") == True  # Windows path

    # Negative cases
    assert _is_arch_file("src/app.py") == False
    assert _is_arch_file("tests/test_example.py") == False
    assert _is_arch_file("README.md") == False
    assert _is_arch_file("") == False
    assert _is_arch_file(None) == False


def test_generate_nudge_function():
    """Direct unit test of _generate_nudge function."""
    from anti_lazy_diff_nudge import _generate_nudge

    nudge = _generate_nudge("arch/base.md")

    assert "TEMPLATE UPDATE VISIBILITY REQUIRED" in nudge
    assert "arch/base.md" in nudge
    assert "Unified diff" in nudge
    assert "1–2 sentences" in nudge
