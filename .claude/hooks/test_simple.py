#!/usr/bin/env python3
import subprocess
import sys

# Run without stdin input - see if it starts
result = subprocess.run(
    [sys.executable, "-c", "print('hello'"],
    capture_output=True,
    timeout=2,
)
print(f"Simple test: Exit {result.returncode}, stdout: {result.stdout.decode()}")

# Now try the hook with minimal input
result = subprocess.run(
    [sys.executable, "-c", "import sys; data = sys.stdin.read(; print('Got:', repr(data))"],
    input=b"{}",
    capture_output=True,
    timeout=2,
)
print(f"Stdin test: Exit {result.returncode}, stdout: {result.stdout.decode()}")
