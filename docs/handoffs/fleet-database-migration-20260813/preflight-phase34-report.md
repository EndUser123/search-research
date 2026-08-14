# Preflight packet — fleet migration Phases 3+4

Date: 2026-08-14 | Session: 019fee3d-50cb-7553-83c6-558c06919132
Audit: `P:\tmp\preflight-phase34.json` (decision: proceed_with_discovery, 0 marker conflicts)
Verdict: **needs_review** — do not start Phase 3 until the 3 blockers below are resolved.

## fleet-models.json consumer inventory (complete)

| Artifact | Classification | Role | In handoff Phase 3? |
|---|---|---|---|
| `model-quota/scripts/pick_model.py:56` | canonical reader | `load_registry()` | YES |
| `model-quota/scripts/registry_schema.py` | schema definition | FleetRegistry/CandidateRecord/ThresholdPolicy | YES |
| `model-quota/scripts/registry_writer.py:24` | canonical locked writer | atomic write/update | implied |
| `model-quota/scripts/promote_models.py:29` | lifecycle writer | candidate→active | YES |
| `model-quota/scripts/snapshot_manager.py:47` | snapshot/diff tool | registry + threshold_policy diffs | **NO — missing** |
| `model-quota/scripts/migrate_registry.py`, `migrate_to_v4.py` | historical migration | one-time v4→v5 | not listed (classify: historical, read-only) |
| `model-benchmark/scripts/benchmark.py:37` | reader | coverage print + slug defaults | **NO — missing** |
| `~/.grok/hooks/PreToolUse_spawn_model_gate.py:40` | hook reader | serde_broken set + lane fallbacks | **NO — missing** |
| `~/.grok/hooks/PostToolUseFailure_spawn_quota.py` | hook reader+writer | learned serde + **writes quarantine.json:560** | **NO — missing** |
| `packages/codex-external-delegation/src/model-selector.mjs:5` | cross-orchestrator reader | `DEFAULT_FLEET_REGISTRY` hardcoded path | **NO — constraint violation** |
| Tests: `test_pick_model_shadow`, `test_migration`, `test_snapshot_manager`, `test_pick_model_migration`, `test_registry_schema`, `test_benchmark_gate`, `test_promote_identity_diagnostics` | tests | fixtures/mock paths | partial |

## Blocker 1 — Codex selector constraint violation

`P:/.data/wiki/concepts/codex-pi-grok-schema-v5-registry-integration.md` (Decision section):
> "Use schema 5 as the only live registry contract. The Codex selector now requires `schema_version: 5` and `candidates`…"

Proposed change: Phase 3 eliminates fleet-models.json.
Conflict class: **violation** — `model-selector.mjs:5` hardcodes the file as DEFAULT_FLEET_REGISTRY; deleting it breaks Codex dispatch.
Resolution options: (a) migrate model-selector.mjs to the split stores in the same phase; (b) keep a generated fleet-models.json as a compat export built from fleet-config.json + model_metadata; (c) revise the wiki contract + selector together.

## Blocker 2 — hook consumers missing from Phase 3 scope

`PreToolUse_spawn_model_gate.py` reads the registry on EVERY spawn (serde_broken, spawn_broken, lane fallbacks). Multi-terminal isolation: every terminal's in-flight sessions hold this code — a format cutover without a dual-read transition breaks all concurrent sessions' spawn gates.
Resolution: hooks get the same SQLite-first/JSON-fallback dual-read as Phases 1–2, migrated before the file is removed.

## Blocker 3 — Phase 2 shipped with a write-side gap (defect D1)

`PostToolUseFailure_spawn_quota.py:587 write_quarantine_record()` still **writes quarantine.json**. Phase 2 changed only the read side (`pick_model.py` reads SQLite first, JSON only if table empty). The moment any SQLite quarantine row exists, hook-written JSON records become invisible (either-or read, not merge).
Fix: (1) make `load_quarantine_records()` MERGE both stores (union on candidate_id+level+reprobe_after, newest wins), and (2) migrate `write_quarantine_record()` to dual-write (SQLite `insert_quarantine` + legacy JSON) during transition.

## Constraint audit (other)

| Citing artifact | Constraint | Class | Note |
|---|---|---|---|
| Migration handoff | "No script reads usage.db directly — all via fleet_db.py" | **stress** | analyze.py, compare_models.py, model_comparison.py, pool_test.py read usage.db directly today. Scope the principle to selection-path code or migrate them too. |
| Migration handoff | Consumer-audit-before-delete protocol | ok | this preflight satisfies step 1; re-run at implementation start + pre-delete |
| AGENTS.md | Removal protocol (grep→migrate→verify→delete) | ok | verified greps above |
| codex-pi wiki | "Legacy benchmark write-back cannot mutate live v5 routing" | ok | Phase 4 keeps invariant if benchmark never writes threshold_policy table |

## Phase 4 scope check (blocked behind Phase 3)

threshold_policy consumers: `registry_schema.py` (ThresholdPolicy class + defaults), `circuit_breaker.py check_promotion` (thresholds), `benchmark_runner.py:812` (promotion threshold lookup), `promote_models.py:133` (constructs policy), `snapshot_manager.py:68` (TRACKED_POLICY_FIELDS + tp diffs), tests constructing ThresholdPolicy (test_model_router make_policy, test_benchmark_gate, scripts/test_pick_model.py). Clean — no unaccounted consumers, but snapshot_manager appears in BOTH phases and must not be migrated twice.

## Runtime/config receipt

- pick_model live path verified this session (`python ~/.grok/skills/model-quota/scripts/pick_model.py reasoning` → returns models + alternatives).
- Hooks in dispatch chain: PreToolUse_spawn_model_gate (active), PostToolUseFailure_spawn_quota (active writer).
- Worktrees: P:/ (main, HEAD ef24479), overnight-supervisor-20260808, dotgrok-baseline-main — none touch model-quota or codex-external-delegation paths. Dirty-tree noise is sibling-session state; no overlap with migration write scope.
