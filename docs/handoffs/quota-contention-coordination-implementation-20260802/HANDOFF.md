---
thread_id: quota-contention-coordination-20260802
parent_handoff_path: docs/handoffs/auto-model-switch-on-rate-limit-20260728/HANDOFF.md
current_session_id: 019fc36f-b586-7900-be4d-b077920e8a6e
produced_at: 2026-08-02T00:00:00Z
status: open
handoff_type: implementation
assigned_to: grok
---

# Quota contention coordination implementation

## Objective

Build the proactive rate-limit coordination layer identified by the /www research.
The wiki concept at `P:/.data/wiki/concepts/model-quota-contention-coordination-fleet-rate-limiting.md`
contains the full 5-tier architecture. This handoff covers implementing Tier 1
(shared quota ledger) as the highest-ROI starting point.

## Status

OPEN — research complete, implementation not started.

## Context

- **Research:** `/www` run produced 15 sources, 4/4 subagents, disconfirmation pass.
  Key finding: rate limits are throughput-based (RPM/TPM), not concurrency-based.
  The coordinator must track token consumption, not just availability flags.
- **Wiki concept:** Committed at `3176cbc`, updated at `3ff0acc`.
- **Prior work:** `auto-model-switch-on-rate-limit-20260728` handoff covers the
  reactive failover system (fleet_quota.py, pick_model.py, spawn gate). This
  handoff adds the **proactive coordination layer** that prior work assumed would
  eventually exist.
- **Existing infrastructure:** `fleet_quota.py` (dashboard), `pick_model.py`
  (model picker with quota awareness), `PreToolUse_spawn_model_gate.py` (deny-and-redirect).

## Task packets

### QCC-01 — Shared quota ledger (SQLite WAL)

- **goal:** Create `P:/.data/fleet/quota-state.db` with a schema tracking
  per-provider, per-window quota consumption. Each session consults it before
  dispatching and updates it after each API call.
- **schema:** `provider TEXT, window_start TEXT, window_type TEXT (5h/daily/weekly),
  tokens_consumed INTEGER, requests_made INTEGER, last_updated TEXT,
  holder_session TEXT, ttl_expires TEXT`
- **acceptance:**
  1. SQLite WAL file created at `P:/.data/fleet/quota-state.db`
  2. `query_quota(provider, window_type)` returns current consumption
  3. `record_usage(provider, tokens, requests)` atomically updates the ledger
  4. Stale entries (TTL > 120s) auto-expired by background sweep
- **verification:** Unit test with 10 concurrent writers; verify no corruption
- **falsifier:** SQLite WAL corrupts under concurrent access from 10 processes

### QCC-02 — Wire pick_model.py to read the ledger

- **goal:** `pick_model.py --json --lane <lane>` consults the quota ledger before
  returning a model, filtering out providers whose consumption indicates imminent
  rate-limit risk.
- **acceptance:**
  1. `pick_model.py` reads `quota-state.db` before returning
  2. Models whose provider shows >80% quota consumption are deprioritized
  3. Disclosure: "consulted quota-state.db (age: Ns)"
- **verification:** Mock ledger with high consumption; verify model is skipped

### QCC-03 — Watchdog sweep process

- **goal:** Background Python process that sweeps stale ledger entries every 30s
  and can be launched by `cc-ccr.ps1`.
- **acceptance:**
  1. Process runs every 30s, removes entries with `ttl_expires < now()`
  2. Restarts if killed (via cc-ccr supervisor or Windows scheduled task)
  3. Progress-based liveness: logs "swept N entries" every cycle

## Read-first list

1. `P:/.data/wiki/concepts/model-quota-contention-coordination-fleet-rate-limiting.md`
2. `P:/docs/handoffs/auto-model-switch-on-rate-limit-20260728/HANDOFF.md`
3. `P:/.data/wiki/concepts/execution-path-based-model-routing-grok-build.md`
4. `~/.grok/skills/model-quota/scripts/pick_model.py`

## Dependencies

- **Requires:** SQLite with WAL mode (standard Python `sqlite3` module)
- **Blocks:** QCC-02 depends on QCC-01; QCC-03 depends on QCC-01

## Resumption protocol

1. Read this handoff + the wiki concept
2. Start with QCC-01 (shared quota ledger)
3. Verify SQLite WAL works under concurrent access before proceeding
4. Wire pick_model.py (QCC-02) after ledger is stable
5. Add watchdog (QCC-03) last

## Falsifier

This handoff is obsolete if:
- Grok Build adds `updatedInput` to PreToolUse hooks (enables seamless model injection)
- The serde bug is fixed (removes need for execution-path selection)
- Provider rate limits become transparent and queryable via API
