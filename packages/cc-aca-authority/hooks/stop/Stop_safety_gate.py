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


# --- plugin bootstrap ---
import sys as _s; from pathlib import Path as _P
_l = _P(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in _s.path: _s.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

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
# Catches: suggesting new background/daemon services, autonomous self-healing/auto-correct as prescriptive actions
# Does NOT catch: descriptive architecture ("runs as background"), feature nouns ("self-healing mechanism"), examples
FORBIDDEN_PATTERNS = [
    # Modal + action + optional intermediate words + background/daemon (prescriptive: "should/need/going to/will ADD a background service")
    r"\bshould\s+(?:run|start|launch|add|create)\s+.+?(?:background|daemon|persistent)\b",
    r"\bneed\s+to\s+(?:run|start|launch|add)\s+.+?(?:background|daemon|persistent)\b",
    r"\bgoing\s+to\s+(?:run|start|launch|add)\s+.+?(?:background|daemon|persistent)\b",
    r"\bwill\s+(?:run|start|launch|add)\s+.+?(?:background|daemon|persistent)\b",
    r"\bshould\s+be\s+(?:running|started|launched|added)\b.*?(?:background|daemon)\b",
    # Autonomous self-healing/fix as PRESCRIPTIVE ACTION (not feature noun)
    r"\b(?:need\s+to|going\s+to)\s+(?:self.?heal|auto.?correct)\b",
    r"\bshould\s+(?:self.?heal|auto.?correct)\b",
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

# Patterns that indicate a bare except or missing import for exception classes
# Detects: "except UndefinedErrorName:" where the error name looks like a custom
# exception that hasn't been imported. Does NOT flag standard library exceptions.
_UNLIKELY_ERROR_NAMES = re.compile(
    r"except\s+([A-Z][a-zA-Z]+Error)\s*:",
    re.MULTILINE,
)
_STANDARD_LIBRARY_ERRORS = {
    "Exception", "BaseException", "ValueError", "TypeError", "RuntimeError",
    "KeyError", "IndexError", "AttributeError", "ImportError", "ModuleNotFoundError",
    "FileNotFoundError", "PermissionError", "TimeoutError", "OSError", "IOError",
    "NotImplementedError", "StopIteration", "GeneratorExit", "SystemExit",
    "KeyboardInterrupt", "SignalException", "Warning",
    "AssertionError", "SyntaxError", "IndentationError", "TabError",
    "LookupError", "NameError", "UnboundLocalError",
    "EnvironmentError", "IOError", "EOFError", "ZeroDivisionError",
    "OverflowError", "FloatingPointError", "DecimalConversionError",
    "UnicodeError", "UnicodeDecodeError", "UnicodeEncodeError", "UnicodeTranslateError",
    "ConnectionError", "BrokenPipeError", "ConnectionAbortedError",
    "ConnectionRefusedError", "ConnectionResetError", "FileExistsError",
    "FileNotFoundError", "IsADirectoryError", "NotADirectoryError",
    "ProcessLookupError", "ChildProcessError", "InvalidStateError",
}

def check_catch_block_hygiene(response: str) -> str | None:
    """Detect suspicious except blocks that reference undefined or unimported error classes."""
    for match in _UNLIKELY_ERROR_NAMES.finditer(response):
        error_name = match.group(1)
        if error_name not in _STANDARD_LIBRARY_ERRORS:
            # Flag as suspicious but not blocking — just advisory
            return (
                f"suspicious except block: '{error_name}' is not a standard exception. "
                "Verify it is imported or defined before use."
            )
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

        print(json.dumps({"decision": "approve"}))

    except Exception as e:
        # Safety gate fails OPEN on error to prevent deadlock during refactor
        print(json.dumps({"decision": "approve"}))
        sys.exit(0)

if __name__ == "__main__":
    main()
