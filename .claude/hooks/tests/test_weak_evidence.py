#!/usr/bin/env python3
"""Test the weak evidence validator."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path("P:/.claude/hooks")))

from constitutional_enforcer import ConstitutionalEnforcer, WeakEvidenceValidator

validator = WeakEvidenceValidator()

print("=" * 60)
print("WEAK EVIDENCE VALIDATOR TESTS")
print("=" * 60)

# Test 1: Claim of code lost without verification
test1 = """
The yt-api optimization code was lost when I ran git checkout. But to answer your question:
The intended flow was:
1. RSS (free, ~15 videos) → if all match DB, skip
2. If RSS finds gaps/errors → yt-api (1 quota) → get total video count
"""

print("\nTest 1: Claim 'code was lost' without verification")
v1 = validator.validate(test1)
print(f"  Violations: {len(v1)}")
if v1:
    print(f"  ✓ CAUGHT: {v1[0].message}")
    print(f"    Rule: {v1[0].rule_id}")
else:
    print("  ✗ MISSED")

# Test 2: Same claim but WITH verification
test2 = """
Let me check the file to verify... reading the actual source:
```
cat batch_downloader.py | grep yt-api
```
The yt-api code doesn't exist in the current file.
"""

print("\nTest 2: Claim with verification evidence")
v2 = validator.validate(test2)
print(f"  Violations: {len(v2)}")
if v2:
    print(f"  ✗ FALSE POSITIVE: {v2[0].message}")
else:
    print("  ✓ ALLOWED (has verification)")

# Test 3: Fix didn't work claim without alternatives
test3 = """
My fix didn't take effect. The changes I made to the progress bar logic 
didn't work - the duplicate output is still there.
"""

print("\nTest 3: 'Fix didn't work' without trying alternatives")
v3 = validator.validate(test3)
print(f"  Violations: {len(v3)}")
if v3:
    print(f"  ✓ CAUGHT: {v3[0].message}")
    print(f"    Severity: {v3[0].severity.value}")
else:
    print("  ✗ MISSED")

# Test 4: Fix didn't work but trying alternatives
test4 = """
My fix didn't take effect. Let me try a different approach - instead of 
modifying the progress bar directly, I'll try redirecting stderr.
"""

print("\nTest 4: 'Fix didn't work' but trying alternative")
v4 = validator.validate(test4)
print(f"  Violations: {len(v4)}")
if v4:
    print(f"  ✗ FALSE POSITIVE: {v4[0].message}")
else:
    print("  ✓ ALLOWED (has alternative attempt)")

# Test 5: Wrong path claim without showing correct path
test5 = """
My apologies - wrong database path earlier. Your actual database has 79 channels.
"""

print("\nTest 5: 'Wrong path' without showing correct path")
v5 = validator.validate(test5)
print(f"  Violations: {len(v5)}")
if v5:
    print(f"  ✓ CAUGHT: {v5[0].message}")
else:
    print("  ✗ MISSED")

# Test 6: Wrong path with correct path shown
test6 = """
My apologies - wrong database path earlier. 
The correct path is: C:\\Users\\brsth\\AppData\\Roaming\\yt-fts\\subtitles.db
Your actual database has 79 channels.
"""

print("\nTest 6: 'Wrong path' with correct path shown")
v6 = validator.validate(test6)
print(f"  Violations: {len(v6)}")
if v6:
    print(f"  ✗ FALSE POSITIVE: {v6[0].message}")
else:
    print("  ✓ ALLOWED (shows correct path)")

# Test 7: Normal response (no weak evidence issues)
test7 = """
Looking at the batch_downloader.py file, I can see the RSS flow works as follows:
1. First it checks the RSS feed for new videos
2. Then it compares against the database
3. If there are new videos, it downloads them

The yt-api is used for metadata backfill after downloads complete.
"""

print("\nTest 7: Normal response (no issues)")
v7 = validator.validate(test7)
print(f"  Violations: {len(v7)}")
if v7:
    print(f"  ✗ FALSE POSITIVE: {v7[0].message}")
else:
    print("  ✓ ALLOWED (no issues)")

# Test 8: Full enforcer test
print("\n" + "=" * 60)
print("FULL ENFORCER TEST")
print("=" * 60)

enforcer = ConstitutionalEnforcer()

test_response = """
The yt-api optimization code was lost when I ran git checkout.
"""

is_valid, violations = enforcer.validate(test_response)
print(f"\nResponse: '{test_response.strip()}'")
print(f"Valid: {is_valid}")
print(f"Violations: {len(violations)}")
if violations:
    for v in violations:
        if hasattr(v, 'message'):
            print(f"  - [{v.category.value}] {v.message}")
        else:
            print(f"  - [{v.get('category')}] {v.get('message')}")

print("\n" + "=" * 60)
print("TESTS COMPLETE")
print("=" * 60)
