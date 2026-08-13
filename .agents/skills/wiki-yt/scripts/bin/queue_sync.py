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
  python queue_sync.py --retry-deferred --synth-backend mmx
  python queue_sync.py --retry-poisoned --notebook-id <UUID> --synth-backend dgemma

Retry refuses legacy failed records that do not carry an exact canonical
account profile. It must never fall back to a stale or non-canonical queue
profile because that can send work to the wrong account.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import signal
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
DEFAULT_SYNC_TIMEOUT_S = 3600
PROCESS_TERMINATION_GRACE_S = 30
QUEUE_SCHEMA_VERSION = 2
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

def _decode_output(value):
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _terminate_process_tree(process):
    """Terminate a timed-out sync process and descendants."""
    pid = getattr(process, "pid", None)
    if not pid:
        return
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    try:
        os.killpg(os.getpgid(pid), signal.SIGKILL)
    except (ProcessLookupError, OSError):
        try:
            process.kill()
        except (AttributeError, OSError):
            pass


def _run_captured(cmd, timeout=120):
    """Run one child with a hard deadline and descendant cleanup."""
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            creationflags=creationflags,
            start_new_session=os.name != "nt",
        )
    except OSError as exc:
        return 127, "", f"RUNNER_ERROR: {type(exc).__name__}: {exc}", False
    try:
        stdout, stderr = process.communicate(timeout=timeout)
        return process.returncode, _decode_output(stdout), _decode_output(stderr), False
    except subprocess.TimeoutExpired as exc:
        _terminate_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=PROCESS_TERMINATION_GRACE_S)
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except (AttributeError, OSError):
                pass
            stdout, stderr = process.communicate()
        timeout_message = f"TIMEOUT after {timeout:g}s; process_tree_terminated"
        stderr_text = _decode_output(stderr)
        if timeout_message not in stderr_text:
            stderr_text = (stderr_text + "\n" + timeout_message).strip()
        return 124, _decode_output(stdout or exc.stdout), stderr_text, True


def _run(cmd, timeout=120):
    return _run_captured(cmd, timeout)[:3]

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
            os.fsync(fd)
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
            queue = json.loads(QUEUE_FILE.read_text(encoding="utf-8"))
            _upgrade_queue(queue)
            return queue
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"queue file is invalid JSON; refusing to replace it: {QUEUE_FILE}: {exc}"
            ) from exc
    return _empty_queue()

def _upgrade_queue(queue):
    """Add durable fields and recover known deferred quality obligations."""
    queue.setdefault("pending", [])
    queue.setdefault("in_progress", {})
    queue.setdefault("completed", [])
    queue.setdefault("failed", [])
    queue.setdefault("failure_history", [])
    queue.setdefault("poisoned", [])
    queue.setdefault("needs_resynthesis", [])
    queue.setdefault("deferred_history", [])
    queue.setdefault("config", {})
    queue["config"].setdefault("sync_timeout_s", DEFAULT_SYNC_TIMEOUT_S)
    queue["config"].setdefault("profile_meta", PROFILE_META)
    queue["config"].setdefault(
        "profile_limits",
        {profile: meta["max_workers"] for profile, meta in PROFILE_META.items()},
    )
    queue["schema_version"] = QUEUE_SCHEMA_VERSION

    # A later true semantic sync resolves any older degraded quality debt for
    # the same notebook/account. Keep this set separate from degraded terminal
    # records so migration cannot resurrect already-cleared debt on every load.
    semantic_successes = {
        _item_key(item)
        for item in queue["completed"]
        if item.get("status") == "synced"
    }
    queue["needs_resynthesis"] = [
        item for item in queue["needs_resynthesis"]
        if _item_key(item) not in semantic_successes
    ]

    # Older queue files recorded degraded output as completed but had no
    # durable quality debt list. Reconstruct only what the old record proves:
    # notebook ID, title, profile, status, and completion time.
    known = {_item_key(item) for item in queue["needs_resynthesis"]}
    for item in queue["completed"]:
        if item.get("status") != "synced_degraded_fallback":
            continue
        key = _item_key(item)
        if key in known or key in semantic_successes:
            continue
        queue["needs_resynthesis"].append({
            "nb_id": item.get("nb_id", ""),
            "title": item.get("title", ""),
            "source_count": item.get("source_count", 0),
            "profile": item.get("profile", ""),
            "reason": "degraded_fallback",
            "attempts": 0,
            "deferred_at": item.get("completed_at", ""),
            "legacy_migration": True,
            "stdout_path": item.get("stdout_path", ""),
            "stderr_path": item.get("stderr_path", ""),
        })
        known.add(key)

def _empty_queue():
    return {"schema_version": QUEUE_SCHEMA_VERSION,
            "pending": [], "in_progress": {}, "completed": [], "failed": [], "failure_history": [], "poisoned": [],
            "needs_resynthesis": [], "deferred_history": [],
            "config": {"workers": 1, "profiles": [PROFILE_DEFAULT], "profile": PROFILE_DEFAULT,
                       "max_retries": MAX_RETRIES, "lease_timeout_s": LEASE_TIMEOUT_S,
                       "sync_timeout_s": DEFAULT_SYNC_TIMEOUT_S,
                       "min_sources": MIN_SOURCES, "profile_meta": PROFILE_META,
                       "profile_limits": {p: meta["max_workers"] for p, meta in PROFILE_META.items()}},
            "created": date.today().isoformat()}

def save_queue(queue):
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = QUEUE_FILE.with_suffix(".tmp")
    _write_and_fsync(tmp, json.dumps(queue, ensure_ascii=False, indent=2))
    os.replace(tmp, QUEUE_FILE)


def _write_and_fsync(path, content):
    """Flush the queue snapshot before publishing its atomic replacement."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def persist_run_output(worker_id, item, stdout, stderr):
    """Keep the full child output for post-run diagnosis and retries."""
    run_dir = QUEUE_LOG_DIR / datetime.now().strftime("%Y%m%d")
    run_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{worker_id}-{item['nb_id']}-{time.time_ns()}"
    stdout_path = run_dir / f"{stem}.stdout.log"
    stderr_path = run_dir / f"{stem}.stderr.log"
    _write_and_fsync(stdout_path, stdout or "")
    _write_and_fsync(stderr_path, stderr or "")
    return stdout_path, stderr_path


def classify_sync_result(returncode, stdout, stderr):
    """Require an explicit successful per-notebook result before completion."""
    combined = f"{stdout or ''}\n{stderr or ''}"
    for failure_class in (
        "synthesis_degraded",
        "citation_invalid",
        "synthesis_backend_exhausted",
    ):
        if f"FAILURE_CLASS={failure_class}" in combined:
            return f"failed ({failure_class})"
    if "SYNTHESIS_QUALITY=degraded_fallback" in combined:
        if "DEGRADED_FALLBACK_PROMOTED=1" not in combined:
            return "failed (degraded_fallback_not_promoted)"
        if returncode == 0 and re.search(r"Synced:\s*1/1\b", combined):
            return "synced_degraded_fallback"
        return "failed (degraded_fallback_incomplete)"
    if returncode != 0:
        return f"failed (rc={returncode})"
    if "SKIP (source_ids unchanged" in combined:
        return "skipped_unchanged"
    if re.search(r"Synced:\s*1/1\b", combined):
        return "synced"
    return "failed (pipeline_not_complete)"

def _pending_record(item, profile):
    record = {
        "nb_id": item["nb_id"],
        "title": item.get("title", ""),
        "source_count": item.get("source_count", 0),
        "profile": item.get("profile") or profile,
    }
    # Preserve explicit retry policy across automatic attempts. Without this,
    # a deferred alternate-backend retry silently reverted to the default
    # backend after its first failure.
    for key in (
        "retry_backend",
        "allow_degraded_fallback",
        "force_resynthesis",
        "timeout_s",
        "max_attempts",
        "retry_reason",
        "deferred_resynthesis",
        "synth_context_budget",
        "synth_checkpoint_path",
    ):
        if key in item:
            record[key] = item[key]
    return record


def _synth_checkpoint_args(item):
    """Return the Stage-C create/resume flag for one queue item."""
    checkpoint_path = item.get("synth_checkpoint_path")
    if not checkpoint_path:
        return []
    checkpoint = Path(str(checkpoint_path))
    return ["--synth-resume" if checkpoint.exists() else "--synth-checkpoint", str(checkpoint)]

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


def _pid_is_alive(pid):
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except (OSError, ProcessLookupError, PermissionError):
        return False
    return True


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


def _item_key(item, profile=None):
    return (
        str(item.get("nb_id", "")).strip(),
        str(item.get("profile") or profile or "").strip(),
    )


def _sync_timeout_s(item):
    """Return a finite positive per-item timeout, with legacy fallback."""
    raw = item.get("timeout_s", DEFAULT_SYNC_TIMEOUT_S)
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return DEFAULT_SYNC_TIMEOUT_S
    return value if value > 0 else DEFAULT_SYNC_TIMEOUT_S


def _terminal_keys(queue):
    """Return notebook/account keys with an authoritative terminal outcome."""
    completed = {_item_key(item) for item in queue.get("completed", [])}
    poisoned = {_item_key(item) for item in queue.get("poisoned", [])}
    return completed | poisoned


def reconcile_terminal_records(queue):
    """Archive stale failed attempts that already have a terminal outcome.

    Failed attempts are retained in ``failure_history`` for diagnosis, but are
    removed from the active ``failed`` list so status and retry operations cannot
    treat a later success or poison disposition as actionable work.
    """
    terminal = _terminal_keys(queue)
    if not terminal:
        return 0
    active_failed = []
    archived = []
    resolved_at = _utc_now().isoformat().replace("+00:00", "Z")
    for item in queue.get("failed", []):
        if _item_key(item) not in terminal:
            active_failed.append(item)
            continue
        record = dict(item)
        record["history_status"] = "resolved_terminal"
        record["resolved_at"] = resolved_at
        archived.append(record)
    if not archived:
        return 0
    queue["failed"] = active_failed
    queue.setdefault("failure_history", []).extend(archived)
    return len(archived)


def _failure_attempts(queue, item, profile):
    prior = [
        record for record in queue.get("failed", [])
        if record.get("nb_id") == item.get("nb_id")
        and (record.get("profile") or profile) == profile
    ]
    return max(int(item.get("attempts", 0) or 0), len(prior)) + 1


def _release_claim(
    queue, worker_id, lease_id, item, profile, error, *, requeue=True,
    output_paths=None,
):
    """Release a live claim and record a retryable failure, if still owned."""
    if not _remove_current_claim(queue, worker_id, lease_id):
        return False
    attempts = _failure_attempts(queue, item, profile)
    failure = _failure_record(item, profile, error, attempts)
    failure["last_failed_at"] = _utc_now().isoformat().replace("+00:00", "Z")
    if output_paths:
        failure["stdout_path"] = str(output_paths[0])
        failure["stderr_path"] = str(output_paths[1])
    configured_max = item.get("max_attempts")
    max_retries = int(
        configured_max
        if configured_max is not None
        else queue.get("config", {}).get("max_retries", MAX_RETRIES)
    )
    if max_retries < 1:
        raise ValueError("max_attempts must be >= 1")
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


def _record_success(
    queue, worker_id, lease_id, item, profile, status, elapsed, output_paths=None
):
    if not _remove_current_claim(queue, worker_id, lease_id):
        return False
    completed_at = _utc_now().isoformat().replace("+00:00", "Z")
    completed = {
        "nb_id": item["nb_id"],
        "title": item.get("title", ""),
        "source_count": item.get("source_count", 0),
        "profile": profile,
        "status": status,
        "elapsed_s": round(elapsed, 1),
        "completed_at": completed_at,
    }
    if output_paths:
        completed["stdout_path"] = str(output_paths[0])
        completed["stderr_path"] = str(output_paths[1])
    queue.setdefault("completed", []).append(completed)

    key = _item_key(item, profile)
    deferred = queue.setdefault("needs_resynthesis", [])
    if status == "synced_degraded_fallback":
        existing = next((record for record in deferred if _item_key(record) == key), None)
        if existing is None:
            deferred.append({
                "nb_id": item["nb_id"],
                "title": item.get("title", ""),
                "source_count": item.get("source_count", 0),
                "profile": profile,
                "reason": "degraded_fallback",
                "attempts": 0,
                "deferred_at": completed_at,
                "stdout_path": str(output_paths[0]) if output_paths else "",
                "stderr_path": str(output_paths[1]) if output_paths else "",
            })
        else:
            existing.update({
                "last_deferred_at": completed_at,
                "stdout_path": str(output_paths[0]) if output_paths else existing.get("stdout_path", ""),
                "stderr_path": str(output_paths[1]) if output_paths else existing.get("stderr_path", ""),
            })
    elif status == "synced":
        queue["needs_resynthesis"] = [
            record for record in deferred if _item_key(record) != key
        ]
    reconcile_terminal_records(queue)
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
            sync_command = [
                sys.executable,
                SYNC_SCRIPT,
                "--notebook",
                nb_id,
                "--account-profile",
                item_profile,
            ]
            retry_backend = item.get("retry_backend")
            if retry_backend:
                sync_command.extend(["--synth-backend", str(retry_backend)])
            if item.get("allow_degraded_fallback"):
                sync_command.append("--allow-degraded-fallback")
            if item.get("force_resynthesis"):
                sync_command.append("--force-resynthesis")
            if item.get("synth_context_budget") is not None:
                sync_command.extend([
                    "--synth-context-budget",
                    str(item["synth_context_budget"]),
                ])
            sync_command.extend(_synth_checkpoint_args(item))
            timeout_s = _sync_timeout_s(item)
            returncode, stdout, stderr, timed_out = _run_captured(
                sync_command,
                timeout=timeout_s,
            )
            elapsed = time.time() - start
        except Exception as exc:
            elapsed = time.time() - start
            returncode = 1
            stdout = ""
            stderr = f"RUNNER_ERROR: {type(exc).__name__}: {exc}"
            timed_out = False
        stdout_path, stderr_path = persist_run_output(worker_id, item, stdout, stderr)
        if timed_out:
            status = f"failed (timeout after {_sync_timeout_s(item):g}s)"
        else:
            status = classify_sync_result(returncode, stdout, stderr)
        fd = _acquire_lock()
        try:
            queue = load_queue()
            if status in ("synced", "synced_degraded_fallback", "skipped_unchanged"):
                recorded = _record_success(
                    queue, worker_id, lease_id, item, item_profile, status, elapsed,
                    output_paths=(stdout_path, stderr_path),
                )
            else:
                error = status
                recorded = _release_claim(
                    queue, worker_id, lease_id, item, item_profile, error,
                    output_paths=(stdout_path, stderr_path),
                )
            if recorded:
                save_queue(queue)
            else:
                print(f"[worker:{worker_id}] lease no longer current; late result not recorded", flush=True)
        finally:
            _release_lock(fd)
        err_lines = [line for line in f"{stdout or ''}\n{stderr or ''}".splitlines() if line.strip()][-3:]
        for line in err_lines: print(f"[worker:{worker_id}]   {line.strip()}", flush=True)
        print(f"[worker:{worker_id}]   -> {status} ({elapsed:.0f}s)", flush=True)
        print(f"[worker:{worker_id}]   logs: {stdout_path} / {stderr_path}", flush=True)
    print(f"[worker:{worker_id}] Done", flush=True)

def do_status():
    fd = _acquire_lock()
    try:
        queue = load_queue()
        reconcile_terminal_records(queue)
        # Status is also the safe, locked place to persist schema upgrades and
        # migrate historical degraded completions into the visible debt list.
        save_queue(queue)
    finally:
        _release_lock(fd)
    p, ip, c, f, po = queue.get("pending",[]), queue.get("in_progress",{}), queue.get("completed",[]), queue.get("failed",[]), queue.get("poisoned",[])
    deferred = queue.get("needs_resynthesis", [])
    cfg = queue.get("config",{})
    print(f"\n{'='*60}\nNLM-TO-WIKI QUEUE STATUS\n{'='*60}")
    print(f"  Pending: {len(p)}  In progress: {len(ip)}  Completed: {len(c)}  Failed: {len(f)}  Poisoned: {len(po)}")
    print(f"  Needs semantic resynthesis: {len(deferred)}")
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
    if deferred:
        print(f"\nNEEDS SEMANTIC RESYNTHESIS ({len(deferred)}):")
        for item in deferred[:5]:
            print(f"  {item['nb_id'][:12]}  {item.get('profile','?'):<15}  {item.get('reason','deferred')}")
    if queue.get("failure_history"):
        print(f"\n  Archived failure attempts: {len(queue['failure_history'])}")


def do_reconcile():
    """Archive failed records already resolved by completed or poisoned state."""
    fd = _acquire_lock()
    try:
        queue = load_queue()
        archived = reconcile_terminal_records(queue)
        if archived:
            save_queue(queue)
        print(f"[reconcile] Archived {archived} stale failed record(s)", flush=True)
        return 0
    finally:
        _release_lock(fd)

def do_retry_failed():
    fd = _acquire_lock()
    try:
        queue = load_queue()
        reconcile_terminal_records(queue)
        failed = queue.get("failed", [])
        if not failed:
            print("[retry] No failed items", flush=True)
            return 0

        # Older queue records may predate durable account ownership. Refuse
        # the whole operation rather than silently routing them through the
        # legacy queue-level profile (which may be an alias or stale value).
        invalid_profile_items = []
        for item in failed:
            profile = str(item.get("profile") or "").strip()
            if not item.get("nb_id") or profile not in PROFILE_META:
                invalid_profile_items.append(item)
        if invalid_profile_items:
            ids = ", ".join(
                str(item.get("nb_id") or "<missing-id>")[:80]
                for item in invalid_profile_items
            )
            print(
                "[retry] Refusing to requeue failed items without an exact "
                f"canonical account profile: {ids}. Reconcile ownership "
                "from authoritative account inventory first; no queue state "
                "was changed.",
                file=sys.stderr,
                flush=True,
            )
            return 2

        for item in failed:
            profile = str(item["profile"]).strip()
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


def do_retry_deferred(notebook_ids=None, synth_backend="mmx",
                      reason="bounded deferred semantic retry",
                      timeout_s=None, max_attempts=1,
                      synth_context_budget=None):
    """Queue exact degraded outputs for a bounded semantic retry.

    The degraded page remains usable and its deferred record remains present
    until a true ``synced`` result clears it. This prevents a failed retry from
    losing the quality obligation or silently creating duplicate normal work.
    """
    requested = {str(item).strip() for item in (notebook_ids or []) if str(item).strip()}
    if synth_backend not in {"mmx", "dgemma"}:
        raise ValueError("deferred semantic retry requires mmx or dgemma")
    if timeout_s is not None:
        timeout_s = float(timeout_s)
        if timeout_s <= 0:
            raise ValueError("timeout_s must be > 0")
    if isinstance(max_attempts, bool) or int(max_attempts) < 1:
        raise ValueError("max_attempts must be >= 1")
    max_attempts = int(max_attempts)
    if synth_context_budget is not None:
        synth_context_budget = int(synth_context_budget)
        if synth_context_budget <= 0:
            raise ValueError("synth_context_budget must be > 0")
    fd = _acquire_lock()
    try:
        queue = load_queue()
        deferred = queue.setdefault("needs_resynthesis", [])
        selected = [
            item for item in deferred
            if not requested or str(item.get("nb_id", "")).strip() in requested
        ]
        if requested:
            found = {str(item.get("nb_id", "")).strip() for item in selected}
            missing = sorted(requested - found)
            if missing:
                raise RuntimeError(
                    "requested deferred notebook IDs not found: " + ", ".join(missing)
                )
        if not selected:
            print("[retry-deferred] No matching deferred items", flush=True)
            return 0

        invalid_profile_items = [
            item for item in selected
            if not item.get("nb_id")
            or str(item.get("profile") or "").strip() not in PROFILE_META
        ]
        if invalid_profile_items:
            ids = ", ".join(str(item.get("nb_id") or "<missing-id>")[:80]
                             for item in invalid_profile_items)
            print(
                "[retry-deferred] Refusing to queue items without an exact "
                f"canonical account profile: {ids}. No queue state was changed.",
                file=sys.stderr,
                flush=True,
            )
            return 2

        active = {
            _item_key(item) for item in queue.get("pending", [])
        }
        active.update(_item_key(item) for item in queue.get("in_progress", {}).values())
        active.update(_item_key(item) for item in queue.get("poisoned", []))
        now = _utc_now().isoformat().replace("+00:00", "Z")
        reopened = 0
        for item in selected:
            key = _item_key(item)
            if key in active:
                continue
            profile = str(item["profile"]).strip()
            retry_item = _pending_record(item, profile)
            retry_item.update({
                "attempts": int(item.get("attempts", 0) or 0),
                "last_error": item.get("last_error", ""),
                "retry_reason": reason,
                "retry_backend": synth_backend,
                "force_resynthesis": True,
                "deferred_resynthesis": True,
                "timeout_s": timeout_s if timeout_s is not None else _sync_timeout_s(item),
                "max_attempts": max_attempts,
                "reopened_at": now,
            })
            if synth_context_budget is not None:
                retry_item["synth_context_budget"] = synth_context_budget
            queue.setdefault("pending", []).append(retry_item)
            history_record = dict(item)
            history_record.update({
                "history_status": "reopened",
                "reopened_at": now,
                "reopen_reason": reason,
                "retry_backend": synth_backend,
                "force_resynthesis": True,
                "timeout_s": retry_item["timeout_s"],
                "max_attempts": max_attempts,
            })
            if synth_context_budget is not None:
                history_record["synth_context_budget"] = synth_context_budget
            queue.setdefault("deferred_history", []).append(history_record)
            item.update({
                "last_reopened_at": now,
                "retry_backend": synth_backend,
                "timeout_s": retry_item["timeout_s"],
                "max_attempts": max_attempts,
                "attempts": retry_item["attempts"],
            })
            active.add(key)
            reopened += 1

        save_queue(queue)
        print(
            f"[retry-deferred] Reopened {reopened} deferred item(s); "
            f"backend={synth_backend}; deferred records preserved",
            flush=True,
        )
        return 0
    finally:
        _release_lock(fd)


def do_recover_worker(worker_id, *, requeue=False, reason="orphaned worker recovery"):
    """Release a claim only after its recorded worker PID is no longer alive."""
    worker_id = str(worker_id or "").strip()
    if not worker_id:
        raise ValueError("worker_id must be non-empty")
    fd = _acquire_lock()
    try:
        queue = load_queue()
        record = queue.get("in_progress", {}).get(worker_id)
        if not isinstance(record, dict):
            print(f"[recover] No in-progress claim for {worker_id}", flush=True)
            return 0
        pid = record.get("pid")
        if _pid_is_alive(pid):
            print(
                f"[recover] Refusing to release active worker {worker_id} pid={pid}",
                file=sys.stderr,
                flush=True,
            )
            return 2
        queue.setdefault("in_progress", {}).pop(worker_id, None)
        now = _utc_now().isoformat().replace("+00:00", "Z")
        history = dict(record)
        history.update({
            "history_status": "abandoned_orphan",
            "recovered_at": now,
            "recovery_reason": reason,
        })
        queue.setdefault("failure_history", []).append(history)
        if requeue:
            item = _pending_record(record, record.get("profile") or PROFILE_DEFAULT)
            item["last_error"] = reason
            item["recovered_at"] = now
            queue.setdefault("pending", []).append(item)
        else:
            failure = _failure_record(
                record,
                record.get("profile") or PROFILE_DEFAULT,
                reason,
                int(record.get("attempts", 0) or 0),
            )
            failure["recovered_at"] = now
            queue.setdefault("failed", []).append(failure)
        save_queue(queue)
        print(
            f"[recover] Released orphaned worker {worker_id}; requeued={requeue}",
            flush=True,
        )
        return 0
    finally:
        _release_lock(fd)


def do_retry_poisoned(notebook_ids=None, synth_backend=None,
                      reason="explicit poisoned retry",
                      allow_degraded_fallback=False,
                      force_resynthesis=True,
                      timeout_s=None,
                      synth_context_budget=None,
                      synth_checkpoint_dir=None):
    """Reopen exact poisoned items while preserving their terminal history."""
    requested = {str(item).strip() for item in (notebook_ids or []) if str(item).strip()}
    if synth_backend not in {None, "mmx", "dgemma", "deterministic"}:
        raise ValueError(f"unsupported synthesis backend: {synth_backend}")
    if timeout_s is not None:
        timeout_s = float(timeout_s)
        if timeout_s <= 0:
            raise ValueError("timeout_s must be > 0")
    if synth_context_budget is not None:
        synth_context_budget = int(synth_context_budget)
        if synth_context_budget <= 0:
            raise ValueError("synth_context_budget must be > 0")
    checkpoint_dir = Path(synth_checkpoint_dir).resolve() if synth_checkpoint_dir else None
    fd = _acquire_lock()
    try:
        queue = load_queue()
        poisoned = queue.get("poisoned", [])
        selected = [
            item for item in poisoned
            if not requested or str(item.get("nb_id", "")).strip() in requested
        ]
        if requested:
            found = {str(item.get("nb_id", "")).strip() for item in selected}
            missing = sorted(requested - found)
            if missing:
                raise RuntimeError("requested poisoned notebook IDs not found: " + ", ".join(missing))
        if not selected:
            print("[retry-poisoned] No matching poisoned items", flush=True)
            return 0

        invalid_profile_items = [
            item for item in selected
            if not item.get("nb_id")
            or str(item.get("profile") or "").strip() not in PROFILE_META
        ]
        if invalid_profile_items:
            ids = ", ".join(
                str(item.get("nb_id") or "<missing-id>")[:80]
                for item in invalid_profile_items
            )
            print(
                "[retry-poisoned] Refusing to reopen items without an exact "
                f"canonical account profile: {ids}. No queue state was changed.",
                file=sys.stderr,
                flush=True,
            )
            return 2

        history = queue.setdefault("poisoned_history", [])
        selected_ids = {str(item.get("nb_id", "")).strip() for item in selected}
        now = _utc_now().isoformat().replace("+00:00", "Z")
        reopened = 0
        for item in selected:
            nb_id = str(item.get("nb_id", "")).strip()
            profile = str(item["profile"]).strip()
            if not nb_id or _has_pending(queue, nb_id, profile):
                continue
            retry_item = _pending_record(item, profile)
            retry_item["attempts"] = int(item.get("attempts", 0) or 0)
            retry_item["last_error"] = item.get("error", "")
            retry_item["retry_reason"] = reason
            retry_item["reopened_at"] = now
            if synth_backend:
                retry_item["retry_backend"] = synth_backend
            if allow_degraded_fallback:
                retry_item["allow_degraded_fallback"] = True
            if force_resynthesis:
                retry_item["force_resynthesis"] = True
            if timeout_s is not None:
                retry_item["timeout_s"] = timeout_s
            if synth_context_budget is not None:
                retry_item["synth_context_budget"] = synth_context_budget
            if checkpoint_dir is not None:
                retry_item["synth_checkpoint_path"] = str(
                    checkpoint_dir / f"{profile}-{nb_id}.stage-c.json"
                )
            queue.setdefault("pending", []).append(retry_item)
            history_record = dict(item)
            history_record.update({
                "history_status": "reopened",
                "reopened_at": now,
                "reopen_reason": reason,
                "retry_backend": synth_backend,
                "allow_degraded_fallback": bool(allow_degraded_fallback),
                "force_resynthesis": bool(force_resynthesis),
                "timeout_s": timeout_s,
                "synth_context_budget": synth_context_budget,
            })
            if checkpoint_dir is not None:
                history_record["synth_checkpoint_path"] = retry_item["synth_checkpoint_path"]
            history.append(history_record)
            reopened += 1

        queue["poisoned"] = [
            item for item in poisoned
            if str(item.get("nb_id", "")).strip() not in selected_ids
        ]
        save_queue(queue)
        print(
            f"[retry-poisoned] Reopened {reopened} poisoned item(s); "
            f"backend={synth_backend or 'default'}; history preserved",
            flush=True,
        )
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
    g.add_argument("--retry-deferred", action="store_true")
    g.add_argument("--retry-poisoned", action="store_true")
    g.add_argument("--reconcile", action="store_true")
    g.add_argument("--recover-worker", action="store_true")
    ap.add_argument("--profile", "--account-profile", dest="profile", default=PROFILE_DEFAULT,
                    help="Single profile (default: a.hominidae). Use --all-profiles to enqueue from all.")
    ap.add_argument("--all-profiles", action="store_true",
                    help="Enqueue from all configured profiles (a.hominidae + troup.hominidae + brsthomson)")
    ap.add_argument("--worker-id", default=None)
    ap.add_argument("--requeue-orphan", action="store_true",
                    help="requeue a recovered dead-worker claim instead of recording it as failed")
    ap.add_argument("--min-sources", type=int, default=MIN_SOURCES)
    ap.add_argument("--workers", type=int, default=None,
                    help="total queue worker capacity (per-account limits still apply)")
    ap.add_argument("--notebook-id", action="append", default=None,
                    help="exact notebook ID; repeat for multiple IDs (retry-poisoned only)")
    ap.add_argument("--synth-backend", choices=["mmx", "dgemma", "deterministic"], default=None,
                    help="synthesis backend for a reopened poisoned item")
    ap.add_argument("--retry-reason", default="explicit poisoned retry",
                    help="audit reason recorded when reopening poisoned items")
    ap.add_argument("--timeout-s", type=float, default=None,
                    help="per-item sync deadline for a reopened poisoned item")
    ap.add_argument("--synth-context-budget", type=int, default=None,
                    help="synthesis map-reduce threshold in characters")
    ap.add_argument("--synth-checkpoint-dir", type=Path,
                    help="durable per-notebook Stage-C checkpoint directory")
    ap.add_argument("--max-attempts", type=int, default=1,
                    help="maximum worker attempts for a deferred semantic retry")
    ap.add_argument("--allow-degraded-fallback", action="store_true",
                    help="allow exact reopened items to promote citation-backed excerpt pages")
    ap.add_argument("--no-force-resynthesis", action="store_true",
                    help="do not bypass the unchanged-source gate when reopening poisoned items")
    args = ap.parse_args()
    if args.enqueue:
        profiles = list(PROFILE_META.keys()) if args.all_profiles else [args.profile]
        return do_enqueue(profiles, args.min_sources, args.workers)
    elif args.worker: do_worker(args.worker_id or f"w{int(time.time())%10000}", args.profile)
    elif args.status: do_status()
    elif args.retry_failed: return do_retry_failed()
    elif args.recover_worker:
        return do_recover_worker(args.worker_id, requeue=args.requeue_orphan)
    elif args.retry_deferred:
        return do_retry_deferred(
            args.notebook_id,
            args.synth_backend or "mmx",
            args.retry_reason,
            args.timeout_s,
            args.max_attempts,
            args.synth_context_budget,
        )
    elif args.retry_poisoned:
        return do_retry_poisoned(
            args.notebook_id,
            args.synth_backend,
            args.retry_reason,
            args.allow_degraded_fallback,
            not args.no_force_resynthesis,
            args.timeout_s,
            args.synth_context_budget,
            args.synth_checkpoint_dir,
        )
    elif args.reconcile: return do_reconcile()
    return 0

if __name__ == "__main__":
    sys.exit(main() if callable(main) else 0)
