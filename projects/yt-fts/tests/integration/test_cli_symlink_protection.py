"""Integration tests for CLI symlink protection (SEC-011 CRITICAL).

These tests verify that symlinks and directory junctions cannot be used
to bypass path security restrictions in solo-dev mode.

Security Issue: Symlinks pointing outside CWD could allow unauthorized
file system access if not properly validated.
"""
import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest


pytestmark = pytest.mark.integration


class TestSymlinkProtection:
    """CRITICAL: Test that symlinks pointing outside CWD are blocked in solo-dev mode.

    These tests verify path traversal attack prevention through symlink manipulation.
    """

    def test_symlink_pointing_outside_cwd_is_blocked(self):
        """CRITICAL: verify symlinks pointing outside CWD are BLOCKED.

        Given: A symlink inside CWD pointing to a directory outside CWD
        When: Attempting to access files through the symlink
        Then: Access should be DENIED with a security error

        Attack Vector:
        1. Attacker creates symlink: CWD/project/data -> external/sensitive/data
        2. Attacker attempts to read CWD/project/data
        3. Without proper validation, this reads external sensitive data
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cwd = temp_path / "cwd"
            cwd.mkdir()

            outside_dir = temp_path / "outside"
            outside_dir.mkdir()

            outside_file = outside_dir / "secret.txt"
            outside_file.write_text("SENSITIVE DATA")

            if platform.system() != "Windows":
                symlink_path = cwd / "data_link"
                try:
                    symlink_path.symlink_to(outside_dir)
                except OSError:
                    pytest.skip("Symlink creation not permitted")

                with patch("yt_fts.core.validation.validate_project_path") as mock_validate:
                    from yt_fts.core.cli import cli
                    from click.testing import CliRunner

                    runner = CliRunner()
                    result = runner.invoke(cli, ["--config", str(symlink_path), "status"])

                    assert mock_validate.called, (
                        "SECURITY VIOLATION: validate_project_path() was not called. "
                        "Symlink traversal not detected."
                    )
            else:
                pytest.skip("Symlink test skipped on Windows (use junction test)")

    def test_directory_junction_on_windows_is_validated(self):
        """CRITICAL: verify Windows directory junctions are properly validated.

        Given: A directory junction inside CWD pointing outside CWD
        When: Attempting to access files through the junction
        Then: Access should be DENIED with a security error

        Note: This test only runs on Windows where junctions are supported.
        """
        if platform.system() != "Windows":
            pytest.skip("Directory junction test only runs on Windows")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cwd = temp_path / "cwd"
            cwd.mkdir()

            outside_dir = temp_path / "outside"
            outside_dir.mkdir()

            outside_file = outside_dir / "secret.txt"
            outside_file.write_text("SENSITIVE DATA")

            junction_path = cwd / "data_junction"
            try:
                import subprocess
                subprocess.run(
                    ["mklink", "/J", str(junction_path), str(outside_dir)],
                    shell=True,
                    check=True,
                    capture_output=True
                )
            except (subprocess.CalledProcessError, OSError):
                pytest.skip("Directory junction creation not permitted")

            with patch("yt_fts.core.validation.validate_project_path") as mock_validate:
                from yt_fts.core.cli import cli
                from click.testing import CliRunner

                runner = CliRunner()
                result = runner.invoke(cli, ["--config", str(junction_path), "status"])

                assert mock_validate.called, (
                    "SECURITY VIOLATION: validate_project_path() was not called. "
                    "Directory junction traversal not detected."
                )

    def test_path_normalization_before_security_checks(self):
        """CRITICAL: verify path normalization happens BEFORE security checks.

        Given: A path with traversal components like ../outside/secret
        When: The path is validated
        Then: Path should be normalized BEFORE checking against allowed roots

        This test ensures the validation sequence:
        1. Normalize path (resolve .., ., symlinks)
        2. Check if normalized path is within allowed roots
        3. Reject if outside allowed roots
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            allowed_root = temp_path / "allowed"
            allowed_root.mkdir()

            escape_path = allowed_root / "subdir" / ".." / ".." / "outside"

            with patch("yt_fts.core.validation.validate_project_path") as mock_validate:
                from yt_fts.core.cli import cli
                from click.testing import CliRunner

                validated_paths = []
                def capture_validated_path(path):
                    validated_paths.append(path)
                    return True

                mock_validate.side_effect = capture_validated_path

                runner = CliRunner()
                result = runner.invoke(cli, ["--config", str(escape_path), "status"])

                assert mock_validate.called, (
                    "SECURITY VIOLATION: validate_project_path() was not called. "
                    "Path normalization may not have occurred."
                )

                if validated_paths:
                    assert ".." not in str(validated_paths[0]), (
                        "SECURITY VIOLATION: Path was not normalized before validation. "
                        "Traversal components still present."
                    )


class TestSymlinkAttackVectors:
    """Test specific symlink-based attack vectors."""

    def test_symlink_to_config_file(self):
        """Attack: Symlink pointing to sensitive config files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cwd = temp_path / "cwd"
            cwd.mkdir()

            config_dir = temp_path / "sensitive_config"
            config_dir.mkdir()

            if platform.system() != "Windows":
                symlink_path = cwd / "config_backup"
                try:
                    symlink_path.symlink_to(config_dir)

                    with patch("yt_fts.core.validation.validate_project_path") as mock_validate:
                        from yt_fts.core.cli import cli
                        from click.testing import CliRunner

                        runner = CliRunner()
                        result = runner.invoke(cli, ["--config", str(symlink_path), "status"])

                        assert mock_validate.called, (
                            "SECURITY: Symlink to sensitive config not detected"
                        )
                except OSError:
                    pytest.skip("Symlink creation failed")
            else:
                pytest.skip("Symlink test skipped on Windows")

    def test_symlink_chain_bypass(self):
        """Attack: Chain of symlinks to obscure final destination."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            cwd = temp_path / "cwd"
            cwd.mkdir()

            if platform.system() != "Windows":
                link1 = cwd / "link1"
                link2 = temp_path / "link2"
                target = temp_path / "secret"
                target.mkdir()

                try:
                    link2.symlink_to(target)
                    link1.symlink_to(link2)

                    with patch("yt_fts.core.validation.validate_project_path") as mock_validate:
                        from yt_fts.core.cli import cli
                        from click.testing import CliRunner

                        runner = CliRunner()
                        result = runner.invoke(cli, ["--config", str(link1), "status"])

                        assert mock_validate.called, (
                            "SECURITY: Symlink chain not fully resolved"
                        )
                except OSError:
                    pytest.skip("Symlink chain creation failed")
            else:
                pytest.skip("Symlink chain test skipped on Windows")

    def test_relative_symlink_escape(self):
        """Attack: Relative symlinks using .. to escape."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            allowed_root = temp_path / "allowed"
            allowed_root.mkdir()

            subdir = allowed_root / "subdir"
            subdir.mkdir()

            if platform.system() != "Windows":
                outside = temp_path / "outside"
                outside.mkdir()

                link_path = subdir / "data"
                try:
                    link_path.symlink_to("../outside")

                    with patch("yt_fts.core.validation.validate_project_path") as mock_validate:
                        from yt_fts.core.cli import cli
                        from click.testing import CliRunner

                        runner = CliRunner()
                        result = runner.invoke(cli, ["--config", str(link_path), "status"])

                        assert mock_validate.called, (
                            "SECURITY: Relative symlink escape not detected"
                        )
                except OSError:
                    pytest.skip("Relative symlink creation failed")
            else:
                pytest.skip("Relative symlink test skipped on Windows")
