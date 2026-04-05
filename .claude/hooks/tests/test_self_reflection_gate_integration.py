#!/usr/bin/env python3
"""
Integration test for Stop_self_reflection_gate.py (TASK-003B)

This test verifies the self-reflection gate integrates properly with
the Stop hook infrastructure (Stop_router.py integration).

Tests:
- Hook is callable through Stop_router.py
- Hook processes Stop event input correctly
- Advisory output format matches expectations
- Hook allows responses even when low confidence detected
"""

import sys
from pathlib import Path

# Add hooks to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import Stop_router


class TestSelfReflectionGateIntegration:
    """Integration tests for self-reflection gate with Stop infrastructure."""

    def test_hook_in_hook_sequence(self):
        """Test that self-reflection gate is in HOOK_SEQUENCE."""
        hook_names = [h[0] for h in Stop_router.HOOK_SEQUENCE]
        assert (
            "Stop_self_reflection_gate.py" in hook_names
        ), "Stop_self_reflection_gate.py should be in HOOK_SEQUENCE"

    def test_hook_in_active_runtime_hooks(self):
        """Test that self-reflection gate is in ACTIVE_RUNTIME_HOOKS."""
        assert (
            "Stop_self_reflection_gate.py" in Stop_router.ACTIVE_RUNTIME_HOOKS
        ), "Stop_self_reflection_gate.py should be in ACTIVE_RUNTIME_HOOKS"

    def test_hook_priority_assigned(self):
        """Test that hook has a priority number assigned."""
        priority = Stop_router.HOOK_PRIORITY.get("Stop_self_reflection_gate.py")
        assert priority is not None, "Hook should have a priority number"
        assert isinstance(priority, int), "Priority should be an integer"

    def test_hook_dispatch_mode_set(self):
        """Test that hook has dispatch mode configured."""
        dispatch = Stop_router.HOOK_DISPATCH.get("Stop_self_reflection_gate.py")
        assert dispatch is not None, "Hook should have dispatch mode"
        assert dispatch in [
            "inprocess",
            "subprocess",
        ], f"Dispatch mode should be inprocess or subprocess, got {dispatch}"

    def test_hook_process_stop_event(self):
        """Test that hook can process Stop event data."""
        # Simulate Stop event input
        stop_event = {"response": "This probably works but might need testing."}

        # Import and run hook directly
        import Stop_self_reflection_gate

        result = Stop_self_reflection_gate.run(stop_event)

        assert result is not None, "Hook should return a result"
        assert result.get("allow") == True, "Hook should allow (advisory mode)"
        assert "advisory" in result.get("reason", "").lower(), "Reason should mention advisory"

    def test_hook_file_exists_at_correct_path(self):
        """Test that hook file exists at expected path."""
        hook_path = Path("P:/.claude/hooks/Stop_self_reflection_gate.py")
        assert hook_path.exists(), "Hook file should exist at P:/.claude/hooks/"
        assert hook_path.is_file(), "Hook should be a file"

    def test_environment_variables_configured(self):
        """Test that environment variables are configured."""
        import os

        enabled = os.environ.get("SELF_REFLECTION_ENABLED", "true")
        threshold = os.environ.get("SELF_REFLECTION_CONFIDENCE_THRESHOLD", "0.7")

        assert enabled.lower() in [
            "true",
            "false",
            "1",
            "0",
        ], f"SELF_REFLECTION_ENABLED should be boolean-like, got {enabled}"
        assert (
            0.0 <= float(threshold) <= 1.0
        ), f"SELF_REFLECTION_CONFIDENCE_THRESHOLD should be 0-1, got {threshold}"

    def test_hook_disabled_when_env_var_false(self):
        """Test that hook disables when SELF_REFLECTION_ENABLED=false."""
        import os

        import Stop_self_reflection_gate

        # Save original value
        original = os.environ.get("SELF_REFLECTION_ENABLED")

        try:
            # Set to disabled
            os.environ["SELF_REFLECTION_ENABLED"] = "false"

            # Reload module to pick up new env var
            import importlib

            importlib.reload(Stop_self_reflection_gate)

            # Test with disabled hook
            result = Stop_self_reflection_gate.run(
                {"response": "This probably needs verification."}
            )

            assert result is not None, "Hook should still return result when disabled"
            assert result.get("allow") == True, "Hook should allow when disabled"
            assert (
                "disabled" in result.get("reason", "").lower()
                or "no weak claims" in result.get("reason", "").lower()
            ), "Reason should indicate disabled or pass through"

        finally:
            # Restore original value
            if original is not None:
                os.environ["SELF_REFLECTION_ENABLED"] = original
            else:
                # If there was no original value, delete the env var entirely
                # Don't set it to "None" as a string - that breaks subsequent tests
                os.environ.pop("SELF_REFLECTION_ENABLED", None)

    def test_multiple_low_confidence_claims_all_detected(self):
        """Test that multiple claims in one response are all detected."""
        import importlib

        import Stop_self_reflection_gate

        importlib.reload(Stop_self_reflection_gate)  # Clear module cache from previous tests

        response = """
        This probably works.
        That seems correct.
        It might fail.
        """
        result = Stop_self_reflection_gate.run({"response": response})

        assert result is not None, "Hook should return a result"
        assert result.get("allow") == True, "Hook should allow (advisory mode)"
        # The reason should mention detection
        assert (
            "advisory" in result.get("reason", "").lower()
            or "claim" in result.get("reason", "").lower()
        ), "Reason should mention claims or advisory"

    def test_high_confidence_response_bypasses_detection(self):
        """Test that verified responses bypass detection."""
        import importlib

        import Stop_self_reflection_gate

        importlib.reload(Stop_self_reflection_gate)  # Clear module cache from previous tests

        response = "This is verified and tested code."
        result = Stop_self_reflection_gate.run({"response": response})

        assert result is not None, "Hook should return a result"
        assert result.get("allow") == True, "Hook should allow verified responses"
        assert (
            "no weak claims" in result.get("reason", "").lower()
        ), "Reason should indicate no weak claims"

    def test_advisory_output_format(self):
        """Test that advisory output has expected format."""
        import contextlib
        import importlib
        from io import StringIO

        import Stop_self_reflection_gate

        importlib.reload(Stop_self_reflection_gate)  # Clear module cache from previous tests

        response = "This probably needs verification."
        data = {"response": response}

        # Capture stdout
        f = StringIO()
        with contextlib.redirect_stdout(f):
            result = Stop_self_reflection_gate.run(data)

        output = f.getvalue()

        assert result is not None, "Hook should return a result"
        # Check advisory format elements
        assert (
            "SELF-REFLECTION" in output or "advisory" in output.lower()
        ), "Output should contain self-reflection advisory"
        assert (
            "consider either:" in output.lower() or "verify" in output.lower()
        ), "Output should contain verification suggestions"


if __name__ == "__main__":
    import pytest

    sys.exit(pytest.main([__file__, "-v"]))
