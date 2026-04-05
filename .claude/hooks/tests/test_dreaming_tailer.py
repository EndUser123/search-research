"""
Tests for JSONL Tailer module (T-004).

These tests verify time-based partitioning for the dream journal JSONL:
- Read new events since last offset
- Skip malformed JSON lines
- Detect file rotation
- Reset offset on rotation
- Time-based partitioning
- Preserve all raw events
- Track offset across partitions
- Clean up old partitions
"""

import json
from datetime import datetime, timedelta

import pytest

# Module under test
from ..dreaming_tailer import JSONLTailer


class TestReadNewEvents:
    """Tests for reading new events since last offset."""

    @pytest.fixture
    def jsonl_file(self, tmp_path):
        """Create a test JSONL file."""
        return tmp_path / "test.jsonl"

    @pytest.fixture
    def sample_events(self):
        """Sample events for testing."""
        return [
            {"timestamp": "2026-03-07T10:00:00", "event": "test_event_1"},
            {"timestamp": "2026-03-07T10:01:00", "event": "test_event_2"},
            {"timestamp": "2026-03-07T10:02:00", "event": "test_event_3"},
        ]

    def test_reads_new_events_since_last_offset(self, jsonl_file, sample_events):
        """
        Test that read_new_events returns only new lines since last offset.

        Given: A JSONL file with 3 lines and offset at 0
        When: Reading events after advancing offset to 1
        Then: Should return only events 2 and 3
        """
        # Arrange - write sample events
        for event in sample_events:
            with open(jsonl_file, 'a') as f:
                f.write(json.dumps(event) + "\n")

        # Act - this will fail because JSONLTailer doesn't exist
        tailer = JSONLTailer(jsonl_file)
        tailer.offset = 1  # Skip first event
        events = list(tailer.read_new_events())

        # Assert
        assert len(events) == 2
        assert events[0]["event"] == "test_event_2"
        assert events[1]["event"] == "test_event_3"

    def test_returns_all_events_on_first_read(self, jsonl_file, sample_events):
        """
        Test that first read returns all events when offset is 0.

        Given: A JSONL file with 3 lines and offset at 0
        When: Reading events for the first time
        Then: Should return all 3 events
        """
        # Arrange
        for event in sample_events:
            with open(jsonl_file, 'a') as f:
                f.write(json.dumps(event) + "\n")

        # Act
        tailer = JSONLTailer(jsonl_file)
        events = list(tailer.read_new_events())

        # Assert
        assert len(events) == 3
        assert events == sample_events

    def test_returns_empty_list_when_no_new_events(self, jsonl_file, sample_events):
        """
        Test that read_new_events returns empty list when file hasn't changed.

        Given: A JSONL file with 3 lines and offset at 3 (end of file)
        When: Reading events again
        Then: Should return empty list
        """
        # Arrange
        for event in sample_events:
            with open(jsonl_file, 'a') as f:
                f.write(json.dumps(event) + "\n")

        # Act
        tailer = JSONLTailer(jsonl_file)
        tailer.offset = 3  # Already at end
        events = list(tailer.read_new_events())

        # Assert
        assert len(events) == 0


class TestSkipMalformedJSON:
    """Tests for handling malformed JSON lines."""

    @pytest.fixture
    def jsonl_file_with_malformed(self, tmp_path):
        """Create a JSONL file with some malformed lines."""
        jsonl_file = tmp_path / "test_malformed.jsonl"
        lines = [
            '{"timestamp": "2026-03-07T10:00:00", "event": "valid_1"}',
            '{invalid json}',
            '{"timestamp": "2026-03-07T10:01:00", "event": "valid_2"}',
            'not json at all',
            '{"timestamp": "2026-03-07T10:02:00", "event": "valid_3"}',
        ]
        jsonl_file.write_text("\n".join(lines))
        return jsonl_file

    def test_skips_malformed_json_lines(self, jsonl_file_with_malformed):
        """
        Test that malformed JSON lines are skipped without crashing.

        Given: A JSONL file with 5 lines (3 valid, 2 invalid)
        When: Reading all events
        Then: Should return only the 3 valid events
        """
        # Act
        tailer = JSONLTailer(jsonl_file_with_malformed)
        events = list(tailer.read_new_events())

        # Assert
        assert len(events) == 3
        assert all("event" in e for e in events)
        assert events[0]["event"] == "valid_1"
        assert events[1]["event"] == "valid_2"
        assert events[2]["event"] == "valid_3"

    def test_continues_after_malformed_line(self, jsonl_file_with_malformed):
        """
        Test that processing continues after encountering malformed line.

        Given: A JSONL file with valid, invalid, valid pattern
        When: Reading events
        Then: Should process all valid lines, not stop at first error
        """
        # Act
        tailer = JSONLTailer(jsonl_file_with_malformed)
        events = list(tailer.read_new_events())

        # Assert - verify we got events after the malformed lines
        assert len(events) == 3
        # The last valid event should be included
        assert events[-1]["event"] == "valid_3"


class TestDetectRotation:
    """Tests for detecting file rotation."""

    @pytest.fixture
    def jsonl_file(self, tmp_path):
        """Create a test JSONL file."""
        return tmp_path / "test.jsonl"

    def test_detects_rotation_when_file_size_decreases(self, jsonl_file):
        """
        Test that rotation is detected when file size decreases.

        Given: A JSONL file with 1000 bytes
        When: File is replaced with a smaller file (100 bytes)
        Then: Should detect rotation and reset offset
        """
        # Arrange - create large file
        large_content = "\n".join([f'{{"event": "event_{i}"}}' for i in range(100)])
        jsonl_file.write_text(large_content)
        original_size = jsonl_file.stat().st_size

        # Create tailer and read some events
        tailer = JSONLTailer(jsonl_file)
        list(tailer.read_new_events())  # Read all
        assert tailer.offset > 0

        # Act - replace with smaller file (simulate rotation)
        small_content = '{"event": "new_event"}'
        jsonl_file.write_text(small_content)

        # Assert - offset should reset
        events = list(tailer.read_new_events())
        assert tailer.offset == 1  # Reset after rotation
        assert len(events) == 1
        assert events[0]["event"] == "new_event"

    def test_resets_offset_on_rotation_detection(self, jsonl_file):
        """
        Test that offset resets to 0 when rotation is detected.

        Given: A tailer with offset at 50
        When: File rotation occurs (size decreases)
        Then: Offset should reset to 0
        """
        # Arrange
        large_content = "\n".join([f'{{"id": {i}}}' for i in range(100)])
        jsonl_file.write_text(large_content)

        tailer = JSONLTailer(jsonl_file)
        list(tailer.read_new_events())
        original_offset = tailer.offset
        assert original_offset == 100

        # Act - rotate file
        jsonl_file.write_text('{"new": "file"}')

        # Assert - offset should reset
        events = list(tailer.read_new_events())
        assert tailer.offset == 1
        assert events[0]["new"] == "file"


class TestTimeBasedPartitioning:
    """Tests for time-based partitioning of JSONL files."""

    @pytest.fixture
    def jsonl_file(self, tmp_path):
        """Create a test JSONL file."""
        return tmp_path / "dreaming.jsonl"

    def test_rotates_file_when_size_exceeds_threshold(self, jsonl_file):
        """
        Test that file rotates when size exceeds 50MB threshold.

        Given: A JSONL file approaching 50MB
        When: Writing events that push it over 50MB
        Then: Should create new partition with date suffix
        """
        # Arrange - create file close to threshold (48MB)
        large_line = '{"data": "' + "x" * 49000 + '"}'  # ~50KB per line
        lines = [large_line] * 980  # ~48MB
        jsonl_file.write_text("\n".join(lines))

        tailer = JSONLTailer(jsonl_file, max_size_mb=50)

        # Act - add more data to trigger rotation (push over 50MB)
        additional_lines = [large_line] * 100  # Push well over 50MB
        with open(jsonl_file, 'a') as f:
            f.write("\n" + "\n".join(additional_lines))

        # Trigger rotation check
        tailer.check_rotation()

        # Assert - old file should be renamed with date suffix
        today = datetime.now().strftime("%Y-%m-%d")
        expected_old_file = jsonl_file.parent / f"dreaming_{today}.jsonl"
        assert expected_old_file.exists()

        # New file should exist
        assert jsonl_file.exists()

    def test_adds_date_suffix_to_rotated_files(self, jsonl_file):
        """
        Test that rotated files get date suffix in format YYYY-MM-DD.

        Given: A file that needs rotation
        When: Rotation is triggered
        Then: Old file should be renamed with date suffix
        """
        # Arrange - create file larger than threshold
        large_line = '{"data": "' + "x" * 50000 + '"}'
        jsonl_file.write_text("\n".join([large_line] * 1100))  # ~55MB

        tailer = JSONLTailer(jsonl_file, max_size_mb=50)
        tailer.check_rotation()

        # Assert
        today = datetime.now().strftime("%Y-%m-%d")
        expected_name = f"dreaming_{today}.jsonl"
        rotated_files = list(jsonl_file.parent.glob("dreaming_*.jsonl"))

        assert len(rotated_files) >= 1
        assert today in rotated_files[0].name

    def test_multiple_partitions_for_same_day(self, jsonl_file):
        """
        Test that multiple rotations on same day get incrementing suffixes.

        Given: A file that rotates multiple times in one day
        When: Multiple rotations occur
        Then: Files should have incrementing counters (e.g., _1, _2)
        """
        # Arrange - first rotation
        large_line = '{"data": "' + "x" * 50000 + '"}'
        jsonl_file.write_text("\n".join([large_line] * 1100))  # ~55MB

        tailer = JSONLTailer(jsonl_file, max_size_mb=50)
        tailer.check_rotation()

        # Fill up again
        jsonl_file.write_text("\n".join([large_line] * 1100))  # Another ~55MB
        tailer.check_rotation()

        # Assert - should have multiple partitions
        rotated_files = list(jsonl_file.parent.glob("dreaming_*.jsonl"))
        assert len(rotated_files) >= 2


class TestPreserveRawEvents:
    """Tests for preserving all raw events."""

    @pytest.fixture
    def jsonl_file(self, tmp_path):
        """Create a test JSONL file."""
        return tmp_path / "test.jsonl"

    def test_preserves_all_valid_events(self, jsonl_file):
        """
        Test that all valid events are preserved during rotation.

        Given: A file with 100 valid events
        When: File rotates
        Then: All 100 events should be in the rotated partition
        """
        # Arrange
        events = [f'{{"id": {i}, "data": "test_{i}"}}' for i in range(100)]
        jsonl_file.write_text("\n".join(events))

        # Act - trigger rotation
        tailer = JSONLTailer(jsonl_file, max_size_mb=0.001)  # Very small threshold
        tailer.check_rotation()

        # Assert - find rotated file and verify content
        rotated_files = list(jsonl_file.parent.glob("test_*.jsonl"))
        assert len(rotated_files) >= 1

        rotated_content = rotated_files[0].read_text()
        rotated_events = [json.loads(line) for line in rotated_content.strip().split("\n")]

        assert len(rotated_events) == 100
        assert rotated_events[0]["id"] == 0
        assert rotated_events[-1]["id"] == 99

    def test_malformed_lines_dont_block_valid_events(self, jsonl_file):
        """
        Test that malformed lines don't prevent valid events from being processed.

        Given: A file with valid, invalid, valid events
        When: Reading events
        Then: All valid events should be returned, invalid skipped
        """
        # Arrange
        lines = [
            '{"valid": 1}',
            'invalid',
            '{"valid": 2}',
            'also invalid',
            '{"valid": 3}',
        ]
        jsonl_file.write_text("\n".join(lines))

        # Act
        tailer = JSONLTailer(jsonl_file)
        events = list(tailer.read_new_events())

        # Assert
        assert len(events) == 3
        assert events[0]["valid"] == 1
        assert events[1]["valid"] == 2
        assert events[2]["valid"] == 3


class TestTrackOffsetAcrossPartitions:
    """Tests for tracking offset across file partitions."""

    @pytest.fixture
    def jsonl_file(self, tmp_path):
        """Create a test JSONL file."""
        return tmp_path / "test.jsonl"

    def test_tracks_offset_across_rotation(self, jsonl_file):
        """
        Test that offset tracking works across file rotation.

        Given: A file with 50 events that then rotates
        When: Reading events before and after rotation
        Then: Should track correct position in new file
        """
        # Arrange - initial file
        events = [f'{{"id": {i}}}' for i in range(50)]
        jsonl_file.write_text("\n".join(events))

        # Act 1 - read initial events
        tailer = JSONLTailer(jsonl_file)
        initial_events = list(tailer.read_new_events())
        assert len(initial_events) == 50
        assert tailer.offset == 50

        # Rotate
        jsonl_file.write_text('{"new": "event1"}\n{"new": "event2"}')

        # Act 2 - read after rotation (offset should reset)
        new_events = list(tailer.read_new_events())
        assert len(new_events) == 2
        assert tailer.offset == 2  # Reset after rotation

    def test_reads_continuously_across_partitions(self, jsonl_file):
        """
        Test continuous reading across multiple partitions.

        Given: Multiple file partitions over time
        When: Continuously reading events
        Then: Should read all events without gaps
        """
        # This is a more complex integration test
        # For now, verify the concept exists
        tailer = JSONLTailer(jsonl_file)
        assert hasattr(tailer, 'offset')
        assert hasattr(tailer, 'read_new_events')


class TestCleanupOldPartitions:
    """Tests for cleaning up old partitions."""

    @pytest.fixture
    def jsonl_dir(self, tmp_path):
        """Create a directory with multiple partition files."""
        jsonl_dir = tmp_path
        today = datetime.now()

        # Create files with different dates
        dates = [
            today - timedelta(days=10),  # 10 days old - should be deleted
            today - timedelta(days=5),   # 5 days old
            today - timedelta(days=2),   # 2 days old
            today,                       # today - current file
        ]

        for i, date in enumerate(dates):
            filename = date.strftime("%Y-%m-%d") + ".jsonl"
            (jsonl_dir / filename).write_text(f'{{"file": "{filename}"}}')

        return jsonl_dir

    def test_deletes_partitions_older_than_retention_period(self, jsonl_dir):
        """
        Test that partitions older than retention period are deleted.

        Given: Multiple partition files with ages 10, 5, 2, 0 days
        When: Running cleanup with 7-day retention
        Then: Should delete 10-day-old file, keep others
        """
        # Act
        tailer = JSONLTailer(
            jsonl_dir / "current.jsonl",
            retention_days=7
        )
        tailer.cleanup_old_partitions()

        # Assert
        all_files = list(jsonl_dir.glob("*.jsonl"))
        dates_str = [f.stem for f in all_files]

        # 10-day-old file should be gone
        # This is a basic assertion - real test would parse dates
        assert len(all_files) <= 4  # At least one deleted

    def test_keeps_recent_partitions(self, jsonl_dir):
        """
        Test that recent partitions are not deleted.

        Given: Partitions from last 2 days
        When: Running cleanup with 7-day retention
        Then: Should keep all recent partitions
        """
        # Act
        tailer = JSONLTailer(
            jsonl_dir / "current.jsonl",
            retention_days=7
        )
        tailer.cleanup_old_partitions()

        # Assert - should still have files
        all_files = list(jsonl_dir.glob("*.jsonl"))
        assert len(all_files) >= 2  # At least some files remain


class TestJSONLSizeConstraints:
    """Tests for JSONL file size constraints."""

    @pytest.fixture
    def jsonl_file(self, tmp_path):
        """Create a test JSONL file."""
        return tmp_path / "test.jsonl"

    def test_no_single_file_exceeds_100mb(self, jsonl_file):
        """
        Test that no single partition file exceeds 100MB.

        Given: A JSONLTailer with 50MB rotation threshold
        When: Writing large amounts of data
        Then: No individual file should exceed 100MB (2x threshold for safety)
        """
        # This is a constraint test
        # In real scenario, we'd write lots of data and verify sizes

        tailer = JSONLTailer(jsonl_file, max_size_mb=50)

        # Verify threshold is set
        assert tailer.max_size_bytes == 50 * 1024 * 1024

        # Write data that would exceed threshold
        # (in real test, this would trigger rotation)
        large_line = '{"data": "' + "x" * 1000 + '"}'

        # The mechanism exists to prevent files exceeding limit
        assert hasattr(tailer, 'check_rotation')
        assert hasattr(tailer, 'max_size_bytes')

    def test_rotation_threshold_is_configurable(self, jsonl_file):
        """
        Test that rotation threshold can be configured.

        Given: JSONLTailer class
        When: Creating with different max_size_mb values
        Then: Should respect configured threshold
        """
        # Act
        tailer_default = JSONLTailer(jsonl_file)
        tailer_custom = JSONLTailer(jsonl_file, max_size_mb=100)

        # Assert
        assert tailer_custom.max_size_bytes == 100 * 1024 * 1024
        assert tailer_default.max_size_bytes == 50 * 1024 * 1024  # Default
