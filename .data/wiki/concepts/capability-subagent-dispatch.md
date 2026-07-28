---
title: "Capability: subagent-dispatch — design notes and consumer analysis"
created: 2026-07-28
source: session-2026-07-28
tags: [capability-node, subagent, spawn, model-pool, skill-graph, phase-2]
summary: >
  Design notes for the subagent-dispatch capability. The lean contract is at
  capabilities/subagent-dispatch.md. This page documents why the node exists,
  the 5+ skills that duplicate the dispatch procedure, and how each customizes
  it with glue.
agent: grok
host: grok
relations:
  - target: capabilities/subagent-dispatch.md
    type: contract-for
  - target: wiki/concepts/capability-node-architecture.md
    type: instance-of
  - target: wiki/concepts/model-pool-not-chain.md
    type: grounds
---

# subagent-dispatch: design notes

## The contract

Lean operational page: `P:/.data/wiki/capabilities/subagent-dispatch.md`
Contains: inputs, outputs, 5-step procedure (wiki query, criteria, exclusions,
spawn, telemetry). No prose.

## Why this node exists

5+ skills each implement their own version of "spawn a fresh subagent from a
model pool, handle failure gracefully, record telemetry." Each duplicates:
the wiki query for pool candidates, the criteria checklist, the hard
exclusions table, the fallback logic, and the inline disclosure. When a new
model is added or removed from the pool, all copies need updates.

## Consumers (identified from frontmatter + lexical analysis)

| Skill | Glue (how they customize dispatch) |
|-------|-------------------------------------|
| `/tp` | Passes protocol.md, extracts ~500 token context bundle, verification synthesis with spot-check gate |
| `/review` | Writes findings to run_dir JSON, spawns per-lens specialists, verify pass is a separate agent |
| `/check` | Spawns per-concern verifiers with evidence packets, merges verdicts |
| `/debrief` | 5 parallel lens subagents + verifier + critic, automated model-tier routing |
| `/model-benchmark` | Sends standardized prompts to each fleet model in parallel |
| `/www` | Dispatches parallel M3 research subagents (context firewall pattern) |
| `/grok-parallel` | Fans out independent work across worktree-isolated subagents |

## The procedure being extracted

The core dispatch logic (Steps 2a–2 from /tp SKILL.md):

1. **Wiki query** for pool candidates (grep model-tool-calling-capability-matrix)
2. **Criteria application** (real-prompt reliability, lane, cost, diversity)
3. **Hard exclusions** (kimi-k3 cost, nemotron serde)
4. **Pool spawn** (try in order, record results, break on success)
5. **Inline fallback** with mandatory disclosure if all fail
6. **Telemetry** via log_spawn.py

The capability node defines this sequence once. Skills add their own:
- Prompt construction (what the subagent is asked to do)
- Context bundle contents (what verified facts to include)
- Result handling (verification gate, findings JSON, verdict merge)
- Tool access specification (capability_mode)

## Falsifier

Obsolete when Grok Build adds native model-pool support to spawn_subagent
(eliminating the need for the wiki-query-then-try pattern). Until then,
the manual pool logic is the only path to fresh-lens dispatch.
