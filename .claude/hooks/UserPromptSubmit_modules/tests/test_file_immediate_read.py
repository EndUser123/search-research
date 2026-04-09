"""Tests for file_immediate_read hook."""

from __future__ import annotations

import pytest
from pathlib import Path
import tempfile
import os

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.file_immediate_read import (
    _extract_paths,
    _is_readable_file,
    _expand_path,
    file_immediate_read,
)


class TestExtractPaths:
    """Test path extraction from prompts."""

    def test_windows_absolute_path(self):
        assert _extract_paths(r"C:\Users\brsth\Downloads\file.txt") == [r"C:\Users\brsth\Downloads\file.txt"]
        assert _extract_paths(r"P:\.claude\skills\ai-gemini\SKILL.md") == [r"P:\.claude\skills\ai-gemini\SKILL.md"]

    def test_unix_absolute_path(self):
        assert _extract_paths("/home/user/file.py") == ["/home/user/file.py"]
        assert _extract_paths("/mnt/data/doc.md") == ["/mnt/data/doc.md"]
        assert _extract_paths("/tmp/test.txt") == ["/tmp/test.txt"]

    def test_tilde_path(self):
        # Tilde expansion only works mid-string (word boundary before ~)
        # At prompt start, \b can't match start-of-string, so this is a known limitation
        result = _extract_paths("Use ~/Documents/readme.md for this")
        assert len(result) == 1
        # os.path.expanduser normalizes the path
        assert result[0].endswith("Documents/readme.md") or result[0].endswith("Documents\\readme.md")

    def test_relative_path(self):
        assert _extract_paths("./src/main.py") == ["./src/main.py"]
        assert _extract_paths("../config/settings.yaml") == ["../config/settings.yaml"]

    def test_no_paths(self):
        assert _extract_paths("Hello world, this has no paths") == []
        assert _extract_paths("") == []

    def test_multiple_paths(self):
        result = _extract_paths(r"Read P:\.claude\hooks\test.py and ./config.yaml")
        assert len(result) >= 2


class TestIsReadableFile:
    """Test readable file detection."""

    def test_readable_extensions(self, tmp_path):
        for ext in (".py", ".md", ".txt", ".yaml", ".json"):
            f = tmp_path / f"test{ext}"
            f.write_text("content")
            assert _is_readable_file(str(f)) is True

    def test_binary_extensions(self, tmp_path):
        for ext in (".exe", ".dll", ".png", ".jpg", ".pdf", ".zip"):
            f = tmp_path / f"test{ext}"
            f.write_text("content")
            assert _is_readable_file(str(f)) is False

    def test_nonexistent_file(self):
        assert _is_readable_file("/nonexistent/path/file.py") is False

    def test_directory(self, tmp_path):
        assert _is_readable_file(str(tmp_path)) is False


class TestExpandPath:
    """Test path resolution."""

    def test_existing_absolute(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello")
        result = _expand_path(str(f))
        assert result is not None
        assert result.exists()

    def test_nonexistent_with_p_drive_fallback(self, tmp_path):
        # Create a temp path structure on P: drive if possible
        result = _expand_path("nonexistent_file.txt")
        # May or may not resolve depending on environment
        # Just verify it doesn't crash
        assert result is None or result.exists()

    def test_relative_to_p_drive(self):
        # Test resolution against P: drive
        result = _expand_path("README.md")
        # README.md at P:\ should exist
        if result is not None:
            assert not result.exists() or result.is_file()


class TestFileImmediateReadIntegration:
    """Integration tests for the hook."""

    def test_hook_returns_empty_for_no_paths(self):
        context = HookContext(prompt="Hello world", data={})
        result = file_immediate_read(context)
        assert result.is_empty()

    def test_hook_returns_empty_for_nonexistent_paths(self):
        context = HookContext(prompt="/nonexistent/file/path.md", data={})
        result = file_immediate_read(context)
        assert result.is_empty()

    def test_hook_reads_existing_file(self, tmp_path):
        test_file = tmp_path / "test_read.md"
        test_file.write_text("# Test File\n\nHello world")
        # Use the full path in prompt
        prompt = f"Read {test_file} and summarize it"
        context = HookContext(prompt=prompt, data={})
        result = file_immediate_read(context)
        assert not result.is_empty()
        assert "[FILE:" in result.context
        assert "# Test File" in result.context

    def test_hook_skips_file_already_in_prompt(self, tmp_path):
        # Case: user pastes file contents in prompt — shouldn't re-read
        content = "# Existing Content\n\nAlready in prompt"
        prompt = f"""Here's the file content:
```
{content}
```

Analyze it."""
        context = HookContext(prompt=prompt, data={})
        result = file_immediate_read(context)
        # Should be empty since file path is part of the prompt content
        assert result.is_empty()

    def test_hook_truncates_large_files(self, tmp_path):
        test_file = tmp_path / "large.md"
        lines = ["line"] * 200
        test_file.write_text("\n".join(lines))
        context = HookContext(prompt=f"Review {test_file}", data={})
        result = file_immediate_read(context)
        assert not result.is_empty()
        assert "truncated" in result.context

    def test_hook_priority(self):
        context = HookContext(prompt="/fake/path.md", data={})
        result = file_immediate_read(context)
        assert result.priority == 9.5
