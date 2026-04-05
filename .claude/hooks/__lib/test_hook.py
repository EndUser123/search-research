#!/usr/bin/env python3
"""Quick hook testing utility.

Usage:
    python -m __lib.test_hook <hook_name> [tool_name] [json_input]

Examples:
    # Test PostToolUse hook with Bash tool
    python -m __lib.test_hook post_tool_use_change_propagation Bash '{"command": "echo test"}'

    # Test UserPromptSubmit hook
    python -m __lib.test_hook UserPromptSubmit_router prompt '{"prompt": "continue"}'
"""

import json
import subprocess
import sys
import time
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent


def build_test_input(tool_name: str, extra_json: str = "{}") -> str:
    """Build test JSON input for a hook."""
    try:
        extra = json.loads(extra_json) if extra_json else {}
    except json.JSONDecodeError:
        extra = {}

    if tool_name == "prompt":
        # UserPromptSubmit format
        return json.dumps({"prompt": extra.get("prompt", "test prompt")})
    else:
        # Tool use format
        return json.dumps({
            "tool_name": tool_name,
            "tool_input": extra,
            "tool_response": {"stdout": "test output", "exit_code": 0}
        })


def test_hook(hook_name: str, tool_name: str = "Bash", extra_json: str = "{}"):
    """Test a hook with simulated input."""
    # Find hook file
    hook_file = HOOKS_DIR / f"{hook_name}.py"
    if not hook_file.exists():
        # Try subdirectories
        for subdir in ["PreToolUse", "PostToolUse", "UserPromptSubmit"]:
            alt = HOOKS_DIR / subdir / f"{hook_name}.py"
            if alt.exists():
                hook_file = alt
                break

    if not hook_file.exists():
        print(f"❌ Hook not found: {hook_name}")
        print(f"   Searched: {HOOKS_DIR}")
        return 1

    # Build input
    test_input = build_test_input(tool_name, extra_json)

    print(f"🧪 Testing: {hook_file.name}")
    print(f"   Input: {test_input[:100]}{'...' if len(test_input) > 100 else ''}")
    print()

    # Run hook
    start = time.time()
    result = subprocess.run(
        [sys.executable, str(hook_file)],
        input=test_input,
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(HOOKS_DIR)
    )
    elapsed = time.time() - start

    # Report results
    print(f"⏱️  Time: {elapsed*1000:.0f}ms")
    print(f"📤 Exit: {result.returncode}")

    if result.stdout:
        print(f"📝 Stdout: {result.stdout.strip()[:500]}")
    if result.stderr:
        print(f"⚠️  Stderr: {result.stderr.strip()[:500]}")

    if result.returncode == 0:
        print("\n✅ Hook passed")
    elif result.returncode == 124:
        print("\n❌ Hook TIMEOUT")
    else:
        print(f"\n❌ Hook FAILED (exit {result.returncode})")

    return result.returncode


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    hook_name = sys.argv[1]
    tool_name = sys.argv[2] if len(sys.argv) > 2 else "Bash"
    extra_json = sys.argv[3] if len(sys.argv) > 3 else "{}"

    sys.exit(test_hook(hook_name, tool_name, extra_json))
