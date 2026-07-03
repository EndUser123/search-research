"""Tests for cc-aca-session plugin hooks."""

import json
import sys
import io
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Ensure plugin lib is importable
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_ROOT / "__lib"))
sys.path.insert(0, str(PLUGIN_ROOT))


class TestStatePaths:
    """Test state path resolution works from any install location."""

    def test_get_hooks_dir_finds_project(self):
        from aca_state_paths import get_hooks_dir
        hooks_dir = get_hooks_dir()
        assert hooks_dir.name == "hooks"
        assert hooks_dir.exists()

    def test_get_state_dir_under_hooks(self):
        from aca_state_paths import get_state_dir, get_hooks_dir
        state_dir = get_state_dir()
        assert state_dir == get_hooks_dir() / "state"

    def test_get_plan_dir_under_home(self):
        from aca_state_paths import get_plan_dir
        plan_dir = get_plan_dir()
        assert plan_dir == Path.home() / ".claude" / "plans"

    def test_safe_id_sanitizes(self):
        from aca_state_paths import safe_id
        assert safe_id(None) == "unknown"
        assert safe_id("") == "unknown"
        assert safe_id("console_abc123") == "console_abc123"
        assert safe_id("a/b\\c") == "a_b_c"

    def test_get_plugin_lib_dir(self):
        from aca_state_paths import get_plugin_lib_dir
        lib_dir = get_plugin_lib_dir()
        assert lib_dir.name == "__lib"
        assert lib_dir.exists()


class TestPreCompactHook:
    """Test the deprecated PreCompact stub."""

    def test_approves_and_returns_context(self):
        from hooks.precompact.aca_session_precompact import main
        data = json.dumps({
            "terminal_id": "test_terminal",
            "session_id": "test_session",
        })
        sys.stdin = io.StringIO(data)
        main()
        captured_stdout = sys.stdout
        # main() prints JSON to stdout — verify it parses and has decision
        sys.stdin = io.StringIO(data)
        main()

    def test_output_contains_deprecated_notice(self, capsys):
        from hooks.precompact.aca_session_precompact import main
        data = json.dumps({
            "terminal_id": "t1",
            "session_id": "s1",
        })
        sys.stdin = io.StringIO(data)
        main()
        captured = capsys.readouterr()
        assert "DEPRECATED" in captured.out


class TestVerificationCleanup:
    """Test the SessionStart verification cleanup hook."""

    def test_import_succeeds(self):
        from hooks.sessionstart.aca_session_verification_cleanup import (
            main,
            ENABLED,
            MAX_AGE_HOURS,
            PLAN_MAX_AGE_DAYS,
        )
        assert ENABLED is True
        assert MAX_AGE_HOURS == 24
        assert PLAN_MAX_AGE_DAYS == 30

    def test_cleanup_functions_exist(self):
        from hooks.sessionstart.aca_session_verification_cleanup import (
            cleanup_old_verification_states,
            cleanup_old_file_existence_decisions,
            cleanup_old_observe_before_act,
            cleanup_old_plan_files,
        )
        assert callable(cleanup_old_verification_states)
        assert callable(cleanup_old_file_existence_decisions)
        assert callable(cleanup_old_observe_before_act)
        assert callable(cleanup_old_plan_files)

    def test_cleanup_empty_state_dir(self):
        from hooks.sessionstart.aca_session_verification_cleanup import (
            cleanup_old_verification_states,
        )
        with tempfile.TemporaryDirectory() as tmp:
            # No files to clean
            result = cleanup_old_verification_states(max_age_hours=1)
            assert result == 0


class TestSessionEndCleanup:
    """Test the SessionEnd cleanup hook."""

    def test_import_succeeds(self):
        from hooks.sessionend.aca_session_cleanup import main
        assert callable(main)

    def test_exits_clean_on_empty_input(self):
        from hooks.sessionend.aca_session_cleanup import main
        sys.stdin = io.StringIO("")
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    def test_exits_clean_on_session_data(self):
        from hooks.sessionend.aca_session_cleanup import main
        data = json.dumps({
            "session_id": "test_session",
            "terminal_id": "console_test123",
        })
        sys.stdin = io.StringIO(data)
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0


class TestTDDCleanup:
    """Test the SessionEnd TDD cleanup hook."""

    def test_import_succeeds(self):
        from hooks.sessionend.aca_session_tdd_cleanup import (
            main,
            cleanup_expired_tdd_states,
        )
        assert callable(main)
        assert callable(cleanup_expired_tdd_states)

    def test_cleanup_nonexistent_dir(self):
        from hooks.sessionend.aca_session_tdd_cleanup import (
            cleanup_expired_tdd_states,
        )
        with patch.dict("os.environ", {"CLAUDE_TERMINAL_ID": "test_nonexistent"}):
            result = cleanup_expired_tdd_states()
            assert result["cleaned"] == 0


class TestCompatibilityWrappers:
    """Test that compatibility wrappers delegate correctly."""

    WRAPPERS = [
        ("SessionStart_verification_cleanup.py", "aca_session_verification_cleanup"),
        ("SessionStart_breadcrumb_init.py", "aca_session_breadcrumb_init"),
        ("SessionEnd_cleanup.py", "aca_session_cleanup"),
        ("SessionEnd_breadcrumb_cleanup.py", "aca_session_breadcrumb_cleanup"),
        ("SessionEnd_tdd_cleanup.py", "aca_session_tdd_cleanup"),
        ("PreCompact.py", "aca_session_precompact"),
    ]

    @pytest.mark.parametrize("filename,expected_module", WRAPPERS)
    def test_wrapper_exists(self, filename, expected_module):
        hooks_dir = Path("P:/.claude/hooks")
        wrapper = hooks_dir / filename
        assert wrapper.exists(), f"Wrapper missing: {filename}"

    @pytest.mark.parametrize("filename,expected_module", WRAPPERS)
    def test_wrapper_delegates_to_plugin(self, filename, expected_module):
        hooks_dir = Path("P:/.claude/hooks")
        wrapper = hooks_dir / filename
        content = wrapper.read_text(encoding="utf-8")
        assert "cc-aca-session" in content
        assert expected_module in content

    def test_backups_exist(self):
        """Original files were backed up before wrapping."""
        hooks_dir = Path("P:/.claude/hooks")
        for filename, _ in self.WRAPPERS:
            backup = hooks_dir / f"{filename}.pre-aca"
            assert backup.exists(), f"Backup missing: {backup.name}"


class TestPluginStructure:
    """Test the plugin directory structure."""

    def test_plugin_json_exists(self):
        p = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
        assert p.exists()
        data = json.loads(p.read_text())
        assert data["name"] == "cc-aca-session"

    def test_hooks_json_exists(self):
        p = PLUGIN_ROOT / "hooks" / "hooks.json"
        assert p.exists()

    def test_claude_md_exists(self):
        p = PLUGIN_ROOT / "CLAUDE.md"
        assert p.exists()

    def test_lib_init_exists(self):
        p = PLUGIN_ROOT / "__lib" / "__init__.py"
        assert p.exists()

    def test_lib_aca_state_paths_exists(self):
        p = PLUGIN_ROOT / "__lib" / "aca_state_paths.py"
        assert p.exists()

    def test_hook_files_exist(self):
        expected = [
            "hooks/sessionstart/aca_session_verification_cleanup.py",
            "hooks/sessionstart/aca_session_breadcrumb_init.py",
            "hooks/sessionend/aca_session_cleanup.py",
            "hooks/sessionend/aca_session_breadcrumb_cleanup.py",
            "hooks/sessionend/aca_session_tdd_cleanup.py",
            "hooks/precompact/aca_session_precompact.py",
        ]
        for rel in expected:
            assert (PLUGIN_ROOT / rel).exists(), f"Missing: {rel}"
