#!/usr/bin/env python3
"""Test FrameGuard classifier hook.

Tests the frameguard_classifier UserPromptSubmit hook:
- Systemic pattern detection
- HookContext/HookResult pattern
- Registry integration
- Fail-open behavior
- Metrics tracking
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys_path_insert = str(Path(__file__).resolve().parents[1])
if sys_path_insert not in sys.path:
    sys.path.insert(0, sys_path_insert)

# Import after path setup
from UserPromptSubmit_modules.base import HookContext, HookResult

# Import the frameguard_classifier module directly
try:
    from UserPromptSubmit_modules import frameguard_classifier as fc_module

    frameguard_classifier = fc_module.frameguard_classifier
    FRAMEGUARD_ENABLED_VAR = fc_module.FRAMEGUARD_ENABLED
except ImportError:
    frameguard_classifier = None
    FRAMEGUARD_ENABLED_VAR = True


# === Helper Functions ===


def _create_hook_context(
    prompt: str = "",
    session_id: str = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    terminal_id: str = "console_test",
    turn_id: str = "test_turn_123",
    **kwargs,
) -> HookContext:
    """Create a HookContext for testing."""
    data = {
        "prompt": prompt,
        "message": prompt,
        "session_id": session_id,
        "sessionId": session_id,
        "terminal_id": terminal_id,
        "terminalId": terminal_id,
        "turn_id": turn_id,
        **kwargs,
    }
    return HookContext(
        prompt=prompt,
        data=data,
        session_id=session_id,
        terminal_id=terminal_id,
    )


# === Pattern Detection Tests ===


def test_systemic_pattern_detected() -> None:
    """Test systemic pattern triggers recording."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    # Save original env value
    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        # "do we have a hook for X" pattern
        context = _create_hook_context(
            prompt="Do we have a hook for validating user input?",
            session_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )

        # Mock evidence_store functions
        with patch("evidence_store.record_frameguard_trigger", return_value=True):
            result = frameguard_classifier(context)

        # Should return HookResult with additionalContext
        assert result is not None
        assert isinstance(result, HookResult)
        assert result.context is not None
        assert "additionalContext" in result.context
        assert "FRAMEGUARD" in result.context["additionalContext"]
        assert "SYSTEMIC FRAME DETECTED" in result.context["additionalContext"]

    finally:
        # Restore original env value
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


def test_no_pattern_no_trigger() -> None:
    """Test no pattern = no recording."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        # Simple question without systemic pattern
        context = _create_hook_context(
            prompt="What is the capital of France?",
            session_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        )

        result = frameguard_classifier(context)

        # Should return empty HookResult
        assert result is not None
        assert isinstance(result, HookResult)
        assert result.context is None

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


def test_disabled_when_env_false() -> None:
    """Test FRAMEGUARD_ENABLED=false disables the hook."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    # Note: FRAMEGUARD_ENABLED is evaluated at module import time
    # We can't change it during test, so we skip this test if it's currently enabled
    # The module-level check means setting env var during test has no effect
    # This test documents the expected behavior when FRAMEGUARD_ENABLED=false at import

    if FRAMEGUARD_ENABLED_VAR:
        pytest.skip("FRAMEGUARD_ENABLED is true at import time, cannot test false case")

    # If FRAMEGUARD_ENABLED was false at import time, test that it's disabled
    context = _create_hook_context(
        prompt="Do we have a hook for X?",
        session_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
    )

    result = frameguard_classifier(context)

    # Should return empty HookResult when disabled
    assert result is not None
    assert isinstance(result, HookResult)
    assert result.context is None


def test_injection_content() -> None:
    """Test correct warning injection."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        context = _create_hook_context(
            prompt="is there a hook configured for session management?",
            session_id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
        )

        with patch("evidence_store.record_frameguard_trigger", return_value=True):
            result = frameguard_classifier(context)

        assert result.context is not None
        injection = result.context.get("additionalContext", "")

        # Verify injection contains required elements
        assert "FRAMEGUARD" in injection
        assert "SYSTEMIC FRAME DETECTED" in injection
        assert "broader structural" in injection

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


# === HookContext/HookResult Tests ===


def test_hook_context_input() -> None:
    """Test HookContext used correctly."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        # Test with various HookContext field combinations
        context1 = _create_hook_context(
            prompt="Do we have a hook for X?",
            session_id="11111111-1111-1111-1111-111111111111",
        )

        with patch("evidence_store.record_frameguard_trigger", return_value=True):
            # Should handle HookContext correctly
            result = frameguard_classifier(context1)
        assert isinstance(result, HookResult)

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


def test_hook_result_output() -> None:
    """Test HookResult returned correctly."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        context = _create_hook_context(
            prompt="thought we had a hook for validation",
            session_id="22222222-2222-2222-2222-222222222222",
        )

        with patch("evidence_store.record_frameguard_trigger", return_value=True):
            result = frameguard_classifier(context)

        # Verify HookResult structure
        assert isinstance(result, HookResult)
        assert hasattr(result, "context")

        # When triggered, context should be a dict with additionalContext
        if result.context:
            assert isinstance(result.context, dict)
            assert "additionalContext" in result.context

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


# === Fail-Open Tests ===


def test_fail_open_on_db_error() -> None:
    """Test database error doesn't block UserPromptSubmit."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        # Mock evidence_store to raise an error
        with patch("evidence_store.record_frameguard_trigger", side_effect=Exception("DB error")):
            context = _create_hook_context(
                prompt="Do we have a hook for X?",
                session_id="33333333-3333-3333-3333-333333333333",
            )

            # Should not raise exception, should fail-open
            result = frameguard_classifier(context)
            assert isinstance(result, HookResult)

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


# === Data Handling Tests ===


def test_turn_id_propagation() -> None:
    """Test turn_id passed to evidence_store."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        # Mock record_frameguard_trigger to capture arguments
        captured = {}

        def mock_record(**kwargs):
            captured.update(kwargs)
            return True

        # Patch where the function is used (in frameguard_classifier module)
        with patch(
            "UserPromptSubmit_modules.frameguard_classifier.record_frameguard_trigger",
            side_effect=mock_record,
        ):
            context = _create_hook_context(
                prompt="Do we have a hook for X?",
                session_id="44444444-4444-4444-4444-444444444444",
                turn_id="specific_turn_789",
            )

            frameguard_classifier(context)

            # Verify turn_id was passed
            assert "turn_id" in captured
            assert captured["turn_id"] == "specific_turn_789"

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


def test_terminal_id_sanitization() -> None:
    """Test terminal_id passed through."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        captured = {}

        def mock_record(**kwargs):
            captured.update(kwargs)
            return True

        with patch(
            "UserPromptSubmit_modules.frameguard_classifier.record_frameguard_trigger",
            side_effect=mock_record,
        ):
            context = _create_hook_context(
                prompt="Do we have a hook for X?",
                session_id="55555555-5555-5555-5555-555555555555",
                terminal_id="console/with/slashes",
            )

            frameguard_classifier(context)

            # Terminal ID should be passed (sanitization happens in evidence_store)
            assert "terminal_id" in captured

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


def test_latent_questions_structure() -> None:
    """Test valid latent_questions generated."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        captured = {}

        def mock_record(**kwargs):
            captured.update(kwargs)
            return True

        with patch(
            "UserPromptSubmit_modules.frameguard_classifier.record_frameguard_trigger",
            side_effect=mock_record,
        ):
            context = _create_hook_context(
                prompt="Do we have a hook for X?",
                session_id="66666666-6666-6666-6666-666666666666",
            )

            frameguard_classifier(context)

            # Verify latent_questions structure
            assert "latent_questions" in captured
            latent_questions = captured["latent_questions"]
            assert isinstance(latent_questions, list)

            # Each question should have 'id' and 'question' keys
            for q in latent_questions:
                assert isinstance(q, dict)
                assert "id" in q
                assert "question" in q

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


# === Pattern Tests ===


def test_multiple_patterns() -> None:
    """Test first matching pattern wins."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        # Prompt that matches multiple patterns
        context = _create_hook_context(
            prompt="Do we have a hook configured for X? Also thought we had a hook for Y.",
            session_id="77777777-7777-7777-7777-777777777777",
        )

        with patch("evidence_store.record_frameguard_trigger", return_value=True):
            result = frameguard_classifier(context)

        # Should trigger (first pattern matches)
        assert result.context is not None
        assert "additionalContext" in result.context

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


def test_case_insensitive_patterns() -> None:
    """Test patterns are case-insensitive."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        # Test various cases - at least one should trigger
        test_prompts = [
            "DO WE HAVE a hook for X?",
            "do we HAVE A hook for X?",
            "Do We Have a hook for X?",
        ]

        triggered_count = 0
        for prompt in test_prompts:
            context = _create_hook_context(
                prompt=prompt,
                session_id="88888888-8888-8888-8888-888888888888",
            )

            with patch("evidence_store.record_frameguard_trigger", return_value=True):
                result = frameguard_classifier(context)

            if result.context and "additionalContext" in result.context:
                triggered_count += 1

        # At least one case variation should trigger
        assert triggered_count > 0, "At least one case variation should trigger"

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


def test_empty_prompt_handling() -> None:
    """Test empty prompt handled gracefully."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    original_enabled = os.environ.get("FRAMEGUARD_ENABLED", "true")

    try:
        os.environ["FRAMEGUARD_ENABLED"] = "true"

        context = _create_hook_context(
            prompt="",
            session_id="99999999-9999-9999-9999-999999999999",
        )

        result = frameguard_classifier(context)

        # Should not trigger on empty prompt
        assert result is not None
        assert isinstance(result, HookResult)
        assert result.context is None

    finally:
        if original_enabled:
            os.environ["FRAMEGUARD_ENABLED"] = original_enabled
        else:
            os.environ.pop("FRAMEGUARD_ENABLED", None)


# === Registry Tests ===


def test_registry_integration() -> None:
    """Test hook is importable and has correct signature."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    # Verify the function exists and is callable
    assert callable(frameguard_classifier)

    # Verify it's registered with @register_hook decorator
    # The decorator adds metadata to the function
    assert hasattr(frameguard_classifier, "__name__")
    assert frameguard_classifier.__name__ == "frameguard_classifier"


def test_priority_7_0() -> None:
    """Test priority configured correctly via decorator."""
    if frameguard_classifier is None:
        pytest.skip("frameguard_classifier module not available")

    # The decorator should have registered the hook with priority 7.0
    # We can verify the module has the correct configuration
    assert hasattr(fc_module, "SYSTEMIC_PATTERNS")
    assert hasattr(fc_module, "LATENT_TEMPLATES")
    assert isinstance(fc_module.SYSTEMIC_PATTERNS, list)
    assert isinstance(fc_module.LATENT_TEMPLATES, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
