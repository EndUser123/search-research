"""
Tests for channel URL deduplication in add_channel_info.

Bug: add_channel_info allows duplicate channel_url entries when called with
different channel_id values, creating duplicate rows in the Channels table.

Expected behavior:
- add_channel_info should check if channel_url already exists
- If URL exists with different channel_id, update existing row instead of inserting
- No duplicate channel_url entries should exist in database
"""

import pytest

from yt_fts.db.channels import add_channel_info
from yt_fts.db.infra import get_db_connection


class TestChannelUrlDeduplication:
    """Test that add_channel_info prevents duplicate channel_url entries."""

    def test_add_channel_info_prevents_duplicate_urls(self):
        """
        Test that add_channel_info does not create duplicate channel_url entries.
        
        Given: A channel is added with channel_url
        When: The same URL is added again with a different channel_id
        Then: Should update existing row, NOT create a duplicate
        
        This catches the bug where multiple rows with the same channel_url
        but different channel_id values are created.
        """
        import time
        timestamp = int(time.time() * 1000)
        
        # Use unique URLs to avoid test pollution
        test_url = f"https://www.youtube.com/@dedup_test_{timestamp}"
        
        with get_db_connection() as conn:
            # Clean up any existing test data first
            conn.execute(
                "DELETE FROM Channels WHERE channel_url LIKE ?",
                (f"%@dedup_test_{timestamp}%",)
            )
            conn.commit()
            
            # Add a channel with specific URL
            add_channel_info(
                channel_id=f"UC_test_1_{timestamp}",
                channel_name="Test Channel 1",
                channel_url=test_url
            )
            
            # Verify it was added (exactly 1 row)
            count = conn.execute(
                "SELECT COUNT(*) FROM Channels WHERE channel_url = ?",
                (test_url,)
            ).fetchone()[0]
            
            assert count == 1, f"First insert should create 1 row, found {count}"
            
            # Try to add same URL with different channel_id (this should NOT create duplicate)
            add_channel_info(
                channel_id=f"UC_test_2_{timestamp}",  # Different channel_id
                channel_name="Test Channel 2",
                channel_url=test_url  # Same URL
            )
            
            # Check if duplicate was created
            rows_with_url = conn.execute(
                "SELECT COUNT(*) FROM Channels WHERE channel_url = ?",
                (test_url,)
            ).fetchone()[0]
            
            # BUG: Currently creates 2 rows, should only have 1
            assert rows_with_url == 1, \
                f"Should have exactly 1 row with this URL, but found {rows_with_url}"
            
            # Verify the existing row was updated (name changed)
            channel_name = conn.execute(
                "SELECT channel_name FROM Channels WHERE channel_url = ?",
                (test_url,)
            ).fetchone()[0]
            
            # The name should be updated to the latest one
            assert channel_name == "Test Channel 2", \
                f"Channel name should be updated, got {channel_name}"
            
            # Clean up
            conn.execute(
                "DELETE FROM Channels WHERE channel_url LIKE ?",
                (f"%@dedup_test_{timestamp}%",)
            )
            conn.commit()

    def test_add_channel_info_with_videos_suffix_variant(self):
        """
        Test that add_channel_info handles /videos suffix variants correctly.
        
        Given: A channel exists with URL "https://www.youtube.com/@test"
        When: Adding with "https://www.youtube.com/@test/videos"
        Then: Should recognize as duplicate and update existing row
        """
        import time
        timestamp = int(time.time() * 1000)
        test_url = f"https://www.youtube.com/@suffix_test_{timestamp}"
        
        with get_db_connection() as conn:
            # Clean up first
            conn.execute(
                "DELETE FROM Channels WHERE channel_url LIKE ?",
                (f"%@suffix_test_{timestamp}%",)
            )
            conn.commit()
            
            # Add initial channel
            add_channel_info(
                channel_id=f"UC_suffix_1_{timestamp}",
                channel_name="Suffix Test",
                channel_url=test_url
            )
            
            # Try to add with /videos suffix
            add_channel_info(
                channel_id=f"UC_suffix_2_{timestamp}",
                channel_name="Suffix Test 2",
                channel_url=f"{test_url}/videos"
            )
            
            # Should only have 1 row (both variants map to same channel)
            count = conn.execute(
                "SELECT COUNT(*) FROM Channels WHERE channel_url = ? OR channel_url = ?",
                (test_url, f"{test_url}/videos")
            ).fetchone()[0]
            
            assert count == 1, \
                f"Should have 1 row for both /videos and non-/videos variants, found {count}"
            
            # Clean up
            conn.execute(
                "DELETE FROM Channels WHERE channel_url LIKE ?",
                (f"%@suffix_test_{timestamp}%",)
            )
            conn.commit()
