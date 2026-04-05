#!/usr/bin/env python3
"""Test if git branch call causes timeout in subprocess."""
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path("P:/").resolve()

print("Test 1: git branch with normal env", flush=True)
try:
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT,
        timeout=5),
)
    print(f"  Result: {result.stdout.strip()}", flush=True)
except Exception as e:
    print(f"  Failed: {e}", flush=True)

print("Test 2: git branch with isolated env", flush=True)
try:
    isolated_env = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    # Need to merge with existing env for PATH etc
    isolated_env.update({k: v for k, v in os.environ.items() if k not in isolated_env})

    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT,
        timeout=5,
        env=isolated_env),
)
    print(f"  Result: {result.stdout.strip()}", flush=True)
except Exception as e:
    print(f"  Failed: {e}", flush=True)

print("ALL OK")
