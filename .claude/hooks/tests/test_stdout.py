#!/usr/bin/env python3
"""Test: Print to STDOUT (not stderr)"""
import json
import sys

try:
    input_text = sys.stdin.read()
    if input_text.strip():
        data = json.loads(input_text)
    else:
        data = {"prompt": ""}

    # Print TEST message to STDOUT (not stderr)
    print("🧪 TEST STDOUT MESSAGE", flush=True)
    print(json.dumps(data), flush=True)
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    print(json.dumps({"prompt": ""}))
