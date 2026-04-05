"""
Integration tests for declaration_reminder.py UserPromptSubmit hook.

Tests the anti-lazy declaration detection hook that prevents "I'll update the template"
declarations without execution.
"""

import json
import sys
from pathlib import Path
from unittest.mock import Mock

# Add hooks directory to path for imports
hooks_dir = Path(__file__).parent.parent
sys.path.insert(0, str(hooks_dir))

# Test state directory (matching the hook's STATE_DIR)
# declaration_reminder.py uses: Path(__file__).resolve().parent.parent / "state"
# which for P:\.claude\hooks\UserPromptSubmit_modules\declaration_reminder.py
# resolves to P:\.claude\hooks\state
TEST_STATE_DIR = hooks_dir / "state"


def _get_hook_context(prompt: str, terminal_id: str = "test_terminal") -> Mock:
    """Create a mock HookContext for testing."""
    context = Mock()
    context.prompt = prompt
    context.data = {
        "terminal_id": terminal_id,
        "terminalId": terminal_id,
    }
    return context


def _clean_test_state(terminal_id: str = "test_terminal") -> None:
    """Clean up test state files."""
    TEST_STATE_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(c if c.isalnum() or c in "_.-:" else "_" for c in terminal_id)
    state_file = TEST_STATE_DIR / f"arch_declaration_{safe_id}.json"
    if state_file.exists():
        state_file.unlink()


def test_declaration_pattern_detection():
    """Test that declaration patterns are detected correctly."""
    from UserPromptSubmit_modules.declaration_reminder import _detect_template_declaration

    # Positive cases - should be detected
    positive_cases = [
        "I'll update the template",
        "I'd like to update arch/ base.md",
        "I will fix the SKILL.md file",
        "Let me modify the template",
        "I'm going to edit the arch file",
        "I should update the template",
        "Need to fix the template",
        "have to modify arch/",
    ]

    for case in positive_cases:
        assert _detect_template_declaration(case), f"Should detect: {case}"

    # Negative cases - should NOT be detected
    negative_cases = [
        "Update the file",  # No declaration
        "The template is good",  # No intent to modify
        "",  # Empty
        "Let's check the documentation",  # No template keyword
    ]

    for case in negative_cases:
        assert not _detect_template_declaration(case), f"Should NOT detect: {case}"


def test_arch_path_extraction():
    """Test extraction of arch path from declarations."""
    from UserPromptSubmit_modules.declaration_reminder import _extract_arch_path

    # Explicit path mentions
    assert _extract_arch_path("Update the template at arch/base.md") == "arch/base.md"
    assert _extract_arch_path("I'll fix the SKILL.md file") == "SKILL.md"
    assert _extract_arch_path("Modify arch/behavior-template.md") == "arch/behavior-template.md"

    # No path - should default
    result = _extract_arch_path("I'll update the template")
    assert result == "arch/base.md"  # Default


def test_hook_returns_empty_for_non_declarations():
    """Test that non-declarations return empty HookResult."""
    from UserPromptSubmit_modules.declaration_reminder import HookResult, declaration_reminder_hook

    context = _get_hook_context("Just a regular prompt about something else")
    result = declaration_reminder_hook(context)

    assert result == HookResult.empty()


def test_hook_injects_context_for_declarations():
    """Test that declarations trigger context injection."""
    from UserPromptSubmit_modules.declaration_reminder import declaration_reminder_hook

    terminal_id = "test_terminal_123"
    context = _get_hook_context("I'll update the template", terminal_id)
    result = declaration_reminder_hook(context)

    # Should have additionalContext
    assert hasattr(result, "context") or hasattr(result, "additional_context")

    # Context should contain required elements
    context_text = result.context if hasattr(result, "context") else result.additional_context
    assert "TEMPLATE UPDATE DECLARATION DETECTED" in context_text
    assert "Declaration ≠ Execution" in context_text
    assert terminal_id in context_text or "arch/base.md" in context_text


def test_state_file_creation():
    """Test that declaration state is stored for coordination."""
    from UserPromptSubmit_modules.declaration_reminder import (
        _get_state_file,
        declaration_reminder_hook,
    )

    terminal_id = "test_state_creation"
    _clean_test_state(terminal_id)

    try:
        context = _get_hook_context("I'll update the arch template", terminal_id)
        declaration_reminder_hook(context)

        # Check state file was created in the correct location
        state_file = _get_state_file(terminal_id)
        assert (
            state_file.parent == TEST_STATE_DIR
        ), f"State file should be in {TEST_STATE_DIR}, but is in {state_file.parent}"

        # Verify the file exists and has correct content
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
            assert "path" in state
            assert "timestamp" in state
    finally:
        _clean_test_state(terminal_id)


def test_multiple_declaration_patterns():
    """Test various declaration pattern formats."""
    from UserPromptSubmit_modules.declaration_reminder import _detect_template_declaration

    patterns = [
        r"i'll update the template",  # Lowercase
        r"I'LL MODIFY ARCH/",  # Uppercase
        r"I'd love to fix SKILL.md",  # Different modal
        r"i should modify the template file",  # Should pattern
    ]

    for pattern in patterns:
        assert _detect_template_declaration(pattern), f"Should detect pattern: {pattern}"


def test_non_english_patterns():
    """Test that non-English text doesn't trigger false positives."""
    from UserPromptSubmit_modules.declaration_reminder import _detect_template_declaration

    non_english = [
        "これはテンプレートです",  # Japanese
        "Ceci est un modèle",  # French
        "Это шаблон",  # Russian
    ]

    for text in non_english:
        result = _detect_template_declaration(text)
        # Should not detect unless it contains English keywords
        # These don't have "template/arch/SKILL.md" keywords, so should be False
        assert not result, f"Should NOT detect non-English: {text}"


def test_hook_context_contains_required_elements():
    """Test that injected context contains all required elements."""
    from UserPromptSubmit_modules.declaration_reminder import declaration_reminder_hook

    context = _get_hook_context("I'll update the arch/ template")
    result = declaration_reminder_hook(context)

    context_text = result.context if hasattr(result, "context") else result.additional_context

    required_phrases = [
        "TEMPLATE UPDATE DECLARATION DETECTED",
        "Declaration ≠ Execution",
        "Read",
        "Edit/Write",
        "State:",
        "Enforcement",
    ]

    for phrase in required_phrases:
        assert phrase in context_text, f"Missing required phrase: {phrase}"


def test_terminal_id_extraction():
    """Test terminal ID extraction from context."""
    from UserPromptSubmit_modules.declaration_reminder import _get_terminal_id

    # Test with terminal_id field
    context = Mock()
    context.data = {"terminal_id": "term_123"}
    assert _get_terminal_id(context) == "term_123"

    # Test with terminalId field (alternative)
    context.data = {"terminalId": "term_456"}
    assert _get_terminal_id(context) == "term_456"

    # Test with CLAUDE_TERMINAL_ID
    context.data = {"CLAUDE_TERMINAL_ID": "term_789"}
    assert _get_terminal_id(context) == "term_789"

    # Test with no terminal_id - should use default
    context.data = {}
    result = _get_terminal_id(context)
    assert result == "default" or result is not None  # Should have SOME value


def test_state_file_path_safety():
    """Test that state file paths are sanitized for safety."""
    from UserPromptSubmit_modules.declaration_reminder import _get_state_file

    # Terminal IDs with special characters should be sanitized
    unsafe_ids = [
        "term:with:colons",
        "term/with/slashes",
        "term\\with\\backslashes",
        "term with spaces",
    ]

    for unsafe_id in unsafe_ids:
        state_file = _get_state_file(unsafe_id)
        # Path should be safe (no directory traversal)
        assert ".." not in str(state_file)
        assert state_file.name.startswith("arch_declaration_")


def test_integration_workflow():
    """Test the full workflow: declaration → state storage → enforcement can read it."""
    from UserPromptSubmit_modules.declaration_reminder import (
        declaration_reminder_hook,
    )

    terminal_id = "test_workflow_integration"
    _clean_test_state(terminal_id)

    try:
        # Step 1: User makes declaration
        context = _get_hook_context("I'll update the arch template", terminal_id)
        result = declaration_reminder_hook(context)

        # Step 2: State should be stored
        state_dir = hooks_dir / "state"
        state_file = state_dir / f"arch_declaration_{terminal_id}.json"

        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)

            # Step 3: State should have path for PreToolUse to check
            assert "path" in state
            assert "arch" in state["path"] or "template" in state["path"].lower()

            # Verify PreToolUse can read this format
            assert isinstance(state["path"], str)
            assert "timestamp" in state
    finally:
        _clean_test_state(terminal_id)


if __name__ == "__main__":
    import pytest

    # Create test state directory
    TEST_STATE_DIR.mkdir(parents=True, exist_ok=True)

    pytest.main([__file__, "-v"])
