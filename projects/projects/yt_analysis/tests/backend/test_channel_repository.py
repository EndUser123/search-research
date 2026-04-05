from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session
from src.backend_engine.persistence.models.channel import Channel, Video
from src.backend_engine.persistence.repositories.channel_repository import (
    ChannelRepository,
    VideoRepository,
)


@pytest.fixture
def mock_db_session():
    """Fixture to provide a mocked SQLAlchemy session."""
    return MagicMock(spec=Session)


@pytest.fixture
def channel_repository(mock_db_session):
    """Fixture to provide a ChannelRepository instance with a mocked session."""
    return ChannelRepository(mock_db_session)


@pytest.fixture
def video_repository(mock_db_session):
    """Fixture to provide a VideoRepository instance with a mocked session."""
    return VideoRepository(mock_db_session)


def test_create_channel(channel_repository, mock_db_session):
    """Test creating a new channel."""
    channel_data = {
        "channel_id": "UC_test_channel",
        "channel_name": "Test Channel",
        "channel_url": "http://example.com/channel",
        "assigned_categories": "[]",
        "upload_playlist_id": "PL_test_playlist",
        "last_scanned_date": None,
        "date_added_to_ytap": None,
    }
    channel = channel_repository.create_channel(Channel(**channel_data))

    assert isinstance(channel, Channel)
    assert channel.channel_id == channel_data["channel_id"]
    assert channel.channel_name == channel_data["channel_name"]
    assert channel.channel_url == channel_data["channel_url"]
    assert channel.assigned_categories == channel_data["assigned_categories"]
    mock_db_session.add.assert_called_once_with(channel)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(channel)


def test_get_channel_by_id(channel_repository, mock_db_session):
    """Test retrieving a channel by its ID."""
    channel_id = "UC_existing_channel"
    mock_channel = Channel(
        channel_id=channel_id,
        channel_name="Existing Channel",
        channel_url="http://example.com/existing",
        assigned_categories="[]",
    )
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
        mock_channel
    )

    found_channel = channel_repository.get_channel_by_id(channel_id)

    assert found_channel == mock_channel
    mock_db_session.query.assert_called_once_with(Channel)
    mock_db_session.query.return_value.filter_by.assert_called_once_with(
        channel_id=channel_id
    )


def test_get_channel_by_id_not_found(channel_repository, mock_db_session):
    """Test retrieving a non-existent channel by its ID."""
    channel_id = "UC_non_existent"
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

    found_channel = channel_repository.get_channel_by_id(channel_id)

    assert found_channel is None


def test_get_all_channels(channel_repository, mock_db_session):
    """Test retrieving all channels."""
    mock_channels = [
        Channel(
            channel_id="UC1",
            channel_name="Channel 1",
            channel_url="http://example.com/1",
            assigned_categories="[]",
        ),
        Channel(
            channel_id="UC2",
            channel_name="Channel 2",
            channel_url="http://example.com/2",
            assigned_categories="[]",
        ),
    ]
    mock_db_session.query.return_value.all.return_value = mock_channels

    all_channels = channel_repository.get_all_channels()

    assert all_channels == mock_channels
    mock_db_session.query.assert_called_once_with(Channel)


def test_delete_channel(channel_repository, mock_db_session):
    """Test deleting a channel."""
    channel_id = "UC_delete_channel"
    mock_channel = Channel(
        channel_id=channel_id,
        channel_name="Channel to Delete",
        channel_url="http://delete.com",
        assigned_categories="[]",
    )
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
        mock_channel
    )

    deleted = channel_repository.delete_channel(channel_id)

    assert deleted is True
    mock_db_session.delete.assert_called_once_with(mock_channel)
    mock_db_session.commit.assert_called_once()


def test_delete_channel_not_found(channel_repository, mock_db_session):
    """Test deleting a non-existent channel."""
    channel_id = "UC_non_existent_delete"
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

    deleted = channel_repository.delete_channel(channel_id)

    assert deleted is False
    mock_db_session.delete.assert_not_called()
    mock_db_session.commit.assert_not_called()


def test_create_video(video_repository, mock_db_session):
    """Test creating a new video."""
    video_data = {
        "video_id": "test_video_id",
        "channel_id": "UC_test_channel",
        "video_title": "Test Video",
        "video_url": "http://example.com/video",
        "publication_date": None,
        "duration": "PT10M",
        "view_count": 1000,
        "transcript_status": "pending",
        "transcript_source": None,
        "transcript_file_path": None,
        "automated_quality_indicators": "[]",
        "manual_quality_flag": None,
        "manual_quality_note": None,
        "date_added_to_ytap": None,
        "last_processed_date": None,
        "assigned_categories": "[]",
    }
    video = video_repository.create_video(Video(**video_data))

    assert isinstance(video, Video)
    assert video.video_id == video_data["video_id"]
    assert video.channel_id == video_data["channel_id"]
    assert video.video_title == video_data["video_title"]
    assert video.video_url == video_data["video_url"]
    mock_db_session.add.assert_called_once_with(video)
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(video)


def test_get_video_by_id(video_repository, mock_db_session):
    """Test retrieving a video by its ID."""
    video_id = "existing_video_id"
    mock_video = Video(
        video_id=video_id,
        channel_id="UC_channel",
        video_title="Existing Video",
        video_url="http://example.com/existing_video",
        transcript_status="completed",
        assigned_categories="[]",
    )
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
        mock_video
    )

    found_video = video_repository.get_video_by_id(video_id)

    assert found_video == mock_video
    mock_db_session.query.assert_called_once_with(Video)
    mock_db_session.query.return_value.filter_by.assert_called_once_with(
        video_id=video_id
    )


def test_get_video_by_id_not_found(video_repository, mock_db_session):
    """Test retrieving a non-existent video by its ID."""
    video_id = "non_existent_video_id"
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

    found_video = video_repository.get_video_by_id(video_id)

    assert found_video is None


def test_get_videos_for_channel(video_repository, mock_db_session):
    """Test retrieving videos for a specific channel."""
    channel_id = "UC_channel_with_videos"
    mock_videos = [
        Video(
            video_id="v1",
            channel_id=channel_id,
            video_title="Video 1",
            video_url="http://v1.com",
            transcript_status="pending",
            assigned_categories="[]",
        ),
        Video(
            video_id="v2",
            channel_id=channel_id,
            video_title="Video 2",
            video_url="http://v2.com",
            transcript_status="completed",
            assigned_categories="[]",
        ),
    ]
    mock_db_session.query.return_value.filter_by.return_value.all.return_value = (
        mock_videos
    )

    channel_videos = video_repository.get_videos_by_channel_id(channel_id)

    assert channel_videos == mock_videos
    mock_db_session.query.assert_called_once_with(Video)
    mock_db_session.query.return_value.filter_by.assert_called_once_with(
        channel_id=channel_id
    )


def test_delete_video(video_repository, mock_db_session):
    """Test deleting a video."""
    video_id = "video_to_delete"
    mock_video = Video(
        video_id=video_id,
        channel_id="UC_channel",
        video_title="Video to Delete",
        video_url="http://delete.com",
        transcript_status="completed",
        assigned_categories="[]",
    )
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = (
        mock_video
    )

    deleted = video_repository.delete_video(video_id)

    assert deleted is True
    mock_db_session.delete.assert_called_once_with(mock_video)
    mock_db_session.commit.assert_called_once()


def test_delete_video_not_found(video_repository, mock_db_session):
    """Test deleting a non-existent video."""
    video_id = "non_existent_video_delete"
    mock_db_session.query.return_value.filter_by.return_value.first.return_value = None

    deleted = video_repository.delete_video(video_id)

    assert deleted is False
    mock_db_session.delete.assert_not_called()
    mock_db_session.commit.assert_not_called()
