#!/usr/bin/env python3
# Test case from the test file
evidence_text = "Read on `C:\\\\Users\\\\test\\\\file.py` showed content."
print("Evidence text:", evidence_text)
print("Evidence repr:", repr(evidence_text))

# What we want it to be:
desired_text = r"Read on `C:\\Users\\test\\file.py` showed content."
print("\nDesired text:", desired_text)
print("Desired repr:", repr(desired_text))

# Test with the actual function
import sys

sys.path.insert(0, ".")
from StopHook_rca_contract import _extract_artifact_paths

paths = _extract_artifact_paths(evidence_text)
print("\nExtracted paths:", paths)
for i, path in enumerate(paths):
    print(f"Path {i}: {path}")
    print(f"  Contains file.py: {'file.py' in path}")
