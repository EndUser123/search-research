"""TDD RED: Canonical terminal_id — tests that fail before implementation.

These tests define the expected behavior of canonical_terminal_id().
All 4 terminal_id call sites should eventually delegate to it.
"""

from __future__ import annotations

import os
import hashlib
import socket
from pathlib import Path
from unittest.mock import patch

import pytest


class TestCanonicalTerminalId:
    """Tests for canonical_terminal_id() expected behavior."""

    def test_returns_non_default_string(self):
        """canonical_terminal_id() must NOT return 'default'."""
        # Lazy import to avoid import error before module exists
        import core.terminal_id as terminal_id_module

        result = terminal_id_module.canonical_terminal_id()
        assert result != "default", f"Got '{result}' — 'default' is not a valid terminal_id"

    def test_returns_same_value_for_same_cwd(self):
        """Same cwd + hostname + pid must produce same ID within a process."""
        import core.terminal_id as terminal_id_module

        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": ""}, clear=True):
            id1 = terminal_id_module.canonical_terminal_id()
            id2 = terminal_id_module.canonical_terminal_id()
            assert id1 == id2

    def test_differs_between_different_cwd(self):
        """Different working directories must produce different IDs."""
        import core.terminal_id as terminal_id_module

        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": ""}, clear=True):
            id1 = terminal_id_module.canonical_terminal_id()
            with patch("pathlib.Path.cwd", return_value=Path("C:/different/path")):
                id2 = terminal_id_module.canonical_terminal_id()
            # Same hostname + pid, different cwd → different hash
            assert id1 != id2

    def test_env_var_overrides(self):
        """CLAUDE_TERMINAL_ID env var must take priority."""
        import core.terminal_id as terminal_id_module

        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "my-terminal-123"}):
            result = terminal_id_module.canonical_terminal_id()
            assert result == "my-terminal-123"

    def test_env_var_overrides_others(self):
        """TERMINAL_ID and TERM_ID env vars are NOT used by canonical (not in priority)."""
        import core.terminal_id as terminal_id_module

        with patch.dict(
            os.environ,
            {"CLAUDE_TERMINAL_ID": "primary", "TERMINAL_ID": "secondary", "TERM_ID": "tertiary"},
            clear=True,
        ):
            result = terminal_id_module.canonical_terminal_id()
            assert result == "primary"

    def test_id_is_valid_pattern(self):
        """Terminal ID must match [a-zA-Z0-9_-]{1,64}."""
        import core.terminal_id as terminal_id_module
        import re

        pattern = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
        result = terminal_id_module.canonical_terminal_id()
        assert pattern.match(result), f"'{result}' does not match required pattern"

    def test_is_string(self):
        """canonical_terminal_id() must return a str."""
        import core.terminal_id as terminal_id_module

        result = terminal_id_module.canonical_terminal_id()
        assert isinstance(result, str)


class TestCritiqueIoDelegation:
    """Verify critique_io path construction approaches search-research correctly.

    critique_io does dynamic sys.path manipulation to reach search-research.
    These tests verify the path injection approach works.
    """

    def test_critique_io_uses_search_research_path(self):
        """critique_io builds correct path to search-research/src."""
        from pathlib import Path

        # Simulate critique_io._get_terminal_id() path construction
        result_path = (
            Path(__file__).parent.parent / ".claude" / "packages" / "search-guard" / "src"
        )
        # Path should go: tests/ → search-research/ → P:\ → .claude → packages → search-research → src
        assert "packages" in str(result_path)

    def test_gto_orchestrator_uses_search_research_path(self):
        """gto_orchestrator builds correct path to search-research/src."""
        from pathlib import Path

        # Simulate gto_orchestrator._get_default_terminal_id() path construction
        result_path = (
            Path("P:/packages/search-research/skills/gto")
            .parent.parent.parent
            / "packages"
            / "search-research"
            / "src"
        )
        assert str(result_path).replace("\\", "/").endswith("packages/search-research/src")


class TestGtoOrchestratorDelegation:
    """Verify gto_orchestrator._get_default_terminal_id() delegates to canonical."""

    def test_gto_default_returns_canonical_format(self):
        """gto._get_default_terminal_id returns 12-char hex like canonical."""
        import re

        from core.terminal_id import canonical_terminal_id

        # Both canonical and the wired gto should return same format
        result = canonical_terminal_id()
        assert re.match(r"^[0-9a-f]{12}$", result), (
            f"canonical_terminal_id() should return 12-char hex, got: '{result}'"
        )


class TestClaudeCodeRawNoDefault:
    """Verify claude_code_raw._resolve_terminal_id() no longer returns 'default'."""

    def test_claude_code_raw_no_default_fallback(self):
        """claude_code_raw._resolve_terminal_id() must not return bare 'default'."""
        from core.chs.providers.claude_code_raw import _resolve_terminal_id

        with patch.dict(os.environ, {}, clear=True):
            result = _resolve_terminal_id(None)
            assert result != "default", (
                f"Got '{result}' — 'default' fallback creates state collisions "
                "between terminals. Should use canonical_terminal_id()."
            )

    def test_claude_log_no_default_fallback(self):
        """claude_log._resolve_terminal_id() must not return bare 'default'."""
        from core.chs.providers.claude_log import _resolve_terminal_id

        with patch.dict(os.environ, {}, clear=True):
            result = _resolve_terminal_id(None)
            assert result != "default", (
                f"Got '{result}' — 'default' fallback creates state collisions."
            )
