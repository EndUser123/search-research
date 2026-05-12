"""Tests for Bifrost provider."""
import os
from unittest.mock import patch
import pytest


class TestBifrostProvider:
    """Tests for Bifrost LLM provider."""

    @pytest.mark.asyncio
    async def test_generate_calls_bf_agent(self):
        """Test that generate calls bf_agent run_simple."""
        from reasoning.llm import BifrostProvider

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            with patch("bf_agent.run_simple") as mock_run:
                mock_run.return_value = {"ok": True, "text": "Bifrost response"}
                provider = BifrostProvider(default_model="DSv4-flash", default_mode="brainstorm")
                response = await provider.generate("Test prompt")
                assert response == "Bifrost response"
                mock_run.assert_called_once_with(mode="brainstorm", prompt="Test prompt", model="DSv4-flash")

    @pytest.mark.asyncio
    async def test_generate_error_raises(self):
        """Test that generate raises on error."""
        from reasoning.llm import BifrostProvider

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            with patch("bf_agent.run_simple") as mock_run:
                mock_run.return_value = {"ok": False, "error": "Timeout"}
                provider = BifrostProvider()
                with pytest.raises(RuntimeError, match="Bifrost error: Timeout"):
                    await provider.generate("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_with_history(self):
        """Test that generate_with_history uses run_compare."""
        from reasoning.llm import BifrostProvider

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            with patch("bf_agent.run_compare") as mock_run:
                mock_run.return_value = {"ok": True, "results": [{"text": "Compared response"}]}
                provider = BifrostProvider(default_model="M27")
                history = [{"role": "user", "content": "Previous message"}]
                response = await provider.generate_with_history("Current prompt", history)
                assert response == "Compared response"


class TestBifrostRouter:
    """Tests for router with Bifrost default."""

    def test_get_provider_bifrost_explicit(self):
        """Test explicit bifrost provider selection."""
        from reasoning.llm import get_provider, BifrostProvider
        with patch.dict(os.environ, {}, clear=False):
            provider = get_provider("bifrost")
            assert isinstance(provider, BifrostProvider)

    def test_get_provider_auto_detect_bifrost(self):
        """Test auto-detection when ANTHROPIC_API_KEY is set."""
        from reasoning.llm import get_provider, BifrostProvider
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-key"}, clear=False):
            provider = get_provider()
            assert isinstance(provider, BifrostProvider)

    def test_get_provider_no_credentials_raises(self):
        """Test that ValueError is raised when no credentials available."""
        from reasoning.llm import get_provider
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "REASONING_LLM_PROVIDER": ""}, clear=True):
            with pytest.raises(ValueError, match="No LLM provider configured"):
                get_provider()
