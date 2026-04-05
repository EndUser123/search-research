#!/usr/bin/env python3
import os
import subprocess
import sys

sys.path.insert(0, r"P:\.claude\hooks\tests")
os.chdir(r"P:\.claude\hooks\tests")

result = subprocess.run(
    ["python", "-m", "pytest", "test_powerhook_validation.py", "-v", "--tb=short"],
    capture_output=True,
    text=True,
)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr)
sys.exit(result.returncode)
