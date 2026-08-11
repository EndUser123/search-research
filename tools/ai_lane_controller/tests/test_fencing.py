"""Test Milestone 4 — terminal isolation and stale-writer fencing.

Verifies:
1. Claim carries terminal_id, session_id, workspace_id, fencing_epoch.
2. Two terminals claiming the same lane — second rejected.
3. Stale heartbeat after replacement — rejected with fencing error.
4. Stale release after replacement — rejected with fencing error.
5. Wrong session — rejected.
6. Wrong terminal — rejected.
7. Wrong workspace — rejected.
8. Fencing epoch mismatch — rejected.
9. PID reuse — still rejected.
10. Concurrent claim/replacement — fail-closed.
11. Atomic claim-file visibility — reader never sees partial JSON.
12. Expired claim with live owner — cannot reclaim (liveness-first).
"""

import sys, json, os, tempfile, time
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from ai_lane_controller.registry import Lane, RegistryError
from ai_lane_controller.storage import MessageStorage
from ai_lane_controller.claim import (
    ClaimError, LaneClaim, claim_lane,
    release_claim, get_active_claim, heartbeat_claim,
    verify_process_liveness,
)

TWO_LANES = [Lane("lane-a"), Lane("lane-b")]
PID = os.getpid()
NOW = "2026-07-14T12:00:00Z"
T1 = "terminal-one"
T2 = "terminal-two"
S1 = "session-one"
S2 = "session-two"
W1 = "workspace-one"
W2 = "workspace-two"


# -- identity fields present on new claim ------------------------------------


def test_claim_carries_terminal_session_workspace_epoch() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1, workspace_id=W1,
        )
        assert claim.terminal_id == T1
        assert claim.session_id == S1
        assert claim.workspace_id == W1
        assert claim.fencing_epoch == 1


def test_first_claim_epoch_is_one() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW)
        assert claim.fencing_epoch == 1


# -- two terminals cannot claim the same lane --------------------------------


def test_two_terminals_same_lane_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1,
        )
        try:
            claim_lane(
                "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
                terminal_id=T2, session_id=S2,
            )
            assert False
        except ClaimError:
            pass
        # First claim still active
        assert get_active_claim("lane-a", storage) is not None
        assert get_active_claim("lane-a", storage).session_nonce == c1.session_nonce


# -- stale heartbeat after replacement ---------------------------------------


def test_stale_heartbeat_after_replacement_rejected() -> None:
    """After an expired claim is taken over, the old nonce and epoch cannot
    heartbeat — fencing epoch mismatch rejects it."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        # Create a claim with a dead PID and expired heartbeat
        dead_pid = 99999998
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=dead_pid, process_start_time=NOW,
            terminal_id=T1, session_id=S1, workspace_id=W1,
        )
        assert c1.fencing_epoch == 1

        # Backdate heartbeat to make it expired
        cp = Path(td) / "lane-a" / "claim.json"
        old_data = json.loads(cp.read_text(encoding="utf-8"))
        old_ts = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat().replace("+00:00", "Z")
        old_data["heartbeat_at"] = old_ts
        cp.write_text(json.dumps(old_data, indent=2) + "\n", encoding="utf-8")

        # Take over — epoch must increment to 2
        c2 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=222, process_start_time=NOW,
            terminal_id=T1, session_id=S2, workspace_id=W1,
        )
        assert c2.fencing_epoch == 2

        # Trying to heartbeat with c1's nonce and epoch=1 — epoch mismatch
        try:
            heartbeat_claim("lane-a", c1.session_nonce, storage,
                            terminal_id=T1, session_id=S1, workspace_id=W1,
                            fencing_epoch=1)
            assert False
        except ClaimError as e:
            assert "epoch" in str(e).lower() or "mismatch" in str(e).lower() or "superseded" in str(e).lower()


# -- stale release after replacement -----------------------------------------


def test_stale_release_after_replacement_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1, workspace_id=W1,
        )
        # Release and reclaim
        release_claim("lane-a", c1.session_nonce, storage,
                       terminal_id=T1, session_id=S1, workspace_id=W1,
                       fencing_epoch=1)

        c2 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1, workspace_id=W1,
        )

        # Old c1 release with epoch 1 — fencing rejects it
        try:
            release_claim("lane-a", c1.session_nonce, storage,
                           terminal_id=T1, session_id=S1, workspace_id=W1,
                           fencing_epoch=1)
            assert False
        except ClaimError as e:
            assert "mismatch" in str(e).lower() or "epoch" in str(e).lower() or "superseded" in str(e).lower()


# -- wrong session -----------------------------------------------------------


def test_wrong_session_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1,
        )
        try:
            heartbeat_claim("lane-a", c1.session_nonce, storage,
                            terminal_id=T1, session_id=S2)
            assert False
        except ClaimError as e:
            assert "session" in str(e).lower() or "mismatch" in str(e).lower()


# -- wrong terminal ----------------------------------------------------------


def test_wrong_terminal_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1,
        )
        try:
            heartbeat_claim("lane-a", c1.session_nonce, storage,
                            terminal_id=T2, session_id=S1)
            assert False
        except ClaimError as e:
            assert "terminal" in str(e).lower() or "mismatch" in str(e).lower()


# -- wrong workspace ---------------------------------------------------------


def test_wrong_workspace_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            workspace_id=W1,
        )
        try:
            heartbeat_claim("lane-a", c1.session_nonce, storage, workspace_id=W2)
            assert False
        except ClaimError as e:
            assert "workspace" in str(e).lower() or "mismatch" in str(e).lower()


# -- fencing epoch mismatch --------------------------------------------------


def test_fencing_epoch_mismatch_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1,
        )
        # epoch 2 does not match on-disk epoch 1
        try:
            heartbeat_claim("lane-a", c1.session_nonce, storage,
                            terminal_id=T1, session_id=S1, fencing_epoch=2)
            assert False
        except ClaimError as e:
            assert "mismatch" in str(e).lower() or "epoch" in str(e).lower() or "superseded" in str(e).lower()


def test_same_fencing_epoch_ok() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1,
        )
        # heartbeat with correct epoch 1 succeeds
        hb = heartbeat_claim("lane-a", c1.session_nonce, storage,
                              terminal_id=T1, session_id=S1, fencing_epoch=1)
        assert hb is not None


# -- PID reuse ---------------------------------------------------------------


def test_pid_reuse_rejected() -> None:
    """PID reuse must still be rejected (Milestone 2 invariant)."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim_lane(
            "lane-a", storage, TWO_LANES, pid=999,
            process_start_time="2026-07-14T10:00:00Z",
        )
        try:
            claim_lane(
                "lane-a", storage, TWO_LANES, pid=999,
                process_start_time="2026-07-14T11:00:00Z",
            )
            assert False
        except ClaimError as e:
            assert "recycled" in str(e).lower() or "reuse" in str(e).lower() or "mismatch" in str(e).lower()


# -- concurrent claim/replacement --------------------------------------------


def test_concurrent_claim_replacement_first_wins() -> None:
    """Two concurrent claim attempts — first to acquire the lock wins."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1,
        )
        # Second attempt with same active claim — must fail
        try:
            claim_lane(
                "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
                terminal_id=T1, session_id=S2,
            )
            assert False
        except ClaimError:
            pass
        assert get_active_claim("lane-a", storage).session_nonce == c1.session_nonce


def test_concurrent_heartbeat_release_race() -> None:
    """A heartbeat while a concurrent release happens — both acquire the
    lock sequentially; one succeeds, the other encounters a removed claim."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1, workspace_id=W1,
        )

        # Release the claim as if another path released it
        release_claim("lane-a", c1.session_nonce, storage,
                       terminal_id=T1, session_id=S1, workspace_id=W1,
                       fencing_epoch=1)

        # Heartbeat after release — must fail
        try:
            heartbeat_claim("lane-a", c1.session_nonce, storage,
                            terminal_id=T1, session_id=S1, workspace_id=W1,
                            fencing_epoch=1)
            assert False
        except ClaimError as e:
            assert "no active claim" in str(e).lower()


# -- atomic claim-file visibility --------------------------------------------


def test_atomic_write_reader_never_sees_partial() -> None:
    """Even if we simulate an interrupted write, a reader sees the old valid
    claim (or the new valid claim, or nothing) — never partial JSON."""
    from ai_lane_controller.claim import _claim_path
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1,
        )
        cp = _claim_path(storage, "lane-a")

        # Simulate a truncated file (what a non-atomic writer would produce)
        with open(cp, "wb") as f:
            f.write(b'{"lane_id": "lane-a", "session_nonce": "')
            f.flush()
            os.fsync(f.fileno())

        # Reader must not raise — should treat corrupt file as no claim
        active = get_active_claim("lane-a", storage)
        # Partial file is not valid JSON, so get_active_claim returns None
        assert active is None, "reader must not return partial claim"


def test_read_after_atomic_write_consistent() -> None:
    """After a normal atomic write, the reader sees consistent data."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=111, process_start_time=NOW,
            terminal_id=T1, session_id=S1, workspace_id=W1,
        )
        active = get_active_claim("lane-a", storage)
        assert active is not None
        assert active.pid == 111
        assert active.terminal_id == T1
        assert active.workspace_id == W1
        assert active.fencing_epoch == 1


# -- expired claim with live owner cannot be reclaimed -----------------------


def test_expired_claim_live_owner_cannot_reclaim() -> None:
    """An expired claim whose owner process is still alive must not be
    reclaimable — prevents stealing a live-but-slow heartbeat."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1,
        )
        # Backdate the heartbeat so the claim appears expired
        cp = Path(td) / "lane-a" / "claim.json"
        old_data = json.loads(cp.read_text(encoding="utf-8"))
        old_data["heartbeat_at"] = (
            datetime.now(timezone.utc) - timedelta(seconds=120)
        ).isoformat().replace("+00:00", "Z")
        cp.write_text(json.dumps(old_data, indent=2) + "\n", encoding="utf-8")

        # Active check should show stale
        assert get_active_claim("lane-a", storage, ttl=30) is None

        # Reclaim attempt should fail — owner is still this process
        try:
            claim_lane(
                "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
                terminal_id=T2, session_id=S2,
            )
            assert False
        except ClaimError as e:
            assert "still alive" in str(e).lower()


# -- release validates identity ----------------------------------------------


def test_release_wrong_terminal_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1,
        )
        try:
            release_claim("lane-a", c1.session_nonce, storage,
                           terminal_id=T2, session_id=S1)
            assert False
        except ClaimError as e:
            assert "terminal" in str(e).lower() or "mismatch" in str(e).lower()


# -- fencing epoch increments on replacement ---------------------------------


def test_fencing_epoch_increments_on_replacement() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        c1 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=PID, process_start_time=NOW,
            terminal_id=T1, session_id=S1, workspace_id=W1,
        )
        assert c1.fencing_epoch == 1

        # Manually kill the claim (simulate dead process), then reclaim
        # Set the owner to a dead PID so the expired-claim liveness check passes.
        cp = Path(td) / "lane-a" / "claim.json"
        old_data = json.loads(cp.read_text(encoding="utf-8"))
        old_ts = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat().replace("+00:00", "Z")
        old_data["heartbeat_at"] = old_ts
        old_data["pid"] = 99999999  # dead PID
        old_data["process_start_time"] = "2000-01-01T00:00:00Z"
        cp.write_text(json.dumps(old_data, indent=2) + "\n", encoding="utf-8")

        c2 = claim_lane(
            "lane-a", storage, TWO_LANES, pid=222, process_start_time=NOW,
            terminal_id=T1, session_id=S2, workspace_id=W1,
        )
        assert c2.fencing_epoch == 2  # incremented from c1's epoch 1
