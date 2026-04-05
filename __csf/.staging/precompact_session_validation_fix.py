#!/usr/bin/env python3
"""
Session validation fix for PreCompact_handoff_capture.py

This is the actual code patch to add session ownership validation to PreCompact.
The fix should be inserted after line 548 (after task name is determined).
"""

import json
from pathlib import Path


def validate_session_ownership_before_handoff(
    transcript_path: str,
    project_root,
    task_name: str
) -> bool:
    """Validate that handoff belongs to current session before creating it.

    Args:
        transcript_path: Path to session transcript
        project_root: Project root path
        task_name: Name of task for logging

    Returns:
        True if handoff should be created, False if it should be skipped
    """
    # Extract session ID from transcript path
    # Path format: "P:/.claude/sessions/session_abc123.jsonl"
    handoff_session = Path(transcript_path).stem

    # Read current session from authoritative source
    current_session_file = project_root / ".claude" / "current_session.json"
    current_session = ""

    if current_session_file.exists():
        try:
            with open(current_session_file, encoding="utf-8") as f:
                current_session_data = json.load(f)
            current_session = current_session_data.get("session_id", "")
        except (json.JSONDecodeError, OSError):
            current_session = ""

    # Edge case: No current session (allow handoff creation)
    if not current_session:
        print("[PreCompact] ⚠️  No current session - creating handoff without validation")
        return True

    # Validate session ownership
    if handoff_session != current_session:
        print(f"[PreCompact] ⊘ Skipping handoff: '{task_name}' from stale session")
        print(f"  Handoff session: {handoff_session}")
        print(f"  Current session: {current_session}")
        print("  Action: Preventing wasted I/O on cross-session handoff")
        return False

    # Sessions match - proceed with handoff creation
    print(f"[PreCompact] ✓ Session validated: '{task_name}' belongs to current session")
    return True


# ============================================================
# INSERT THIS CODE INTO PreCompact_handoff_capture.py
# Location: After line 548 (after task name determination)
# Before: "Step 2: Extract handoff data..."
# ============================================================

# In the run() method of PreCompactHandoffCapture class:

"""
    def run(self) -> bool:
        \"\"\"Execute full PreCompact handoff process.

        Returns:
            True if handoff process succeeded, False otherwise
        \"\"\"
        print("[PreCompact] Starting handoff capture...")

        # Step 1: Get task identity
        task_name = self.task_manager.get_current_task()
        if not task_name:
            # Generate checkpoint name using timestamp
            task_name = f"session_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
            task_id = f"task_{task_name}"
            print(f"[PreCompact] Generated handoff task name: {task_name}")
        else:
            task_id = f"task_{task_name.lower()}"
            print(f"[PreCompact] Using task name: {task_name}")

        # ============================================================
        # NEW CODE: Session validation BEFORE handoff creation
        # ============================================================
        # Validate session ownership before extracting handoff data
        # This prevents wasted I/O creating handoffs that will be rejected
        # by SessionStart due to session mismatch
        if not validate_session_ownership_before_handoff(
            self.transcript_path,
            self.project_root,
            task_name
        ):
            # Session validation failed - skip handoff creation
            # Return True (success) because this is expected behavior, not an error
            print("[PreCompact] Handoff skipped due to session mismatch")
            return True
        # ============================================================

        # Step 2: Extract handoff data using focused components
        # (existing code continues unchanged...)
        progress_pct = self.extract_progress_percentage(task_name)
        # ... rest of the method
"""
