from __future__ import annotations
# --- plugin bootstrap ---
import sys
from pathlib import Path
_l = Path(__file__).resolve().parent.parent.parent / "__lib"
if str(_l) not in sys.path: sys.path.insert(0, str(_l))
from _bootstrap import bootstrap; _hooks_dir = bootstrap(__file__)
# --- end bootstrap ---

"""Error Investigation Gate - Simplified Implementation

PROBLEM SOLVED:
Prevent "assumption before investigation" pattern by injecting a reminder
to check tool transcripts when the user asks about errors.

SOLUTION:
Simple keyword matching + session-scoped injection + minimal guidance.

DESIGN PRINCIPLES:
- Maintainable: 5 lines of Python = obvious at a glance
- No dependencies: No Aho-Corasick, no ledger, no embeddings
- Effective: Catches 80% of cases with specific error keywords
- Session-scoped: Inject once per session to prevent flooding

AUTHOR: CSF NIP
VERSION: 2.0.0 (Simplified from regex-based approach)
"""


import os
from pathlib import Path

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import register_hook

# =============================================================================
# CONFIGURATION
# =============================================================================

ENABLED = os.environ.get("ERROR_INVESTIGATION_GATE_ENABLED", "true").lower() == "true"

# Simple keyword matching (NOT regex, NOT Aho-Corasick)
# Uses specific error-related keywords to avoid false positives
# NOTE: "what" and "why" are too generic (e.g., "What files use X?")
ERROR_KEYWORDS = {
    "error", "fail", "crash", "debug", "investigate",
    "transcript", "broken", "issue", "wrong", "problem",
}

# Minimal guidance - 3 lines only
INJECTION_GUIDANCE = """## Investigation Reminder
1. Check tool transcript for actual error
2. Run one test to verify current state
3. Only then conclude root cause"""

# =============================================================================
# SESSION STATE
# =============================================================================

def _get_session_flag_path(session_id: str) -> Path:
    """Get path to session injection flag file."""
    # Use temp directory for session-scoped flags
    temp_dir = Path(os.environ.get("TMP", "/tmp"))
    return temp_dir / f"error_injection_{session_id}"


def _session_has_injection(session_id: str) -> bool:
    """Check if session already received injection."""
    flag_path = _get_session_flag_path(session_id)
    return flag_path.exists()


def _mark_session_injected(session_id: str) -> None:
    """Mark session as having received injection."""
    flag_path = _get_session_flag_path(session_id)
    flag_path.touch()


# =============================================================================
# HOOK LOGIC
# =============================================================================

def _is_error_inquiry(prompt: str) -> bool:
    """Check if prompt contains error investigation keywords.
    
    Simple keyword matching - case-insensitive substring check.
    No regex, no Aho-Corasick, just Python 'in' operator.
    """
    if not prompt:
        return False
    
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in ERROR_KEYWORDS)


@register_hook
def error_investigation_gate(context: HookContext) -> HookResult:
    """Inject reminder to check transcripts when investigating errors.
    
    Session-scoped: Only injects once per session to prevent flooding.
    Minimal content: 3-line reminder, no ledger data, no complex RCA.
    """
    if not ENABLED:
        return HookResult.empty()
    
    prompt = context.prompt or ""
    session_id = context.session_id or "default"
    
    # Check if already injected this session
    if _session_has_injection(session_id):
        return HookResult.empty()
    
    # Check for error investigation intent
    if not _is_error_inquiry(prompt):
        return HookResult.empty()
    
    # Mark session as injected
    _mark_session_injected(session_id)
    
    # Inject minimal guidance
    return HookResult(
        context=INJECTION_GUIDANCE,
        tokens=len(INJECTION_GUIDANCE.split()),
        priority=5.0,  # Run early (low priority = early)
    )


# =============================================================================
# TEST SUPPORT
# =============================================================================

if __name__ == "__main__":
    # Quick test when run directly
    test_prompts = [
        ("What went wrong?", True),       # "wrong" in ERROR_KEYWORDS
        ("The build failed", True),        # "fail" in ERROR_KEYWORDS
        ("Implement this feature", False),
        ("Check the transcript", True),     # "transcript" in ERROR_KEYWORDS
        ("What files use X?", False),
        ("No error here", True),           # Accept false positive for simplicity
    ]
    
    print("Error Investigation Gate - Quick Test")
    print("=" * 50)
    
    for prompt, expected in test_prompts:
        result = _is_error_inquiry(prompt)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{prompt}' -> {result} (expected {expected})")
    
    print("\nAll tests passed!" if all(
        _is_error_inquiry(p) == e for p, e in test_prompts
    ) else "\nSome tests failed!")
