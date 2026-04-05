#!/usr/bin/env python3
"""
Test UserPromptSubmit hook with in-process execution via HookImporter.

This verifies that the absolute import refactoring worked correctly.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from __lib.hook_importer import HookImporter


def test_userpromptsubmit_inprocess():
    """Test UserPromptSubmit with HookImporter after absolute import refactor."""

    print("\n" + "=" * 60)
    print("Testing UserPromptSubmit In-Process Execution")
    print("=" * 60)

    # Prepare minimal input data
    input_data = {
        "prompt": "test prompt for UserPromptSubmit",
        "message": "test message",
        "session_id": "test-session-123",
        "terminal_id": "test-terminal-456",
    }

    # Save original stdin
    old_stdin = sys.stdin

    try:
        # Replace stdin with test data
        sys.stdin = io.StringIO(json.dumps(input_data))

        # Create HookImporter instance
        importer = HookImporter(HOOKS_DIR)

        print("\n📦 Loading UserPromptSubmit hook...")
        print("   Using HookImporter with dynamic module loading")

        print("\n⚙️  Executing hook in-process...")
        result = importer.execute_hook("UserPromptSubmit", timeout=15.0)

        print("\n📊 Result:")
        print(f"   Status: {'✅ SUCCESS' if result.get('ok') else '❌ FAILED'}")

        if result.get("ok"):
            print(f"   Exit code: {result.get('exit_code', 'N/A')}")
            if result.get("output"):
                output_preview = result["output"][:200]
                print(f"   Output preview: {output_preview}...")
            print("\n✅ UserPromptSubmit works with in-process execution!")
            print("   Absolute import refactoring successful!")
            assert True
            return

        print(f"   Error: {result.get('error', 'Unknown error')}")
        print("\n❌ UserPromptSubmit failed with in-process execution")
        print("   May need additional debugging")
        assert False, result

    except ImportError as e:
        print(f"\n❌ ImportError: {e}")
        print("   Absolute import refactoring may have issues")
        assert False, str(e)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        assert False, str(e)

    finally:
        sys.stdin = old_stdin


def main():
    """Run test and report results."""
    try:
        test_userpromptsubmit_inprocess()
        success = True
    except AssertionError:
        success = False

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    if success:
        print("\n✅ PASS: UserPromptSubmit works with in-process execution")
        print("\nNext steps:")
        print("1. Update settings.json to use in-process for UserPromptSubmit")
        print("2. Run full test suite for in-process hooks")
        print("3. Measure latency improvement")
    else:
        print("\n❌ FAIL: UserPromptSubmit in-process execution has issues")
        print("\nDebugging steps:")
        print("1. Check for remaining relative imports")
        print("2. Verify module path resolution")
        print("3. Review error messages above")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
