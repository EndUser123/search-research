---
thread_id: 9b7e3a4f-2c1d-4e6a-8d5b-7a9c0f1e8b2c
parent_handoff_path: P:/docs/handoffs/model-benchmark-dispatch-019fc95d/HANDOFF.md
current_session_id: 019ffd06-0d7f-7f21-98fc-6117652ba7e3
parent_session: none
current_terminal_id: console_019ffd06
produced_at: 2026-08-13T23:30:00Z
last_updated_by: 019ffd06-0d7f-7f21-98fc-6117652ba7e3
last_updated_at: 2026-08-13T23:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 48a327574395b7ba6a003b4f6e619496d3c791b7
---

# Handoff: Model-benchmark effort — consolidated remaining work

## Objective

Complete the model-benchmark effort: ship the four open workstreams (dispatch-paths fallback revert, /review findings fixes, telemetry integration, benchmark coverage gaps) plus the older-pending workstreams (pool contracts validation, telemetry storage migration, fleet-code bugs), so the model-benchmark skill is reliable, evidence-driven, and the fleet picker has empirical data for every active model.

**Scope bounds:** Work scope is the 4 active model-benchmark handoffs (3 of 4 owned by session 019fc95d, 1 unowned) and 3 older-pending workstreams (model-benchmark-20260728, model-benchmark-pool-contracts-bridge-20260729, telemetry-integration-20260724). Adjacent handoffs (routing-library, transport-aware-dispatch-design, sqlite-telemetry-backend, fleet-code-bugs, model-selection-domain-index-20260809, ship-py-*, tp-parallel-panel-dispatch-20260801, cross-model-dispatch-improvements-20260801, fleet-dispatch-improvements-20260731) are referenced where they couple to model-benchmark work but not in scope for this handoff.

## Status

OPEN — 4 active workstreams, ~6 task packets with ~1h total work in the smallest packet; full effort estimated 6–10 hours across multiple sessions.

## Producing context

- Date: 2026-08-13
- Session: `019ffd06-0d7f-7f21-98fc-6117652ba7e3` (this handoff's author)
- Terminal: `console_019ffd06`
- Host: Grok Build (this session)
- Producing context: the operator asked for remaining work for the model-benchmark effort, then asked what handoff files exist, then asked to (a) handle each workstream, (b) create one umbrella handoff, (c) update old handoff files, (d) cleanup preserving ones with remaining work.

## Read-first list (ordered, with reasons)

1. `~/.grok/skills/model-benchmark/SKILL.md` — the canonical skill surface (5 capabilities: benchmark, quality, telemetry, analyze, discovery); what every other handoff references.
2. `P:/docs/handoffs/model-benchmark-dispatch-019fc95d/HANDOFF.md` — parent handoff; 4 revisions; Execution Status table at line 224–240 lists 5 prior remaining-work items as DONE; current remaining work is in child handoffs and the dispatch-paths fallback.
3. `P:/docs/handoffs/dispatch-paths-fallback-not-spawn-block-20260805/HANDOFF.md` — **CRITICAL** — 4 task packets (~1h total), small, fully unit-tested, blocks the critic lane routing.
4. `P:/docs/handoffs/review-findings-fix-019fc95d-20260806/HANDOFF.md` — 14 verified findings from session review; 3 root-cause clusters (uncertainty_gate, Cohere quota wiring, crawl dead code).
5. `P:/docs/handoffs/model-telemetry-integration/HANDOFF.md` — wire `log_call()`/`log_spawn()` into 7 skills; oldest open item (2w); no integration code shipped.
6. `P:/docs/handoffs/model-benchmark-20260728/HANDOFF.md` — older workstream; 7 pending operator decisions (Kimi K3 status, dead NIM models, Groq TPM fix, fleet-size wiki update, missing groq in benchmark.py provider map, SKILL.md:190 stale max_tokens table, zero tests for 4 new features).
7. `P:/docs/handoffs/model-benchmark-pool-contracts-bridge-20260729/HANDOFF.md` — older workstream; Codex OAuth bridge + pool contracts + skill wiring; validation incomplete (no real /debrief, no GPT-5.6 tool calls, code-exec expansion unfinished).
8. `P:/docs/handoffs/telemetry-integration-20260724/HANDOFF.md` — older duplicate of model-telemetry-integration; same scope; not started.
9. `P:/docs/handoffs/model-selection-domain-index-20260809/HANDOFF.md` — organizes the broader model-selection domain; **adjacent**, not in scope but useful for context on why model-benchmark work matters.
10. `~/.grok/skills/model-quota/scripts/fleet-models.json` — fleet registry with `dispatch_paths`, `dispatch_latency`, `tool_grounded_spawn_broken`, per-lane `quota_floor` (v5 schema).
11. `~/.grok/skills/model-quota/scripts/pick_model.py` — the picker that the dispatch-paths-fallback handoff targets (DP-01/02).
12. `P:/.data/wiki/concepts/dedicated-quota-first-dispatch-routing.md` — wiki concept capturing the dispatch_paths design rationale.

## Verified facts (with source paths)

- [FACT] `/model-benchmark` skill ships 5 capabilities: parallel benchmark, quality scoring, telemetry logging, analyze reports, multimodal tier (SKILL.md lines 18–55).
- [FACT] 14 of 20 fleet models have quality scores; 17 of 20 have dispatch latency; 15 of 20 have HTTP+PI coverage (parent handoff Rev 4 fleet results table, model-benchmark-dispatch-019fc95d/HANDOFF.md line 354).
- [FACT] `tool_grounded_spawn_broken` list in `fleet-models.json` currently blocks 3 models (`nvidia-nemotron-3-ultra`, `nim-deepseek-ai-deepseek-v4-flash`, `nim-deepseek-ai-deepseek-v4-pro`) from all lanes in `pick_model.py` despite their working via PI/OC/HTTP (dispatch-paths-fallback-not-spawn-block-20260805/HANDOFF.md lines 38–45).
- [FACT] `pick_model.py critic --exclude-self --json` returns `nim-openai-gpt-oss-20b` as the only verified-spawn critic-lane model after the tool-fallbacks update — both DeepSeek variants are blocked (dispatch-paths-fallback-not-spawn-block-20260805/HANDOFF.md line 65, verified 2026-08-05).
- [FACT] Zen PI was fixed (supportsDeveloperRole) AFTER the prior benchmark completed; the recorded Zen-PI latency data is therefore stale and reflects pre-fix failure (model-benchmark-dispatch-019fc95d/HANDOFF.md lines 126–134).
- [FACT] 14 `/review` findings at `P:/.artifacts/review/019fc95d-session-review/FINDINGS.md`, 3 root-cause clusters: Cluster B uncertainty_gate (3 findings), Cluster C Cohere quota wiring (5 findings), Cluster D crawl dead code (2 findings) (review-findings-fix-019fc95d-20260806/HANDOFF.md lines 33–73).
- [FACT] 7 skills still need telemetry integration: `/check`, `/go`, `/review` (Priority 1); `/www`, `/web`, `/wiki`, `/preflight` (Priority 2); zero integration code shipped to any of them (model-telemetry-integration/HANDOFF.md lines 38–58, verified by absence of `from telemetry import log_call` in those skill files).
- [FACT] 3 older model-benchmark handoffs (model-benchmark-20260728, model-benchmark-pool-contracts-bridge-20260729, telemetry-integration-20260724) all have remaining work items — none are pure noise (read each handoff's "Next steps" / "Pending decisions" sections; cited above).
- [FACT] `model-benchmark-dispatch-enhancement-20260803/HANDOFF.md` is `yaml:closed, work:CLOSED` — already closed by prior session (handoff list output 2026-08-13, `list_handoffs.py`).
- [FACT] Session 019fc95d owns 3 of 4 active model-benchmark handoffs (model-benchmark-dispatch-019fc95d, dispatch-paths-fallback, review-findings-fix-019fc95d); session 019ffd06 (this session) owns this umbrella. The handoff SKILL.md Hard Constraint #6 (single-writer per handoff) prevents this session from appending revision blocks to 019fc95d's handoffs.
- [FACT] Git HEAD at this handoff's write: `48a327574395b7ba6a003b4f6e619496d3c791b7` (verified via `git -C P:/ rev-parse HEAD` at 2026-08-13T23:30Z).

## Current state

**Done (across all model-benchmark workstreams):**

- `/model-benchmark` skill: 5 capabilities shipped, 38 existing tests, parameter-aware tier system, multi-method dispatch, auto-discovery, auto-promotion pipeline.
- Benchmark infrastructure (Rev 4): 5 defects fixed (per-provider throttling, print_fleet_coverage count bug, default model loading from fleet-models.json, entry point order, quality score write-back).
- Provider config fixes: PI supportsDeveloperRole for Zen; PI zai provider added; OpenCode providers added (opencode-zen, openrouter, nvidia-nim); MiniMax-M3 alias in PI; glm-5.2 + MiniMax-M3 in OpenCode; 3-tuple `_PROVIDER_DISPATCH_MAP`.
- Subprocess timeout fix: `_run_cli_with_timeout()` in benchmark.py uses Popen + `taskkill /F /T /PID` to avoid Windows `communicate()` deadlock.
- Quality-tier benchmarks: production 10/10 Q=1.0, reasoning-base 50/50 Q=1.0, code-exec 129/130 Q=0.99 (1 nemotron-ultra timeout at 600s).
- Tier-aware timeouts in benchmark_tiers.py: `CodeExecTier(300s)`, `ProductionTier(120s)`, `DeepReasoningTier(300s)`.
- Pool test suite + orchestrator (3×3 matrix: 3 capabilities × 3 methods with concurrency ceilings per provider).
- Discovery mode: catalog list + config diff + reachability verify probe (catches `/v1/models` lie pattern).
- Auto-promotion via `promote_models.py` with Wilson lower-bound + N≥10 independent successes gate.
- Wiki concepts (6 written in Rev 4 alone): `llm-uncertainty-hedging-detection-research-landscape`, `crawl4ai-optimization-built-in-features`, `coverage-gap-hiding-reporting-success-without-surfacing-incomplete-state`, `cohere-trial-api-quota-signals-and-failure-modes`, `pi-cli-ignores-supports-developer-role-for-mistral`, `dedicated-quota-first-dispatch-routing` (updated).
- Cohere trial quota investigation: monthly limit 1000 calls, parse from 429 body (`{"message": ...}` not `{"id": ...}`), wired into `fleet_quota.py`.
- PI system prompt prepend fix: prompts with `input=` (stdin, not positional arg) + capability-specific prepend; all PI benchmarks before 2026-08-11 invalidated.
- Pool contracts (4 files in capabilities/): coding, reasoning, mechanical, critic; wired into 9 skills via `consumes:` declarations (model-benchmark-pool-contracts-bridge-20260729/HANDOFF.md lines 25–42).

**Not done (this handoff's scope):**

- WS-1: `dispatch-paths-fallback-not-spawn-block-20260805` — 4 task packets unimplemented.
- WS-2: `review-findings-fix-019fc95d-20260806` — 14 findings, 0 fixed.
- WS-3: `model-telemetry-integration` — 7 skills, 0 integrated.
- WS-4: `model-benchmark-dispatch-019fc95d` — 3 remaining items per Rev 4 (review findings, dispatch-paths revert, push repos); parent handoff's own remaining-work list is now fully delegated to children.
- WS-5 (older): `model-benchmark-20260728` — 7 pending decisions including Groq TPM fix and zero test coverage.
- WS-6 (older): `model-benchmark-pool-contracts-bridge-20260729` — validation pending (real /debrief, GPT-5.6 tool calls, code-exec expansion to 13 problems).
- WS-7 (older duplicate): `telemetry-integration-20260724` — same scope as WS-3; not started.

## Task packets

22 task packets across 7 workstreams. WS-X headings are *narrative*, not task packets — each MBE-XX is a discrete task packet.

**WS-1: dispatch-paths-fallback** (4 packets, ~60 min)

### MBE-01: Remove `tool_grounded_spawn_broken` hard-exclusion (15 min)
- Goal: Stop blocking models from `pick_model.py` selection when only `spawn_subagent` is broken; keep the list as transport metadata.
- In scope: `~/.grok/skills/model-quota/scripts/pick_model.py` `is_available()` function, lines ~100–115.
- Out of scope: changes to `fleet-models.json` structure; changes to other callers.
- Files / anchors: `pick_model.py` lines 100–115 (the tool_grounded_spawn_broken block).
- Acceptance: `pick_model.py critic --exclude-self --json` returns `nim-deepseek-ai-deepseek-v4-flash` as available when it's the best tier match; `tool_grounded_spawn_broken` models show `available: true` with a `spawn_limitation` field.
- Falsifier: `pick_model.py critic --json` still excludes models in `serde_broken` or `learned_broken` (those are real hard exclusions); only `tool_grounded_spawn_broken` stops being a hard exclusion.
- Verification level required: UNIT_TEST

### MBE-02: Add `spawn_limitation` field to pick_model JSON output (10 min)
- Goal: Surface `spawn_limitation: "tool-grounded-spawn-broken"` (or `null`) so callers know to skip spawn.
- In scope: `pick_model.py` `pick_model()` return dict construction.
- Out of scope: caller changes (handled in MBE-03).
- Files / anchors: `pick_model.py` `pick_model()` return dict.
- Acceptance: JSON output includes `spawn_limitation` for `tool_grounded_spawn_broken` models; `null` for others.
- Falsifier: a model NOT in the list shows `spawn_limitation: null`.
- Verification level required: UNIT_TEST

### MBE-03: /tp spawn lens uses `dispatch_paths` fallback (30 min)
- Goal: When `/tp` dispatches a spawn lens and the model has `spawn_limitation: "tool-grounded-spawn-broken"`, skip `spawn_subagent` and use `pi -p` or the next `dispatch_path`.
- In scope: `~/.grok/skills/tp/SKILL.md` Step 2 spawn lens dispatch logic, or `~/.grok/skills/tp/__lib/tp_dispatch.py` if it exists.
- Out of scope: other pick_model consumers (/go, /check) — they'll benefit from MBE-01/02 automatically.
- Files / anchors: `~/.grok/skills/tp/SKILL.md` Step 2.
- Acceptance: `/tp critic` with a `tool_grounded_spawn_broken` model in the critic lane returns a critique via PI instead of failing via spawn.
- Falsifier: `/tp` still calls `spawn_subagent` for a `tool_grounded_spawn_broken` model and gets the serde error.
- Verification level required: LIVE_BEHAVIOR

### MBE-04: Add `zen-deepseek-v4-flash-free` to `tool_grounded_spawn_broken` list (5 min)
- Goal: Complete the list — `zen-deepseek-v4-flash-free` is documented as spawn-broken in `tool-fallbacks.md` but missing from the list.
- In scope: `fleet-models.json` `tool_grounded_spawn_broken` array (top-level + derived_views).
- Out of scope: pick_model.py logic (MBE-01 handles).
- Files / anchors: `fleet-models.json` lines ~1121 and ~2070.
- Acceptance: After MBE-01, `pick_model.py` shows `zen-deepseek` with `spawn_limitation: "tool-grounded-spawn-broken"`.
- Falsifier: `zen-deepseek` shows `spawn_limitation: null`.
- Verification level required: STATIC_INSPECTION

**WS-2: review-findings-fix** (3 clusters, ~3–4 hours total)

### MBE-05: Cluster B — uncertainty_gate detection gaps (45 min)
- Goal: Fix REV-002 (copular hedge pattern), REV-003 (sentence-level suppression), REV-008 (write-failure resilience).
- In scope: `~/.grok/hooks/scripts/uncertainty_gate.py`.
- Out of scope: other hooks.
- Files / anchors: uncertainty_gate.py detection patterns; suppression filters; log_detection try/except.
- Acceptance: "I think this is a problem" triggers detection (REV-002); "I think the limit is around 5 RPM. What do you think? Let me know." is suppressed (REV-003); file write failure doesn't crash the gate (REV-008).
- Falsifier: "I think we should fix this" still suppressed (REV-002 not a false positive); "The limit is around 5 RPM." still triggers (REV-003 not over-suppressed).
- Verification level required: UNIT_TEST

### MBE-06: Cluster C — Cohere quota wiring (60 min)
- Goal: Fix REV-004 (Cohere in spawn gate provider map — highest blast radius, blocks Cohere dispatch when exhausted), REV-005/006/010 (telemetry-undercount honesty + dynamic 429 body parsing), REV-009 (probe name harmonization).
- In scope: `~/.grok/skills/model-quota/scripts/fleet_quota.py` lines ~916–936 (provider map), telemetry-undercount logic, 429 body parser.
- Out of scope: provider-specific changes outside Cohere.
- Files / anchors: `fleet_quota.py` `write_quota_cache` provider map; probe model name `command-a-plus-05-2026` vs `cohere-command-a-plus`.
- Acceptance: When Cohere is exhausted, spawn gate blocks Cohere dispatch (REV-004); when probe returns 200 OK but telemetry has 0 entries, shows "?" not "100%" (REV-005/006/010); both files use the same model identifier (REV-009).
- Falsifier: Cohere dispatch still allowed after 429; undercount still shown as 100%; probe name mismatch remains.
- Verification level required: UNIT_TEST

### MBE-07: Cluster D — crawl dead code + no-op flag (45 min)
- Goal: Fix REV-007 (wire `--prune-boilerplate` or remove), REV-013 (remove dead BFS code).
- In scope: `~/.grok/skills/wiki-crawl4ai/crawl_to_qmd.py`.
- Out of scope: crawl4ai library itself.
- Files / anchors: `crawl_to_qmd.py` `FilterChain` for `--prune-boilerplate`; dead functions `_content_score`, `_is_boilerplate`.
- Acceptance: Flag either works or doesn't exist; no unreferenced functions.
- Falsifier: `--prune-boilerplate` still silently ignored; dead functions still present.
- Verification level required: UNIT_TEST

**WS-3: model-telemetry-integration** (3 packets, ~4 hours total)

### MBE-08: Priority 1 skills — /check, /go, /review telemetry wiring (2 hours)
- Goal: Wire `log_spawn()` into the 3 highest-signal dispatchers.
- In scope: `~/.grok/skills/check/SKILL.md` Step 3; `~/.grok/skills/go/SKILL.md` H4 wave; `~/.grok/skills/review/SKILL.md` specialist spawn.
- Out of scope: Priority 2/3 skills (separate packets).
- Files / anchors: each SKILL.md's spawn block.
- Acceptance: Each skill's spawn points log to `P:/.artifacts/model-telemetry/usage.db`; `python ~/.grok/skills/model-benchmark/scripts/analyze.py` produces non-empty per-model stats after 1 day of usage.
- Falsifier: After 1 week of active use, `analyze.py` shows <10 entries per model — wiring is too shallow, check `from telemetry import log_spawn` resolves correctly.
- Verification level required: LIVE_BEHAVIOR

### MBE-09: Priority 2 skills — /www, /web, /wiki, /preflight telemetry wiring (1.5 hours)
- Goal: Wire `log_spawn()` into 4 research/discovery skills.
- In scope: respective SKILL.md spawn blocks.
- Out of scope: Priority 3 direct API scripts (separate packet).
- Files / anchors: `~/.grok/skills/www/SKILL.md`, `~/.grok/skills/web/SKILL.md`, `~/.grok/skills/wiki/SKILL.md`, `P:/.agents/skills/preflight/SKILL.md`.
- Acceptance: Each spawn point logs with appropriate `task_domain` tag.
- Falsifier: Same as MBE-08.
- Verification level required: LIVE_BEHAVIOR

### MBE-10: Priority 3 direct API scripts (30 min)
- Goal: Add `log_call()` to `P:/.agents/scripts/models/dgemma_read.py` and any other direct API scripts.
- In scope: dgemma_read.py and similar.
- Out of scope: new scripts (deferred).
- Files / anchors: `P:/.agents/scripts/models/dgemma_read.py`.
- Acceptance: Direct API calls log with `task_domain="extraction"` or appropriate tag.
- Falsifier: Script runs but no telemetry entry.
- Verification level required: UNIT_TEST

**WS-4: benchmark coverage gaps** (3 packets, ~3 hours total)

### MBE-11: Re-run benchmark for 3 OC-quota-exhausted models (45 min)
- Goal: Fill the 3/20 dispatch_latency gap (parent handoff Rev 4 line 354) — OpenCode Go quota was exhausted as of 2026-08-04 with reset ~Aug 6; re-run benchmark.
- In scope: 3 OC-quota-exhausted models re-tested via `python ~/.grok/skills/model-benchmark/scripts/benchmark.py --methods pi,opencode,direct --timeout 90 --max-per-provider 1`.
- Out of scope: other coverage gaps (separate packets).
- Files / anchors: `benchmark.py`, `fleet-models.json` `dispatch_latency` fields.
- Acceptance: `--gaps` reports <20 models missing dispatch_latency data.
- Falsifier: Models still missing after re-run; OC Go quota still exhausted.
- Verification level required: LIVE_BEHAVIOR

### MBE-12: Multi-method quality benchmarking implementation (90 min)
- Goal: Implement the design section in benchmark SKILL.md (multi-method quality transport); `benchmark_model()` takes a `transport` parameter.
- In scope: `benchmark.py` `benchmark_model()` signature, dispatch routing per transport.
- Out of scope: new transports (e.g., Codex→runner→Pi is already in `benchmark_runner.py`).
- Files / anchors: `benchmark.py` `benchmark_model()`.
- Acceptance: `python benchmark.py --tier code-exec --models <models> --transports http,pi` produces quality scores per transport.
- Falsifier: `--transports` flag is rejected; quality scores identical across transports (signals no measurement happened).
- Verification level required: LIVE_BEHAVIOR

### MBE-13: Zen-PI re-benchmark after fix (30 min)
- Goal: Update Zen-PI latency data — recorded data is from before supportsDeveloperRole fix (verified stale per parent handoff Rev 4 lines 126–134).
- In scope: 2 Zen models (`zen-deepseek-v4-flash-free`, `zen-north-mini-code-free`).
- Out of scope: other Zen models or non-Zen models.
- Files / anchors: `fleet-models.json` `dispatch_latency` for Zen models.
- Acceptance: fleet-models.json shows new Zen-PI latency values (not FAIL).
- Falsifier: Zen-PI still FAIL after re-run.
- Verification level required: LIVE_BEHAVIOR

**WS-5 (older): model-benchmark-20260728** (6 packets, ~3 hours total)

### MBE-14: Groq TPM fix (15 min)
- Goal: Cap Groq `max_completion_tokens` to ≤6000 in config.toml (Groq free tier TPM limit per model-benchmark-20260728/HANDOFF.md lines 240–254).
- In scope: `~/.grok/config.toml` Groq model entries.
- Out of scope: other providers' TPM limits (separate work).
- Files / anchors: `~/.grok/config.toml` Groq model entries.
- Acceptance: Groq benchmark stops returning HTTP 413.
- Falsifier: Groq still fails after cap.
- Verification level required: STATIC_INSPECTION

### MBE-15: Add `groq` to benchmark.py provider map (5 min)
- Goal: Fix `benchmark.py:312-318` missing `groq` (model-benchmark-20260728/HANDOFF.md lines 257–261).
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

### MBE-18: Wiki update for 118-model fleet (30 min)
- Goal: Update `P:/.data/wiki/concepts/model-fleet-provider-pools.md` (currently says 46, drift = 72).
- In scope: `model-fleet-provider-pools.md`.
- Out of scope: other wiki concepts.
- Files / anchors: `P:/.data/wiki/concepts/model-fleet-provider-pools.md`.
- Acceptance: Wiki reflects 118 models.
- Falsifier: Wiki still says 46.
- Verification level required: STATIC_INSPECTION

### MBE-19: Operator decisions on Kimi K3 + dead NIM models (BLOCKED)
- Goal: Decide keep-or-remove for Kimi K3 and ~12 dead NIM models.
- In scope: operator decision on config.toml entries.
- Out of scope: model selection logic.
- Files / anchors: `~/.grok/config.toml`.
- Acceptance: Operator decision recorded; config.toml updated accordingly.
- Falsifier: Decision deferred; models remain in config.
- Verification level required: STATIC_INSPECTION

**WS-6 (older): model-benchmark-pool-contracts-bridge-20260729** (3 packets, validation pending)

### MBE-20: Pool wiring production validation (30 min)
- Goal: Run real /debrief or /tp and confirm subagents dispatch from pool files, not hardcoded defaults (model-benchmark-pool-contracts-bridge-20260729/HANDOFF.md lines 67–69).
- In scope: real /debrief or /tp run with subagent trace inspection.
- Out of scope: pool contract content changes.
- Files / anchors: capabilities/ pool files, skill spawn points.
- Acceptance: Subagent spawn traces show pool-sourced model slugs.
- Falsifier: Hardcoded slugs still observed in traces.
- Verification level required: LIVE_BEHAVIOR

### MBE-21: GPT-5.6 bridge under real load (60 min)
- Goal: Test bridge with streaming, tool calls, long context, multi-turn as parent (model-benchmark-pool-contracts-bridge-20260729/HANDOFF.md lines 70–73).
- In scope: bridge load test with each feature dimension.
- Out of scope: bridge implementation changes.
- Files / anchors: bridge endpoint `http://127.0.0.1:11435/v1`.
- Acceptance: `gpt-5-6-luna` works through bridge with tool calls.
- Falsifier: Tool calls fail or stream breaks.
- Verification level required: LIVE_BEHAVIOR

### MBE-22: Code-exec benchmark expansion to 13 problems (45 min)
- Goal: Currently 5-problem set is too easy to discriminate coding pool — expand to 13 (already added to `benchmark_tiers.py` per handoff; needs validation run).
- In scope: code-exec tier validation run with 13 problems.
- Out of scope: tier definition changes.
- Files / anchors: `~/.grok/skills/model-benchmark/scripts/benchmark_tiers.py`.
- Acceptance: 13-problem run completes; results discriminate coding pool.
- Falsifier: 13-problem run fails or doesn't discriminate.
- Verification level required: LIVE_BEHAVIOR

**WS-7 (older duplicate): telemetry-integration-20260724** — see D3 below; no task packet (covered by WS-3 / MBE-08..10).

This handoff duplicates WS-3's scope (`model-telemetry-integration` supersedes it — newer, more detailed, same objective). Recommended disposition: close as superseded after WS-3 ships. **No separate task packet** — included in WS-3 acceptance.

## Open decisions

**D1: Order of execution.**
- Options: (a) WS-1 first (60 min, fully scoped, unit-tested, unblocks critic lane), (b) WS-5+WS-6 cleanup first (older debt, mostly cosmetic), (c) WS-3 first (telemetry enables empirical data for the rest).
- Selection criterion: ROI per minute of operator attention + reversibility.
- Currently leads: (a) — WS-1 is the smallest, highest-confidence packet; unblocks a routing failure the operator flagged.
- Evidence that would change the lead: if telemetry wiring is needed before any further benchmark runs to capture data, WS-3 moves up.

**D2: Should the dispatch-paths fallback use soft preference (rank tool_grounded_spawn_broken lower) or hard pass-through (let caller decide)?**
- Options: (a) soft preference, (b) hard pass-through.
- Selection criterion: caller complexity vs. flexibility.
- Currently leads: (a) — minimal change from current behavior; `spawn_limitation` field still surfaced for callers that want it.
- Evidence that would change the lead: callers that need to select transport dynamically based on prompt characteristics.

**D3: Merge `telemetry-integration-20260724` into `model-telemetry-integration` or keep separate?**
- Options: (a) close the older as superseded, (b) keep both, (c) merge content.
- Selection criterion: avoiding double work; freshness.
- Currently leads: (a) — `model-telemetry-integration` is newer (same objective, more detailed plan).
- Evidence that would change the lead: if the older handoff has unique content the newer lacks.

**D4: Push unpushed commits before or after WS-1?**
- Options: (a) push first (standing action from `~/.grok/AGENTS.md` — push at session end), (b) push after WS-1.
- Selection criterion: risk of losing work vs. clean commit history.
- Currently leads: (a) — `~/.grok/AGENTS.md` says push is pre-authorized standing policy; do it now to capture the umbrella handoff.

## Hard constraints

1. **Single-writer per handoff.** Per SKILL.md Hard Constraint #6, handoffs owned by session 019fc95d (`model-benchmark-dispatch-019fc95d`, `dispatch-paths-fallback-not-spawn-block-20260805`, `review-findings-fix-019fc95d-20260806`) cannot be mutated by this session (019ffd06). They are referenced as cross-references in this umbrella. **Operator directive:** the user explicitly asked to "update the old handoff files" — interpretation: this umbrella IS the update; appending revision blocks to 019fc95d's files requires a session that can claim them first. The umbrella captures all necessary updates.
2. **`tool_grounded_spawn_broken` list stays in `fleet-models.json`.** MBE-01 removes the hard exclusion in `is_available()`; the list itself remains as transport metadata. Do NOT remove the list.
3. **`serde_broken` and `learned_broken` stay as hard exclusions.** MBE-01 only changes `tool_grounded_spawn_broken` from hard to soft.
4. **Don't delete a handoff with remaining work.** Per operator directive in this session: every older handoff with a "Next steps" / "Pending decisions" section is preserved. `model-benchmark-dispatch-enhancement-20260803` is already `yaml:closed, work:CLOSED` — no action.
5. **PI prompts via stdin.** `subprocess.run(["pi", ..., prompt])` truncates to first line. Must use `input=prompt`. All PI benchmarks before 2026-08-11 invalidated.
6. **Don't burn `~/.grok` quota** by running all benchmarks at once. Re-run in phases by lane.

## Cross-reference couplings

- `P:/docs/handoffs/model-benchmark-dispatch-019fc95d/HANDOFF.md` (parent) → 4 revisions; this umbrella inherits and supersedes the open remaining-work items.
- `P:/docs/handoffs/dispatch-paths-fallback-not-spawn-block-20260805/HANDOFF.md` → 4 task packets; this umbrella's MBE-01..04 mirror them.
- `P:/docs/handoffs/review-findings-fix-019fc95d-20260806/HANDOFF.md` → 14 findings; this umbrella's MBE-05..07 cluster them.
- `P:/docs/handoffs/model-telemetry-integration/HANDOFF.md` → 7 skills; this umbrella's MBE-08..10 mirror them.
- `P:/docs/handoffs/model-benchmark-20260728/HANDOFF.md` → 7 decisions; this umbrella's MBE-14..19 mirror them.
- `P:/docs/handoffs/model-benchmark-pool-contracts-bridge-20260729/HANDOFF.md` → 3 validations; this umbrella's MBE-20..22 mirror them.
- `P:/docs/handoffs/telemetry-integration-20260724/HANDOFF.md` → older duplicate; this umbrella recommends close-as-superseded after WS-3 ships.
- `~/.grok/skills/model-benchmark/scripts/benchmark.py` → MBE-12 modifies `benchmark_model()` signature; MBE-13 calls it.
- `~/.grok/skills/model-quota/scripts/pick_model.py` → MBE-01/02 modify `is_available()` and `pick_model()`.
- `~/.grok/skills/model-quota/scripts/fleet-models.json` → MBE-04 adds `zen-deepseek-v4-flash-free`; MBE-11/13 write dispatch_latency.
- `~/.grok/skills/model-quota/scripts/fleet_quota.py` → MBE-06 modifies provider map and 429 parser.
- `~/.grok/hooks/scripts/uncertainty_gate.py` → MBE-05 modifies detection patterns.
- `~/.grok/skills/wiki-crawl4ai/crawl_to_qmd.py` → MBE-07 removes dead code.
- `~/.grok/skills/tp/SKILL.md` Step 2 → MBE-03 modifies dispatch logic.
- `~/.grok/config.toml` → MBE-14 caps Groq max_completion_tokens.
- `P:/.data/wiki/concepts/model-fleet-provider-pools.md` → MBE-18 updates fleet size.
- `P:/.data/wiki/concepts/dedicated-quota-first-dispatch-routing.md` → already exists; cites this umbrella's WS-1 rationale.
- `P:/.data/wiki/concepts/pi-cli-ignores-supports-developer-role-for-mistral.md` → exists; cited by MBE-13 root cause for Zen-PI re-run.
- This handoff's `accurate_as_of_head` → `48a327574395b7ba6a003b4f6e619496d3c791b7`. If HEAD moves, re-verify cited paths.

## Other outstanding streams (not handed off)

- **`P:/docs/handoffs/routing-library`** — OPEN, 2w old, DRIFT. Build `route.py` centralizing task-domain → model selection; wraps `spawn_subagent` + telemetry. Consumes the model-pool-selection-policy domain table. Adjacent, not in scope.
- **`P:/docs/handoffs/transport-aware-dispatch-design-20260802`** — OPEN, 10d old, DRIFT, checkpoint. Design doc complete (3 revisions). v3 schema decision not yet made. Adjacent.
- **`P:/docs/handoffs/sqlite-telemetry-backend`** — OPEN, 2w old, DRIFT. Replace JSONL telemetry with SQLite WAL-mode. Adjacent — would unblock scale beyond ~10K rows.
- **`P:/docs/handoffs/fleet-code-bugs`** — OPEN, 2w old, DRIFT. BUG-03: DeepSeek code-verification recommendation blocked by a bug. Adjacent.
- **`P:/docs/handoffs/model-selection-domain-index-20260809`** — OPEN, 4d old, DRIFT, claimed:grok. Organizes the broader model-selection domain; useful for context but not in scope here.
- **`P:/docs/handoffs/ship-py-pi-dispatch-and-quality-gate-gaps-20260810`**, **`ship-py-pi-dispatch-not-found-20260809`**, **`ship-py-pipeline-integration-gaps-20260810`** — ship-py integration gaps; touch `benchmark_runner.py` indirectly. Adjacent.
- **`P:/docs/handoffs/fleet-dispatch-improvements-20260731`**, **`cross-model-dispatch-improvements-20260801`**, **`tp-parallel-panel-dispatch-20260801`** — related dispatch improvements; out of scope.

## Explicit non-goals

- Do NOT remove `tool_grounded_spawn_broken` from `fleet-models.json` (only the hard-exclusion in `is_available()`).
- Do NOT change model selection logic in any skill (only add telemetry logging).
- Do NOT run the full benchmark in one session (use phased lane-by-lane runs).
- Do NOT remove `serde_broken` or `learned_broken` (only `tool_grounded_spawn_broken` becomes soft).
- Do NOT delete any handoff file with remaining work (operator directive in this session).
- Do NOT mutate handoffs owned by session 019fc95d from this session (single-writer constraint).
- Do NOT remove the `~/.grok` commits before pushing them.
- Do NOT add new providers to PI/OpenCode without verifying via `pi -p --provider <name> --model <id> "test"` first.

## Resumption protocol

1. **Read this handoff** (you're already doing that).
2. **Read `P:/docs/handoffs/dispatch-paths-fallback-not-spawn-block-20260805/HANDOFF.md`** — the smallest, highest-confidence packet (MBE-01..04).
3. **Run `/go implement MBE-01 through MBE-04`** — 60 min, fully scoped, unit-tested.
4. **Verify** with `pytest ~/.grok/skills/model-quota/scripts/test_pick_model.py -v` (16 tests must pass).
5. **Run `/check`** before declaring done — pick_model output shape change affects consumers.
6. **Update this handoff** with a Revision 5 block (current session's claim to it) reporting what shipped.

## Suggested next invocation

```
/go implement MBE-01 through MBE-04 from P:/docs/handoffs/model-benchmark-effort-20260813/HANDOFF.md
```

## Last user message (verbatim)

> /handoff for each workstream.  then create one handoff for the model-benchmark work.  update the old handoff files and cleanup.  don't delete a handoff file that still has other work in it.

## Epistemic labels

- [FACT] All factual claims above cite source paths in the Verified facts section. No claim is asserted without a file:line or session-id receipt.
- [INFERENCE] The recommended order in D1 (WS-1 first) is inferred from "smallest, highest-confidence packet" reasoning, not operator-confirmed.
- [INFERENCE] The single-writer constraint interpretation in Hard Constraint #1 (umbrella as the update) is inferred from SKILL.md Hard Constraint #6 + the operator's literal request to "update the old handoff files"; the operator may have intended to override the constraint, in which case this handoff should be followed by an explicit override.
- [UNKNOWN] Whether the operator wants to commit/push the umbrella handoff immediately or accumulate it for batch push. The standing action says push at session end; this handoff itself is a session-end artifact.
- [UNKNOWN] Whether `telemetry-integration-20260724` should be closed as superseded by `model-telemetry-integration` (D3). The operator's literal request was "cleanup" but did not specify close-superseded.

## Suggested skills for next session

- **`/go`** — 22 task packets ready to execute across 7 workstreams; MBE-01..04 is the highest-confidence starting point.
- **`/check`** — verify pick_model output shape didn't break consumers after MBE-01/02 (DP-03 acceptance test).
- **`/handoff close`** — after WS-3 ships, close `telemetry-integration-20260724` as superseded.
- **`/review --focus maintainability`** — after WS-1 ships, audit the new `spawn_limitation` field for caller correctness.
- **`/wiki`** — capture the "tool_grounded_spawn_broken as metadata not exclusion" pattern as a durable concept (already partially captured in `dedicated-quota-first-dispatch-routing.md`; could be promoted to its own concept).

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-13T23:30 | 019ffd06-0d7f-7f21-98fc-6117652ba7e3 | created — consolidates 4 active + 3 older model-benchmark workstreams into single umbrella; 22 task packets |
