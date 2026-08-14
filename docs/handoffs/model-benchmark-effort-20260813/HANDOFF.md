---
thread_id: 9b7e3a4f-2c1d-4e6a-8d5b-7a9c0f1e8b2c
parent_handoff_path: none
current_session_id: 019ffd06-0d7f-7f21-98fc-6117652ba7e3
parent_session: none
current_terminal_id: console_019ffd06
produced_at: 2026-08-13T23:30:00Z
last_updated_by: 019ffd06-0d7f-7f21-98fc-6117652ba7e3
last_updated_at: 2026-08-14T00:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: af73e5750398d9e47161f50c59495b1c06ec8055
---

# Handoff: Model-benchmark skill cleanup + telemetry wiring

## Authority split (locked 2026-08-14)

Two handoffs divide the model-benchmark / fleet domain:

| Handoff | Owns | Does NOT own |
|---|---|---|
| **`P:/docs/handoffs/fleet-database-migration-20260813/HANDOFF.md`** | Fleet infrastructure: SQLite migration, fleet-models.json elimination, stale-JSONL consumer migration, EOL detector, quarantine table, model_metadata table, dispatch-paths / serde_broken filter rewrite | `/model-benchmark` skill surface, telemetry wiring into skills, benchmark.py / benchmark_tiers.py / pool_test.py code |
| **This handoff** | `/model-benchmark` skill cleanup, telemetry wiring into 7 skills, Groq/SKILL.md fixes, GPT-5.6 bridge validation, code-exec benchmark expansion | Fleet registry storage, picker internals, serde_broken filter, dispatch_paths, fleet-models.json |

The migration handoff is **authoritative for fleet infrastructure**. This handoff is **authoritative for model-benchmark skill cleanup and telemetry wiring**. When the two touch the same file (e.g., `fleet_quota.py`), the migration handoff leads and this handoff sequences after.

## Objective

Ship the model-benchmark skill cleanup and telemetry wiring that is independent of the fleet-database migration: fix review findings on hooks/crawl code independent of fleet state, wire `log_spawn()`/`log_call()` into 7 dispatching skills, and clean up `/model-benchmark` skill internals (Groq TPM, provider map, SKILL.md staleness, missing tests, code-exec expansion, GPT-5.6 bridge validation).

**Scope bounds:** 14 task packets (MBE-05..10, MBE-14..19, MBE-21..22). 10 prior task packets were deferred to the migration handoff (see "Deferred items" below). Total remaining effort: ~7 hours across multiple sessions.

## Status

OPEN — 14 task packets, downsized from 22 after the fleet-database-migration-20260813 handoff absorbed the dispatch-paths, fleet-models.json, and stale-JSONL consumer work.

## Producing context

- Date: 2026-08-13 (created), 2026-08-14 (downsized)
- Session: `019ffd06-0d7f-7f21-98fc-6117652ba7e3`
- Terminal: `console_019ffd06`
- Host: Grok Build
- Producing context: operator asked for model-benchmark remaining work → consolidated into umbrella → operator directed consolidation cleanup (close superseded handoffs) → `/preflight investigate` revealed the `model_router.py:707` filter is load-bearing → operator surfaced `fleet-database-migration-20260813` handoff → operator directed option (b): downsize this umbrella; the migration handoff is authoritative for fleet infrastructure, this handoff is authoritative for skill cleanup and telemetry.

## Read-first list (ordered, with reasons)

1. `P:/docs/handoffs/fleet-database-migration-20260813/HANDOFF.md` — **read first** — the authoritative fleet-infrastructure workstream. Establishes which files are being eliminated (`fleet-models.json`, `usage.jsonl` consumers) and which are being added (`fleet_db.py`, `fleet-config.json`, `model_metadata` table).
2. `~/.grok/skills/model-benchmark/SKILL.md` — the canonical skill surface (5 capabilities: benchmark, quality, telemetry, analyze, discovery).
3. `P:/.artifacts/review/019fc95d-session-review/FINDINGS.md` — 14 verified findings; this handoff's MBE-05..07 cover Cluster B (uncertainty_gate) + Cluster D (crawl dead code). Cluster C (Cohere quota wiring, MBE-06) coordinates with the migration's Phase 3 `fleet_quota.py` changes.
4. `~/.grok/skills/model-benchmark/scripts/telemetry.py` — the `log_call()` / `log_spawn()` API this handoff wires into 7 skills.
5. `~/.grok/skills/model-benchmark/scripts/benchmark.py` — main benchmark engine; MBE-12 was deferred (multi-method quality benchmarking) but MBE-15 (provider map) and MBE-16 (SKILL.md:190) still apply.
6. `~/.grok/skills/model-benchmark/scripts/benchmark_tiers.py` — tier definitions; MBE-22 (code-exec expansion to 13 problems) lives here.
7. `~/.grok/skills/model-quota/scripts/fleet_db.py` — single data access layer introduced by Phase 1 of the migration; MBE-08..10 (telemetry wiring) should ensure `log_spawn()` writes flow into `usage.db` which `fleet_db.py` reads.

## Verified facts (with source paths)

- [FACT] `/model-benchmark` skill ships 5 capabilities: parallel benchmark, quality scoring, telemetry logging, analyze reports, multimodal tier (SKILL.md lines 18–55).
- [FACT] 14 `/review` findings at `P:/.artifacts/review/019fc95d-session-review/FINDINGS.md`, 3 root-cause clusters: Cluster B uncertainty_gate (3 findings), Cluster C Cohere quota wiring (5 findings), Cluster D crawl dead code (2 findings). Clusters B and D are independent of fleet infrastructure; Cluster C modifies `fleet_quota.py` which the migration also modifies.
- [FACT] 7 skills still need telemetry integration: `/check`, `/go`, `/review` (Priority 1); `/www`, `/web`, `/wiki`, `/preflight` (Priority 2); zero integration code shipped to any of them (verified by absence of `from telemetry import log_call` in those skill files).
- [FACT] `telemetry.py` writes to `P:/.artifacts/model-telemetry/usage.db` (9.3 MB, 14,840 rows, last updated 2026-08-13). The `fleet_db.py` data access layer (migration Phase 1) reads from this same database. Telemetry wiring is therefore complementary to the migration — more skill dispatches = more data for `fleet_db.py` queries.
- [FACT] `~/.grok/skills/model-benchmark/SKILL.md:190` prompt-tiers table still says "Max tokens: 300" for all tiers, contradicting the config-driven approach.
- [FACT] `benchmark.py:312-318` is missing `groq` in the provider map — Groq models fall through to `provider = "other"`, causing wrong per-provider semaphore bucketing.
- [FACT] Zero tests exist for the 4 new `benchmark.py` features (`--methods`, `--max-per-provider`, config-driven `max_tokens`, 4096 fallback) — all 38 existing tests cover `discover.py` + `telemetry.py` only.
- [FACT] `fleet-database-migration-20260813` Phase 1 (evidence_cache → SQLite `model_evidence` table) is shipped (commit `c2c531b`, 927 rows). Phases 2-4 are queued. Phase 3 will eliminate `fleet-models.json` and migrate the 3 stale-JSONL consumers.
- [FACT] Git HEAD at this revision: `af73e5750398d9e47161f50c59495b1c06ec8055`.

## Current state

**Done (model-benchmark skill surface):**

- `/model-benchmark` skill: 5 capabilities shipped, 38 existing tests, parameter-aware tier system, multi-method dispatch, auto-discovery, auto-promotion pipeline.
- Benchmark infrastructure (Rev 4): 5 defects fixed.
- Provider config fixes (Zen supportsDeveloperRole, PI zai provider, OpenCode providers, MiniMax-M3 alias, glm-5.2, 3-tuple `_PROVIDER_DISPATCH_MAP`).
- Subprocess timeout fix (Popen + taskkill /F /T /PID).
- Quality-tier benchmarks: production 10/10 Q=1.0, reasoning-base 50/50 Q=1.0, code-exec 129/130 Q=0.99.
- Tier-aware timeouts in benchmark_tiers.py.
- Pool test suite + orchestrator (3×3 matrix).
- Discovery mode with verify probe.
- Auto-promotion via `promote_models.py` with Wilson lower-bound + N≥10 gate.
- Cohere trial quota investigation (monthly limit 1000 calls, parse from 429 body).
- PI system prompt prepend fix (input= stdin).
- 6 wiki concepts captured.

**Not done (this handoff's remaining scope):**

- WS-Cleanup: review findings on hooks/crawl code (MBE-05, MBE-07); coordinate MBE-06 with migration Phase 3.
- WS-Telemetry: wire `log_spawn()`/`log_call()` into 7 skills (MBE-08..10).
- WS-SkillCleanup: Groq TPM fix (MBE-14), benchmark.py provider map (MBE-15), SKILL.md:190 staleness (MBE-16), zero tests (MBE-17), wiki fleet-size update (MBE-18 — re-anchor to new architecture), operator decisions on Kimi K3 + dead NIM (MBE-19 — re-anchor to `fleet-config.json`).
- WS-Validation: GPT-5.6 bridge load test (MBE-21), code-exec expansion to 13 problems (MBE-22).

## Task packets

14 task packets. MBE-XX numbers are preserved from the original 22-packet umbrella for traceability; gaps in the sequence (no MBE-01..04, MBE-11..13, MBE-20) mark items deferred to the migration handoff.

### MBE-05: Cluster B — uncertainty_gate detection gaps (45 min)
- Goal: Fix REV-002 (copular hedge pattern), REV-003 (sentence-level suppression), REV-008 (write-failure resilience).
- In scope: `~/.grok/hooks/scripts/uncertainty_gate.py`.
- Out of scope: other hooks; fleet infrastructure (independent).
- Files / anchors: uncertainty_gate.py detection patterns; suppression filters; log_detection try/except.
- Acceptance: "I think this is a problem" triggers detection (REV-002); "I think the limit is around 5 RPM. What do you think? Let me know." is suppressed (REV-003); file write failure doesn't crash the gate (REV-008).
- Falsifier: "I think we should fix this" still suppressed (REV-002 false positive); "The limit is around 5 RPM." still triggers (REV-003 over-suppressed).
- Verification level required: UNIT_TEST

### MBE-06: Cluster C — Cohere quota wiring (60 min, COORDINATE with migration Phase 3)
- Goal: Fix REV-004 (Cohere in spawn gate provider map — highest blast radius), REV-005/006/010 (telemetry-undercount honesty + dynamic 429 body parsing), REV-009 (probe name harmonization).
- In scope: `~/.grok/skills/model-quota/scripts/fleet_quota.py` lines ~916–936 (provider map), telemetry-undercount logic, 429 body parser.
- Out of scope: provider-specific changes outside Cohere.
- Files / anchors: `fleet_quota.py` `write_quota_cache` provider map; probe model name `command-a-plus-05-2026` vs `cohere-command-a-plus`.
- Acceptance: When Cohere is exhausted, spawn gate blocks Cohere dispatch (REV-004); when probe returns 200 OK but telemetry has 0 entries, shows "?" not "100%" (REV-005/006/010); both files use the same model identifier (REV-009).
- Falsifier: Cohere dispatch still allowed after 429; undercount still shown as 100%; probe name mismatch remains.
- Verification level required: UNIT_TEST
- **Migration coordination:** Phase 3 of `fleet-database-migration-20260813` modifies `fleet_quota.py:820-827` (Cohere counter JSONL→SQLite). Sequence MBE-06 AFTER Phase 3 ships to avoid merge conflicts. Or: bundle MBE-06 into Phase 3 if the migration session will take it.

### MBE-07: Cluster D — crawl dead code + no-op flag (45 min)
- Goal: Fix REV-007 (wire `--prune-boilerplate` or remove), REV-013 (remove dead BFS code).
- In scope: `~/.grok/skills/wiki-crawl4ai/crawl_to_qmd.py`.
- Out of scope: crawl4ai library itself; fleet infrastructure (independent).
- Files / anchors: `crawl_to_qmd.py` `FilterChain` for `--prune-boilerplate`; dead functions `_content_score`, `_is_boilerplate`.
- Acceptance: Flag either works or doesn't exist; no unreferenced functions.
- Falsifier: `--prune-boilerplate` still silently ignored; dead functions still present.
- Verification level required: UNIT_TEST

### MBE-08: Priority 1 telemetry — /check, /go, /review (2 hours)
- Goal: Wire `log_spawn()` into the 3 highest-signal dispatchers.
- In scope: `~/.grok/skills/check/SKILL.md` Step 3; `~/.grok/skills/go/SKILL.md` H4 wave; `~/.grok/skills/review/SKILL.md` specialist spawn.
- Out of scope: Priority 2/3 skills (separate packets); telemetry.py internals.
- Files / anchors: each SKILL.md's spawn block.
- Acceptance: Each skill's spawn points log to `P:/.artifacts/model-telemetry/usage.db`; `python ~/.grok/skills/model-benchmark/scripts/analyze.py` produces non-empty per-model stats after 1 day of usage.
- Falsifier: After 1 week of active use, `analyze.py` shows <10 entries per model — wiring is too shallow, check `from telemetry import log_spawn` resolves correctly.
- Verification level required: LIVE_BEHAVIOR

### MBE-09: Priority 2 telemetry — /www, /web, /wiki, /preflight (1.5 hours)
- Goal: Wire `log_spawn()` into 4 research/discovery skills.
- In scope: respective SKILL.md spawn blocks.
- Out of scope: Priority 1 (MBE-08) and Priority 3 (MBE-10) skills.
- Files / anchors: `~/.grok/skills/www/SKILL.md`, `~/.grok/skills/web/SKILL.md`, `~/.grok/skills/wiki/SKILL.md`, `P:/.agents/skills/preflight/SKILL.md`.
- Acceptance: Each spawn point logs with appropriate `task_domain` tag.
- Falsifier: Same as MBE-08.
- Verification level required: LIVE_BEHAVIOR

### MBE-10: Priority 3 telemetry — direct API scripts (30 min)
- Goal: Add `log_call()` to `P:/.agents/scripts/models/dgemma_read.py` and any other direct API scripts.
- In scope: dgemma_read.py and similar.
- Out of scope: new scripts (deferred).
- Files / anchors: `P:/.agents/scripts/models/dgemma_read.py`.
- Acceptance: Direct API calls log with `task_domain="extraction"` or appropriate tag.
- Falsifier: Script runs but no telemetry entry.
- Verification level required: UNIT_TEST

### MBE-14: Groq TPM fix (15 min)
- Goal: Cap Groq `max_completion_tokens` to ≤6000 in config.toml (Groq free tier TPM limit).
- In scope: `~/.grok/config.toml` Groq model entries.
- Out of scope: other providers' TPM limits.
- Files / anchors: `~/.grok/config.toml` Groq model entries.
- Acceptance: Groq benchmark stops returning HTTP 413.
- Falsifier: Groq still fails after cap.
- Verification level required: STATIC_INSPECTION

### MBE-15: Add `groq` to benchmark.py provider map (5 min)
- Goal: Fix `benchmark.py:312-318` missing `groq` (Groq models currently bucket as `provider="other"`).
- In scope: `benchmark.py:312-318` provider map.
- Out of scope: other providers.
- Files / anchors: `benchmark.py:312-318`.
- Acceptance: Groq models bucket as `provider="groq"` not `provider="other"`.
- Falsifier: Groq models still show `provider="other"`.
- Verification level required: STATIC_INSPECTION

### MBE-16: SKILL.md:190 prompt-tiers table staleness (5 min)
- Goal: Update table — still says "Max tokens: 300" but config-driven approach changed this.
- In scope: `~/.grok/skills/model-benchmark/SKILL.md:190`.
- Out of scope: other SKILL.md sections.
- Files / anchors: `SKILL.md:190`.
- Acceptance: Table reflects config-driven max_tokens.
- Falsifier: Table still says 300.
- Verification level required: STATIC_INSPECTION

### MBE-17: Tests for 4 new benchmark features (90 min)
- Goal: Cover `--methods`, `--max-per-provider`, config-driven `max_tokens`, 4096 fallback behavior (currently zero tests).
- In scope: `~/.grok/skills/model-benchmark/tests/test_benchmark.py` (new file).
- Out of scope: existing test files.
- Files / anchors: `~/.grok/skills/model-benchmark/tests/test_benchmark.py` (new file).
- Acceptance: `pytest ~/.grok/skills/model-benchmark/tests/test_benchmark.py -v` covers all 4 features.
- Falsifier: New tests don't cover all 4 features.
- Verification level required: UNIT_TEST

### MBE-18: Wiki update for fleet architecture (30 min, RE-ANCHORED)
- Goal: Update `P:/.data/wiki/concepts/model-fleet-provider-pools.md` to reflect the new architecture (operator JSON + SQLite split) rather than the legacy `fleet-models.json` monolith. The wiki currently says "46 model slugs" — the count is stale AND the storage model is changing.
- In scope: `model-fleet-provider-pools.md`.
- Out of scope: other wiki concepts.
- Files / anchors: `P:/.data/wiki/concepts/model-fleet-provider-pools.md`.
- Acceptance: Wiki reflects the `fleet-config.json` (operator) + `usage.db`/`model_metadata` table (automation) split per `fleet-database-migration-20260813`; model count is current.
- Falsifier: Wiki still describes `fleet-models.json` as the storage model after the migration ships.
- Verification level required: STATIC_INSPECTION
- **Migration coordination:** Sequence AFTER migration Phase 3 ships (which eliminates `fleet-models.json`). Otherwise the wiki will describe a storage model that no longer exists.

### MBE-19: Operator decisions on Kimi K3 + dead NIM models (BLOCKED, RE-ANCHORED)
- Goal: Decide keep-or-remove for Kimi K3 and ~12 dead NIM models.
- In scope: operator decision on `fleet-config.json` entries (post-migration) or `~/.grok/config.toml` model entries (pre-migration).
- Out of scope: model selection logic.
- Files / anchors: post-migration: `~/.grok/skills/model-quota/scripts/fleet-config.json`; pre-migration: `~/.grok/config.toml`.
- Acceptance: Operator decision recorded; entries updated accordingly.
- Falsifier: Decision deferred; models remain in config.
- Verification level required: STATIC_INSPECTION
- **Migration coordination:** Sequence AFTER migration Phase 3 ships so the decision lands in `fleet-config.json` (the new operator-authored file), not the soon-to-be-deleted `fleet-models.json`.

### MBE-21: GPT-5.6 bridge under real load (60 min)
- Goal: Test bridge with streaming, tool calls, long context, multi-turn as parent.
- In scope: bridge load test with each feature dimension.
- Out of scope: bridge implementation changes.
- Files / anchors: bridge endpoint `http://127.0.0.1:11435/v1`.
- Acceptance: `gpt-5-6-luna` works through bridge with tool calls.
- Falsifier: Tool calls fail or stream breaks.
- Verification level required: LIVE_BEHAVIOR

### MBE-22: Code-exec benchmark expansion to 13 problems (45 min)
- Goal: 5-problem set is too easy to discriminate coding pool — expand to 13 (already added to `benchmark_tiers.py`; needs validation run).
- In scope: code-exec tier validation run with 13 problems.
- Out of scope: tier definition changes.
- Files / anchors: `~/.grok/skills/model-benchmark/scripts/benchmark_tiers.py`.
- Acceptance: 13-problem run completes; results discriminate coding pool.
- Falsifier: 13-problem run fails or doesn't discriminate.
- Verification level required: LIVE_BEHAVIOR

## Deferred items (moved to fleet-database-migration-20260813)

These items were in the original 22-packet umbrella but are absorbed by the migration handoff. They are listed here for traceability — do NOT execute them from this handoff.

| Original MBE | Goal | Why deferred |
|---|---|---|
| MBE-01..04 | dispatch-paths fallback (remove `tool_grounded_spawn_broken` hard-exclusion in `model_router.py:707`) | Migration Phase 2 replaces `serde_broken`/`tool_grounded_spawn_broken` arrays with the `quarantine` table. The filter at `model_router.py:707` will be deleted. Solving the transport-aware-filter problem by modifying soon-to-be-deleted code is wasted work. |
| MBE-11..13 | benchmark coverage gaps (`dispatch_latency` for 3 OC-quota models; multi-method quality benchmarking; Zen-PI re-benchmark) | Migration Phase 3 eliminates `fleet-models.json` (where `dispatch_latency` is stored). Writing data to a file being deleted is wasted work. Multi-method quality benchmarking (MBE-12) is still relevant but should be re-scoped after the migration to write to SQLite, not JSON. |
| MBE-20 | pool wiring production validation | Migration Phase 3 changes pool derivation (lanes derived from capabilities at query time, not stored). Validation approach changes. |
| (proposed NEW-1) | `fleet_quota.py:820-827` Cohere counter JSONL→SQLite | Already in migration Phase 3 acceptance criteria. |
| (proposed NEW-2) | `pool_health.py:35` JSONL→SQLite | Already in migration Phase 3 acceptance criteria. |
| (proposed NEW-3) | EOL detector from discovery probe data | Already in migration Phase 3 (Decision 4 follow-up); writes to `model_metadata.lifecycle = 'suspected_eol'`. |
| (proposed MBE-26) | verify `promote_models.py` is actually promoting | Subsumed by migration Phase 3 acceptance criteria ("Automation writes lifecycle/promotion to model_metadata table via fleet_db.py"). |

**Net:** 10 items deferred (MBE-01..04, MBE-11..13, MBE-20, NEW-1/2/3, MBE-26). 14 items remain.

## Open decisions

**D1: Order of execution within this handoff.**
- Options: (a) telemetry wiring first (MBE-08..10 — adds data flow), (b) review findings first (MBE-05, MBE-07 — independent, fast), (c) skill cleanup first (MBE-14..17 — small fixes).
- Selection criterion: ROI per minute + independence from migration.
- Currently leads: (b) — MBE-05 and MBE-07 are independent of both the migration and fleet state; ship them first while the migration runs in parallel. Then (a) telemetry wiring complements the migration's data layer. Then (c) skill cleanup.
- Evidence that would change the lead: if the migration blocks on something, MBE-14..17 (skill cleanup) becomes the parallelizable work.

**D2: Coordinate or bundle MBE-06 (Cohere quota wiring) with migration Phase 3?**
- Options: (a) sequence after Phase 3, (b) bundle into Phase 3, (c) do independently before Phase 3.
- Selection criterion: avoid merge conflicts on `fleet_quota.py`.
- Currently leads: (a) — Phase 3 modifies `fleet_quota.py:820-827`; MBE-06 modifies `fleet_quota.py:916-936`. Sequencing avoids touching the same file concurrently.
- Evidence that would change the lead: if the migration session wants to absorb MBE-06 into Phase 3, bundle it.

## Hard constraints

1. **Do not duplicate migration work.** If a task packet touches a file or behavior the migration handoff owns, defer or coordinate (see MBE-06, MBE-18, MBE-19).
2. **Telemetry writes flow to `usage.db`.** All `log_call()` / `log_spawn()` writes go to `P:/.artifacts/model-telemetry/usage.db` — the same database the migration's `fleet_db.py` reads from. Do not write to `usage.jsonl` (stale, last modified 2026-07-24).
3. **PI prompts via stdin.** `subprocess.run(["pi", ..., prompt])` truncates to first line. Must use `input=prompt`. All PI benchmarks before 2026-08-11 invalidated.
4. **Don't burn `~/.grok` quota** by running all benchmarks at once. Re-run in phases by lane.
5. **Do not add new providers to PI/OpenCode** without verifying via `pi -p --provider <name> --model <id> "test"` first.

## Cross-reference couplings

- `P:/docs/handoffs/fleet-database-migration-20260813/HANDOFF.md` → **authoritative for fleet infrastructure**. This handoff coordinates with it on MBE-06 (`fleet_quota.py`), MBE-18 (wiki architecture), MBE-19 (operator decisions target file).
- `P:/.artifacts/review/019fc95d-session-review/FINDINGS.md` → 14 findings source for MBE-05..07.
- `~/.grok/skills/model-benchmark/scripts/telemetry.py` → the `log_call` / `log_spawn` API MBE-08..10 wire into skills.
- `~/.grok/skills/model-benchmark/scripts/benchmark.py` → MBE-15 modifies provider map; MBE-17 adds tests for its 4 new features.
- `~/.grok/skills/model-benchmark/scripts/benchmark_tiers.py` → MBE-22 validates 13-problem code-exec expansion.
- `~/.grok/skills/model-quota/scripts/fleet_quota.py` → MBE-06 modifies Cohere provider map; migration Phase 3 modifies Cohere counter. Coordinate.
- `~/.grok/hooks/scripts/uncertainty_gate.py` → MBE-05 modifies detection patterns.
- `~/.grok/skills/wiki-crawl4ai/crawl_to_qmd.py` → MBE-07 removes dead code.
- `~/.grok/config.toml` → MBE-14 caps Groq max_completion_tokens.
- `P:/.data/wiki/concepts/model-fleet-provider-pools.md` → MBE-18 updates architecture description (post-migration).
- `~/.grok/skills/model-quota/scripts/fleet-config.json` → MBE-19 target file (post-migration Phase 3).
- This handoff's `accurate_as_of_head` → `af73e5750398d9e47161f50c59495b1c06ec8055`. If HEAD moves, re-verify cited paths.

## Other outstanding streams (not handed off)

- **`P:/docs/handoffs/routing-library`** — OPEN, 2w+. Build `route.py` centralizing task-domain → model selection. Adjacent.
- **`P:/docs/handoffs/fleet-code-bugs`** — OPEN, 2w+. BUG-03: DeepSeek code-verification recommendation blocked by a bug. Adjacent.
- **`P:/docs/handoffs/model-selection-domain-index-20260809`** — OPEN, 4d+. Organizes the broader model-selection domain. Adjacent.
- **`P:/docs/handoffs/ship-py-pi-dispatch-and-quality-gate-gaps-20260810`**, **`ship-py-pi-dispatch-not-found-20260809`**, **`ship-py-pipeline-integration-gaps-20260810`** — ship-py integration gaps. Adjacent.
- **`P:/docs/handoffs/transport-aware-dispatch-design-20260802`** — design doc for transport-aware dispatch; migration supersedes much of this. Adjacent.

## Explicit non-goals

- Do NOT modify `model_router.py:707` (serde_broken filter) — owned by migration Phase 2.
- Do NOT write `dispatch_latency` data to `fleet-models.json` — file is being eliminated by migration Phase 3.
- Do NOT migrate `usage.jsonl` consumers to SQLite — owned by migration Phase 3.
- Do NOT build EOL detector — owned by migration Phase 3 (Decision 4 follow-up).
- Do NOT change model selection logic in any skill (only add telemetry logging).
- Do NOT run the full benchmark in one session (use phased lane-by-lane runs).
- Do NOT add new providers to PI/OpenCode without verifying via `pi -p --provider <name> --model <id> "test"` first.

## Resumption protocol

1. **Read this handoff** (you're already doing that).
2. **Read `P:/docs/handoffs/fleet-database-migration-20260813/HANDOFF.md`** — establish what the migration owns so you don't duplicate.
3. **Pick a starting packet:**
   - For independent fast wins: MBE-05 (uncertainty_gate) or MBE-07 (crawl dead code) — both ~45 min, independent of migration.
   - For high-signal data flow: MBE-08 (telemetry wiring into /check, /go, /review) — 2 hours, complementary to migration.
   - For skill cleanup: MBE-14 (Groq TPM, 15 min) or MBE-15 (provider map, 5 min) — small, independent.
4. **Verify** with the per-packet verification command.
5. **Update this handoff** with a revision block reporting what shipped.

## Suggested next invocation

```
/go implement MBE-05 and MBE-07 from P:/docs/handoffs/model-benchmark-effort-20260813/HANDOFF.md
```

(Both are ~45 min each, independent of the migration, fix verified review findings.)

## Last user message (verbatim)

> go with option (b) and commit the downsized umbrella. The migration handoff is authoritative for fleet infrastructure; the umbrella is authoritative for model-benchmark skill cleanup and telemetry wiring.

## Epistemic labels

- [FACT] All factual claims in the Verified facts section cite source paths (file:line, commit SHA, or handoff line).
- [INFERENCE] D1 lead (review findings first) is inferred from "independent + fast" reasoning, not operator-confirmed.
- [INFERENCE] D2 lead (sequence MBE-06 after Phase 3) is inferred from merge-conflict-avoidance reasoning.
- [UNKNOWN] Whether the migration session wants to bundle MBE-06 into Phase 3 (D2 option b). Operator decision.

## Suggested skills for next session

- **`/go`** — 14 task packets ready to execute; MBE-05 and MBE-07 are the highest-confidence starting points (independent of migration).
- **`/check`** — verify telemetry wiring after MBE-08..10 ship.
- **`/review --focus maintainability`** — after MBE-17 ships (new test file), audit coverage.
- **`/wiki`** — after migration Phase 3 ships, MBE-18 needs the wiki concept updated to reflect the new architecture.

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-13T23:30 | 019ffd06-0d7f-7f21-98fc-6117652ba7e3 | created — consolidates 4 active + 3 older model-benchmark workstreams into single umbrella; 22 task packets |
| 2026-08-14T00:00 | 019ffd06-0d7f-7f21-98fc-6117652ba7e3 | updated — closed 5 superseded handoffs (deleted: `model-benchmark-dispatch-019fc95d`, `dispatch-paths-fallback-not-spawn-block-20260805`, `review-findings-fix-019fc95d-20260806`, `model-telemetry-integration`, `telemetry-integration-20260724`); their work is fully captured in MBE-01..10. `parent_handoff_path` reset to `none` since parent is closed. Preserved `model-benchmark-20260728` and `model-benchmark-pool-contracts-bridge-20260729` (have unique reference content beyond umbrella). |
| 2026-08-14T00:30 | 019ffd06-0d7f-7f21-98fc-6117652ba7e3 | **downsized (option b)** — deferred 10 task packets to `fleet-database-migration-20260813` (MBE-01..04, MBE-11..13, MBE-20, NEW-1/2/3, MBE-26). 14 packets remain (MBE-05..10, MBE-14..19, MBE-21..22). Authority split locked: migration owns fleet infrastructure; this handoff owns model-benchmark skill cleanup + telemetry wiring. MBE-06/18/19 marked "coordinate with migration." Objective, status, verified facts, cross-references, hard constraints, non-goals, resumption protocol, suggested skills all updated to reflect new scope. `accurate_as_of_head` bumped to `af73e57`. |
