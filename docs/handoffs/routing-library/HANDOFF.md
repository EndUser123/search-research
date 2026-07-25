---
thread_id: routing-library-2026-07-24
parent_handoff_path: none
current_session_id: 019f91d3-2741-7f83-af68-211796180474
current_terminal_id: console_b7ba7bf3-2403-437a-b44a-c5c9
produced_at: 2026-07-24T19:35:00Z
status: open
handoff_type: architectural
accurate_as_of_head: non-git-session
---

# Routing library: route.py for domain-driven model dispatch

## Objective

Build a routing library that centralizes task-domain → model selection, telemetry logging, and fallback — so every skill calls `route.spawn()` instead of bare `spawn_subagent`, and the domain table becomes a live control surface instead of wiki documentation.

## Status

OPEN — design identified, not started. The `/check` skill has a proof-of-concept `model=` parameter (shipped this session), but no routing library exists yet.

## Producing context

- Date: 2026-07-24
- Session: 019f91d3-2741-7f83-af68-211796180474
- Origin: red-team root cause RC-1 (domain table unenforced, amplified × 5 across specialists)

## Read-first list

1. `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md` — the domain table this library reads
2. `P:/.grok/skills/check/SKILL.md:140-155` — proof-of-concept: `/check` now passes `model="zen-deepseek-v4-flash-free"` to spawn_subagent
3. `C:/Users/brsth/.grok/skills/model-benchmark/scripts/telemetry.py` — the `log_spawn()` function the library wraps
4. `C:/Users/brsth/.grok/skills/go/SKILL.md:234-249` — `/go`'s reconciliation note (domain table is SoT; /go lanes are internal simplification)

## Verified facts

- [FACT] `/check` SKILL.md line 146 now includes `model="zen-deepseek-v4-flash-free"` in the spawn_subagent call (shipped + verified this session)
- [FACT] No other skill in the fleet passes `model=` to spawn_subagent (grep confirmed, red-team WF-4)
- [FACT] `/go` has its own two-lane model selection system that does not reference the domain table (red-team WF-3)
- [FACT] The domain table has 7 rows mapping task domains to default models with fallbacks
- [FACT] `spawn_subagent` accepts a `model` parameter (Grok Build ≥ v0.2.98, documented in `/go` SKILL.md L329)

## Current state

- Domain table exists as wiki documentation (`model-pool-selection-policy-speed-quota-diversity.md`)
- `/check` has proof-of-concept model routing (manual, not library-driven)
- `/go` has a reconciliation note pointing to the domain table
- No routing library exists
- No skill other than `/check` uses the domain table

## Task packets

### RT-01: Build route.py core

- **Goal:** Create `P:/.agents/scripts/models/route.py` that maps task_domain → model + calls spawn_subagent + logs telemetry
- **In scope:** the library module, domain table as TOML/Python dict, spawn wrapper, telemetry wrapper
- **Out of scope:** per-skill integration (RT-02)
- **Files:** `P:/.agents/scripts/models/route.py`
- **API design:**
  ```python
  from route import spawn_for_domain
  result = spawn_for_domain(
      domain="code-verification",
      description="Verify: KSC core",
      subagent_type="general-purpose",
      capability_mode="execute",
      background=True,
      prompt=<path-only prompt>,
  )
  # Internally: looks up domain table → picks model → spawn_subagent → log_spawn
  ```
- **Domain table source:** the table from `model-pool-selection-policy-speed-quota-diversity.md` lines 124-135, encoded as a Python dict or TOML at `P:/.agents/scripts/models/domain-table.toml`
- **Acceptance:** `spawn_for_domain("code-verification", ...)` dispatches to `zen-deepseek-v4-flash-free` with telemetry logged
- **Falsifier:** any domain that has no model mapping; or telemetry not logged; or model not passed to spawn_subagent

### RT-02: Integrate into /check (replace proof-of-concept)

- **Goal:** Replace `/check`'s manual `model=` with `route.spawn_for_domain()`
- **In scope:** `P:/.grok/skills/check/SKILL.md` Step 3 spawn block
- **Acceptance:** `/check` verifiers route through the library, not hardcoded model slugs

### RT-03: Integrate into /review, /www, /web, /wiki, /preflight

- **Goal:** Each skill's spawn_subagent calls use `route.spawn_for_domain()`
- **In scope:** 5 skills' spawn blocks
- **Out of scope:** `/go` (has its own wave-dispatch system; the reconciliation note is sufficient for now)
- **Acceptance:** all 5 skills route through the library

## Open decisions

- **Domain table format: Python dict in route.py, or separate TOML file?** Python dict is simpler (no parsing); TOML is more editable. Recommendation: Python dict initially, extract to TOML if it changes frequently.
- **Should the library handle fallback automatically?** If DeepSeek is down, should route.py automatically try MiMo, then M3? Recommendation: yes for the first fallback level; surface the fallback in telemetry.
- **Should /go use route.py?** /go's wave system is more complex (personas, effort levels). Recommendation: defer — /go's reconciliation note is sufficient for now.

### OD-04: Pool selection strategy (which model does the orchestrator pick from a multi-model pool?)

**The problem:** When a domain maps to a pool of multiple qualified models (e.g., code-verification → {nemotron, glm, inkling, mimo}), the routing library must decide WHICH one to dispatch to. The current /tp approach (try in fixed order: nemotron → glm → inkling → mimo) is a chain, not a pool — nemotron bears all calls and the others are never exercised.

**Candidate strategies:**

| Strategy | How it picks | Pro | Con | Data needed |
|----------|-------------|-----|-----|-------------|
| **Always-first (current)** | Fixed order, first available | Simple, predictable | One model bears all load; others never exercised; no quality comparison data | None |
| **Round-robin** | Cycle through pool members per dispatch | Spreads quota/load across providers; exercises all models; builds telemetry on each; provider-resilience (one outage doesn't kill all dispatches) | Might pick a slower model for time-sensitive tasks | None |
| **Quality-weighted** | Pick model with best historical quality_score for this domain | Routes to empirically best model per task type | Cold-start: no data for first N calls; needs telemetry integration first | Telemetry (quality_score per model per domain) |
| **Speed-weighted** | Pick fastest model for this domain | Minimizes latency | Might sacrifice quality | Telemetry (latency per model per domain) |
| **Quota-aware** | Pick model with most remaining quota in current window | Avoids rate limits | Needs live quota data (not available for most providers — only GLM and MiniMax have published per-5h limits) | Provider quota API or static limits from wiki |
| **Composite (quality × speed × quota)** | Weighted score combining all three | Optimal routing | Most complex; weights need tuning | All three data sources |

**Recommendation (initial):** Start with **round-robin** for these reasons:
1. Zero data dependency (works from first call, unlike quality-weighted or quota-aware)
2. Exercises all pool members, which builds the telemetry data needed to later upgrade to quality-weighted
3. Spreads quota usage across providers, reducing single-provider rate-limit risk
4. The wiki's cross-family diversity principle is preserved (pool members are already cross-family)

**Upgrade path:** after ~50 telemetry entries per model per domain, switch to quality-weighted or composite. The round-robin phase IS the data collection phase.

**Cold-start handling:** if a model has <3 data points for a domain, always include it in the rotation (even if quality-weighted would exclude it). This ensures every model gets minimum calibration data before being deprioritized.

### OD-05: Inkling delegation-only constraint

**The problem:** Inkling (Thinking Machines) produces garbage as a Grok Build interactive model ("UBS", "Savings") but works correctly via spawn_subagent delegation (2.9s, correct output) and direct API (Q=1.0 all benchmark tiers). The routing library must know that Inkling is valid for delegation but not for interactive use.

**Proposed mechanism:** add a `delegation_only = true` field to Inkling's domain table entry. The routing library respects this for spawn dispatch (includes it in pools) but the operator-facing model picker documentation should warn against selecting it as a primary model.

**tool-fallbacks.md already documents this** (committed 2026-07-24). The routing library should read tool-fallbacks.md or the domain table's delegation_only flag to exclude delegation-only models from any "suggested primary model" logic.

### OD-06: Cross-family diversity enforcement

**The problem:** random selection within a family does NOT decorrelate errors (wiki: `multi-agent-correlated-errors.md`). The routing library should ensure pool members are from different model families, not just different slugs from the same provider.

**Evidence from wiki:**
- `multi-agent-correlated-errors.md`: "Persona mutations don't change attention. Frame mutations change what each agent attends to."
- `llm-council-and-model-fusion.md`: "Prefer cross-family panel members over three clones of the same API."
- `ai-thought-partner-landscape-and-tp-improvements-2026.md`: "Same-model debate → degenerate consensus. Cross-model diversity is the fix." (Zhang et al 2025, 26 citations)
- `best-practices-enforcement-mechanism-grok-build.md`: "Same model family = correlated failure, not validation."

**Proposed mechanism:** the domain table tags each model with its family (NVIDIA, Zhipu, Thinking Machines, Xiaomi, Google, etc.). When multiple dispatches happen in parallel (e.g., /check spawns 3 verifiers), the routing library distributes them across families, not within one. Round-robin within a cross-family pool satisfies this automatically — the pool is already cross-family, and round-robin naturally spreads across families.

## Hard constraints

- The library must not break if telemetry is unavailable (same fail-open contract as extract.py)
- The library must not break if the domain table is missing a domain (fall back to parent-inherited model with a warning)
- The library must log every spawn to telemetry (this is the whole point — data accumulation)

## Cross-reference couplings

- `P:/.grok/skills/check/SKILL.md:146` — current proof-of-concept model= (will be replaced by route.py call)
- `P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md` — the domain table source of truth
- `C:/Users/brsth/.grok/skills/model-benchmark/scripts/telemetry.py` — the `log_spawn()` function
- Red-team root cause RC-1 (amplified × 5) — this library is the structural fix
- The telemetry integration handoff — route.py should log_spawn() internally, so it subsumes part of that handoff's scope

## Explicit non-goals

- Do NOT build a PreToolUse hook (the library approach is simpler and more inspectable)
- Do NOT modify /go's wave-dispatch system (reconciliation note is sufficient)
- Do NOT implement cascade/escalation logic here (that's the cascade handoff)

## Resumption protocol

1. Read the domain table from `model-pool-selection-policy-speed-quota-diversity.md:124-135`
2. Create `P:/.agents/scripts/models/route.py` with the domain → model mapping
3. Implement `spawn_for_domain()` that wraps `spawn_subagent` + `log_spawn`
4. Test: call `spawn_for_domain("code-verification", ...)` and verify model + telemetry

## Suggested next invocation

```
/go build P:/.agents/scripts/models/route.py — a routing library that maps task domains to models per the domain table in model-pool-selection-policy-speed-quota-diversity.md. Wraps spawn_subagent + telemetry. Then integrate into /check, /review, /www, /web, /wiki, /preflight.
```

## Last user message (verbatim)

> "/handoff please create for each open and paused workstream."

## Epistemic labels

- [FACT] All file paths verified this session
- [FACT] Domain table contents verified by reading the wiki
- [INFERENCE] 5 skills can be integrated in ~30 min each (mechanical swap of spawn_subagent → route.spawn_for_domain)
