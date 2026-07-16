"""Multi-process and mutex validation tests for UIMutex."""
import sys, os, json, tempfile, subprocess
sys.path.insert(0, "P:/tools")

from ai_lane_controller.scheduler import UIMutex, SchedulerError, _process_is_valid, _get_process_start_time

_MUTEX_CODE = r'''
import sys, os, json
sys.path.insert(0, "P:/tools")
from ai_lane_controller.scheduler import UIMutex, _process_is_valid
action = sys.argv[1]; path = sys.argv[2] if len(sys.argv) > 2 else None
if action == "try-acquire" and path:
    m = UIMutex(path); r = m.acquire(timeout=2.0)
    if r: m.release()
    print(json.dumps({"acquired": r, "pid": os.getpid()}))
elif action == "acquire-hold" and path:
    m = UIMutex(path); r = m.acquire(timeout=5.0)
    print(json.dumps({"acquired": r, "pid": os.getpid()}))
    if r: import time; time.sleep(3); m.release()
'''


def test_mutex_two_separate_processes() -> None:
    """Two separate processes cannot hold the mutex simultaneously."""
    with tempfile.TemporaryDirectory() as td:
        mp = os.path.join(td, "um.json")
        m = UIMutex(mp)
        assert m.acquire(timeout=5.0)
        r = subprocess.run([sys.executable, "-c", _MUTEX_CODE, "try-acquire", mp], capture_output=True, text=True, timeout=10)
        d = json.loads(r.stdout.strip())
        assert d["acquired"] is False
        assert d["pid"] != os.getpid()
        m.release()


def test_mutex_release_then_other_process() -> None:
    """After release, a different process can acquire."""
    with tempfile.TemporaryDirectory() as td:
        mp = os.path.join(td, "um2.json")
        m = UIMutex(mp)
        assert m.acquire(timeout=5.0)
        m.release()
        r = subprocess.run([sys.executable, "-c", _MUTEX_CODE, "try-acquire", mp], capture_output=True, text=True, timeout=10)
        d = json.loads(r.stdout.strip())
        assert d["acquired"] is True
        assert d["pid"] != os.getpid()


def test_mutex_wrong_pid_cannot_release() -> None:
    """Release with a different PID is rejected."""
    with tempfile.TemporaryDirectory() as td:
        mp = os.path.join(td, "um3.json")
        m = UIMutex(mp)
        assert m.acquire(timeout=5.0)
        try:
            m.release(pid=99999999)
            assert False
        except SchedulerError:
            pass
        m.release()


def test_mutex_concurrent_attempts_one_wins() -> None:
    """Multiple concurrent attempts against locked mutex all fail."""
    with tempfile.TemporaryDirectory() as td:
        mp = os.path.join(td, "um4.json")
        m = UIMutex(mp)
        assert m.acquire(timeout=5.0)
        procs = [subprocess.Popen([sys.executable, "-c", _MUTEX_CODE, "try-acquire", mp], stdout=subprocess.PIPE) for _ in range(3)]
        for p in procs:
            out, _ = p.communicate(timeout=10)
            d = json.loads(out.strip())
            assert d["acquired"] is False
        m.release()


def test_process_is_valid_checks_start_time() -> None:
    """_process_is_valid rejects mismatched start times (PID reuse)."""
    assert _process_is_valid(os.getpid(), _get_process_start_time(os.getpid())) is True
    # Same PID, wrong start time -> recycled
    assert _process_is_valid(os.getpid(), "2000-01-01T00:00:00Z") is False
    # Nonexistent PID
    assert _process_is_valid(99999999, "2000-01-01T00:00:00Z") is False


def test_mutex_workspace_identity_in_lock() -> None:
    """Lock file contains workspace_id and process_start_time."""
    with tempfile.TemporaryDirectory() as td:
        mp = os.path.join(td, "um5.json")
        m = UIMutex(mp)
        m.acquire(timeout=5.0, workspace_id="test-workspace")
        data = json.loads(open(mp).read())
        assert "pid" in data
        assert "process_start_time" in data
        assert data["workspace_id"] == "test-workspace"
        m.release()