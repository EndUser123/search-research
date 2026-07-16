"""Recovery operations for pending lane messages.

The system can recover after process termination without losing messages.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .messages import transition_status
from .storage import MessageStorage


def _event_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def list_pending(storage: MessageStorage) -> list[dict[str, Any]]:
    """Return every pending message across all lanes.

    Messages whose status has not been advanced to *acknowledged* or *failed*
    are considered pending and recoverable.
    """
    pending: list[dict[str, Any]] = []
    for lane_id in storage.all_lane_dirs():
        for msg in storage.list_messages(lane_id):
            if msg.get("status") == "pending":
                pending.append(msg)
    return pending


def acknowledge_message(
    message: dict[str, Any],
    storage: MessageStorage,
) -> dict[str, Any]:
    """Advance a pending message to *acknowledged* status.

    Returns the updated message dict.  The original is preserved and
    the transition is recorded in the event log.
    """
    updated = transition_status(message, "acknowledged")
    lane_id = message["lane_id"]
    msg_id = message["id"]

    meta_path = storage.message_path(lane_id, msg_id)
    meta_path.write_text(
        __import__("json").dumps(updated, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    event = {
        "type": "message_acknowledged",
        "message_id": msg_id,
        "lane_id": lane_id,
        "status": "acknowledged",
        "timestamp": _event_now(),
    }
    storage.append_event(lane_id, event)

    return updated


def recover_pending(storage: MessageStorage) -> list[dict[str, Any]]:
    """Return all pending messages that are recoverable.

    Currently any pending message is recoverable (the system has no
    dead-letter concept at this milestone).  This function exists as
    the single entry-point so recovery policy can be tightened later
    without callers changing.
    """
    return list_pending(storage)

