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
    mock.should_include = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_discoverer():
    mock = MagicMock(spec=VideoDiscoverer)
    mock.get_video_ids_from_playlist = MagicMock(return_value=[])
    return mock


@pytest.fixture
def auditor(mock_args, mock_metadata_manager, mock_filterer, mock_discoverer):
    return Auditor(
        mock_args,
        Path("/tmp"),
        Path("/tmp/archive.txt"),
        mock_metadata_manager,
        mock_filterer,
        mock_discoverer,
        "uploads_playlist_id",
    )


def test_read_archive_file_no_file(auditor):
    # Arrange
    with patch.object(Path, "is_file", return_value=False):
        # Act
        result = auditor.read_archive_file()

        # Assert
        assert result == set()


def test_read_archive_file_empty(auditor):
    # Arrange
    m = mock_open(read_data="")
    with patch.object(Path, "is_file", return_value=True):
        with patch("builtins.open", m):
            # Act
            result = auditor.read_archive_file()

            # Assert
            assert result == set()


def test_read_archive_file_with_content(auditor):
    # Arrange
    mock_content = "youtube 12345678901\nyoutube 98765432109\n"
    m = mock_open(read_data=mock_content)
    with patch.object(Path, "is_file", return_value=True):
        with patch("builtins.open", m):
            # Act
            result = auditor.read_archive_file()

            # Assert
            assert result == {"12345678901", "98765432109"}


def test_read_archive_file_error(auditor):
    # Arrange
    with patch.object(Path, "is_file", return_value=True):
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            # Act
            result = auditor.read_archive_file()

            # Assert
            assert result == set()


def test_find_and_remove_ghost_entries_no_ghosts(auditor):
    # Arrange
    with patch.object(auditor, "read_archive_file", return_value={"123", "456"}):
        with patch.object(
            utils,
            "get_video_files_in_dir",
            return_value=[Path("video_123.mp4"), Path("video_456.mkv")],
        ):
            with patch.object(
                utils,
                "get_id_from_filename",
                side_effect=lambda x: "123" if "123" in x else "456",
            ):
                # Act
                result = auditor.find_and_remove_ghost_entries()

                # Assert
                assert result == 0


def test_find_and_remove_ghost_entries_with_ghosts(auditor):
    # Arrange
    mock_archive_ids = {"123", "456", "789"}  # 789 is a ghost

    with patch.object(auditor, "read_archive_file", return_value=mock_archive_ids):
        with patch.object(
            utils,
            "get_video_files_in_dir",
            return_value=[Path("video_123.mp4"), Path("video_456.mkv")],
        ):
            with patch.object(
                utils,
                "get_id_from_filename",
                side_effect=lambda x: "123" if "123" in x else "456",
            ):
                with patch("builtins.open", mock_open()) as mo:
                    # Act
                    result = auditor.find_and_remove_ghost_entries()

                    # Assert
                    assert result == 1
                    # Check that the archive was rewritten without the ghost ID
                    mo.assert_called_once()
                    written_content = mo().write.call_args_list[0][0][0]
                    assert "789" not in written_content


def test_find_and_remove_ghost_entries_multiple_ghosts(auditor):
    # Arrange
    mock_archive_ids = {"123", "456", "789", "abc", "def"}  # 3 ghosts

    with patch.object(auditor, "read_archive_file", return_value=mock_archive_ids):
        with patch.object(
            utils,
            "get_video_files_in_dir",
            return_value=[Path("video_123.mp4"), Path("video_456.mkv")],
        ):
            with patch.object(
                utils,
                "get_id_from_filename",
                side_effect=lambda x: "123" if "123" in x else "456",
            ):
                with patch("builtins.open", mock_open()) as mo:
                    # Act
                    result = auditor.find_and_remove_ghost_entries()

                    # Assert
                    assert result == 3
                    mo.assert_called_once()
                    written_content = mo().write.call_args_list[0][0][0]
                    assert all(
                        ghost not in written_content for ghost in ["789", "abc", "def"]
                    )


def test_find_and_remove_ghost_entries_empty_archive(auditor):
    # Arrange
    with patch.object(auditor, "read_archive_file", return_value=set()):
        with patch.object(
            utils, "get_video_files_in_dir", return_value=[Path("video_123.mp4")]
        ):
            # Act
            result = auditor.find_and_remove_ghost_entries()

            # Assert
            assert result == 0


def test_find_and_remove_ghost_entries_rewrite_error(auditor):
    # Arrange
    mock_archive_ids = {"123", "456", "789"}  # 789 is a ghost

    with patch.object(auditor, "read_archive_file", return_value=mock_archive_ids):
        with patch.object(
            utils,
            "get_video_files_in_dir",
            return_value=[Path("video_123.mp4"), Path("video_456.mkv")],
        ):
            with patch.object(
                utils,
                "get_id_from_filename",
                side_effect=lambda x: "123" if "123" in x else "456",
            ):
                with patch("builtins.open", side_effect=OSError("Permission denied")):
                    # Act
                    result = auditor.find_and_remove_ghost_entries()

                    # Assert
                    assert result == 0


def test_run_audit_full_flow(auditor):
    # Arrange
    mock_archive_ids = {"123", "456"}
    mock_unmanaged_files = [Path("unmanaged1.mp4")]

    with patch.object(
        auditor,
        "run_file_system_audit",
        return_value=(mock_archive_ids, mock_unmanaged_files),
    ):
        # Act
        result = auditor.run_audit()

        # Assert
        assert isinstance(result, dict)
        assert "file_system" in result
        assert "filter_mismatches" in result
        assert "unmanaged_files" in result
        assert result["file_system"]["archived_ids"] == mock_archive_ids
        assert result["file_system"]["unmanaged_files"] == mock_unmanaged_files


def test_run_audit_no_unmanaged_files(auditor):
    # Arrange
    mock_archive_ids = {"123", "456"}
    mock_unmanaged_files = []

    with patch.object(
        auditor,
        "run_file_system_audit",
        return_value=(mock_archive_ids, mock_unmanaged_files),
    ):
        # Act
        result = auditor.run_audit()

        # Assert
        assert isinstance(result, dict)
        assert "file_system" in result
        assert result["file_system"]["archived_ids"] == mock_archive_ids
        assert result["file_system"]["unmanaged_files"] == []


def test_auto_import_existing_files_no_new_files(auditor):
    # Arrange
    existing_ids = {"123", "456"}
    mock_files = [Path("video_123.mp4"), Path("video_456.mkv")]

    with patch.object(auditor, "read_archive_file", return_value=existing_ids):
        with patch.object(utils, "get_video_files_in_dir", return_value=mock_files):
            with patch.object(
                utils,
                "get_id_from_filename",
                side_effect=lambda x: "123" if "123" in x else "456",
            ):
                # Act
                result = auditor.auto_import_existing_files()

                # Assert
                assert result == 0


def test_auto_import_existing_files_with_new_files(auditor):
    # Arrange
    existing_ids = {"123", "456"}
    mock_files = [
        Path("video_123.mp4"),  # Already in archive
        Path("video_456.mkv"),  # Already in archive
        Path("video_789.mp4"),  # New file to import
    ]

    with patch.object(auditor, "read_archive_file", return_value=existing_ids):
        with patch.object(utils, "get_video_files_in_dir", return_value=mock_files):
            with patch.object(
                utils,
                "get_id_from_filename",
                side_effect=lambda x: "123"
                if "123" in x
                else "456"
                if "456" in x
                else "789",
            ):
                with patch("builtins.open", mock_open()) as mo:
                    # Mock the Path objects to avoid file system access
                    mock_path_789 = MagicMock(spec=Path)
                    mock_path_789.name = "video_789.mp4"
                    mock_path_789.exists.return_value = True
                    mock_path_789.is_file.return_value = True
                    mock_path_789.stat.return_value = MagicMock(st_size=1000)

                    # Replace the real Path object with our mock for the specific file
                    with patch(
                        "pathlib.Path",
                        side_effect=[
                            Path("video_123.mp4"),
                            Path("video_456.mkv"),
                            mock_path_789,
                        ],
                    ):
                        # Mock the utils.get_video_files_in_dir to return our mock files
                        with patch.object(
                            utils,
                            "get_video_files_in_dir",
                            return_value=[mock_path_789],
                        ):
                            # Act
                            result = auditor.auto_import_existing_files()

                            # Assert
                            assert result == 1
                            # Check that the new ID was added to the archive
                            mo.assert_called_once()
                            written_content = mo().write.call_args_list[0][0][0]
                            assert "789" in written_content


def test_audit_filter_mismatches_no_filterer(auditor):
    # Arrange
    auditor.filterer = None
    test_ids = {"123", "456"}

    # Act
    result = auditor._audit_filter_mismatches(test_ids)

    # Assert
    assert result["status"] == "no_filterer_configured"


def test_audit_filter_mismatches_all_valid(auditor, mock_filterer):
    # Arrange
    test_ids = {"123", "456"}
    mock_filterer.should_include.side_effect = lambda x: True
    auditor.discoverer = None  # Skip playlist check

    # Act
    result = auditor._audit_filter_mismatches(test_ids)

    # Assert
    assert result["counts"]["in_archive_but_filtered"] == 0
    assert result["counts"]["passed_filters_but_missing"] == 0


def test_audit_filter_mismatches_invalid_in_archive(auditor, mock_filterer):
    # Arrange
    test_ids = {"123", "456"}
    mock_filterer.should_include.side_effect = (
        lambda x: x == "123"
    )  # Only 123 passes filter

    # Act
    result = auditor._audit_filter_mismatches(test_ids)

    # Assert
    assert result["counts"]["in_archive_but_filtered"] == 1
    assert "456" in result["details"]["in_archive_but_filtered"]


def test_audit_filter_mismatches_missing_from_archive(
    auditor, mock_filterer, mock_discoverer
):
    # Arrange
    test_ids = {"123"}  # Only 123 in archive
    mock_filterer.should_include.side_effect = lambda x: True  # All pass filter
    mock_discoverer.get_video_ids_from_playlist.return_value = [
        "123",
        "456",
    ]  # 456 is missing from archive

    # Act
    result = auditor._audit_filter_mismatches(test_ids)

    # Assert
    assert result["counts"]["passed_filters_but_missing"] == 1
    assert "456" in result["details"]["passed_filters_but_missing"]


def test_audit_filter_mismatches_discovery_error(
    auditor, mock_filterer, mock_discoverer
):
    # Arrange
    test_ids = {"123"}
    mock_filterer.should_include.side_effect = lambda x: True
    mock_discoverer.get_video_ids_from_playlist.side_effect = Exception("API error")

    # Act
    result = auditor._audit_filter_mismatches(test_ids)

    # Assert
    assert len(result["details"]["errors"]) == 1
    assert "API error" in result["details"]["errors"][0]


def test_auto_import_existing_files_archive_write_error(auditor):
    # Arrange
    mock_archive_ids = {"123"}
    mock_files = [Path("video_456.mp4")]

    with patch.object(auditor, "read_archive_file", return_value=mock_archive_ids):
        with patch.object(utils, "get_video_files_in_dir", return_value=mock_files):
            with patch.object(utils, "get_id_from_filename", return_value="456"):
                with patch("builtins.open", side_effect=OSError("Permission denied")):
                    # Act
                    result = auditor.auto_import_existing_files()

                    # Assert
                    assert result == 0


def test_fix_unmanaged_files_add_to_archive(auditor):
    # Arrange
    unmanaged_file = Path("video_123.mp4")
    with patch.object(utils, "get_id_from_filename", return_value="123"):
        with patch("builtins.open", mock_open()):
            # Act
            result = auditor._fix_unmanaged_files([unmanaged_file])

            # Assert
            assert isinstance(result, dict)
            assert "added_to_archive" in result
            assert result["added_to_archive"] == 1


def test_fix_unmanaged_files_empty_list(auditor):
    # Arrange
    unmanaged_files = []

    # Act
    result = auditor._fix_unmanaged_files(unmanaged_files)

    # Assert
    assert isinstance(result, dict)
    assert result == {"status": "no_unmanaged_files"}


def test_fix_unmanaged_files_error_handling(auditor):
    # Arrange
    unmanaged_file = Path("corrupt.mp4")
    with patch.object(
        utils, "get_id_from_filename", side_effect=Exception("Test error")
    ):
        # Act
        result = auditor._fix_unmanaged_files([unmanaged_file])

        # Assert
        assert result == {"deleted": 0, "quarantined": 0, "added_to_archive": 0}
