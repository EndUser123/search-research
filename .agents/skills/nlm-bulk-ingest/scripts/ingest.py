#!/usr/bin/env python3
"""ingest.py — Stage 4-5: create notebooks, bulk-add, verify, checkpoint.

Usage:
  # Pilot one cluster end-to-end
  python ingest.py clusters.json --pilot <id> --prefix "WL: " --profile a.hominidae

  # Ingest all clusters (crash-resumable via --state)
  python ingest.py clusters.json --all --prefix "WL: " --profile a.hominidae --state run.json

Notes:
  - The first URL of every bulk-add prints "Error: Failed to add URL source"
    and the exit code is 1. THIS IS COSMETIC. The bulk continues and lands
    all sources. Verify via `nlm notebook get <id>` source_count, NOT exit code.
    See [[notebooklm-cli-operational-gotchas]].
  - Auth: `nlm login --check` lies about expiry. If `notebook list` fails,
    run `nlm login --profile <name>` (silent CDP re-auth). See tool-fallbacks.md.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_STATE = Path("nlm-ingest-state.json")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def run(cmd: list[str], timeout: int = 1800) -> tuple[int, str, str]:
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8"
        )
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"


def ensure_auth(profile: str) -> bool:
    """Verify nlm auth; attempt silent re-auth if needed. Returns True if auth ok."""
    rc, _, _ = run(
        ["nlm", "notebook", "list", "--profile", profile, "--quiet"], timeout=60
    )
    if rc == 0:
        return True
    log(
        f"Auth check failed (rc={rc}); attempting silent re-auth via profile '{profile}'..."
    )
    rc2, out, err = run(["nlm", "login", "--profile", profile], timeout=300)
    if rc2 != 0:
        log(f"  re-auth failed: {err.strip()[:300]}")
        return False
    # Verify
    rc3, _, _ = run(
        ["nlm", "notebook", "list", "--profile", profile, "--quiet"], timeout=60
    )
    return rc3 == 0


def create_notebook(title: str, profile: str) -> str | None:
    cmd = ["nlm", "notebook", "create", title, "--profile", profile, "--json"]
    rc, out, err = run(cmd, timeout=120)
    if rc != 0:
        log(f"  CREATE FAILED rc={rc}: {(err or out).strip()[:300]}")
        return None
    try:
        data = json.loads(out)
        return data.get("notebook_id") or data.get("id")
    except json.JSONDecodeError:
        log(f"  CREATE output not JSON: {out.strip()[:300]}")
        return None


def bulk_add(notebook_id: str, urls: list[str], profile: str) -> tuple[float, str]:
    """Returns (elapsed_s, output_excerpt). Bulk-adds all URLs in one call."""
    cmd = ["nlm", "source", "add", notebook_id, "--profile", profile]
    for u in urls:
        cmd.extend(["--youtube", u])
    t0 = time.time()
    rc, out, err = run(cmd, timeout=1800)
    elapsed = time.time() - t0
    excerpt = (err or out).strip()[:500]
    # Note: rc=1 and "Failed to add URL source" is cosmetic; see module docstring.
    return elapsed, excerpt


def verify_source_count(
    notebook_id: str,
    profile: str,
    expected: int,
    max_polls: int = 10,
    initial_wait: int = 30,
) -> int:
    """Poll notebook get for source_count. Returns actual, or -1 on error."""
    for attempt in range(max_polls):
        if attempt == 0:
            time.sleep(initial_wait)
        else:
            time.sleep(15)
        rc, out, _ = run(
            ["nlm", "notebook", "get", notebook_id, "--profile", profile, "--json"],
            timeout=60,
        )
        if rc != 0:
            continue
        try:
            actual = int(json.loads(out).get("source_count", -1))
        except (json.JSONDecodeError, ValueError):
            return -1
        if actual >= expected:
            return actual
        if actual > 0 and attempt >= 3:
            return actual  # stable but short
    return -1


def load_state(path: Path) -> dict:
    if path.exists():
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    return {"notebooks": {}, "completed": [], "failed": []}


def save_state(state: dict, path: Path) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


def process_cluster(
    cluster: dict, prefix: str, profile: str, state: dict, state_path: Path | None
) -> dict:
    cid = cluster["cluster_id"]
    title = f"{prefix}{cluster['name']}"
    urls = [v["url"] for v in cluster["videos"]]
    expected = len(urls)

    log("")
    log(f"--- Cluster {cid}: {title} ({expected} URLs) ---")

    nb_id = create_notebook(title, profile)
    if not nb_id:
        state["failed"].append(cid)
        if state_path:
            save_state(state, state_path)
        return {"cluster_id": cid, "status": "create_failed"}

    log(f"  created notebook {nb_id}")

    elapsed, excerpt = bulk_add(nb_id, urls, profile)
    log(f"  bulk-add: {elapsed:.0f}s ({elapsed / expected:.2f}s/url)")
    if excerpt:
        log(f"  output: {excerpt[:200]}")

    actual = verify_source_count(nb_id, profile, expected)
    status = "ok" if actual == expected else ("partial" if actual > 0 else "unknown")
    log(f"  source_count: {actual}/{expected} -> {status}")

    record = {
        "cluster_id": cid,
        "title": title,
        "notebook_id": nb_id,
        "expected": expected,
        "actual": actual,
        "status": status,
        "url": f"https://notebooklm.google.com/notebook/{nb_id}",
    }
    state["notebooks"][str(cid)] = record
    if status == "ok":
        state["completed"].append(cid)
    else:
        state["failed"].append(cid)
    if state_path:
        save_state(state, state_path)
    return record


def reconcile_state(state: dict, profile: str) -> int:
    """Re-verify any completed entry whose actual count is missing or looks stale.

    Pilot-seed pattern and crash-resume both can leave entries with actual=None
    or status='pilot'. This self-heals by re-running verify_source_count for any
    completed entry that lacks a confirmed actual count.

    Returns count of entries reconciled.
    """
    fixed = 0
    for cid_str, rec in state.get("notebooks", {}).items():
        nb_id = rec.get("notebook_id")
        expected = rec.get("expected")
        actual = rec.get("actual")
        if not nb_id or not expected:
            continue
        if actual == expected:
            continue  # already confirmed
        log(
            f"reconcile: cluster {cid_str} has actual={actual}, expected={expected}; re-verifying..."
        )
        new_actual = verify_source_count(
            nb_id, profile, expected, max_polls=3, initial_wait=15
        )
        if new_actual == expected:
            rec["actual"] = new_actual
            rec["status"] = "ok"
            if int(cid_str) not in state.get("completed", []):
                state.setdefault("completed", []).append(int(cid_str))
            fixed += 1
            log(f"  reconciled: {new_actual}/{expected} ok")
        else:
            log(f"  still mismatched: {new_actual}/{expected}")
    return fixed


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("clusters", type=Path, help="clusters.json from cluster.py")
    ap.add_argument("--pilot", type=int, help="Pilot a single cluster end-to-end")
    ap.add_argument(
        "--all", action="store_true", help="Ingest all clusters not yet in --state"
    )
    ap.add_argument("--prefix", default="", help="Prefix for notebook titles")
    ap.add_argument("--profile", default="a.hominidae", help="nlm profile name")
    ap.add_argument(
        "--state", type=Path, default=DEFAULT_STATE, help="State file for resume"
    )
    args = ap.parse_args()

    if not args.pilot is not None and not args.all:
        # Allow --pilot 0 (falsy)
        if args.pilot is None and not args.all:
            ap.error("must pass --pilot <id> or --all")

    with args.clusters.open(encoding="utf-8") as f:
        clusters = json.load(f)

    if not ensure_auth(args.profile):
        log(f"FATAL: auth failed for profile '{args.profile}'")
        return 2

    state = load_state(args.state)
    # Checkpoint in both --all and --pilot modes. The pilot MUST write to
    # state so a subsequent --all run treats the piloted cluster as completed
    # instead of re-processing it and creating a duplicate notebook.
    # Incident: session 2026-08-12, pilot-then-all created duplicate notebooks
    # twice because pilot passed state_path=None.
    state_path = args.state if (args.all or args.pilot is not None) else None

    # Self-heal: re-verify any completed entries whose actual count is missing.
    # Catches pilot-seed gaps and crash-resume artifacts. Cheap (skips entries
    # already confirmed); only re-runs verify for entries that need it.
    if state.get("notebooks"):
        fixed = reconcile_state(state, args.profile)
        if fixed and state_path:
            save_state(state, state_path)

    if args.pilot is not None:
        cluster = next((c for c in clusters if c["cluster_id"] == args.pilot), None)
        if not cluster:
            log(f"Cluster {args.pilot} not found")
            return 2
        record = process_cluster(cluster, args.prefix, args.profile, state, state_path)
        log("")
        log(f"Pilot complete: {record['url']}")
        log(
            f"  Pilot result checkpointed to state. --all will skip cluster {args.pilot}."
        )
        log("  Open this notebook in NotebookLM UI to verify before running --all.")
        return 0 if record["status"] == "ok" else 1

    # --all mode
    todo = [
        c
        for c in clusters
        if c["cluster_id"] not in state["completed"]
        and c["cluster_id"] not in state["failed"]
    ]
    log(
        f"=== Bulk ingest: {len(todo)} clusters to do, {len(state['completed'])} done, {len(state['failed'])} failed ==="
    )

    for cluster in todo:
        process_cluster(cluster, args.prefix, args.profile, state, state_path)

    log("")
    log("=== Run complete ===")
    log(f"Completed: {len(state['completed'])}/{len(clusters)}")
    if state["failed"]:
        log(f"Failed: {state['failed']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
