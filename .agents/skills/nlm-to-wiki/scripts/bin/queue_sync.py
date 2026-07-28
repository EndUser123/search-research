#!/usr/bin/env python3
"""queue_sync.py — queue-of-work pattern for parallel nlm-to-wiki ingestion.

Durable location: P:/.agents/skills/nlm-to-wiki/scripts/bin/queue_sync.py
Queue file: P:/.data/wiki/_state/nlm-sync/queue.json

Usage:
  python queue_sync.py --enqueue --profile codex
  python queue_sync.py --worker --worker-id w1 --profile codex
  python queue_sync.py --status
  python queue_sync.py --retry-failed
"""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import sys
import time
from datetime import date
from pathlib import Path

PROFILE_DEFAULT = "codex"
MIN_SOURCES = 50
MAX_RETRIES = 3
QUEUE_FILE = Path("P:/.data/wiki/_state/nlm-sync/queue.json")
SYNC_SCRIPT = "P:/.agents/skills/nlm-to-wiki/scripts/sync.py"

def _run(cmd, timeout=120):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, encoding="utf-8")
        return r.returncode, r.stdout or "", r.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", f"TIMEOUT after {timeout}s"

def _lock_path(): return QUEUE_FILE.with_suffix(".lock")

def _acquire_lock(timeout=30):
    lock = _lock_path()
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            return fd
        except FileExistsError:
            time.sleep(0.1)
    raise TimeoutError(f"Could not acquire queue lock after {timeout}s")

def _release_lock(fd):
    try: os.close(fd)
    except OSError: pass
    try: _lock_path().unlink()
    except FileNotFoundError: pass

def load_queue():
    if QUEUE_FILE.exists():
        try: return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError: pass
    return _empty_queue()

def _empty_queue():
    return {"pending": [], "in_progress": {}, "completed": [], "failed": [], "poisoned": [],
            "config": {"workers": 1, "profile": PROFILE_DEFAULT, "max_retries": MAX_RETRIES, "min_sources": MIN_SOURCES},
            "created": date.today().isoformat()}

def save_queue(queue):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, QUEUE_FILE)

def list_notebooks(profile):
    rc, out, _ = _run(["nlm", "notebook", "list", "--profile", profile, "--json"], timeout=120)
    if rc != 0: return []
    try:
        data = json.loads(out)
        return data if isinstance(data, list) else data.get("notebooks", [])
    except json.JSONDecodeError: return []

def do_enqueue(profile, min_sources):
    nbs = list_notebooks(profile)
    candidates = [n for n in nbs if (n.get("source_count") or 0) >= min_sources and not (n.get("title") or "").startswith("[INGESTED]")]
    candidates.sort(key=lambda n: -(n.get("source_count") or 0))
    fd = _acquire_lock()
    try:
        queue = load_queue()
        already = set(queue.get("pending", [])) | {i["nb_id"] for i in queue.get("completed", [])} | {i["nb_id"] for i in queue.get("failed", [])} | {i["nb_id"] for i in queue.get("poisoned", [])}
        new_items = [{"nb_id": n["id"], "title": (n.get("title") or "")[:60], "source_count": n.get("source_count", 0)} for n in candidates if n["id"] not in already]
        if new_items:
            queue.setdefault("pending", []).extend(new_items)
            queue["config"]["profile"] = profile
            save_queue(queue)
        print(f"[enqueue] {len(new_items)} new notebooks added. Queue: {len(queue['pending'])} pending, {len(queue.get('completed',[]))} completed", flush=True)
    finally:
        _release_lock(fd)

def ensure_auth(profile):
    rc, _, _ = _run(["nlm", "notebook", "list", "--profile", profile, "--quiet"], timeout=60)
    if rc == 0: return True
    print("[worker] Auth expired; silent re-auth via CDP...", flush=True)
    rc2, _, _ = _run(["nlm", "login", "--profile", profile], timeout=300)
    if rc2 != 0: return False
    rc3, _, _ = _run(["nlm", "notebook", "list", "--profile", profile, "--quiet"], timeout=60)
    return rc3 == 0

def do_worker(worker_id, profile):
    print(f"[worker:{worker_id}] Starting (profile={profile})", flush=True)
    while True:
        queue = load_queue()
        active = len(queue.get("in_progress", {}))
        configured = queue.get("config", {}).get("workers", 1)
        current_profile = queue.get("config", {}).get("profile", profile)
        if active > configured:
            print(f"[worker:{worker_id}] {active} active > {configured} configured; exiting", flush=True)
            break
        fd = _acquire_lock()
        try:
            queue = load_queue()
            pending = queue.get("pending", [])
            if not pending:
                break
            item = pending.pop(0)
            queue.setdefault("in_progress", {})[worker_id] = {"nb_id": item["nb_id"], "title": item.get("title",""), "started_at": time.strftime("%H:%M:%S")}
            save_queue(queue)
        finally:
            _release_lock(fd)
        nb_id = item["nb_id"]; title = item.get("title", ""); sc = item.get("source_count", 0)
        print(f"[worker:{worker_id}] Claimed: {title[:50]} ({sc} sources)", flush=True)
        if not ensure_auth(current_profile):
            fd = _acquire_lock()
            try:
                queue = load_queue()
                queue.get("in_progress", {}).pop(worker_id, None)
                queue.setdefault("failed", []).append({"nb_id": nb_id, "title": title, "error": "auth_failed", "attempts": 1})
                save_queue(queue)
            finally:
                _release_lock(fd)
            break
        start = time.time()
        try:
            r = subprocess.run(["python", SYNC_SCRIPT, "--notebook", nb_id, "--profile", current_profile], capture_output=True, text=True, timeout=3600, encoding="utf-8")
            elapsed = time.time() - start
        except subprocess.TimeoutExpired:
            elapsed = 3600
            fd = _acquire_lock()
            try:
                queue = load_queue()
                queue.get("in_progress", {}).pop(worker_id, None)
                queue.setdefault("failed", []).append({"nb_id": nb_id, "title": title, "error": "timeout", "attempts": 1})
                save_queue(queue)
            finally:
                _release_lock(fd)
            print(f"[worker:{worker_id}] TIMEOUT: {title[:40]} ({elapsed:.0f}s)", flush=True)
            continue
        if r.returncode == 0:
            if "SKIP" in (r.stderr or ""): status = "skipped_unchanged"
            elif "wrote 0 pages" in (r.stderr or "") or "0 pages" in (r.stderr or ""): status = "synced_0_pages"
            else: status = "synced"
        else: status = f"failed (rc={r.returncode})"
        fd = _acquire_lock()
        try:
            queue = load_queue()
            queue.get("in_progress", {}).pop(worker_id, None)
            if status in ("synced", "skipped_unchanged"):
                queue.setdefault("completed", []).append({"nb_id": nb_id, "title": title, "status": status, "elapsed_s": round(elapsed, 1), "completed_at": time.strftime("%H:%M:%S")})
            elif status == "synced_0_pages":
                queue.setdefault("failed", []).append({"nb_id": nb_id, "title": title, "error": "0 pages", "attempts": 1})
            else:
                attempts = sum(1 for f in queue.get("failed", []) if f.get("nb_id") == nb_id) + 1
                max_r = queue.get("config", {}).get("max_retries", MAX_RETRIES)
                if attempts >= max_r:
                    queue.setdefault("poisoned", []).append({"nb_id": nb_id, "title": title, "error": status, "attempts": attempts})
                else:
                    queue.setdefault("failed", []).append({"nb_id": nb_id, "title": title, "error": status, "attempts": attempts})
                    queue.setdefault("pending", []).append({"nb_id": nb_id, "title": title, "source_count": sc})
            save_queue(queue)
        finally:
            _release_lock(fd)
        err_lines = [line for line in (r.stderr or "").splitlines() if line.strip()][-3:]
        for line in err_lines: print(f"[worker:{worker_id}]   {line.strip()}", flush=True)
        print(f"[worker:{worker_id}]   -> {status} ({elapsed:.0f}s)", flush=True)
    print(f"[worker:{worker_id}] Done", flush=True)

def do_status():
    queue = load_queue()
    p, ip, c, f, po = queue.get("pending",[]), queue.get("in_progress",{}), queue.get("completed",[]), queue.get("failed",[]), queue.get("poisoned",[])
    cfg = queue.get("config",{})
    print(f"\n{'='*60}\nNLM-TO-WIKI QUEUE STATUS\n{'='*60}")
    print(f"  Pending: {len(p)}  In progress: {len(ip)}  Completed: {len(c)}  Failed: {len(f)}  Poisoned: {len(po)}")
    print(f"  Config: workers={cfg.get('workers',1)}, profile={cfg.get('profile','?')}, max_retries={cfg.get('max_retries',3)}")
    if ip:
        print("\nIN PROGRESS:")
        for wid, info in ip.items(): print(f"  [{wid}] {info.get('title','')[:50]} (started {info.get('started_at','?')})")
    if p:
        print(f"\nNEXT {min(5,len(p))} PENDING:")
        for item in p[:5]: print(f"  {item.get('source_count',0):>4}  {item['nb_id'][:12]}  {item.get('title','')[:50]}")
        if len(p) > 5: print(f"  ... and {len(p)-5} more")
    if f:
        print(f"\nFAILED ({len(f)}):")
        for item in f[:5]: print(f"  {item['nb_id'][:12]}  attempts={item.get('attempts',0)}  {item.get('error','')[:50]}")

def do_retry_failed():
    fd = _acquire_lock()
    try:
        queue = load_queue()
        failed = queue.get("failed", [])
        if not failed: print("[retry] No failed items", flush=True); return
        for item in failed: queue.setdefault("pending", []).append({"nb_id": item["nb_id"], "title": item.get("title",""), "source_count": 0})
        queue["failed"] = []
        save_queue(queue)
        print(f"[retry] Moved {len(failed)} failed items back to pending", flush=True)
    finally:
        _release_lock(fd)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--enqueue", action="store_true")
    g.add_argument("--worker", action="store_true")
    g.add_argument("--status", action="store_true")
    g.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--profile", default=PROFILE_DEFAULT)
    ap.add_argument("--worker-id", default=None)
    ap.add_argument("--min-sources", type=int, default=MIN_SOURCES)
    args = ap.parse_args()
    if args.enqueue: do_enqueue(args.profile, args.min_sources)
    elif args.worker: do_worker(args.worker_id or f"w{int(time.time())%10000}", args.profile)
    elif args.status: do_status()
    elif args.retry_failed: do_retry_failed()

if __name__ == "__main__":
    sys.exit(main() if callable(main) else 0)
