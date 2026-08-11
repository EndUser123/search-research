"""Test lane identity and registry operations."""

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from ai_lane_controller.registry import (
    Lane,
    RegistryError,
    lane_exists,
    load_registry,
    require_lane,
    save_registry,
)
from ai_lane_controller.messages import (
    ALLOWED_SOURCES,
    ALLOWED_DESTINATIONS,
    MessageValidationError,
    create_message,
    validate_message,
)


# -- lane creation -----------------------------------------------------------

def test_lane_creation() -> None:
    lane = Lane("lane-a")
    assert lane.id == "lane-a"
    assert lane.enabled is True

    d = lane.to_dict()
    assert d == {"id": "lane-a", "enabled": True}

    restored = Lane.from_dict(d)
    assert restored.id == "lane-a"


def test_lane_disabled() -> None:
    lane = Lane("lane-b", enabled=False)
    assert not lane.enabled
    assert not lane_exists([lane], "lane-b")


def test_lane_empty_id_rejected() -> None:
    try:
        Lane("")
        assert False
    except ValueError:
        pass


def test_lane_whitespace_id_rejected() -> None:
    try:
        Lane("  ")
        assert False
    except ValueError:
        pass


# -- registry file round-trip -----------------------------------------------

def test_registry_round_trip() -> None:
    lanes = [Lane("lane-a"), Lane("lane-b", enabled=False)]
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "registry.json"
        save_registry(lanes, path)
        reloaded = load_registry(path)
    assert len(reloaded) == 2
    assert reloaded[0].id == "lane-a"
    assert reloaded[0].enabled is True
    assert reloaded[1].id == "lane-b"
    assert reloaded[1].enabled is False


def test_registry_duplicate_ids_rejected() -> None:
    lanes = [Lane("lane-a"), Lane("lane-a")]
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "registry.json"
        save_registry(lanes, path)
        try:
            load_registry(path)
            assert False
        except ValueError:
            pass


# -- lane existence checks ---------------------------------------------------

def test_lane_exists() -> None:
    lanes = [Lane("lane-a"), Lane("lane-b")]
    assert lane_exists(lanes, "lane-a")
    assert lane_exists(lanes, "lane-b")
    assert not lane_exists(lanes, "lane-c")


def test_require_lane_passes() -> None:
    require_lane([Lane("lane-a")], "lane-a")  # no error


def test_require_lane_raises() -> None:
    try:
        require_lane([Lane("lane-a")], "lane-z")
        assert False
    except RegistryError:
        pass


# -- message creation --------------------------------------------------------

def test_create_message_valid() -> None:
    msg = create_message("lane-a", "chatgpt", "claude", "design review")
    assert msg["schema"] == "lane-message.v1"
    assert msg["lane_id"] == "lane-a"
    assert msg["source"] == "chatgpt"
    assert msg["destination"] == "claude"
    assert msg["status"] == "pending"
    assert msg["payload_path"] is None
    assert msg["id"].startswith("msg-")


def test_create_message_reverse_direction() -> None:
    msg = create_message("lane-b", "claude", "chatgpt", "response")
    assert msg["source"] == "claude"
    assert msg["destination"] == "chatgpt"


def test_unknown_source_rejected() -> None:
    try:
        create_message("lane-a", "vscode", "claude", "")
        assert False
    except MessageValidationError as e:
        assert "source" in str(e)


def test_unknown_destination_rejected() -> None:
    try:
        create_message("lane-a", "chatgpt", "vscode", "")
        assert False
    except MessageValidationError:
        pass


def test_self_message_rejected() -> None:
    try:
        create_message("lane-a", "chatgpt", "chatgpt", "")
        assert False
    except MessageValidationError:
        pass


def test_empty_lane_id_rejected() -> None:
    try:
        create_message("", "chatgpt", "claude", "")
        assert False
    except MessageValidationError:
        pass


# -- schema validation -------------------------------------------------------

def test_validate_existing_message() -> None:
    msg = create_message("lane-a", "chatgpt", "claude", "test")
    validate_message(msg)  # no error


def test_validate_rejects_bad_schema() -> None:
    msg = create_message("lane-a", "chatgpt", "claude", "test")
    msg["schema"] = "wrong.v1"
    try:
        validate_message(msg)
        assert False
    except MessageValidationError:
        pass


def test_validate_rejects_bad_status() -> None:
    msg = create_message("lane-a", "chatgpt", "claude", "test")
    msg["status"] = "invalid_status"
    try:
        validate_message(msg)
        assert False
    except MessageValidationError:
        pass


def test_allowed_lists_contain_expected() -> None:
    assert "chatgpt" in ALLOWED_SOURCES
    assert "claude" in ALLOWED_SOURCES
    assert "chatgpt" in ALLOWED_DESTINATIONS
    assert "claude" in ALLOWED_DESTINATIONS
