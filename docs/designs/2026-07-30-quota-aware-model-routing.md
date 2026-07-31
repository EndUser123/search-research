# Design: Quota-Aware Model Routing for Fleet Subagent Dispatch

## Problem

GLM-5.2 is the orchestrator (Tau2 #1, best thought partner). It has ~1600 calls per 5h window. Every tool call — including mechanical work like running `ruff check` or formatting tables — burns one orchestrator call. When the window empties, work stops. Meanwhile, the fleet has free-tier models (OpenRouter, Zen, NIM, Google) and subscription models (MiniMax, OpenCode Go) on separate quota pools that are underutilized.

The system needed: (1) prevent wasted spawns on quota-exhausted or serde-broken models, (2) provide visibility into fleet quota state, (3) route subagent work to appropriate models while preserving orchestrator quota for orchestration.

## Architecture: three-layer enforcement

### Layer 1 — Proactive (UserPromptSubmit injector)

**Component:** `~/.grok/hooks/UserPromptSubmit_quota_availability.py`
**Registration:** `~/.grok/hooks/quota-availability-injector.json`

Fires on every user prompt. Reads the quota cache + fleet-models.json registry. If any provider is below 10% quota, injects `additionalContext`:

```
⚠️ Model availability: BLOCKED (do not spawn): OpenCode Go at 0%.
Low quota (prefer alternatives): Z.ai (GLM) at 20%.
Run `python ~/.grok/skills/model-quota/scripts/pick_model.py --list` for best available models per lane.
```

When all providers are healthy, produces no output (silent — no context bloat).

**Backout:** delete `quota-availability-injector.json`

### Layer 2 — Enforcement (PreToolUse spawn gate)

**Component:** `~/.grok/hooks/PreToolUse_spawn_model_gate.py`
**Registration:** `~/.grok/hooks/spawn-model-gate.json`
**Matcher:** `spawn_subagent|Task`

Intercepts every `spawn_subagent` call. Two checks:

1. **Serde-broken check:** model slug is in SERDE_BROKEN set (read from `fleet-models.json` registry + `learned-serde-broken.json`). These models crash on spawn with serialization errors. Blocked with deny message naming the issue + recommended alternatives.

2. **Quota-exhausted check:** model's provider is below 10% in the quota cache. Blocked with deny message showing lane-aware fallbacks from the registry.

Both checks include cache expiry: error-hook marks older than 1 hour are ignored (provider may have recovered).

**Backout:** delete `spawn-model-gate.json`

### Layer 3 — Reactive (PostToolUseFailure error learner)

**Component:** `~/.grok/hooks/PostToolUseFailure_spawn_quota.py`
**Registration:** `~/.grok/hooks/spawn-quota-error-gate.json`
**Event:** PostToolUseFailure

When a spawn fails with a rate-limit error (429, "quota exceeded", "rate limit", "RESOURCE_EXHAUSTED"), marks that provider as 0% in the quota cache via `fleet_quota.py --update-provider <id> 0`.

When a spawn fails with a serde error ("missing field 'id'", "serialization error"), adds the model to `learned-serde-broken.json` with a 24h TTL.

**Backout:** delete `spawn-quota-error-gate.json`

## Infrastructure

### Quota cache

**Path:** `~/.cache/opencode/fleet-quota-cache.json`

Maps provider IDs to `{pct, updated, source, reset_ts}`. Written by `fleet_quota.py --write-cache` and updated by error hooks via `--update-provider`. Read by both the spawn gate and the UserPromptSubmit injector.

Provider ID mapping (model slug prefix → provider):

| Prefix | Provider ID |
|--------|------------|
| `go-*` | opencode-go |
| `or-*` | openrouter |
| `nim-*` | (no quota API — free tier) |
| `zen-*` | (free — never blocked) |
| `minimax-*` | minimax |
| `glm-*` | zai |
| `gpt-5-6-*` | codex-bridge |
| `groq-*` | groq |
| `grok-*` | (host model — N/A) |

### fleet_quota.py

**Path:** `~/.grok/skills/model-quota/scripts/fleet_quota.py`

Single script covering all providers. Renders a grouped dashboard (LLM / Search / Platform) with progress bars and timezone-aware reset times. Supports:
- `--write-cache` — writes quota cache from live data
- `--update-provider <id> <pct>` — targeted update from error hooks
- `--llm` / `--search` — category filtering
- Timezone detection (Mountain Time for this host)

Sources: opencode-quota (Google, MiniMax, Z.ai, OpenCode Go, Copilot) + direct APIs (OpenRouter, SerpAPI, Tavily, Firecrawl, GitHub, ElevenLabs).

### Scheduled cache refresh

Every 30 minutes, a scheduled task runs `fleet_quota.py --write-cache` (full opencode-quota refresh). Keeps the cache fresh without operator intervention. The scheduler is registered via `scheduler_create`.

### Pool contracts (source of truth for model selection judgment)

Four pool contract files at `P:/.data/wiki/capabilities/`:
- `coding-model-pool.md` — tier-1: or-ling-3-flash-free, mistral-medium-latest, nim-openai-gpt-oss-20b
- `reasoning-model-pool.md` — tier-1: glm-5-2; backup: zen-deepseek-v4-flash-free
- `mechanical-model-pool.md` — tier-1: or-ling-3-flash-free, nim-openai-gpt-oss-20b, minimax-m3 (formatting)
- `critic-model-pool.md` — code review + adversarial + cross-model

Pool contracts contain: benchmark data, known issues (serde, spawn compatibility), quota recovery speed, fallback rationale. These are the judgment layer — they tell the orchestrator *why* each model is tier-1.

### pick_model.py (availability checker, NOT selector)

**Path:** `~/.grok/skills/model-quota/scripts/pick_model.py`

Returns first available tier-1 model for a lane, filtered by quota cache + serde set. **Deliberately not wired into skills** — reverted after testing. The picker is an availability checker; pool contracts are the selector. The picker removes judgment from the process; the pool contracts preserve it.

### fleet-models.json (machine-readable registry)

**Path:** `~/.grok/skills/model-quota/scripts/fleet-models.json`

4 lanes × 2 tiers. Each model entry includes: provider, spawn_broken flag, serde_broken flag. Read by the spawn gate and pick_model.py.

## Delegation decision rule (governs when to use a different model)

**From wiki concept `delegation-decision-rule-context-dependency.md`:**

Delegate when ALL of:
1. Output is a self-contained artifact (file written, test run, search results)
2. Work product can be summarized back without losing decision-relevant signal
3. Work won't inform future turns in conversation memory

Keep on orchestrator when ANY of:
1. Reasoning process must inform the next decision
2. Operator needs to see the evolution in real time
3. Task needs conversation history only the parent has
4. Output is a durable knowledge artifact (wiki, handoff, ADR)

The dual basis for model selection: **task-fit** (validated by operator experience — M3 as orchestrator is maddening, GLM-5.2 is effective) + **quota isolation** (GLM has ~1600 calls/5h, delegate mechanical work to preserve quota for orchestration).

## What was tried and reverted

1. **pick_model.py wired into 5 skills** (commit 261f0ac) — reverted (72ddee6). The picker's greedy first-available algorithm removed task-fit judgment from the process. Pool contracts contain richer context (benchmark data, known issues, fallback rationale) that the picker can't reason about.

2. **SPAWN_OK set in the gate** — removed. The SPAWN_OK list conflated "serde-compatible" (a gate concern) with "recommended" (a routing concern). LLMs reading the deny message saw it as a recommendation list. Gate now only blocks, never recommends.

3. **Throttle zone (10-25%)** — removed. The throttle added a 60s cooldown between spawns to a near-limited provider. Replaced with failover: when a provider is below 10%, recommend specific equivalent models on free providers (e.g., go-deepseek-v4-flash → zen-deepseek-v4-flash-free).

4. **caut (Rust usage tracker)** — evaluated, uninstalled. Returns zero usable quota data on Windows. Doesn't discover OpenCode credentials. Only unique feature (Codex/Claude JSONL cost tracking) is irrelevant since we use Grok Build.

5. **WorkWeave Router proxy** — evaluated, not deployed. Can't intercept Grok Build's spawn_subagent. Would only help if we used opencode as a subagent execution backend. The proxy pattern is the industry standard but works at a layer Grok Build doesn't expose.

## Data flow

```
Scheduled task (30 min) → fleet_quota.py --write-cache → quota cache JSON
Operator runs /model-quota → fleet_quota.py → dashboard + cache update
                                                                     ↓
UserPromptSubmit hook reads cache → injects availability context
                                                                     ↓
Orchestrator picks model (reads pool contract for judgment)
                                                                     ↓
spawn_subagent called → PreToolUse gate reads cache + serde set
                         ↓                          ↓
                    provider >10% → ALLOW    provider <10% → DENY + lane fallback
                         ↓
              spawn fails with 429 → PostToolUseFailure hook
                         ↓
              fleet_quota.py --update-provider <id> 0
                         ↓
              cache shows 0% → future spawns blocked
```

## Files

| File | Role |
|------|------|
| `~/.grok/hooks/PreToolUse_spawn_model_gate.py` | Spawn gate (serde + quota check) |
| `~/.grok/hooks/spawn-model-gate.json` | Gate registration |
| `~/.grok/hooks/PostToolUseFailure_spawn_quota.py` | Error learner (quota + serde) |
| `~/.grok/hooks/spawn-quota-error-gate.json` | Error hook registration |
| `~/.grok/hooks/UserPromptSubmit_quota_availability.py` | Proactive injector |
| `~/.grok/hooks/quota-availability-injector.json` | Injector registration |
| `~/.grok/skills/model-quota/scripts/fleet_quota.py` | Dashboard + cache writer |
| `~/.grok/skills/model-quota/scripts/pick_model.py` | Availability checker |
| `~/.grok/skills/model-quota/scripts/fleet-models.json` | Model registry |
| `~/.grok/skills/model-quota/scripts/test_fleet_quota.py` | 29 tests |
| `P:/.data/wiki/capabilities/coding-model-pool.md` | Coding pool contract |
| `P:/.data/wiki/capabilities/reasoning-model-pool.md` | Reasoning pool contract |
| `P:/.data/wiki/capabilities/mechanical-model-pool.md` | Mechanical pool contract |
| `P:/.data/wiki/capabilities/critic-model-pool.md` | Critic pool contract |
| `P:/.data/wiki/concepts/execution-path-based-model-routing-grok-build.md` | Architecture concept |
| `P:/.data/wiki/concepts/delegation-decision-rule-context-dependency.md` | Delegation rule |
| `P:/.data/wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md` | Selection basis |

## Backout plan

Each layer is independently removable by deleting its JSON registration file:

| Remove | Effect |
|--------|--------|
| `quota-availability-injector.json` | No proactive injection (Layer 1 off) |
| `spawn-model-gate.json` | No serde/quota blocking (Layer 2 off) |
| `spawn-quota-error-gate.json` | No error learning (Layer 3 off) |
| `scheduler_create` task | No auto-refresh (manual /model-quota only) |

Removing all three JSON files returns to pre-session behavior. The scripts, cache, and pool contracts remain on disk but are never invoked.

## Falsifier

This architecture is wrong if:
- The spawn gate's deny-and-redirect pattern (one extra round-trip per blocked spawn) costs more than the quota it saves
- The quota cache staleness window (30 min between refreshes) causes the gate to block recovered providers or allow exhausted ones frequently enough to matter
- Pool contracts are ignored by the orchestrator (behavioral compliance fails), making the whole system depend solely on the mechanical gate — which can only block, not select

**Measurable falsifier (from /tp critique):** Over a 14-day observation window, instrument two counters: (a) orchestrator calls consumed per 5h window, and (b) spawns blocked by the gate for quota reasons (not serde). If (a) never exceeds ~50% of 1600 AND (b) is zero, both the quota-protection and the routing are solving non-problems.

**Delegation math falsifier:** Count, per delegation, the subagent's internal tool calls. If the median is ≤2, the "delegation preserves quota" premise is empirically false for the majority of delegations (delegation saves N-1 orchestrator calls; for N≤1 it's quota-neutral or net-negative).

## Known limitations

1. **Parent model is fixed per session.** Cannot switch GLM-5.2 to M3 mid-session. The only lever is behavioral: delegate mechanical work to subagents.
2. **CLI tools (agy, codex, mmx, opencode) are outside the gate.** The gate intercepts spawn_subagent only. CLI tool model selection is governed by the skills (/agy, /codex, /mmx) and the operator directive.
3. **No `updatedInput` support.** Grok Build PreToolUse hooks can only allow or deny — cannot modify tool arguments. Seamless model injection is impossible. The deny-and-redirect pattern is the closest approximation.
4. **Quota cache is only as fresh as the last refresh.** Between scheduled runs, the gate may use stale data. The error-hook (Layer 3) provides reactive updates to close the gap.
5. **Pool contracts are behavioral.** The orchestrator may or may not read them before spawning. The gate catches the worst failures; pool contracts improve the average case.

## Key decisions

1. **Pool contracts are the selector; pick_model.py is the availability checker.** The picker was wired into skills and reverted because its greedy algorithm removed task-fit judgment. Pool contracts contain benchmark data, known issues, and fallback rationale — richer context for judgment calls.

2. **Gate only blocks, never recommends.** The SPAWN_OK set was removed because LLMs interpreted it as a recommendation list. The gate's job is enforcement; the pool contracts' job is recommendation.

3. **Failover, not throttle.** When a provider is below 10%, recommend specific equivalent models on free providers — don't add a cooldown delay. The user has free-tier alternatives for every model family.

4. **Error hooks learn both quota AND serde.** The PostToolUseFailure hook marks providers as exhausted (1h TTL) AND learns new serde-broken models (24h TTL). Self-correcting system — no manual updates needed when new models break.

5. **Three independent layers with independent backout.** Each layer is a separate JSON file. Remove any one without affecting the others. This is the easy-backout design.

## Critique findings (from /tp fresh-lens review)

A fresh subagent critiqued this design doc and returned REVISE verdict. The findings:

### Finding 1: This is spawn protection, not routing

The title says "Routing" but the design has zero mechanical task-fit enforcement. 100% of the infrastructure enforces quota; 0% enforces task-fit. Calling pool contracts "the selector" is a category error — a document the system cannot enforce is a recommendation, not a selector. The honest framing: this is "Quota-Aware Spawn Protection." Routing requires a selection mechanism; this design has only a blocking mechanism plus a reading-compliance hope.

### Finding 2: Layer 1 (UserPromptSubmit injector) may be redundant

If behavioral compliance is reliable (LLM reads the injector), then the LLM is reliable enough to read pool contracts directly — making the injector redundant. If compliance is unreliable (LLM ignores the injector), the gate (Layer 2) catches the failure anyway. Layer 1 only earns its keep if it converts would-be-blocked spawns into never-attempted ones — saving one round-trip. That hasn't been measured. **Action:** instrument blocked-spawn counts before/after Layer 1 deployment.

### Finding 3: Delegation math doesn't always work

Delegation saves (N-1) orchestrator calls where N = subagent's internal tool calls. For multi-step work (N=8), saves 7 calls. For single-step work like `ruff check` (N=1), saves 0 — it's a wash with added latency. The delegation decision rule gates on output shape, not on whether delegation is quota-positive. **Action:** instrument subagent step counts to validate the quota-saving premise.

### Finding 4: Pool contracts pre-date this design

The four pool contracts existed before this session. This design added quota infrastructure and cited the pre-existing pool contracts as "the other half" of a dual basis. The design contributes nothing to task-fit enforcement — it only adds quota infrastructure. The dual-basis framing is post-hoc.

### Where the critic was wrong

The critic claimed quota exhaustion is "theoretical and unverified." It's verified — the operator hit "Usage limit reached for 5 hour" earlier this session (2026-07-31 01:35:01 UTC reset). GLM-5.2 runs through the Z.ai API, and the 5h window DID empty. The premise is sound.

### Verdict: REVISE

The blocking half (Layers 2+3) is sound and worth shipping. The "routing" framing should be corrected. The instrumentation gaps (blocked-spawn counts, delegation step counts) should be added to validate the system is solving real problems.
