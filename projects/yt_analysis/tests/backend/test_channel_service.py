import json
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from src.backend_engine.persistence.models.channel import Channel as DBChannel
from src.backend_engine.persistence.repositories.category_repository import (
    CategoryRepository,
)
from src.backend_engine.persistence.repositories.channel_repository import (
    ChannelRepository,
)
from src.backend_engine.services.channel_service import ChannelService


@pytest.fixture
def mock_db_session():
    return MagicMock()


@pytest.fixture
def mock_channel_repository():
    # Mock the class itself, so we can mock its methods on instances
    return MagicMock(spec=ChannelRepository)


@pytest.fixture
def mock_category_repository():
    # Mock the class itself
    return MagicMock(spec=CategoryRepository)


@pytest.fixture
def channel_service(mock_db_session, mock_channel_repository, mock_category_repository):
    # Inject the mocked repositories into the service
    service = ChannelService(mock_db_session)
    service.channel_repo = mock_channel_repository
    service.category_repo = mock_category_repository
    return service


def test_validate_url_valid(channel_service):
    assert (
        channel_service.validate_url(
            "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        )
        is True
    )
    assert channel_service.validate_url("https://www.youtube.com/c/Google") is True
    assert channel_service.validate_url("https://www.youtube.com/user/YouTube") is True
    assert (
        channel_service.validate_url("https://youtu.be/abcdefg1234") is True
    )  # This is a video URL, but the regex allows it for now.


def test_validate_url_invalid(channel_service):
    assert channel_service.validate_url("invalid-url") is False
    assert channel_service.validate_url("https://www.google.com") is False
    assert (
        channel_service.validate_url(
            "https://www.youtube.com/not-a-channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        )
        is False
    )


def test_add_channel_success(
    channel_service, mock_channel_repository, mock_category_repository
):
    # Configure mocks
    mock_channel_repository.get_channel_by_id.return_value = None
    mock_category_repository.get_category_by_name.return_value = (
        MagicMock()
    )  # Category exists

    # Mock the create_channel to return a DBChannel instance with a date_added_to_ytap
    def mock_create_channel(db_channel_instance):
        db_channel_instance.date_added_to_ytap = datetime.now(
            UTC
        )  # Simulate DB setting default
        return db_channel_instance

    mock_channel_repository.create_channel.side_effect = mock_create_channel

    channel_url = "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    categories = ["Health", "Learning"]

    # Call the service method
    new_channel = channel_service.add_channel(channel_url, categories)

    # Assertions
    assert new_channel.channel_id == "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    assert new_channel.channel_name == "Mock Channel Name for UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    assert new_channel.channel_url == channel_url
    assert new_channel.assigned_categories == categories
    assert isinstance(new_channel.date_added_to_ytap, datetime)
    mock_channel_repository.create_channel.assert_called_once()
    mock_channel_repository.get_channel_by_id.assert_called_once_with(
        "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    )
    mock_category_repository.get_category_by_name.assert_any_call("Health")
    mock_category_repository.get_category_by_name.assert_any_call("Learning")


def test_add_channel_invalid_url(channel_service):
    with pytest.raises(ValueError, match="Invalid YouTube channel URL provided."):
        channel_service.add_channel("invalid-youtube-url", ["Health"])


def test_add_channel_already_exists(
    channel_service, mock_channel_repository, mock_category_repository
):
    mock_channel_repository.get_channel_by_id.return_value = DBChannel(
        channel_id="UC-lHJZR3Gqxm24_Vd_AJ5Yw",
        channel_name="Existing Channel",
        channel_url="https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw",
        assigned_categories=json.dumps(["Health"]),
        date_added_to_ytap=datetime.now(UTC),
    )
    mock_category_repository.get_category_by_name.return_value = MagicMock()

    with pytest.raises(
        ValueError, match="Channel with ID 'UC-lHJZR3Gqxm24_Vd_AJ5Yw' already exists."
    ):
        channel_service.add_channel(
            "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw", ["Health"]
        )


def test_add_channel_category_not_found(
    channel_service, mock_channel_repository, mock_category_repository
):
    mock_channel_repository.get_channel_by_id.return_value = None
    mock_category_repository.get_category_by_name.return_value = (
        None  # Category does not exist
    )

    with pytest.raises(
        ValueError, match="Category 'NonExistentCategory' does not exist."
    ):
        channel_service.add_channel(
            "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw",
            ["NonExistentCategory"],
        )
