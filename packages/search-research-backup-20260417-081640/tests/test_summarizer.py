"""Tests for core.chs.summarizer."""

import pytest
from unittest.mock import patch, AsyncMock

from core.chs.summarizer import SUMMARIZER_PROMPT


@pytest.mark.asyncio
async def test_summarizer_basic():
    """Summarizer returns a non-empty string for valid messages."""
    mock_fn = AsyncMock(return_value=("Fixed the auth bug", True))
    with patch("core.llm.provider_manager.generate_with_fallback", mock_fn):
        from core.chs import summarizer
        result = await summarizer.generate_session_summary([
            {"role": "user", "content": "How do I configure the database?"},
            {"role": "assistant", "content": "Set DATABASE_URL in your environment."},
        ])
        assert isinstance(result, str)
        assert len(result) > 0
        assert len(result) <= 255
        mock_fn.assert_called_once()


@pytest.mark.asyncio
async def test_summarizer_truncates_long_content():
    """Summarizer truncates content to max_preview_chars."""
    mock_fn = AsyncMock(return_value=("Discussed auth patterns", True))
    with patch("core.llm.provider_manager.generate_with_fallback", mock_fn):
        from core.chs import summarizer
        result = await summarizer.generate_session_summary(
            [{"role": "user", "content": "x" * 1000}], max_preview_chars=200
        )
        assert isinstance(result, str)


@pytest.mark.asyncio
async def test_summarizer_failure_returns_placeholder():
    """On LLM failure, summarizer returns placeholder."""
    mock_fn = AsyncMock(return_value=("[summary unavailable]", False))
    with patch("core.llm.provider_manager.generate_with_fallback", mock_fn):
        from core.chs import summarizer
        result = await summarizer.generate_session_summary([{"role": "user", "content": "test"}])
        assert result == "[summary unavailable]"


@pytest.mark.asyncio
async def test_summarizer_enforces_255_char_limit():
    """Summary is truncated to 255 chars."""
    long_summary = "a" * 300
    mock_fn = AsyncMock(return_value=(long_summary, True))
    with patch("core.llm.provider_manager.generate_with_fallback", mock_fn):
        from core.chs import summarizer
        result = await summarizer.generate_session_summary([{"role": "user", "content": "test"}])
        assert len(result) <= 255


def test_summarizer_prompt_template():
    """Prompt template contains required sections."""
    assert "Recent messages:" in SUMMARIZER_PROMPT
    assert "Summary (1 sentence" in SUMMARIZER_PROMPT
