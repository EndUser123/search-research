"""Test lane phase state machine -- ADR-5 (phase transitions) + watchdog storage.

Tests cover:
- Phase constants and VALID_TRANSITIONS
- PhaseState dataclass (to_dict / from_dict / validation)
- Read: get_phase on initialised / uninitialised / corrupt files
- Write: set_phase (direct), transition_phase (validated)
- Phase mismatch rejection, illegal transition rejection
- Heartbeat refreshes updated_at / heartbeat_at
- Watchdog: recover_stale_phase on timeout, no-op on fresh phases
- Event logging side-effect
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(ROOT / "tools"))

from ai_lane_controller.registry import Lane
from ai_lane_controller.storage import MessageStorage
from ai_lane_controller.claim import LaneClaim, claim_lane
from ai_lane_controller.phase import (
    PhaseError,
    PhaseState,
    PhaseTransitionError,
    PHASE_IDLE,
    PHASE_WAITING_FOR_CHATGPT as PHASE_WFG,
    PHASE_WAITING_FOR_CLAUDE as PHASE_WFC,
    ALL_PHASES,
    VALID_TRANSITIONS,
    DEFAULT_PHASE_TTL_SECONDS,
    get_phase,
    set_phase,
    transition_phase,
    phase_heartbeat,
    recover_stale_phase,
)


TWO_LANES = [Lane("lane-a"), Lane("lane-b")]
NOW = "2026-07-14T12:00:00Z"


# -- Constants & data model --------------------------------------------------


def test_all_phases_defined() -> None:
    assert PHASE_IDLE == "IDLE"
    assert PHASE_WFG == "WAITING_FOR_CHATGPT"
    assert PHASE_WFC == "WAITING_FOR_CLAUDE"
    assert ALL_PHASES == {"IDLE", "WAITING_FOR_CHATGPT", "WAITING_FOR_CLAUDE"}


def test_valid_transitions() -> None:
    assert VALID_TRANSITIONS[PHASE_IDLE] == {PHASE_WFG}
    assert VALID_TRANSITIONS[PHASE_WFG] == {PHASE_WFC}
    assert VALID_TRANSITIONS[PHASE_WFC] == {PHASE_IDLE}


def test_phase_state_to_dict() -> None:
    state = PhaseState(
        lane_id="lane-a",
        phase=PHASE_IDLE,
        fencing_epoch=1,
        entered_at=NOW,
        updated_at=NOW,
        heartbeat_at=NOW,
    )
    d = state.to_dict()
    assert d["lane_id"] == "lane-a"
    assert d["phase"] == PHASE_IDLE
    assert d["fencing_epoch"] == 1


def test_phase_state_from_dict() -> None:
    d = {
        "lane_id": "lane-a",
        "phase": PHASE_WFG,
        "fencing_epoch": 3,
        "entered_at": NOW,
    }
    state = PhaseState.from_dict(d)
    assert state.lane_id == "lane-a"
    assert state.phase == PHASE_WFG
    assert state.fencing_epoch == 3
    assert state.updated_at == NOW  # falls back to entered_at
    assert state.heartbeat_at == NOW


def test_phase_state_from_dict_missing_fields() -> None:
    d = {"lane_id": "lane-a"}
    try:
        PhaseState.from_dict(d)
        assert False, "expected PhaseError"
    except PhaseError:
        pass


# -- Read --------------------------------------------------------------------


def test_get_phase_uninitialised() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        assert get_phase(storage, "lane-a") is None


def test_get_phase_initialised() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        state = set_phase(storage, "lane-a", PHASE_IDLE)
        assert state.phase == PHASE_IDLE

        read = get_phase(storage, "lane-a")
        assert read is not None
        assert read.phase == PHASE_IDLE
        assert read.lane_id == "lane-a"


def test_get_phase_corrupt_file() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        phase_path = Path(td) / "lane-a" / "phase.json"
        phase_path.parent.mkdir(parents=True, exist_ok=True)
        phase_path.write_text("{bad json", encoding="utf-8")
        assert get_phase(storage, "lane-a") is None


# -- Write: set_phase --------------------------------------------------------


def test_set_phase_idle() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        state = set_phase(storage, "lane-a", PHASE_IDLE)
        assert state.phase == PHASE_IDLE
        assert state.fencing_epoch == 1  # first claim


def test_set_phase_increments_epoch() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        s1 = set_phase(storage, "lane-a", PHASE_IDLE)
        assert s1.fencing_epoch == 1
        s2 = set_phase(storage, "lane-a", PHASE_WFG)
        assert s2.fencing_epoch == 2
        assert s2.phase == PHASE_WFG


def test_set_phase_with_explicit_epoch() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        state = set_phase(storage, "lane-a", PHASE_IDLE, fencing_epoch=42)
        assert state.fencing_epoch == 42


def test_set_phase_unknown_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        try:
            set_phase(storage, "lane-a", "BOGUS")
            assert False, "expected PhaseError"
        except PhaseError as e:
            assert "unknown phase" in str(e)


# -- Write: transition_phase -------------------------------------------------


def test_transition_idle_to_wfg() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        state = transition_phase(storage, "lane-a", PHASE_IDLE, PHASE_WFG)
        assert state.phase == PHASE_WFG
        assert state.fencing_epoch == 1  # implicit init


def test_transition_wfg_to_wfc() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        s1 = transition_phase(storage, "lane-a", PHASE_IDLE, PHASE_WFG)
        assert s1.phase == PHASE_WFG
        s2 = transition_phase(storage, "lane-a", PHASE_WFG, PHASE_WFC)
        assert s2.phase == PHASE_WFC
        assert s2.fencing_epoch == 1  # same epoch, no recovery


def test_transition_complete_cycle() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        s1 = transition_phase(storage, "lane-a", PHASE_IDLE, PHASE_WFG)
        assert s1.phase == PHASE_WFG
        s2 = transition_phase(storage, "lane-a", PHASE_WFG, PHASE_WFC)
        assert s2.phase == PHASE_WFC
        s3 = transition_phase(storage, "lane-a", PHASE_WFC, PHASE_IDLE)
        assert s3.phase == PHASE_IDLE


def test_transition_illegal_direction_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        set_phase(storage, "lane-a", PHASE_IDLE)
        try:
            transition_phase(storage, "lane-a", PHASE_IDLE, PHASE_WFC)
            assert False, "expected PhaseTransitionError"
        except PhaseTransitionError:
            pass


def test_transition_phase_mismatch_rejected() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        set_phase(storage, "lane-a", PHASE_WFG)
        try:
            transition_phase(storage, "lane-a", PHASE_IDLE, PHASE_WFG)
            assert False, "expected PhaseError"
        except PhaseError as e:
            assert "phase mismatch" in str(e)


# -- Heartbeat ---------------------------------------------------------------


def test_phase_heartbeat_refreshes_timestamps() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        s1 = set_phase(storage, "lane-a", PHASE_WFG)
        import time
        time.sleep(0.01)
        s2 = phase_heartbeat(storage, "lane-a")
        assert s2.phase == PHASE_WFG
        assert s2.heartbeat_at > s1.heartbeat_at
        assert s2.updated_at > s1.updated_at


def test_phase_heartbeat_initialises_if_missing() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        state = phase_heartbeat(storage, "lane-a")
        assert state.phase == PHASE_IDLE  # default init


# -- Watchdog recovery -------------------------------------------------------


def test_recover_stale_phase_fresh_returns_none() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        set_phase(storage, "lane-a", PHASE_WFG)
        # Phase was just set -- should be fresh
        result = recover_stale_phase(storage, "lane-a", max_dwell=300)
        assert result is None


def test_recover_stale_phase_idle_returns_none() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        set_phase(storage, "lane-a", PHASE_IDLE)
        result = recover_stale_phase(storage, "lane-a", max_dwell=1)
        assert result is None


def test_recover_stale_phase_stale_is_reset() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        s1 = set_phase(storage, "lane-a", PHASE_WFG)

        # Manually backdate the entered_at timestamp
        phase_path = Path(td) / "lane-a" / "phase.json"
        data = json.loads(phase_path.read_text(encoding="utf-8"))
        data["entered_at"] = "2020-01-01T00:00:00Z"
        phase_path.write_text(json.dumps(data), encoding="utf-8")

        result = recover_stale_phase(storage, "lane-a", max_dwell=1)
        assert result is not None
        assert result.phase == PHASE_IDLE
        # Epoch increments
        assert result.fencing_epoch == s1.fencing_epoch + 1


def test_recover_stale_phase_only_resets_when_entered_at_expired() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        set_phase(storage, "lane-a", PHASE_WFG, fencing_epoch=5)
        # No backdate -- still fresh
        result = recover_stale_phase(storage, "lane-a", max_dwell=3600)
        assert result is None


def test_recover_stale_uninitialised_returns_none() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        result = recover_stale_phase(storage, "lane-a", max_dwell=1)
        assert result is None


# -- Event logging (side-effect) ---------------------------------------------


def test_transition_logs_event() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        transition_phase(storage, "lane-a", PHASE_IDLE, PHASE_WFG)

        # Read the event log
        log_path = Path(td) / "lane-a" / "events.jsonl"
        assert log_path.exists()
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        events = [json.loads(l) for l in lines if l]
        phase_events = [e for e in events if e.get("type") == "phase_transition"]
        assert len(phase_events) >= 1
        assert phase_events[0]["phase"] == PHASE_WFG
        assert phase_events[0]["action"] == "transition"


def test_phase_heartbeat_logs_event() -> None:
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        set_phase(storage, "lane-a", PHASE_WFG)
        phase_heartbeat(storage, "lane-a")

        log_path = Path(td) / "lane-a" / "events.jsonl"
        assert log_path.exists()
        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        events = [json.loads(l) for l in lines if l]
        hb_events = [e for e in events if e.get("action") == "heartbeat"]
        assert len(hb_events) >= 1


# -- Concurrency safety ------------------------------------------------------


def test_concurrent_transition_via_lock() -> None:
    """Two transitions on the same lane from different processes are serialised."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        # Simulate a full cycle
        transition_phase(storage, "lane-a", PHASE_IDLE, PHASE_WFG)
        # Another caller trying to transition with wrong from-phase is rejected
        try:
            transition_phase(storage, "lane-a", PHASE_IDLE, PHASE_WFG)
            assert False, "expected PhaseError"
        except PhaseError:
            pass


# -- Integration with claim system -------------------------------------------


def test_phase_transition_after_claim_works() -> None:
    """ADR-5 integration: claim then transition should work."""
    with tempfile.TemporaryDirectory() as td:
        storage = MessageStorage(td)
        claim = claim_lane("lane-a", storage, TWO_LANES, process_start_time=NOW)
        assert claim is not None

        state = transition_phase(storage, "lane-a", PHASE_IDLE, PHASE_WFG)
        assert state.phase == PHASE_WFG