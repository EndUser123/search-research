---
title: "Agent consolidation in parallel workflows: group by capability need, not by topic"
created: 2026-08-01
source: session-2026-07-31 (close-check 9→3 agent consolidation)
tags: [workflow, agent-design, consolidation, parallel, rate-limit, model-routing, design-decision, grok-build]
host: grok
agent: grok
verification: single-source-verified
cognitive_load: 2
relations:
  - target: wiki/concepts/command-wrapper-pattern-for-workflows.md
    type: related
  - target: wiki/concepts/context-firewall-architecture.md
    type: related
summary: >
  When designing parallel workflows, consolidate agents by what they need
  (mechanical: run commands + parse output; judgment: reason about context)
  rather than by topic (one agent per check). 9 topic-based agents → 3
  capability-based agents: mechanical sweep (one agent, ~12 commands),
  wiki+fmea (bounded scope), judgment (transcript reasoning). Fewer spawns,
  no rate-limit collisions, faster runtime.
---

# Agent consolidation in parallel workflows

## Decision context

**Why this was needed:** the close-check workflow started with 9 agents
(one per check). 3 hit free-tier rate limits (429), 1 hit max_tokens
(948K from unbounded exploration), only 5 returned useful results.
Consolidating to 3 agents (grouped by capability) eliminated all failure
modes.

## The consolidation principle

**Group by capability need, not by topic.**

| Grouping | Agent count | Failure mode |
|----------|-------------|-------------|
| Topic-based (1 agent per check) | 9 | Rate limits, max_tokens, wasted spawns |
| Capability-based (mechanical vs judgment) | 3 | None observed |

### Capability groups

| Group | What it does | Provider | Why grouped |
|-------|-------------|----------|-------------|
| **Mechanical sweep** | Run 8-12 deterministic commands, parse output, classify findings | Free-tier A | All commands have known output shapes; one agent runs them serially |
| **Wiki + bounded analysis** | Run validators + scoped file analysis | Free-tier B (different provider) | Bounded scope prevents max_tokens; different provider avoids rate collision |
| **Judgment** | Read transcript, reason about work streams and friction patterns | Inherited (session model) | The only reasoning task; needs session context |

## Why topic-based fails at scale

1. **Rate limits:** N agents on the same free-tier provider hit the per-minute
   cap simultaneously. Max safe concurrent on one provider: ~2-3.
2. **Max tokens:** an agent given open-ended scope ("check pipeline scripts")
   reads the entire repo (948K tokens, 21 tool calls). Bounded scope
   ("analyze ONLY these 3 files from git log") prevents this.
3. **Spawn overhead:** each agent costs startup + context-loading time.
   9 agents × ~60s average = 9 minutes. 3 agents × ~120s = 4 minutes.

## When NOT to consolidate

- Each check genuinely needs a different capability mode (execute vs read-only
  vs write) that can't coexist in one agent
- Checks have dependencies (check B needs check A's output) — though this
  argues for sequential, not for separate agents
- The checks are so complex that one agent can't hold all the output in context

## What this means for our workspace

1. **Default to 2-3 agents for parallel workflows**, not 9+. Group by
   capability, use multi-check schemas (each agent returns an array of
   check results).
2. **Bound every agent's scope in the prompt:** "analyze ONLY these files,"
   "do NOT read files outside this list."
3. **Mix free-tier providers:** max 2-3 concurrent agents per provider.

## Falsifier

This pattern is wrong if:
- Consolidated agents hit their own max_tokens from holding too much output
  (the multi-check schema means one agent's output is larger)
- Topic-based agents prove necessary because checks have conflicting
  capability needs that can't coexist

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| 9 agents: 3 failed with 429, 1 with max_tokens | Journal: seq 0,1,3 (429), seq 5 (max_tokens 948K) | [OBSERVED] |
| 3-agent consolidation: no failures | Not yet run in production — smoke check only | [UNKNOWN] |
| Free-tier rate limit: ~2-3 concurrent per provider | 4 of 7 OpenRouter agents failed; 3 succeeded | [INFERENCE] |

## Auto-related

- [[grok-build-workflows-rhai-orchestration]]
- [[skill-graph]]
- [[parallelizing-design-doc-generation-what-works]]
- [[skill-catalog]]
- [[parallel-safe-solution-decomposition]]

