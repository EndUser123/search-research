"""
T10: NormalizedEvent field validation test for CHS normalized layer.

Verifies that ingested events have correct content_hash, occurred_at is ISO 8601,
and raw_payload_path resolves to a readable file with valid JSON.
"""

import json
import hashlib
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from .normalized import upsert_event, get_events_by_hash
from .db import init_db


@pytest.fixture
def temp_normalized_db(tmp_path):
    """Fixture providing a temporary database path for normalized events."""
    db_path = tmp_path / "test_normalized.db"
    # Initialize the schema before tests run
    init_db(db_path)
    yield db_path, tmp_path
    # Cleanup handled by tmp_path fixture


@pytest.fixture
def temp_archive_base(tmp_path):
    """Fixture providing a temporary archive base for raw payload files."""
    archive_dir = tmp_path / "chs_archive"
    archive_dir.mkdir()
    return archive_dir


def compute_content_hash(content: str) -> str:
    """Compute SHA256 hash of content string."""
    return hashlib.sha256(content.encode()).hexdigest()


def create_test_raw_payload(archive_dir: Path, event_id: str, content: str) -> Path:
    """Create a test raw payload file and return its path."""
    payload_path = archive_dir / f"raw_{event_id}.json"
    payload_data = {
        "event_id": event_id,
        "provider": "test_provider",
        "content": content,
        "metadata": {"created": "2024-01-01T00:00:00"},
    }
    payload_path.write_text(json.dumps(payload_data))
    return payload_path


class TestNormalizedEventValidation:
    """Tests verifying NormalizedEvent field validation on ingest."""

    def test_upsert_event_with_valid_content_hash(self, temp_normalized_db, temp_archive_base):
        """
        Test that upsert_event correctly computes and stores content_hash.
        Uses precomputed SHA256 hash to verify the stored value matches.
        """
        db_path, tmp_path = temp_normalized_db
        with patch("core.chs.normalized.DB_PATH", db_path):
            with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
                event_id = "hash-test-event-001"
                content = "Test content for hash verification"
                expected_hash = compute_content_hash(content)

                # Create raw payload
                payload_path = create_test_raw_payload(temp_archive_base, event_id, content)

                # Upsert the event - note: occurred_at must be provided
                event_dict = {
                    "provider_id": "test_provider",
                    "source_id": "test-source",
                    "event_id": event_id,
                    "content_hash": expected_hash,
                    "occurred_at": "2024-01-01T00:00:00",
                    "raw_payload_path": str(payload_path),
                }
                result = upsert_event(event_dict)

                # Verify row was inserted (returns True for new insert)
                assert result is True, "upsert_event should return True for new insert"

                # Query back and verify hash matches
                events = get_events_by_hash(
                    provider_id="test_provider",
                    source_id="test-source",
                    content_hash=expected_hash,
                )
                assert len(events) == 1, f"Expected 1 event with hash {expected_hash}, got {len(events)}"

                stored_event = events[0]
                assert stored_event["content_hash"] == expected_hash, (
                    f"Stored hash {stored_event['content_hash']} != expected {expected_hash}"
                )

    def test_occurred_at_is_valid_iso_8601_format(self, temp_normalized_db, temp_archive_base):
        """
        Test that occurred_at field is stored in valid ISO 8601 format.
        Pattern: YYYY-MM-DDTHH:MM:SS
        """
        db_path, tmp_path = temp_normalized_db
        with patch("core.chs.normalized.DB_PATH", db_path):
            with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
                event_id = "iso-time-test-002"
                content = "Test content for ISO timestamp"
                expected_hash = compute_content_hash(content)

                payload_path = create_test_raw_payload(temp_archive_base, event_id, content)

                event_dict = {
                    "provider_id": "test_provider",
                    "source_id": "test-source",
                    "event_id": event_id,
                    "content_hash": expected_hash,
                    "occurred_at": "2024-01-02T12:30:00",
                    "raw_payload_path": str(payload_path),
                }
                upsert_event(event_dict)

                # Query and verify ISO 8601 format
                events = get_events_by_hash(
                    provider_id="test_provider",
                    source_id="test-source",
                    content_hash=expected_hash,
                )
                assert len(events) == 1

                occurred_at = events[0]["occurred_at"]
                iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
                assert iso_pattern.match(occurred_at), (
                    f"occurred_at '{occurred_at}' does not match ISO 8601 pattern YYYY-MM-DDTHH:MM:SS"
                )

    def test_raw_payload_path_resolves_to_readable_file(self, temp_normalized_db, temp_archive_base):
        """
        Test that raw_payload_path stored in DB points to an existing, readable file.
        """
        db_path, tmp_path = temp_normalized_db
        with patch("core.chs.normalized.DB_PATH", db_path):
            with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
                event_id = "readable-path-test-003"
                content = "Test content for readable path check"
                expected_hash = compute_content_hash(content)

                # Create the raw payload file
                payload_path = create_test_raw_payload(temp_archive_base, event_id, content)

                # Verify file exists before upsert
                assert payload_path.exists(), f"Payload file should exist at {payload_path}"

                event_dict = {
                    "provider_id": "test_provider",
                    "source_id": "test-source",
                    "event_id": event_id,
                    "content_hash": expected_hash,
                    "occurred_at": "2024-01-03T00:00:00",
                    "raw_payload_path": str(payload_path),
                }
                upsert_event(event_dict)

                # Query and verify raw_payload_path is accessible
                events = get_events_by_hash(
                    provider_id="test_provider",
                    source_id="test-source",
                    content_hash=expected_hash,
                )
                assert len(events) == 1

                stored_path = events[0]["raw_payload_path"]
                path_obj = Path(stored_path)

                assert path_obj.exists(), f"raw_payload_path '{stored_path}' does not exist"
                assert path_obj.is_file(), f"raw_payload_path '{stored_path}' is not a file"

                # Verify file is readable
                content_read = path_obj.read_text()
                assert len(content_read) > 0, "raw_payload file should not be empty"

    def test_raw_payload_file_contains_valid_json(self, temp_normalized_db, temp_archive_base):
        """
        Test that the file at raw_payload_path contains valid JSON.
        """
        db_path, tmp_path = temp_normalized_db
        with patch("core.chs.normalized.DB_PATH", db_path):
            with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
                event_id = "valid-json-test-004"
                content = "Test content for JSON validation"
                expected_hash = compute_content_hash(content)

                payload_path = create_test_raw_payload(temp_archive_base, event_id, content)

                event_dict = {
                    "provider_id": "test_provider",
                    "source_id": "test-source",
                    "event_id": event_id,
                    "content_hash": expected_hash,
                    "occurred_at": "2024-01-04T00:00:00",
                    "raw_payload_path": str(payload_path),
                }
                upsert_event(event_dict)

                # Query and verify file contains valid JSON
                events = get_events_by_hash(
                    provider_id="test_provider",
                    source_id="test-source",
                    content_hash=expected_hash,
                )
                assert len(events) == 1

                stored_path = events[0]["raw_payload_path"]
                path_obj = Path(stored_path)

                # Should not raise - file contains valid JSON
                json_content = json.loads(path_obj.read_text())
                assert isinstance(json_content, dict), "Parsed JSON should be a dict"
                assert "event_id" in json_content, "JSON should have 'event_id' field"

    def test_multiple_events_all_validated(self, temp_normalized_db, temp_archive_base):
        """
        Verify that multiple events ingested all pass validation checks.
        """
        db_path, tmp_path = temp_normalized_db
        iso_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

        with patch("core.chs.normalized.DB_PATH", db_path):
            with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
                events_data = [
                    {"id": "multi-001", "content": "Content one"},
                    {"id": "multi-002", "content": "Content two"},
                    {"id": "multi-003", "content": "Content three"},
                ]

                for idx, event_data in enumerate(events_data, start=1):
                    event_id = event_data["id"]
                    content = event_data["content"]
                    expected_hash = compute_content_hash(content)

                    payload_path = create_test_raw_payload(temp_archive_base, event_id, content)

                    event_dict = {
                        "provider_id": "test_provider",
                        "source_id": "test-source",
                        "event_id": event_id,
                        "content_hash": expected_hash,
                        "occurred_at": f"2024-01-{idx+4:02d}T00:00:00",
                        "raw_payload_path": str(payload_path),
                    }
                    result = upsert_event(event_dict)
                    assert result is True

                    # Validate each event
                    events = get_events_by_hash(
                        provider_id="test_provider",
                        source_id="test-source",
                        content_hash=expected_hash,
                    )
                    assert len(events) == 1

                    event = events[0]

                    # Check content_hash
                    assert event["content_hash"] == expected_hash

                    # Check ISO 8601 format
                    assert iso_pattern.match(event["occurred_at"])

                    # Check raw_payload_path exists and readable
                    path_obj = Path(event["raw_payload_path"])
                    assert path_obj.exists()

                    # Check valid JSON
                    json_data = json.loads(path_obj.read_text())
                    assert isinstance(json_data, dict)

    def test_hash_mismatch_detected(self, temp_normalized_db, temp_archive_base):
        """
        Verify that when content_hash doesn't match actual content, querying by
        precomputed hash returns no results.
        """
        db_path, tmp_path = temp_normalized_db
        with patch("core.chs.normalized.DB_PATH", db_path):
            with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
                event_id = "hash-mismatch-005"
                content = "Original content"
                wrong_hash = compute_content_hash("Different content")

                payload_path = create_test_raw_payload(temp_archive_base, event_id, content)

                # Store with correct hash
                correct_hash = compute_content_hash(content)
                event_dict = {
                    "provider_id": "test_provider",
                    "source_id": "test-source",
                    "event_id": event_id,
                    "content_hash": correct_hash,
                    "occurred_at": "2024-01-05T00:00:00",
                    "raw_payload_path": str(payload_path),
                }
                upsert_event(event_dict)

                # Query with wrong hash - should return no results
                events = get_events_by_hash(
                    provider_id="test_provider",
                    source_id="test-source",
                    content_hash=wrong_hash,
                )
                assert len(events) == 0, "Hash mismatch should return no events"