---
thread_id: fleet-database-migration-20260813
title: "Fleet model registry migration: static JSON → SQLite + git-versioned config"
created: 2026-08-13T22:47:00Z
session: 019fee3d-50cb-7553-83c6-558c06919132
status: OPEN
last_updated_at: 2026-08-13T22:47:00Z
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

## Implementation phases (Decision 6 = incremental)

### Phase 1: evidence_cache → SQLite model_evidence table

**Scope:** Move the evidence cache from JSON to a SQLite table. This is
the safest first step because `evidence_cache.json` doesn't exist in
production yet — no existing consumers to break.

**Files to modify:**
- `evidence_accumulator.py` — write to `model_evidence` table instead of `evidence_cache.json`
- `model_router.py` — `_evidence_for()` and related accessors read from SQLite table instead of dict
- `pick_model.py` — `load_evidence_cache()` loads from SQLite instead of JSON
- New: `migrate_evidence_to_sqlite.py` — one-time migration script

**Acceptance criteria:**
- `evidence_accumulator.py --compute` writes to `model_evidence` table
- `pick_model.py` reads evidence from SQLite table
- All existing tests pass (model-quota suite, 425+ tests)
- No `evidence_cache.json` file is created or read after migration

### Phase 2: quarantine.json → SQLite quarantine table

**Scope:** Move circuit-breaker state to SQLite.

**Files to modify:**
- `circuit_breaker.py` — read/write quarantine records from SQLite
- `model_router.py` — `health_gate()` reads from SQLite
- `pick_model.py` — `load_quarantine_records()` loads from SQLite
- serde_broken / spawn_broken arrays → quarantine table entries

**Acceptance criteria:**
- No `quarantine.json` file is created or read
- Circuit breaker quarantine/expiry works identically
- All existing tests pass

### Phase 3: fleet-models.json split

**Scope:** Split fleet-models.json into fleet-config.json (operator) +
SQLite model_metadata table (automation).

**Files to modify:**
- `fleet-config.json` — new file, extracted from fleet-models.json operator fields
- `model_metadata` table — populated from fleet-models.json automation fields
- `pick_model.py` — `load_registry()` reads from both sources, joins in memory
- `registry_schema.py` — updated for split schema
- `promote_models.py` — writes to model_metadata table instead of JSON
- `migrate_registry.py` — one-time migration from JSON to split stores
- All test fixtures that reference fleet-models.json

**Acceptance criteria:**
- No `fleet-models.json` file exists
- Operator edits `fleet-config.json` (git-versioned) for capabilities/policy
- Automation writes lifecycle/promotion to `model_metadata` table
- Lane derivation from capabilities works (no stored lanes)
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
