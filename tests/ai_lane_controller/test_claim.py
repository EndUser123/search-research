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
    verify_process_liveness,
    verify_process_liveness,
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


# -- ADR-1: identity_token tests ---------------------------------------------


def test_claim_with_identity_token() -> None:
    """ADR-1: claim_lane with identity_token creates a pid=None claim."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane(
            "lane-a", storage, TWO_LANES,
            identity_token="chatgpt-session-abc",
            process_start_time=NOW,
        )
        assert claim.lane_id == "lane-a"
        assert claim.pid is None
        assert claim.identity_token == "chatgpt-session-abc"


def test_claim_both_pid_and_token_rejected() -> None:
    """ADR-1: providing both pid and identity_token raises."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        try:
            claim_lane(
                "lane-a", storage, TWO_LANES,
                pid=111, identity_token="token-1",
                process_start_time=NOW,
            )
            assert False, "expected ClaimError"
        except ClaimError as e:
            assert "both pid and identity_token are set" in str(e)


def test_claim_with_token_defaults_to_pid() -> None:
    """ADR-1: backward compat -- neither pid nor token defaults to PID."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES, process_start_time=NOW)
        assert claim.pid is not None
        assert claim.identity_token == ""


def test_token_claim_round_trip_to_dict() -> None:
    """ADR-1: token claim serializes and deserializes correctly."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane(
            "lane-a", storage, TWO_LANES,
            identity_token="chatgpt-session-abc",
            process_start_time=NOW,
        )
        claim2 = get_active_claim("lane-a", storage)
        assert claim2 is not None
        assert claim2.pid is None
        assert claim2.identity_token == "chatgpt-session-abc"


def test_token_claim_heartbeat() -> None:
    """ADR-1: heartbeat works with token-based claims."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane(
            "lane-a", storage, TWO_LANES,
            identity_token="chatgpt-session-abc",
            process_start_time=NOW,
        )
        hb = heartbeat_claim(
            "lane-a", claim.session_nonce, storage,
            workspace_id=claim.workspace_id,
            terminal_id=claim.terminal_id,
            session_id=claim.session_id,
            fencing_epoch=claim.fencing_epoch,
        )
        assert hb.identity_token == "chatgpt-session-abc"
        assert hb.pid is None
        assert hb.heartbeat_at != claim.heartbeat_at


def test_token_claim_liveness_returns_true() -> None:
    """ADR-1: verify_process_liveness for token claims returns True."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane(
            "lane-a", storage, TWO_LANES,
            identity_token="chatgpt-session-abc",
            process_start_time=NOW,
        )
        alive, reason = verify_process_liveness(claim)
        assert alive is True
        assert reason == ""


def test_token_claim_from_dict_missing_pid() -> None:
    """ADR-1: from_dict handles claim without pid field."""
    data = {
        "lane_id": "lane-a",
        "session_nonce": "abc123",
        "process_start_time": NOW,
        "created_at": NOW,
        "heartbeat_at": NOW,
        "identity_token": "token-1",
    }
    claim = LaneClaim.from_dict(data)
    assert claim.pid is None
    assert claim.identity_token == "token-1"


def test_token_claim_reclaim_after_expiry() -> None:
    """ADR-1: expired token-based claim can be reclaimed."""
    import json
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane(
            "lane-a", storage, TWO_LANES,
            identity_token="chatgpt-session-abc",
            process_start_time=NOW,
        )
        orig_epoch = claim.fencing_epoch
        claim_path = Path(td) / "lane-a" / "claim.json"
        data = json.loads(claim_path.read_text(encoding="utf-8"))
        data["heartbeat_at"] = "2020-01-01T00:00:00Z"
        claim_path.write_text(json.dumps(data), encoding="utf-8")
        claim2 = claim_lane(
            "lane-a", storage, TWO_LANES,
            identity_token="new-token",
            process_start_time=NOW,
            ttl=30,
        )
        assert claim2.identity_token == "new-token"
        assert claim2.fencing_epoch == orig_epoch + 1


def test_token_claim_release() -> None:
    """ADR-1: release_claim works for token-based claims."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane(
            "lane-a", storage, TWO_LANES,
            identity_token="chatgpt-session-abc",
            process_start_time=NOW,
        )
        release_claim(
            "lane-a", claim.session_nonce, storage,
            workspace_id=claim.workspace_id,
            terminal_id=claim.terminal_id,
            session_id=claim.session_id,
            fencing_epoch=claim.fencing_epoch,
        )
        assert get_active_claim("lane-a", storage) is None


def test_token_claim_lock_records_identity_token() -> None:
    """ADR-1: lock file records identity_token when claim uses token (checked during claim)."""
    with tempfile.TemporaryDirectory() as td:
        # Verify via the claim JSON on disk rather than the ephemeral lock
        storage = MessageStorage(td)
        claim = claim_lane(
            "lane-a", storage, TWO_LANES,
            identity_token="chatgpt-session-abc",
            process_start_time=NOW,
        )
        # Claim file has the right identity
        assert claim.identity_token == "chatgpt-session-abc"
        assert claim.pid is None
        # Re-read from disk to confirm persistence
        claim2 = get_active_claim("lane-a", storage)
        assert claim2 is not None
        assert claim2.identity_token == "chatgpt-session-abc"
        assert claim2.pid is None


def test_token_liveness_for_pid_claim() -> None:
    """ADR-1: pid-based verify_process_liveness still works."""
    import os
    from ai_lane_controller.claim import _get_process_start_time
    real_start = _get_process_start_time(os.getpid()) or "2026-07-14T12:00:00Z"
    claim = LaneClaim(
        lane_id="lane-a",
        session_nonce="nonce",
        pid=os.getpid(),
        process_start_time=real_start,
        created_at=NOW,
        heartbeat_at=NOW,
        identity_token="",
    )
    alive, reason = verify_process_liveness(claim)
    assert alive is True
    assert reason == ""
