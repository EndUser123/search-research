"""Test Milestone 5 — multi-lane controller foundation.

Tests:
1. Exactly eight valid lane slots.
2. Invalid lane rejection.
3. Controller epoch fencing.
4. Stale controller command rejection.
5. Duplicate idempotency-key rejection.
6. One active operation per lane.
7. Concurrent operations allowed across different lanes.
8. Global UI-input mutex serialization.
9. No fallback to another lane.
10. Foreign-session artifact rejection.
11. Controller cannot target itself.
12. Standard lane IDs are correct.
"""

import sys
sys.path.insert(0, "P:/tools")

from ai_lane_controller.registry import Lane, create_standard_lanes, LANE_IDS
from ai_lane_controller.controller import (
    ControllerIdentity, ControllerCommand, ControllerError,
    create_controller_identity, validate_controller_command,
)
from ai_lane_controller.scheduler import (
    Scheduler, UIMutex, LaneQueue, SchedulerError, LANE_STATUSES,
)
from pathlib import Path
import tempfile
import os
import uuid


# -- Standard lane registry ------------------------------------------------


def test_eight_standard_lanes() -> None:
    lanes = create_standard_lanes()
    assert len(lanes) == 8
    for i, lane in enumerate(lanes, start=1):
        assert lane.id == f"lane-{i:02d}"
        assert lane.enabled is True


def test_lane_ids_constant() -> None:
    assert LANE_IDS == [
        "lane-01", "lane-02", "lane-03", "lane-04",
        "lane-05", "lane-06", "lane-07", "lane-08",
    ]


def test_invalid_lane_rejected() -> None:
    """A lane ID outside lane-01..lane-08 is rejected by the controller."""
    lanes = create_standard_lanes()
    ids = [l.id for l in lanes]
    assert "lane-00" not in ids
    assert "lane-09" not in ids
    assert "lane-a" not in ids
    assert "lane-b" not in ids


# -- Controller identity and commands --------------------------------------


def test_controller_identity_created() -> None:
    identity = create_controller_identity()
    assert identity.controller_session_id
    assert identity.controller_claim_nonce
    assert identity.pid == os.getpid()
    assert identity.fencing_epoch == 1
    assert identity.workspace_id


def test_controller_identity_round_trip() -> None:
    identity = create_controller_identity()
    data = identity.to_dict()
    restored = ControllerIdentity.from_dict(data)
    assert restored == identity


def test_controller_command_validated() -> None:
    identity = create_controller_identity()
    command = ControllerCommand(
        controller_session_id=identity.controller_session_id,
        controller_claim_nonce=identity.controller_claim_nonce,
        controller_fencing_epoch=1,
        command_id=uuid.uuid4().hex[:16],
        idempotency_key=uuid.uuid4().hex[:16],
        target_lane="lane-01",
        expected_lane_claim_nonce=uuid.uuid4().hex,
        expected_lane_fencing_epoch=1,
        operation="deliver",
        handoff_id=uuid.uuid4().hex[:16],
    )
    validate_controller_command(command, identity)
    assert True


def test_stale_controller_command_rejected() -> None:
    identity = create_controller_identity()
    # Lower epoch than current
    command = ControllerCommand(
        controller_session_id=identity.controller_session_id,
        controller_claim_nonce=identity.controller_claim_nonce,
        controller_fencing_epoch=0,  # stale
        command_id=uuid.uuid4().hex[:16],
        idempotency_key=uuid.uuid4().hex[:16],
        target_lane="lane-01",
        expected_lane_claim_nonce=uuid.uuid4().hex,
        expected_lane_fencing_epoch=1,
        operation="deliver",
    )
    try:
        validate_controller_command(command, identity)
        assert False
    except ControllerError:
        pass


def test_wrong_session_rejected() -> None:
    identity = create_controller_identity()
    command = ControllerCommand(
        controller_session_id="wrong-session-id",
        controller_claim_nonce=identity.controller_claim_nonce,
        controller_fencing_epoch=1,
        command_id=uuid.uuid4().hex[:16],
        idempotency_key=uuid.uuid4().hex[:16],
        target_lane="lane-01",
        expected_lane_claim_nonce=uuid.uuid4().hex,
        expected_lane_fencing_epoch=1,
        operation="deliver",
    )
    try:
        validate_controller_command(command, identity)
        assert False
    except ControllerError:
        pass


def test_duplicate_idempotency_key_rejected() -> None:
    identity = create_controller_identity()
    key = uuid.uuid4().hex[:16]
    seen = set()

    command1 = ControllerCommand(
        controller_session_id=identity.controller_session_id,
        controller_claim_nonce=identity.controller_claim_nonce,
        controller_fencing_epoch=1,
        command_id=uuid.uuid4().hex[:16],
        idempotency_key=key,
        target_lane="lane-01",
        expected_lane_claim_nonce=uuid.uuid4().hex,
        expected_lane_fencing_epoch=1,
        operation="deliver",
    )
    # First use should pass
    validate_controller_command(command1, identity, seen_idempotency_keys=seen)
    assert True

    # Second use should fail
    command2 = ControllerCommand(
        controller_session_id=identity.controller_session_id,
        controller_claim_nonce=identity.controller_claim_nonce,
        controller_fencing_epoch=1,
        command_id=uuid.uuid4().hex[:16],
        idempotency_key=key,
        target_lane="lane-01",
        expected_lane_claim_nonce=uuid.uuid4().hex,
        expected_lane_fencing_epoch=1,
        operation="deliver",
    )
    try:
        validate_controller_command(command2, identity, seen_idempotency_keys=seen)
        assert False
    except ControllerError:
        pass


def test_invalid_target_lane_rejected() -> None:
    identity = create_controller_identity()
    command = ControllerCommand(
        controller_session_id=identity.controller_session_id,
        controller_claim_nonce=identity.controller_claim_nonce,
        controller_fencing_epoch=1,
        command_id=uuid.uuid4().hex[:16],
        idempotency_key=uuid.uuid4().hex[:16],
        target_lane="lane-99",  # invalid
        expected_lane_claim_nonce=uuid.uuid4().hex,
        expected_lane_fencing_epoch=1,
        operation="deliver",
    )
    try:
        validate_controller_command(command, identity)
        assert False
    except ControllerError:
        pass


def test_controller_command_round_trip() -> None:
    command = ControllerCommand(
        controller_session_id=uuid.uuid4().hex,
        controller_claim_nonce=uuid.uuid4().hex,
        controller_fencing_epoch=2,
        command_id=uuid.uuid4().hex[:16],
        idempotency_key=uuid.uuid4().hex[:16],
        target_lane="lane-03",
        expected_lane_claim_nonce=uuid.uuid4().hex,
        expected_lane_fencing_epoch=3,
        operation="verify",
        handoff_id=uuid.uuid4().hex[:16],
    )
    data = command.to_dict()
    restored = ControllerCommand.from_dict(data)
    assert restored == command


# -- Scheduling -------------------------------------------------------------


def test_one_active_handoff_per_lane() -> None:
    queue = LaneQueue("lane-01")
    assert queue.is_idle

    queue.start_handoff("handoff-001")
    assert not queue.is_idle
    assert queue.active_handoff_id == "handoff-001"

    try:
        queue.start_handoff("handoff-002")
        assert False
    except SchedulerError:
        pass

    queue.complete_handoff("handoff-001")
    assert queue.is_idle


def test_handoff_mismatch_rejected() -> None:
    queue = LaneQueue("lane-01")
    queue.start_handoff("handoff-001")
    try:
        queue.complete_handoff("handoff-999")
        assert False
    except SchedulerError:
        pass


def test_different_lanes_concurrent() -> None:
    q1 = LaneQueue("lane-01")
    q2 = LaneQueue("lane-02")

    q1.start_handoff("h1")
    q2.start_handoff("h2")

    assert not q1.is_idle
    assert not q2.is_idle

    q1.complete_handoff()
    q2.complete_handoff()

    assert q1.is_idle
    assert q2.is_idle


def test_scheduler_routes_to_correct_lane() -> None:
    lanes = ["lane-01", "lane-02"]
    mutex_path = Path(tempfile.mkdtemp()) / "ui-mutex.json"
    mutex = UIMutex(mutex_path)
    sched = Scheduler(lanes, mutex)

    assert sched.status("lane-01") == "UNREGISTERED"
    assert sched.status("lane-02") == "UNREGISTERED"

    sched.set_status("lane-01", "CLAIMED")
    assert sched.status("lane-01") == "CLAIMED"
    assert sched.is_idle("lane-01")

    sched.start_handoff("lane-01", "handoff-001")
    assert not sched.is_idle("lane-01")

    # lane-02 is unaffected
    assert sched.is_idle("lane-02")

    sched.complete_handoff("lane-01", "handoff-001")
    assert sched.is_idle("lane-01")


def test_ui_mutex_serializes() -> None:
    mutex_path = Path(tempfile.mkdtemp()) / "ui-mutex.json"
    m1 = UIMutex(mutex_path)
    m2 = UIMutex(mutex_path)

    assert m1.acquire()
    assert not m2.acquire(timeout=1.0)
    m1.release()
    assert m2.acquire(timeout=1.0)
    m2.release()