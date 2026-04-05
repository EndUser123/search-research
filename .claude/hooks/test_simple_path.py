#!/usr/bin/env python3
import re

# The actual test case
evidence_text = "Read on `C:\\Users\\test\\file.py` showed content."
print("Evidence text:", evidence_text)
print("Evidence repr:", repr(evidence_text))

# Test the pattern step by step
# First, let's just match the backtick part
simple_pattern = r"`([^`]+)`"
match = re.search(simple_pattern, evidence_text)
if match:
    print("Simple pattern matched:", match.group(1))
else:
    print("Simple pattern no match")

# Test if the path contains backslashes
path_content = match.group(1) if match else ""
print("Path content repr:", repr(path_content))
print("Path contains backslash:", "\\" in path_content)

# Test the actual pattern we want to use
# Pattern: Read optionally followed by "on" or "from", then quoted path
# We want to capture: C:\Users\test\file.py
test_pattern = r'Read\s+(?:on\s+)?(?:from\s+)?["\`]([^\`"]+)["\`]'
match = re.search(test_pattern, evidence_text, re.IGNORECASE)
if match:
    print("Test pattern matched:", match.group(1))
else:
    print("Test pattern no match")
