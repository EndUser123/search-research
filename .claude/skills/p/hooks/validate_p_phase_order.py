#!/usr/bin/env python3
"""
PreToolUse hook for /p skill - Phase order enforcement

Prevents skipping phases by validating that:
1. P2 cannot run if P1 marker doesn't exist
2. P3 cannot run if P2 marker doesn't exist
3. P4 cannot run if P3 marker doesn't exist
4. P5 cannot run if P4 marker doesn't exist

Usage: This hook is automatically called when /p skill is invoked
Input: JSON via stdin with tool details
Output: JSON via stdout with allow/deny decision
"""

import json
import sys
from pathlib import Path

# State directory for phase markers
STATE_DIR = Path(".claude/state")

# Phase marker files (using directories for atomic operations)
PHASE1_MARKER = STATE_DIR / "p1-complete.marker"
PHASE2_MARKER = STATE_DIR / "p2-complete.marker"
PHASE3_MARKER = STATE_DIR / "p3-complete.marker"
PHASE4_MARKER = STATE_DIR / "p4-complete.marker"
PHASE5_MARKER = STATE_DIR / "p5-complete.marker"

# JSON validation limits (SEC-002: JSON deserialization safeguards)
MAX_JSON_SIZE_BYTES = 10 * 1024 * 1024  # 10MB limit
MAX_JSON_DEPTH = 100  # Maximum nesting depth


def safe_json_loads(json_string: str, max_size: int = MAX_JSON_SIZE_BYTES, max_depth: int = MAX_JSON_DEPTH) -> dict:
    """
    Safely parse JSON with size and depth limits (SEC-002 fix).

    Prevents denial-of-service attacks via:
    - Oversized JSON payloads (10MB limit)
    - Excessive nesting depth (100 levels limit)

    Args:
        json_string: Raw JSON string to parse
        max_size: Maximum allowed size in bytes (default: 10MB)
        max_depth: Maximum nesting depth allowed (default: 100)

    Returns:
        Parsed JSON object as dict

    Raises:
        ValueError: If JSON exceeds size limit, depth limit, or is malformed
    """
    # Check size limit first
    if len(json_string.encode('utf-8')) > max_size:
        raise ValueError(f"JSON input exceeds maximum size of {max_size} bytes")

    def check_depth(obj, current_depth=0):
        """Recursively check JSON nesting depth."""
        if current_depth > max_depth:
            raise ValueError(f"JSON nesting depth exceeds maximum of {max_depth}")

        if isinstance(obj, dict):
            for value in obj.values():
                check_depth(value, current_depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                check_depth(item, current_depth + 1)

    try:
        # Parse JSON
        parsed = json.loads(json_string)
        # Check depth
        check_depth(parsed)
        return parsed
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")


def marker_exists(marker_path: Path, expected_phase: int) -> bool:
    """
    Check if phase marker exists and has valid content (multi-terminal safe).

    Validates that marker file exists and contains the expected phase prefix.
    This prevents corrupted or empty marker files from being accepted.

    Args:
        marker_path: Path to the marker file
        expected_phase: The phase number to validate (1-5)

    Returns:
        True if marker exists and has valid content, False otherwise
    """
    try:
        # Combine exists check and read in single operation
        # This avoids TOCTOU race condition
        content = marker_path.read_text().strip()

        # Check if content is non-empty and has expected prefix
        if not content:
            return False

        expected_prefix = f"Phase {expected_phase} completed"
        return content.startswith(expected_prefix)

    except (OSError, FileNotFoundError):
        # File doesn't exist or error reading - treat as non-existent
        return False


def deny(reason: str):
    """Deny the request with a reason."""
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason
        }
    }
    print(json.dumps(result))
    sys.exit(0)


def allow():
    """Allow the request."""
    result = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }
    }
    print(json.dumps(result))
    sys.exit(0)


def main():
    try:
        # Read JSON input from stdin (SEC-002: Use safe JSON parsing)
        try:
            json_input = sys.stdin.read()
            input_data = safe_json_loads(json_input)
        except (ValueError, json.JSONDecodeError) as e:
            # Malformed JSON input - deny the request
            deny(f"❌ Invalid JSON input: {e}")

        # Extract phase from input (e.g., --phase=2)
        args = input_data.get("tool_input", {}).get("args", [])
        phase = "auto"

        for arg in args:
            if arg.startswith("--phase="):
                phase = arg.split("=")[1]
                break

        # Extract tool name
        tool = input_data.get("tool_name", "")

        # Only validate Skill() calls for /p skill
        if tool != "Skill":
            # Not a Skill call - allow it
            allow()

        # Extract skill name
        skill = input_data.get("tool_input", {}).get("name", "")

        if skill != "p":
            # Not /p skill - allow it
            allow()

        # Validate phase order based on explicit --phase flag or detected phase
        # Check prerequisites first, then allow if all pass

        if phase in ("2", "review"):
            # P2 (Review) - requires P1 marker
            if not marker_exists(PHASE1_MARKER, expected_phase=1):
                deny("❌ Cannot run P2 (Review) before P1 (Build) completes. Run /p without --phase flag to auto-detect phase.")

        elif phase in ("3", "validate"):
            # P3 (Validate) - requires P2 marker
            if not marker_exists(PHASE2_MARKER, expected_phase=2):
                deny("❌ Cannot run P3 (Validate) before P2 (Review) completes. Run /p without --phase flag to auto-detect phase.")

        elif phase in ("4", "publish"):
            # P4 (Publish) - requires P3 marker
            if not marker_exists(PHASE3_MARKER, expected_phase=3):
                deny("❌ Cannot run P4 (Publish) before P3 (Validate) completes. Run /p without --phase flag to auto-detect phase.")

        elif phase in ("5", "certify"):
            # P5 (Certify) - requires P4 marker
            if not marker_exists(PHASE4_MARKER, expected_phase=4):
                deny("❌ Cannot run P5 (Certify) before P4 (Publish) completes. Run /p without --phase flag to auto-detect phase.")

        # All other phases (0, 1, auto, unknown) are allowed
        allow()

    except Exception:
        # Catch ALL exceptions to prevent stderr leakage
        # Any unexpected error results in a sanitized deny response
        deny("❌ Hook error: Unable to process request.")


if __name__ == "__main__":
    main()
