"""
Investigation Verification Module

Prevents lazy investigation patterns by ensuring comprehensive search
across all error log sources before concluding "no error found."

Features:
- Keyword detection with synonyms and obfuscation normalization
- Bypass flag support with audit logging
- Multi-source investigation verification
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

# Configure logging (no stderr output)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# =============================================================================
# Configuration
# =============================================================================

# Direct investigation keywords
DIRECT_KEYWORDS = [
    "investigate",
    "investigation",
    "debug",
    "diagnose",
    "trace",
    "analyze",
]

# Synonym keywords (less explicit but indicate investigation)
SYNONYM_KEYWORDS = [
    "trouble",
    "issue",
    "problem",
    "error",
    "broken",
    "crash",
    "fail",
    "bug",
    "wrong",
    "incorrect",
]

# Bypass flag
BYPASS_FLAG = "--skip-investigation-verify"

# Bypass log file location
HOOKS_DIR = Path(__file__).resolve().parent.parent
BYPASS_LOG = HOOKS_DIR / "state" / "investigation_bypass.log"

# =============================================================================
# Bypass Flag Detection
# =============================================================================

def check_bypass_flag(data: dict[str, Any]) -> bool:
    """
    Check if the bypass flag is present in the user prompt.

    Args:
        data: Hook input data with userPrompt field

    Returns:
        True if bypass flag detected, False otherwise
    """
    user_prompt = data.get("userPrompt", "")

    if not isinstance(user_prompt, str):
        return False

    # Check for bypass flag
    if BYPASS_FLAG in user_prompt:
        # Log the bypass usage
        _log_bypass_usage(data)
        return True

    return False


def _log_bypass_usage(data: dict[str, Any]) -> None:
    """
    Log bypass flag usage to audit file.

    Args:
        data: Hook input data
    """
    try:
        # Ensure state directory exists
        BYPASS_LOG.parent.mkdir(parents=True, exist_ok=True)

        # Get session ID
        session_id = data.get("sessionId", "unknown")

        # Create log entry
        timestamp = datetime.now().isoformat()
        user_prompt = data.get("userPrompt", "")

        log_entry = f"[{timestamp}] Session: {session_id} | Bypass flag used | Prompt: {user_prompt[:100]}\n"

        # Append to log file
        with open(BYPASS_LOG, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    except OSError as e:
        logger.error(f"Failed to log bypass usage: {e}")


# =============================================================================
# Keyword Detection
# =============================================================================

def has_investigation_keywords(data: dict[str, Any]) -> bool:
    """
    Check if the user prompt contains investigation keywords.

    Detects direct keywords, synonyms, and handles obfuscated
    keywords (e.g., "e r r o r" with spaces).

    Args:
        data: Hook input data with userPrompt field

    Returns:
        True if investigation keywords detected, False otherwise
    """
    user_prompt = data.get("userPrompt", "")

    if not isinstance(user_prompt, str):
        # Non-string input (e.g., dict) - convert and check
        user_prompt = str(user_prompt)

    if not user_prompt:
        return False

    # Normalize: remove spaces for obfuscation detection
    normalized = user_prompt.replace(" ", "").lower()

    # Check direct keywords
    for keyword in DIRECT_KEYWORDS:
        if keyword.lower() in user_prompt.lower():
            return True

    # Check synonym keywords
    for keyword in SYNONYM_KEYWORDS:
        if keyword.lower() in user_prompt.lower():
            return True

    # Check obfuscated keywords (e.g., "e r r o r" → "error")
    for keyword in DIRECT_KEYWORDS + SYNONYM_KEYWORDS:
        if keyword.lower() in normalized:
            return True

    return False


# =============================================================================
# Investigation Verification Template
# =============================================================================

INVESTIGATION_VERIFICATION_TEMPLATE = """
## Multi-Source Investigation Verification

Before concluding "no error found" or "all checks passed," you MUST search
ALL error log sources. This is mandatory for investigation queries.

### Required Search Locations

1. **Claude Code State Errors**
   ```bash
   grep -r "error" .claude/state/session_data/*.jsonl
   ```

2. **CCS Error Logs**
   ```bash
   grep -r "error" ~/.claude/state/cc_errors.jsonl
   ```

3. **Hook Logs**
   ```bash
   ls -la .claude/hooks/logs/
   grep -r "error" .claude/hooks/logs/
   ```

4. **Recent Build Failures**
   ```bash
   git log --since='1 day ago' --oneline
   git diff HEAD~1
   ```

### Verification Protocol

- **Step 1**: Search ALL FOUR sources above
- **Step 2**: Report findings from each source
- **Step 3**: Only conclude "no error" after ALL sources checked
- **Step 4**: Document what you searched (evidence of thoroughness)

### Bypass Option

To skip this verification (not recommended), use: {bypass_flag}

---

*This verification prevents lazy investigation patterns where only one
source is checked before concluding "no error found."*
""".strip().format(bypass_flag=BYPASS_FLAG)


# =============================================================================
# Main Entry Point
# =============================================================================

def run(data: dict[str, Any]) -> dict[str, Any] | None:
    """
    Run investigation verification.

    Injects mandatory search template when investigation keywords
    are detected and bypass flag is not present.

    Args:
        data: Hook input data with userPrompt field

    Returns:
        Dict with additionalContext to inject, or None if no injection needed
    """
    # Check for bypass flag first
    if check_bypass_flag(data):
        # User explicitly opted out - no verification
        return None

    # Check for investigation keywords
    if not has_investigation_keywords(data):
        # Not an investigation query - no verification needed
        return None

    # Investigation query detected - inject verification template
    return {
        "additionalContext": INVESTIGATION_VERIFICATION_TEMPLATE,
        "tokens": len(INVESTIGATION_VERIFICATION_TEMPLATE.split())
    }
