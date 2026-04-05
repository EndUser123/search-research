"""Tests for _strip_rich_tags function."""

import pytest

from yt_fts.download.batch_downloader import _strip_rich_tags


class TestStripRichTags:
    """Tests for _strip_rich_tags utility function."""

    def test_strips_color_tags(self):
        """Should remove [red], [/red], [green], [/green] etc."""
        input_text = "[red]Error[/red]"
        expected = "Error"
        result = _strip_rich_tags(input_text)
        assert result == expected, f"Expected '{expected}', got '{result}'"

    def test_strips_bold_tags(self):
        """Should remove [bold], [/bold] tags."""
        input_text = "[bold]Important[/bold]"
        expected = "Important"
        result = _strip_rich_tags(input_text)
        assert result == expected

    def test_strips_mixed_tags(self):
        """Should handle multiple different tag types."""
        input_text = "[red][bold]Text[/bold][/red]"
        expected = "Text"
        result = _strip_rich_tags(input_text)
        assert result == expected

    def test_preserves_text_between_tags(self):
        """Should preserve actual content, only removing tags."""
        input_text = "[green]Success[/green] - [bold]Done[/bold]"
        expected = "Success - Done"
        result = _strip_rich_tags(input_text)
        assert result == expected

    def test_handles_plain_text(self):
        """Should return plain text unchanged."""
        input_text = "Just plain text"
        expected = "Just plain text"
        result = _strip_rich_tags(input_text)
        assert result == expected

    def test_handles_empty_string(self):
        """Should handle empty input."""
        input_text = ""
        expected = ""
        result = _strip_rich_tags(input_text)
        assert result == expected

    def test_handles_only_tags(self):
        """Should handle string with only tags."""
        input_text = "[red][/red]"
        expected = ""
        result = _strip_rich_tags(input_text)
        assert result == expected

    def test_handles_complex_real_world_example(self):
        """Should handle real-world Rich markup."""
        # This is the actual use case from the code
        input_text = "[green]1,234 videos[/green] ✓"
        expected = "1,234 videos ✓"
        result = _strip_rich_tags(input_text)
        assert result == expected

    def test_handles_nested_different_tags(self):
        """Should handle various Rich markup patterns."""
        input_text = "[yellow]Warning[/yellow]: [bold]Check[/bold] [italic]this[/italic]"
        expected = "Warning: Check this"
        result = _strip_rich_tags(input_text)
        assert result == expected

    def test_handles_consecutive_tags(self):
        """Should handle back-to-back tags without spaces."""
        input_text = "[red][bold]A[/bold][/red][green]B[/green]"
        expected = "AB"
        result = _strip_rich_tags(input_text)
        assert result == expected
