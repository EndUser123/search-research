#!/usr/bin/env python3
"""Test with HANDOFF_INPUT env var."""
import os
import sys

sys.path.insert(0, r"P:/packages/handoff/src")
sys.path.insert(0, r"P:/.claude/hooks")

os.environ["HANDOFF_INPUT"] = "{}"

print("Step 1: Importing hook_base...", flush=True)
print("  OK", flush=True)

print("Step 2: Importing handoff modules...", flush=True)
print("  OK", flush=True)

print("Step 3: Importing terminal_detection...", flush=True)
print("  OK", flush=True)

print("Step 4: Importing PreCompact_handoff_capture...", flush=True)
import PreCompact_handoff_capture

print("  OK", flush=True)

print("Step 5: Calling main()...", flush=True)
exit_code = PreCompact_handoff_capture.main()
print(f"  Exit code: {exit_code}", flush=True)

print("ALL OK")
