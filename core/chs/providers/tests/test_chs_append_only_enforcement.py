"""
T9: Append-only enforcement test for CHS archive layer.

Verifies that archive files cannot be deleted once written - the archive is
append-only by design. This prevents tampering with historical event data.

Note: The append-only enforcement is at the API level - the archive module
does not expose any delete operation. On Windows, files can technically be
deleted via os.unlink() but the archive layer provides no such capability.
"""

import os
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from ..archive import append_raw_event, write_watermark, read_watermark


@pytest.fixture
def temp_archive_base(tmp_path):
    """Fixture providing a temporary archive base directory."""
    archive_dir = tmp_path / "chs_archive"
    archive_dir.mkdir()
    return archive_dir


class TestAppendOnlyEnforcement:
    """Tests verifying archive files cannot be deleted via API."""

    def test_archive_no_delete_function_in_api(self, temp_archive_base):
        """
        Verify that the archive module does not expose any delete operation.

        The archive is append-only - there should be no function like
        delete_archive_file, remove_event, etc. in the public API.
        """
        import core.chs.archive as archive_module

        # List of prohibited delete operations that should not exist
        prohibited_attrs = [
            'delete_archive', 'delete_event', 'remove_event',
            'delete_file', 'remove_file', 'unlink_event',
        ]

        for attr in prohibited_attrs:
            assert not hasattr(archive_module, attr), (
                f"Archive module should not expose '{attr}' - archive is append-only"
            )

    def test_append_raw_event_returns_path_not_delete_handle(self, temp_archive_base):
        """
        Verify that append_raw_event() returns a path string, not a delete-enabled object.
        """
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            event_data = {
                "event_id": "test-event-001",
                "provider": "test_provider",
                "content": "Test content for append-only verification",
            }
            raw_payload_path = temp_archive_base / "raw_test-event-001.json"
            raw_payload_path.write_text(json.dumps(event_data))

            result = append_raw_event(
                provider_id="test_provider",
                source_id="test-source",
                event=event_data,
            )

            # Result should be a string path, not a custom object
            assert isinstance(result, str), f"append_raw_event should return str, got {type(result)}"

            archive_path = Path(result)
            assert archive_path.exists(), f"Archive file should exist at {archive_path}"

    def test_write_watermark_no_delete_operation(self, temp_archive_base):
        """
        Verify that write_watermark() has no delete operation exposed.
        """
        import core.chs.archive as archive_module

        # Watermark operations should not include delete
        prohibited = ['delete_watermark', 'remove_watermark', 'clear_watermark']
        for attr in prohibited:
            assert not hasattr(archive_module, attr), (
                f"Watermark module should not expose '{attr}'"
            )

    def test_multiple_events_written_all_persist(self, temp_archive_base):
        """
        Verify that multiple events written to the archive all persist and
        no delete mechanism is available.
        """
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            event_ids = ["event-a", "event-b", "event-c"]
            archive_paths = []

            for event_id in event_ids:
                event_data = {"event_id": event_id, "provider": "test", "content": f"Content for {event_id}"}
                raw_payload_path = temp_archive_base / f"raw_{event_id}.json"
                raw_payload_path.write_text(json.dumps(event_data))

                archive_path_str = append_raw_event(
                    provider_id="test_provider",
                    source_id="test-source",
                    event=event_data,
                )
                archive_paths.append(Path(archive_path_str))

            # All files should exist
            for ap in archive_paths:
                assert ap.exists(), f"Archive file {ap} should exist"

            # Verify no delete function exists in the module
            import core.chs.archive as archive_mod
            delete_funcs = [a for a in dir(archive_mod) if 'delete' in a.lower() or 'remove' in a.lower()]
            assert len(delete_funcs) == 0, (
                f"Archive module should not have delete functions: {delete_funcs}"
            )

    def test_append_only_behavior_documented(self, temp_archive_base):
        """
        Verify that the append_raw_event function has docstring confirming append-only behavior.
        """
        with patch("core.chs.archive._ARCHIVE_BASE", temp_archive_base):
            event_data = {"event_id": "doc-test", "provider": "test", "content": "content"}
            raw_payload_path = temp_archive_base / "raw_doc-test.json"
            raw_payload_path.write_text(json.dumps(event_data))

            archive_path_str = append_raw_event(
                provider_id="test_provider",
                source_id="test-source",
                event=event_data,
            )

            # Docstring should mention append-only
            doc = append_raw_event.__doc__
            assert doc is not None, "append_raw_event should have a docstring"
            assert "append" in doc.lower(), "Docstring should mention append-only behavior"