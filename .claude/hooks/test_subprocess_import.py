#!/usr/bin/env python3
"""Test imports one at a time in subprocess to find the blocker."""
import os
import sys

print("TEST: Step 1 - sys.path setup", flush=True)
sys.path.insert(0, r"P:/packages/handoff/src")
sys.path.insert(0, r"P:/__csf/src")
sys.path.insert(0, r"P:/.claude/hooks")

print("TEST: Step 2 - Import hook_base", flush=True)

print("TEST: Step 3 - Import handoff.config", flush=True)

print("TEST: Step 4 - Import handoff.migrate", flush=True)

print("TEST: Step 5 - Import handoff.protocol", flush=True)

print("TEST: Step 6 - Import handoff_store module", flush=True)
from core.hooks.__lib import handoff_store

print("TEST: Step 7 - Import handover module", flush=True)
from core.hooks.__lib import handover

print("TEST: Step 8 - Import task_identity_manager module", flush=True)
from core.hooks.__lib import task_identity_manager

print("TEST: Step 9 - Import transcript module", flush=True)
from core.hooks.__lib import transcript

print("TEST: Step 10 - Import session_activity_tracker", flush=True)
try:
    from modules.session_management.session_activity_tracker import (
        _get_session_id_from_env,
        get_session_files,
    )
    print("  OK")
except ImportError:
    print("  Not available")

print("TEST: Step 11 - Import terminal_detection", flush=True)
try:
    from __lib.terminal_detection import detect_terminal_id
    print("  OK")
except ImportError:
    print("  Using fallback")

print("TEST: Step 12 - Create class aliases", flush=True)
HandoffStoreClass = handoff_store.HandoffStore
HandoverBuilder = handover.HandoverBuilder
TaskIdentityManager = task_identity_manager.TaskIdentityManager
TranscriptParser = transcript.TranscriptParser
print("  OK")

print("TEST: Step 13 - Define PreCompactHandoffCapture class", flush=True)
print("  (skipping for test - just checking imports)")

print("TEST: Step 14 - Read stdin (should be DEVNULL)", flush=True)
input_text = sys.stdin.read().strip()
if not input_text:
    input_text = os.environ.get("HANDOFF_INPUT", "").strip()
print(f"  input_text: '{input_text}'")

print("TEST: ALL IMPORTS COMPLETE")
