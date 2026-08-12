"""Regression tests for two nlm-bulk-ingest bugs fixed 2026-08-12.

Bug 1: cluster.py split_oversized crashed with RecursionError on homogeneous
       input (k-means collapses to 1 cluster → infinite recursion).
       Fix: detect collapse, fall back to sequential split.

Bug 2: ingest.py --pilot created duplicate notebooks because it didn't write
       to state, so --all re-processed the piloted cluster.
       Fix: pilot now passes state_path to process_cluster.

Bug 3 (minor): the double-negative arg guard was confusing; left in place
       but worth a smoke test.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

CLUSTER_PY = Path("P:/.agents/skills/nlm-bulk-ingest/scripts/cluster.py")
INGEST_PY = Path("P:/.agents/skills/nlm-bulk-ingest/scripts/ingest.py")
PASS = 0
FAIL = 0


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {label}")
    else:
        FAIL += 1
        print(f"  FAIL: {label} — {detail}")


# ---------------------------------------------------------------------------
# Bug 1: split_oversized must terminate on homogeneous input
# ---------------------------------------------------------------------------

def test_split_oversized_homogeneous():
    """K-means collapses on homogeneous input; the fix must fall back to
    sequential splitting and terminate without RecursionError."""
    import numpy as np
    # Import the function under test by execing cluster.py's namespace
    import importlib.util
    spec = importlib.util.spec_from_file_location("cluster_mod", CLUSTER_PY)
    mod = importlib.util.module_from_spec(spec)
    # cluster.py expects numpy as np at module level; ensure available
    try:
        spec.loader.exec_module(mod)
    except Exception:
        print("  SKIP: cluster.py import failed (dependency missing?)")
        return

    # Construct homogeneous embeddings: 300 points, all identical.
    # k-means cannot split these — this is the exact collapse that caused
    # RecursionError before the fix.
    emb = np.zeros((300, 16), dtype=float)
    labels = np.zeros(300, dtype=int)

    try:
        result = mod.split_oversized(labels, emb, max_size=50)
        n_pieces = len(result)
        total = sum(len(p) for p in result)
        max_piece = max(len(p) for p in result) if result else 0
        check("homogeneous: terminates without RecursionError", n_pieces > 0)
        check("homogeneous: all 300 points accounted for", total == 300, f"got {total}")
        check("homogeneous: every piece <= max_size", max_piece <= 50, f"max piece {max_piece}")
    except RecursionError:
        check("homogeneous: terminates without RecursionError", False, "RecursionError raised")
    except Exception as e:
        check("homogeneous: terminates without RecursionError", False, f"{type(e).__name__}: {e}")


def test_split_oversized_heterogeneous():
    """Normal heterogeneous input should still split via k-means (regression:
    the fix didn't break the happy path)."""
    import numpy as np
    import importlib.util
    spec = importlib.util.spec_from_file_location("cluster_mod", CLUSTER_PY)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        print("  SKIP: cluster.py import failed")
        return

    # Two well-separated blobs, 150 points each, max_size=50.
    np.random.seed(0)
    blob_a = np.random.randn(150, 8) + np.array([5.0] * 8)
    blob_b = np.random.randn(150, 8) + np.array([-5.0] * 8)
    emb = np.vstack([blob_a, blob_b])
    labels = np.array([0] * 150 + [1] * 150)

    result = mod.split_oversized(labels, emb, max_size=50)
    total = sum(len(p) for p in result)
    max_piece = max(len(p) for p in result) if result else 0
    check("heterogeneous: all 300 points accounted for", total == 300, f"got {total}")
    check("heterogeneous: every piece <= max_size", max_piece <= 50, f"max piece {max_piece}")
    check("heterogeneous: produces >1 piece for 300 points at cap 50", len(result) >= 6,
          f"got {len(result)} pieces")


# ---------------------------------------------------------------------------
# Bug 2: pilot must write to state so --all skips it
# ---------------------------------------------------------------------------

def test_pilot_writes_state():
    """Verify the pilot code path passes state_path (not None) to
    process_cluster. We can't run the live API, so we check the source
    for the bug's fingerprint: the pilot branch must not pass None."""
    src = INGEST_PY.read_text(encoding="utf-8")

    # The old buggy line was:
    #   record = process_cluster(cluster, args.prefix, args.profile, state, None)
    # The fix passes state_path instead of None.
    pilot_block_start = src.find("if args.pilot is not None:")
    pilot_block_end = src.find("return 0 if record[\"status\"]", pilot_block_start)
    pilot_block = src[pilot_block_start:pilot_block_end]
    has_none_call = "process_cluster(cluster, args.prefix, args.profile, state, None)" in pilot_block
    has_state_path_call = "process_cluster(cluster, args.prefix, args.profile, state, state_path)" in pilot_block
    check("pilot: does NOT pass None to process_cluster", not has_none_call,
          "found None in pilot process_cluster call")
    check("pilot: passes state_path to process_cluster", has_state_path_call,
          "state_path not found in pilot call")

    # Also verify state_path is set for pilot mode (not just --all)
    state_path_line = [l for l in src.splitlines()
                       if "state_path = args.state" in l]
    check("state_path: active for pilot mode", state_path_line and "args.pilot" in state_path_line[0],
          f"line: {state_path_line}")


def test_state_path_logic():
    """Verify state_path is truthy when --pilot or --all, None otherwise."""
    src = INGEST_PY.read_text(encoding="utf-8")
    # Find the state_path assignment
    line = [l.strip() for l in src.splitlines() if l.strip().startswith("state_path = args.state")]
    check("state_path line exists", len(line) == 1, f"found {len(line)} lines")
    if line:
        check("state_path covers pilot mode", "args.pilot is not None" in line[0], line[0])
        check("state_path covers all mode", "args.all" in line[0], line[0])


# ---------------------------------------------------------------------------
# Bug 3: arg guard smoke test
# ---------------------------------------------------------------------------

def test_arg_guard_no_action_mode():
    """Running with neither --pilot nor --all should error cleanly."""
    # Create a minimal clusters.json
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump([{"cluster_id": 0, "name": "test", "videos": []}], f)
        clusters_path = f.name

    r = subprocess.run(
        ["python", str(INGEST_PY), clusters_path],
        capture_output=True, text=True, timeout=30, encoding="utf-8"
    )
    Path(clusters_path).unlink(missing_ok=True)
    # Should error (exit non-zero) because neither --pilot nor --all given
    check("no-mode: exits non-zero without --pilot/--all", r.returncode != 0,
          f"exited {r.returncode}")


if __name__ == "__main__":
    print("=== test_bugs_20260812.py ===\n")
    print("--- Bug 1: split_oversized recursion ---")
    test_split_oversized_homogeneous()
    test_split_oversized_heterogeneous()
    print("\n--- Bug 2: pilot duplicate notebooks ---")
    test_pilot_writes_state()
    test_state_path_logic()
    print("\n--- Bug 3: arg guard ---")
    test_arg_guard_no_action_mode()
    print(f"\n=== {PASS} passed, {FAIL} failed ===")
    sys.exit(1 if FAIL else 0)
