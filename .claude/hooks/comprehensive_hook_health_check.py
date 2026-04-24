#!/usr/bin/env python3
"""Comprehensive hook health check - test all hooks for errors."""

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent

def test_hook(hook_name: str, test_payload: dict) -> dict:
    """Test a single hook and return results."""
    hook_path = HOOKS_DIR / hook_name

    if not hook_path.exists():
        return {
            "status": "skip",
            "reason": "File not found"
        }

    try:
        result = subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(test_payload).encode(),
            capture_output=True,
            timeout=10
        )

        stderr_text = result.stderr.decode('utf-8', errors='replace')
        stdout_text = result.stdout.decode('utf-8', errors='replace')

        # Check for actual errors (not just advisory output)
        has_error = False
        error_type = None

        if result.returncode != 0:
            has_error = True
            error_type = f"Exit code {result.returncode}"

        if "ImportError" in stderr_text or "ModuleNotFoundError" in stderr_text:
            has_error = True
            error_type = "Import error"

        if "Traceback" in stderr_text and "Error" in stderr_text:
            has_error = True
            error_type = "Exception"

        return {
            "status": "error" if has_error else "success",
            "exit_code": result.returncode,
            "stderr_length": len(stderr_text),
            "stderr_preview": stderr_text[:200] if stderr_text else "",
            "stdout_length": len(stdout_text),
            "error_type": error_type,
            "stderr_full": stderr_text if has_error else ""
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "reason": "Timeout after 10s"
        }
    except Exception as e:
        return {
            "status": "error",
            "reason": str(e)
        }

def test_stale_lock_files() -> dict:
    """Check for stale session ledger lock files that indicate cleanup bugs."""
    try:
        # LEDGER_DIR is at .claude/.session/ relative to project root
        # HOOKS_DIR is P:/.claude/hooks/, so we go up one level to get to P:/.claude/
        ledger_dir = HOOKS_DIR.parent / ".session"

        if not ledger_dir.exists():
            return {"status": "skip", "reason": "Ledger directory not found"}

        # Find all .lock files in the ledger directory
        lock_files = list(ledger_dir.glob("*.lock"))

        if lock_files:
            # Get file ages
            import time
            now = time.time()
            stale_locks = []

            for lock_file in lock_files:
                age_hours = (now - lock_file.stat().st_mtime) / 3600
                # Consider locks older than 1 hour as stale
                if age_hours > 1:
                    stale_locks.append({
                        "path": str(lock_file.relative_to(HOOKS_DIR.parent.parent)),
                        "age_hours": round(age_hours, 1)
                    })

            if stale_locks:
                return {
                    "status": "error",
                    "reason": f"Found {len(stale_locks)} stale lock file(s) indicating cleanup bug in file_lock()",
                    "stale_locks": stale_locks[:5]  # Show first 5
                }

        return {"status": "success", "checked": True}

    except Exception as e:
        return {"status": "error", "reason": f"Failed to check lock files: {e}"}


def test_think_trigger_profile_consistency() -> dict:
    """Test that all think_trigger profiles have both patterns and templates."""
    try:
        from UserPromptSubmit_modules.think_trigger import (
            _COMPILED_STRONG,
            _PROFILES,
            _THINK_PROFILES,
        )

        # Check that _THINK_PROFILES has all 7 profiles
        expected_profiles = {
            "debug_rca",
            "tradeoff_decision",
            "architecture",
            "pre_commit_risk",
            "security_review",
            "performance_analysis",
            "multi_file_refactor",
        }
        actual_profiles = set(_THINK_PROFILES.keys())

        if actual_profiles != expected_profiles:
            return {
                "status": "error",
                "reason": f"Profile count mismatch: expected {len(expected_profiles)}, got {len(actual_profiles)}. "
                         f"Missing: {expected_profiles - actual_profiles}, Extra: {actual_profiles - expected_profiles}"
            }

        # Verify derived dictionaries match single source
        if set(_PROFILES.keys()) != actual_profiles:
            return {
                "status": "error",
                "reason": "_PROFILES keys don't match _THINK_PROFILES"
            }

        if set(_COMPILED_STRONG.keys()) != actual_profiles:
            return {
                "status": "error",
                "reason": "_COMPILED_STRONG keys don't match _THINK_PROFILES"
            }

        # Verify each profile has required fields
        for profile_name, profile in _THINK_PROFILES.items():
            if not profile.name:
                return {"status": "error", "reason": f"Profile {profile_name} has no name"}
            if not profile.template:
                return {"status": "error", "reason": f"Profile {profile_name} has no template"}
            if not profile.strong_patterns:
                return {"status": "error", "reason": f"Profile {profile_name} has no strong_patterns"}

        return {"status": "success", "profiles_tested": len(actual_profiles)}

    except Exception as e:
        return {"status": "error", "reason": str(e)}


def main():
    print("=" * 70)
    print("COMPREHENSIVE HOOK HEALTH CHECK")
    print("=" * 70)
    print()

    # Define test payloads for different hook types
    test_cases = {
        "UserPromptSubmit.py": {
            "prompt": "/code implement the plan",
            "command_name": "code",
            "command_arguments": "implement the plan"
        },
        "PreToolUse.py": {
            "tool_name": "Bash",
            "tool_input": {"command": "echo test"}
        },
        "PostToolUse.py": {
            "tool_name": "Bash",
            "tool_input": {"command": "echo test"},
            "tool_output": "test"
        },
        "Stop.py": {
            "response": "I will help with that",
            "tool_calls": "[]"
        }
    }

    results = {}

    # Test each hook
    for hook_name, test_payload in test_cases.items():
        print(f"Testing {hook_name}...", end=" ", flush=True)

        result = test_hook(hook_name, test_payload)
        results[hook_name] = result

        if result["status"] == "success":
            print(f"✓ PASS (exit {result['exit_code']})")
        elif result["status"] == "skip":
            print(f"⊘ SKIP ({result['reason']})")
        else:
            print(f"✗ FAIL ({result.get('error_type', result.get('reason', 'Unknown'))})")

    # Test think_trigger profile consistency
    print("Testing think_trigger profile consistency...", end=" ", flush=True)
    profile_result = test_think_trigger_profile_consistency()
    results["think_trigger_profiles"] = profile_result

    if profile_result["status"] == "success":
        print(f"✓ PASS ({profile_result['profiles_tested']} profiles tested)")
    else:
        print(f"✗ FAIL ({profile_result.get('reason', 'Unknown')})")

    # Test for stale lock files (cleanup bug detection)
    print("Testing for stale lock files...", end=" ", flush=True)
    lock_result = test_stale_lock_files()
    results["stale_lock_files"] = lock_result

    if lock_result["status"] == "success":
        print("✓ PASS (no stale locks)")
    else:
        print(f"✗ FAIL ({lock_result.get('reason', 'Unknown')})")
        if lock_result.get("stale_locks"):
            print(f"   Stale locks found: {len(lock_result['stale_locks'])}")
            for lock_info in lock_result['stale_locks'][:3]:
                print(f"     - {lock_info['path']} ({lock_info['age_hours']}h old)")

    print()
    print("=" * 70)
    print("DETAILED RESULTS")
    print("=" * 70)
    print()

    # Show detailed results for failures
    has_failures = False
    for hook_name, result in results.items():
        if result["status"] == "error":
            has_failures = True
            print(f"❌ {hook_name}")
            print(f"   Error: {result.get('error_type', result.get('reason', 'Unknown'))}")
            if result.get("stderr_full"):
                print(f"   Stderr: {result['stderr_full'][:500]}")
            print()

    if not has_failures:
        print("✅ ALL HOOKS PASSED - No errors detected")
    else:
        print("⚠️  FAILURES DETECTED - See details above")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total hooks tested: {len(results)}")
    print(f"Passed: {sum(1 for r in results.values() if r['status'] == 'success')}")
    print(f"Failed: {sum(1 for r in results.values() if r['status'] == 'error')}")
    print(f"Skipped: {sum(1 for r in results.values() if r['status'] == 'skip')}")
    print()

    return 0 if not has_failures else 1

if __name__ == "__main__":
    sys.exit(main())
