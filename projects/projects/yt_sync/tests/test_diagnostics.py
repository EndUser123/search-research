import subprocess
from unittest.mock import patch

import pytest
from yt_sync.diagnostics import RestrictedVideoFinder, find_ytdlp_executable


@pytest.fixture
def finder():
    """Fixture to create a RestrictedVideoFinder instance with mocked dependencies."""
    return RestrictedVideoFinder(
        channel_urls=["https://www.youtube.com/channel/UCXIJgqnII2ZOINSWNOGFThA"]
    )


def test_find_ytdlp_executable(mocker):
    """Test the find_ytdlp_executable function to ensure it returns a path or None."""
    mocker.patch("shutil.which", return_value="path/to/yt-dlp")
    result = find_ytdlp_executable()
    assert result is not None

    mocker.patch("shutil.which", return_value=None)
    result = find_ytdlp_executable()
    assert result is not None  # Assuming the function has a fallback to a local path


def test_restricted_video_finder_init():
    """Test initialization of RestrictedVideoFinder with different input types."""
    # Test with single string
    finder_str = RestrictedVideoFinder(
        "https://www.youtube.com/channel/UCXIJgqnII2ZOINSWNOGFThA"
    )
    assert finder_str.channel_urls == [
        "https://www.youtube.com/channel/UCXIJgqnII2ZOINSWNOGFThA"
    ]

    # Test with list of strings
    finder_list = RestrictedVideoFinder(
        ["https://www.youtube.com/channel/UCXIJgqnII2ZOINSWNOGFThA"]
    )
    assert finder_list.channel_urls == [
        "https://www.youtube.com/channel/UCXIJgqnII2ZOINSWNOGFThA"
    ]

    # Test with None
    finder_none = RestrictedVideoFinder()
    assert finder_none.channel_urls == []


@patch("yt_sync.diagnostics.subprocess.run")
def test_run_command_success(mock_run, finder):
    """Test _run_command method with a successful command execution."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["test"], returncode=0, stdout="success", stderr=""
    )
    result = finder._run_command(["test"])
    assert result.returncode == 0
    assert result.stdout == "success"
    mock_run.assert_called_once()


@patch("yt_sync.diagnostics.subprocess.run")
def test_run_command_failure(mock_run, finder):
    """Test _run_command method with a failed command execution."""
    mock_run.side_effect = Exception("Command failed")
    mock_run.return_value = subprocess.CompletedProcess(
        args=["test"], returncode=1, stdout="", stderr="Command failed"
    )
    result = finder._run_command(["test"])
    assert result.returncode == 1
    assert "Command failed" in result.stderr


@patch.object(RestrictedVideoFinder, "_run_command")
def test_is_video_restricted_true(mock_run, finder):
    """Test is_video_restricted method when video is restricted."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["yt-dlp", "--dump-json", "--no-warnings", "video_url"],
        returncode=1,
        stdout="",
        stderr="sign in to confirm your age",
    )
    finder.ytdlp_exec = "yt-dlp"
    result = finder.is_video_restricted("video_url")
    assert result is True


@patch.object(RestrictedVideoFinder, "_run_command")
def test_is_video_restricted_false(mock_run, finder):
    """Test is_video_restricted method when video is not restricted."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["yt-dlp", "--dump-json", "--no-warnings", "video_url"],
        returncode=0,
        stdout="{}",
        stderr="",
    )
    finder.ytdlp_exec = "yt-dlp"
    result = finder.is_video_restricted("video_url")
    assert result is False


@patch.object(RestrictedVideoFinder, "_run_command")
def test_get_video_ids_for_channel_success(mock_run, finder):
    """Test _get_video_ids_for_channel method with successful retrieval of video IDs."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["yt-dlp", "--flat-playlist", "--print", "%(id)s", "channel_url"],
        returncode=0,
        stdout="video1\nvideo2\nvideo3",
        stderr="",
    )
    finder.ytdlp_exec = "yt-dlp"
    result = finder._get_video_ids_for_channel("channel_url")
    assert result == ["video1", "video2", "video3"]


@patch.object(RestrictedVideoFinder, "_run_command")
def test_get_video_ids_for_channel_failure(mock_run, finder):
    """Test _get_video_ids_for_channel method when retrieval fails."""
    mock_run.return_value = subprocess.CompletedProcess(
        args=["yt-dlp", "--flat-playlist", "--print", "%(id)s", "channel_url"],
        returncode=1,
        stdout="",
        stderr="Failed to retrieve video list",
    )
    finder.ytdlp_exec = "yt-dlp"
    result = finder._get_video_ids_for_channel("channel_url")
    assert result is None


@patch.object(RestrictedVideoFinder, "_get_video_ids_for_channel")
@patch.object(RestrictedVideoFinder, "is_video_restricted")
def test_find_first_restricted_video_found(mock_restricted, mock_ids, finder):
    """Test find_first_restricted_video method when a restricted video is found."""
    mock_ids.return_value = ["video1", "video2", "video3"]
    mock_restricted.side_effect = [False, True, False]
    finder.ytdlp_exec = "yt-dlp"
    result = finder.find_first_restricted_video()
    assert result == "https://www.youtube.com/watch?v=video2"


@patch.object(RestrictedVideoFinder, "_get_video_ids_for_channel")
@patch.object(RestrictedVideoFinder, "is_video_restricted")
def test_find_first_restricted_video_not_found(mock_restricted, mock_ids, finder):
    """Test find_first_restricted_video method when no restricted video is found."""
    mock_ids.return_value = ["video1", "video2", "video3"]
    mock_restricted.return_value = False
    finder.ytdlp_exec = "yt-dlp"
    result = finder.find_first_restricted_video()
    assert result is None


@patch.object(RestrictedVideoFinder, "find_first_restricted_video")
def test_run_and_print_found(mock_find, finder):
    """Test run_and_print method when a restricted video is found."""
    mock_find.return_value = "https://www.youtube.com/watch?v=restricted"
    with patch("rich.console.Console.print") as mock_print:
        finder.run_and_print()
        mock_print.assert_called()
        call_args = mock_print.call_args[0][0]
        assert "Restricted Video Found" in call_args.title


@patch.object(RestrictedVideoFinder, "find_first_restricted_video")
def test_run_and_print_not_found(mock_find, finder):
    """Test run_and_print method when no restricted video is found."""
    mock_find.return_value = None
    with patch("rich.console.Console.print") as mock_print:
        finder.run_and_print()
        mock_print.assert_called()
        call_args = mock_print.call_args[0][0]
        assert "No Restricted Videos Found" in call_args.title
