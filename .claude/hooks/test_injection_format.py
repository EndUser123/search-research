#!/usr/bin/env python3
from __future__ import annotations

"""
Test Hook - Verify Injection Works
==================================
Minimal test to determine which output format Claude Code accepts.

Test 1: Plain text only (no JSON)
Test 2: Simple JSON {"additionalContext": "..."}
Test 3: Full JSON {"hookSpecificOutput": {...}}
"""

import json
import sys
from pathlib import Path

hooks_dir = Path(__file__).resolve().parent

# Read input
try:
    input_data = json.loads(sys.stdin.read())
    prompt = input_data.get("prompt", "")
except:
    prompt = ""

# Only trigger on test prompts
if "INJECTION_TEST" not in prompt:
    # Pass through silently
    sys.exit(0)

# Determine which test format to use based on prompt
test_type = "plain"  # default
if "TEST_JSON_SIMPLE" in prompt:
    test_type = "json_simple"
elif "TEST_JSON_FULL" in prompt:
    test_type = "json_full"
elif "TEST_PLAIN" in prompt:
    test_type = "plain"

# Log what we're doing
log_file = hooks_dir / "hooks/logs/injection_test.log"
log_file.parent.mkdir(parents=True, exist_ok=True)
with open(log_file, "a") as f:
    f.write(f"TEST: {test_type}\n")

if test_type == "plain":
    # Option A: Plain text only
    print("🧪 INJECTION TEST SUCCESSFUL - PLAIN TEXT FORMAT")
    print("If Claude sees this, plain text injection works!")
    sys.exit(0)

elif test_type == "json_simple":
    # Option B: Simple JSON
    output = {
        "additionalContext": "🧪 INJECTION TEST SUCCESSFUL - SIMPLE JSON FORMAT\nIf Claude sees this, simple JSON injection works!"
    }
    print(json.dumps(output))
    sys.exit(0)

elif test_type == "json_full":
    # Option C: Full hookSpecificOutput format
    output = {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "🧪 INJECTION TEST SUCCESSFUL - FULL JSON FORMAT\nIf Claude sees this, full JSON injection works!"
        }
    }
    print(json.dumps(output))
    sys.exit(0)
