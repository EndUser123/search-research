---
thread_id: sqlite-telemetry-2026-07-24
parent_handoff_path: none
current_session_id: 019f91d3-2741-7f83-af68-211796180474
current_terminal_id: console_b7ba7bf3-2403-437a-b44a-c5c9
produced_at: 2026-07-24T19:30:00Z
status: open
handoff_type: implementation
accurate_as_of_head: non-git-session
---

# SQLite telemetry backend

## Objective

Replace the JSONL append-only telemetry store with a SQLite WAL-mode database to eliminate concurrent-write corruption, unbounded growth, and full-scan analysis cost.

## Status

OPEN — design identified, not started.

## Producing context

- Date: 2026-07-24
- Session: 019f91d3-2741-7f83-af68-211796180474
- Origin: red-team finding ST-1 (no file locking), ST-6 (unbounded growth), ST-9 (silent read corruption)

## Read-first list

1. `C:/Users/brsth/.grok/skills/model-benchmark/scripts/telemetry.py` — current JSONL implementation to replace
2. `C:/Users/brsth/.grok/skills/model-benchmark/scripts/analyze.py` — current full-scan analysis to rewrite as SQL
3. `P:/docs/handoffs/model-telemetry-integration/HANDOFF.md` — the integration plan (this SQLite change should land BEFORE skill integration, so integration targets the new backend)
4. `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md` — why telemetry exists (dynamic quota thresholds need it)

## Verified facts

- [FACT] `telemetry.py` opens `usage.jsonl` with mode `'a'` and writes `json.dumps(record) + "\n"` — no locking (`telemetry.py:65-73`)
- [FACT] `analyze.py:detect_gaps` and `print_coverage_matrix` re-read the entire file on every call (`benchmark.py:442-498, 501-552`)
- [FACT] Current file size: 9 records, ~3KB. Projected growth: 50-500 records/day after skill integration
- [FACT] Python stdlib includes `sqlite3` — zero new dependencies
- [FACT] SQLite WAL mode supports concurrent reads + single writer with no application-level locking

## Current state

- JSONL telemetry works for single-writer (verified, 9 records accumulated)
- 7 skills identified as integration targets (handoff written)
- The JSONL → SQLite migration has not started

## Task packets

### ST-DB-01: Create SQLite backend

- **Goal:** Replace `telemetry.py`'s JSONL with SQLite WAL database at `P:/.artifacts/model-telemetry/usage.db`
- **In scope:** `telemetry.py` (rewrite log_call/log_spawn), schema design, WAL pragma
- **Out of scope:** analyze.py rewrite (ST-DB-02), benchmark.py/extract.py consumer updates (ST-DB-03)
- **Files:** `C:/Users/brsth/.grok/skills/model-benchmark/scripts/telemetry.py`
- **Schema:**
  ```sql
  CREATE TABLE usage (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp TEXT NOT NULL,
      epoch REAL NOT NULL,
      model TEXT NOT NULL,
      provider TEXT,
      task_domain TEXT,
      latency_ms REAL,
      success INTEGER NOT NULL,
      caller TEXT,
      input_tokens INTEGER,
      output_tokens INTEGER,
      error_type TEXT,
      notes TEXT
  );
  CREATE INDEX idx_model_domain ON usage(model, task_domain);
  CREATE INDEX idx_timestamp ON usage(timestamp);
  ```
- **Acceptance:** `log_call()` writes to SQLite; concurrent writes from 2 terminals do not corrupt; `PRAGMA journal_mode=WAL` is set
- **Falsifier:** any write corruption under concurrent load; or any existing telemetry consumer (extract.py, benchmark.py) breaks
- **Verification:** LIVE_BEHAVIOR — run extract.py and benchmark.py simultaneously, verify both records land

### ST-DB-02: Rewrite analyze.py as SQL queries

- **Goal:** Replace full-file JSONL scan with SQL queries
- **In scope:** `analyze.py` — rewrite `load_records`, `report_model_stats`, `report_temporal`, `report_domains`, `detect_gaps`
- **Out of scope:** benchmark.py's `--gaps` mode (uses detect_gaps — update import only)
- **Files:** `C:/Users/brsth/.grok/skills/model-benchmark/scripts/analyze.py`
- **Acceptance:** `python analyze.py` produces the same output shape as before; queries use indexes (EXPLAIN QUERY PLAN shows no full scans)
- **Falsifier:** analysis output is empty or missing models that have data; or query time > 1s on 10K records

### ST-DB-03: Update consumers

- **Goal:** Update `benchmark.py` and `extract.py` to import from new telemetry module
- **In scope:** `benchmark.py` (log_call usage), `extract.py` (log_telemetry function)
- **Out of scope:** the 7-skill integration (that's the separate telemetry handoff)
- **Acceptance:** benchmark and extract both write to SQLite without errors

## Open decisions

- **Migration of existing JSONL data?** Import the 9 existing records into SQLite, or start fresh? Recommendation: import (trivial, preserves history).
- **JSONL export for debugging?** Keep a `--export-jsonl` flag on analyze.py for human-readable output? Recommendation: yes, cheap to maintain.

## Hard constraints

- SQLite file at `P:/.artifacts/model-telemetry/usage.db` (same directory as current JSONL)
- WAL mode mandatory (not DELETE or TRUNCATE journal)
- `sqlite3` stdlib only — no new dependencies
- Backward-compatible API: `log_call()` and `log_spawn()` keep the same signature

## Cross-reference couplings

- `extract.py` imports `from telemetry import log_call` — will keep working (same API)
- `benchmark.py` imports `from telemetry import log_call` — same
- `P:/docs/handoffs/model-telemetry-integration/HANDOFF.md` — the 7-skill integration should target the SQLite backend, not JSONL
- Red-team findings ST-1, ST-3, ST-6, ST-9, ST-10, PERF-003, PERF-012 — all resolved by this change

## Explicit non-goals

- Do NOT build a web dashboard or visualization layer
- Do NOT add authentication or multi-user support
- Do NOT implement retention policies (VACUUM schedule) — defer until file hits 100MB

## Resumption protocol

1. Read `telemetry.py` to understand current API
2. Create `usage.db` with schema + WAL pragma
3. Rewrite `log_call()` to INSERT into SQLite
4. Import existing 9 JSONL records
5. Test: run extract.py, verify record lands in SQLite

## Suggested next invocation

```
/go implement SQLite WAL telemetry backend per P:/docs/handoffs/sqlite-telemetry-backend/HANDOFF.md. Replace JSONL with sqlite3 stdlib. Tasks ST-DB-01 through ST-DB-03.
```

## Last user message (verbatim)

> "recap workstreams please."
> (prior: "start on the 5 immediate fixes now")
> (prior: "We need an optimal design. How do we get that?")

## Epistemic labels

- [FACT] All file paths and line numbers verified this session
- [FACT] SQLite WAL properties verified from Python docs
- [INFERENCE] 50-500 records/day projection based on fleet usage of ~170 calls/hour and assumed 30% telemetry coverage after integration
