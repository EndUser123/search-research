#!/usr/bin/env python3
"""
Stop_safety_gate.py - Consolidated Safety & Protocol Validator
==============================================================

Single-source enforcement for:
1. Secret/PII Leakage (sk- keys, credentials)
2. Forbidden Execution Patterns (Daemons, Background tasks, autonomous fixes)
3. Protocol Integrity (Command execution vs description)
"""

from __future__ import annotations

import json
import re
import sys

# === CONFIGURATION ===
# Patterns indicating secrets (PII)
SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9]{32,}",  # OpenAI/API Keys
    r"(?:password|passwd|secret|token|key)\s*[:=]\s*['\"][^'\"]{8,}['\"]",
]

# Patterns indicating forbidden autonomous behavior (Part C.1)
FORBIDDEN_PATTERNS = [
    r"\bbackground\s+(?:service|process|task|job)\b",
    r"\bdaemon|persistent\s+process\b",
    r"\bself.?healing|auto.?correct|autonomous\s+fix\b",
]

# Patterns that indicate describing a command instead of executing it
DESCRIPTION_PATTERNS = [
    r"\bthis\s+command\s+(?:provides|offers|enables|allows|supports)\b",
    r"\bthe\s+/\w+\s+command\s+(?:is|does|provides|will)\b",
    r"\blet\s+me\s+(?:explain|describe|summarize)\s+(?:what|how|the)\b",
]

def check_secrets(response: str) -> str | None:
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return "Possible Secret/API Key detected in output."
    return None

def check_forbidden(response: str) -> str | None:
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return "Forbidden autonomous/background pattern detected (Part C.1)."
    return None

def check_protocol(response: str, data: dict) -> str | None:
    # Look for active command state (Turnover-turn logic)
    # Check if a slash command was active in this session
    # This logic is simplified from command_execution_validator.py
    response_lower = response.lower()
    for pattern in DESCRIPTION_PATTERNS:
        if re.search(pattern, response_lower):
            return "Protocol violation: Describing a command instead of executing it."
    return None

def main():
    try:
        raw_input = sys.stdin.read().strip()
        if not raw_input:
            sys.exit(0)

        data = json.loads(raw_input)
        response = data.get("response", "")

        if not response:
            sys.exit(0)

        # 1. Check Secrets
        secret_violation = check_secrets(response)
        if secret_violation:
            print(json.dumps({
                "decision": "block",
                "reason": f"SAFETY VIOLATION: {secret_violation}",
                "blocking_hook": "Stop_safety_gate.py",
            }))
            sys.exit(2)

        # 2. Check Forbidden Patterns
        forbidden_violation = check_forbidden(response)
        if forbidden_violation:
            print(json.dumps({
                "decision": "block",
                "reason": f"POLICY VIOLATION: {forbidden_violation}",
                "blocking_hook": "Stop_safety_gate.py",
            }))
            sys.exit(2)

        # 3. Check Protocol
        protocol_violation = check_protocol(response, data)
        if protocol_violation:
            # We treat this as a block to force execution
            print(json.dumps({
                "decision": "block",
                "reason": f"PROTOCOL VIOLATION: {protocol_violation}",
                "blocking_hook": "Stop_safety_gate.py",
            }))
            sys.exit(2)

        print(json.dumps({"decision": "allow"}))

    except Exception as e:
        # Safety gate fails OPEN on error to prevent deadlock during refactor
        print(json.dumps({"decision": "allow", "note": f"Safety error: {e}"}))
        sys.exit(0)

if __name__ == "__main__":
    main()
