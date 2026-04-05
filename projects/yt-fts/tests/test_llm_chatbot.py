"""Tests for LLMHandler in chatbot.py.

These tests verify the behavior of LLMHandler methods.
Run with: pytest tests/test_llm_chatbot.py -v
"""

from unittest.mock import MagicMock, patch, Mock
import pytest

from yt_fts.llm.chatbot import LLMHandler


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    client = MagicMock()
    return client


@pytest.fixture
def mock_console():
    """Create mock Rich Console."""
    console = MagicMock()
    return console


@pytest.fixture
def handler(mock_openai_client, mock_console):
    """Create LLMHandler with mocked dependencies."""
    with patch("yt_fts.llm.chatbot.get_model_config") as mock_config, \
         patch("yt_fts.llm.chatbot.get_channel_id_from_input") as mock_channel:
        mock_config.return_value = {
            "base_url": "https://api.openai.com/v1",
            "chat_model": "gpt-3.5-turbo",
            "name": "OPENAI"
        }
        mock_channel.return_value = "test_channel_id"
        
        handler = LLMHandler(api_key="test_key", channel="@testchannel")
        handler.openai_client = mock_openai_client
        handler.console = mock_console
        return handler


class TestWrapTextPreservesCodeBlocks:
    """Tests for wrap_text preserving code blocks."""

    def test_code_block_marker_not_wrapped(self, handler):
        """Test that lines starting with triple backtick are not wrapped."""
        text = "```python\ndef hello():\n    pass\n```"
        result = handler.wrap_text(text)
        
        # Code block markers should be preserved without wrapping
        assert "```python" in result
        assert "```" in result

    def test_inline_code_marker_not_wrapped(self, handler):
        """Test that lines starting with single backtick are not wrapped."""
        text = "`inline code` and some more text"
        result = handler.wrap_text(text)
        
        # The line with backtick should be preserved
        assert "`inline code`" in result

    def test_multiline_code_block_preserved(self, handler):
        """Test that multiline code blocks are preserved."""
        text = "```python\nprint('hello')\nx = 123\n```"
        result = handler.wrap_text(text)
        
        # All code block lines should be present
        assert "```python" in result
        assert "print('hello')" in result
        assert "x = 123" in result
        assert "```" in result


class TestWrapTextWrapsNormalText:
    """Tests for wrap_text wrapping regular text."""

    def test_long_line_gets_wrapped(self, handler):
        """Test that long lines are wrapped to max_width."""
        # Create a line longer than max_width (80)
        long_text = "a" * 100
        result = handler.wrap_text(long_text)
        
        # Result should be wrapped (joined with "  \n")
        # The line should be split due to textwrap.wrap
        lines = result.split("  \n")
        # At least one line should be <= max_width
        for line in lines:
            assert len(line) <= handler.max_width, f"Line too long: {len(line)}"

    def test_short_line_not_wrapped(self, handler):
        """Test that short lines are not wrapped."""
        short_text = "Hello world"
        result = handler.wrap_text(short_text)
        
        assert result == short_text

    def test_multiple_lines_wrapped_separately(self, handler):
        """Test that each line is wrapped independently."""
        text = "Line one\nLine two is a bit longer and might get wrapped\nLine three"
        result = handler.wrap_text(text)
        
        # Each original line should be present (possibly wrapped)
        assert "Line one" in result
        assert "Line two" in result
        assert "Line three" in result


class TestFormatMessageHistoryContextFormatsMessages:
    """Tests for format_message_history_context formatting."""

    def test_includes_role_prefixes(self):
        """Test that messages include role prefixes."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        result = LLMHandler.format_message_history_context(messages)
        
        assert "user: Hello" in result
        assert "assistant: Hi there" in result

    def test_formats_multiple_messages(self):
        """Test that multiple messages are all formatted."""
        messages = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
        ]
        result = LLMHandler.format_message_history_context(messages)
        
        assert "user: Question 1" in result
        assert "assistant: Answer 1" in result
        assert "user: Question 2" in result


class TestFormatMessageHistoryContextSkipsSystem:
    """Tests for format_message_history_context skipping system messages."""

    def test_system_messages_skipped(self):
        """Test that system messages are not included in output."""
        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
        ]
        result = LLMHandler.format_message_history_context(messages)
        
        # System message should not be in result
        assert "You are a helpful assistant" not in result
        # But other messages should be
        assert "user: Hello" in result
        assert "assistant: Hi" in result

    def test_only_system_messages_returns_empty(self):
        """Test that only system messages returns empty string."""
        messages = [
            {"role": "system", "content": "System prompt"},
        ]
        result = LLMHandler.format_message_history_context(messages)
        
        assert result == ""

    def test_mixed_roles_skips_only_system(self):
        """Test mixed roles - only system is skipped."""
        messages = [
            {"role": "system", "content": "System"},
            {"role": "user", "content": "User msg"},
            {"role": "system", "content": "Another system"},
            {"role": "assistant", "content": "Assistant msg"},
        ]
        result = LLMHandler.format_message_history_context(messages)
        
        # No system messages in result
        assert "System" not in result
        assert "Another system" not in result
        # User and assistant should be present
        assert "user: User msg" in result
        assert "assistant: Assistant msg" in result


class TestDisplayMessageFormatsMarkdownForAssistant:
    """Tests for display_message formatting for assistant role."""

    def test_assistant_message_uses_markdown(self, handler):
        """Test that assistant messages are formatted as Markdown."""
        content = "This is **bold** text"
        handler.display_message(content, "assistant")
        
        # Console.print should have been called with Markdown
        handler.console.print.assert_called()
        # Get the call arguments
        call_args = handler.console.print.call_args
        # The first argument should be a Markdown object
        from rich.markdown import Markdown
        assert isinstance(call_args[0][0], Markdown)

    def test_assistant_message_wrapped_before_markdown(self, handler):
        """Test that content is wrapped before Markdown conversion."""
        long_content = "a" * 100  # Longer than max_width
        handler.display_message(long_content, "assistant")
        
        call_args = handler.console.print.call_args
        markdown_obj = call_args[0][0]
        # The wrapped text should be in the Markdown
        assert len(markdown_obj.markup) <= handler.max_width or "  \n" in markdown_obj.markup


class TestDisplayMessageFormatsBoldForUser:
    """Tests for display_message formatting for user role."""

    def test_user_message_uses_bold_style(self, handler):
        """Test that user messages use bold blue style."""
        content = "User message here"
        handler.display_message(content, "user")
        
        # Console.print should have been called
        handler.console.print.assert_called()
        # Get the call arguments
        call_args = handler.console.print.call_args
        # The first argument should be a Text object
        from rich.text import Text
        assert isinstance(call_args[0][0], Text)

    def test_user_message_has_bold_style(self, handler):
        """Test that user Text object has bold style."""
        content = "User message"
        handler.display_message(content, "user")
        
        call_args = handler.console.print.call_args
        text_obj = call_args[0][0]
        
        # Check the style is "bold blue"
        assert text_obj.style == "bold blue"

    def test_non_assistant_non_user_treated_as_user(self, handler):
        """Test that roles other than assistant are treated as user."""
        content = "Some message"
        handler.display_message(content, "other")
        
        # Should use Text with bold blue style (same as user)
        call_args = handler.console.print.call_args
        from rich.text import Text
        assert isinstance(call_args[0][0], Text)
