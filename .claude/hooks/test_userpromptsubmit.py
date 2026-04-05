#!/usr/bin/env python3
"""Test UserPromptSubmit hook for stderr output."""

import subprocess
import sys

# Run UserPromptSubmit hook and capture ALL output
result = subprocess.run(
    [sys.executable, 'UserPromptSubmit.py'],
    input=b'{"prompt": "test"}',
    capture_output=True,
    timeout=5
)

print('=== Exit Code:', result.returncode, '===')
print()

print('=== STDERR ===')
stderr_text = result.stderr.decode('utf-8', errors='replace')
if stderr_text:
    print(stderr_text)
    print('^^^ STDERR DETECTED ^^^')
else:
    print('(empty)')

print()
print('=== STDOUT (first 500 chars) ===')
stdout_text = result.stdout.decode('utf-8', errors='replace')
print(stdout_text[:500])
print()
print('=== STDOUT length:', len(stdout_text), 'chars ===')
