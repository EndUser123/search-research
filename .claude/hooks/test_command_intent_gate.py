#!/usr/bin/env python3
"""Test script for command intent gate (consolidated in bash_router)."""

import sys

sys.path.insert(0, 'P:/.claude/hooks')

import json
import time
from pathlib import Path

# Import the router module
import PreToolUse_bash_router as router


def setup_test_state(skill: str, prompt: str) -> str:
    """Write test state file, return session ID."""
    STATE_DIR = Path('P:/.claude/hooks/state')
    session_id = router._get_session_id()
    state_file = STATE_DIR / f'pending_command_intent_{session_id}.json'

    state = {
        'skill': skill,
        'prompt': prompt,
        'session_id': session_id,
        'expires_at': time.time() + 300
    }
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f)

    return session_id


def test_unauthorized_flag():
    """Test: User says 'review the plan', CC adds --qwen-only → BLOCK."""
    print("\n" + "="*60)
    print("TEST 1: Unauthorized restrictive flag")
    print("="*60)

    session_id = setup_test_state('ask-cli4', 'review the plan')
    print("Setup: skill=ask-cli4, prompt='review the plan'")
    print(f"Session: {session_id}")

    test_data = {
        'tool_input': {
            'command': 'python ask_cli.py "review the plan" --qwen-only'
        }
    }

    result = router.run_command_intent_gate(test_data)

    if result and result.get('hookSpecificOutput', {}).get('permissionDecision') == 'deny':
        print("✅ PASS: Blocked unauthorized --qwen-only")
        reason = result['hookSpecificOutput']['permissionDecisionReason']
        print(f"   Reason snippet: {reason[:80]}...")
        return True
    else:
        print("❌ FAIL: Should have blocked")
        print(f"   Result: {result}")
        return False


def test_justified_flag():
    """Test: User says 'use qwen to review', CC adds --qwen-only → ALLOW."""
    print("\n" + "="*60)
    print("TEST 2: Justified restrictive flag")
    print("="*60)

    session_id = setup_test_state('ask-cli4', 'use qwen to review the code')
    print("Setup: skill=ask-cli4, prompt='use qwen to review the code'")
    print(f"Session: {session_id}")

    test_data = {
        'tool_input': {
            'command': 'python ask_cli.py "review" --qwen-only'
        }
    }

    result = router.run_command_intent_gate(test_data)

    if result is None:
        print("✅ PASS: Allowed justified --qwen-only")
        return True
    else:
        print("❌ FAIL: Should have allowed")
        print(f"   Result: {result}")
        return False


def test_no_restrictive_flags():
    """Test: No restrictive flags → ALLOW."""
    print("\n" + "="*60)
    print("TEST 3: No restrictive flags")
    print("="*60)

    session_id = setup_test_state('ask-cli4', 'review the plan')
    print("Setup: skill=ask-cli4, prompt='review the plan'")
    print(f"Session: {session_id}")

    test_data = {
        'tool_input': {
            'command': 'python ask_cli.py "review the plan"'
        }
    }

    result = router.run_command_intent_gate(test_data)

    if result is None:
        print("✅ PASS: Allowed (no restrictive flags)")
        return True
    else:
        print("❌ FAIL: Should have allowed")
        print(f"   Result: {result}")
        return False


def test_no_pending_intent():
    """Test: No state file → ALLOW (fail-open)."""
    print("\n" + "="*60)
    print("TEST 4: No pending intent (fail-open)")
    print("="*60)

    # Clear any existing state
    STATE_DIR = Path('P:/.claude/hooks/state')
    session_id = router._get_session_id()
    state_file = STATE_DIR / f'pending_command_intent_{session_id}.json'
    if state_file.exists():
        state_file.unlink()

    print(f"Setup: No state file for session {session_id}")

    test_data = {
        'tool_input': {
            'command': 'python ask_cli.py "anything" --qwen-only'
        }
    }

    result = router.run_command_intent_gate(test_data)

    if result is None:
        print("✅ PASS: Allowed (no pending intent)")
        return True
    else:
        print("❌ FAIL: Should have allowed (fail-open)")
        print(f"   Result: {result}")
        return False


def test_non_skill_command():
    """Test: Different command (not skill execution) → ALLOW."""
    print("\n" + "="*60)
    print("TEST 5: Non-skill command")
    print("="*60)

    session_id = setup_test_state('ask-cli4', 'review the plan')
    print("Setup: skill=ask-cli4, prompt='review the plan'")
    print(f"Session: {session_id}")

    test_data = {
        'tool_input': {
            'command': 'ls -la'  # Not ask_cli.py
        }
    }

    result = router.run_command_intent_gate(test_data)

    if result is None:
        print("✅ PASS: Allowed (not skill execution)")
        return True
    else:
        print("❌ FAIL: Should have allowed")
        print(f"   Result: {result}")
        return False


if __name__ == '__main__':
    print("Command Intent Gate Tests")
    print("=" * 60)

    results = []
    results.append(('Unauthorized flag', test_unauthorized_flag()))
    results.append(('Justified flag', test_justified_flag()))
    results.append(('No restrictive flags', test_no_restrictive_flags()))
    results.append(('No pending intent', test_no_pending_intent()))
    results.append(('Non-skill command', test_non_skill_command()))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")

    print(f"\n  {passed}/{total} tests passed")

    sys.exit(0 if passed == total else 1)
