#!/usr/bin/env python3
import re

# The actual test case
evidence_text = "Read on `C:\\Users\\test\\file.py` showed content."
print("Evidence text:", evidence_text)
print("Evidence repr:", repr(evidence_text))

# Current pattern
pattern = r'Read\s+(?:on\s+)?(?:from\s+)?[`\"']([^`\"']+)[`\"']'
print("Pattern:", pattern)

match = re.search(pattern, evidence_text, re.IGNORECASE)
if match:
    print("Matched group:", match.group(1))
    print("Matched group repr:", repr(match.group(1)))
else:
    print("No match")

# Pattern with backslash support
pattern_with_backslash = r'Read\s+(?:on\s+)?(?:from\s+)?[`\"']([^`\"'\\]+)[`\"']'
print()
print("Pattern with backslash:", pattern_with_backslash)
match2 = re.search(pattern_with_backslash, evidence_text, re.IGNORECASE)
if match2:
    print("Matched group:", match2.group(1))
else:
    print("No match with backslash pattern")
