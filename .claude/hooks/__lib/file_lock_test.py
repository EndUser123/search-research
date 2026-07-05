#!/usr/bin/env python3
"""Regression test for file_lock.append_jsonl under concurrent access."""
import json, sys, tempfile, multiprocessing as mp
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from file_lock import append_jsonl, FileLock

WORKERS = 8
LINES_PER_WORKER = 200


def _worker_append(args):
    path, worker_id, n = args
    for i in range(n):
        append_jsonl(Path(path), {"worker": worker_id, "i": i})


def _worker_rapid_cycle(args):
    """Direct FileLock write -- exercises lock churn."""
    path, worker_id, n = args
    lock_path = Path(path).with_suffix(".lock")
    for i in range(n):
        with FileLock(lock_path):
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps({"worker": worker_id, "i": i}) + "\n")


def _parses_json(s):
    try:
        json.loads(s)
        return True
    except Exception:
        return False


def run_variant(name, worker_fn, tmpdir):
    path = str(Path(tmpdir) / f"{name}.jsonl")
    args = [(path, w, LINES_PER_WORKER) for w in range(WORKERS)]
    ctx = mp.get_context("spawn")
    procs = [ctx.Process(target=worker_fn, args=(a,)) for a in args]
    for p in procs:
        p.start()
    for p in procs:
        p.join()
    expected = WORKERS * LINES_PER_WORKER
    raw = Path(path).read_text(encoding="utf-8") if Path(path).exists() else ""
    text_lines = [l for l in raw.splitlines() if l.strip()]
    lost = expected - len(text_lines)
    corrupt = sum(1 for l in text_lines if not _parses_json(l))
    return {"variant": name, "expected": expected, "actual": len(text_lines),
            "lost": max(0, lost), "corrupt": corrupt}


def main():
    print("file_lock.append_jsonl concurrent regression test")
    print(f"workers={WORKERS} lines_per_worker={LINES_PER_WORKER}")
    print("-" * 60)
    with tempfile.TemporaryDirectory(prefix="flock_test_") as tmpdir:
        results = [
            run_variant("append_jsonl_8way", _worker_append, tmpdir),
            run_variant("rapid_cycle_8way", _worker_rapid_cycle, tmpdir),
        ]
    all_pass = True
    for r in results:
        flag = "PASS" if r["lost"] == 0 and r["corrupt"] == 0 else "FAIL"
        if flag == "FAIL":
            all_pass = False
        print(f"[{flag}] {r['variant']:25s} lines={r['actual']}/{r['expected']} "
              f"lost={r['lost']} corrupt={r['corrupt']}")
    print("-" * 60)
    if all_pass:
        print("ALL TESTS PASSED")
    else:
        print("TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()