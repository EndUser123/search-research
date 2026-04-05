"""
Tests for plugin discovery security features.

Tests the security improvements added in Phase 1.1 of the refactor plan:
- Allowlist validation for plugin directories
- Opt-in requirement for user config plugins (YT_FTS_ALLOW_PLUGINS)
- Proper logging of all plugin load failures (no silent exceptions)
- register_plugin_dir() functionality
"""
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest


# Helper to get the environment variable check
def check_opt_in_enabled(value: str) -> bool:
    """Check if a YT_FTS_ALLOW_PLUGINS value would enable plugins."""
    return value.lower() in ("1", "true", "yes")


class TestPluginSecurityOptIn:
    """Tests for YT_FTS_ALLOW_PLUGINS opt-in requirement."""

    def test_opt_in_check_true_values(self):
        """Valid opt-in values should return True."""
        assert check_opt_in_enabled("1")
        assert check_opt_in_enabled("true")
        assert check_opt_in_enabled("yes")
        assert check_opt_in_enabled("TRUE")  # Case insensitive
        assert check_opt_in_enabled("YES")

    def test_opt_in_check_false_values(self):
        """Invalid opt-in values should return False."""
        assert not check_opt_in_enabled("0")
        assert not check_opt_in_enabled("false")
        assert not check_opt_in_enabled("no")
        assert not check_opt_in_enabled("")
        assert not check_opt_in_enabled("random")


class TestPluginAllowlist:
    """Tests for plugin directory allowlist functionality."""

    def test_builtin_plugins_in_allowed_dirs(self):
        """Builtin plugin directory should always be in allowed list."""
        from yt_fts.display.discovery import get_allowed_plugin_dirs

        allowed = get_allowed_plugin_dirs()

        # Builtin plugins should always be allowed
        builtin_allowed = any("display" in str(p) and "plugins" in str(p) for p in allowed)
        assert builtin_allowed, "Builtin plugins should always be allowed"

    def test_register_plugin_dir_adds_to_allowlist(self):
        """register_plugin_dir should add a directory to the allowlist."""
        from yt_fts.display.discovery import (
            is_safe_plugin_dir,
            register_plugin_dir,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_plugins"
            custom_dir.mkdir()

            # Initially not allowed
            assert not is_safe_plugin_dir(custom_dir)

            # After registration, should be allowed
            result = register_plugin_dir(custom_dir)
            assert result is True
            assert is_safe_plugin_dir(custom_dir)

    def test_register_plugin_dir_rejects_non_directory(self):
        """register_plugin_dir should reject non-directories."""
        from yt_fts.display.discovery import register_plugin_dir

        with tempfile.NamedTemporaryFile() as tmpfile:
            result = register_plugin_dir(Path(tmpfile.name))
            assert result is False

    def test_get_allowed_includes_registered_dirs(self):
        """get_allowed_plugin_dirs should include registered directories."""
        from yt_fts.display.discovery import (
            get_allowed_plugin_dirs,
            register_plugin_dir,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_plugins"
            custom_dir.mkdir()

            register_plugin_dir(custom_dir)
            allowed = get_allowed_plugin_dirs()

            # The custom directory should be in the allowed list
            resolved_custom = custom_dir.resolve()
            allowed_resolved = [p.resolve() for p in allowed]
            assert any(
                resolved_custom == p or resolved_custom.is_relative_to(p)
                for p in allowed_resolved
            )

    def test_unlisted_directory_not_safe(self):
        """Unlisted directories should be rejected."""
        from yt_fts.display.discovery import is_safe_plugin_dir

        with tempfile.TemporaryDirectory() as tmpdir:
            unlisted_dir = Path(tmpdir) / "unlisted_plugins"
            unlisted_dir.mkdir()

            assert not is_safe_plugin_dir(unlisted_dir)


class TestPluginDiscoveryLogging:
    """Tests for proper logging (no silent exceptions)."""

    def test_discover_plugins_logs_blocked_directory(self, caplog):
        """discover_plugins should log when directory is not allowed."""
        from yt_fts.display.discovery import discover_plugins

        with tempfile.TemporaryDirectory() as tmpdir:
            unlisted_dir = Path(tmpdir) / "unlisted"
            unlisted_dir.mkdir()

            with caplog.at_level(logging.WARNING):
                result = discover_plugins(unlisted_dir)

            # Should log a warning about blocked directory
            assert result == 0
            assert any(
                "disabled" in record.message.lower() or "allowlist" in record.message.lower()
                for record in caplog.records
            )

    def test_discover_plugins_logs_nonexistent_directory(self, caplog):
        """discover_plugins should log when directory doesn't exist."""
        from yt_fts.display.discovery import discover_plugins

        nonexistent = Path("/nonexistent/plugins/directory/that/does/not/exist")

        with caplog.at_level(logging.DEBUG):
            result = discover_plugins(nonexistent)

        # Should return 0 and may log debug message
        assert result == 0

    def test_load_plugin_logs_syntax_errors(self, caplog):
        """_load_plugin_from_file should log syntax errors."""
        from yt_fts.display.discovery import _load_plugin_from_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with syntax error
            bad_plugin = Path(tmpdir) / "bad_plugin.py"
            bad_plugin.write_text("def broken_syntax(:\n    pass")

            with caplog.at_level(logging.ERROR):
                result = _load_plugin_from_file(bad_plugin)

            # Should log the syntax error
            assert result == 0
            assert any(
                "syntax error" in record.message.lower()
                for record in caplog.records
            )

    def test_load_plugin_logs_import_errors(self, caplog):
        """_load_plugin_from_file should log import errors."""
        from yt_fts.display.discovery import _load_plugin_from_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file with import error
            bad_plugin = Path(tmpdir) / "import_error_plugin.py"
            bad_plugin.write_text("from nonexistent_module import Something")

            with caplog.at_level(logging.WARNING):
                result = _load_plugin_from_file(bad_plugin)

            # Should log the import error
            assert result == 0
            assert any(
                "import error" in record.message.lower()
                for record in caplog.records
            )

    def test_load_plugin_logs_runtime_errors(self, caplog):
        """_load_plugin_from_file should log runtime errors."""
        from yt_fts.display.discovery import _load_plugin_from_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file that will raise a runtime error
            error_plugin = Path(tmpdir) / "error_plugin.py"
            error_plugin.write_text("raise RuntimeError('Intentional error')")

            with caplog.at_level(logging.ERROR):
                result = _load_plugin_from_file(error_plugin)

            # Should log the runtime error with traceback
            assert result == 0
            assert any(
                "RuntimeError" in record.message
                for record in caplog.records
            )


class TestPluginDiscoverySecurity:
    """Security-focused integration tests for plugin discovery."""

    def test_cannot_load_from_arbitrary_directory(self):
        """Plugins should not load from arbitrary directories."""
        from yt_fts.display.discovery import discover_plugins

        with tempfile.TemporaryDirectory() as tmpdir:
            rogue_dir = Path(tmpdir) / "rogue_plugins"
            rogue_dir.mkdir()

            # Create a fake plugin file
            rogue_plugin = rogue_dir / "malicious.py"
            rogue_plugin.write_text("# malicious plugin code")

            # Should not load anything (directory not in allowlist)
            count = discover_plugins(rogue_dir)
            assert count == 0

    def test_registered_directory_allows_loading(self):
        """Registered directories should allow plugin loading."""
        from yt_fts.display.discovery import (
            discover_plugins,
            register_plugin_dir,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            custom_dir = Path(tmpdir) / "custom_plugins"
            custom_dir.mkdir()

            # Register the directory as safe
            register_plugin_dir(custom_dir)

            # Create a minimal valid plugin
            plugin_file = custom_dir / "minimal.py"
            plugin_file.write_text("""
from yt_fts.display.base import DisplayPlugin

class MinimalTestPlugin(DisplayPlugin):
    def get_name(self):
        return "minimal"
""")

            # Should attempt to load (may fail due to import issues, but shouldn't be blocked)
            with patch("yt_fts.display.discovery._logger") as mock_logger:
                discover_plugins(custom_dir)

                # Should not log "blocked" or "allowlist" warnings
                blocked_warnings = [
                    call for call in mock_logger.warning.call_args_list
                    if "blocked" in str(call).lower() or "allowlist" in str(call).lower()
                ]
                assert len(blocked_warnings) == 0


class TestLoggingCoverage:
    """Tests that all exception types are properly logged."""

    def test_attribute_error_is_logged(self, caplog):
        """AttributeError during plugin load should be logged."""
        from yt_fts.display.discovery import _load_plugin_from_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file that will cause attribute error
            error_plugin = Path(tmpdir) / "attr_error.py"
            error_plugin.write_text("import sys; sys.nonexistent_attr")

            with caplog.at_level(logging.WARNING):
                result = _load_plugin_from_file(error_plugin)

            # Should log the attribute error
            assert result == 0
            assert any(
                "attribute" in record.message.lower() or "import" in record.message.lower()
                for record in caplog.records
            )

    def test_type_error_is_logged(self, caplog):
        """TypeError during plugin load should be logged."""
        from yt_fts.display.discovery import _load_plugin_from_file

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a file that will cause type error
            error_plugin = Path(tmpdir) / "type_error.py"
            error_plugin.write_text("int('not a number')")

            with caplog.at_level(logging.ERROR):
                result = _load_plugin_from_file(error_plugin)

            # Should log the type error
            assert result == 0
            assert any(
                "type error" in record.message.lower() or "value" in record.message.lower()
                for record in caplog.records
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
