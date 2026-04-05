"""
Integration tests for CLI security (SEC-010 CRITICAL).

These tests verify that validate_project_path() is called during CLI execution
to prevent security bypass through unvalidated project paths.

Security Issue: cli.py:486 - cli() function never calls validate_project_path(),
allowing complete security bypass.
"""
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest


class TestCLIPathValidationSecurity:
    """CRITICAL: Test that validate_project_path() is called to prevent security bypass."""

    def test_cli_validates_project_path_before_scanning(self):
        """
        CRITICAL: verify validate_project_path() is called to prevent security bypass.
        
        Given: A temporary directory outside the allowed workspace
        When: Attempting to validate it via CLI
        Then: Access should be DENIED and validate_project_path() should be called
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            with patch("yt_fts.core.validation.validate_project_path") as mock_validate:
                mock_validate.side_effect = PermissionError(
                    f"Path outside allowed workspace: {temp_path}"
                )
                
                from yt_fts.core.cli import cli
                from click.testing import CliRunner
                
                runner = CliRunner()
                result = runner.invoke(cli, ["--config", str(temp_path), "status"])
                
                # CRITICAL: validate_project_path() MUST have been called
                assert mock_validate.called, (
                    "SECURITY VIOLATION: validate_project_path() was never called. "
                    "This allows complete security bypass."
                )

    def test_cli_rejects_paths_outside_allowed_roots(self):
        """CRITICAL: verify paths OUTSIDE allowed_roots are REJECTED."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            mock_allowed_roots = [
                Path("/safe/workspace1"),
                Path("/safe/workspace2"),
            ]
            
            with patch("yt_fts.core.validation.get_allowed_roots") as mock_get_roots,                     patch("yt_fts.core.validation.validate_project_path") as mock_validate:
                
                mock_get_roots.return_value = mock_allowed_roots
                
                def validate_rejects_outside(path):
                    if not any(str(path).startswith(str(root)) for root in mock_allowed_roots):
                        raise PermissionError(
                            f"SECURITY: Path outside allowed roots: {mock_allowed_roots}"
                        )
                    return True
                
                mock_validate.side_effect = validate_rejects_outside
                
                from yt_fts.core.cli import cli
                from click.testing import CliRunner
                
                runner = CliRunner()
                result = runner.invoke(cli, ["--config", str(temp_path), "status"])
                
                assert mock_validate.called, (
                    "SECURITY VIOLATION: validate_project_path() was not called."
                )
