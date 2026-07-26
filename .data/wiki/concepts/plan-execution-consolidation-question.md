---
title: "Plan execution consolidation question (execute-plan / executing-plans vs /go)"
created: 2026-07-26
source: session-2026-07-26 (skill catalog audit)
tags: [plan-execution, consolidation, go, execute-plan, executing-plans, open-question]
host: both
agent: grok
---

# Plan execution consolidation question

## The question

`execute-plan` (bundled skill: PR DAG executor with worktree isolation + orchestrator review) and `executing-plans` (superpowers: checkpoint-based execution) overlap with `/go`'s implementation waves. Should they consolidate into `/go`?

## Why this is NOT urgent

- No friction reported from having three execution paths
- Each serves a different mechanism: PR DAG (execute-plan), checkpoint review (executing-plans), inline waves (/go)
- Consolidating would destroy the PR-DAG mechanism that /go doesn't have
- The question arose during a catalog audit, not from real-use friction

## Trigger for revisiting

Surface this concept when:
- Real friction appears from choosing between execution paths
- `/go` gains a PR-DAG mode (making execute-plan redundant)
- A user reports confusion about which execution skill to use

## Sources

- Preflight audit 2026-07-26 (no conflicts, no competing plans)
- Skill catalog audit (operator noticed 3 plan-execution skills)
