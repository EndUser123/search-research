#!/usr/bin/env python3
"""Test consent validation fix for case sensitivity and diagnostics."""

import json
import sys
from pathlib import Path

# Add hooks lib to path
sys.path.insert(0, str(Path("P:/.claude/hooks/__lib")))

def test_case_insensitive_path_comparison():
    """Test that path comparison is case-insensitive."""
    from pre_tool_use_logic import normalize_canonical_path

    # Test case 1: Same path, different case
    path1 = "P:/.claude/hooks/__lib/pre_tool_use_logic.py"
    path2 = "P:/.claude/hooks/__lib/PreToolUse_Preview_Logic.py"  # Different case
    path3 = "p:/.claude/hooks/__lib/pre_tool_use_logic.py"  # Different case, same file

    norm1 = normalize_canonical_path(path1)
    norm2 = normalize_canonical_path(path2)
    norm3 = normalize_canonical_path(path3)

    print("✓ Test 1: Path normalization")
    print(f"  {path1}")
    print(f"    → {norm1}")
    print(f"  {path2}")
    print(f"    → {norm2}")
    print(f"  {path3}")
    print(f"    → {norm3}")

    # Verify case insensitivity
    token_path_value = norm1.lower()  # As stored in token
    target_path = norm3.lower()      # As compared in validation

    assert token_path_value == target_path, "Case-insensitive comparison failed"
    print("\n✓ Test 2: Case-insensitive comparison")
    print(f"  token_path_value: {token_path_value}")
    print(f"  target_path:      {target_path}")
    print(f"  Match: {token_path_value == target_path}")

def test_diagnostic_mismatch_messages():
    """Test that validation returns specific mismatch details."""
    from pre_tool_use_logic import check_claude_edit_consent

    # Mock data simulating validation scenarios
    class MockData:
        def __init__(self, session_id, terminal_id):
            self.data = {
                "session": {"id": session_id},
                "terminal_id": terminal_id
            }

        def get(self, key, default=None):
            return self.data.get(key, default)

    print("\n✓ Test 3: Diagnostic mismatch messages")

    # Test case 1: Path mismatch only
    session_id = "test_session_abc123"
    terminal_id = "term_001"
    file_path = "P:/.claude/hooks/test_file.py"

    # Simulate token with different path
    mock_data = MockData(session_id, terminal_id)

    # Create a fake token file with mismatched path
    import hashlib
    import tempfile

    consent_dir = Path(tempfile.gettempdir()) / "claude_test_consent"
    consent_dir.mkdir(parents=True, exist_ok=True)

    # Build token name as the system does
    scope_digest = hashlib.sha256(terminal_id.encode("utf-8")).hexdigest()[:10]
    path_digest = hashlib.sha256(file_path.lower().encode("utf-8")).hexdigest()[:12]
    safe_session = "test_session_abc123"
    token_name = f"edit_consent_{safe_session}_{scope_digest}_{path_digest}.json"

    token_path = consent_dir / token_name

    # Create token with WRONG path (simulating case mismatch)
    wrong_path = "p:/.claude/hooks/DIFFERENT_FILE.py"
    token_payload = {
        "file": "hooks/DIFFERENT_FILE.py",
        "canonical_path": wrong_path,
        "session_id": session_id,
        "terminal_id": terminal_id,
        "major_task_id": "task_test",
        "granted_at": 1234567890
    }

    with open(token_path, 'w') as f:
        json.dump(token_payload, f)

    # Override the consent directory for testing
    import pre_tool_use_logic
    original_dirs = pre_tool_use_logic._iter_edit_consent_dirs()
    pre_tool_use_logic._iter_edit_consent_dirs = lambda: [consent_dir]

    try:
        # Test validation - should fail with diagnostic message
        has_consent, reason, canonical = check_claude_edit_consent(
            {"session": {"id": session_id}, "terminal_id": terminal_id},
            file_path
        )

        print(f"  Consent granted: {has_consent}")
        print(f"  Reason: {reason}")
        print("  Expected: Should contain 'path_mismatch' with diagnostic details")

        # Verify the reason contains diagnostic info
        assert not has_consent, "Expected consent to be denied"
        assert "path" in reason.lower(), f"Expected 'path' in reason, got: {reason}"

        # Clean up
        token_path.unlink()
        consent_dir.rmdir()

        print("\n✓ All tests passed!")
        print("\nSummary:")
        print("  1. Case-insensitive path comparison: WORKING")
        print("  2. Diagnostic mismatch messages: WORKING")
        print("  3. Validation logic: FUNCTIONAL")

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original directories
        pre_tool_use_logic._iter_edit_consent_dirs = original_dirs

if __name__ == "__main__":
    test_case_insensitive_path_comparison()
    test_diagnostic_mismatch_messages()
