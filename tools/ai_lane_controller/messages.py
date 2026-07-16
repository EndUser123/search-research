"""Versioned message contracts for lane communication.

Schema ``lane-message.v1`` — messages are append-only artifacts with explicit
status transitions.  Invalid messages are rejected with understandable errors.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "lane-message.v1"

ALLOWED_SOURCES = frozenset({"chatgpt", "claude"})
ALLOWED_DESTINATIONS = frozenset({"chatgpt", "claude"})
VALID_STATUSES = frozenset({"pending", "acknowledged", "failed"})

ALLOWED_TRANSITIONS: dict[str, frozenset[str]] = {
    "pending": frozenset({"acknowledged", "failed"}),
}


class MessageValidationError(ValueError):
    """Message failed schema validation."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _message_id() -> str:
    return f"msg-{uuid.uuid4().hex[:24]}"


def create_message(
    lane_id: str,
    source: str,
    destination: str,
    payload: str = "",
    *,
    message_id: str | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    """Build a validated lane-message.v1 dict.

    Payload is stored separately as a markdown/text file; this function
    only assigns the metadata and writes no files.
    """
    msg: dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "id": message_id or _message_id(),
        "lane_id": lane_id,
        "source": source,
        "destination": destination,
        "created_at": created_at or _iso_now(),
        "status": "pending",
        "payload_path": None,
    }
    validate_message(msg)
    return msg


def validate_message(msg: Any) -> None:
    """Raise MessageValidationError if *msg* does not match the contract."""
    errors: list[str] = []

    if not isinstance(msg, dict):
        raise MessageValidationError("message must be a JSON object")

    _check_str(msg, "schema", errors)
    if msg.get("schema") != SCHEMA_VERSION:
        errors.append(f"schema: expected '{SCHEMA_VERSION}', got '{msg.get('schema')}'")

    _check_str(msg, "id", errors)

    lid = msg.get("lane_id")
    _check_str(msg, "lane_id", errors)
    if isinstance(lid, str) and not lid.strip():
        errors.append("lane_id: must not be empty")

    src = msg.get("source")
    _check_str(msg, "source", errors)
    if isinstance(src, str) and src not in ALLOWED_SOURCES:
        errors.append(f"source: '{src}' not in {{{', '.join(sorted(ALLOWED_SOURCES))}}}")

    dest = msg.get("destination")
    _check_str(msg, "destination", errors)
    if isinstance(dest, str) and dest not in ALLOWED_DESTINATIONS:
        errors.append(f"destination: '{dest}' not in {{{', '.join(sorted(ALLOWED_DESTINATIONS))}}}")

    _check_str(msg, "created_at", errors)
    created = msg.get("created_at")
    if isinstance(created, str):
        try:
            datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            errors.append("created_at: invalid ISO-8601 timestamp")

    status = msg.get("status")
    _check_str(msg, "status", errors)
    if isinstance(status, str) and status not in VALID_STATUSES:
        errors.append(f"status: '{status}' not in {{{', '.join(sorted(VALID_STATUSES))}}}")

    payload_path = msg.get("payload_path")
    if payload_path is not None and not isinstance(payload_path, str):
        errors.append("payload_path: must be a string or null")

    if msg.get("source") == msg.get("destination"):
        errors.append("source and destination must be different")

    if errors:
        raise MessageValidationError("; ".join(errors))


def transition_status(msg: dict[str, Any], new_status: str) -> dict[str, Any]:
    """Return a new message dict with an explicit status transition.

    Raises MessageValidationError if the transition is not allowed.
    """
    current = msg["status"]
    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    if new_status not in allowed:
        raise MessageValidationError(
            f"status transition '{current}' -> '{new_status}' not allowed; "
            f"allowed from '{current}': {{{', '.join(sorted(allowed)) or 'none'}}}"
        )
    updated = dict(msg)
    updated["status"] = new_status
    return updated


def _check_str(msg: dict[str, Any], field: str, errors: list[str]) -> None:
    value = msg.get(field)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{field}: expected non-empty string")


def format_message(msg: dict[str, Any]) -> str:
    """Return a human-friendly one-line summary of a message."""
    return (f"[{msg['status']}] {msg['id']}  "
            f"{msg['source']} -> {msg['destination']}  "
            f"lane={msg['lane_id']}  at={msg['created_at']}")

