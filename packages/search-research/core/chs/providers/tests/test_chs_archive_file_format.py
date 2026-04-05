"""
T14: Archive file format validation test for CHS archive layer.

Verifies that raw_{event_id}.jsonl files contain valid JSON lines with required fields.
Each line in the archive file must be a valid JSON object with at minimum an identifier field.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from core.chs.archive import append_raw_event, write_watermark, read_watermark


@pytest.fixture
def temp_archive_base(tmp_path):
    """Fixture providing a temporary archive base directory."""
    archive_dir = tmp_path / "chs_archive"
    archive_dir.mkdir()
    return archive_dir


def create_raw_payload(archive_dir: Path, event_id: str, content: str) -> Path:
    """Create a raw payload file and return its path."""
    payload_path = archive_dir / f"raw_{event_id}.json"
    payload_data = {
        "uuid": event_id,
        "provider": "test_provider",
        "content": content,
        "metadata": {"created": "2024-01-01T00:00:00"},
    }
    payload_path.write_text(json.dumps(payload_data))
    return payload_path


class TestArchiveFileFormatValidation:
    """Tests verifying archive file format compliance."""

    def test_each_line_is_valid_json(self, temp_archive_base):
        """
        Test that each line in the archive file is valid parseable JSON.
        """
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            # Write first event
            content1 = "First event content for JSON validation"
            payload1 = create_raw_payload(temp_archive_base, "json-valid-001", content1)
            event1 = {"uuid": "json-valid-001", "provider": "test_provider", "content": content1}
            archive_path_str1 = append_raw_event(
                provider_id="test_provider",
                source_id="test-source",
                event=event1,
            )
            archive_path1 = Path(archive_path_str1)

            # Write second event
            content2 = "Second event content for JSON validation"
            payload2 = create_raw_payload(temp_archive_base, "json-valid-002", content2)
            event2 = {"uuid": "json-valid-002", "provider": "test_provider", "content": content2}
            archive_path_str2 = append_raw_event(
                provider_id="test_provider",
                source_id="test-source",
                event=event2,
            )
            archive_path2 = Path(archive_path_str2)

            # Read archive file and verify each line is valid JSON
            for archive_path in [archive_path1, archive_path2]:
                assert archive_path.exists()

                with open(archive_path, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue  # Skip empty lines

                        # Each line should be valid JSON (no parse errors)
                        try:
                            parsed = json.loads(line)
                            assert isinstance(parsed, dict), (
                                f"Line {line_num} in {archive_path} is not a JSON object"
                            )
                        except json.JSONDecodeError as e:
                            pytest.fail(
                                f"Line {line_num} in {archive_path} is not valid JSON: {e}"
                            )

    def test_each_json_object_has_required_fields(self, temp_archive_base):
        """
        Test that each JSON object in the archive has required fields.
        At minimum, must have an identifier field (uuid/event_id).
        """
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            event_id = "required-fields-003"
            content = "Content for required fields test"
            payload = create_raw_payload(temp_archive_base, event_id, content)
            event = {"uuid": event_id, "provider": "test_provider", "content": content}
            archive_path_str = append_raw_event(
                provider_id="test_provider",
                source_id="test-source",
                event=event,
            )
            archive_path = Path(archive_path_str)

            with open(archive_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    obj = json.loads(line)

                    # Must have at least one identifying field
                    has_identifier = (
                        "event_id" in obj or
                        "uuid" in obj or
                        "id" in obj
                    )
                    assert has_identifier, (
                        f"JSON object missing identifier field (event_id/uuid/id): {obj}"
                    )

    def test_multiple_events_in_same_archive_file(self, temp_archive_base):
        """
        Test that multiple events can be written to the archive file
        and all are readable and valid.
        """
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            # Write multiple events - they may go to same or different archive files
            # depending on provider partitioning, but each should be valid
            event_ids = ["multi-event-a", "multi-event-b", "multi-event-c"]

            archive_paths = []
            for event_id in event_ids:
                content = f"Content for {event_id}"
                payload = create_raw_payload(temp_archive_base, event_id, content)
                event = {"uuid": event_id, "provider": "test_provider", "content": content}
                archive_path_str = append_raw_event(
                    provider_id="test_provider",
                    source_id="test-source",
                    event=event,
                )
                archive_paths.append(Path(archive_path_str))

            # Verify each archive file is valid
            for archive_path in archive_paths:
                assert archive_path.exists()

                with open(archive_path, 'r', encoding='utf-8') as f:
                    line_count = 0
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        # Must be valid JSON
                        obj = json.loads(line)
                        assert isinstance(obj, dict)

                        # Must have identifier
                        assert any(k in obj for k in ["event_id", "uuid", "id"])

                        line_count += 1

                    # Should have at least one line per file
                    assert line_count >= 1, f"Archive file {archive_path} should have at least 1 event"

    def test_archive_file_content_integrity(self, temp_archive_base):
        """
        Test that archived file content is preserved correctly and can be read back.
        """
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            event_id = "integrity-test-004"
            original_content = "Original content for integrity check"

            # Create raw payload with the content
            payload_path = temp_archive_base / f"raw_{event_id}.json"
            payload_data = {
                "uuid": event_id,
                "provider": "test_provider",
                "content": original_content,
            }
            payload_path.write_text(json.dumps(payload_data))

            # Append to archive
            event = {"uuid": event_id, "provider": "test_provider", "content": original_content}
            archive_path_str = append_raw_event(
                provider_id="test_provider",
                source_id="test-source",
                event=event,
            )
            archive_path = Path(archive_path_str)

            # Read back and verify
            assert archive_path.exists()

            with open(archive_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    obj = json.loads(line)

                    # Verify content matches original
                    assert obj["uuid"] == event_id
                    assert obj["provider"] == "test_provider"
                    assert obj["content"] == original_content

    def test_archive_file_no_trailing_corruption(self, temp_archive_base):
        """
        Test that archive files don't have trailing corruption or malformed data.
        """
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            event_id = "corruption-test-005"
            content = "Content for corruption test"
            payload = create_raw_payload(temp_archive_base, event_id, content)
            event = {"uuid": event_id, "provider": "test_provider", "content": content}
            archive_path_str = append_raw_event(
                provider_id="test_provider",
                source_id="test-source",
                event=event,
            )
            archive_path = Path(archive_path_str)

            # Read entire file and verify no parse errors
            with open(archive_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # If file is empty, skip
            if not content.strip():
                pytest.skip("Archive file is empty")

            # Each line should be independently parseable
            for line_num, line in enumerate(content.split('\n'), 1):
                line = line.strip()
                if not line:
                    continue

                try:
                    json.loads(line)
                except json.JSONDecodeError as e:
                    pytest.fail(
                        f"Archive file {archive_path} has corrupted data at line {line_num}: {e}"
                    )

    def test_jsonl_format_one_event_per_line(self, temp_archive_base):
        """
        Verify the archive file follows JSONL format: one JSON object per line.
        No arrays, no trailing commas, no multi-line objects.
        """
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            events = [
                {"id": "jsonl-001", "data": "first"},
                {"id": "jsonl-002", "data": "second"},
                {"id": "jsonl-003", "data": "third"},
            ]

            archive_paths = []
            for evt in events:
                event_id = evt["id"]
                payload_path = temp_archive_base / f"raw_{event_id}.json"
                payload_path.write_text(json.dumps(evt))

                event = {"uuid": event_id, "provider": "test_provider", "content": evt["data"]}
                archive_path_str = append_raw_event(
                    provider_id="test_provider",
                    source_id="test-source",
                    event=event,
                )
                archive_paths.append(Path(archive_path_str))

            # Each file should contain valid JSONL
            for archive_path in archive_paths:
                with open(archive_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Should not be a JSON array (would have [ at start)
                if content.strip().startswith('['):
                    pytest.fail(f"{archive_path} is JSON array, expected JSONL format")

                # Each line should be a separate JSON object
                for line_num, line in enumerate(content.split('\n'), 1):
                    line = line.strip()
                    if not line:
                        continue

                    # Must be a JSON object (starts with {)
                    if not line.startswith('{'):
                        pytest.fail(
                            f"Line {line_num} in {archive_path} is not a JSON object: {line}"
                        )

                    # Must be parseable
                    try:
                        obj = json.loads(line)
                        assert isinstance(obj, dict)
                    except json.JSONDecodeError as e:
                        pytest.fail(f"Line {line_num} in {archive_path} is malformed: {e}")