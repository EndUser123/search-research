#!/usr/bin/env python3
"""Debug phrase matching in historical claims gate."""
import sys
sys.path.insert(0, r'P:\.claude\hooks')
from Stop_historical_claims_gate import check_fake_state_transition

# Test the fake state transition detector
response = 'gh was found before but now it is not found.'
is_blocking, reason_code, detected = check_fake_state_transition(response, [])

print(f'Fake state transition test:')
print(f'  is_blocking={is_blocking}')
print(f'  reason_code={reason_code}')
print(f'  detected_claims={detected}')

# Also debug phrase matching directly
response_lower = response.lower()
print(f'\nDirect phrase debug:')
print(f'  response_lower = {repr(response_lower)}')

# Check past success phrases
past_phrases = ['was found before', 'used to work', 'worked earlier']
print(f'\n  Checking past phrases:')
for p in past_phrases:
    result = p in response_lower
    print(f'    {repr(p)}: {result}')

# Check current failure phrases
current_phrases = ['now not found', 'now it\'s not']
print(f'\n  Checking current failure phrases:')
for p in current_phrases:
    result = p in response_lower
    print(f'    {repr(p)}: {result}')
