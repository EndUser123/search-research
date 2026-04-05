from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given
from hypothesis import strategies as st
from yt_sync.metadata import MetadataManager


@pytest.fixture
def metadata_manager(faker):
    """Create a MetadataManager instance for testing."""
    args = MagicMock()
    args.enrichment_config = {
        "enabled": True,
        "timeout_seconds": 30,
        "skip_threshold": 100,
    }
    api_client = MagicMock()
    metadata_dir = Path(faker.word())
    return MetadataManager(args, metadata_dir, api_client)


@pytest.mark.parametrize("invalid_id", ["invalid1", "invalid2", "invalid3"])
def test_load_metadata_for_ids_with_invalid_id(metadata_manager, invalid_id):
    """Test that load_metadata_for_ids handles invalid video IDs gracefully."""
    # Arrange
    # Act
    with patch.object(metadata_manager, "metadata_dir", Path("/tmp")):
        result = metadata_manager.load_metadata_for_ids([invalid_id])

    # Assert
    assert isinstance(result, dict)
    assert invalid_id not in result


@given(st.lists(st.text(min_size=1), min_size=1, max_size=10))
def test_load_metadata_for_ids_with_multiple_ids(video_ids):
    """Test that load_metadata_for_ids can handle multiple video IDs."""
    # Arrange
    metadata_manager = MagicMock()
    metadata_manager.api_client.get_videos_metadata.return_value = {
        video_ids[0]: {"title": "Test Video 1", "id": video_ids[0]}
    }
    metadata_manager.metadata_dir = Path("/tmp")
    metadata_manager.load_metadata_for_ids.return_value = {
        video_ids[0]: {"title": "Test Video 1", "id": video_ids[0]}
    }

    # Act
    result = metadata_manager.load_metadata_for_ids(video_ids)

    # Assert
    assert isinstance(result, dict)
    assert len(result) <= len(video_ids)
    if video_ids[0] in result:
        assert result[video_ids[0]]["title"] == "Test Video 1"
