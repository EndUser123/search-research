"""Integration test: PreToolUse modify decision protocol."""
import json
import subprocess
import sys
from pathlib import Path


def test_pretooluse_modify_handling():
    """
    RED test: Verify PreToolUse.py handles modify decision.

    This test FAILS until modify handling is implemented in PreToolUse.py.
    Expected behavior: Hook returns modify → tool_input is updated → continue processing
    Actual behavior (current): Hook returns modify → treated as unknown decision → blocked or ignored
    """
    # Create a test hook that returns modify decision
    test_hook = Path("P:/.claude/hooks/tests/test_modify_protocol/fixtures/modify_test_hook.py")
    test_hook.parent.mkdir(parents=True, exist_ok=True)

    test_hook.write_text("""import sys
import json

# Read input from stdin
data = json.loads(sys.stdin.read())

# Return modify decision with corrected command
result = {
    "decision": "modify",
    "tool_input": {
        "command": 'ls "P:/.claude/hooks"'  # Fixed: backslashes → forward slashes
    }
}

# Write output to stdout
print(json.dumps(result))
sys.exit(0)
""")

    # Create test input
    test_input = {
        "tool_name": "Bash",
        "tool_input": {
            "command": 'ls "P:\\.claude\\hooks"'  # Windows backslashes
        }
    }

    # Run PreToolUse with our test hook
    pretooluse_path = Path("P:/.claude/hooks/PreToolUse.py")

    # Create a minimal settings.json with only our test hook
    test_settings = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": ".*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python {test_hook}",
                            "timeout": 5
                        }
                    ]
                }
            ]
        }
    }

    # Save test settings temporarily
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_settings, f)
        test_settings_path = f.name

    try:
        # Run PreToolUse.py with test settings
        env = {**subprocess.os.environ, "CLAUDE_SETTINGS_PATH": test_settings_path}
        result = subprocess.run(
            [sys.executable, str(pretooluse_path)],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )

        output = result.stdout.strip()

        # Parse output
        if output == "{}":
            # Current behavior: modify decision ignored → allow
            print("✗ FAIL: modify decision was ignored (returned empty allow)")
            print("  Expected: Modified tool_input in output or continue:true")
            print("  Actual: Empty allow ({} means allow without modification)")
            return False
        elif output:
            try:
                parsed = json.loads(output)
                if parsed.get("continue") is False:
                    # Current behavior: modify decision treated as block
                    print("✗ FAIL: modify decision caused block")
                    print(f"  Output: {parsed}")
                    return False
                elif "tool_input" in parsed:
                    # Expected behavior: modify decision returned modified input
                    print("✓ PASS: modify decision handled correctly")
                    print(f"  Modified tool_input: {parsed['tool_input']}")
                    return True
                else:
                    print(f"✗ FAIL: Unexpected output format: {parsed}")
                    return False
            except json.JSONDecodeError as e:
                print(f"✗ FAIL: Invalid JSON output: {output}")
                print(f"  Error: {e}")
                return False
        else:
            print("✗ FAIL: No output from PreToolUse.py")
            return False

    finally:
        # Cleanup
        Path(test_settings_path).unlink(missing_ok=True)
        if test_hook.exists():
            test_hook.unlink()


def test_backward_compat_block():
    """Verify block decision still works (backward compatibility)."""
    test_hook = Path("P:/.claude/hooks/tests/test_modify_protocol/fixtures/block_test_hook.py")
    test_hook.parent.mkdir(parents=True, exist_ok=True)

    test_hook.write_text("""import sys
import json

data = json.loads(sys.stdin.read())

result = {
    "decision": "block",
    "reason": "Test block"
}

print(json.dumps(result))
sys.exit(0)
""")

    test_input = {
        "tool_name": "Bash",
        "tool_input": {"command": "ls P:/.claude/hooks"}
    }

    pretooluse_path = Path("P:/.claude/hooks/PreToolUse.py")

    test_settings = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": ".*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python {test_hook}",
                            "timeout": 5
                        }
                    ]
                }
            ]
        }
    }

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_settings, f)
        test_settings_path = f.name

    try:
        env = {**subprocess.os.environ, "CLAUDE_SETTINGS_PATH": test_settings_path}
        result = subprocess.run(
            [sys.executable, str(pretooluse_path)],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )

        # Should exit with code 2 (block)
        if result.returncode == 2:
            print("✓ PASS: block decision works (exit code 2)")
            return True
        else:
            print(f"✗ FAIL: block decision didn't block (exit code {result.returncode})")
            return False

    finally:
        Path(test_settings_path).unlink(missing_ok=True)
        if test_hook.exists():
            test_hook.unlink()


def test_backward_compat_none():
    """Verify None return still allows (backward compatibility)."""
    test_hook = Path("P:/.claude/hooks/tests/test_modify_protocol/fixtures/none_test_hook.py")
    test_hook.parent.mkdir(parents=True, exist_ok=True)

    # Hook that prints nothing (returns None equivalent)
    test_hook.write_text("""import sys
import json

# Read input but don't return anything
data = json.loads(sys.stdin.read())

# Print nothing (equivalent to None/allow)
# Just exit successfully
sys.exit(0)
""")

    test_input = {
        "tool_name": "Bash",
        "tool_input": {"command": "ls P:/.claude/hooks"}
    }

    pretooluse_path = Path("P:/.claude/hooks/PreToolUse.py")

    test_settings = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": ".*",
                    "hooks": [
                        {
                            "type": "command",
                            "command": f"python {test_hook}",
                            "timeout": 5
                        }
                    ]
                }
            ]
        }
    }

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_settings, f)
        test_settings_path = f.name

    try:
        env = {**subprocess.os.environ, "CLAUDE_SETTINGS_PATH": test_settings_path}
        result = subprocess.run(
            [sys.executable, str(pretooluse_path)],
            input=json.dumps(test_input),
            capture_output=True,
            text=True,
            env=env,
            timeout=10
        )

        # Should exit with code 0 (allow)
        output = result.stdout.strip()
        if result.returncode == 0 and (output == "{}" or output == ""):
            print("✓ PASS: None return works (allow, exit 0)")
            return True
        else:
            print(f"✗ FAIL: None return didn't allow (exit {result.returncode}, output: {output})")
            return False

    finally:
        Path(test_settings_path).unlink(missing_ok=True)
        if test_hook.exists():
            test_hook.unlink()


if __name__ == "__main__":
    print("=" * 70)
    print("RED PHASE: Integration tests (should FAIL until feature implemented)")
    print("=" * 70)

    print("\n[1/3] Test modify decision handling (expected FAIL):")
    modify_pass = test_pretooluse_modify_handling()

    print("\n[2/3] Test backward compat - block (expected PASS):")
    block_pass = test_backward_compat_block()

    print("\n[3/3] Test backward compat - None (expected PASS):")
    none_pass = test_backward_compat_none()

    print("\n" + "=" * 70)
    print("RESULTS:")
    print(f"  modify handling: {'PASS (feature implemented!)' if modify_pass else 'FAIL (expected - feature not implemented)'}")
    print(f"  block compat: {'PASS' if block_pass else 'FAIL (regression!)'}")
    print(f"  none compat: {'PASS' if none_pass else 'FAIL (regression!)'}")
    print("=" * 70)

    # Exit with error if modify test failed (expected in RED phase)
    sys.exit(0 if modify_pass else 1)
