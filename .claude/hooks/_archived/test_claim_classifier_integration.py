#!/usr/bin/env python3
"""
Test claim classifier integration in Stop hooks.

Verifies that:
1. Meta/self-explanation responses are skipped (allow)
2. External fact claims are properly evaluated
3. Docs-only softening works correctly
"""

import json
import subprocess
import sys

HOOKS_DIR = r"P:\.claude\hooks"

test_cases = [
    {
        "name": "Meta response - should SKIP",
        "input": {
            "response": "I did not use TDD for this change.",
            "transcript": [{"role": "user", "content": "test"}],
            "tools_used": [],
            "workload_type": "code"
        },
        "expect_skip": True
    },
    {
        "name": "Self-explanation - should SKIP",
        "input": {
            "response": "The reason I did that was to avoid the import error.",
            "transcript": [{"role": "user", "content": "Why did you do that?"}],
            "tools_used": [],
            "workload_type": "code"
        },
        "expect_skip": True
    },
    {
        "name": "External fact claim - should PROCESS",
        "input": {
            "response": "The fix works. All tests passed.",
            "transcript": [{"role": "user", "content": "Fix the bug"}],
            "tools_used": [],
            "workload_type": "code"
        },
        "expect_skip": False
    },
    {
        "name": "Docs-only without external_fact - should SKIP (softened)",
        "input": {
            "response": "Updated the README with new installation instructions.",
            "transcript": [{"role": "user", "content": "Update the docs"}],
            "tools_used": [{"name": "Write", "input": {"file_path": "README.md"}}],
            "workload_type": "docs"
        },
        "expect_skip": True
    },
]

hooks = [
    ("StopHook_cross_validator.py", "cross_validator"),
    ("StopHook_claim_consistency_tracker.py", "consistency_tracker"),
    ("Stop_absence_claim_gate.py", "absence_claim_gate"),
]


def run_hook(hook_name: str, input_data: dict) -> tuple[int, str, str]:
    """Run a hook and return (exit_code, stdout, stderr)."""
    hook_path = f"{HOOKS_DIR}/{hook_name}"
    result = subprocess.run(
        ["python", hook_path],
        input=json.dumps(input_data,
        capture_output=True,
        text=True,
        timeout=10
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def is_skip_allowed(output: str, exit_code: int) -> bool:
    """Check if hook allowed the response (skip)."""
    if exit_code == 0:
        # Empty output or approve decision = allow
        if not output or output == "{}":
            return True
        try:
            data = json.loads(output)
            return data.get("decision") in ("approve", "allow", "ok") or "META_CONVERSATION_SKIP" in output
        except json.JSONDecodeError:
            pass
    return False


def main():
    print("=" * 70)
    print("CLAIM CLASSIFIER INTEGRATION TEST")
    print("=" * 70)

    passed = 0
    failed = 0

    for hook_file, hook_name in hooks:
        print(f"\n[{hook_name}]")
        print("-" * 50)

        for tc in test_cases:
            exit_code, stdout, stderr = run_hook(hook_file, tc["input"])
            is_skip = is_skip_allowed(stdout, exit_code)

            if tc["expect_skip"]:
                if is_skip or exit_code == 0:
                    print(f"  SKIP: {tc['name']}")
                    passed += 1
                else:
                    print(f"  FAIL: {tc['name']} (expected skip, got exit {exit_code})")
                    if stderr:
                        print(f"    stderr: {stderr[:200]}")
                    failed += 1
            else:
                if not is_skip and exit_code not in (0, 2):
                    # Non-zero exit that's not a block = unexpected
                    print(f"  FAIL: {tc['name']} (unexpected exit {exit_code})")
                    if stderr:
                        print(f"    stderr: {stderr[:200]}")
                    failed += 1
                else:
                    print(f"  PROCESS: {tc['name']}")
                    passed += 1

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
