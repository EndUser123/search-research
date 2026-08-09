#!/usr/bin/env python3
# ruff: noqa: E701, E702
"""queue_sync.py — queue-of-work pattern for parallel wiki-yt ingestion.

Durable location: P:/.agents/skills/wiki-yt/scripts/bin/queue_sync.py
Queue file: P:/.data/wiki/_state/nlm-sync/queue.json

Usage:
  python queue_sync.py --enqueue --account-profile a.hominidae
  python queue_sync.py --worker --worker-id w1 --account-profile a.hominidae
  python queue_sync.py --status
  python queue_sync.py --retry-failed
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
from ytis_nlm import ensure_account_session, list_notebooks as list_canonical_notebooks

PROFILE_DEFAULT = "a.hominidae"
MIN_SOURCES = 50
MAX_RETRIES = 3
LEASE_TIMEOUT_S = 7200
LOCK_TIMEOUT_S = 300
# Exact account identities known to this host. Each account has its own
# canonical YTIS storage file and rate/concurrency budget; worker labels are
# telemetry only and never select auth state.
PROFILE_META = {
    "a.hominidae": {"email": "a.hominidae@gmail.com", "tier": "paid", "max_sources": 300, "max_workers": 3},
    "troup.hominidae": {"email": "troup.hominidae@gmail.com", "tier": "free", "max_sources": 50, "max_workers": 3},
    "brsthomson": {"email": "brsthomson@hotmail.com", "tier": "free", "max_sources": 50, "max_workers": 3},
}
QUEUE_FILE = Path("P:/.data/wiki/_state/nlm-sync/queue.json")
QUEUE_LOG_DIR = Path("P:/.logs/wiki-yt-queue")
SYNC_SCRIPT = "P:/.agents/skills/wiki-yt/scripts/sync.py"

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
            os.write(fd, json.dumps({
                "pid": os.getpid(),
                "started_at_epoch": time.time(),
            }).encode("utf-8"))
            return fd
        except FileExistsError:
            try:
                age_s = time.time() - lock.stat().st_mtime
                if age_s > LOCK_TIMEOUT_S:
                    lock.unlink()
                    continue
            except (FileNotFoundError, OSError):
                continue
            time.sleep(0.1)
    raise TimeoutError(f"Could not acquire queue lock after {timeout}s")

def _release_lock(fd):
    try:
        os.close(fd)
    except OSError:
        pass
    try:
        _lock_path().unlink()
    except FileNotFoundError:
        pass

def load_queue():
    if QUEUE_FILE.exists():
        try:
            return json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"queue file is invalid JSON; refusing to replace it: {QUEUE_FILE}: {exc}"
            ) from exc
    return _empty_queue()

def _empty_queue():
    return {"pending": [], "in_progress": {}, "completed": [], "failed": [], "poisoned": [],
            "config": {"workers": 1, "profiles": [PROFILE_DEFAULT], "profile": PROFILE_DEFAULT,
                       "max_retries": MAX_RETRIES, "lease_timeout_s": LEASE_TIMEOUT_S,
                       "min_sources": MIN_SOURCES, "profile_meta": PROFILE_META,
                       "profile_limits": {p: meta["max_workers"] for p, meta in PROFILE_META.items()}},
            "created": date.today().isoformat()}

def save_queue(queue):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(queue, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, QUEUE_FILE)


def persist_run_output(worker_id, item, stdout, stderr):
    """Keep the full child output for post-run diagnosis and retries."""
    run_dir = QUEUE_LOG_DIR / datetime.now().strftime("%Y%m%d")
    run_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{worker_id}-{item['nb_id']}-{time.time_ns()}"
    stdout_path = run_dir / f"{stem}.stdout.log"
    stderr_path = run_dir / f"{stem}.stderr.log"
    stdout_path.write_text(stdout or "", encoding="utf-8")
    stderr_path.write_text(stderr or "", encoding="utf-8")
    return stdout_path, stderr_path


def classify_sync_result(returncode, stdout, stderr):
    """Require an explicit successful per-notebook result before completion."""
    combined = f"{stdout or ''}\n{stderr or ''}"
    if returncode != 0:
        return f"failed (rc={returncode})"
    if "SKIP (source_ids unchanged" in combined:
        return "skipped_unchanged"
    if re.search(r"Synced:\s*1/1\b", combined):
        return "synced"
    return "failed (pipeline_not_complete)"

def _pending_record(item, profile):
    return {
        "nb_id": item["nb_id"],
        "title": item.get("title", ""),
        "source_count": item.get("source_count", 0),
        "profile": item.get("profile") or profile,
    }

def _failure_record(item, profile, error, attempts):
    record = _pending_record(item, profile)
    record.update({"error": error, "attempts": attempts})
    return record


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _lease_age_s(record, now_epoch: float) -> float | None:
    started_epoch = record.get("started_at_epoch")
    if isinstance(started_epoch, (int, float)):
        return max(0.0, now_epoch - float(started_epoch))
    # Old HH:MM:SS records are deliberately not reclaimed: their date is
    # ambiguous across midnight and an unsafe reclaim can duplicate work.
    started_at = str(record.get("started_at", ""))
    if "T" not in started_at:
        return None
    try:
        parsed = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0.0, now_epoch - parsed.timestamp())


def _profile_limit(queue, profile):
    config = queue.get("config", {})
    limits = config.get("profile_limits", {})
    if isinstance(limits, dict) and isinstance(limits.get(profile), int):
        return max(1, int(limits[profile]))
    meta = config.get("profile_meta", PROFILE_META)
    if isinstance(meta, dict) and isinstance(meta.get(profile), dict):
        return max(1, int(meta[profile].get("max_workers", 1)))
    return max(1, int(PROFILE_META.get(profile, {}).get("max_workers", 1)))


def _active_for_profile(queue, profile):
    return sum(
        1
        for record in queue.get("in_progress", {}).values()
        if str(record.get("profile", "")) == profile
    )


def _reclaim_stale_leases(queue, *, now_epoch=None):
    """Return expired claims to pending without losing account identity."""
    now_epoch = time.time() if now_epoch is None else now_epoch
    timeout_s = float(queue.get("config", {}).get("lease_timeout_s", LEASE_TIMEOUT_S))
    reclaimed = []
    in_progress = queue.setdefault("in_progress", {})
    for worker_id, record in list(in_progress.items()):
        age_s = _lease_age_s(record, now_epoch)
        if age_s is None or age_s <= timeout_s:
            continue
        item = {
            "nb_id": record.get("nb_id", ""),
            "title": record.get("title", ""),
            "source_count": record.get("source_count", 0),
            "profile": record.get("profile", PROFILE_DEFAULT),
        }
        if not item["nb_id"]:
            continue
        if not _has_pending(queue, item["nb_id"], item["profile"]):
            queue.setdefault("pending", []).append(item)
        in_progress.pop(worker_id, None)
        reclaimed.append({"worker_id": worker_id, "nb_id": item["nb_id"], "profile": item["profile"], "age_s": round(age_s, 1)})
    return reclaimed


def _claim_pending(queue, worker_id, profile):
    """Claim one eligible item while holding the queue lock."""
    config = queue.setdefault("config", {})
    active_total = len(queue.get("in_progress", {}))
    configured_total = max(1, int(config.get("workers", 1)))
    active_profile = _active_for_profile(queue, profile)
    if active_total >= configured_total or active_profile >= _profile_limit(queue, profile):
        return None, "capacity"
    pending = queue.setdefault("pending", [])
    index = next((i for i, item in enumerate(pending) if item.get("profile", profile) == profile), None)
    if index is None:
        return None, "no_pending_for_profile"
    item = pending.pop(index)
    now = _utc_now()
    lease_id = f"{worker_id}-{time.time_ns()}"
    queue.setdefault("in_progress", {})[worker_id] = {
        "lease_id": lease_id,
        "worker_id": worker_id,
        "nb_id": item["nb_id"],
        "title": item.get("title", ""),
        "source_count": item.get("source_count", 0),
        "profile": item.get("profile", profile),
        "started_at": now.isoformat().replace("+00:00", "Z"),
        "started_at_epoch": now.timestamp(),
        "pid": os.getpid(),
    }
    return (item, lease_id), "claimed"


def _claim_is_current(queue, worker_id, lease_id):
    return queue.get("in_progress", {}).get(worker_id, {}).get("lease_id") == lease_id


def _remove_current_claim(queue, worker_id, lease_id):
    if not _claim_is_current(queue, worker_id, lease_id):
        return False
    queue.setdefault("in_progress", {}).pop(worker_id, None)
    return True


def _has_pending(queue, nb_id, profile):
    return any(
        item.get("nb_id") == nb_id and (item.get("profile") or profile) == profile
        for item in queue.get("pending", [])
    )


def _failure_attempts(queue, item, profile):
    prior = [
        record for record in queue.get("failed", [])
        if record.get("nb_id") == item.get("nb_id")
        and (record.get("profile") or profile) == profile
    ]
    return max(int(item.get("attempts", 0) or 0), len(prior)) + 1


def _release_claim(queue, worker_id, lease_id, item, profile, error, *, requeue=True):
    """Release a live claim and record a retryable failure, if still owned."""
    if not _remove_current_claim(queue, worker_id, lease_id):
        return False
    attempts = _failure_attempts(queue, item, profile)
    failure = _failure_record(item, profile, error, attempts)
    failure["last_failed_at"] = _utc_now().isoformat().replace("+00:00", "Z")
    max_retries = int(queue.get("config", {}).get("max_retries", MAX_RETRIES))
    if attempts >= max_retries:
        queue.setdefault("poisoned", []).append(failure)
    else:
        queue.setdefault("failed", []).append(failure)
        if requeue and not _has_pending(queue, item.get("nb_id"), profile):
            retry_item = _pending_record(item, profile)
            retry_item["attempts"] = attempts
            retry_item["last_error"] = error
            queue.setdefault("pending", []).append(retry_item)
    return True


def _record_success(queue, worker_id, lease_id, item, profile, status, elapsed):
    if not _remove_current_claim(queue, worker_id, lease_id):
        return False
    queue.setdefault("completed", []).append({
        "nb_id": item["nb_id"],
        "title": item.get("title", ""),
        "profile": profile,
        "status": status,
        "elapsed_s": round(elapsed, 1),
        "completed_at": _utc_now().isoformat().replace("+00:00", "Z"),
    })
    return True

def list_notebooks(profile):
    try:
        return list_canonical_notebooks(profile, worker_id="wiki-yt-queue-list")
    except Exception as exc:
        raise RuntimeError(
            f"canonical notebook list failed for {profile}: {type(exc).__name__}: {str(exc)[:240]}"
        ) from exc

def do_enqueue(profiles, min_sources, workers=None):
    """Enqueue notebooks from one or more profiles."""
    if isinstance(profiles, str):
        profiles = [profiles]
    discovered = {}
    for prof in profiles:
        if not ensure_auth(prof):
            print(f"[enqueue:{prof}] refused: canonical account is unavailable", flush=True)
            return 2
        try:
            discovered[prof] = list_notebooks(prof)
        except RuntimeError as exc:
            print(f"[enqueue:{prof}] refused: {exc}", flush=True)
            return 2
    fd = _acquire_lock()
    try:
        queue = load_queue()
        already = {i["nb_id"] for i in queue.get("pending", [])} | {i["nb_id"] for i in queue.get("completed", [])} | {i["nb_id"] for i in queue.get("failed", [])} | {i["nb_id"] for i in queue.get("poisoned", [])}
        total_new = 0
        for prof in profiles:
            nbs = discovered[prof]
            candidates = [n for n in nbs if (n.get("source_count") or 0) >= min_sources and not (n.get("title") or "").startswith("[INGESTED]")]
            candidates.sort(key=lambda n: -(n.get("source_count") or 0))
            new_items = [{"nb_id": n["id"], "title": (n.get("title") or "")[:60], "source_count": n.get("source_count", 0), "profile": prof} for n in candidates if n["id"] not in already]
            if new_items:
                queue.setdefault("pending", []).extend(new_items)
                already.update(n["nb_id"] for n in new_items)
                total_new += len(new_items)
            print(f"[enqueue:{prof}] {len(new_items)} new notebooks ({len(nbs)} total, {len(candidates)} qualifying)", flush=True)
        queue.setdefault("config", {})["profiles"] = profiles
        if workers is not None:
            if workers < 1:
                print("[enqueue] --workers must be at least 1", flush=True)
                return 2
            queue.setdefault("config", {})["workers"] = int(workers)
        queue.setdefault("config", {})["profile_limits"] = {
            profile: _profile_limit(queue, profile) for profile in profiles
        }
        save_queue(queue)
        print(f"[enqueue] {total_new} new notebooks added across {len(profiles)} profile(s). Queue: {len(queue['pending'])} pending, {len(queue.get('completed',[]))} completed", flush=True)
    finally:
        _release_lock(fd)
    return 0

def ensure_auth(profile):
    try:
        probe = ensure_account_session(profile, worker_id="wiki-yt-queue-worker")
    except Exception as exc:
        print(f"[worker] canonical auth probe failed for {profile}: {str(exc)[:240]}", flush=True)
        return False
    if probe.ok:
        return True
    print(
        f"[worker] canonical auth unavailable for {profile}: {probe.reason}; "
        "non-interactive durable repair was attempted",
        flush=True,
    )
    return False

def do_worker(worker_id, profile):
    print(f"[worker:{worker_id}] Starting (profile={profile})", flush=True)
    while True:
        fd = _acquire_lock()
        try:
            queue = load_queue()
            reclaimed = _reclaim_stale_leases(queue)
            claim, reason = _claim_pending(queue, worker_id, profile)
            if reclaimed or reason == "claimed":
                save_queue(queue)
            if reclaimed:
                print(f"[worker:{worker_id}] Reclaimed {len(reclaimed)} stale lease(s)", flush=True)
            if reason == "capacity":
                print(f"[worker:{worker_id}] configured capacity reached; exiting", flush=True)
                break
            if reason == "no_pending_for_profile":
                break
            item, lease_id = claim
        finally:
            _release_lock(fd)
        nb_id = item["nb_id"]; title = item.get("title", ""); sc = item.get("source_count", 0)
        item_profile = item.get("profile") or profile
        print(f"[worker:{worker_id}] Claimed: {title[:50]} ({sc} sources, profile={item_profile})", flush=True)
        if not ensure_auth(item_profile):
            fd = _acquire_lock()
            try:
                queue = load_queue()
                if _release_claim(queue, worker_id, lease_id, item, item_profile, "auth_failed"):
                    save_queue(queue)
            finally:
                _release_lock(fd)
            print(f"[worker:{worker_id}] auth unavailable; claim returned for retry", flush=True)
            break
        start = time.time()
        try:
            r = subprocess.run(
                [sys.executable, SYNC_SCRIPT, "--notebook", nb_id, "--account-profile", item_profile],
                capture_output=True, text=True, timeout=3600, encoding="utf-8",
            )
            elapsed = time.time() - start
        except subprocess.TimeoutExpired:
            elapsed = 3600
            fd = _acquire_lock()
            try:
                queue = load_queue()
                if _release_claim(queue, worker_id, lease_id, item, item_profile, "timeout"):
                    save_queue(queue)
            finally:
                _release_lock(fd)
            print(f"[worker:{worker_id}] TIMEOUT: {title[:40]} ({elapsed:.0f}s)", flush=True)
            continue
        stdout_path, stderr_path = persist_run_output(worker_id, item, r.stdout, r.stderr)
        status = classify_sync_result(r.returncode, r.stdout, r.stderr)
        fd = _acquire_lock()
        try:
            queue = load_queue()
            if status in ("synced", "skipped_unchanged"):
                recorded = _record_success(queue, worker_id, lease_id, item, item_profile, status, elapsed)
            else:
                error = status
                recorded = _release_claim(queue, worker_id, lease_id, item, item_profile, error)
            if recorded:
                save_queue(queue)
            else:
                print(f"[worker:{worker_id}] lease no longer current; late result not recorded", flush=True)
        finally:
            _release_lock(fd)
        err_lines = [line for line in f"{r.stdout or ''}\n{r.stderr or ''}".splitlines() if line.strip()][-3:]
        for line in err_lines: print(f"[worker:{worker_id}]   {line.strip()}", flush=True)
        print(f"[worker:{worker_id}]   -> {status} ({elapsed:.0f}s)", flush=True)
        print(f"[worker:{worker_id}]   logs: {stdout_path} / {stderr_path}", flush=True)
    print(f"[worker:{worker_id}] Done", flush=True)

def do_status():
    queue = load_queue()
    p, ip, c, f, po = queue.get("pending",[]), queue.get("in_progress",{}), queue.get("completed",[]), queue.get("failed",[]), queue.get("poisoned",[])
    cfg = queue.get("config",{})
    print(f"\n{'='*60}\nNLM-TO-WIKI QUEUE STATUS\n{'='*60}")
    print(f"  Pending: {len(p)}  In progress: {len(ip)}  Completed: {len(c)}  Failed: {len(f)}  Poisoned: {len(po)}")
    print(f"  Config: workers={cfg.get('workers',1)}, profiles={cfg.get('profiles',[cfg.get('profile','?')])}, max_retries={cfg.get('max_retries',3)}")
    if ip:
        print("\nIN PROGRESS:")
        for wid, info in ip.items(): print(f"  [{wid}] {info.get('title','')[:50]} (started {info.get('started_at','?')})")
    if p:
        print(f"\nNEXT {min(5,len(p))} PENDING:")
        for item in p[:5]: print(f"  {item.get('source_count',0):>4}  {item.get('profile','?'):<12}  {item['nb_id'][:12]}  {item.get('title','')[:50]}")
        if len(p) > 5: print(f"  ... and {len(p)-5} more")
    if f:
        print(f"\nFAILED ({len(f)}):")
        for item in f[:5]: print(f"  {item['nb_id'][:12]}  attempts={item.get('attempts',0)}  {item.get('error','')[:50]}")

def do_retry_failed():
    fd = _acquire_lock()
    try:
        queue = load_queue()
        failed = queue.get("failed", [])
        if not failed:
            print("[retry] No failed items", flush=True)
            return 0
        for item in failed:
            profile = item.get("profile") or queue.get("config", {}).get("profile", PROFILE_DEFAULT)
            if not _has_pending(queue, item["nb_id"], profile):
                queue.setdefault("pending", []).append({
                    "nb_id": item["nb_id"],
                    "title": item.get("title", ""),
                    "source_count": item.get("source_count", 0),
                    "profile": profile,
                    "attempts": item.get("attempts", 0),
                })
        queue["failed"] = []
        save_queue(queue)
        print(f"[retry] Moved {len(failed)} failed items back to pending", flush=True)
        return 0
    finally:
        _release_lock(fd)

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--enqueue", action="store_true")
    g.add_argument("--worker", action="store_true")
    g.add_argument("--status", action="store_true")
    g.add_argument("--retry-failed", action="store_true")
    ap.add_argument("--profile", "--account-profile", dest="profile", default=PROFILE_DEFAULT,
                    help="Single profile (default: a.hominidae). Use --all-profiles to enqueue from all.")
    ap.add_argument("--all-profiles", action="store_true",
                    help="Enqueue from all configured profiles (a.hominidae + troup.hominidae + brsthomson)")
    ap.add_argument("--worker-id", default=None)
    ap.add_argument("--min-sources", type=int, default=MIN_SOURCES)
    ap.add_argument("--workers", type=int, default=None,
                    help="total queue worker capacity (per-account limits still apply)")
    args = ap.parse_args()
    if args.enqueue:
        profiles = list(PROFILE_META.keys()) if args.all_profiles else [args.profile]
        return do_enqueue(profiles, args.min_sources, args.workers)
    elif args.worker: do_worker(args.worker_id or f"w{int(time.time())%10000}", args.profile)
    elif args.status: do_status()
    elif args.retry_failed: return do_retry_failed()
    return 0

if __name__ == "__main__":
    sys.exit(main() if callable(main) else 0)
