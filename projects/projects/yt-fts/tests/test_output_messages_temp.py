def test_escalate_to_api_when_rss_fails_completely():
    """When RSS fetch fails completely, escalation method should be callable."""
    from unittest.mock import patch, MagicMock
    from yt_fts.services.rss_precheck import RssPreChecker

    checker = RssPreChecker()

    # Mock the API response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "items": [
            {
                "snippet": {
                    "title": "Escalated Channel Name"
                }
            }
        ]
    }

    # Test that escalation method exists and works
    with patch.dict("os.environ", {"YOUTUBE_API_KEY": "test_key"}):
        with patch("requests.get", return_value=mock_response):
            result = checker._escalate_channel_name_via_api("UC1234567890ABCDEFGHIJ")

            # Should return the channel name from API
            assert result == "Escalated Channel Name"
