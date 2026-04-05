#!/usr/bin/env python3
"""Test stub: SessionStart - ALWAYS passes through"""
import json
import sys

try:
    input_text = sys.stdin.read()
    if input_text.strip():
        data = json.loads(input_text)
    else:
        data = {"session_id": "test"}
    print("🧪 TEST SessionStart", file=sys.stderr)
    print(json.dumps(data))
except Exception:
    print("🧪 TEST SessionStart (no input)", file=sys.stderr)
    print(json.dumps({"session_id": "test"}))
