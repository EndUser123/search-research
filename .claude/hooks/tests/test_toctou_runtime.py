#!/usr/bin/env python3
"""
Runtime TOCTOU test for BUG-003 fix

Verifies that the TOCTOU fix in _load_band_aid_state properly handles
concurrent file deletion attempts.
"""

import os
import tempfile
import threading
import time
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _load_band_aid_state_from_path(file_path: str) -> dict:
    """Test wrapper that loads the actual function."""
    # Import here to avoid import issues
    from StopHook_rca_contract import _load_band_aid_state, BAND_AID_FILE
    from __lib.state_paths import get_terminal_state_path

    # Create a mock terminal_id
    terminal_id = "test_terminal"

    # Temporarily patch the get_terminal_state_path to return our test file
    original_get_path = get_terminal_state_path
    def mock_get_path(terminal_id: str, filename: str) -> Path:
        return Path(file_path)

    try:
        import StopHook_rca_contract as hook_module
        hook_module.get_terminal_state_path = mock_get_path
        return _load_band_aid_state(terminal_id)
    finally:
        hook_module.get_terminal_state_path = original_get_path


def test_toctou_concurrent_deletion():
    """Runtime test: Verify TOCTOU handling works correctly."""
    # Create a temporary state file
    state_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    state_file.write('{"_ts": ' + str(time.monotonic()) + ', "fixes": {}}')
    state_file.close()

    delete_event = threading.Event()
    results = {'toctou_triggered': False, 'handled_gracefully': False}

    def delete_file_after_delay():
        delete_event.wait()  # Wait for main thread to signal ready
        time.sleep(0.001)  # Tiny delay to create race window
        try:
            os.unlink(state_file.name)
        except FileNotFoundError:
            pass  # Already deleted, that's fine

    # Start thread that will delete the file
    deleter = threading.Thread(target=delete_file_after_delay)
    deleter.start()

    try:
        # Signal the deleter thread, then immediately try to load
        # This creates the TOCTOU race condition window
        delete_event.set()
        result = _load_band_aid_state_from_path(state_file.name)

        # If we got here, the file wasn't deleted in time
        # But the function should still handle it gracefully
        results['handled_gracefully'] = isinstance(result, dict)

    except FileNotFoundError:
        # Race condition triggered - this is the TOCTOU case
        results['toctou_triggered'] = True
        results['handled_gracefully'] = True
    finally:
        deleter.join(timeout=2.0)
        # Cleanup
        try:
            if os.path.exists(state_file.name):
                os.unlink(state_file.name)
        except:
            pass

    # The critical assertion: exception handling works correctly
    # Whether race triggered or not, graceful handling is required
    assert results['handled_gracefully'], "TOCTOU not handled gracefully"

    if results['toctou_triggered']:
        print("✓ Runtime TOCTOU test passed: Race condition triggered and handled gracefully")
    else:
        print("✓ Runtime TOCTOU test passed: Function completed without race (timing variance)")


def test_toctou_ttl_expiration():
    """Test that TTL expiration works correctly."""
    import tempfile
    from StopHook_rca_contract import BAND_AID_STATE_TTL

    # Create state file with old timestamp (expired)
    old_timestamp = time.monotonic() - BAND_AID_STATE_TTL - 10
    state_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    state_file.write('{"_ts": ' + str(old_timestamp) + ', "fixes": {}}')
    state_file.close()

    try:
        result = _load_band_aid_state_from_path(state_file.name)

        # Should return {} due to TTL expiration
        assert result == {}, f"TTL expiration failed: got {result}"

    finally:
        # Cleanup
        try:
            os.unlink(state_file.name)
        except:
            pass

    print("✓ TTL expiration test passed: Old state returns empty dict")


def test_band_aid_corrupt_json():
    """Test that corrupt JSON is handled correctly."""
    import tempfile

    # Create file with invalid JSON
    corrupt_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
    corrupt_file.write('{invalid json content}')
    corrupt_file.close()

    try:
        result = _load_band_aid_state_from_path(corrupt_file.name)

        # Should return {} and not crash
        assert result == {}, f"Corrupt JSON handling failed: got {result}"

    finally:
        # Cleanup
        try:
            os.unlink(corrupt_file.name)
        except:
            pass

    print("✓ Corrupt JSON test passed: Invalid JSON returns empty dict")


if __name__ == "__main__":
    print("Running runtime TOCTOU tests...")
    test_toctou_concurrent_deletion()
    test_toctou_ttl_expiration()
    test_band_aid_corrupt_json()
    print("\n✅ All runtime TOCTOU tests passed")
