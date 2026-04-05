import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from yt_sync import utils
from yt_sync.auditing import Auditor
from yt_sync.discovery import VideoDiscoverer
from yt_sync.filtering import VideoFilterer
from yt_sync.metadata import MetadataManager


@pytest.fixture
def mock_args():
    return MagicMock()


@pytest.fixture
def mock_metadata_manager():
    return MagicMock(spec=MetadataManager)


@pytest.fixture
def mock_filterer():
    mock = MagicMock(spec=VideoFilterer)
    mock.rules = True
    mock.should_include = MagicMock(
        side_effect=lambda x: x == "123"
    )  # Only include ID "123"
    return mock


@pytest.fixture
def mock_discoverer():
    mock = MagicMock(spec=VideoDiscoverer)
    mock.get_video_ids_from_playlist = MagicMock(return_value=set())
    return mock


@pytest.fixture
def auditor(
    mock_args, mock_metadata_manager, mock_filterer, mock_discoverer, monkeypatch
):
    # Create a temporary directory for testing that will persist for the test
    temp_dir = Path(tempfile.gettempdir()) / "yt_sync_test"
    os.makedirs(temp_dir, exist_ok=True)

    # Create a temporary archive file
    archive_file = temp_dir / "archive.txt"
    with open(archive_file, "w") as f:
        f.write("")

    # Create Auditor with only required params
    auditor = Auditor(mock_args, temp_dir, archive_file)

    # Use monkeypatch to temporarily add mocks for tests that need them
    monkeypatch.setattr(auditor, "metadata_manager", mock_metadata_manager)
    monkeypatch.setattr(auditor, "filterer", mock_filterer)
    monkeypatch.setattr(auditor, "discoverer", mock_discoverer)
    monkeypatch.setattr(auditor, "uploads_playlist_id", "uploads_playlist_id")

    return auditor


def test_run_audit_no_files(auditor):
    # Arrange
    with patch.object(utils, "get_video_files_in_dir", return_value=[]):
        # Act
        auditor.run_audit()
        # Assert - no assertion needed as this is just a smoke test


def test_run_audit_with_files(auditor):
    # Arrange
    mock_files = [Path("video_123.mp4"), Path("video_456.mkv")]
    with patch.object(utils, "get_video_files_in_dir", return_value=mock_files):
        with patch.object(
            utils,
            "get_id_from_filename",
            side_effect=lambda x: "123" if "123" in str(x) else "456",
        ):
            # Act
            auditor.run_audit()
            # Assert - no assertion needed as this is just a smoke test


def test_audit_filter_mismatches_with_mismatches(auditor):
    # Arrange
    mock_archived_ids = {"123", "456"}
    mock_metadata = {"123": {"title": "Test Video"}, "456": {"title": "Another Video"}}
    mock_passed_ids = {"123"}  # 456 is a mismatch

    # Act
    with patch.object(
        auditor.metadata_manager, "load_metadata_for_ids", return_value=mock_metadata
    ):
        with patch.object(
            auditor.filterer, "apply_filters", return_value=mock_passed_ids
        ):
            with patch("yt_sync.auditing.logger.warning") as mock_warning:
                auditor._audit_filter_mismatches(mock_archived_ids)
                # Assert - verify exactly one warning was called with the expected message
                mock_warning.assert_called_once_with("  - MISMATCH: 456")


def test_fix_unmanaged_files_no_files(auditor):
    # Arrange
    with patch.object(auditor, "_fix_unmanaged_files", return_value=0):
        # Act
        auditor.run_audit()
        # Assert - no assertion needed as this is just a smoke test


def test_audit_filter_mismatches_no_ids(auditor):
    # Arrange
    with patch.object(auditor, "_audit_filter_mismatches", return_value=None):
        # Act
        auditor.run_audit()
        # Assert - no assertion needed as this is just a smoke test


def test_find_and_remove_ghost_entries_with_ghosts(auditor):
    # Arrange
    mock_archived_ids = {"123", "456"}
    mock_video_files = [Path("video_123.mp4")]

    with patch.object(auditor, "read_archive_file", return_value=mock_archived_ids):
        with patch.object(
            utils, "get_video_files_in_dir", return_value=mock_video_files
        ):
            with patch.object(
                utils,
                "get_id_from_filename",
                side_effect=lambda x: "123" if "123" in str(x) else None,
            ):
                with patch("yt_sync.auditing.logger.warning") as mock_warning:
                    with patch("builtins.open", mock_open()):
                        # Act
                        result = auditor.find_and_remove_ghost_entries()
                        # Assert
                        assert result == 1
                        mock_warning.assert_called_with(
                            "👻 Found 1 ghost entries in the archive that are missing on disk. Removing them..."
                        )


def test_find_and_remove_ghost_entries_no_ghosts(auditor):
    # Arrange
    mock_archived_ids = {"123"}
    mock_video_files = [Path("video_123.mp4")]

    with patch.object(auditor, "read_archive_file", return_value=mock_archived_ids):
        with patch.object(
            utils, "get_video_files_in_dir", return_value=mock_video_files
        ):
            with patch.object(
                utils,
                "get_id_from_filename",
                side_effect=lambda x: "123" if "123" in str(x) else None,
            ):
                # Act
                result = auditor.find_and_remove_ghost_entries()
                # Assert
                assert result == 0


def test_auto_import_existing_files(auditor, tmp_path):
    # Arrange
    mock_archived_ids = {"123"}
    test_file = tmp_path / "video_456.mkv"
    test_file.write_bytes(b"test video content")  # Create a real file
    mock_video_files = [test_file]  # Use the temp file path
    test_content = "youtube 123\n"
    written_data = []

    def mock_write(data):
        written_data.append(data)

    with patch.object(auditor, "read_archive_file", return_value=mock_archived_ids):
        with patch.object(
            utils, "get_video_files_in_dir", return_value=mock_video_files
        ):
            with patch.object(
                utils,
                "get_id_from_filename",
                side_effect=lambda x: "456" if "456" in str(x) else None,
            ):
                with patch(
                    "builtins.open", mock_open(read_data=test_content)
                ) as mock_open_file:
                    mock_file = mock_open_file.return_value.__enter__.return_value
                    mock_file.write.side_effect = mock_write
                    # Act
                    result = auditor.auto_import_existing_files()
                    # Assert
                    assert result == 1
                    assert "youtube 456\n" in written_data
                    mock_open_file.assert_called_with(
                        auditor.archive_file, "a", encoding="utf-8"
                    )


def test_auto_import_existing_files_no_new_files(auditor):
    # Arrange
    mock_archived_ids = {"123"}
    mock_video_files = [Path("video_123.mp4")]  # 123 is already in archive

    with patch.object(auditor, "read_archive_file", return_value=mock_archived_ids):
        with patch.object(
            utils, "get_video_files_in_dir", return_value=mock_video_files
        ):
            with patch.object(
                utils,
                "get_id_from_filename",
                side_effect=lambda x: "123" if "123" in str(x) else None,
            ):
                # Act
                result = auditor.auto_import_existing_files()
                # Assert
                assert result == 0


def test_read_archive_file(auditor):
    # Arrange
    mock_content = "youtube 123\nyoutube 456"
    with patch("builtins.open", mock_open(read_data=mock_content)):
        # Act
        result = auditor.read_archive_file()
        # Assert
        assert result == {"123", "456"}


def test_read_archive_file_empty(auditor):
    # Arrange
    with patch("builtins.open", mock_open(read_data="")):
        # Act
        result = auditor.read_archive_file()
        # Assert
        assert result == set()


def test_read_archive_file_error(auditor):
    # Arrange
    with patch("builtins.open", side_effect=OSError("Test error")):
        with patch("yt_sync.auditing.logger.error") as mock_error:
            # Act
            result = auditor.read_archive_file()
            # Assert
            assert result == set()
            mock_error.assert_called_with(
                "Error reading archive file %s: Test error" % auditor.archive_file
            )
