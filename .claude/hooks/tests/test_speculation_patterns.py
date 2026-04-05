#!/usr/bin/env python3
"""Test new speculation patterns in empirical_claims_gate."""

import re

PATTERNS = [
    r'\b(?:likely|probably)\s+(?:the|this|that|what|a)\s+(?:\w+\s+)?(?:cause|issue|problem|reason|hook|file|script)',
    r'\bthis\s+is\s+(?:likely|probably)\b',
    r'\bthat(?:\'s| is)\s+(?:likely|probably)\b',
    r'\bi\s+(?:believe|think)\s+(?:the|this|that|it)',
    r'\bseems\s+like\s+(?:the|this|that|a)',
    r'\bmost\s+likely\s+(?:caused|the|due|because|what)',
    r'\b(?:likely|probably)\s+what\s+(?:happened|caused|broke|failed|went)',
]

TEST_CASES = [
    # Should match (speculation)
    ('likely the relocator hook', True),
    ('probably the issue', True),
    ('this is likely the cause', True),
    ("that's probably what happened", True),
    ('I believe the hook moved it', True),
    ('I think this is the problem', True),
    ('seems like the file was moved', True),
    ('most likely caused by the hook', True),
    ('probably what happened', True),
    ('likely this hook', True),

    # Should NOT match (legitimate statements)
    ('the hook is working correctly', False),
    ('I verified the file exists', False),
    ('the likely cause was identified', False),  # "likely" as adjective, not speculative
]

def test_patterns():
    print('Testing speculation patterns:\n')
    passed = 0
    failed = 0

    for text, should_match in TEST_CASES:
        matched = any(re.search(p, text, re.IGNORECASE) for p in PATTERNS)
        status = '✓' if matched == should_match else '✗'

        if matched == should_match:
            passed += 1
        else:
            failed += 1

        print(f'  {status} "{text}"')
        if matched != should_match:
            print(f'      Expected: {should_match}, Got: {matched}')

    print(f'\nResults: {passed} passed, {failed} failed')
    return failed == 0

if __name__ == '__main__':
    import sys
    sys.exit(0 if test_patterns() else 1)
