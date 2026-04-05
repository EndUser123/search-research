#!/usr/bin/env python3
"""Trace execution of PreCompact_handoff_capture to find where it blocks."""
import os
import sys

# Add paths
sys.path.insert(0, r"P:/packages/handoff/src")
sys.path.insert(0, r"P:/.claude/hooks")

# Set env var
os.environ["HANDOFF_INPUT"] = "{}"

# Step by step import and execution
print("Step 1: Importing hook_base...", flush=True)
try:
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAILED: {e}", flush=True)
    sys.exit(1)

print("Step 2: Importing handoff modules...", flush=True)
try:
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAILED: {e}", flush=True)
    sys.exit(1)

print("Step 3: Importing terminal_detection...", flush=True)
try:
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAILED: {e}", flush=True)
    sys.exit(1)

print("Step 4: Importing PreCompact_handoff_capture module...", flush=True)
try:
    import PreCompact_handoff_capture
    print("  OK", flush=True)
except Exception as e:
    print(f"  FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Step 5: Calling main()...", flush=True)
try:
    exit_code = PreCompact_handoff_capture.main()
    print(f"  Exit code: {exit_code}", flush=True)
except Exception as e:
    print(f"  FAILED: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("ALL STEPS COMPLETED")
