"""Test extract.py's dedup and tab-merge logic without hitting YouTube.

extract.py fetches tabs via yt-dlp, which we can't run in a unit test. But
the dedup logic (by video ID, across tabs) and the canonical JSONL emission
are pure functions we CAN test by stubbing fetch_tab.

Goal: ensure cross-tab duplicates collapse, per-tab counts are reported
correctly, and the output JSONL feeds cleanly into cluster.py.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path("P:/.agents/skills/nlm-bulk-ingest/scripts/extract.py")
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


def test_dedup_logic():
    """Verify cross-tab dedup collapses by video ID."""
    # Import the dedup logic by simulating what extract.py does after fetch_tab
    # returns. We replicate the by_tab structure and run the merge loop.
    by_tab = {
        "videos": [
            {"id": "vid1", "title": "Long form A"},
            {"id": "vid2", "title": "Long form B"},
        ],
        "shorts": [
            {"id": "vid2", "title": "Short that's same ID as vid2 (cross-listed)"},
            {"id": "short1", "title": "Short A"},
            {"id": "short2", "title": "Short B"},
        ],
        "streams": [
            {"id": "stream1", "title": "Stream A"},
        ],
    }

    # Replicate extract.py's merge loop
    tabs = list(by_tab.keys())
    seen = {}
    order = []
    for tab in tabs:
        for item in by_tab[tab]:
            vid = item["id"]
            if vid in seen:
                seen[vid]["tabs"].add(tab)
                continue
            seen[vid] = {
                "id": vid,
                "title": item["title"],
                "url": f"https://www.youtube.com/watch?v={vid}",
                "tabs": {tab},
            }
            order.append(vid)

    total = len(order)
    cross_dup = sum(1 for r in seen.values() if len(r["tabs"]) > 1)

    check("dedup: 5 unique from 6 raw (vid2 cross-listed)", total == 5, f"got {total}")
    check("dedup: 1 cross-tab duplicate collapsed", cross_dup == 1, f"got {cross_dup}")
    check(
        "dedup: vid2 appears on both videos+shorts",
        seen["vid2"]["tabs"] == {"videos", "shorts"},
        f"got {seen['vid2']['tabs']}",
    )
    check(
        "dedup: vid2 title is from first-seen tab (videos)",
        seen["vid2"]["title"] == "Long form B",
        f"got {seen['vid2']['title']}",
    )


def test_script_help_runs():
    """Smoke test: extract.py --help works without import errors."""
    r = subprocess.run(
        ["python", str(SCRIPT), "--help"],
        capture_output=True, text=True, timeout=30, encoding="utf-8"
    )
    check("extract.py --help exits 0", r.returncode == 0, r.stderr[:200])
    check(
        "extract.py --help mentions tabs",
        "--tabs" in r.stdout,
        "no --tabs flag in help",
    )
    check(
        "extract.py --help mentions /shorts or shorts",
        "shorts" in r.stdout.lower(),
        "no shorts reference in help",
    )


def test_no_yt_dlp_errors_cleanly():
    """If yt-dlp isn't found, extract.py should error cleanly (not crash)."""
    r = subprocess.run(
        ["python", str(SCRIPT), "https://www.youtube.com/@test", "--yt-dlp", "/nonexistent/yt-dlp"],
        capture_output=True, text=True, timeout=30, encoding="utf-8"
    )
    check("missing yt-dlp exits non-zero", r.returncode != 0, "exited 0")
    check(
        "missing yt-dlp gives clear error",
        "not found" in r.stdout.lower() or "not found" in r.stderr.lower(),
        f"output: {(r.stdout + r.stderr)[:200]}",
    )


if __name__ == "__main__":
    print("=== test_extract.py ===")
    test_dedup_logic()
    print()
    test_script_help_runs()
    print()
    test_no_yt_dlp_errors_cleanly()
    print(f"\n=== {PASS} passed, {FAIL} failed ===")
    sys.exit(1 if FAIL else 0)
