#!/usr/bin/env python3
"""Test stub: Stop - ALWAYS passes through"""
import json
import sys

try:
    input_text = sys.stdin.read()
    if input_text.strip():
        data = json.loads(input_text)
    else:
        data = {"response": "test"}
    print("🧪 TEST Stop", file=sys.stderr)
    print(json.dumps(data))
except Exception:
    print("🧪 TEST Stop (no input)", file=sys.stderr)
    print(json.dumps({"response": "test"}))
