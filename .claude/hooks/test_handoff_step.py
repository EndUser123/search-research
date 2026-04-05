#!/usr/bin/env python3
"""Test where PreCompact_handoff_capture blocks."""
import subprocess
import sys

tests = [
    # Test 1: Import the handoff modules
    ("import handoff config", """
import sys
sys.path.insert(0, r'P:/packages/handoff')
from handoff.config import ensure_directories
ensure_directories()
print("Step 1 OK")
"""),
    # Test 2: Import handoff_store
    ("import handoff_store", """
import sys
sys.path.insert(0, r'P:/packages/handoff')
from core.hooks.__lib import handoff_store
print("Step 2 OK")
"""),
    # Test 3: Import terminal_detection
    ("import terminal_detection", """
import sys
sys.path.insert(0, r'P:/.claude/hooks')
from __lib.terminal_detection import detect_terminal_id
print(f"Step 3 OK: {detect_terminal_id()}")
"""),
]

for name, code in tests:
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            timeout=5,
        )
        print(f"{name}: Exit {result.returncode}")
        if result.returncode == 0:
            print(f"  stdout: {result.stdout.decode().strip()}")
        else:
            print(f"  stderr: {result.stderr.decode()[:200]}")
    except subprocess.TimeoutExpired:
        print(f"{name}: TIMEOUT")
