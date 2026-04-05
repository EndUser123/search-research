#!/usr/bin/env python3
import re

# The actual test case
evidence_text = "Read on `C:\\Users\\test\\file.py` showed content."
print("Evidence text:", evidence_text)
print("Evidence repr:", repr(evidence_text))

# Test the pattern step by step
# First, let's just match the backtick part
simple_pattern = r'`([^`]+)`'
match = re.search(simple_pattern, evidence_text)
if match:
    print("Simple pattern matched:", match.group(1))
else:
    print("Simple pattern no match")

# Current pattern from StopHook_rca_contract.py (fixed character class)
current_pattern = r'Read\s+(?:on\s+)?(?:from\s+)?[]`\"'`([^]`\"'']+)[`\"']'
match = re.search(current_pattern, evidence_text, re.IGNORECASE)
if match:
    print("Current pattern matched:", match.group(1))
else:
    print("Current pattern no match")

# Pattern with backslash support (fixed)
pattern_with_backslash = r'Read\s+(?:on\s+)?(?:from\s+)?[]`\"'`([^]`\"'\\\\]+)[`\"']'
match = re.search(pattern_with_backslash, evidence_text, re.IGNORECASE)
if match:
    print("Pattern with backslash matched:", match.group(1))
else:
    print("Pattern with backslash no match")
