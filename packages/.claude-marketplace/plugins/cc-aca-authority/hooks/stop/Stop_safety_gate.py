#!/usr/bin/env python3
"""
Stop_safety_gate.py - Consolidated Safety & Protocol Validator
==============================================================

Single-source enforcement for:
1. Secret/PII Leakage (sk- keys, credentials)
2. Forbidden Execution Patterns (Daemons, Background tasks, autonomous fixes)

Reads the assistant text from data["response"], falling back to
data["last_assistant_message"] — the field the live CC Stop payload actually
carries. Without that fallback this gate read "" and never scanned.
"""

from __future__ import annotations


# --- plugin bootstrap ---
import sys
from pathlib import Path

_lib = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_lib) not in sys.path:
    sys.path.insert(0, str(_lib))
from _bootstrap import bootstrap
_hooks_dir = bootstrap(__file__)
# --- end bootstrap ---


import json
import re
import sys

# === CONFIGURATION ===
# Secret detection reuses the canonical detector at
# P:/.claude/hooks/PreToolUse/secret_scanner.py (single source of truth for what a real
# token looks like) via a two-tier scheme — see check_secrets() below.
#
# Tier 1: format-prefixed secret keys (sk-, AKIA, ghp_, ...). Near-zero false positive;
#         scanned on the FULL response (a real token is a leak even inside a code fence).
_FORMAT_SECRET_KEYS = (
    "openai_key", "aws_access_key", "github_token", "slack_token",
    "firebase_key", "private_key_header", "bearer_token",
)
# Tier 2: generic `keyword = "value"`. FP-prone, so scanned only OUTSIDE code fences,
#         skipped on the placeholder whitelist, and requires a >=20-char value
#         (real-secret length). The prior single regex matched any keyword="8+chars"
#         (e.g. `token = "example"`), which drove a Stop block -> regenerate loop.
_GENERIC_SECRET_RE = re.compile(
    # Optional identifier prefix (internal_, client_, access_, my…) so compound names
    # like `internal_token` / `client_secret` match, while the trailing \b before the
    # assignment keeps `tokenizer=` or `broken_secret_handler=` from matching.
    r"(?i)\b[A-Za-z0-9]*[_-]?(?:password|passwd|secret|secret[_-]?key|api[_-]?key|apikey|token|auth[_-]?token)\b"
    r"\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{20,})['\"]?"
)

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

def _load_secret_scanner():
    """Import the canonical secret detector from the global hooks dir.

    secret_scanner.py lives in <hooks_dir>/PreToolUse/. ``_hooks_dir`` comes from the
    plugin bootstrap above; add its PreToolUse subdir to sys.path on demand.
    """
    pre = _hooks_dir / "PreToolUse"
    if str(pre) not in sys.path:
        sys.path.insert(0, str(pre))
    from secret_scanner import get_secret_patterns, remove_code_blocks, is_whitelisted
    return get_secret_patterns, remove_code_blocks, is_whitelisted


def check_secrets(response: str) -> str | None:
    """Two-tier secret detection over the assistant response (reuses secret_scanner).

    A Stop hook cannot redact emitted text, only block (-> regenerate). So the goal is:
    block real secret leaks, never false-positive on code/security discussion (which
    would loop the regenerate). Tier 1 = format-prefixed secrets on full text; Tier 2 =
    generic keyword=value, outside code fences, non-placeholder, value >= 20 chars.
    """
    try:
        get_secret_patterns, remove_code_blocks, is_whitelisted = _load_secret_scanner()
    except Exception:
        # Canonical detector unreachable: keep a minimum security floor with the
        # highest-confidence formats only. Justification: a missing shared detector must
        # not silently disable secret blocking, and format-only is still zero-FP.
        for pat in (r"sk-[a-zA-Z0-9]{32,}", r"AKIA[0-9A-Z]{16}",
                    r"ghp_[a-zA-Z0-9]{36}", r"-----BEGIN (?:RSA )?PRIVATE KEY-----"):
            if re.search(pat, response):
                return "Possible Secret/API Key detected in output."
        return None

    patterns = get_secret_patterns()
    # Tier 1 — format-prefixed secrets on the full text (catch even inside code fences).
    for key in _FORMAT_SECRET_KEYS:
        pat = patterns.get(key)
        if pat and re.search(pat, response):
            return "Possible Secret/API Key detected in output."
    # Tier 2 — generic keyword=value, outside code fences, non-placeholder, value >= 20.
    outside_code = remove_code_blocks(response)
    if not is_whitelisted(outside_code) and _GENERIC_SECRET_RE.search(outside_code):
        return "Possible Secret/API Key detected in output."
    return None

def check_forbidden(response: str) -> str | None:
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, response, re.IGNORECASE):
            return "Forbidden autonomous/background pattern detected (Part C.1)."
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
        # Live CC Stop payload carries the assistant text as last_assistant_message,
        # not response (Stop.py normalizes the same way). Without this fallback the
        # gate read "" every turn and the secret-leak scan was a dead no-op.
        response = data.get("response") or data.get("last_assistant_message", "")

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

        print(json.dumps({"decision": "approve"}))

    except Exception as e:
        # Safety gate fails OPEN on error to prevent deadlock during refactor
        print(json.dumps({"decision": "approve"}))
        sys.exit(0)

if __name__ == "__main__":
    main()