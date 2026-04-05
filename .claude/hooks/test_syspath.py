#!/usr/bin/env python3
"""Test if sys.path modifications cause blocking."""
import sys

sys.path.insert(0, r"P:/packages/handoff/src")
sys.path.insert(0, r"P:/.claude/hooks")

print("Step 1: Importing hook_base...", flush=True)
print("  OK", flush=True)

print("Step 2: Importing handoff modules...", flush=True)
print("  OK", flush=True)

print("Step 3: Importing terminal_detection...", flush=True)
print("  OK", flush=True)

print("Step 4: Importing PreCompact_handoff_capture...", flush=True)
print("  OK", flush=True)

print("ALL OK")
