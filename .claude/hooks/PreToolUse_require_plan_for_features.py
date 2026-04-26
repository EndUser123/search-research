#!/usr/bin/env python3
"""
PreToolUse: Require Plan for New Features
==========================================

Blocks Write/Edit operations for new features when plan.md is missing.

Heuristic: New files = new features (require plan). Existing file edits = refactors/fixes (no plan needed).

Exemptions:
- Refactors (improve code quality)
- Bug fixes
- CRUD operations
- Simple changes
- Documentation, tests, imports
- Test files (via test_detection module)

Created: 2026-03-01
Author: CSF NIP
Version: 1.2.0 - OPTIMIZED: Uses shared path_classifier for cached classification
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Import shared path classifier (optimization: cached classification)
try:
    sys.path.insert(0, str(Path(__file__).resolve().parent / "__lib"))
    from path_classifier import (
        is_exempt_path,
        is_new_file,
        is_test_file,
    )
    CLASSIFIER_AVAILABLE = True
except ImportError:
    CLASSIFIER_AVAILABLE = False

# Refactor indicators in user messages
REFACTOR_INDICATORS = [
    r"\brefactor\b",
    r"\bclean\s*(up)?\b",
    r"\bimprove\b.*\bcode\b",
    r"\bcode\b.*\bquality\b",
    r"\breorganize\b",
    r"\brestructure\b",
]

# Bug fix indicators
BUG_FIX_INDICATORS = [
    r"\bfix\b",
    r"\bbug\b",
    r"\berror\b",
    r"\bissue\b",
    r"\bpatch\b",
]

# CRUD indicators
CRUD_INDICATORS = [
    r"\bcreate\b",
    r"\bread\b",
    r"\bupdate\b",
    r"\bdelete\b",
    r"\bcrud\b",
    r"\bsimple\b",
]


def is_refactor(user_message: str) -> bool:
    """Check if user message indicates refactor work."""
    if not user_message:
        return False
    for indicator in REFACTOR_INDICATORS:
        if re.search(indicator, user_message, re.IGNORECASE):
            return True
    return False


def is_bug_fix(user_message: str) -> bool:
    """Check if user message indicates bug fix work."""
    if not user_message:
        return False
    for indicator in BUG_FIX_INDICATORS:
        if re.search(indicator, user_message, re.IGNORECASE):
            return True
    return False


def is_crud_or_simple(user_message: str) -> bool:
    """Check if user message indicates CRUD or simple work."""
    if not user_message:
        return False
    for indicator in CRUD_INDICATORS:
        if re.search(indicator, user_message, re.IGNORECASE):
            return True
    return False


def get_ready_for_implementation_plans() -> list[Path]:
    """Find all plan result JSON files that are validator-ready for implementation.

    Returns:
        List of plan file paths that are ready for implementation
    """
    ready_plans = []

    # Check for plan result JSON files in common locations
    search_dirs = [
        Path(".claude/hooks/plans"),
        Path(".claude/plans"),
        Path("~/.claude/plans").expanduser(),
        Path(".claude"),
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        # Find all .review.result.json files
        for result_file in search_dir.glob("*.review.result.json"):
            try:
                result_data = json.loads(result_file.read_text(encoding="utf-8"))

                status = result_data.get("status")
                claimed_status = result_data.get("claimed_status")

                # Current verifier model: machine status READY + claimed_status implementation-ready
                legacy_ready = status == "READY-FOR-IMPLEMENTATION"
                current_ready = status == "READY" and claimed_status == "implementation-ready"

                if legacy_ready or current_ready:
                    # Extract plan path from result
                    plan_path_str = result_data.get("plan_path", "")
                    if plan_path_str:
                        plan_path = Path(plan_path_str)
                        if plan_path.exists():
                            ready_plans.append(plan_path)
            except (json.JSONDecodeError, OSError):
                # Skip malformed result files
                continue

    return ready_plans


def has_active_plan_review_state() -> bool:
    """Check if there's an active plan review in progress.

    Returns:
        True if plan review state file exists and has recent activity
    """
    # Check for plan workflow state file
    state_file = Path(".claude/hooks/state/pr_workflow.json")

    if not state_file.exists():
        # Fallback to alternate location
        state_file = Path("~/.claude/state/pr_workflow.json").expanduser()

    if not state_file.exists():
        return False

    try:
        state_data = json.loads(state_file.read_text(encoding="utf-8"))

        # Check if there's an active plan review
        # State contains: plan_path, current_phase, completed_phases, last_updated
        if state_data.get("plan_path"):
            # Check if last updated within last 24 hours
            import time
            last_updated = state_data.get("last_updated", 0)
            if time.time() - last_updated < 86400:  # 24 hours
                return True
    except (json.JSONDecodeError, OSError):
        pass

    return False


def plan_exists() -> bool:
    """Check if plan.md exists in the current session."""
    # Check both possible locations
    plan_paths = [
        Path(".claude/sessions/current/plan.md"),
        Path(".claude/plan.md"),
        Path("plan.md"),
    ]

    for plan_path in plan_paths:
        if plan_path.exists():
            return True
    return False


def has_active_plan_implementation() -> bool:
    """Check if there's an active plan being implemented.

    This is the enhanced version that checks:
    1. Plans with READY-FOR-IMPLEMENTATION status
    2. Active plan review state

    Returns:
        True if an active plan is being implemented
    """
    # Check 1: Ready-for-implementation plans
    if get_ready_for_implementation_plans():
        return True

    # Check 2: Active plan review state
    if has_active_plan_review_state():
        return True

    # Check 3: Legacy plan.md check
    if plan_exists():
        return True

    return False


def main() -> None:
    """Main entry point - optimized with shared path classifier."""
    # Read JSON from stdin
    raw_input = sys.stdin.read().strip()
    if not raw_input:
        sys.exit(0)

    try:
        data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        sys.exit(0)

    # Get file path from tool_input
    tool_input = data.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""

    if not file_path:
        sys.exit(0)

    # Get user message for intent detection
    user_message = data.get("user_message", "")

    # Use shared path classifier (single classification pass)
    if CLASSIFIER_AVAILABLE:
        # Test file exemption
        if is_test_file(file_path, data):
            sys.exit(0)

        # Exempt path check (config files, docs, libraries)
        if is_exempt_path(file_path, data):
            sys.exit(0)

        # Get file status from cache
        is_new = is_new_file(file_path, data)
    else:
        # Classifier unavailable — manual file existence check only
        path = Path(file_path)
        is_new = not path.exists() or path.stat().st_size == 0

    # Check 1: Is this clearly a refactor/fix/CRUD based on user message?
    if is_refactor(user_message) or is_bug_fix(user_message) or is_crud_or_simple(user_message):
        sys.exit(0)

    # Check 2: Does plan.md exist or is there an active plan being implemented?
    if has_active_plan_implementation():
        sys.exit(0)

    # Check 3: Is this a new file? (New file = new feature)
    if is_new:
        result = {
            "decision": "block",
            "reason": (
                f"**Plan Required:** Creating `{file_path}`\n\n"
                "Run: `/plan-workflow build <description>`\n\n"
                "Exemptions: refactor, fix, tests, docs, config"
            ),
            "blocking_hook": "PreToolUse_require_plan_for_features.py"
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(2)

    # For existing file edits without refactor indicators, allow but remind
    # (Only for edits that don't match exemption patterns)
    if tool_name == "Edit" and not is_refactor(user_message):
        # This is an existing file edit - allow it
        sys.exit(0)

    sys.exit(0)


if __name__ == "__main__":
    main()
