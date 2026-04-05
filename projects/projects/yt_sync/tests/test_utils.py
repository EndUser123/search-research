import pytest
from yt_sync import utils


def test_sanitize_filename():
    """Test the sanitize_filename function."""
    assert utils.sanitize_filename("A Simple Title") == "A Simple Title"
    assert (
        utils.sanitize_filename('Title with /\\:*?"<>| special chars')
        == "Title with _________ special chars"
    )
    assert (
        utils.sanitize_filename("  Leading and Trailing Spaces  ")
        == "Leading and Trailing Spaces"
    )
    assert (
        utils.sanitize_filename("Multiple   Spaces   Together")
        == "Multiple Spaces Together"
    )
    assert utils.sanitize_filename("") == "untitled"
    assert utils.sanitize_filename("None") == "untitled"


def test_get_id_from_filename():
    """Test the get_id_from_filename function."""
    assert (
        utils.get_id_from_filename("A Normal Video Title [aBcDeFgH123].mp4")
        == "aBcDeFgH123"
    )
    assert (
        utils.get_id_from_filename("Another-Video_Title-Here [a-b_c-d_1-2].mkv")
        == "a-b_c-d_1-2"
    )
    assert utils.get_id_from_filename("No ID in this filename.webm") is None
    assert utils.get_id_from_filename("Malformed ID [12345].mp4") is None
    assert (
        utils.get_id_from_filename("ID at start [aBcDeFgH123] of title.mp4")
        == "aBcDeFgH123"
    )
    assert (
        utils.get_id_from_filename(
            "Brackets in title [but not an id] [aBcDeFgH123].mp4"
        )
        == "aBcDeFgH123"
    )
    assert utils.get_id_from_filename("[aBcDeFgH123]") == "aBcDeFgH123"
    assert utils.get_id_from_filename("") is None


def test_select_best_formats_programmatically():
    """Test the select_best_formats_programmatically function."""
    # Test with valid formats
    valid_formats = [
        {
            "format_id": "248",
            "vcodec": "vp9",
            "height": 1080,
            "width": 1920,
            "acodec": "none",
            "vbr": 5000,
        },
        {"format_id": "251", "acodec": "opus", "vcodec": "none", "abr": 160},
    ]
    result = utils.select_best_formats_programmatically(valid_formats)
    assert result == "248+251"

    # Test with empty list
    with pytest.raises(ValueError, match="Format list is empty."):
        utils.select_best_formats_programmatically([])

    # Test with malformed formats
    malformed_formats = [
        {"format_id": "1", "vcodec": "vp9"},  # Missing height
        {"acodec": "opus"},  # Missing format_id
    ]
    with pytest.raises(ValueError, match="No usable formats found after sanitization."):
        utils.select_best_formats_programmatically(malformed_formats)
