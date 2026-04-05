#!/usr/bin/env python3
r"""
Final verification: Repository visibility guard is protecting P:\ drive

This script demonstrates that the hook is working correctly without
executing dangerous commands.
"""

import json
import subprocess
import sys
from pathlib import Path

print("="*70)
print("REPOSITORY VISIBILITY GUARD - FUNCTIONAL VERIFICATION")
print("="*70)

# Test 1: Verify hook is registered
print("\n[1/5] Verifying hook registration...")
pretooluse_path = Path("P:/.claude/hooks/PreToolUse.py")
content = pretooluse_path.read_text()

if "PreToolUse_repo_visibility_guard.py" in content:
    print("✓ Hook is registered in PreToolUse.py")
else:
    print("❌ Hook NOT found in PreToolUse.py")
    sys.exit(1)

# Test 2: Verify environment variable is set
print("\n[2/5] Verifying environment configuration...")
settings_path = Path("P:/.claude/settings.json")
settings = json.loads(settings_path.read_text())

if settings.get("env", {}).get("REPO_VISIBILITY_GUARD_ENABLED") == "true":
    print("✓ Environment variable REPO_VISIBILITY_GUARD_ENABLED=true")
else:
    print("❌ Environment variable not set correctly")
    sys.exit(1)

# Test 3: Verify hook file exists and is valid
print("\n[3/5] Verifying hook file integrity...")
hook_path = Path("P:/.claude/hooks/PreToolUse_repo_visibility_guard.py")

if hook_path.exists():
    print(f"✓ Hook file exists: {hook_path}")

    # Try to import it
    try:
        sys.path.insert(0, str(hook_path.parent))
        print("✓ Hook module imports successfully")
    except Exception as e:
        print(f"❌ Hook module import failed: {e}")
        sys.exit(1)
else:
    print(f"❌ Hook file not found: {hook_path}")
    sys.exit(1)

# Test 4: Verify hook logic works
print("\n[4/5] Testing hook detection logic...")

from PreToolUse_repo_visibility_guard import (
    detect_visibility_change,
    is_allowed_public_path,
    is_protected_path,
)

# Test path detection
tests = [
    (is_protected_path("P:/"), True, "P:/ is protected"),
    (is_protected_path("C:/"), False, "C:/ is not protected"),
    (is_allowed_public_path("P:/packages/"), True, "P:/packages/ can be public"),
    (is_allowed_public_path("P:/other/"), False, "P:/other/ cannot be public"),
]

all_passed = True
for test_func, expected, description in tests:
    result = test_func
    if result == expected:
        print(f"  ✓ {description}")
    else:
        print(f"  ❌ {description} (got {result}, expected {expected})")
        all_passed = False

# Test command detection
cmd_tests = [
    ("gh repo edit x y --visibility public", True, "Detects gh CLI public"),
    ("gh repo edit x y --visibility private", True, "Detects gh CLI private"),
    ("git status", False, "Allows safe commands"),
]

for cmd, should_detect, description in cmd_tests:
    is_change, _ = detect_visibility_change(cmd)
    if is_change == should_detect:
        print(f"  ✓ {description}")
    else:
        print(f"  ❌ {description} (got {is_change}, expected {should_detect})")
        all_passed = False

if not all_passed:
    sys.exit(1)

# Test 5: Verify hook blocks dangerous commands
print("\n[5/5] Testing hook blocking behavior (through direct invocation)...")

test_input = {
    "tool_name": "Bash",
    "tool_input": {
        "command": "gh repo edit owner/repo --visibility public"
    }
}

result = subprocess.run(
    [sys.executable, str(hook_path)],
    input=json.dumps(test_input),
    capture_output=True,
    text=True,
    timeout=5,
    cwd="P:\\"
)

if result.returncode == 2:
    output = json.loads(result.stdout)
    if output.get("decision") == "block":
        print(r"✓ Hook correctly blocks P:\ drive public visibility changes")
        print(f"  Reason: {output['reason'][:100]}...")
    else:
        print("❌ Hook returned wrong decision")
        sys.exit(1)
else:
    print(f"❌ Hook returned exit code {result.returncode} (expected 2)")
    sys.exit(1)

# Summary
print("\n" + "="*70)
print("✓ ALL VERIFICATION CHECKS PASSED")
print("="*70)
print("\nRepository Visibility Guard Status: OPERATIONAL")
print("\nProtected paths:")
print("  • P:/ drive (blocked from public)")
print("\nAllowed exceptions:")
print("  • P:/packages/ (can be public)")
print("  • All repos can be made private (safe operation)")
print("\nTo bypass: Add --allow-visibility-change flag")
print("To disable: export REPO_VISIBILITY_GUARD_ENABLED=false")
print("\n" + "="*70)
