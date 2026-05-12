"""Tests for LLM provider abstraction."""

import os
from unittest.mock import AsyncMock, patch

import pytest
from reasoning.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""

    def __init__(self, response: str = "Mock response") -> None:
        self.response = response
        self.generate_called = False
        self.generate_with_history_called = False

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate mock response."""
        self.generate_called = True
        return self.response

    async def generate_with_history(
        self,
        prompt: str,
        history: list[dict],
        max_tokens: int = 2000,
        temperature: float = 0.7,
    ) -> str:
        """Generate mock response with history."""
        self.generate_with_history_called = True
        return f"{self.response} (with {len(history)} messages)"


@pytest.fixture
def mock_provider():
    """Create a mock provider for testing."""
    return MockLLMProvider()


@pytest.mark.asyncio
async def test_generate_returns_response(mock_provider):
    """Test that generate returns a non-empty response."""
    response = await mock_provider.generate("Test prompt")
    assert response == "Mock response"
    assert mock_provider.generate_called is True


@pytest.mark.asyncio
async def test_generate_with_history_includes_history(mock_provider):
    """Test that generate_with_history processes history."""
    history = [{"role": "user", "content": "Previous message"}]
    response = await mock_provider.generate_with_history("Test prompt", history)
    assert "with 1 messages" in response
    assert mock_provider.generate_with_history_called is True


@pytest.mark.asyncio
async def test_generate_with_max_tokens(mock_provider):
    """Test that generate respects max_tokens parameter."""
    response = await mock_provider.generate("Test prompt", max_tokens=100)
    assert response == "Mock response"


@pytest.mark.asyncio
async def test_generate_with_temperature(mock_provider):
    """Test that generate respects temperature parameter."""
    response = await mock_provider.generate("Test prompt", temperature=0.5)
    assert response == "Mock response"


# =============================================================================
# Tests for AnthropicProvider
# =============================================================================

class TestAnthropicProvider:
    """Tests for Anthropic LLM provider."""

    @pytest.mark.asyncio
    async def test_generate_calls_anthropic_client(self):
        """Test that generate calls the Anthropic API."""
        from reasoning.llm import AnthropicProvider

        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.content = [type("Content", (), {"text": "Claude response"})()]
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            provider = AnthropicProvider(api_key="test-key")
            response = await provider.generate("Test prompt")

            assert response == "Claude response"
            mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_history_builds_messages(self):
        """Test that generate_with_history builds conversation history."""
        from reasoning.llm import AnthropicProvider

        with patch("anthropic.AsyncAnthropic") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.content = [type("Content", (), {"text": "Response"})()]
            mock_client.messages.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            provider = AnthropicProvider(api_key="test-key")
            history = [
                {"role": "user", "content": "First message"},
                {"role": "assistant", "content": "Second message"},
            ]
            response = await provider.generate_with_history("Current prompt", history)

            # Verify messages include history + current prompt
            call_args = mock_client.messages.create.call_args
            messages = call_args.kwargs["messages"]
            assert len(messages) == 3
            assert messages[0]["content"] == "First message"
            assert messages[1]["content"] == "Second message"
            assert messages[2]["content"] == "Current prompt"


# =============================================================================
# Tests for OpenAIProvider
# =============================================================================

class TestOpenAIProvider:
    """Tests for OpenAI LLM provider."""

    @pytest.mark.asyncio
    async def test_generate_calls_openai_client(self):
        """Test that generate calls the OpenAI API."""
        from reasoning.llm import OpenAIProvider

        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = AsyncMock()
            mock_choice = type("Choice", (), {"message": type("Message", (), {"content": "GPT response"})()})()
            mock_client.chat.completions.create = AsyncMock(return_value=type("Response", (), {"choices": [mock_choice]})())
            mock_client_class.return_value = mock_client

            provider = OpenAIProvider(api_key="test-key")
            response = await provider.generate("Test prompt")

            assert response == "GPT response"
            mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_with_history_builds_messages(self):
        """Test that generate_with_history builds conversation history."""
        from reasoning.llm import OpenAIProvider

        with patch("openai.AsyncOpenAI") as mock_client_class:
            mock_client = AsyncMock()
            mock_choice = type("Choice", (), {"message": type("Message", (), {"content": "Response"})()})()
            mock_client.chat.completions.create = AsyncMock(return_value=type("Response", (), {"choices": [mock_choice]})())
            mock_client_class.return_value = mock_client

            provider = OpenAIProvider(api_key="test-key")
            history = [{"role": "user", "content": "Previous"}]
            response = await provider.generate_with_history("Current", history)

            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]
            assert len(messages) == 2
            assert messages[0]["content"] == "Previous"
            assert messages[1]["content"] == "Current"


# =============================================================================
# Tests for router
# =============================================================================

class TestProviderRouter:
    """Tests for LLM provider router/factory."""

    def test_get_provider_anthropic_explicit(self):
        """Test explicit anthropic provider selection."""
        from reasoning.llm import get_provider, AnthropicProvider

        with patch.dict(os.environ, {}, clear=False):
            provider = get_provider("anthropic")
            assert isinstance(provider, AnthropicProvider)

    def test_get_provider_openai_explicit(self):
        """Test explicit openai provider selection."""
        from reasoning.llm import get_provider, OpenAIProvider

        with patch.dict(os.environ, {}, clear=False):
            provider = get_provider("openai")
            assert isinstance(provider, OpenAIProvider)

    def test_get_provider_auto_detect_bifrost(self):
        """Test auto-detection when ANTHROPIC_API_KEY is set (defaults to Bifrost)."""
        from reasoning.llm import get_provider, BifrostProvider

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-key"}, clear=False):
            provider = get_provider()
            assert isinstance(provider, BifrostProvider)

    def test_get_provider_no_credentials_raises(self):
        """Test that ValueError is raised when no credentials available."""
        from reasoning.llm import get_provider

        # Clear all relevant env vars
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "", "OPENAI_API_KEY": "", "REASONING_LLM_PROVIDER": ""}, clear=True):
            with pytest.raises(ValueError, match="No LLM provider configured"):
                get_provider()

    def test_get_provider_unknown_raises(self):
        """Test that ValueError is raised for unknown provider."""
        from reasoning.llm import get_provider

        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("unknown_provider")

    def test_cached_provider_singleton(self):
        """Test that get_cached_provider returns same instance."""
        from reasoning.llm import get_cached_provider, clear_provider_cache

        clear_provider_cache()
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            p1 = get_cached_provider()
            p2 = get_cached_provider()
            assert p1 is p2

        # Clean up
        clear_provider_cache()

    def test_clear_provider_cache(self):
        """Test that clear_provider_cache resets singleton."""
        from reasoning.llm import get_cached_provider, clear_provider_cache

        clear_provider_cache()
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test"}, clear=False):
            p1 = get_cached_provider()
            clear_provider_cache()
            p2 = get_cached_provider()
            assert p1 is not p2