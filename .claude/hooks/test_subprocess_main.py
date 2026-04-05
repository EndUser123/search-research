#!/usr/bin/env python3
"""Test main() execution with minimal setup."""
import os
import sys

sys.path.insert(0, r"P:/packages/handoff/src")
sys.path.insert(0, r"P:/__csf/src")
sys.path.insert(0, r"P:/.claude/hooks")

# Set env var for hook input
os.environ["HANDOFF_INPUT"] = "{}"

print("TEST: Importing hook_base...", flush=True)

print("TEST: Importing main hook file...", flush=True)
import PreCompact_handoff_capture

print("TEST: Calling main()...", flush=True)
exit_code = PreCompact_handoff_capture.main()
print(f"TEST: main() returned {exit_code}", flush=True)

print("TEST: COMPLETE")
