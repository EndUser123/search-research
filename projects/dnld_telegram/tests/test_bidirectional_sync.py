"""
TDD Tests for Bidirectional Database-Filesystem Sync

Tests for the missing functionality: Database → Filesystem verification
This addresses the case where database shows "completed" but files are missing/renamed.
"""

# Import the module we'll be testing
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

sys.path.insert(0, "C:/_Python/_Projects/dnld_telegram/src")


class TestBidirectionalSync:
    """TDD tests for bidirectional sync - RED phase first."""

    @pytest.mark.asyncio
    async def test_find_missing_files_from_database_not_implemented(self):
        """RED: Test that find_missing_files_from_database function exists and has correct signature."""
        # This should fail initially because the function doesn't exist
        try:
            # Check function signature
            import inspect

            from dnld_telegram.download.reverse_sync import (
                find_missing_files_from_database,
            )

            sig = inspect.signature(find_missing_files_from_database)
            assert "channel_name" in sig.parameters
            assert "dry_run" in sig.parameters
            assert sig.parameters["dry_run"].default is False
        except ImportError:
            pytest.fail("find_missing_files_from_database function not implemented yet")

    @pytest.mark.asyncio
    async def test_find_file_for_database_record_not_implemented(self):
        """RED: Test that find_file_for_database_record function exists."""
        try:
            import inspect

            from dnld_telegram.download.reverse_sync import (
                find_file_for_database_record,
            )

            sig = inspect.signature(find_file_for_database_record)
            assert "record" in sig.parameters
            assert "media_dir" in sig.parameters
        except ImportError:
            pytest.fail("find_file_for_database_record function not implemented yet")

    def test_files_match_by_size_not_implemented(self):
        """RED: Test that files_match_by_size utility function exists."""
        try:
            import inspect

            from dnld_telegram.download.reverse_sync import files_match_by_size

            sig = inspect.signature(files_match_by_size)
            assert "file_path" in sig.parameters
            assert "expected_size" in sig.parameters
            assert "tolerance" in sig.parameters
            assert sig.parameters["tolerance"].default == 0.02
        except ImportError:
            pytest.fail("files_match_by_size function not implemented yet")

    @pytest.mark.asyncio
    async def test_complete_database_filesystem_sync_not_implemented(self):
        """RED: Test that complete bidirectional sync function exists."""
        try:
            import inspect

            from dnld_telegram.download.reverse_sync import (
                complete_database_filesystem_sync,
            )

            sig = inspect.signature(complete_database_filesystem_sync)
            assert "channel_name" in sig.parameters
            assert "dry_run" in sig.parameters
        except ImportError:
            pytest.fail(
                "complete_database_filesystem_sync function not implemented yet"
            )


class TestFileSizeMatching:
    """TDD tests for file size matching utility."""

    def test_files_match_by_size_exact_match(self):
        """GREEN target: Exact size match should return True."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")  # 12 bytes
            tmp.flush()

            # Once implemented, this should work
            # result = files_match_by_size(Path(tmp.name), 12)
            # assert result is True

            # For now, this will fail - RED phase
            try:
                from dnld_telegram.download.reverse_sync import files_match_by_size

                result = files_match_by_size(Path(tmp.name), 12)
                assert result is True
            except (ImportError, NameError):
                pytest.skip("files_match_by_size not implemented yet")

        Path(tmp.name).unlink()  # cleanup

    def test_files_match_by_size_within_tolerance(self):
        """GREEN target: Size within tolerance should return True."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp.write(b"test content")  # 12 bytes
            tmp.flush()

            try:
                from dnld_telegram.download.reverse_sync import files_match_by_size

                # 11 bytes vs 12 bytes = ~8.3% difference, default tolerance is 2%
                result = files_match_by_size(
                    Path(tmp.name), 11, tolerance=0.1
                )  # 10% tolerance
                assert result is True

                # Should fail with default 2% tolerance
                result = files_match_by_size(Path(tmp.name), 11)  # 2% tolerance
                assert result is False
            except (ImportError, NameError):
                pytest.skip("files_match_by_size not implemented yet")

        Path(tmp.name).unlink()


class TestDatabaseToFilesystemSync:
    """TDD tests for Database → Filesystem direction."""

    @pytest.mark.asyncio
    async def test_find_missing_files_identifies_missing_files(self):
        """GREEN target: Should identify when DB says completed but file is missing."""

        # Mock database storage
        mock_storage = AsyncMock()
        mock_storage.channel_name = "test_channel"
        mock_storage.get_channel_id.return_value = 123

        # Mock database records - DB says these files are completed
        mock_records = [
            {
                "id": 1,
                "telegram_id": 101,
                "filename": "missing_file.mp4",
                "file_size": 1000,
            },
            {
                "id": 2,
                "telegram_id": 102,
                "filename": "existing_file.mp4",
                "file_size": 2000,
            },
        ]

        # Mock media directory
        with tempfile.TemporaryDirectory() as tmp_dir:
            media_dir = Path(tmp_dir)

            # Create only one of the files that DB thinks exists
            (media_dir / "existing_file.mp4").write_bytes(b"x" * 2000)
            # missing_file.mp4 is NOT created - this is the missing file

            with (
                patch(
                    "dnld_telegram.download.reverse_sync.get_storage",
                    return_value=mock_storage,
                ),
                patch(
                    "dnld_telegram.download.reverse_sync.get_channel_media_path",
                    return_value=media_dir,
                ),
                patch(
                    "dnld_telegram.download.reverse_sync.get_connection"
                ) as mock_conn,
            ):
                # Mock database connection
                mock_cursor = AsyncMock()
                mock_cursor.fetchall.return_value = mock_records
                mock_conn_ctx = AsyncMock()
                mock_conn_ctx.__aenter__.return_value.execute.return_value = mock_cursor
                mock_conn.return_value = mock_conn_ctx

                try:
                    from dnld_telegram.download.reverse_sync import (
                        find_missing_files_from_database,
                    )

                    stats, missing_records = await find_missing_files_from_database(
                        "test_channel", dry_run=True
                    )

                    # Should identify 1 missing file
                    assert stats["database_completed"] == 2
                    assert stats["files_missing"] == 1
                    assert len(missing_records) == 1
                    assert missing_records[0]["filename"] == "missing_file.mp4"

                except (ImportError, NameError):
                    pytest.fail(
                        "find_missing_files_from_database not implemented yet - RED phase"
                    )

    @pytest.mark.asyncio
    async def test_find_file_for_database_record_telegram_id_strategy(self):
        """GREEN target: Should find renamed files using telegram_id prefix strategy."""

        with tempfile.TemporaryDirectory() as tmp_dir:
            media_dir = Path(tmp_dir)

            # Create a file with telegram_id prefix
            actual_file = media_dir / "101_video.mp4"
            actual_file.write_bytes(b"x" * 1000)

            # Database record expects different filename
            record = {
                "id": 1,
                "telegram_id": 101,
                "filename": "video.mp4",  # Different from actual filename
                "file_size": 1000,
            }

            try:
                from dnld_telegram.download.reverse_sync import (
                    find_file_for_database_record,
                )

                result = await find_file_for_database_record(record, media_dir)

                assert result is not None
                assert result.name == "101_video.mp4"

            except (ImportError, NameError):
                pytest.fail(
                    "find_file_for_database_record not implemented yet - RED phase"
                )


class TestCompleteBidirectionalSync:
    """TDD tests for complete bidirectional sync."""

    @pytest.mark.asyncio
    async def test_complete_sync_calls_both_directions(self):
        """GREEN target: Should call both file→DB and DB→file sync functions."""

        # Mock both existing and new functions
        with (
            patch(
                "dnld_telegram.download.reverse_sync.sync_channel_database_with_filesystem"
            ) as mock_files_to_db,
            patch(
                "dnld_telegram.download.reverse_sync.find_missing_files_from_database"
            ) as mock_db_to_files,
        ):
            mock_files_to_db.return_value = {"files_on_disk": 5, "matches_found": 3}
            mock_db_to_files.return_value = (
                {"database_completed": 10, "files_missing": 2},
                [],
            )

            try:
                from dnld_telegram.download.reverse_sync import (
                    complete_database_filesystem_sync,
                )

                result = await complete_database_filesystem_sync(
                    "test_channel", dry_run=True
                )

                # Should call both directions
                mock_files_to_db.assert_called_once_with("test_channel", True)
                mock_db_to_files.assert_called_once_with("test_channel", True)

                # Should return combined results
                assert "file_to_db" in result
                assert "db_to_file" in result

            except (ImportError, NameError):
                pytest.fail(
                    "complete_database_filesystem_sync not implemented yet - RED phase"
                )


if __name__ == "__main__":
    # Run the tests to see RED phase failures
    pytest.main([__file__, "-v"])
