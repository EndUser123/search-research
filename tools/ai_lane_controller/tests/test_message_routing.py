"""Test message routing — lane isolation, rejection, and audit."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from ai_lane_controller.registry import Lane, RegistryError
from ai_lane_controller.router import RoutingError, submit_message
from ai_lane_controller.storage import MessageStorage


LANE_A = Lane("lane-a")
LANE_B = Lane("lane-b")
TWO_LANES = [LANE_A, LANE_B]


def test_submit_message_creates_artifact() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        result = submit_message("lane-a", "chatgpt", "claude", "Hello", storage, TWO_LANES)
        assert result["lane_id"] == "lane-a"
        assert result["source"] == "chatgpt"
        assert result["destination"] == "claude"
        assert result["status"] == "pending"
        assert result["payload_path"] is not None
        assert "lane-a" in result["payload_path"]
        assert result["id"].startswith("msg-")


def test_submit_and_read_payload() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        result = submit_message("lane-a", "claude", "chatgpt", "## Response\n\nTest content.", storage, TWO_LANES)
        payload = storage.read_payload("lane-a", result["id"])
        assert payload == "## Response\n\nTest content."


# -- lane isolation ---------------------------------------------------------

def test_lane_a_message_not_visible_in_lane_b() -> None:
    """Given: message created for lane-a.  Assert: lane-b cannot see it."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        submit_message("lane-a", "chatgpt", "claude", "secret", storage, TWO_LANES)
        b_messages = storage.list_messages("lane-b")
        assert len(b_messages) == 0


def test_lane_b_message_not_visible_in_lane_a() -> None:
    """Symmetry: message for lane-b is isolated from lane-a."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        submit_message("lane-b", "chatgpt", "claude", "other", storage, TWO_LANES)
        a_messages = storage.list_messages("lane-a")
        assert len(a_messages) == 0


# -- invalid identity rejection ---------------------------------------------

def test_unknown_lane_rejected() -> None:
    """Given: unknown lane ID.  Assert: message creation fails."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        try:
            submit_message("lane-z", "chatgpt", "claude", "nope", storage, TWO_LANES)
            assert False
        except RegistryError:
            pass


def test_disabled_lane_rejected() -> None:
    """Given: disabled lane.  Assert: message creation fails."""
    disabled_lanes = [LANE_A, Lane("lane-b", enabled=False)]
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        try:
            submit_message("lane-b", "chatgpt", "claude", "nope", storage, disabled_lanes)
            assert False
        except RegistryError:
            pass


# -- source/destination validation ------------------------------------------

def test_invalid_source_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        try:
            submit_message("lane-a", "vscode", "claude", "nope", storage, TWO_LANES)
            assert False
        except RoutingError:
            pass


def test_invalid_destination_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        try:
            submit_message("lane-a", "chatgpt", "vscode", "nope", storage, TWO_LANES)
            assert False
        except RoutingError:
            pass


def test_self_routing_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        try:
            submit_message("lane-a", "chatgpt", "chatgpt", "nope", storage, TWO_LANES)
            assert False
        except RoutingError:
            pass


# -- audit trail ------------------------------------------------------------

def test_routing_event_recorded() -> None:
    """Given: message lifecycle.  Assert: creation appears in event log."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        result = submit_message("lane-a", "chatgpt", "claude", "Hello", storage, TWO_LANES)
        events = storage.list_events("lane-a")
        assert len(events) >= 1
        event = events[0]
        assert event["type"] == "message_routed"
        assert event["message_id"] == result["id"]
        assert event["lane_id"] == "lane-a"
        assert event["status"] == "pending"


def test_event_log_human_readable() -> None:
    """Events are plain JSONL — a human can inspect them directly."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        submit_message("lane-a", "chatgpt", "claude", "data", storage, TWO_LANES)
        events_path = Path(td) / "lane-a" / "events.jsonl"
        assert events_path.exists()
        raw = events_path.read_text(encoding="utf-8").strip()
        assert "message_routed" in raw
        assert "message_id" in raw
        assert "timestamp" in raw
