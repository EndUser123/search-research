#!/usr/bin/env python3
"""Test concern detection on recent user messages"""
import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

import user_prompt_submit_concern_detection as mod

test_messages = [
    "what the fuck?  stop being stupid.",
    "Can worktrees hide the info until after a git sync?",
    "I've not seen any anti-verification indicators lately.  Is that hook working?",
]

print(f"Hook enabled: {mod.ENABLED}")
print(f"State file: {mod.STATE_FILE}")
print(f"State file exists: {mod.STATE_FILE.exists()}")
print()

for msg in test_messages:
    print(f"Testing: {msg[:60]}...")
    result = mod.process_hook(msg)
    if result:
        print(f"  ✅ DETECTED - Injection: {result[:100]}...")
    else:
        print("  ❌ NO DETECTION")
    print()
