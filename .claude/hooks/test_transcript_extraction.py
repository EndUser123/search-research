#!/usr/bin/env python3
"""Test Stop_router response extraction from transcript."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent


def test_extract_from_transcript():
    """Test extracting response from transcript when field is missing."""
    print("\n=== Test: Extract response from transcript ===")

    # Create fake transcript
    transcript = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "You're absolutely right! This is sycophantic."}
    ]

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(transcript, f)
        transcript_path = f.name

    try:
        # Input without response field but with transcript_path
        input_data = {
            "session_id": "test",
            "transcript_path": transcript_path,
            "cwd": "/fake",
            "permission_mode": "allow",
            "hook_event_name": "Stop"
        }

        result = subprocess.run(
            [sys.executable, str(HOOKS_DIR / "Stop_router.py")],
            input=json.dumps(input_data),
            capture_output=True,
            text=True,
            cwd=str(HOOKS_DIR)
        )

        print(f"Exit code: {result.returncode}")
        print("\nStderr output:")
        print(result.stderr)

        # Check for extraction message
        if "Extracted response from transcript" in result.stderr:
            print("\n✅ Response extracted from transcript!")
            if "48 chars" in result.stderr or "50 chars" in result.stderr:
                print("✅ Correct response length detected")
        else:
            print("\n❌ Failed to extract response")

        # Check if pattern hook would have seen it
        if "Pattern-detection hooks active" in result.stderr:
            if "response_length: 0" not in result.stderr:
                print("✅ Pattern hooks received response text!")
            else:
                print("❌ Pattern hooks still got empty response")

    finally:
        Path(transcript_path).unlink()

    return result


if __name__ == "__main__":
    print("Testing Stop_router transcript extraction fix...")
    print("=" * 80)

    test_extract_from_transcript()

    print("\n" + "=" * 80)
    print("Test complete.")
