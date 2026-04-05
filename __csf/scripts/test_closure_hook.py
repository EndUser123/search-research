
import sys
import os

# Add the hooks directory to the path so we can import the hook
sys.path.append(os.path.abspath("P:/.claude/hooks"))

try:
    import StopHook_closure_enforcer as hook
except ImportError:
    print("Error: Could not import StopHook_closure_enforcer. Check path.")
    sys.exit(1)

# Test Case 1: Diagnosis without Recommendation (Should Fail)
response_fail_diagnosis = """
## Root Cause
The issue is caused by a null pointer exception in the login handler.
"""
result = hook.check_closure(response_fail_diagnosis)
print(f"Test 1 (Diagnosis Only): {'PASSED' if not result['allow'] else 'FAILED'}")
if result['allow']:
    print("  -> Expected block, but was allowed.")
else:
    print(f"  -> Blocked as expected: {result['reason']}")

# Test Case 2: Fix without Verification (Should Fail)
response_fail_fix = """
I have fixed the issue by updating the settings.json file.
"""
result = hook.check_closure(response_fail_fix)
print(f"Test 2 (Fix Only): {'PASSED' if not result['allow'] else 'FAILED'}")
if result['allow']:
    print("  -> Expected block, but was allowed.")
else:
    print(f"  -> Blocked as expected: {result['reason']}")

# Test Case 3: Complete Diagnosis (Should Pass)
response_pass_diagnosis = """
## Root Cause
The issue is caused by a null pointer exception.

## Recommendation
We should add a null check before accessing the user object.
"""
result = hook.check_closure(response_pass_diagnosis)
print(f"Test 3 (Complete Diagnosis): {'PASSED' if result['allow'] else 'FAILED'}")
if not result['allow']:
    print(f"  -> Unexpected block: {result['reason']}")

# Test Case 4: Complete Fix (Should Pass)
response_pass_fix = """
I have fixed the issue by adding the missing environmental variable.
Verification:
I ran the system test and confirmed it passes.
"""
result = hook.check_closure(response_pass_fix)
print(f"Test 4 (Complete Fix): {'PASSED' if result['allow'] else 'FAILED'}")
if not result['allow']:
    print(f"  -> Unexpected block: {result['reason']}")
