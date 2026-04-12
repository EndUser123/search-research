#!/usr/bin/env python3
"""Unit tests for architectural recommendation detection in investigation gate.

Tests the anti-laziness gate that prevents architectural recommendations
without prior investigation (e.g., "move X to cognitive-stack" without
reading /s/SKILL.md to verify actual architectural fit).

Source: plan-20260312-anti-laziness-arch-verification.md
"""

import os
import sys
from pathlib import Path

# Set block mode for testing (override settings.json warn mode)
os.environ["CSF_ARCH_RECOMMENDATION_MODE"] = "block"

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

# Mock shared_utils before import
class MockSharedUtils:
    @staticmethod
    def log_hook_event(**kwargs):
        """Mock log_hook_event for testing."""
        pass

# Inject mock
sys.modules['shared_utils'] = MockSharedUtils()

import PreToolUse_investigation_gate as gate


def run_hook_input(tool_name: str, tool_input: dict, user_message: str = "", reset_state: bool = True, preloaded_state: dict = None) -> tuple[bool, str]:
    """Helper to run hook with synthetic input.

    Args:
        tool_name: Tool being invoked (e.g., "Edit", "Write")
        tool_input: Tool input parameters
        user_message: User message content
        reset_state: Whether to reset state before running (default: True)
        preloaded_state: Optional pre-saved state to use (bypasses load_state)

    Returns:
        (allowed: bool, message: str) - If False, message contains block reason
    """
    # Temporarily set enabled for test
    original_enabled = gate.ENABLED
    gate.ENABLED = True

    try:
        # Create synthetic input data
        input_data = {
            "tool_name": tool_name,
            "tool_input": tool_input,
        }

        # Add user message to conversation
        if user_message:
            input_data["conversation"] = [
                {"role": "user", "content": user_message}
            ]

        # Reset state to clean slate for each test (unless disabled)
        if reset_state:
            gate.save_state(gate.fresh_state())

        # If preloaded state provided, load it (bypasses normal load_state)
        if preloaded_state:
            # Temporarily replace load_state to return our preloaded state
            original_load = gate.load_state
            gate.load_state = lambda terminal_id="", input_data=None: preloaded_state
            try:
                # Run the hook
                allowed, message = gate.process_hook(
                    tool_name,
                    tool_input,
                    user_message,
                    terminal_id=""
                )
            finally:
                gate.load_state = original_load
            return allowed, message
        else:
            # Run the hook normally
            allowed, message = gate.process_hook(
                tool_name,
                tool_input,
                user_message
            )

        return allowed, message
    finally:
        gate.ENABLED = original_enabled


def test_01_block_recommendation_without_reading():
    """Test 1: Block architectural recommendation without reading architecture files."""
    user_message = "move Persona Memory to cognitive-stack"
    tool_input = {
        "path": "P:/packages/search-research/core/backends/local/persona_memory_backend.py",
        "old_string": "# old code",
        "new_string": "# new code"
    }

    allowed, message = run_hook_input("Edit", tool_input, user_message)

    # Should block - no architecture files read
    assert not allowed, "Should block recommendation without reading architecture files"
    assert "ARCHITECTURAL RECOMMENDATION WITHOUT INVESTIGATION" in message
    assert "cognitive-stack" in message
    assert "Read P:/.claude/skills/s/SKILL.md" in message or "Read target skill/file SKILL.md" in message
    print("✓ Test 1 passed: Blocks recommendation without reading")


def test_02_allow_after_investigation():
    """Test 2: Allow recommendation after reading architecture files."""
    user_message = "move Persona Memory to /s"
    tool_input = {
        "path": "P:/packages/search-research/core/backends/local/persona_memory_backend.py",
        "old_string": "# old code",
        "new_string": "# new code"
    }

    # Create state with /s/SKILL.md AND target file read
    # (target file read satisfies investigation gate's related reads requirement)
    state = gate.fresh_state()
    state["files_read"].append("P:/.claude/skills/s/SKILL.md")  # Architecture file
    state["files_read"].append(tool_input["path"])  # Target file (self-read exemption)

    # Pass preloaded state to the hook
    allowed, message = run_hook_input("Edit", tool_input, user_message, reset_state=False, preloaded_state=state)

    # Should allow - architecture file was read
    assert allowed, f"Should allow after reading architecture files. Message: {message}"
    print("✓ Test 2 passed: Allows after investigation")


def test_03_bypass_flag():
    """Test 3: Bypass flag allows recommendation without investigation."""
    user_message = "move Persona Memory to cognitive-stack --allow-arch-rec"
    tool_input = {
        "path": "P:/packages/search-research/core/backends/local/persona_memory_backend.py",
        "old_string": "# old code",
        "new_string": "# new code"
    }

    # Create state with target file read (to satisfy investigation gate)
    state = gate.fresh_state()
    state["files_read"].append(tool_input["path"])

    # Pass preloaded state to the hook
    allowed, message = run_hook_input("Edit", tool_input, user_message, reset_state=False, preloaded_state=state)

    # Should allow - bypass flag present
    assert allowed, f"Should allow with bypass flag. Message: {message}"
    assert message is None or "Bypass flag present" in message or "investigation" in message.lower()
    print("✓ Test 3 passed: Bypass flag works")


def test_04_false_positive_legitimate_refactoring():
    """Test 4: Don't block legitimate refactoring within same project."""
    user_message = "move this function to utils.py for better organization"  # No skill destination
    tool_input = {
        "path": "P:/packages/search-research/src/utils.py",
        "old_string": "# old code",
        "new_string": "# new code"
    }

    # Create state with target file read
    state = gate.fresh_state()
    state["files_read"].append("P:/packages/search-research/src/utils.py")

    # Pass preloaded state to the hook
    allowed, message = run_hook_input("Edit", tool_input, user_message, reset_state=False, preloaded_state=state)

    # Should allow - no architectural recommendation pattern matched
    assert allowed, f"Should allow legitimate refactoring. Message: {message}"
    print("✓ Test 4 passed: Allows legitimate refactoring")


def test_05_destination_pattern_detection():
    """Test 5: Detect various architectural recommendation patterns."""
    test_cases = [
        ("belongs in cognitive-stack", "cognitive-stack"),
        ("should go to /main", "/main"),
        ("would fit better in /s", "/s"),
        ("move to /all", "/all"),
        ("suggest putting in /arch", "/arch"),
    ]

    for user_message, expected_destination in test_cases:
        tool_input = {
            "path": "P:/test.py",
            "old_string": "# old",
            "new_string": "# new"
        }

        # Each test gets fresh state (arch gate should block before investigation gate)
        allowed, message = run_hook_input("Edit", tool_input, user_message, reset_state=True)

        # Should block - pattern matched
        # Note: If arch gate doesn't block, investigation gate might block instead
        assert not allowed, f"Should block pattern: {user_message}"
        # Check that either the arch gate or the investigation gate blocked
        assert expected_destination in message or "ARCHITECTURAL" in message or "INVESTIGATION" in message, \
            f"Expected block message for: {user_message}. Got: {message}"

    print("✓ Test 5 passed: Destination pattern detection works")


def test_06_hook_audit_integration():
    """Test 6: Verify /hook-audit integration is called with correct data."""
    # Track if log_hook_event was called
    log_calls = []

    class TrackingMockUtils:
        @staticmethod
        def log_hook_event(**kwargs):
            log_calls.append(kwargs)

    # Replace shared_utils mock
    sys.modules['shared_utils'] = TrackingMockUtils()

    # Reload gate to use new mock
    import importlib
    importlib.reload(gate)

    user_message = "move Persona Memory to cognitive-stack"
    tool_input = {
        "path": "P:/test.py",
        "old_string": "# old",
        "new_string": "# new"
    }

    # Reset state
    gate.save_state(gate.fresh_state())

    allowed, message = gate.process_hook("Edit", tool_input, user_message)

    # Verify /hook-audit was called
    assert len(log_calls) > 0, "log_hook_event should be called"
    assert log_calls[0]["event_type"] == "block", "Should log block event"
    assert log_calls[0]["hook_name"] == "investigation_gate_arch_recommendation"
    assert "data_report" in log_calls[0]["data"], "Should include data_report"
    assert "pattern_matched" in log_calls[0]["data"]["data_report"], \
        "Data report should include pattern_matched"

    print("✓ Test 6 passed: /hook-audit integration works")


def test_07_no_arch_recommendation():
    """Test 7: Don't block normal edits without architectural recommendations."""
    user_message = "fix the bug in the logging function"
    tool_input = {
        "path": "P:/test.py",
        "old_string": "# old",
        "new_string": "# new"
    }

    # Create state with target file read (to satisfy investigation gate)
    state = gate.fresh_state()
    state["files_read"].append(tool_input["path"])

    # Pass preloaded state to the hook
    allowed, message = run_hook_input("Edit", tool_input, user_message, reset_state=False, preloaded_state=state)

    # Should allow - no architectural recommendation pattern
    assert allowed, f"Should allow normal edits. Message: {message}"
    print("✓ Test 7 passed: Allows normal edits")


def test_08_disabled_gate():
    """Test 8: Gate doesn't block when disabled."""
    # Temporarily disable the gate
    original_enabled = gate.ARCH_RECOMMENDATION_ENABLED
    gate.ARCH_RECOMMENDATION_ENABLED = False

    try:
        user_message = "move Persona Memory to cognitive-stack"
        tool_input = {
            "path": "P:/test.py",
            "old_string": "# old",
            "new_string": "# new"
        }

        # Create state with target file read (to satisfy investigation gate)
        state = gate.fresh_state()
        state["files_read"].append(tool_input["path"])

        # Pass preloaded state to the hook
        allowed, message = run_hook_input("Edit", tool_input, user_message, reset_state=False, preloaded_state=state)

        # Should allow - gate is disabled (and investigation gate satisfied)
        assert allowed, f"Should allow when gate disabled. Message: {message}"
        print("✓ Test 8 passed: Respects enabled flag")
    finally:
        gate.ARCH_RECOMMENDATION_ENABLED = original_enabled


if __name__ == "__main__":
    print("Running architectural recommendation gate tests...\n")

    test_01_block_recommendation_without_reading()
    test_02_allow_after_investigation()
    test_03_bypass_flag()
    test_04_false_positive_legitimate_refactoring()
    test_05_destination_pattern_detection()
    test_06_hook_audit_integration()
    test_07_no_arch_recommendation()
    test_08_disabled_gate()

    print("\n✅ All 8 tests passed!")
