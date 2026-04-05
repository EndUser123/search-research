#!/usr/bin/env python3
"""
Test: Assumption Audit Principle
=================================

Verifies that test_assumption_audit.py catches unverified claims
WITHOUT needing specific patterns for each claim type.

PRINCIPLE: Any response without observation tools triggers self-audit.
"""

import json
import subprocess
import sys
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")

def test_assumption_audit(transcript_path: str, should_block: bool, description: str):
    """Test if assumption audit blocks as expected."""

    input_data = {
        "transcript_path": transcript_path,
        "conversation": [],
        "stop_hook_active": False
    }

    result = subprocess.run(
        [sys.executable, str(HOOKS_DIR / "test_assumption_audit.py")],
        input=json.dumps(input_data).encode(),
        capture_output=True,
        timeout=5
    )

    # Exit code 2 = block (per block_protocol)
    blocked = result.returncode == 2

    status = "✓" if blocked == should_block else "✗"
    print(f"{status} {description}")

    if blocked != should_block:
        print(f"  Expected: {'BLOCK' if should_block else 'ALLOW'}")
        print(f"  Got: {'BLOCK' if blocked else 'ALLOW'}")
        if result.stderr:
            print(f"  Reason: {result.stderr.decode()[:200]}")
        return False

    return True


def create_test_transcript(tools_used: list[str], response: str) -> str:
    """Create a test transcript file."""

    transcript = []

    # User turn
    transcript.append(json.dumps({
        "type": "user",
        "message": {"content": "test query"}
    }))

    # Assistant turn with tools
    content = []
    for tool in tools_used:
        content.append({
            "type": "tool_use",
            "name": tool,
            "input": {"command": "test"}
        })

    content.append({
        "type": "text",
        "text": response
    })

    transcript.append(json.dumps({
        "type": "assistant",
        "message": {"content": content}
    }))

    # Write to temp file
    temp_file = HOOKS_DIR / "temp_test_transcript.jsonl"
    temp_file.write_text("\n".join(transcript))

    return str(temp_file)


def main():
    """Run tests."""

    print("Testing Assumption Audit Principle")
    print("=" * 50)

    all_passed = True

    # Test 1: Enumeration claim without tools → BLOCK
    transcript = create_test_transcript(
        tools_used=[],
        response="Found them! 13 tasks already have [yt-fts] in their title."
    )

    all_passed &= test_assumption_audit(
        transcript,
        should_block=True,
        description="Enumeration claim without tools"
    )

    # Test 2: Enumeration claim WITH tools → ALLOW
    transcript = create_test_transcript(
        tools_used=["Grep", "Read"]
    )

    all_passed &= test_assumption_audit(
        transcript,
        should_block=False,
        description="Enumeration claim WITH verification"
    )

    # Test 3: Code behavior claim without Read → BLOCK
    transcript = create_test_transcript(
        tools_used=[],
        response="The daemon handles this by polling every 5 seconds."
    )

    all_passed &= test_assumption_audit(
        transcript,
        should_block=True,
        description="Code behavior claim without Read"
    )

    # Test 4: Code behavior WITH Read → ALLOW
    transcript = create_test_transcript(
        tools_used=["Read"],
        response="The daemon polls every 5 seconds (line 42: time.sleep(5))."
    )

    all_passed &= test_assumption_audit(
        transcript,
        should_block=False,
        description="Code behavior WITH Read"
    )

    # Test 5: NEW claim type (not in patterns) → Still caught!
    transcript = create_test_transcript(
        tools_used=[],
        response="The system automatically rotates logs every 7 days and keeps 30 backups."
    )

    all_passed &= test_assumption_audit(
        transcript,
        should_block=True,
        description="New claim type (log rotation) - no specific pattern needed"
    )

    # Test 6: Simple question/answer → ALLOW (not making claims)
    transcript = create_test_transcript(
        tools_used=[],
        response="A git worktree allows you to check out multiple branches simultaneously."
    )

    all_passed &= test_assumption_audit(
        transcript,
        should_block=False,
        description="General explanation (not system-specific claim)"
    )

    # Cleanup
    try:
        Path(HOOKS_DIR / "temp_test_transcript.jsonl").unlink()
    except Exception:
        pass

    print("=" * 50)
    if all_passed:
        print("✓ All tests passed - Principle works!")
        print("\nKey insight: Self-evaluation catches ANY unverified claim,")
        print("not just patterns we've thought of.")
        sys.exit(0)
    else:
        print("✗ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
