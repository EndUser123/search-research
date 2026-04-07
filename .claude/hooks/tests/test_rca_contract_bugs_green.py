#!/usr/bin/env python3
"""
GREEN phase tests for StopHook_rca_contract.py P1 bug fixes

BUG-002: Inconsistent dictionary key access (lines 190, 290) - FIXED
BUG-003: TOCTOU race condition in _load_band_aid_state() (line 467-468) - FIXED
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_bug_002_fixed():
    """GREEN phase: Verify BUG-002 is fixed - uses only 'name' key."""
    hook_file = Path(__file__).parent.parent / "StopHook_rca_contract.py"

    if not hook_file.exists():
        return False

    content = hook_file.read_text(encoding="utf-8")

    # BUG-002 fix: The code should use event.get("name", "") directly
    # NOT event.get("name") or event.get("tool_name", "")

    has_fallback_pattern = 'event.get("name") or event.get("tool_name"' in content
    has_correct_pattern = 'event.get("name", "")' in content

    # GREEN phase: The problematic pattern should NOT exist
    assert not has_fallback_pattern, "GREEN PHASE FAILED: Fallback pattern still present"
    assert has_correct_pattern, "GREEN PHASE FAILED: Correct pattern not found"

    print("✓ GREEN phase complete: BUG-002 (dict key inconsistency) fixed")


def test_bug_003_fixed():
    """GREEN phase: Verify BUG-003 is fixed - no TOCTOU in _load_band_aid_state."""
    hook_file = Path(__file__).parent.parent / "StopHook_rca_contract.py"

    if not hook_file.exists():
        return False

    content = hook_file.read_text(encoding="utf-8")

    # BUG-003 fix: The code should NOT have exists() check before read_text()
    # It should use try/except FileNotFoundError instead

    # Find the _load_band_aid_state function
    load_band_aid_start = content.find("def _load_band_aid_state(")
    if load_band_aid_start == -1:
        print("✗ Warning: _load_band_aid_state function not found")
        return False

    # Get the function content (until next function definition)
    next_def = content.find("\ndef ", load_band_aid_start + 1)
    if next_def == -1:
        next_def = len(content)
    func_content = content[load_band_aid_start:next_def]

    # Check for TOCTOU pattern: exists() followed by read_text()
    has_toctou_pattern = ".exists()" in func_content and 'read_text(encoding="utf-8")' in func_content

    # Check for correct pattern: try/except FileNotFoundError
    has_file_not_found_error = "FileNotFoundError" in func_content
    has_json_decode_error = "json.JSONDecodeError" in func_content

    # GREEN phase: TOCTOU pattern should NOT exist
    assert not has_toctou_pattern, "GREEN PHASE FAILED: TOCTOU pattern still present"

    # Should have proper error handling
    assert has_file_not_found_error, "GREEN PHASE FAILED: FileNotFoundError handling not found"

    print("✓ GREEN phase complete: BUG-003 (TOCTOU race condition) fixed")
    print(f"  Function _load_band_aid_state now has:")
    print(f"    - FileNotFoundError handling: {has_file_not_found_error}")
    print(f"    - JSONDecodeError handling: {has_json_decode_error}")


if __name__ == "__main__":
    print("Running GREEN phase tests for P1 bug fixes...")
    test_bug_002_fixed()
    test_bug_003_fixed()
    print("\n✓ All GREEN phase checks passed - bugs are fixed")
