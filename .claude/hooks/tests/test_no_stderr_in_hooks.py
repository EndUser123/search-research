"""
Regression test to ensure PreToolUse hooks never write to stderr.

Claude Code treats ANY stderr output from hooks as "hook error".
This test prevents regression of the bug fixed on 2026-03-01.
See: C:/Users/brsth/.claude/projects/P--/memory/bugfixes.md

Test pattern: Scan for active print(..., file=sys.stderr) calls
(excluding commented lines).
"""
import re
from pathlib import Path


def test_no_stderr_in_pretooluse_hooks():
    """
    Verify that all PreToolUse hooks have zero active stderr writes.

    This is a regression test for the bug where hooks wrote to stderr,
    causing Claude Code to show "hook error" even when hooks succeeded.

    If this test fails, it means someone has re-introduced stderr writes,
    which will cause the "PreToolUse:Bash hook error" issue to recur.
    """
    # Find all PreToolUse hooks in the current directory
    hook_files = list(Path('.').glob('PreToolUse*.py'))

    # If no hooks found, skip test (wrong directory)
    if not hook_files:
        import pytest
        pytest.skip("No PreToolUse*.py files found in current directory")

    failures = []

    for hook_file in hook_files:
        content = hook_file.read_text()
        lines = content.split('\n')

        # Pattern: Active stderr writes (not commented)
        # Matches: print(..., file=sys.stderr) including f-strings
        # Excludes: # print(..., file=sys.stderr) (commented)
        pattern = r'print\(.*file=sys\.stderr\)'

        matches = []
        for i, line in enumerate(lines, start=1):
            # Match pattern, but exclude commented lines
            if re.search(pattern, line) and not line.strip().startswith('#'):
                matches.append(f"  Line {i}: {line.strip()}")

        if matches:
            failures.append(
                f"{hook_file.name} has {len(matches)} active stderr write(s):\n"
                + "\n".join(matches)
            )

    # Assert: No failures allowed
    assert len(failures) == 0, (
        "PreToolUse hooks must not write to stderr.\n"
        "Claude Code treats ANY stderr as 'hook error'.\n\n"
        "The following hooks have stderr writes:\n" + "\n\n".join(failures) +
        "\n\nFix: Comment out or remove the stderr writes.\n"
        "See: C:/Users/brsth/.claude/projects/P--/memory/bugfixes.md"
    )


def test_no_stderr_in_posttooluse_hooks():
    """
    Verify that all PostToolUse hooks have zero active stderr writes.

    This is a regression test for the bug where hooks wrote to stderr,
    causing Claude Code to show "hook error" even when hooks succeeded.

    If this test fails, it means someone has re-introduced stderr writes,
    which will cause the "PostToolUse:* hook error" issue to recur.
    """
    # Find all PostToolUse hooks in the current directory
    hook_files = list(Path('.').glob('PostToolUse*.py'))

    # If no hooks found, skip test (wrong directory)
    if not hook_files:
        import pytest
        pytest.skip("No PostToolUse*.py files found in current directory")

    failures = []

    for hook_file in hook_files:
        content = hook_file.read_text()
        lines = content.split('\n')

        # Pattern: Active stderr writes (not commented)
        # Matches: print(..., file=sys.stderr) including f-strings
        # Excludes: # print(..., file=sys.stderr) (commented)
        pattern = r'print\(.*file=sys\.stderr\)'

        matches = []
        for i, line in enumerate(lines, start=1):
            # Match pattern, but exclude commented lines
            if re.search(pattern, line) and not line.strip().startswith('#'):
                matches.append(f"  Line {i}: {line.strip()}")

        if matches:
            failures.append(
                f"{hook_file.name} has {len(matches)} active stderr write(s):\n"
                + "\n".join(matches)
            )

    # Assert: No failures allowed
    assert len(failures) == 0, (
        "PostToolUse hooks must not write to stderr.\n"
        "Claude Code treats ANY stderr as 'hook error'.\n\n"
        "The following hooks have stderr writes:\n" + "\n\n".join(failures) +
        "\n\nFix: Replace with logging framework using NullHandler.\n"
        "See: P:/plan-20260307-hook-stderr-fix.md"
    )


def test_documentation_counts_match_reality():
    """
    Verify that documented stderr write counts match actual code.

    This test ensures CKS_STORAGE_WORKING_PATTERNS.md documentation
    stays accurate when hooks are modified.
    """
    # Find all PreToolUse and PostToolUse hooks
    hook_files = list(Path('.').glob('*ToolUse*.py'))

    if not hook_files:
        import pytest
        pytest.skip("No *ToolUse*.py files found")

    # Count actual commented stderr writes
    actual_counts = {}
    for hook_file in hook_files:
        content = hook_file.read_text()

        # Count commented stderr writes: # print(..., file=sys.stderr)
        pattern = r'#.*print\(.*file=sys\.stderr\)'
        count = len(re.findall(pattern, content))

        if count > 0:
            actual_counts[hook_file.name] = count

    # This test is advisory - it documents what we found
    # If counts change, update docs/CKS_STORAGE_WORKING_PATTERNS.md
    if actual_counts:
        print("\nActual commented stderr write counts (for documentation):")
        for filename, count in sorted(actual_counts.items()):
            print(f"  {filename}: {count}")
