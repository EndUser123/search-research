"""Test recovery — pending messages survive process restart."""

import sys
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from ai_lane_controller.registry import Lane
from ai_lane_controller.router import submit_message
from ai_lane_controller.recovery import acknowledge_message, list_pending, recover_pending
from ai_lane_controller.storage import MessageStorage


TWO_LANES = [Lane("lane-a"), Lane("lane-b")]


def test_list_pending_returns_unacknowledged() -> None:
    """Newly routed messages are pending."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        submit_message("lane-a", "chatgpt", "claude", "One", storage, TWO_LANES)
        submit_message("lane-b", "chatgpt", "claude", "Two", storage, TWO_LANES)
        pending = list_pending(storage)
        assert len(pending) == 2


def test_acknowledge_removes_from_pending() -> None:
    """Acknowledged messages no longer appear in the pending list."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        result = submit_message("lane-a", "chatgpt", "claude", "Ack me", storage, TWO_LANES)
        assert len(list_pending(storage)) == 1
        ack_msg = storage.get_message("lane-a", result["id"])
        assert ack_msg is not None
        acknowledge_message(ack_msg, storage)
        assert len(list_pending(storage)) == 0


def test_acknowledge_recorded_in_events() -> None:
    """Acknowledging creates an event log entry."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        result = submit_message("lane-a", "chatgpt", "claude", "Log me", storage, TWO_LANES)
        msg = storage.get_message("lane-a", result["id"])
        assert msg is not None
        acknowledge_message(msg, storage)
        events = storage.list_events("lane-a")
        ack_events = [e for e in events if e["type"] == "message_acknowledged"]
        assert len(ack_events) == 1
        assert ack_events[0]["message_id"] == result["id"]
        assert ack_events[0]["status"] == "acknowledged"


# -- restart recovery -------------------------------------------------------

def test_message_survives_storage_recreation() -> None:
    """Given: pending message exists.  Simulate process restart.
    Assert: message remains recoverable."""
    with tempfile.TemporaryDirectory() as td:
        storage1 = MessageStorage(td)
        result = submit_message("lane-a", "chatgpt", "claude", "Survive restart", storage1, TWO_LANES)
        msg_id = result["id"]

        # Simulate restart: create a fresh storage instance pointed at the same dir.
        storage2 = MessageStorage(td)
        pending = list_pending(storage2)
        ids = [m["id"] for m in pending]
        assert msg_id in ids, f"Message {msg_id} not found after restart: {ids}"
        assert pending[0]["payload_path"] is not None


def test_payload_survives_restart() -> None:
    """The payload text is durable across storage instances."""
    content = "## Persisted\n\nThis should survive any restart."
    with tempfile.TemporaryDirectory() as td:
        storage1 = MessageStorage(td)
        result = submit_message("lane-a", "chatgpt", "claude", content, storage1, TWO_LANES)
        # New storage, same dir
        storage2 = MessageStorage(td)
        payload = storage2.read_payload("lane-a", result["id"])
        assert payload == content


# -- recover_pending --------------------------------------------------------

def test_recover_pending_returns_all() -> None:
    """recover_pending returns the same set as list_pending currently."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        submit_message("lane-a", "chatgpt", "claude", "R1", storage, TWO_LANES)
        submit_message("lane-b", "chatgpt", "claude", "R2", storage, TWO_LANES)
        recovered = recover_pending(storage)
        assert len(recovered) == 2
        lanes = {m["lane_id"] for m in recovered}
        assert lanes == {"lane-a", "lane-b"}


def test_recover_empty_after_all_acknowledged() -> None:
    """After acknowledging all messages, recover_pending returns [ ]."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        result = submit_message("lane-a", "chatgpt", "claude", "Gone", storage, TWO_LANES)
        msg = storage.get_message("lane-a", result["id"])
        assert msg is not None
        acknowledge_message(msg, storage)
        assert recover_pending(storage) == []
