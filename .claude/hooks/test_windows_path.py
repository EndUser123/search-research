#!/usr/bin/env python3
import re

# Test the Windows path extraction
evidence_text = "Read on `C:\\Users\\test\\file.py` showed content."
print("Text:", evidence_text)
print("Repr:", repr(evidence_text))

# Current pattern
pattern = r"Read\s+(?:on\s+)?(?:from\s+)?[`\"']([^`\"']+)[`\"']"
match = re.search(pattern, evidence_text, re.IGNORECASE)
if match:
    print("Matched:", match.group(1))
else:
    print("No match with current pattern")

# Test with the actual backslash pattern
test_patterns = [
    r"Read\s+(?:on\s+)?(?:from\s+)?[`\"']([^`\"']+)[`\"']",
    r"Read\s+(?:on\s+)?(?:from\s+)?[`\"']([^\x60\"\'']+)[\x60\"\'']",
    r"Read\s+(?:on\s+)?(?:from\s+)?[`\"']([^`\"'']*)[`\"']",
]

for i, pat in enumerate(test_patterns):
    match = re.search(pat, evidence_text, re.IGNORECASE)
    if match:
        print(f"Pattern {i} matched:", match.group(1))
