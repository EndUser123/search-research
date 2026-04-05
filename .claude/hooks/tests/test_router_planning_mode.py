# Minimal test for planning mode message
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestPlanningMode:
    @pytest.fixture
    def router_module(self):
        hooks_dir = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(hooks_dir))
        import UserPromptSubmit_router as router
        return router

    @pytest.fixture
    def mock_auth(self):
        mock_mod = MagicMock()
        mock_mod.detect_question.return_value = True
        mock_mod.has_authorization.return_value = False
        return mock_mod

    def test_planning_mode_no_warning_emoji(self, router_module, mock_auth):
        data = {"prompt": "How should I design this?"}
        prompt = "How should I design this?"

        with patch.object(router_module, "import_hook", return_value=mock_auth):
            result = router_module.run_authority_check(data, prompt)

        assert result is not None
        context = result["context"]
        # This FAILS - current behavior has warning emoji
        assert "⚠️" not in context, f"Should NOT contain warning emoji. Got:\n{context}"

    def test_planning_mode_message_contains_blue_banner(self, router_module, mock_auth):
        """Test that planning mode message contains the blue banner emoji."""
        data = {"prompt": "How should I design this component?"}
        prompt = "How should I design this component?"

        with patch.object(router_module, "import_hook", return_value=mock_auth):
            result = router_module.run_authority_check(data, prompt)

        assert result is not None
        assert "context" in result
        context = result["context"]
        assert "🔵 PLANNING MODE ACTIVE" in context

    def test_planning_mode_message_no_warning_text(self, router_module, mock_auth):
        """Test that planning mode message does NOT contain WARNING text."""
        data = {"prompt": "How would you structure this?"}
        prompt = "How would you structure this?"

        with patch.object(router_module, "import_hook", return_value=mock_auth):
            result = router_module.run_authority_check(data, prompt)

        assert result is not None
        assert "context" in result
        context = result["context"]
        assert "WARNING" not in context.upper()

    def test_planning_mode_message_no_error_text(self, router_module, mock_auth):
        """Test that planning mode message does NOT contain error text."""
        data = {"prompt": "What do you think about this design?"}
        prompt = "What do you think about this design?"

        with patch.object(router_module, "import_hook", return_value=mock_auth):
            result = router_module.run_authority_check(data, prompt)

        assert result is not None
        assert "context" in result
        context = result["context"]
        assert "error" not in context.lower()

    def test_planning_mode_message_is_purely_informational(self, router_module, mock_auth):
        """Test that planning mode message is purely informational (combined checks)."""
        data = {"prompt": "Should we use a different architecture?"}
        prompt = "Should we use a different architecture?"

        with patch.object(router_module, "import_hook", return_value=mock_auth):
            result = router_module.run_authority_check(data, prompt)

        assert result is not None
        assert "context" in result
        context = result["context"]

        # Must have blue banner
        assert "🔵 PLANNING MODE ACTIVE" in context

        # Must NOT have warning indicators
        violations = []
        if "⚠️" in context:
            violations.append("Warning emoji (⚠️) found")
        if "WARNING" in context.upper():
            violations.append("'WARNING' text found")
        if "error" in context.lower():
            violations.append("'error' text found")

        assert not violations, (
            "Context has warning indicators (should be informational only):\n" +
            "\n".join(f"  - {v}" for v in violations) +
            "\n\nFull context:\n" + context
        )

    def test_no_result_when_authorized_prompt(self, router_module, mock_auth):
        """Test that no planning mode message when prompt has authorization."""
        # Setup mock to return True for has_authorization (user HAS authorized)
        mock_auth.detect_question.return_value = True
        mock_auth.has_authorization.return_value = True

        data = {"prompt": "Please implement this feature"}
        prompt = "Please implement this feature"

        with patch.object(router_module, "import_hook", return_value=mock_auth):
            result = router_module.run_authority_check(data, prompt)

        assert result is None
