#!/usr/bin/env python3
"""Smoke-launch: prove Stop.py telemetry uses file_lock.append_jsonl."""
import json, sys, time, inspect, tempfile, multiprocessing as mp
from pathlib import Path

def _worker_write(args):
    path, wid = args
    sys.path.insert(0, "P:/.claude/hooks")
    from file_lock import append_jsonl as _aj
    for i in range(100):
        _aj(Path(path), {"w": wid, "i": i})


def run_tests():
    sys.path.insert(0, "P:/.claude/hooks")
    from file_lock import append_jsonl
    print("[1] file_lock.append_jsonl imported OK")

    import Stop, inspect
    src = inspect.getsource(Stop._log_epistemic_telemetry)
    assert "from file_lock import append_jsonl" in src
    assert "append_jsonl(log_path, entry)" in src
    print("[2] _log_epistemic_telemetry calls append_jsonl")

    src2 = inspect.getsource(Stop._log_non_critical_advisory)
    assert "from file_lock import append_jsonl" in src2
    print("[3] _log_non_critical_advisory calls append_jsonl")

    with tempfile.TemporaryDirectory(prefix="stop_smoke_") as tmpdir:
        tp = Path(tmpdir) / "test_telemetry.jsonl"
        entry = {"timestamp": time.time(), "gate": "smoke_test", "decision": "warn"}
        append_jsonl(tp, entry)
        assert tp.exists() and tp.with_suffix(".lock").exists()
        parsed = json.loads(tp.read_text(encoding="utf-8").strip())
        assert parsed["gate"] == "smoke_test"
        print("[4] append_jsonl functional: data + lock sidecar, JSON valid")

    with tempfile.TemporaryDirectory(prefix="stop_smoke_") as tmpdir:
        tp = Path(tmpdir) / "concurrent_telemetry.jsonl"
        ctx = mp.get_context("spawn")
        procs = [ctx.Process(target=_worker_write, args=((str(tp), w),)) for w in range(8)]
        for p in procs: p.start()
        for p in procs: p.join()
        lines = [l for l in tp.read_text(encoding="utf-8").splitlines() if l.strip()]
        assert len(lines) == 800, f"expected 800, got {len(lines)}"
        for l in lines: json.loads(l)
        print("[5] 8-way concurrent smoke: 800/800 lines, all valid JSON")

    print("ALL SMOKE TESTS PASSED")


if __name__ == "__main__":
    run_tests()