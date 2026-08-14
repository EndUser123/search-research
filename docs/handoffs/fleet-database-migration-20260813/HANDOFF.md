---
thread_id: fleet-database-migration-20260813
title: "Fleet model registry migration: static JSON → SQLite + git-versioned config"
created: 2026-08-13T22:47:00Z
session: 019fee3d-50cb-7553-83c6-558c06919132
status: OPEN
last_updated_at: 2026-08-13T23:15:00Z
---

# Handoff — Fleet model registry migration

## Objective

Migrate the fleet model selection system from a monolithic static JSON file
(`fleet-models.json`) to a clean separation of operator-authored config
(git-versioned JSON) and automation-derived state (SQLite tables). Eliminate
the drift, corruption, and maintenance problems caused by mixing operator
config and automation state in one writable file.

## Why

11 concrete incidents in 12 days (2026-08-01 through 2026-08-13) where
`fleet-models.json` caused drift, corruption, or maintenance overhead.
Transcript evidence search found zero cases where the mixed-JSON approach
worked well. See evidence table below.

Industry validation: Portkey (control plane/data plane split), LiteLLM
(Postgres for config + Redis for runtime state), MLflow/Vertex/SageMaker
(immutable version + mutable aliases/approval state) all separate operator
config from automation-derived state. Our approach matches the dominant
pattern.

## Evidence (11 incidents, 12 days)

| # | Date | Incident |
|---|------|----------|
| 1 | Aug 1 | Concurrent session wiped `serde_broken` by testing wrong transport |
| 2 | Aug 2 | Schema version collision (design assumed v2, file was v3) |
| 3 | Aug 1 | Wiki pool contracts drifted from registry changes |
| 4 | Aug 1 | All 10 `serde_broken` entries were false positives |
| 5 | Aug 2 | Picker returned stale "spawn OK" notes; health had drifted |
| 6 | Aug 2 | `parallel_safe_count` caused production 429s |
| 7 | Aug 4 | Concurrent v4 migration forced backward-compat hacks |
| 8 | Aug 5/13 | `tool_grounded_spawn_broken` over-blocked from all lanes |
| 9 | Aug 3/9 | `dispatch_latency` data stale/incomplete (2 of 79 models) |
| 10 | Aug 9 | Dead/paywalled models still recommended (lifecycle not updated) |
| 11 | Aug 6 | `fleet-models.json` flagged as uncommitted shared state |

## Architecture (locked decisions)

### File inventory after migration

**One database, two config files:**

| Store | Location | Who writes | Contents |
|-------|----------|------------|----------|
| `usage.db` | `P:/.artifacts/model-telemetry/usage.db` (exists) | Automation only | 5 tables: `usage`, `model_evidence`, `model_metadata`, `quarantine`, `threshold_policy` |
| `config.toml` | `~/.grok/config.toml` (exists) | Operator | Connection details: `api_key`, `base_url`, `model`, `context_window` |
| `fleet-config.json` | `~/.grok/skills/model-quota/scripts/fleet-config.json` (new) | Operator | Fleet metadata: `capabilities`, `policy`, `transport`, `dispatch_paths`, `provider`, `orchestrator`, `operator_override` |

**Ownership invariant:** no file is ever written by both operator and
automation. Operator writes JSON; automation writes SQLite.

### Files eliminated

| File | Fate |
|------|------|
| `fleet-models.json` | Split: operator fields → `fleet-config.json`, automation fields → SQLite |
| `evidence_cache.json` | Becomes `model_evidence` table |
| `quarantine.json` | Becomes `quarantine` table |

### SQLite schema

```sql
-- Layer 1: Raw events (already exists, 14,840 rows, append-only)
-- usage table — unchanged

-- Layer 2: Materialized evidence (Phase 1)
CREATE TABLE IF NOT EXISTS model_evidence (
    evidence_key TEXT PRIMARY KEY,   -- "provider|model|invocation|orchestrator"
    provider TEXT NOT NULL,
    model TEXT NOT NULL,
    invocation_method TEXT NOT NULL,
    orchestrator TEXT NOT NULL,
    quality_avg REAL,
    quality_min REAL,
    quality_max REAL,
    success_rate_overall REAL,
    latency_p50_ms REAL,
    latency_p90_ms REAL,
    sample_count_raw INTEGER,
    sample_count_effective REAL,
    last_updated TEXT,
    cohort_tag TEXT,
    computed_at TEXT NOT NULL
);

-- Layer 3: Model metadata (Phase 3)
CREATE TABLE IF NOT EXISTS model_metadata (
    id TEXT PRIMARY KEY,             -- slug
    model TEXT NOT NULL,
    provider TEXT NOT NULL,
    orchestrator TEXT NOT NULL DEFAULT 'grok',
    lifecycle TEXT DEFAULT 'candidate',  -- candidate | active | suspected_eol | retired
    policy TEXT DEFAULT 'use_freely',
    transport TEXT,
    notes TEXT,
    operator_override_json TEXT,
    updated_at TEXT NOT NULL
);

-- Layer 3: Quarantine (Phase 2)
CREATE TABLE IF NOT EXISTS quarantine (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT NOT NULL,
    level TEXT NOT NULL,             -- transport | model | provider
    provider TEXT,
    transport TEXT,
    reason TEXT,
    quarantined_at TEXT NOT NULL,
    cooldown_seconds INTEGER,
    reprobe_after TEXT NOT NULL
);

-- Layer 3: Threshold policy (Phase 3)
CREATE TABLE IF NOT EXISTS threshold_policy (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### Lane derivation (Decision 2 = Option A)

Lanes are derived from capabilities at query time, not stored:

```python
def derive_lanes(capabilities: dict, override: dict | None) -> set[str]:
    lanes = set()
    if capabilities.get("tool_calling") or capabilities.get("structured_output"):
        lanes.add("coding")
    if capabilities.get("reasoning"):
        lanes.add("reasoning")
    if override:
        lanes -= set(override.get("exclude_lanes", []))
        lanes |= set(override.get("force_lanes", []))
    return lanes
```

### serde_broken (Decision 3 = Option B)

Merged into quarantine table. No special-case arrays. Circuit breaker
writes serde failures with `reason='serde_broken'` and longer cooldowns.

### EOL detection (Decision 4 follow-up)

Evidence staleness signal in evidence_accumulator.py refresh step:

```sql
UPDATE model_metadata SET lifecycle = 'suspected_eol'
WHERE id IN (
  SELECT model FROM usage
  WHERE success = 0 AND timestamp > datetime('now', '-7 days')
  AND model NOT IN (
    SELECT model FROM usage
    WHERE success = 1 AND timestamp > datetime('now', '-7 days')
  )
  GROUP BY model
);
```

Lifecycle gate excludes `suspected_eol` (same as `retired`). Next
discovery probe confirms or clears.

## Stale JSONL consumers (found 2026-08-13, sibling session)

Three consumers read `usage.jsonl` (23 KB, last modified 2026-07-24) instead of
`usage.db` (9.3 MB, updated continuously). The JSONL file is stale — it was
superseded by the SQLite database when `telemetry.py` switched to `log_call()`
writing to `usage.db`. These scripts never got migrated:

| File | Line | What it reads | Impact |
|------|------|---------------|--------|
| `fleet_quota.py` | 820-827 | Cohere monthly call count from JSONL | Cohere exhaustion detection broken — reads 20-day-stale data |
| `pool_health.py` | 35 | Pool health metrics from JSONL | Pool health reports stale |
| `snapshot_manager.py` | 49 | `EVIDENCE_FILE` constant pointing at JSONL | Stale constant only — surrounding code says "NEVER touched", non-impactful |

**Fix:** Migrate these consumers to read from `usage.db` via `fleet_db.py` query
functions. Each is a small surgical fix (swap file read for SQL query).

**Prevention:** The `fleet_db.py` design principle (single data access layer)
prevents future stale consumers. Once these three are migrated, no script
should read `usage.jsonl` directly — add a grep check to the test suite.

## Consumer audit requirement (applies to all phases)

Every phase must grep for all readers of the file being killed before removing
it. The stale-JSONL consumers above prove that we don't always know every
consumer — the sibling session found two that the primary session missed.

**Protocol per phase:**
1. Grep for all references to the file being killed (both filename and path)
2. Migrate each consumer to the new data source via `fleet_db.py`
3. Add a test that asserts the old file is never read
4. Remove the old file only after all consumers are migrated
5. Run the full test suite

This follows the removal protocol from AGENTS.md (grep imports → grep references →
glob files → check tests → check data → delete → verify zero results).

## Unused data: discovery probes (EOL signal)

1,254 discovery probe records exist in `usage.db` (caller:
`model-benchmark --discover`, 511 successes / 40.7% success rate). Nothing
reads them for lifecycle decisions. This is exactly the EOL signal the
model-selection design needs — models that stop responding to trivial probes
are EOL or degraded.

**Wiring:** The EOL detector (Decision 4 follow-up) should be a `fleet_db.py`
query function that reads discovery probe data and flags models with <50%
probe success in the last 7 days. Output feeds `promote_models.py` to set
`lifecycle = 'suspected_eol'` in the `model_metadata` table (Phase 3).

This is deferred to Phase 3 (when `model_metadata` table exists) — no point
building the EOL signal before the lifecycle table it writes to.

## Implementation phases (Decision 6 = incremental)

### Phase 1: evidence_cache → SQLite model_evidence table [SHIPPED]

**Status:** Complete (commit `c2c531b`, 2026-08-13).

**What shipped:**
- New module `fleet_db.py`: `create_evidence_table()`, `upsert_evidence()`, `load_evidence_from_db()` — returns same dict shape as JSON cache
- `evidence_accumulator.py`: dual-writes to SQLite + JSON (transition period)
- `pick_model.py`: reads SQLite first, falls back to JSON if table empty
- 927 evidence rows computed from 14,840 telemetry records
- 425/425 model-quota tests pass, 133/133 ship-py tests pass

**Design principle adopted:** `fleet_db.py` is the single data access layer for
all fleet telemetry queries. No script should read `usage.db` directly — all
queries go through `fleet_db.py` functions. This prevents the stale-consumer
pattern (see "Stale JSONL consumers" below). When the data source changes,
it's a one-file change, not a multi-file audit. Phase 2+ will add query
functions for quarantine, telemetry counts, discovery probe results, etc.

### Phase 2: quarantine.json → SQLite quarantine table

**Scope:** Move circuit-breaker state to SQLite. Add quarantine query
functions to `fleet_db.py` so all consumers go through the data access layer.

**Files to modify:**
- `fleet_db.py` — add `create_quarantine_table()`, `upsert_quarantine()`, `load_quarantine_from_db()`, `is_quarantined()`
- `circuit_breaker.py` — read/write quarantine records via `fleet_db.py` instead of JSON
- `model_router.py` — `health_gate()` reads from `fleet_db.py`
- `pick_model.py` — `load_quarantine_records()` loads via `fleet_db.py`
- serde_broken / spawn_broken arrays → quarantine table entries (unified circuit-breaker mechanism)
- Consumer audit: grep for all readers of `quarantine.json` before removing it

**Acceptance criteria:**
- No `quarantine.json` file is created or read
- `fleet_db.py` is the only module that touches the quarantine table directly
- Circuit breaker quarantine/expiry works identically
- All existing tests pass

### Phase 3: fleet-models.json split + stale consumer migration + EOL wiring

**Scope:** Split fleet-models.json into fleet-config.json (operator) +
SQLite model_metadata table (automation). Migrate stale JSONL consumers.
Wire EOL detector from discovery probe data.

**Files to modify:**
- `fleet-config.json` — new file, extracted from fleet-models.json operator fields
- `model_metadata` table — populated from fleet-models.json automation fields
- `fleet_db.py` — add `create_metadata_table()`, `load_metadata()`, `update_lifecycle()`, `count_calls_by_provider()`, `get_discovery_probe_success()`, `detect_suspected_eol()`
- `pick_model.py` — `load_registry()` reads from both sources, joins in memory
- `registry_schema.py` — updated for split schema
- `promote_models.py` — writes to model_metadata table via `fleet_db.py`
- `fleet_quota.py:820-827` — Cohere counter reads from `fleet_db.py` (stale JSONL fix)
- `pool_health.py:35` — pool health reads from `fleet_db.py` (stale JSONL fix)
- `migrate_registry.py` — one-time migration from JSON to split stores
- Consumer audit: grep for ALL readers of `fleet-models.json` and `usage.jsonl` before removing either file

**Acceptance criteria:**
- No `fleet-models.json` file exists
- No script reads `usage.jsonl` directly (all go through `fleet_db.py`)
- Operator edits `fleet-config.json` (git-versioned) for capabilities/policy
- Automation writes lifecycle/promotion to `model_metadata` table via `fleet_db.py`
- Lane derivation from capabilities works (no stored lanes)
- EOL detector flags models with <50% discovery probe success in 7-day window
- Cohere quota counter returns correct count from SQLite
- Pool health reports use current data from SQLite
- All existing tests pass

### Phase 4: threshold_policy → SQLite

**Scope:** Move threshold policy to SQLite key-value table.

**Files to modify:**
- `registry_schema.py` — ThresholdPolicy reads from SQLite
- `fleet-config.json` — threshold_policy section removed
- All tests that construct ThresholdPolicy

## Operator decisions locked

1. Operator metadata in git-versioned JSON (`fleet-config.json`), not SQLite
2. Lane derivation from capabilities (Option A), with operator override escape hatch
3. serde_broken merged into quarantine table (Option B)
4. Evidence refreshes after benchmark batches (Option A) + EOL staleness signal
5. Operator edits JSON directly (Option A), CLI for runtime overrides
6. Incremental implementation, 3-4 phases, each independently shippable

## Provenance

- Transcript evidence search: subagent `019ffe84-872d`, 37 tool calls, 11 incidents found
- Industry research: subagent `019ffe84-872f`, 20 tool calls, 7 web searches, 10 sources
- Architecture validation: `/tp` two-lens critique, subagent `019ffe76-de4b`
- Session: `019fee3d-50cb-7553-83c6-558c06919132`

## Related wiki concepts

- `model-pool-selection-policy-speed-quota-diversity.md` — selection policy
- `model-lanes-vs-roles.md` — original 2-lane design (now the basis again)
- `model-pool-not-chain.md` — pool philosophy
- `context-firewall-architecture.md` — cross-family exclusion
- `serde-broken-false-positive-sweep-20260801.md` — incident #4
- `multi-terminal-shared-state-contamination-transport-mismatch.md` — incident #1
- `pick-model-stale-spawn-notes-failure-pattern.md` — incident #5
