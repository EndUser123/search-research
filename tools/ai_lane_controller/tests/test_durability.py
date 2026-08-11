"""Test durability: canonical mutex, idempotency, command persistence,
scheduler reconstruction, crash-point recovery.
"""
import sys, os, json, tempfile, uuid, subprocess, time, hashlib
sys.path.insert(0, "P:/tools")

from ai_lane_controller.scheduler import (
    UIMutex, Scheduler, DurableCommand, SchedulerError,
    _canonical_mutex_path, _cmd_hash, _check_idem, _record_idem,
    _cmd_dir, _iso_now,
)
from ai_lane_controller.controller import (
    ControllerCommand, create_controller_identity,
)

def test_canonical_mutex_path_resolved():
    path = _canonical_mutex_path()
    assert str(path).endswith("ui-input.lock")

def test_mutex_defaults_to_canonical():
    m = UIMutex()
    assert m.path == _canonical_mutex_path()

def test_create_command_persists():
    id1 = create_controller_identity()
    cmd = ControllerCommand(
        controller_session_id=id1.controller_session_id,
        controller_claim_nonce=id1.controller_claim_nonce,
        controller_fencing_epoch=1,
        command_id=uuid.uuid4().hex[:16],
        idempotency_key=uuid.uuid4().hex[:16],
        target_lane="lane-01",
        expected_lane_claim_nonce=uuid.uuid4().hex,
        expected_lane_fencing_epoch=1,
        operation="deliver", handoff_id=uuid.uuid4().hex[:16],
    )
    sched = Scheduler(["lane-01"])
    dc = sched.create_command(cmd)
    assert dc.state == "CREATED"
    cmd_path = _cmd_dir(id1.controller_session_id, cmd.command_id) / "command.json"
    assert cmd_path.exists()

def test_duplicate_idempotency_key_rejected():
    id1 = create_controller_identity()
    key = uuid.uuid4().hex[:16]
    def _c():
        return ControllerCommand(id1.controller_session_id,
            id1.controller_claim_nonce, 1, uuid.uuid4().hex[:16],
            key, "lane-01", uuid.uuid4().hex, 1, "deliver",
            handoff_id=uuid.uuid4().hex[:16])
    sched = Scheduler(["lane-01"])
    sched.create_command(_c())
    try:
        sched.create_command(_c())
        assert False
    except SchedulerError:
        pass

def test_command_state_transitions():
    id1 = create_controller_identity()
    cmd = ControllerCommand(id1.controller_session_id,
        id1.controller_claim_nonce, 1, uuid.uuid4().hex[:16],
        uuid.uuid4().hex[:16], "lane-01", uuid.uuid4().hex, 1,
        "deliver", handoff_id=uuid.uuid4().hex[:16])
    sched = Scheduler(["lane-01"])
    dc = sched.create_command(cmd)
    for st in ("VALIDATED","QUEUED","ACTIVE","UI_AUTHORIZED","DELIVERED","AWAITING_ACK","VERIFIED"):
        dc = sched.transition_command(dc, st)
    assert dc.state == "VERIFIED"
    try:
        sched.transition_command(dc, "FAILED")
        assert False
    except SchedulerError:
        pass

def test_reconstruct_restores_active_handoff():
    id1 = create_controller_identity()
    cmd = ControllerCommand(id1.controller_session_id,
        id1.controller_claim_nonce, 1, uuid.uuid4().hex[:16],
        uuid.uuid4().hex[:16], "lane-01", uuid.uuid4().hex, 1,
        "deliver", handoff_id=uuid.uuid4().hex[:16])
    s1 = Scheduler(["lane-01"])
    dc = s1.create_command(cmd)
    for st in ("VALIDATED","QUEUED","ACTIVE","UI_AUTHORIZED","DELIVERED"):
        dc = s1.transition_command(dc, st)
    s2 = Scheduler.reconstruct(["lane-01"], id1.controller_session_id)
    assert not s2.is_idle("lane-01")
