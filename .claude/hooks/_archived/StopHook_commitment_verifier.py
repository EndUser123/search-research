#!/usr/bin/env python3
from __future__ import annotations

"""
Commitment Verifier Hook (Stop)

PURPOSE: Validate git state claims when "Commitment checkpoint" is detected
         in LLM response.

PROBLEM ADDRESSED:
- "Commitment checkpoint answer: YES - I have not made any changes"
- LLM asserted without verification - ritualized, not verified
- Checkpoint should be validated against actual git state

ENFORCEMENT MECHANISM:
- Detects "Commitment checkpoint" in LLM response
- Parses claim (e.g., "not made any changes", "no breaking changes")
- Runs git status/diff to verify BEFORE response completes
- MEDIUM severity (warn) - injects verification requirement

CONSTITUTIONAL BASIS:
- CLAUDE.md: "Show, Don't Summarize" - Quote actual tool output
- CLAUDE.md: "Unsubstantiated claims" - Verify numeric/state claims
- truth-v8.md: "Verification > confidence"

FEEDBACK CORRECTION: Must be a StopHook (fires on LLM output), not
UserPromptSubmit (fires on user input). Commitment checkpoints appear in
LLM output, so must be validated before response completes.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# === CONFIGURATION ===
ENABLED = os.environ.get("COMMITMENT_VERIFIER_ENABLED", "true").lower() == "true"
DEBUG = os.environ.get("CSF_HOOK_DEBUG", "0") == "1"

# === TERMINAL ISOLATION ===
TERMINAL_DETECTION_PATH = Path(__file__).resolve().parent.parent / "terminal_detection.py"
if TERMINAL_DETECTION_PATH.exists():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    try:
        from skill_guard.utils.terminal_detection import detect_terminal_id
        TERMINAL_ID = detect_terminal_id()
    except ImportError:
        TERMINAL_ID = "fallback_1"
else:
    TERMINAL_ID = "fallback_1"


# === PATTERN DEFINITIONS ===

# Commitment checkpoint detection
COMMITMENT_PATTERNS = [
    r"\bCommitment\s+checkpoint",
    r"\bcheckpoint\s+answer:",
    r"\bcommitment\s+(?:question|query|check)",
]

# Claim types and their verification patterns
CLAIM_VERIFICATION = {
    "not made any changes": {
        "patterns": [
            r"\b(?:I\s+have\s+)?not\s+made\s+any\s+changes",
            r"\bno\s+changes?\s+(?:were|have\s+been)?\s+made",
            r"\bdidn't\s+(?:make|do)\s+anything",
        ],
        "verify_cmd": "status",
        "expected": "clean or only reads",
    },
    "no breaking changes": {
        "patterns": [
            r"\bno\s+breaking\s+changes?",
            r"\b(?:changes?|modifications?)\s+(?:are\s+)?(?:safe|non-breaking)",
        ],
        "verify_cmd": "diff",
        "expected": "show diff to verify",
    },
    "only read operations": {
        "patterns": [
            r"\bonly\s+(?:used|ran)\s+(?:Read|Grep|Glob)",
            r"\b(?:just|only)\s+read?\s+(?:files|code)",
        ],
        "verify_cmd": "status",
        "expected": "no Write/Edit operations",
    },
}


# === GIT VERIFICATION ===


def run_git_command(cmd: list[str]) -> tuple[bool, str]:
    """
    Run a git command and return (success, output).
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path.cwd(
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)


def verify_no_changes() -> tuple[bool, str]:
    """
    Verify claim "not made any changes" by checking git status.
    """
    success, output = run_git_command(["git", "status", "--porcelain"])

    if not success:
        return False, f"git status failed: {output}"

    # Check if working directory is clean
    if not output.strip():
        return True, "Working directory is clean"

    # Parse git status output
    lines = output.strip().split('\n')
    modified = [line for line in lines if line and line[0] in ' MADRC']

    if modified:
        return False, f"Found {len(modified)} modified file(s):\n" + "\n".join(modified[:5])

    return True, "No staged or unstaged changes"


def verify_no_breaking_changes() -> tuple[bool, str]:
    """
    Verify claim "no breaking changes" by checking git diff.
    """
    success, output = run_git_command(["git", "diff", "HEAD"])

    if not success:
        return False, f"git diff failed: {output}"

    if not output.strip():
        return True, "No changes to show"

    # Return diff for review - this is informational
    return True, f"Changes detected - review diff:\n{output[:500]}..." if len(output) > 500 else output


# === DETECTION ===


def detect_commitment_checkpoint(response: str) -> dict | None:
    """
    Detect if response contains a commitment checkpoint.

    Returns:
        dict with 'claim_type' and 'matched_text' if detected, None otherwise
    """
    if not response or len(response) < 10:
        return None

    response_lower = response.lower()

    # Check for commitment checkpoint marker
    for pattern in COMMITMENT_PATTERNS:
        if re.search(pattern, response_lower, re.IGNORECASE):
            # Found checkpoint - now identify the claim type
            for claim_type, claim_data in CLAIM_VERIFICATION.items():
                for claim_pattern in claim_data["patterns"]:
                    if re.search(claim_pattern, response_lower, re.IGNORECASE):
                        return {
                            "claim_type": claim_type,
                            "matched_text": claim_pattern,
                            "verify_cmd": claim_data["verify_cmd"],
                            "expected": claim_data["expected"],
                        }

    return None


# === MAIN HOOK LOGIC ===


def extract_response(input_data: dict) -> str:
    """Extract assistant response from various input formats."""
    response = ""

    # Try transcript_path first
    transcript_path = input_data.get("transcript_path", "")
    if transcript_path:
        try:
            transcript = Path(transcript_path)
            if transcript.exists():
                content = transcript.read_text(encoding="utf-8")
                for line in reversed(content.strip().split("\n")):
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        if entry.get("role") == "assistant":
                            msg_content = entry.get("content", [])
                            if isinstance(msg_content, list):
                                response = " ".join(
                                    b.get("text", "")
                                    for b in msg_content
                                    if b.get("type") == "text"
                                )
                            else:
                                response = str(msg_content)
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass

    # Fallback to conversation field
    if not response:
        conversation = input_data.get("conversation", "") or input_data.get("messages", "")
        if isinstance(conversation, list):
            for msg in reversed(conversation):
                if msg.get("role") == "assistant":
                    response = msg.get("content", "")
                    break
        else:
            response = str(conversation)

    # Final fallback
    if not response:
        response = input_data.get("response", "")

    return response


def process_hook(response: str) -> tuple[bool, str | None, str]:
    """
    Main hook entry point for Stop phase.

    Returns: (allow: bool, message: str | None, verdict: str)
    """
    if not ENABLED:
        return True, None, "OK"

    # Check for commitment checkpoint
    checkpoint_info = detect_commitment_checkpoint(response)

    if not checkpoint_info:
        return True, None, "OK"

    # Verify the claim
    claim_type = checkpoint_info["claim_type"]
    verify_cmd = checkpoint_info["verify_cmd"]

    if claim_type == "not made any changes":
        verified, details = verify_no_changes()
    elif claim_type == "no breaking changes":
        verified, details = verify_no_breaking_changes()
    else:
        # Unknown claim type - allow but warn
        return True, None, "OK"

    if not verified:
        # Claim was false - inject verification requirement
        warning_message = f"""
⚠️ COMMITMENT CLAIM VERIFICATION

You claimed: "{claim_type}"

Verification shows:
{details}

REQUIRED: Run '{verify_cmd}' to verify before claiming.

Your commitment checkpoint should be based on ACTUAL git state, not assumption.

---
Reference: .claude/hooks/CLAUDE.md section "Show, Don't Summarize"
"""
        # MEDIUM severity = warn, don't block
        return True, warning_message, "WARN_UNVERIFIED_COMMITMENT"

    return True, None, "OK"


# === MAIN ===

from __lib.hook_base import hook_main


@hook_main
def main():
    """
    Main hook entry point.

    Protocol (Stop):
    - Input: JSON via stdin with transcript_path, conversation, or messages
    - Output: JSON to stdout with "allow", "reason", "metadata" fields
    - Exit code: 0 = allow, 1 = block
    - Warning message goes to stderr
    """
    input_data = json.load(sys.stdin)

    # DEBUG: Log input structure
    if DEBUG:
        print(
            f"[commitment_verifier DEBUG] input_data keys: {list(input_data.keys())}",
            file=sys.stderr,
        )
        print(
            f"[commitment_verifier DEBUG] transcript_path: {input_data.get('transcript_path', 'MISSING')}",
            file=sys.stderr,
        )

    response = extract_response(input_data)

    if DEBUG:
        print(
            f"[commitment_verifier DEBUG] extracted response length: {len(response)}",
            file=sys.stderr,
        )

    if not response or len(response) < 10:
        print(json.dumps({"allow": True, "reason": "Response too short"}))
        return

    allow, message, verdict_code = process_hook(response)

    output = {
        "allow": allow,
        "reason": message or "OK",
        "metadata": {
            "hook": "stop_commitment_verifier",
            "verdict": verdict_code,
            "terminal_id": TERMINAL_ID,
        },
    }

    print(json.dumps(output))

    if message:
        print(message, file=sys.stderr)


if __name__ == "__main__":
    main()
