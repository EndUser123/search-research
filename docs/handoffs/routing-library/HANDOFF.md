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
