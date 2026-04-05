#!/usr/bin/env python3
import sys

sys.path.insert(0, ".")

from StopHook_rca_contract import _extract_artifact_paths

# Test the actual Windows path case
evidence_text = r"Read on `C:\\Users\\test\\file.py` showed content."
print("Evidence text:", evidence_text)
print("Evidence repr:", repr(evidence_text))

paths = _extract_artifact_paths(evidence_text)
print("Extracted paths:", paths)
print("Number of paths:", len(paths))
for i, path in enumerate(paths):
    print(f"Path {i}: {path}")
    print(f"  Contains file.py: {'file.py' in path}")
