---
title: "Todo-triage-insight skill separation: CRUD vs analysis vs discovery"
created: 2026-08-13
source: packages/.chat_exports/2026-08-10_-_Research_Evaluation_and_Feedback
tags: [skill-design, skill-separation, todo, triage, insight, architecture-decision, task-management, routing]
agent: grok
host: both
cognitive_load: 2
verification: workspace_verified
summary: >
  Todo (task CRUD), triage (analytical prioritization), and insight (discovery
  scanning) are separate concerns that should be separate skills backed by a
  shared task store. Separation gives cleaner routing, independent evaluation,
  and swappable backends. On this workspace, the separation manifested as:
  /todo (mechanical scanner + parallel /insight+/aar subagents), /insight
  (transcript-depth 10-category scan), and /triage (review of session output).
  The /todo Step 0.5 integration (parallel subagents) bridges the discovery
  gap: the operator no longer needs to remember to run /insight separately.
relations:
  - target: wiki/concepts/discover-first-prompt-patterns-for-unbiased-work-item-discovery.md
    type: source
  - target: wiki/concepts/proactive-improvement-opportunity-scanner.md
    type: extends
  - target: wiki/concepts/work-discovery-skill-organization-best-practices.md
    type: complements
  - target: wiki/concepts/scanner-to-handoff-gap-discovered-work-not-persisted.md
    type: related
---

# Todo-triage-insight skill separation: CRUD vs analysis vs discovery

## Decision context

**The question:** should "todo" and "triage" be in the same skill, different
skills, or MCP servers? The operator asked this during the Perplexity research
session that designed the workspace's work-discovery architecture.

**The decision:** keep them as separate skills, backed by a shared task store
(on this workspace: handoffs are the only cross-session persistence).

## The three concerns

| Concern | What it owns | Core tool | Test type |
|---------|-------------|-----------|-----------|
| **TODO (CRUD)** | Creating, updating, listing tasks | `create_task`, `update_task`, `list_tasks` | Data invariants, integration |
| **TRIAGE (analysis)** | Reading tasks/findings, scoring impact & confidence, detecting blockers/risks, reordering backlog | Prompt patterns (discover-first, categorize, bias-check) | Ranking quality, bias metrics, discover-first behavior |
| **INSIGHT (discovery)** | Scanning transcript/context for improvement opportunities the operator hasn't noticed | 10-category scan with evidence anchoring | Coverage (did it find what /aar found?), signal-to-noise |

## Why separate them

1. **Different lifecycle and tests.** TODO is CRUD — test data invariants and
   integration. Triage is analytic — test ranking quality and bias metrics.
   Insight is discovery — test coverage and false-positive rate. Keeping them
   apart lets you iterate and evaluate independently.

2. **Clearer routing.** Discovery agents produce findings. Triage consumes
   findings and existing tasks, then calls TODO to create/update. This matches
   the planner/critic vs executor pattern.

3. **Swappable backends.** The task store can be handoffs (Grok Build), a
   future MCP server (SQLite, JSON), or an external tool (Jira, Todoist).
   Skills that speak to it are thin clients; the backend changes without
   rewriting the triage logic.

## How this manifested on the workspace

| Skill | Concern | Implementation |
|-------|---------|---------------|
| `/todo` | TODO + discovery | Mechanical scanner (16 sources) + parallel `/insight` + `/aar` subagents (Step 0.5) |
| `/insight` | INSIGHT | 10-category transcript scan, dual-stream routing (knowledge vs improvement) |
| `/triage` | TRIAGE | Review of session output for blockers, errors, inefficiencies, risks, opportunities |
| `/aar` | RETROSPECTIVE | Evidence-grounded session reconstruction with value accounting and opportunity discovery |

The `/todo` Step 0.5 integration (added session 019ffc5c) bridges the discovery
gap: `/todo` now spawns `/insight` and `/aar` as parallel background subagents,
merging their findings into the unified action list. The operator no longer
needs to remember to run `/insight` separately — `/todo` does discovery AND
CRUD in one invocation.

## The rejected alternative: one skill doing everything

**One skill (todo + triage + insight):**
- Pros: simpler to wire initially, one entry point
- Cons: harder to evaluate (was it a bad task, or bad prioritization, or bad
  discovery?), more coupled prompts, more chances for over-eager auto-CRUD,
  harder to swap backends

**Why rejected:** the three concerns have different testing methodologies. A
monolithic skill makes it impossible to isolate which layer failed when the
output is wrong. Separation enables independent evaluation.

## Falsifier

This is wrong if:
- The operator consistently invokes all three together and the separation adds
  only latency (merge them if they're always co-invoked)
- The task store is never swapped (the swappable-backend benefit is theoretical)
- Triage and insight produce the same findings (they're redundant, not
  complementary)

## Sources

- `packages/.chat_exports/2026-08-10_-_Research_Evaluation_and_Feedback/attachments/when looking at things to do, we have blockers, er.md` lines 886-960
- Session 019ffc5c: `/todo` Step 0.5 implementation

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[agent-reliability-patterns-and-production-validation]]
- [[ai-agent-systems-in-software-engineering]]
- [[refactor-as-comprehensive-optimization-analyzer]]

