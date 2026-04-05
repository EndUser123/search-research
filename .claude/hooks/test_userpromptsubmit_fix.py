#!/usr/bin/env python3
"""Test that UserPromptSubmit hook works correctly after the fix."""

import sys

sys.path.insert(0, 'P:/.claude/hooks')

from __lib.hook_importer import HookImporter


def test_userpromptsubmit_hook():
    """Test UserPromptSubmit hook execution."""
    importer = HookImporter('P:/.claude/hooks')
    result = importer.execute_hook('UserPromptSubmit')

    if result.get('ok'):
        print('✅ SUCCESS: UserPromptSubmit hook works correctly')
        print(f'   Output: {result.get("output", "").strip()[:50]}...')
        return True
    else:
        print(f'❌ FAILED: {result}')
        return False

if __name__ == '__main__':
    success = test_userpromptsubmit_hook()
    sys.exit(0 if success else 1)
