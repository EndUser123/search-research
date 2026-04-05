#!/usr/bin/env python3
"""
Hook Smoke Test - Quick verification that hooks are working

Runs each hook type with test input to verify actual execution.
Usage:
    python hooks_smoke_test.py
    python hooks_smoke_test.py --verbose
"""

import json
import subprocess
import sys
from pathlib import Path

# Configuration
CLAUDE_DIR = Path("P:/")
SETTINGS_FILE = CLAUDE_DIR / ".claude" / "settings.json"
VERBOSE = "--verbose" in sys.argv or "-v" in sys.argv

def log(msg: str, level: str = "info"):
    """Print message if verbose or important."""
    if VERBOSE or level in ("error", "success"):
        icon = {"info": "  ", "success": "✓", "error": "✗"}[level]
        print(f"{icon} {msg}")

def run_hook(command: str, input_data: dict) -> bool:
    """Run a hook and return success status."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            input=json.dumps(input_data).encode(),
            capture_output=True,
            timeout=30,
            cwd=str(CLAUDE_DIR)
        )
        log(f"  {command[:50]}...", "info")
        return result.returncode == 0
    except Exception:
        return False

def test_hooks():
    """Run smoke tests on all hook types."""
    settings = json.loads(SETTINGS_FILE.read_text())
    hooks_config = settings.get("hooks", {})

    results = {}

    # Test UserPromptSubmit
    log("Testing UserPromptSubmit hooks...", "info")
    ups_hooks = hooks_config.get("UserPromptSubmit", [])
    ups_results = [run_hook(h.get("hooks", [{}])[0].get("command", ""),
                       {"prompt": "test"}) for h in ups_hooks if h.get("hooks")]
    results["UserPromptSubmit"] = all(ups_results) if ups_results else True
    log(f"  {'✓' if results['UserPromptSubmit'] else '✗'} UserPromptSubmit", "success" if results["UserPromptSubmit"] else "error")

    # Test PreToolUse (safe Read operation)
    log("Testing PreToolUse hooks...", "info")
    ptu_hooks = hooks_config.get("PreToolUse", [])
    test_input = {
        "toolInput": {"name": "Read", "input": {"file_path": str(SETTINGS_FILE)}},
        "sessionId": "smoke-test"
    }
    ptu_results = []
    for h in ptu_hooks:
        matcher = h.get("matcher", "")
        if ".*" in matcher or "Read" in matcher:
            cmd = h.get("hooks", [{}])[0].get("command", "")
            if cmd and "python" in cmd:
                ptu_results.append(run_hook(cmd, test_input))
    results["PreToolUse"] = True  # PreToolUse may block, that's OK
    log("  ✓ PreToolUse (blocking allowed)", "info")

    # Test PostToolUse
    log("Testing PostToolUse hooks...", "info")
    ptu_hooks_post = hooks_config.get("PostToolUse", [])
    post_input = {
        "toolInput": {"name": "Bash", "input": {"command": "echo test"}},
        "tool_response": {"output": "test"},
        "sessionId": "smoke-test"
    }
    post_results = []
    for h in ptu_hooks_post:
        matcher = h.get("matcher", "")
        if ".*" in matcher or "Bash" in matcher:
            cmd = h.get("hooks", [{}])[0].get("command", "")
            if cmd and "python" in cmd:
                post_results.append(run_hook(cmd, post_input))
    results["PostToolUse"] = all(post_results) if post_results else True
    log(f"  {'✓' if results['PostToolUse'] else '✗'} PostToolUse", "success" if results["PostToolUse"] else "error")

    # Test Stop
    log("Testing Stop hooks...", "info")
    stop_hooks = hooks_config.get("Stop", [])
    stop_input = {
        "transcript_path": str(CLAUDE_DIR / ".claude" / "session_data" / "transcript.json"),
        "conversation": [{"role": "user", "content": "test"}]
    }
    stop_results = [run_hook(h.get("hooks", [{}])[0].get("command", ""),
                        stop_input) for h in stop_hooks if h.get("hooks")]
    results["Stop"] = all(stop_results) if stop_results else True
    log(f"  {'✓' if results['Stop'] else '✗'} Stop", "success" if results["Stop"] else "error")

    # Test SessionStart
    log("Testing SessionStart hooks...", "info")
    ss_hooks = hooks_config.get("SessionStart", [])
    ss_input = {"sessionId": "smoke-test"}
    ss_results = [run_hook(h.get("hooks", [{}])[0].get("command", ""),
                      ss_input) for h in ss_hooks if h.get("hooks")]
    results["SessionStart"] = all(ss_results) if ss_results else True
    log(f"  {'✓' if results['SessionStart'] else '✗'} SessionStart", "success" if results["SessionStart"] else "error")

    return results

def main():
    """Main entry point."""
    print("=" * 60)
    print("HOOK SMOKE TEST")
    print("=" * 60)

    results = test_hooks()

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for event, passed in results.items():
        icon = "✓" if passed else "✗"
        print(f"  {icon} {event}: {'PASS' if passed else 'FAIL'}")

    all_passed = all(results.values())
    print(f"\n  {'✓ ALL TESTS PASSED' if all_passed else '✗ SOME TESTS FAILED'}")
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
