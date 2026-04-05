#!/usr/bin/env python3
"""Verification script for Stop_behavior_gates import fix."""

import json
import subprocess
import sys
from pathlib import Path


def test_old_behavior():
    """Simulate OLD broken behavior (project root in sys.path)."""
    print("=" * 60)
    print("OLD (BROKEN) BEHAVIOR")
    print("=" * 60)
    print("Adding project root to sys.path before importing...")

    # Simulate old code: add P:\ to sys.path
    project_root = Path(__file__).resolve().parents[2]  # P:\ from P:\.claude\hooks\test\
    test_code = f"""
import sys
sys.path.insert(0, r'{project_root}')
try:
    import Stop_behavior_gates
    print("UNEXPECTED: Import succeeded")
except ImportError as e:
    print(f"ERROR: {{e}}")
    import sys
    sys.exit(1)
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        cwd=str(Path(__file__).resolve().parent.parent.parent)
    )

    output = result.stdout.decode("utf-8", errors="replace")
    if result.returncode != 0:
        print(f"✓ Error reproduced: {output.strip()}")
        return True
    else:
        print(f"✗ Unexpected success: {output.strip()}")
        return False

def test_new_behavior():
    """Test NEW fixed behavior (direct import)."""
    print("\n" + "=" * 60)
    print("NEW (FIXED) BEHAVIOR")
    print("=" * 60)
    print("Importing directly (hooks dir already in sys.path)...")

    test_code = """
import sys
from pathlib import Path
hooks_dir = Path('.claude/hooks').resolve()
sys.path.insert(0, str(hooks_dir))
try:
    from Stop_behavior_gates import check_gate3_agreement
    print("SUCCESS: Import works")
    import sys
    sys.exit(0)
except ImportError as e:
    print(f"ERROR: {{e}}")
    import sys
    sys.exit(1)
"""

    result = subprocess.run(
        [sys.executable, "-c", test_code],
        capture_output=True,
        cwd=str(Path(__file__).resolve().parent.parent.parent)
    )

    output = result.stdout.decode("utf-8", errors="replace")
    if result.returncode == 0:
        print(f"✓ {output.strip()}")
        return True
    else:
        print(f"✗ {output.strip()}")
        return False

def test_actual_hook():
    """Test actual Stop.py hook execution."""
    print("\n" + "=" * 60)
    print("ACTUAL HOOK EXECUTION TEST")
    print("=" * 60)

    test_payload = {
        "response": "I agree with your suggestion",
        "tool_calls": "[]"
    }

    result = subprocess.run(
        [sys.executable, "P:/.claude/hooks/Stop.py"],
        input=json.dumps(test_payload).encode(),
        capture_output=True,
        timeout=5,
        cwd="P:\\"
    )

    stderr_text = result.stderr.decode("utf-8", errors="replace")

    print(f"Exit code: {result.returncode}")

    if "No module named 'Stop_behavior_gates'" in stderr_text:
        print("✗ IMPORT ERROR DETECTED")
        print(f"stderr: {stderr_text}")
        return False
    elif stderr_text:
        print("✓ No import errors (warnings are OK)")
        print(f"stderr: {stderr_text}")
        return True
    else:
        print("✓ Clean execution (no stderr)")
        return True

if __name__ == "__main__":
    old_broken = test_old_behavior()
    new_fixed = test_new_behavior()
    hook_works = test_actual_hook()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Old behavior (broken): {'✓ Error reproduced' if old_broken else '✗ Not reproduced'}")
    print(f"New behavior (fixed): {'✓ Works' if new_fixed else '✗ Failed'}")
    print(f"Actual hook test: {'✓ Passed' if hook_works else '✗ Failed'}")
    print()

    if new_fixed and hook_works:
        print("✅ FIX VERIFIED: Import errors resolved!")
        sys.exit(0)
    else:
        print("❌ FIX FAILED: Issues detected")
        sys.exit(1)
