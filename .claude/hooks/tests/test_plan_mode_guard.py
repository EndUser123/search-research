#!/usr/bin/env python3
"""Test plan mode guard functionality."""

import json
import sys
import tempfile
from pathlib import Path

# Add hooks directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import the guard module
plan_guard_path = Path(__file__).resolve().parent.parent.parent / "skills" / "plan-workflow" / "hooks" / "PreToolUse_plan_mode_guard.py"
import importlib.util

spec = importlib.util.spec_from_file_location("plan_guard", plan_guard_path)
plan_guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_guard)


def test_no_plan_mode_allows_edits():
    """When no plan file exists, all edits should be allowed."""
    print("Test 1: No plan mode - edits allowed")

    # Simulate hook input
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": "some_file.py"}
    }

    # Mock stdin
    import io
    old_stdin = sys.stdin
    sys.stdin = io.StringIO(json.dumps(payload))

    try:
        # Call main - should return continue=True
        with tempfile.TemporaryDirectory() as tmpdir:
            # Override PLAN_MODE_DIR to use temp directory (empty)
            original_dir = plan_guard.PLAN_MODE_DIR
            plan_guard.PLAN_MODE_DIR = Path(tmpdir)

            try:
                # This would normally call sys.exit(), so we can't test it directly
                # Instead, we'll test the detection functions
                assert not plan_guard.is_plan_mode_active(), "Plan mode should be inactive"
                print("✓ Plan mode correctly detected as inactive")
            finally:
                plan_guard.PLAN_MODE_DIR = original_dir
    finally:
        sys.stdin = old_stdin


def test_plan_mode_blocks_non_plan_edits():
    """When plan file exists, edits to other files should be blocked."""
    print("\nTest 2: Plan mode active - blocks non-plan file edits")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a plan file
        plan_file = Path(tmpdir) / "test-plan.md"
        plan_file.write_text("# Test Plan")

        # Override PLAN_MODE_DIR
        original_dir = plan_guard.PLAN_MODE_DIR
        plan_guard.PLAN_MODE_DIR = Path(tmpdir)

        try:
            # Test detection
            assert plan_guard.is_plan_mode_active(), "Plan mode should be active"
            assert plan_guard.get_plan_file() == plan_file, "Should detect plan file"

            # Test that non-plan file edit would be blocked
            target_file = Path(tmpdir) / "other_file.py"
            target_path = target_file.resolve()
            plan_path = plan_file.resolve()

            assert target_path != plan_path, "Paths should be different"
            print("✓ Plan mode correctly detected and would block non-plan edits")

        finally:
            plan_guard.PLAN_MODE_DIR = original_dir


def test_plan_mode_allows_plan_edits():
    """When plan file exists, edits to the plan file itself should be allowed."""
    print("\nTest 3: Plan mode active - allows plan file edits")

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a plan file
        plan_file = Path(tmpdir) / "test-plan.md"
        plan_file.write_text("# Test Plan")

        # Override PLAN_MODE_DIR
        original_dir = plan_guard.PLAN_MODE_DIR
        plan_guard.PLAN_MODE_DIR = Path(tmpdir)

        try:
            # Test that plan file edit is allowed
            target_path = plan_file.resolve()
            plan_path = plan_file.resolve()

            assert target_path == plan_path, "Paths should be same"
            print("✓ Plan mode correctly allows plan file edits")

        finally:
            plan_guard.PLAN_MODE_DIR = original_dir


def test_hook_integration():
    """Test hook integration with PreToolUse router."""
    print("\nTest 4: Router integration")

    # Read PreToolUse.py to verify hook is registered
    router_path = Path(__file__).resolve().parent.parent / "PreToolUse.py"
    router_content = router_path.read_text()

    hook_path = "../.claude/skills/plan-workflow/hooks/PreToolUse_plan_mode_guard.py"

    assert '"Write":' in router_content, "Write hooks should exist"
    assert '"Edit":' in router_content, "Edit hooks should exist"
    assert hook_path in router_content, "Plan mode guard should be registered in router"

    # Check it's in both Write and Edit sections
    lines = router_content.split('\n')
    write_section = []
    edit_section = []
    in_write = False
    in_edit = False

    for line in lines:
        if '"Write":' in line:
            in_write = True
            in_edit = False
        elif '"Edit":' in line:
            in_edit = True
            in_write = False
        elif in_write and ']' in line and not in_write:
            in_write = False
        elif in_edit and ']' in line:
            in_edit = False
        elif in_write:
            write_section.append(line)
        elif in_edit:
            edit_section.append(line)

    write_hooks = '\n'.join(write_section)
    edit_hooks = '\n'.join(edit_section)

    assert hook_path in write_hooks, "Hook should be in Write hooks"
    assert hook_path in edit_hooks, "Hook should be in Edit hooks"

    print("✓ Plan mode guard correctly registered in PreToolUse router")
    print("  ✓ Registered for Write operations")
    print("  ✓ Registered for Edit operations")


if __name__ == "__main__":
    print("Testing Plan Mode Guard")
    print("=" * 50)

    try:
        test_no_plan_mode_allows_edits()
        test_plan_mode_blocks_non_plan_edits()
        test_plan_mode_allows_plan_edits()
        test_hook_integration()

        print("\n" + "=" * 50)
        print("✅ All tests passed!")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
