"""T12: Terminal_id scoping validation — each provider uses correct terminal_id prefix.

Verifies per D3: terminal_id scoping strategy for each provider:
- claude_code_raw: CLAUDE_TERMINAL_ID env or "default"
- claude_code_archive: inherited from source (same as claude_code_raw here)
- codex_desktop: codex_{workspace_hash[:8]}
- gemini_cli: gemini_{session_id[:8]} (not yet implemented)
- claude_desktop: claude_desktop_{conversation_id[:8]} (not yet implemented)
"""

import os
import hashlib
from pathlib import Path
from unittest.mock import patch

import pytest

from core.chs.providers.claude_code_raw import ClaudeCodeRawProvider, _resolve_terminal_id as resolve_ccr
from core.chs.providers.codex_desktop import CodexDesktopProvider, _resolve_terminal_id as resolve_codex
from core.chs.providers.claude_log import ClaudeLogProvider, _resolve_terminal_id as resolve_clog


class TestTerminalIdScoping:
    """T12: Terminal_id scoping validation per provider."""

    def test_claude_code_raw_no_default_fallback(self):
        """claude_code_raw: no env/arg → canonical terminal_id (NOT 'default')."""
        with patch.dict(os.environ, {}, clear=True):
            result = resolve_ccr(None)
            assert result != "default", f"Got '{result}' — 'default' creates terminal collisions"

    def test_claude_code_raw_uses_env_terminal_id(self):
        """claude_code_raw: CLAUDE_TERMINAL_ID env var is used when set."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "my-custom-terminal"}):
            result = resolve_ccr(None)
            assert result == "my-custom-terminal"

    def test_claude_code_raw_uses_explicit_over_env(self):
        """claude_code_raw: explicit terminal_id argument overrides env."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "env-terminal"}):
            result = resolve_ccr("explicit-terminal")
            assert result == "explicit-terminal"

    def test_codex_desktop_defaults_to_codex_prefix(self):
        """codex_desktop: no terminal_id arg → codex_{md5(cwd)[:8]}."""
        with patch.dict(os.environ, {}, clear=True):
            result = resolve_codex(None)
        assert result.startswith("codex_"), f"Expected codex_ prefix, got: {result}"
        suffix = result[len("codex_"):]
        assert len(suffix) == 8, f"Expected 8-char hash suffix, got: {suffix}"
        assert all(c in "0123456789abcdef" for c in suffix), f"Expected hex chars, got: {suffix}"

    def test_codex_desktop_uses_explicit_terminal_id(self):
        """codex_desktop: explicit terminal_id is used directly."""
        result = resolve_codex("my-codex-terminal")
        assert result == "my-codex-terminal"

    def test_codex_desktop_deterministic_for_same_cwd(self):
        """codex_desktop: same CWD always produces same terminal_id."""
        with patch.dict(os.environ, {}):
            id1 = resolve_codex(None)
            id2 = resolve_codex(None)
        assert id1 == id2, "Same CWD should produce same terminal_id"

    def test_claude_log_no_default_fallback(self):
        """claude_log: no env/arg → canonical terminal_id (NOT 'default')."""
        with patch.dict(os.environ, {}, clear=True):
            result = resolve_clog(None)
            assert result != "default", f"Got '{result}' — 'default' creates terminal collisions"

    def test_claude_log_uses_env_terminal_id(self):
        """claude_log: CLAUDE_TERMINAL_ID env var is used when set."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "log-terminal"}):
            result = resolve_clog(None)
            assert result == "log-terminal"

    def test_provider_instances_have_correct_provider_id(self):
        """Each provider instance has the correct provider_id attribute."""
        assert ClaudeCodeRawProvider().provider_id == "claude_code_raw"
        assert CodexDesktopProvider().provider_id == "codex_desktop"
        assert ClaudeLogProvider().provider_id == "claude_log"
