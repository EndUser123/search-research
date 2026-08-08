---
title: "File Locking for Atomic Replace Cache Pattern"
last_verified: 2026-08-02
host: grok
---

# File Locking for Atomic Replace Cache Pattern

## Problem

When multiple processes do read-modify-write on a shared JSON cache file using
the atomic `tmp.replace()` pattern, a TOCTOU (time-of-check-time-of-use) race
occurs: two callers each read the cache, each add their key, each write back —
one update is silently lost.

The per-PID tmp suffix prevents write collision (two processes don't overwrite
each other's tmp file), but does NOT prevent the logical read-modify-write race.

## Solution

Use an advisory file lock on a **separate `.lock` file** (not the cache file
itself) to serialize the read-modify-write section.

### Why a separate lock file?

The cache is written via `tmp.replace()` (atomic rename), which changes the
inode. An `flock` on the cache file would break after the replace because the
locked inode is no longer the live file. The `.lock` file is never replaced,
so the lock survives across cache writes.

### Cross-platform implementation

```python
@contextmanager
def _cache_file_lock(lock_path):
    fd = os.open(str(lock_path), os.O_CREAT | os.O_RDWR)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        if os.name == "nt":
            import msvcrt
            try:
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            except OSError:
                pass
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
```

## Usage

```python
with _cache_file_lock(cache_path.with_suffix(".lock")):
    cache = json.loads(cache_path.read_text())
    cache[provider_id] = {"pct": pct, "updated": time.time()}
    tmp = cache_path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(cache))
    tmp.replace(cache_path)
```

## When to use

- Any workspace script that does read-modify-write on a shared JSON cache
- When multiple hooks or sessions may call the update function concurrently
- When the cache uses atomic `tmp.replace()` (the lock-on-cache-file approach
  breaks because replace changes the inode)

## When NOT to use

- Single-writer scripts (no concurrency risk)
- Append-only JSONL designs (each update is one line, no read-modify-write)

## Reference

- Implemented in `fleet_quota.py` `update_provider_in_cache()` (commit d3f7cfb, 2026-08-02)
- The TOCTOU race was found by `/trace` manual code path verification
- Alternative: JSONL append-only design where each update is one line and
  aggregation happens on read (avoids locking entirely but changes the reader)
