"""
PreToolUse Verification Modules

This package contains verification modules for the PreToolUse
verification router. Each module implements a run() function that
takes hook input data and returns a dict with additionalContext
to inject, or None if no injection is needed.

Available modules:
- investigation_verification: Prevents lazy investigation patterns
"""

from .investigation_verification import (
    BYPASS_FLAG,
    BYPASS_LOG,
    INVESTIGATION_VERIFICATION_TEMPLATE,
    check_bypass_flag,
    has_investigation_keywords,
    run,
)

__all__ = [
    "BYPASS_LOG",
    "BYPASS_FLAG",
    "INVESTIGATION_VERIFICATION_TEMPLATE",
    "check_bypass_flag",
    "has_investigation_keywords",
    "run",
]
