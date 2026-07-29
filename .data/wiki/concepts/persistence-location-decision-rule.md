---
title: "Persistence-location decision rule: durable vs throwaway output"
created: 2026-07-29
source: session-2026-07-29 (operator caught two persistence-location errors)
tags: [persistence, tmp, durable-storage, decision-rule, agent-behavior, output-management]
summary: >
  When an agent generates output that costs API calls, LLM inference, or
  significant time to reproduce, persist it to a durable tracked location
  (P:/.data/wiki/, P:/.agents/scripts/, or git-tracked docs) — never P:/tmp/.
  P:/tmp/ is gitignored and gets wiped. The rule: if reproduction cost > 0,
  the output is reference data, not throwaway. Operator caught this twice in
  one session: first "P:/tmp gets deleted," then "are you throwing
  classifications away?"
agent: grok
host: grok
cognitive_load: 1
verification: operator-corrected (2x same session)
relations:
  - target: ~/.grok/AGENTS.md § "No deferred persistence"
    type: refines
  - target: wiki/concepts/context-firewall-architecture.md
    type: related
---

# Persistence-location decision rule

## The rule

**If output costs API calls, LLM inference, or significant time to reproduce → persist durably. Never to P:/tmp/.**

P:/tmp/ is gitignored and subject to cleanup. Output placed there will be lost.

## The decision tree

```
Output generated
  │
  ├── Is it a temp file consumed in the same turn? (e.g., a script that runs and is done)
  │     → P:/tmp/ is correct
  │
  ├── Does it cost API calls / inference / >30s to reproduce?
  │     → DURABLE: P:/.data/wiki/capabilities/, P:/.agents/scripts/, or git-tracked docs
  │
  ├── Is it reference data someone might query later?
  │     → DURABLE
  │
  └── Is it a log or evidence artifact?
        → P:/.claude/hooks/.evidence/ or P:/.artifacts/ (terminal-scoped)
```

## What triggered this rule (2026-07-29)

Two operator catches in one session, same underlying assumption:

1. **First catch:** I proposed saving LLM skill classifications to `P:/tmp/skill_classifications.json`. Operator: "why do we want to save to P:/tmp? you'll just delete them."

2. **Second catch:** After I dropped the save entirely, operator: "are throwing skill_classifications.json away? don't you want that somewhere else?"

The first catch corrected the location. The second catch corrected the overreaction (dropping persistence entirely instead of choosing a durable location). Both were right.

**Root pattern:** I defaulted to throwaway locations for data that was actually reference material. The classifications cost 18.5s of Mistral API calls to produce — they're not throwaway.

## What counts as "costs to reproduce"

| Output type | Reproduction cost | Location |
|---|---|---|
| LLM classification results | 18.5s + API calls | `P:/.data/wiki/capabilities/` |
| Benchmark telemetry data | Minutes of model calls | `P:/.data/` (tracked) |
| Skill graph output | <5s (pure code) | Rebuild on demand — no persistence needed |
| Search results from /web | Seconds (free DDG) | Inline only — no persistence |
| Wiki concept drafts | LLM reasoning | `P:/.data/wiki/concepts/` (tracked) |
| Handoff documents | Session knowledge | `P:/docs/handoffs/` (tracked) |
| Discovery audit JSON | Script run (<10s) | `P:/tmp/` OK (cheap to re-run) |

## The overreaction trap

When the operator corrects a persistence-location choice, the fix is to **choose a better location**, not to **drop persistence entirely**. Dropping entirely loses the data a second time.

This is the same anti-pattern as "the operator said the fix was wrong, so I reverted the finding." The correction targets the implementation, not the goal.

## Relationship to "No deferred persistence" (AGENTS.md)

AGENTS.md § "No deferred persistence" says: when you state intent to persist something, the write must happen in the same response. This rule refines it: *where* you persist matters as much as *when*. Writing to P:/tmp/ is technically "persistence" but functionally is not — the data will vanish.
