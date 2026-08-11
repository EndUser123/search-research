"""Test Milestone 3A — process liveness validation.

Verifies:
1. Active process identity accepted.
2. Missing process rejected.
3. PID reuse/start-time mismatch rejected.
4. Expired heartbeat rejected.
5. Valid heartbeat extends ownership.
6. Invalid owner cannot heartbeat.
"""

import sys, json, os, tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from ai_lane_controller.registry import Lane
from ai_lane_controller.storage import MessageStorage
from ai_lane_controller.router import RoutingError, submit_message
from ai_lane_controller.claim import (
    ClaimError, LaneClaim, claim_lane,
    get_active_claim, heartbeat_claim,
    _process_exists,
    verify_process_liveness,
)

TWO_LANES = [Lane("lane-a"), Lane("lane-b")]


def test_process_exists_accepts_current_windows_process() -> None:
    assert _process_exists(os.getpid()) is True


def test_liveness_active_process_accepted() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES)
        alive, reason = verify_process_liveness(claim)
        assert alive is True
        assert reason == ""


def test_liveness_active_process_can_submit() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES)
        result = submit_message(
            "lane-a", "chatgpt", "claude", "live",
            storage, TWO_LANES, claim_nonce=claim.session_nonce)
        assert result["status"] == "pending"


def test_liveness_missing_process_rejected() -> None:
    claim = LaneClaim(
        lane_id="lane-b", session_nonce="test-nonce",
        pid=99999999, process_start_time="2026-07-14T12:00:00Z",
        created_at="2026-07-14T12:00:00Z",
        heartbeat_at="2026-07-14T12:00:00Z")
    alive, reason = verify_process_liveness(claim)
    assert alive is False
    assert reason == "process_not_found"


def test_liveness_submit_with_dead_pid_rejected() -> None:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        dead_claim = LaneClaim(
            lane_id="lane-a", session_nonce="dead-session", pid=99999999,
            process_start_time="2026-07-14T12:00:00Z",
            created_at=now, heartbeat_at=now)
        claim_dir = Path(td) / "lane-a"
        claim_dir.mkdir(parents=True, exist_ok=True)
        (claim_dir / "claim.json").write_text(
            json.dumps(dead_claim.to_dict(), indent=2) + "\n",
            encoding="utf-8")
        try:
            submit_message("lane-a", "chatgpt", "claude", "dead",
                storage, TWO_LANES, claim_nonce="dead-session")
            assert False
        except RoutingError as e:
            assert "process_not_found" in str(e)


def test_liveness_pid_recycled_rejected() -> None:
    claim = LaneClaim(
        lane_id="lane-a", session_nonce="recycled", pid=os.getpid(),
        process_start_time="2000-01-01T00:00:00Z",
        created_at="2000-01-01T00:00:00Z",
        heartbeat_at="2000-01-01T00:00:00Z")
    alive, reason = verify_process_liveness(claim)
    assert alive is False
    assert reason == "pid_recycled"


def test_liveness_expired_heartbeat_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES)
        claim_path = Path(td) / "lane-a" / "claim.json"
        old = json.loads(claim_path.read_text(encoding="utf-8"))
        old["heartbeat_at"] = (
            datetime.now(timezone.utc) - timedelta(seconds=120)
        ).isoformat().replace("+00:00", "Z")
        claim_path.write_text(json.dumps(old, indent=2) + "\n", encoding="utf-8")
        active = get_active_claim("lane-a", storage, ttl=30)
        assert active is None
        try:
            submit_message("lane-a", "chatgpt", "claude", "stale-hb",
                storage, TWO_LANES, claim_nonce=claim.session_nonce)
            assert False
        except RoutingError as e:
            assert "not claimed" in str(e).lower() or "stale" in str(e).lower()


def test_liveness_heartbeat_extends_ownership() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES)
        claim_path = Path(td) / "lane-a" / "claim.json"
        old = json.loads(claim_path.read_text(encoding="utf-8"))
        old["heartbeat_at"] = (
            datetime.now(timezone.utc) - timedelta(seconds=25)
        ).isoformat().replace("+00:00", "Z")
        claim_path.write_text(json.dumps(old, indent=2) + "\n", encoding="utf-8")
        active_before = get_active_claim("lane-a", storage, ttl=30)
        assert active_before is not None
        refreshed = heartbeat_claim("lane-a", claim.session_nonce, storage)
        assert refreshed.heartbeat_at > old["heartbeat_at"]
        result = submit_message("lane-a", "chatgpt", "claude", "refreshed",
            storage, TWO_LANES, claim_nonce=claim.session_nonce)
        assert result["status"] == "pending"
        events = storage.list_events("lane-a")
        hb_events = [e for e in events if e["type"] == "heartbeat"]
        assert len(hb_events) >= 1


def test_liveness_invalid_owner_cannot_heartbeat() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim_lane("lane-a", storage, TWO_LANES)
        try:
            heartbeat_claim("lane-a", "wrong-nonce", storage)
            assert False
        except ClaimError:
            pass
        try:
            heartbeat_claim("lane-z", "any-nonce", storage)
            assert False
        except ClaimError:
            pass


def test_liveness_heartbeat_event_recorded() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES)
        events_before = len(storage.list_events("lane-a"))
        heartbeat_claim("lane-a", claim.session_nonce, storage)
        events_after = len(storage.list_events("lane-a"))
        assert events_after > events_before
        hb_events = [e for e in storage.list_events("lane-a")
                     if e["type"] == "heartbeat"]
        assert len(hb_events) == 1
        assert hb_events[0]["lane_id"] == "lane-a"
        assert hb_events[0]["status"] == "acknowledged"
