"""
Unit tests for core download logic in dnld_telegram/src/download/download.py
"""

from unittest.mock import MagicMock

from dnld_telegram.src.download import download


def make_enumerated(file_id=None, media_type=None, status=None):
    return {"file_id": file_id, "media_type": media_type, "status": status}


def make_downloaded(file_id):
    return {"file_id": file_id}


def test_update_file_status_transitions():
    files = {}
    file_info = make_enumerated(file_id="abc123", status="old_status")
    files["1"] = file_info.copy()
    # Should update status
    updated = download._update_file_status(files, "1", files["1"], "downloaded", 1)
    assert updated
    assert files["1"]["status"] == "downloaded"
    # Should not update if status is same
    updated = download._update_file_status(files, "1", files["1"], "downloaded", 1)
    assert not updated


def test_update_file_status_duplicate_handling():
    files = {"1": make_enumerated(file_id="abc123", status="old")}
    # Should update status
    assert download._update_file_status(files, "1", files["1"], "downloaded", 1)
    # Should not update again
    assert not download._update_file_status(files, "1", files["1"], "downloaded", 1)


def test_filter_already_downloaded_marks_status_and_saves(monkeypatch):
    enumerated = {
        "1": make_enumerated(file_id=None),
        "2": make_enumerated(file_id="paid", media_type="MessageMediaPaidMedia"),
        "3": make_enumerated(file_id="abc"),
        "4": make_enumerated(file_id="def"),
    }
    downloaded = {
        "10": make_downloaded("abc"),
    }
    saved = {}

    def fake_save(channel_name, files, telegram_channel_id=None):
        saved[channel_name] = files.copy()

    monkeypatch.setattr(download, "save_enumerated_files", fake_save)
    monkeypatch.setattr(download, "logger", MagicMock())
    result = download._filter_already_downloaded(enumerated, downloaded, "chan")
    # "1" should be marked skipped_null_file_id, "2" skipped_paid_media, "3" as downloaded
    assert enumerated["1"]["status"] == download.SKIP_STATUS_NULL_FILE_ID
    assert enumerated["2"]["status"] == download.SKIP_STATUS_PAID_MEDIA
    assert enumerated["3"]["status"] == download.STATUS_DOWNLOADED
    # Only "4" should remain to download
    assert "4" in result and len(result) == 1
    # Should have called save
    assert "chan" in saved


def test_status_constants_and_workflow():
    # Check status constants
    assert isinstance(download.SKIP_STATUS_NULL_FILE_ID, str)
    assert isinstance(download.STATUS_DOWNLOADED, str)
    assert download.STATUS_DOWNLOADED != download.STATUS_DOWNLOAD_ERROR
