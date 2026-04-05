#!/usr/bin/env python3
import re

# Test the exact pattern from the file
pattern = r'Read\s+(?:on\s+)?(?:from\s+)?["\`]([^\`"]+)["\`]'
print("Pattern:", pattern)

# Test case from the test file
evidence_text = "Read on `C:\\Users\\test\\file.py` showed content."
print("Evidence text:", evidence_text)
print("Evidence repr:", repr(evidence_text))

match = re.search(pattern, evidence_text, re.IGNORECASE)
if match:
    print("Match found!")
    print("Match group 1:", match.group(1))
    print("Match group 1 repr:", repr(match.group(1)))
else:
    print("No match found")

# Now let's see what happens with the test string format
test_text = r"Read on `C:\\Users\\test\\file.py` showed content."
print("\nTest text:", test_text)
print("Test text repr:", repr(test_text))

match2 = re.search(pattern, test_text, re.IGNORECASE)
if match2:
    print("Match2 found!")
    print("Match2 group 1:", match2.group(1))
    print("Match2 group 1 repr:", repr(match2.group(1)))
else:
    print("Match2 no match found")
