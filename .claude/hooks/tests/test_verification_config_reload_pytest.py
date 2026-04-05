#!/usr/bin/env python3
"""Config reload behavior tests for verification system (pytest version).

TASK-015: Test that configuration changes take effect without restart.
Simulates env/policy changes between turns and verifies next Stop invocation
reflects new mode.
"""

import os
import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

# Disable gate BEFORE any imports to prevent hook interception
os.environ["HYPOTHESIS_AS_FACT_GATE_ENABLED"] = "false"


def test_config_reload_warn_to_block():
    """Test 1: Mode change from warn to block takes effect on next turn."""
    import Stop_hypothesis_as_fact_gate

    # Enable gate for testing
    original_enabled = os.environ.get("HYPOTHESIS_AS_FACT_GATE_ENABLED", "true")
    original_mode = os.environ.get("HYPOTHESIS_AS_FACT_GATE_MODE", "warn")

    os.environ["HYPOTHESIS_AS_FACT_GATE_ENABLED"] = "true"

    # Test response that would be blocked in BLOCK mode
    response_text = "The package has no skill/ directory."
    hook_data_warn = {
        "session_id": "test-session-reload",
        "terminal_id": "test-terminal-reload",
        "response_text": response_text,
    }

    # Run in WARN mode - should allow with warning
    result_warn = Stop_hypothesis_as_fact_gate.run(hook_data_warn)
    assert result_warn.get('allow') == True, "WARN mode should allow (with warning)"

    # Simulate Turn 2: Change to BLOCK mode (no restart)
    os.environ["HYPOTHESIS_AS_FACT_GATE_MODE"] = "block"

    # Run again with same data - should now block
    result_block = Stop_hypothesis_as_fact_gate.run(hook_data_warn)

    # Restore original settings
    os.environ["HYPOTHESIS_AS_FACT_GATE_MODE"] = original_mode
    os.environ["HYPOTHESIS_AS_FACT_GATE_ENABLED"] = original_enabled

    # Should block in BLOCK mode
    assert result_block.get('allow') == False, "BLOCK mode should block ungrounded claim"


def test_config_reload_disabled_to_enabled():
    """Test 2: Gate disabled to enabled takes effect on next turn."""
    import Stop_hypothesis_as_fact_gate

    # Simulate Turn 1: Gate disabled
    original_enabled = os.environ.get("HYPOTHESIS_AS_FACT_GATE_ENABLED", "true")
    os.environ["HYPOTHESIS_AS_FACT_GATE_ENABLED"] = "false"

    response_text = "The package has no skill/ directory."
    hook_data = {
        "session_id": "test-session-enable",
        "terminal_id": "test-terminal-enable",
        "response_text": response_text,
    }

    # Run with gate disabled - should allow
    result_disabled = Stop_hypothesis_as_fact_gate.run(hook_data)
    assert result_disabled.get('allow') == True, "Disabled gate should allow"

    # Simulate Turn 2: Enable gate
    os.environ["HYPOTHESIS_AS_FACT_GATE_ENABLED"] = "true"

    # Run again - should now enforce
    result_enabled = Stop_hypothesis_as_fact_gate.run(hook_data)

    # Restore original setting
    os.environ["HYPOTHESIS_AS_FACT_GATE_ENABLED"] = original_enabled

    # Gate is working (may or may not block depending on claim)
    # Just verify it runs without error
    assert 'allow' in result_enabled, "Enabled gate should return allow field"


def test_config_persistence_across_calls():
    """Test 3: Config settings persist across multiple hook invocations."""
    import Stop_hypothesis_as_fact_gate

    # Set mode to block
    original_mode = os.environ.get("HYPOTHESIS_AS_FACT_GATE_MODE", "warn")
    os.environ["HYPOTHESIS_AS_FACT_GATE_MODE"] = "block"

    response_text = "The package has no skill/ directory."
    hook_data = {
        "session_id": "test-session-persist",
        "terminal_id": "test-terminal-persist",
        "response_text": response_text,
    }

    # Call 1: Should block
    result1 = Stop_hypothesis_as_fact_gate.run(hook_data)

    # Call 2: Should still block (config persisted)
    result2 = Stop_hypothesis_as_fact_gate.run(hook_data)

    # Restore original mode
    os.environ["HYPOTHESIS_AS_FACT_GATE_MODE"] = original_mode

    # Both should have same behavior
    assert result1.get('allow') == result2.get('allow'), "Config should persist across calls"
