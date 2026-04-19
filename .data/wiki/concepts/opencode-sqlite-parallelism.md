---
type: concept
title: "OpenCode SQLite Concurrency: Why Sequential is the Safe Ceiling"
created: 2026-04-18
source: ~/Downloads/In claude code on windows 11, is this true____  Su.md
hash: 2318fdb7ca5995653d91ac9383810444acdc5f329b994e5b9317c86d83040058
tags:
  - opencode
  - sqlite
  - concurrency
  - python
  - windows
summary: "OpenCode uses SQLite for state — concurrent CLI processes hitting the same DB causes 'database is locked' errors. Sequential dispatch is the safe ceiling without profile sharding."
---

# OpenCode SQLite Concurrency

## The Problem

OpenCode uses a **local SQLite DB** in the user profile (e.g. `~/.local/.../opencode.db`).

Concurrent opencode CLIs hitting that DB trigger: `SQLiteError: locking protocol` / `database is locked`

## Why This Happens

- SQLite uses **file-level locking** — writes are exclusive
- Only one write transaction can own the lock at a time
- A second process that hits the DB while locked gets an immediate error, not a wait
- OpenCode manages its own DB connection internally — you can't control `busy_timeout` or WAL from outside

## What the Sequential Fix Actually Does

```python
for model in models:
    finding = await dispatch_single(target, model, output_dir)
    findings.append(finding)
```

- Only **one opencode process alive at a time** → true sequential dispatch
- No artificial delay — model N+1 starts the instant model N returns
- Throughput: N × single-model time instead of ~single-model time

**This is correct and safe.** The `for await` pattern is the right fix.

## Options to Get Closer to Parallelism

### Option 1 — Multiple OpenCode Profiles (recommended)

OpenCode supports `OPENCODE_CONFIG_DIR` env var → different config directories → **independent SQLite DB files**

```python
PROFILES = [r"C:\opencode_profiles\profile1", r"C:\opencode_profiles\profile2"]

async def dispatch_sharded(models, target, output_dir):
    tasks = []
    for i, model in enumerate(models):
        profile_dir = PROFILES[i % len(PROFILES)]
        tasks.append(run_opencode_with_profile(profile_dir, model, target, output_dir))
    return await asyncio.gather(*tasks)
```

Each profile has its own DB → **true parallelism across profiles**

### Option 2 — Raw API Calls (defeats purpose)

Replace opencode dispatch with direct Python async clients + `asyncio.gather` → full parallelism. But loses opencode's prompt construction, retry, logging, etc.

### Option 3 — Horizontal Sharding

Run opencode on multiple machines/WSL instances, each with its own home/DB. Effective but heavy.

## What OpenCode Actually Supports

- `OPENCODE_CONFIG_DIR` — custom config directory
- `OPENCODE_CONFIG` — custom config file
- `OPENCODE_CONFIG_CONTENT` — inline JSON config

No `--profile` flag. No documented concurrent session mode.

## Python 3.14+ Notes

No semantic changes to `await` behavior in 3.14. The asyncio introspection tools (`python -m asyncio ps`, `pstree`) are useful for debugging but don't unlock hidden parallelism.

## Bottom Line

| Approach | Parallelism | Effort |
|----------|-------------|-------|
| Sequential `for await` | None | Zero |
| Profile sharding | N profiles | Medium |
| Raw API dispatch | Full | High |
| Multi-machine | Full | Very high |

**Recommendation**: Start with sequential. Add profile sharding if throughput becomes a real bottleneck.

## Related

- [[wiki/concepts/pi-agent-harness]] — Pi avoids this problem entirely (in-process, not CLI+SQLite)
- [[wiki/concepts/opencode-windows-setup]] — OPENCODE_CONFIG_DIR setup on Windows 11
