#!/usr/bin/env python3
"""Test the historical claims gate fix."""
import sys
sys.path.insert(0, r'P:\.claude\hooks')
from Stop_historical_claims_gate import tier1_check

# Test 1: User's example - should now be detected
response1 = 'The tests I ran demonstrate that the fix works.'
should_trigger1, context1, category1 = tier1_check(response1)
print(f'Test 1: The tests I ran demonstrate')
print(f'  should_trigger={should_trigger1}, category={repr(category1)}')
print(f'  Context: {repr(context1[:80] if context1 else "None")}')
print()

# Test 2: gh was found before but now it's not - should detect fake state transition
response2 = 'gh was found before but now it is not found.'
should_trigger2, context2, category2 = tier1_check(response2)
print(f'Test 2: gh was found before but now not')
print(f'  should_trigger={should_trigger2}, category={repr(category2)}')
print(f'  Context: {repr(context2[:80] if context2 else "None")}')
print()

# Test 3: Honest environment mismatch - should NOT trigger
response3 = 'I see Bash cannot find gh while you report it works; this is likely a PATH mismatch.'
should_trigger3, context3, category3 = tier1_check(response3)
print(f'Test 3: Honest environment mismatch')
print(f'  should_trigger={should_trigger3}, category={repr(category3)}')
