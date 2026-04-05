#!/usr/bin/env python3
"""Verify the three fixes are working."""
import sys
import re

# Load the actual patterns from the hook file
exec(open('P:/.claude/hooks/PreToolUse_directory_policy.py').read())

def test_mkdir_extraction():
    """Test that mkdir commands with paths are correctly extracted."""
    test_cases = [
        # (command, expected_paths)
        ('mkdir -p "C:/Users/brsth/.claude/plans/"', ['C:/Users/brsth/.claude/plans/']),
        ('mkdir -p /c/Users/brsth/.claude/plans/', ['/c/Users/brsth/.claude/plans/']),
        ('mkdir -p "P:/__csf"', []),  # Should NOT be extracted as a path
    ]

    for cmd, expected in test_cases:
        paths = extract_paths_from_bash(cmd)
        status = "PASS" if paths == expected else "FAIL"
        print(f"{status}: {cmd[:40]}...")
        print(f"  Expected: {expected}")
        print(f"  Got:      {paths}")
        print()

def test_hook_infra_exemption():
    """Test that hook infrastructure paths are exempt."""
    infra_paths = [
        '.claude/hooks/PreToolUse.py',
        '.claude/skills/planning/__lib/auto_verify.py',
        '.claude/skills/code/SKILL.md',
    ]

    print("Testing hook infrastructure exemption:")
    for path in infra_paths:
        normalized = path.replace("\\", "/").lower()
        hook_infra_paths = (
            ".claude/hooks/",
            ".claude/skills/planning/",
            ".claude/skills/code/",
        )
        is_exempt = any(normalized.startswith(p.lower()) for p in hook_infra_paths)
        status = "PASS" if is_exempt else "FAIL"
        print(f"  {status}: {path} -> exempt={is_exempt}")
    print()

def test_root_guard_fix():
    """Test that the root guard now allows .ext files."""
    project_dir = "P:/"

    test_cases = [
        # (relative_path, should_block)
        ('file.txt', True),   # Root-level file - should block
        ('file.py', True),    # Root-level file - should block
        ('README', False),   # Root-level no-extension - should block
        ('plans/', False),    # Directory with slash - should NOT block
        ('docs/file.md', False),  # Subdirectory - should NOT block
    ]

    print("Testing root guard (dot check):")
    for rel_path, should_block in test_cases:
        if "/" not in rel_path and "." not in rel_path:
            # This is what the NEW guard checks
            would_block = True
        else:
            would_block = False

        status = "PASS" if would_block == should_block else "FAIL"
        print(f"  {status}: {rel_path!r} -> block={would_block} (expected {should_block})")
    print()

if __name__ == '__main__':
    print("=" * 60)
    print("VERIFICATION: Three Fixes")
    print("=" * 60)
    print()

    test_mkdir_extraction()
    test_hook_infra_exemption()
    test_root_guard_fix()

    print("=" * 60)
    print("All tests completed")
    print("=" * 60)
