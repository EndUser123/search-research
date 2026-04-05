#!/usr/bin/env python3
"""Test stub: PostToolUse - ALWAYS passes through"""
import json
import sys

try:
    input_text = sys.stdin.read()
    if input_text.strip():
        data = json.loads(input_text)
    else:
        data = {"tool": "Test"}
    print("🧪 TEST PostToolUse", file=sys.stderr)
    print(json.dumps(data))
except Exception:
    print("🧪 TEST PostToolUse (no input)", file=sys.stderr)
    print(json.dumps({"tool": "Test"}))
