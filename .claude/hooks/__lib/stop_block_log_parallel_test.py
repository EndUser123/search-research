#!/usr/bin/env python3
"""Phase 0 acceptance test: ≥8 procs writing through the migrated _log_stop_block path.

Requirement (Amendment 3): single-process evidence cannot see this bug class.
Assert line-count == writes issued AND every line parses as JSON.
"""
import json, os, sys, tempfile, multiprocessing as mp
from pathlib import Path

_LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(_LIB))
sys.path.insert(0, str(_LIB.parent))

WORKERS = 8
WRITES_PER_WORKER = 50


def _worker(args):
    diag_dir, worker_id, n = args
    os.environ["CC_DIAGNOSTICS_DIR"] = diag_dir
    # Re-import per spawn so the env var is read fresh in each child.
    import importlib
    import stop_block_log
    importlib.reload(stop_block_log)
    ctx = {
        "event": "Stop",
        "session_id": f"sess_{worker_id}",
        "terminal_id": f"term_{worker_id}",
        "transcript_path": "",
        "response_hash": f"h{worker_id}",
    }
    for i in range(n):
        stop_block_log._log_stop_block(
            f"gate_{worker_id}_{i}", f"reason {worker_id}/{i}", f"stderr {i}", ctx
        )


def main():
    print(f"stop_block_log parallel acceptance test  workers={WORKERS} writes/worker={WRITES_PER_WORKER}")
    print("-" * 60)
    with tempfile.TemporaryDirectory(prefix="sbl_parallel_") as tmpdir:
        target = str(Path(tmpdir) / "diagnostics")
        Path(target).mkdir(parents=True, exist_ok=True)
        args = [(target, w, WRITES_PER_WORKER) for w in range(WORKERS)]
        ctx = mp.get_context("spawn")
        procs = [ctx.Process(target=_worker, args=(a,)) for a in args]
        for p in procs:
            p.start()
        for p in procs:
            p.join()

        log_path = Path(target) / "stop_blocks.jsonl"
        raw = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
        lines = [l for l in raw.splitlines() if l.strip()]
        expected = WORKERS * WRITES_PER_WORKER

        corrupt = 0
        gate_set = set()
        for l in lines:
            try:
                obj = json.loads(l)
            except json.JSONDecodeError:
                corrupt += 1
                continue
            gate_set.add(obj.get("gate_name"))

        lost = expected - len(lines)
        ok = lost == 0 and corrupt == 0
        flag = "PASS" if ok else "FAIL"
        print(f"[{flag}] lines={len(lines)}/{expected} lost={max(0,lost)} corrupt={corrupt} "
              f"unique_gates={len(gate_set)}/{expected}")
        dropped = log_path.with_suffix(log_path.suffix + ".dropped.jsonl")
        if dropped.exists():
            d = len(dropped.read_text(encoding="utf-8").splitlines())
            print(f"  dropped-trace sidecar: {d} rows (lock contention observed)")
        print("-" * 60)
        if ok:
            print("ACCEPTANCE PASSED")
        else:
            print("ACCEPTANCE FAILED")
            sys.exit(1)


if __name__ == "__main__":
    main()
