#!/usr/bin/env python3
"""Fault-injection test for append_jsonl_safe's dropped-trace branch.

The parallel acceptance test proved 0 writes drop under contention. That means
the dropped-trace branch (the branch this phase exists for) never executed.
This test FORCES it two ways:
  1. Real cross-process lock contention -> TimeoutError (OSError subclass).
  2. Direct monkeypatch -> BaseLockException (the tuple branch contention
     cannot reach at runtime, since FileLock.__enter__ converts LockException
     to TimeoutError; tuple membership alone does not prove the branch works).
"""
import json, os, sys, tempfile, time, multiprocessing as mp
from pathlib import Path

_LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(_LIB))
sys.path.insert(0, str(_LIB.parent))


def _holder(lock_path_str, ready_flag, release_event):
    """Acquire the sidecar lock the way append_jsonl does, hold past budget."""
    from file_lock import FileLock
    lock = FileLock(Path(lock_path_str), timeout=10.0)
    lock.__enter__()
    ready_flag.set()
    release_event.wait(timeout=15.0)
    lock.__exit__(None, None, None)


def _parses(s):
    try:
        json.loads(s)
        return True
    except Exception:
        return False


def _run_contention():
    import importlib
    import stop_block_log
    from file_lock import append_jsonl_safe

    print("contention path (real TimeoutError):")
    with tempfile.TemporaryDirectory(prefix="drop_fault_") as tmpdir:
        diag_dir = Path(tmpdir) / "diagnostics"
        diag_dir.mkdir(parents=True, exist_ok=True)
        log_path = diag_dir / "stop_blocks.jsonl"
        lock_sidecar = log_path.with_suffix(".lock")
        dropped_sidecar = log_path.with_suffix(log_path.suffix + ".dropped.jsonl")

        mgr = mp.Manager()
        ready = mgr.Event()
        release = mgr.Event()
        ctx = mp.get_context("spawn")
        holder = ctx.Process(target=_holder, args=(str(lock_sidecar), ready, release))
        holder.start()
        ready.wait(timeout=10.0)
        time.sleep(0.3)

        os.environ["CC_DIAGNOSTICS_DIR"] = str(diag_dir)
        importlib.reload(stop_block_log)
        ctx_row = {"event": "Stop", "session_id": "s_drop", "terminal_id": "t_drop",
                   "transcript_path": "", "response_hash": "h_drop"}
        exc = None
        try:
            stop_block_log._log_stop_block("drop_gate", "forced-contention", "stderr", ctx_row)
        except BaseException as e:
            exc = e
        direct = append_jsonl_safe(log_path, {"x": "y"})

        release.set()
        holder.join(timeout=5.0)

        raw = dropped_sidecar.read_text(encoding="utf-8") if dropped_sidecar.exists() else ""
        rows = [l for l in raw.splitlines() if l.strip()]
        required = {"ts", "reason", "orig_path", "entry_keys"}

        results = {
            "no_exception": exc is None,
            "direct_returns_false": direct is False,
            "dropped_rows == 2": len(rows) == 2,
            "required_keys_present": all(set(json.loads(r).keys()) >= required for r in rows) if rows else False,
            "rows_parse": all(_parses(r) for r in rows),
            "main_log_empty": not log_path.exists() or not log_path.read_text(encoding="utf-8").strip(),
        }
        ok = all(results.values())
        for k, v in results.items():
            print(f"  [{'PASS' if v else 'FAIL'}] {k}")
        if rows:
            print(f"  sample reason: {json.loads(rows[0])['reason'][:90]}")
        return ok


def _run_base_lock_exception():
    """Inject BaseLockException directly to exercise the tuple branch."""
    from file_lock import FileLock, append_jsonl_safe
    try:
        from portalocker.exceptions import BaseLockException
    except ImportError:
        print("BaseLockException branch: [SKIP] portalocker unavailable")
        return True

    print("BaseLockException direct-injection (tuple branch):")
    with tempfile.TemporaryDirectory(prefix="drop_ble_") as tmpdir:
        log_path = Path(tmpdir) / "tgt.jsonl"
        dropped = log_path.with_suffix(log_path.suffix + ".dropped.jsonl")
        orig = FileLock.__enter__

        def _raise(self):
            raise BaseLockException("forced base lock branch")

        results = {}
        try:
            FileLock.__enter__ = _raise
            try:
                ret = append_jsonl_safe(log_path, {"k": "v"})
                results["no_exception_escape"] = True
            except BaseException as e:
                results["no_exception_escape"] = False
                results["_escaped"] = f"{type(e).__name__}: {e}"
            results["returns_false"] = ret is False
        finally:
            FileLock.__enter__ = orig

        rows = [l for l in dropped.read_text(encoding="utf-8").splitlines() if l.strip()] if dropped.exists() else []
        results["dropped_rows == 1"] = len(rows) == 1
        if rows:
            obj = json.loads(rows[0])
            results["reason_is_BaseLockException"] = obj.get("reason", "").startswith("BaseLockException")
            results["required_keys"] = {"ts", "reason", "orig_path", "entry_keys"} <= set(obj.keys())
            results["parses"] = True
        else:
            results["reason_is_BaseLockException"] = False
            results["required_keys"] = False
            results["parses"] = False
        results["main_log_empty"] = not log_path.exists() or not log_path.read_text(encoding="utf-8").strip()

        ok = all(v for k, v in results.items() if not k.startswith("_"))
        for k, v in results.items():
            print(f"  [{'PASS' if v else 'FAIL'}] {k}")
        return ok


def main():
    print("dropped-trace fault-injection test")
    print("=" * 60)
    r1 = _run_contention()
    print("-" * 60)
    r2 = _run_base_lock_exception()
    print("=" * 60)
    if r1 and r2:
        print("ACCEPTANCE PASSED")
        sys.exit(0)
    print("ACCEPTANCE FAILED")
    sys.exit(1)


if __name__ == "__main__":
    main()
