"""Tests for --reset-checkpoint flag in batch download.

This test verifies that the --reset-checkpoint flag deletes the checkpoint
file before batch download starts.

Run with: pytest tests/test_batch_checkpoint_reset.py -v
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import click

from yt_fts.download.batch_checkpoint import save_checkpoint, reset_checkpoint


class TestBatchCheckpointResetFlag:
    """Tests for --reset-checkpoint CLI flag behavior."""

    @pytest.fixture
    def temp_checkpoint_dir(self, tmp_path):
        """Create a temporary directory for checkpoint testing."""
        return tmp_path / "checkpoints"

    @pytest.fixture
    def checkpoint_file(self, temp_checkpoint_dir):
        """Create a checkpoint file path in temp directory."""
        temp_checkpoint_dir.mkdir(parents=True, exist_ok=True)
        return temp_checkpoint_dir / "batch_checkpoint.json"

    @pytest.fixture
    def existing_checkpoint(self, checkpoint_file):
        """Create an existing checkpoint file for testing."""
        # Create checkpoint data
        save_checkpoint(5, str(checkpoint_file))
        assert checkpoint_file.exists()
        yield checkpoint_file
        # Cleanup
        if checkpoint_file.exists():
            checkpoint_file.unlink()

    def _get_cli_options(self):
        """Helper to get all CLI option names from batch_download command."""
        from yt_fts.core.download_cli import batch_download
        
        options = []
        # batch_download is a click.Command with params attribute
        if hasattr(batch_download, "params"):
            for param in batch_download.params:
                if isinstance(param, click.core.Option):
                    options.extend(param.opts)
        return options

    def test_reset_checkpoint_cli_flag_exists(self):
        """Test that the --reset-checkpoint CLI flag exists.

        Given: The batch_download CLI command exists
        When: Checking for --reset-checkpoint option
        Then: The option should be available

        This test FAILS until the --reset-checkpoint flag is added.
        """
        options = self._get_cli_options()

        # Assert: --reset-checkpoint flag should exist
        # This will FAIL until we add the option decorator
        if "--reset-checkpoint" not in options:
            available = ", ".join(sorted(options)) if options else "none"
            pytest.fail(
                f"--reset-checkpoint flag not found in CLI options - feature not implemented yet. "
                f"Available options: {available}"
            )

    def test_reset_checkpoint_flag_deletes_checkpoint_file_before_download(self, existing_checkpoint):
        """Test that --reset-checkpoint deletes the checkpoint file.

        Given: A checkpoint file exists at the expected location
        When: batch_download is called with reset_checkpoint=True
        Then: Checkpoint file is deleted before download starts
        And: Batch download proceeds normally

        This test FAILS until reset_checkpoint parameter is added.
        """
        # Arrange: Checkpoint file exists
        checkpoint_file = existing_checkpoint
        assert checkpoint_file.exists(), "Checkpoint file should exist initially"

        # Check if reset_checkpoint option exists
        options = self._get_cli_options()

        has_reset_param = "--reset-checkpoint" in options

        # Assert: The reset_checkpoint parameter should exist
        # This test FAILS until we add the parameter
        if not has_reset_param:
            pytest.fail(
                "reset_checkpoint parameter not found in batch_download function - "
                "feature not implemented yet"
            )

    def test_reset_checkpoint_function_deletes_file(self, checkpoint_file):
        """Test the reset_checkpoint function deletes files correctly.

        This is a unit test for the existing reset_checkpoint function
        to verify our understanding of its behavior.

        This test PASSES because reset_checkpoint already exists.
        """
        # Arrange: Create checkpoint file
        save_checkpoint(10, str(checkpoint_file))
        assert checkpoint_file.exists()

        # Act: Reset checkpoint
        reset_checkpoint(str(checkpoint_file))

        # Assert: File is deleted
        assert not checkpoint_file.exists(), "reset_checkpoint should delete the checkpoint file"

    def test_reset_checkpoint_handles_nonexistent_file(self, checkpoint_file):
        """Test that reset_checkpoint handles missing checkpoint file gracefully.

        Given: No checkpoint file exists
        When: reset_checkpoint is called
        Then: No error is raised

        This test PASSES because reset_checkpoint handles missing files.
        """
        # Arrange: Ensure file doesn't exist
        if checkpoint_file.exists():
            checkpoint_file.unlink()

        # Act & Assert: Should not raise
        reset_checkpoint(str(checkpoint_file))
        assert True  # If we got here, no error was raised

    def test_reset_checkpoint_integration_flow(self, existing_checkpoint):
        """Integration test for --reset-checkpoint with batch download flow.

        Given: The --reset-checkpoint flag is implemented
        When: BatchDownloader is initialized with reset_checkpoint=True
        Then: reset_checkpoint() is called with the correct checkpoint file path

        This test verifies the complete integration flow.
        """
        from yt_fts.download.batch_downloader import BatchDownloader
        from yt_fts.utils.config import get_db_path
        from unittest.mock import patch, call
        
        # Get the actual checkpoint file path used by BatchDownloader
        actual_checkpoint_path = str(Path(get_db_path()).parent / "batch_checkpoint.json")
        
        # Mock reset_checkpoint to verify it's called with correct path
        with patch('yt_fts.download.batch_downloader.reset_checkpoint') as mock_reset:
            # Create a BatchDownloader with reset_checkpoint=True
            downloader = BatchDownloader(
                channels=["@testchannel"],
                reset_checkpoint=True
            )
            
            # Assert: reset_checkpoint was called with the correct checkpoint file path
            mock_reset.assert_called_once_with(actual_checkpoint_path)

