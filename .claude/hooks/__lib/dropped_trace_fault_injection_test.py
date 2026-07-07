#!/usr/bin/env python3
"""Fault-injection test for append_jsonl_safe's dropped-trace branch.

The parallel acceptance test proved 0 writes drop under contention. That means
the dropped-trace branch (the branch this phase exists for) never executed.
This test FORCES it: hold the lock past the retry budget from a second process,
invoke a migrated writer, and assert the drop is traced correctly.
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


def main():
    import importlib
    import stop_block_log
    from file_lock import append_jsonl_safe

    print("dropped-trace fault-injection test")
    print("-" * 60)
    with tempfile.TemporaryDirectory(prefix="drop_fault_") as tmpdir:
        diag_dir = Path(tmpdir) / "diagnostics"
        diag_dir.mkdir(parents=True, exist_ok=True)
        log_path = diag_dir / "stop_blocks.jsonl"
        lock_sidecar = log_path.with_suffix(".lock")
        dropped_sidecar = log_path.with_suffix(log_path.suffix + ".dropped.jsonl")

        # Hold the lock from a separate process.
        mgr = mp.Manager()
        ready = mgr.Event()
        release = mgr.Event()
        ctx = mp.get_context("spawn")
        holder = ctx.Process(
            target=_holder,
            args=(str(lock_sidecar), ready, release),
        )
        holder.start()
        ready.wait(timeout=10.0)  # until holder has the lock
        # Tiny margin so the writer's acquire races a held lock.
        time.sleep(0.3)

        # (a) no exception escapes through the migrated _log_stop_block path.
        os.environ["CC_DIAGNOSTICS_DIR"] = str(diag_dir)
        importlib.reload(stop_block_log)
        ctx_row = {
            "event": "Stop", "session_id": "s_drop", "terminal_id": "t_drop",
            "transcript_path": "", "response_hash": "h_drop",
        }
        exc = None
        try:
            stop_block_log._log_stop_block(
                "drop_gate", "forced-contention", "stderr", ctx_row
            )
        except BaseException as e:
            exc = e
        # Also exercise the helper directly with a tighter-budget path.
        direct = append_jsonl_safe(log_path, {"x": "y"})

        release.set()
        holder.join(timeout=5.0)

        # (b) exactly one row in .dropped.jsonl per write, with required keys.
        raw = dropped_sidecar.read_text(encoding="utf-8") if dropped_sidecar.exists() else ""
        rows = [l for l in raw.splitlines() if l.strip()]
        required = {"ts", "reason", "orig_path", "entry_keys"}

        exc_ok = exc is None
        direct_ok = direct is False
        count_ok = len(rows) == 2  # one for _log_stop_block, one for direct
        keys_ok = all(set(json.loads(r).keys()) >= required for r in rows) if rows else False
        parse_ok = all(_parses(r) for r in rows)

        # Main log must have NO rows (both writes dropped).
        main_empty = not log_path.exists() or not log_path.read_text(encoding="utf-8").strip()

        results = {
            "no_exception": exc_ok,
            "direct_returns_false": direct_ok,
            "dropped_rows == 2": count_ok,
            "required_keys_present": keys_ok,
            "rows_parse": parse_ok,
            "main_log_empty": main_empty,
        }
        all_ok = all(results.values())
        for k, v in results.items():
            print(f"  [{'PASS' if v else 'FAIL'}] {k}")
        if rows:
            print(f"  sample row: {rows[0]}")
        print("-" * 60)
        print("ACCEPTANCE PASSED" if all_ok else "ACCEPTANCE FAILED")
        sys.exit(0 if all_ok else 1)


def _parses(s):
    try:
        json.loads(s)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    main()
