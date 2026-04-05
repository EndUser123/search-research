from pathlib import Path
from unittest.mock import MagicMock

import pytest
from yt_sync.quality_checker import VideoQualityChecker


@pytest.fixture
def mock_args():
    """Fixture for mock argparse.Namespace."""
    args = MagicMock()
    args.quality_management = {
        "enable_quality_upgrade": True,
        "minimum_height": 720,
        "upgrade_batch_size": 10,  # This value is now ignored by the code, but we test against it
    }
    return args


def create_mock_video_file(mocker, path, name, video_id, size=1024 * 1024):
    """Helper to create a mock video file Path object."""
    file_mock = MagicMock(spec=Path)
    file_mock.is_file.return_value = True
    # Ensure the video_id is 11 characters to match the regex in get_id_from_filename
    file_mock.name = f"{name} [{video_id}].mp4"
    file_mock.stat.return_value.st_size = size
    return file_mock


def test_check_for_upgrade_candidates_no_batch_limit(mocker, mock_args):
    """
    Tests that check_for_upgrade_candidates finds ALL candidates and is not limited by the old batch size.
    """
    # 1. SETUP
    # Mock external dependencies (filesystem and ffprobe)
    mocker.patch("shutil.which", return_value="ffprobe")  # ffprobe is available
    mock_get_video_files = mocker.patch("yt_sync.utils.get_video_files_in_dir")

    # Create 15 mock video files, all of which will be low quality
    # Use realistic 11-character IDs
    mock_files = [
        create_mock_video_file(mocker, Path("/fake/dir"), f"vid_{i}", f"id_{i:08d}")
        for i in range(15)
    ]
    mock_get_video_files.return_value = mock_files

    # Mock the quality checker's internal method to always return low quality (480p)
    mock_get_quality = mocker.patch(
        "yt_sync.quality_checker.VideoQualityChecker._get_video_quality",
        return_value={"height": 480},
    )

    # The set of all video IDs that exist for the channel
    all_channel_ids = {f"id_{i:08d}" for i in range(15)}

    # 2. EXECUTION
    checker = VideoQualityChecker(
        mock_args, Path("/fake/dir"), Path("/fake/archive.txt")
    )
    upgrade_candidates, _ = checker.check_for_upgrade_candidates(all_channel_ids)

    # 3. ASSERTION
    # The core of the test: assert that all 15 candidates were found, not just 10.
    assert len(upgrade_candidates) == 15
    assert mock_get_quality.call_count == 15
    assert sorted(upgrade_candidates) == sorted(list(all_channel_ids))


def test_check_for_upgrade_candidates_corrupted_file(mocker, mock_args):
    """
    Tests that a corrupted file (ffprobe returns None) is correctly identified as an upgrade candidate.
    """
    mocker.patch("shutil.which", return_value="ffprobe")
    corrupt_id = "corrupt_id1"
    mocker.patch(
        "yt_sync.utils.get_video_files_in_dir",
        return_value=[
            create_mock_video_file(mocker, Path("/fake/dir"), "corrupt_vid", corrupt_id)
        ],
    )
    # Mock ffprobe failing by returning None
    mocker.patch(
        "yt_sync.quality_checker.VideoQualityChecker._get_video_quality",
        return_value=None,
    )

    checker = VideoQualityChecker(
        mock_args, Path("/fake/dir"), Path("/fake/archive.txt")
    )
    upgrade_candidates, _ = checker.check_for_upgrade_candidates({corrupt_id})

    assert len(upgrade_candidates) == 1
    assert upgrade_candidates[0] == corrupt_id
