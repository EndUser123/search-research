"""Local router for lane messages.

The router verifies the lane exists, checks source and destination are
allowed, creates durable artifacts, and records a routing event.
It enforces strict isolation: lane-a messages never appear in lane-b.

Milestone 2: validates an active lane claim when ``claim_nonce`` is provided.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .claim import get_active_claim, verify_process_liveness
from .messages import ALLOWED_SOURCES, ALLOWED_DESTINATIONS, create_message
from .registry import RegistryError, lane_exists
from .storage import MessageStorage


class RoutingError(ValueError):
    """Message could not be routed."""


def _event_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def submit_message(
    lane_id: str,
    source: str,
    destination: str,
    payload: str,
    storage: MessageStorage,
    lanes: list[Any],
    *,
    claim_nonce: str | None = None,
    claim_ttl: int = 30,
) -> dict[str, Any]:
    """Route a message through the lane controller.

    Parameters
    ----------
    lane_id:
        Explicit lane identity (e.g. ``"lane-a"``).
    source:
        Sender name (``"chatgpt"`` or ``"claude"``).
    destination:
        Recipient name (``"chatgpt"`` or ``"claude"``).
    payload:
        Markdown/text content of the message.
    storage:
        A ``MessageStorage`` instance.
    lanes:
        List of ``Lane`` objects from the registry.
    claim_nonce:
        When provided, validates that an active claim exists for the lane
        and that its ``session_nonce`` matches.
    claim_ttl:
        Staleness threshold for the claim check (seconds).

    Returns
    -------
    The stored message dict, including its assigned id and payload_path.

    Raises
    ------
    RegistryError
        If *lane_id* is unknown or disabled.
    RoutingError
        If source/destination are invalid, claim validation fails, or
        routing fails.
    """
    if not lane_exists(lanes, lane_id):
        raise RegistryError(f"cannot route: unknown or disabled lane '{lane_id}'")

    # -- claim validation (Milestone 2) ----------------------------------
    if claim_nonce is not None:
        claim = get_active_claim(lane_id, storage, ttl=claim_ttl)
        if claim is None:
            raise RoutingError(f"lane '{lane_id}' is not claimed or claim is stale")
        if claim.session_nonce != claim_nonce:
            raise RoutingError(
                f"claim session_nonce mismatch for lane '{lane_id}'"
            )

        # -- liveness validation (Milestone 3A) --------------------------
        alive, liveness_reason = verify_process_liveness(claim)
        if not alive:
            raise RoutingError(
                f"process liveness check failed for lane '{lane_id}': "
                f"{liveness_reason}"
            )

    if source not in ALLOWED_SOURCES:
        raise RoutingError(
            f"invalid source '{source}'; "
            f"must be one of {{{', '.join(sorted(ALLOWED_SOURCES))}}}"
        )

    if destination not in ALLOWED_DESTINATIONS:
        raise RoutingError(
            f"invalid destination '{destination}'; "
            f"must be one of {{{', '.join(sorted(ALLOWED_DESTINATIONS))}}}"
        )

    if source == destination:
        raise RoutingError("source and destination must be different")

    message = create_message(lane_id, source, destination, payload)
    storage.store_message(message, payload)

    event = {
        "type": "message_routed",
        "message_id": message["id"],
        "lane_id": lane_id,
        "source": source,
        "destination": destination,
        "status": "pending",
        "timestamp": _event_now(),
    }
    storage.append_event(lane_id, event)

    stored = storage.get_message(lane_id, message["id"])
    assert stored is not None

    return stored
