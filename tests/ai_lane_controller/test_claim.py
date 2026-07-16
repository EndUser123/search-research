"""Test lane claiming — identity binding, mutual exclusion, staleness.

Identity must include: lane_id, session_nonce, pid, process_start_time,
created_at, heartbeat_at.  PID alone is insufficient authority.
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from ai_lane_controller.registry import Lane, RegistryError
from ai_lane_controller.storage import MessageStorage
from ai_lane_controller.claim import (
    ClaimError,
    LaneClaim,
    claim_lane,
    release_claim,
    get_active_claim,
    heartbeat_claim,
    require_claim,
)


TWO_LANES = [Lane("lane-a"), Lane("lane-b")]
NOW = "2026-07-14T12:00:00Z"


# -- identity fields --------------------------------------------------------

def test_claim_contains_all_identity_fields() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        assert claim.lane_id == "lane-a"
        assert isinstance(claim.session_nonce, str) and len(claim.session_nonce) == 32
        assert claim.pid == 111
        assert claim.process_start_time == NOW
        assert claim.created_at is not None
        assert claim.heartbeat_at is not None
        assert claim.created_at == claim.heartbeat_at


def test_claim_persisted_to_filesystem() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        claim_path = Path(td) / "lane-a" / "claim.json"
        assert claim_path.exists()
        on_disk = json.loads(claim_path.read_text(encoding="utf-8"))
        assert on_disk["session_nonce"] == claim.session_nonce
        assert on_disk["pid"] == 111


def test_claim_unknown_lane_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        try:
            claim_lane("lane-z", storage, TWO_LANES, pid=111, process_start_time=NOW)
            assert False
        except RegistryError:
            pass


# -- mutual exclusion -------------------------------------------------------

def test_two_processes_cannot_claim_same_lane() -> None:
    """Requirement: two processes cannot claim same lane simultaneously."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        try:
            claim_lane("lane-a", storage, TWO_LANES, pid=222, process_start_time=NOW)
            assert False
        except ClaimError:
            pass
        # first claim still active
        active = get_active_claim("lane-a", storage)
        assert active is not None
        assert active.session_nonce == c1.session_nonce


def test_two_lanes_claimed_independently() -> None:
    """Different lanes can be claimed simultaneously."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        ca = claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        cb = claim_lane("lane-b", storage, TWO_LANES, pid=222, process_start_time=NOW)
        assert ca.lane_id == "lane-a"
        assert cb.lane_id == "lane-b"
        assert ca.session_nonce != cb.session_nonce


def test_release_allows_reclaim() -> None:
    """After release, a different process can claim the lane."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        release_claim("lane-a", c1.session_nonce, storage)
        c2 = claim_lane("lane-a", storage, TWO_LANES, pid=222, process_start_time=NOW)
        assert c2.pid == 222
        assert c2.session_nonce != c1.session_nonce


def test_release_with_wrong_nonce_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        try:
            release_claim("lane-a", "wrong-nonce", storage)
            assert False
        except ClaimError:
            pass


# -- PID reuse detection ----------------------------------------------------

def test_pid_reuse_detected() -> None:
    """Requirement: PID reuse detected — same PID, different process_start_time."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim_lane("lane-a", storage, TWO_LANES, pid=999, process_start_time="2026-07-14T10:00:00Z")
        try:
            claim_lane("lane-a", storage, TWO_LANES, pid=999, process_start_time="2026-07-14T11:00:00Z")
            assert False
        except ClaimError as e:
            assert "recycled" in str(e).lower() or "reuse" in str(e).lower() or "mismatch" in str(e).lower()


# -- stale claims -----------------------------------------------------------

def test_stale_claim_rejected_for_submit() -> None:
    """Requirement: stale claims are rejected."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        # Create a claim with an old heartbeat
        claim = claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        # Manually backdate the heartbeat to exceed TTL
        claim_path = Path(td) / "lane-a" / "claim.json"
        old = json.loads(claim_path.read_text(encoding="utf-8"))
        old_time = datetime.now(timezone.utc) - timedelta(seconds=120)
        old["heartbeat_at"] = old_time.isoformat().replace("+00:00", "Z")
        claim_path.write_text(json.dumps(old, indent=2) + "\n", encoding="utf-8")

        active = get_active_claim("lane-a", storage, ttl=30)
        assert active is None  # stale -> not active


def test_stale_claim_can_be_reclaimed() -> None:
    """A stale claim can be reclaimed by a new process."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        claim_path = Path(td) / "lane-a" / "claim.json"
        old = json.loads(claim_path.read_text(encoding="utf-8"))
        old_time = datetime.now(timezone.utc) - timedelta(seconds=120)
        old["heartbeat_at"] = old_time.isoformat().replace("+00:00", "Z")
        claim_path.write_text(json.dumps(old, indent=2) + "\n", encoding="utf-8")

        new_claim = claim_lane("lane-a", storage, TWO_LANES, pid=222, process_start_time=NOW)
        assert new_claim.pid == 222
        assert new_claim.session_nonce != claim.session_nonce


def test_heartbeat_refreshes_staleness() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        refreshed = heartbeat_claim("lane-a", claim.session_nonce, storage)
        assert refreshed.heartbeat_at >= claim.heartbeat_at
        active = get_active_claim("lane-a", storage)
        assert active is not None


def test_heartbeat_wrong_nonce_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        try:
            heartbeat_claim("lane-a", "wrong-nonce", storage)
            assert False
        except ClaimError:
            pass


# -- duplicate active claims -----------------------------------------------

def test_duplicate_active_claim_rejected() -> None:
    """Requirement: duplicate active claims rejected (same lane)."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        try:
            claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
            assert False
        except ClaimError:
            pass


def test_require_claim_raises_when_unclaimed() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        try:
            require_claim("lane-a", storage)
            assert False
        except ClaimError:
            pass


def test_require_claim_returns_active() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW)
        active = require_claim("lane-a", storage)
        assert active.session_nonce == claim.session_nonce
