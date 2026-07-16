"""Test message routing with lane claiming — identity binding prevents cross-lane execution."""

import sys
import json
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from ai_lane_controller.registry import Lane
from ai_lane_controller.router import RoutingError, submit_message
from ai_lane_controller.storage import MessageStorage
from ai_lane_controller.claim import claim_lane

TWO_LANES = [Lane("lane-a"), Lane("lane-b")]


def test_submit_with_valid_claim_succeeds() -> None:
    """A process that holds an active claim can route messages."""
    import os

    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES, pid=os.getpid())
        result = submit_message("lane-a", "chatgpt", "claude", "Hello", storage, TWO_LANES, claim_nonce=claim.session_nonce)
        assert result["status"] == "pending"


def test_submit_without_claim_rejected() -> None:
    """Invalid identity (no claim) cannot submit messages when claim_nonce is required."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        try:
            submit_message("lane-a", "chatgpt", "claude", "fail", storage, TWO_LANES, claim_nonce="no-claim")
            assert False
        except RoutingError as e:
            assert "not claimed" in str(e).lower()


def test_submit_with_wrong_nonce_rejected() -> None:
    """Invalid identity (wrong nonce) cannot submit messages."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time="2026-07-14T12:00:00Z")
        try:
            submit_message("lane-a", "chatgpt", "claude", "evil", storage, TWO_LANES, claim_nonce="bad-nonce")
            assert False
        except RoutingError as e:
            assert "mismatch" in str(e).lower()


def test_cross_lane_claim_rejected() -> None:
    """A process claiming lane-a cannot submit to lane-b."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time="2026-07-14T12:00:00Z")
        try:
            submit_message("lane-b", "chatgpt", "claude", "cross-lane", storage, TWO_LANES, claim_nonce=claim.session_nonce)
            assert False
        except RoutingError as e:
            assert "not claimed" in str(e).lower() or "RegistryError" in str(type(e).__name__)


# -- restart behavior is deterministic ---------------------------------------

def test_restart_deterministic() -> None:
    """After process restart (new storage instance, same dir), pending claims
    from the prior lifetime are stale, but routing with a fresh claim succeeds."""
    import os

    with tempfile.TemporaryDirectory() as td:
        storage1 = MessageStorage(td)
        claim1 = claim_lane("lane-a", storage1, TWO_LANES, pid=os.getpid())

        # Simulate restart: backdate the old claim so it's stale, use nonexistent PID
        claim_path = Path(td) / "lane-a" / "claim.json"
        old_data = json.loads(claim_path.read_text(encoding="utf-8"))
        from datetime import datetime, timezone, timedelta
        old_data["heartbeat_at"] = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat().replace("+00:00", "Z")
        old_data["pid"] = 99999999
        old_data["process_start_time"] = "2026-07-14T10:00:00Z"
        claim_path.write_text(json.dumps(old_data, indent=2) + "\n", encoding="utf-8")

        # New storage instance, no knowledge of old session
        storage2 = MessageStorage(td)

        # Old nonce should not work (stale + PID doesn not exist)
        try:
            submit_message("lane-a", "chatgpt", "claude", "stale", storage2, TWO_LANES, claim_nonce=claim1.session_nonce)
            assert False
        except RoutingError:
            pass

        # Fresh claim works (stale one was reclaimed by new process)
        claim2 = claim_lane("lane-a", storage2, TWO_LANES, pid=os.getpid())
        result = submit_message("lane-a", "chatgpt", "claude", "after-restart", storage2, TWO_LANES, claim_nonce=claim2.session_nonce)
        assert result["status"] == "pending"
