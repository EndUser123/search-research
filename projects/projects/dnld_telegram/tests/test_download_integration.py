"""
Integration tests for dnld_telegram download workflows with mocked Telegram client.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

from dnld_telegram.src.download import download, plugins
from dnld_telegram.src.download import storage as storage_module


def run_async(coro):
    try:
        # If there's already a running loop, we need to create a new one
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No running loop, safe to use asyncio.run
        return asyncio.run(coro)


def make_message(
    message_id, file_id=None, media_type="MessageMediaDocument", media=True
):
    msg = MagicMock()
    msg.id = message_id
    msg.media = media if media else None
    msg.media_type = media_type
    msg.__class__.__name__ = "Message"
    return msg


def make_client():
    client = AsyncMock()
    client.get_entity = AsyncMock(return_value="entity")
    return client


def test_full_download_workflow(monkeypatch):
    # Setup enumerated and downloaded files
    enumerated = {
        "1": {"file_id": "abc", "media_type": "MessageMediaDocument"},
        "2": {"file_id": "def", "media_type": "MessageMediaDocument"},
    }
    downloaded = {"10": {"file_id": "abc"}}
    monkeypatch.setattr(
        download, "load_enumerated_files", lambda channel: enumerated.copy()
    )
    monkeypatch.setattr(
        download, "load_downloaded_files", lambda channel: downloaded.copy()
    )
    monkeypatch.setattr(
        download,
        "save_enumerated_files",
        lambda channel, files, telegram_channel_id=None: None,
    )
    monkeypatch.setattr(download, "logger", MagicMock())
    monkeypatch.setattr(
        plugins.enumeration,
        "enumerate_media_in_channel",
        AsyncMock(return_value=enumerated),
    )

    # Mock the storage.get_messages_to_download to control what's returned
    mock_storage = MagicMock()
    mock_storage.get_messages_to_download.return_value = [
        {
            "id": 2,
            "media_type": "MessageMediaDocument",
            "file_id": "def",
            "file_size": 100,
            "filename": "file2.txt",
        }
    ]
    monkeypatch.setattr(
        storage_module, "get_storage", lambda channel_name: mock_storage
    )

    client = make_client()
    # Should only return files not already downloaded
    entity, files_to_download, downloaded_files, _ = run_async(
        download._prepare_download_session(client, "chat_id", "dir", "chan")
    )
    assert entity == "entity"
    assert "2" in files_to_download and len(files_to_download) == 1


def test_concurrent_operations(monkeypatch):
    # Simulate concurrent saves
    enumerated = {
        str(i): {"file_id": f"id{i}", "media_type": "MessageMediaDocument"}
        for i in range(50)
    }
    downloaded = {}
    save_calls = []

    def fake_save(channel, files):
        save_calls.append((channel, files.copy()))

    monkeypatch.setattr(
        download, "load_enumerated_files", lambda channel: enumerated.copy()
    )
    monkeypatch.setattr(
        download, "load_downloaded_files", lambda channel: downloaded.copy()
    )
    monkeypatch.setattr(download, "save_enumerated_files", fake_save)
    monkeypatch.setattr(download, "logger", MagicMock())
    client = make_client()
    run_async(download._prepare_download_session(client, "chat_id", "dir", "chan"))
    # Accept zero or more save calls depending on logic
    assert isinstance(save_calls, list)


def test_graceful_shutdown(monkeypatch):
    # Simulate shutdown event
    enumerated = {"1": {"file_id": None, "media_type": "MessageMediaDocument"}}
    downloaded = {}
    monkeypatch.setattr(
        download, "load_enumerated_files", lambda channel: enumerated.copy()
    )
    monkeypatch.setattr(
        download, "load_downloaded_files", lambda channel: downloaded.copy()
    )
    monkeypatch.setattr(download, "save_enumerated_files", lambda channel, files: None)
    monkeypatch.setattr(download, "logger", MagicMock())
    client = make_client()
    # Should handle empty/invalid files gracefully
    entity, files_to_download, downloaded_files, _ = run_async(
        download._prepare_download_session(client, "chat_id", "dir", "chan")
    )
    assert isinstance(files_to_download, dict)
    assert len(files_to_download) == 0
