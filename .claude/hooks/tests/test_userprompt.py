#!/usr/bin/env python3
"""Test stub: UserPromptSubmit - ALWAYS passes through"""
import json
import sys

try:
    input_text = sys.stdin.read()
    if input_text.strip():
        data = json.loads(input_text)
    else:
        data = {"prompt": ""}
    print("🧪 TEST UserPromptSubmit", file=sys.stderr)
    print(json.dumps(data))
except Exception:
    print("🧪 TEST UserPromptSubmit (no input)", file=sys.stderr)
    print(json.dumps({"prompt": ""}))
