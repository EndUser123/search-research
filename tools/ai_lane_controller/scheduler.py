"""Lane scheduling, durable commands, and canonical UI-input mutex."""
from __future__ import annotations
import hashlib, json, os, time, uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

class SchedulerError(RuntimeError):
    """Scheduling or mutex operation failed."""
    pass

LANE_STATUSES = {
    "UNREGISTERED","CLAIMED","WINDOW_BOUND","READY","DELIVERING",
    "AWAITING_OUTPUT","VERIFYING","VERIFIED","CORRECTION_PENDING",
    "FAILED","STALE_BINDING","QUARANTINED","DISABLED",
}

COMMAND_STATES = {
    "CREATED","VALIDATED","QUEUED","ACTIVE","UI_AUTHORIZED",
    "DELIVERED","AWAITING_ACK","VERIFIED","FAILED","CANCELLED",
    "STALE_REJECTED","RECOVERY_REQUIRES_RECONCILIATION",
}

_CMD_TRANS = {
    "CREATED":{"VALIDATED","STALE_REJECTED","CANCELLED"},
    "VALIDATED":{"QUEUED","ACTIVE","STALE_REJECTED","CANCELLED"},
    "QUEUED":{"ACTIVE","CANCELLED"},
    "ACTIVE":{"UI_AUTHORIZED","CANCELLED","FAILED","RECOVERY_REQUIRES_RECONCILIATION"},
    "UI_AUTHORIZED":{"DELIVERED","FAILED","CANCELLED"},
    "DELIVERED":{"AWAITING_ACK","FAILED","RECOVERY_REQUIRES_RECONCILIATION"},
    "AWAITING_ACK":{"VERIFIED","FAILED","RECOVERY_REQUIRES_RECONCILIATION"},
    "VERIFIED":set(),"FAILED":set(),"CANCELLED":set(),"STALE_REJECTED":set(),
    "RECOVERY_REQUIRES_RECONCILIATION":{"FAILED","VERIFIED","CANCELLED"},
}

AI_LANE_ROOT = Path("P:/.ai-lanes")

def _canonical_mutex_path() -> Path:
    return (AI_LANE_ROOT / "controller" / "locks" / "ui-input.lock").resolve()

def _workspace_id() -> str:
    try: root = str(AI_LANE_ROOT.resolve())
    except Exception: root = "P:/.ai-lanes"
    return hashlib.sha256(root.encode("utf-8")).hexdigest()[:16]

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def _get_process_start_time(pid):
    import platform, ctypes
    from ctypes import wintypes
    if platform.system() != "Windows": return None
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    h = k32.OpenProcess(0x1000, False, pid)
    if not h: return None
    try:
        c = wintypes.FILETIME()
        if not k32.GetProcessTimes(h, ctypes.byref(c), ctypes.byref(wintypes.FILETIME()), ctypes.byref(wintypes.FILETIME()), ctypes.byref(wintypes.FILETIME())): return None
        ns = (c.dwHighDateTime << 32) | c.dwLowDateTime
        return (datetime(1601, 1, 1, tzinfo=timezone.utc) + timedelta(microseconds=ns // 10)).isoformat().replace("+00:00", "Z")
    finally: k32.CloseHandle(h)

def _process_is_valid(pid, start_time):
    import platform
    if platform.system() != "Windows": return _proc_exists(pid)
    if not start_time: return False
    a = _get_process_start_time(pid)
    if not a: return False
    t1 = datetime.fromisoformat(a.replace("Z", "+00:00"))
    t2 = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
    return abs((t1 - t2).total_seconds()) <= 2.0

def _proc_exists(pid):
    import platform
    if platform.system() == "Windows":
        import ctypes
        h = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if h: ctypes.windll.kernel32.CloseHandle(h); return True
        return False
    try: os.kill(pid, 0); return True
    except: return False

class UIMutex:
    def __init__(self, path=None):
        self._path = Path(path).resolve() if path else _canonical_mutex_path()
        self._locked = False; self._owner_pid = None
    @property
    def path(self): return self._path
    @property
    def owner_pid(self): return self._owner_pid
    def acquire(self, pid=None, *, timeout=30.0, workspace_id=None):
        pid = pid or os.getpid(); ws = workspace_id or _workspace_id()
        ps = _get_process_start_time(pid); deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                with self._path.open("x", encoding="utf-8") as f:
                    f.write(json.dumps({"pid": pid, "process_start_time": ps, "workspace_id": ws, "at": _iso_now()}) + "\n")
                self._locked = True; self._owner_pid = pid; return True
            except FileExistsError:
                if self._path.exists():
                    try:
                        d = json.loads(self._path.read_text(encoding="utf-8"))
                        hp = int(d.get("pid", 0)); hs = d.get("process_start_time"); hw = d.get("workspace_id", "")
                        if hw and ws and hw != ws: raise SchedulerError(f"workspace mismatch: {hw} != {ws}")
                        if not _process_is_valid(hp, hs): self._path.unlink(missing_ok=True); continue
                    except SchedulerError: raise
                    except: self._path.unlink(missing_ok=True); continue
            time.sleep(0.1)
        return False
    def release(self, pid=None):
        pid = pid or os.getpid()
        if self._owner_pid is not None and self._owner_pid != pid:
            raise SchedulerError(f"PID {pid} cannot release mutex held by PID {self._owner_pid}")
        if self._locked: self._path.unlink(missing_ok=True); self._locked = False; self._owner_pid = None
def _append_event(session_id, event):
    d = AI_LANE_ROOT / "controller" / "sessions" / session_id
    d.mkdir(parents=True, exist_ok=True)
    with (d / "events.jsonl").open("a", encoding="utf-8", newline="\n") as f:
        json.dump(event, f, ensure_ascii=False); f.write("\n")

@dataclass(frozen=True)
class DurableCommand:
    command: Any
    command_hash: str
    controller_session_id: str
    controller_claim_nonce: str
    controller_fencing_epoch: int
    target_lane: str
    target_lane_claim_nonce: str
    target_lane_fencing_epoch: int
    idempotency_key: str
    operation: str
    handoff_id: str | None
    created_at: str
    state: str

    def to_dict(self):
        import json
        from .controller import ControllerCommand
        cmd = self.command
        return {
            "command": cmd.to_dict() if isinstance(cmd, ControllerCommand) else cmd,
            "command_hash": self.command_hash,
            "controller_session_id": self.controller_session_id,
            "controller_claim_nonce": self.controller_claim_nonce,
            "controller_fencing_epoch": self.controller_fencing_epoch,
            "target_lane": self.target_lane,
            "target_lane_claim_nonce": self.target_lane_claim_nonce,
            "target_lane_fencing_epoch": self.target_lane_fencing_epoch,
            "idempotency_key": self.idempotency_key,
            "operation": self.operation,
            "handoff_id": self.handoff_id,
            "created_at": self.created_at,
            "state": self.state,
        }

    @classmethod
    def from_dict(cls, data):
        from .controller import ControllerCommand
        cmd_data = data.get("command", {})
        cmd = ControllerCommand.from_dict(cmd_data) if isinstance(cmd_data, dict) else cmd_data
        return cls(
            command=cmd,
            command_hash=data.get("command_hash", ""),
            controller_session_id=data.get("controller_session_id", ""),
            controller_claim_nonce=data.get("controller_claim_nonce", ""),
            controller_fencing_epoch=int(data.get("controller_fencing_epoch", 0)),
            target_lane=data.get("target_lane", ""),
            target_lane_claim_nonce=data.get("target_lane_claim_nonce", ""),
            target_lane_fencing_epoch=int(data.get("target_lane_fencing_epoch", 0)),
            idempotency_key=data.get("idempotency_key", ""),
            operation=data.get("operation", ""),
            handoff_id=data.get("handoff_id"),
            created_at=data.get("created_at", ""),
            state=data.get("state", "CREATED"),
        )

def _cmd_hash(cmd):
    from .controller import ControllerCommand
    import json, hashlib
    return hashlib.sha256(json.dumps(cmd.to_dict(), sort_keys=True).encode()).hexdigest()

def _cmd_dir(sid, cid):
    return AI_LANE_ROOT / "controller" / "sessions" / sid / "commands" / cid

def _atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False); f.write("\n"); f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)

def _write_command(dc):
    _atomic_write(_cmd_dir(dc.controller_session_id, dc.command.command_id) / "command.json", dc.to_dict())

def _transition_state(dc, new_state):
    allowed = _CMD_TRANS.get(dc.state, set())
    if new_state not in allowed:
        raise SchedulerError(f"invalid state transition: {dc.state} -> {new_state}")
    updated = DurableCommand(command=dc.command, command_hash=dc.command_hash,
        controller_session_id=dc.controller_session_id, controller_claim_nonce=dc.controller_claim_nonce,
        controller_fencing_epoch=dc.controller_fencing_epoch, target_lane=dc.target_lane,
        target_lane_claim_nonce=dc.target_lane_claim_nonce, target_lane_fencing_epoch=dc.target_lane_fencing_epoch,
        idempotency_key=dc.idempotency_key, operation=dc.operation, handoff_id=dc.handoff_id,
        created_at=dc.created_at, state=new_state)
    _write_command(updated)
    _append_event(dc.controller_session_id, {"type":"command_"+new_state.lower().replace("requires_reconciliation","reconciliation"),
        "command_id":dc.command.command_id,"handoff_id":dc.handoff_id,"previous_state":dc.state,"new_state":new_state,"timestamp":_iso_now()})
    return updated

def _idem_dir(sid): return AI_LANE_ROOT / "controller" / "sessions" / sid / "idempotency"

def _record_idem(sid, key, cmd_hash, c_epoch, lane, l_epoch, op, hid):
    p = _idem_dir(sid) / (key + ".json")
    _atomic_write(p, {"idempotency_key":key,"command_hash":cmd_hash,"controller_session_id":sid,
        "controller_fencing_epoch":c_epoch,"lane_id":lane,"lane_fencing_epoch":l_epoch,"operation":op,"handoff_id":hid,"recorded_at":_iso_now()})

def _check_idem(sid, key, cmd_hash):
    p = _idem_dir(sid) / (key + ".json")
    if not p.exists(): return False, None
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        if d.get("command_hash","") and d["command_hash"] != cmd_hash:
            return True, f"idempotency key '{key[:16]}...' reused with different content: hash {cmd_hash[:16]}... != {d['command_hash'][:16]}..."
        return True, None
    except: return False, None

def _active_op_path(lane: str) -> Path:
    """Canonical lane-scoped active-operation path: one per lane."""
    return AI_LANE_ROOT / "lanes" / lane / "active-operation.json"

_ACTIVE_OP_GEN_PREFIX = "gen-"

def _next_active_op_generation(p: Path) -> str:
    if not p.exists():
        return _ACTIVE_OP_GEN_PREFIX + "1"
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        gen = d.get("generation", _ACTIVE_OP_GEN_PREFIX + "0")
        num = int(gen.replace(_ACTIVE_OP_GEN_PREFIX, ""))
        return _ACTIVE_OP_GEN_PREFIX + str(num + 1)
    except:
        return _ACTIVE_OP_GEN_PREFIX + "1"

def _append_active_op_event(event_type, lane, fields):
    """Append audit event to lane events file."""
    d = AI_LANE_ROOT / "lanes" / lane
    d.mkdir(parents=True, exist_ok=True)
    event = {"type": event_type, "lane_id": lane, "timestamp": _iso_now()}
    event.update(fields)
    with (d / "events.jsonl").open("a", encoding="utf-8", newline="\n") as f:
        json.dump(event, f, ensure_ascii=False); f.write("\n")

def _set_active_op(lane, snonce, cmd_id, hid, c_sid, c_epoch, l_epoch, *, pid=None, pst=None):
    """Acquire lane-scoped active operation. One per lane, atomic via exclusive-create."""
    p = _active_op_path(lane)
    p.parent.mkdir(parents=True, exist_ok=True)
    pid = pid or os.getpid()
    pst = pst or _get_process_start_time(pid)
    now = _iso_now()
    base = {
        "schema_version": 1,
        "lane_id": lane, "command_id": cmd_id, "handoff_id": hid,
        "session_nonce": snonce,
        "controller_session_id": c_sid,
        "controller_fencing_epoch": c_epoch,
        "lane_fencing_epoch": l_epoch,
        "pid": pid, "process_start_time": pst,
        "state": "ACQUIRED",
        "acquired_at": now, "last_transition_at": now,
    }
    try:
        with p.open("x", encoding="utf-8") as f:
            gen = _ACTIVE_OP_GEN_PREFIX + "1"
            json.dump(dict(base, generation=gen), f, indent=2, ensure_ascii=False)
        _append_active_op_event("active_op_acquired", lane, {
            "command_id": cmd_id, "handoff_id": hid,
            "session_nonce": snonce, "controller_session_id": c_sid,
            "controller_fencing_epoch": c_epoch, "lane_fencing_epoch": l_epoch,
            "generation": gen, "reason": "first_acquisition",
        })
        return True
    except FileExistsError:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except:
            p.unlink(missing_ok=True)
            return _set_active_op(lane, snonce, cmd_id, hid, c_sid, c_epoch, l_epoch, pid=pid, pst=pst)
        ec = d.get("command_id", "")
        ac_ep = int(d.get("controller_fencing_epoch", 0))
        al_ep = int(d.get("lane_fencing_epoch", 0))
        apid = int(d.get("pid", 0))
        apst = d.get("process_start_time", "")
        # Idempotent: same command
        if ec == cmd_id:
            _append_active_op_event("active_op_acquired", lane, {
                "command_id": cmd_id, "handoff_id": hid,
                "session_nonce": snonce, "controller_session_id": c_sid,
                "controller_fencing_epoch": c_epoch, "lane_fencing_epoch": l_epoch,
                "generation": d.get("generation", ""), "reason": "idempotent",
            })
            return True
        # Stale owner (dead PID): replace using sidecar-lock for atomicity
        if apid and not _process_is_valid(apid, apst):
            gen = _next_active_op_generation(p)
            sidecar = p.with_name(p.name + ".replace-lock")
            for _ in range(20):
                try:
                    with sidecar.open("x", encoding="utf-8") as _:
                        pass
                except FileExistsError:
                    time.sleep(0.05)
                    continue
                try:
                    # Re-read under sidecar: another process may have replaced it
                    if p.exists():
                        d2 = json.loads(p.read_text(encoding="utf-8"))
                        apid2 = int(d2.get("pid", 0))
                        apst2 = d2.get("process_start_time", "")
                        if apid2 and _process_is_valid(apid2, apst2):
                            # Not stale anymore — someone else replaced it
                            if d2.get("command_id") == cmd_id:
                                return True  # idempotent
                            raise SchedulerError(
                                f"lane '{lane}' has active op '{d2.get('command_id','')}' (replaced by peer)")
                        # Still stale: safe to unlink
                    p.unlink(missing_ok=True)
                    with p.open("x", encoding="utf-8") as f:
                        json.dump(dict(base, generation=gen), f, indent=2, ensure_ascii=False)
                    _append_active_op_event("active_op_acquired", lane, {
                        "command_id": cmd_id, "handoff_id": hid,
                        "session_nonce": snonce, "controller_session_id": c_sid,
                        "controller_fencing_epoch": c_epoch, "lane_fencing_epoch": l_epoch,
                        "generation": gen, "reason": "stale_owner_replaced",
                    })
                    return True
                except FileExistsError:
                    # p.open("x") failed despite our unlink — edge case, re-check
                    d2 = json.loads(p.read_text(encoding="utf-8"))
                    if d2.get("command_id") == cmd_id:
                        return True
                    raise SchedulerError(f"lane '{lane}' lost replace race for active op")
                finally:
                    sidecar.unlink(missing_ok=True)
            raise SchedulerError(f"lane '{lane}': could not acquire replace lock")
        # Stale controller epoch
        if c_epoch < ac_ep:
            _append_active_op_event("active_op_rejected", lane, {
                "command_id": cmd_id, "handoff_id": hid,
                "session_nonce": snonce, "controller_session_id": c_sid,
                "controller_fencing_epoch": c_epoch, "lane_fencing_epoch": l_epoch,
                "reason": f"stale_controller: {c_epoch} < {ac_ep}",
            })
            raise SchedulerError(f"lane '{lane}' has active op '{ec}' (stale controller epoch {c_epoch} < {ac_ep})")
        # Stale lane epoch
        if l_epoch < al_ep:
            _append_active_op_event("active_op_rejected", lane, {
                "command_id": cmd_id, "handoff_id": hid,
                "session_nonce": snonce, "controller_session_id": c_sid,
                "controller_fencing_epoch": c_epoch, "lane_fencing_epoch": l_epoch,
                "reason": f"stale_lane_epoch: {l_epoch} < {al_ep}",
            })
            raise SchedulerError(f"lane '{lane}' has active op '{ec}' (stale lane epoch {l_epoch} < {al_ep})")
        # Active conflict
        _append_active_op_event("active_op_rejected", lane, {
            "command_id": cmd_id, "handoff_id": hid,
            "session_nonce": snonce, "controller_session_id": c_sid,
            "controller_fencing_epoch": c_epoch, "lane_fencing_epoch": l_epoch,
            "reason": f"conflict: existing {ec}",
        })
        raise SchedulerError(f"lane '{lane}' already has active operation '{ec}'")

def _clear_active_op(lane, snonce, *, c_epoch=0, l_epoch=0, c_sid="", reason="released"):
    """Clear canonical lane active operation with epoch guards."""
    p = _active_op_path(lane)
    if not p.exists():
        _append_active_op_event("active_op_released", lane, {
            "command_id": "", "handoff_id": "", "session_nonce": snonce,
            "controller_session_id": c_sid, "controller_fencing_epoch": c_epoch,
            "lane_fencing_epoch": l_epoch, "reason": "nothing_to_clear",
        })
        return
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
        ac_ep = int(d.get("controller_fencing_epoch", 0))
        al_ep = int(d.get("lane_fencing_epoch", 0))
        apid = int(d.get("pid", 0))
        apst = d.get("process_start_time", "")
        if apid and _process_is_valid(apid, apst):
            if c_epoch and c_epoch < ac_ep:
                _append_active_op_event("active_op_rejected", lane, {
                    "command_id": d.get("command_id",""), "handoff_id": d.get("handoff_id",""),
                    "session_nonce": snonce, "controller_session_id": c_sid,
                    "controller_fencing_epoch": c_epoch, "lane_fencing_epoch": l_epoch,
                    "reason": f"stale_controller: {c_epoch} < {ac_ep}",
                })
                raise SchedulerError(f"cannot clear '{lane}': stale controller {c_epoch} < {ac_ep}")
            if l_epoch and l_epoch < al_ep:
                _append_active_op_event("active_op_rejected", lane, {
                    "command_id": d.get("command_id",""), "handoff_id": d.get("handoff_id",""),
                    "session_nonce": snonce, "controller_session_id": c_sid,
                    "controller_fencing_epoch": c_epoch, "lane_fencing_epoch": l_epoch,
                    "reason": f"stale_lane: {l_epoch} < {al_ep}",
                })
                raise SchedulerError(f"cannot clear '{lane}': stale lane {l_epoch} < {al_ep}")
        cmd_id = d.get("command_id", "")
        hid_val = d.get("handoff_id", "")
        p.unlink(missing_ok=True)
        _append_active_op_event("active_op_released", lane, {
            "command_id": cmd_id, "handoff_id": hid_val, "session_nonce": snonce,
            "controller_session_id": c_sid, "controller_fencing_epoch": c_epoch,
            "lane_fencing_epoch": l_epoch, "generation": d.get("generation", ""),
            "reason": reason,
        })
    except SchedulerError:
        raise
    except:
        p.unlink(missing_ok=True)


class LaneQueue:
    def __init__(self, lane_id):
        self.lane_id = lane_id; self._active_handoff_id = None
    @property
    def is_idle(self): return self._active_handoff_id is None
    @property
    def active_handoff_id(self): return self._active_handoff_id
    def restore_handoff(self, hid): self._active_handoff_id = hid
    def start_handoff(self, hid):
        if self._active_handoff_id is not None:
            raise SchedulerError(f"lane '{self.lane_id}' already has active handoff '{self._active_handoff_id}'")
        self._active_handoff_id = hid
    def complete_handoff(self, hid=None):
        if self._active_handoff_id is None: return
        if hid is not None and self._active_handoff_id != hid:
            raise SchedulerError(f"handoff mismatch: expected '{self._active_handoff_id}', got '{hid}'")
        self._active_handoff_id = None

class Scheduler:
    def __init__(self, lanes, mutex=None, controller_session_id=""):
        self._queues = {l: LaneQueue(l) for l in lanes}
        self._mutex = mutex or UIMutex()
        self._statuses = {l: "UNREGISTERED" for l in lanes}
        self._controller_session_id = controller_session_id

    @property
    def mutex(self): return self._mutex
    @property
    def controller_session_id(self): return self._controller_session_id

    def status(self, lane_id): return self._statuses.get(lane_id, "UNREGISTERED")
    def set_status(self, lane_id, status):
        if status not in LANE_STATUSES: raise SchedulerError(f"invalid lane status: {status}")
        if lane_id not in self._statuses: raise SchedulerError(f"unknown lane: {lane_id}")
        self._statuses[lane_id] = status
    def all_statuses(self): return dict(self._statuses)
    def is_idle(self, lane_id):
        q = self._queues.get(lane_id)
        if q is None: raise SchedulerError(f"unknown lane: {lane_id}")
        return q.is_idle
    def start_handoff(self, lane_id, handoff_id):
        q = self._queues.get(lane_id)
        if q is None: raise SchedulerError(f"unknown lane: {lane_id}")
        q.start_handoff(handoff_id); self._statuses[lane_id] = "DELIVERING"
    def complete_handoff(self, lane_id, handoff_id=None):
        q = self._queues.get(lane_id)
        if q is None: raise SchedulerError(f"unknown lane: {lane_id}")
        q.complete_handoff(handoff_id); self._statuses[lane_id] = "READY"

    def create_command(self, command):
        from .controller import ControllerCommand, ControllerError
        cmd_hash = _cmd_hash(command); sid = command.controller_session_id
        is_dup, conflict = _check_idem(sid, command.idempotency_key, cmd_hash)
        if is_dup:
            if conflict: raise SchedulerError(conflict)
            raise SchedulerError(f"duplicate idempotency key: {command.idempotency_key[:16]}...")
        dc = DurableCommand(command=command, command_hash=cmd_hash,
            controller_session_id=sid, controller_claim_nonce=command.controller_claim_nonce,
            controller_fencing_epoch=command.controller_fencing_epoch,
            target_lane=command.target_lane, target_lane_claim_nonce=command.expected_lane_claim_nonce,
            target_lane_fencing_epoch=command.expected_lane_fencing_epoch,
            idempotency_key=command.idempotency_key, operation=command.operation,
            handoff_id=command.handoff_id, created_at=_iso_now(), state="CREATED")
        _write_command(dc)
        _record_idem(sid, command.idempotency_key, cmd_hash, command.controller_fencing_epoch,
            command.target_lane, command.expected_lane_fencing_epoch, command.operation, command.handoff_id)
        _append_event(sid, {"type":"command_created","command_id":command.command_id,
            "handoff_id":command.handoff_id,"target_lane":command.target_lane,"timestamp":_iso_now()})
        return dc

    def transition_command(self, command, new_state):
        return _transition_state(command, new_state)

    def set_active_operation(self, lane, snonce, cmd_id, hid, c_epoch, l_epoch, *, pid=None):
        _set_active_op(lane, snonce, cmd_id, hid, self._controller_session_id, c_epoch, l_epoch, pid=pid)

    def clear_active_operation(self, lane, snonce, *, c_epoch=0, l_epoch=0):
        _clear_active_op(lane, snonce, c_epoch=c_epoch, l_epoch=l_epoch, c_sid=self._controller_session_id, reason="controller_released")

    @classmethod
    def reconstruct(cls, lanes, controller_session_id, mutex=None):
        """Reconstruct scheduler state from durable artifacts.

        Decision table (evaluated per lane):
        | Cmd state  | Active record | Cmd match | Controller epoch | Lane epoch | Result                              |
        |------------|--------------|-----------|------------------|------------|-------------------------------------|
        | terminal   | -            | -         | -                | -          | Lane idle, no action                |
        | non-term   | absent       | -         | -                | -          | Restore handoff, AWAITING/DELIVERING |
        | non-term   | present      | same      | >= existing      | >= existing | Restore both, lane active           |
        | non-term   | present      | same      | < existing       | -          | RECOVERY_REQUIRES_RECONCILIATION    |
        | non-term   | present      | diff      | -                | -          | RECOVERY_REQUIRES_RECONCILIATION    |
        | terminal   | present      | same      | -                | -          | Reconcile + clear, event logged     |
        | terminal   | present      | diff      | -                | -          | Orphan reconciliation               |
        | -          | orphan       | missing   | -                | -          | RECOVERY_REQUIRES_RECONCILIATION    |
        | -          | malformed    | -         | -                | -          | Quarantine / fail closed            |
        """
        sched = cls(lanes, mutex=mutex, controller_session_id=controller_session_id)
        cmd_root = AI_LANE_ROOT / "controller" / "sessions" / controller_session_id / "commands"
        terminal = {"VERIFIED","FAILED","CANCELLED","STALE_REJECTED"}

        # Phase 1: Restore non-terminal commands
        if not cmd_root.exists():
            sched = cls._reconcile_active_ops(lanes, cmd_root, sched, controller_session_id, terminal)
            return sched
        for d in sorted(cmd_root.iterdir()):
            if not d.is_dir(): continue
            f = d / "command.json"
            if not f.exists(): continue
            try:
                dc = DurableCommand.from_dict(json.loads(f.read_text(encoding="utf-8")))
            except: continue
            if dc.target_lane not in sched._queues: continue
            if dc.state in terminal: continue
            if dc.handoff_id and sched._queues[dc.target_lane].is_idle:
                sched._queues[dc.target_lane].restore_handoff(dc.handoff_id)
                if sched._statuses[dc.target_lane] == "UNREGISTERED":
                    sched._statuses[dc.target_lane] = "AWAITING_OUTPUT" if dc.state in ("DELIVERED","AWAITING_ACK") else "DELIVERING"

        # Phase 2: Read canonical lane-scoped active-operation records
        sched = cls._reconcile_active_ops(lanes, cmd_root, sched, controller_session_id, terminal)
        return sched

    @staticmethod
    def _reconcile_active_ops(lanes, cmd_root, sched, controller_session_id, terminal):
        """Reconcile lane-scoped active-operation records against commands."""
        from pathlib import Path as _Path
        for lid in lanes:
            ap = _active_op_path(lid)
            if not ap.exists(): continue
            try:
                od = json.loads(ap.read_text(encoding="utf-8"))
            except:
                _append_active_op_event("active_op_quarantined", lid, {"reason": "malformed_record"})
                sched._statuses[lid] = "QUARANTINED"
                continue
            cmd_id = od.get("command_id", "")
            if not cmd_id:
                _append_active_op_event("active_op_orphan", lid, {"reason": "empty_command_id"})
                sched._statuses[lid] = "RECOVERY_REQUIRES_RECONCILIATION"
                continue
            cp = cmd_root / cmd_id / "command.json" if cmd_root.exists() else _Path()
            if not cp.exists() or not cp.is_file():
                _append_active_op_event("active_op_orphan", lid, {"command_id": cmd_id, "reason": "no_matching_command"})
                sched._statuses[lid] = "RECOVERY_REQUIRES_RECONCILIATION"
                continue
            try:
                dc = DurableCommand.from_dict(json.loads(cp.read_text(encoding="utf-8")))
            except:
                _append_active_op_event("active_op_orphan", lid, {"command_id": cmd_id, "reason": "matching_command_corrupt"})
                sched._statuses[lid] = "RECOVERY_REQUIRES_RECONCILIATION"
                continue
            ac_epoch = int(od.get("controller_fencing_epoch", 0))
            al_epoch = int(od.get("lane_fencing_epoch", 0))
            ac_sid = od.get("controller_session_id", "")
            if dc.state in terminal:
                _append_active_op_event("active_op_cleared", lid, {
                    "command_id": cmd_id, "handoff_id": od.get("handoff_id",""),
                    "session_nonce": od.get("session_nonce",""),
                    "controller_session_id": ac_sid,
                    "controller_fencing_epoch": ac_epoch,
                    "lane_fencing_epoch": al_epoch,
                    "reason": "terminal_command_stale_active_op",
                })
                ap.unlink(missing_ok=True)
                continue
            if dc.target_lane != lid or dc.command.command_id != cmd_id:
                _append_active_op_event("active_op_stale_detected", lid, {"command_id": cmd_id, "reason": "mismatched_command"})
                sched._statuses[lid] = "RECOVERY_REQUIRES_RECONCILIATION"
                continue
            if ac_sid != controller_session_id:
                _append_active_op_event("active_op_reconciliation", lid, {
                    "command_id": cmd_id, "handoff_id": od.get("handoff_id",""),
                    "session_nonce": od.get("session_nonce",""),
                    "controller_session_id": ac_sid,
                    "controller_fencing_epoch": ac_epoch,
                    "lane_fencing_epoch": al_epoch,
                    "reason": "different_controller_session",
                })
                sched._statuses[lid] = "RECOVERY_REQUIRES_RECONCILIATION"
                continue
            if dc.controller_fencing_epoch < ac_epoch:
                _append_active_op_event("active_op_reconciliation", lid, {
                    "command_id": cmd_id, "handoff_id": od.get("handoff_id",""),
                    "reason": f"controller_epoch_mismatch: {dc.controller_fencing_epoch} < {ac_epoch}",
                })
                sched._statuses[lid] = "RECOVERY_REQUIRES_RECONCILIATION"
                continue
            if sched._queues[lid].is_idle:
                sched._queues[lid].restore_handoff(dc.handoff_id or od.get("handoff_id", ""))
            if sched._statuses[lid] == "UNREGISTERED":
                sched._statuses[lid] = "AWAITING_OUTPUT" if dc.state in ("DELIVERED","AWAITING_ACK") else "DELIVERING"
        return sched