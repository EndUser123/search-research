---
title: "LangGraph vs wrapper scripts for skill step enforcement — decision and rationale"
created: 2026-07-23
source: session-2026-07-23 (/www research on Lang* frameworks for skill instruction enforcement)
sources:
  - https://www.langchain.com/blog/langgraph
  - https://docs.langchain.com/oss/python/langgraph/graph-api
  - https://www.datacamp.com/tutorial/langchain-vs-langgraph-vs-langsmith-vs-langflow
  - https://abstractalgorithms.dev/from-langchain-to-langgraph-when-agents-need-state-machines
  - P:/.data/wiki/concepts/mandatory-step-enforcement-code-over-prose.md
tags: [langgraph, langchain, langsmith, state-machine, enforcement, skill-execution, wrapper-scripts, architecture-decision, prose-vs-code]
agent: grok
host: grok
verification: multi-source-verified
cognitive_load: 3
summary: >
  LangGraph's state-machine pattern (nodes = mandatory steps, edges =
  conditional transitions, shared state = persisted data) is the right
  architecture for enforcing step order during skill execution. We don't
  need the LangGraph framework to get the benefit — a Python script with
  the same node/edge structure achieves identical enforcement at 1% of
  the complexity. The gap is skills that dispatch to external models
  (red-team, /tp) where steps live in SKILL.md prose instead of code.
  Hooks are reactive (fire after), not proactive (can't enforce during).
  Wrapper scripts (like close_accounting.py) are proactive — they run
  their own logic and return results. This decision prevents future
  re-evaluation of Lang* frameworks for this use case.
relations:
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose
    type: extends
  - target: wiki/concepts/skill-enforcement-layers
    type: complements
---

## Decision context

**The problem:** Skills like /red-team and /tp have mandatory steps written in SKILL.md prose (e.g., "merge files before dispatching to agy"). The model skips these steps under context momentum — the exact failure mode documented in `mandatory-step-enforcement-code-over-prose.md`. We need a way to enforce step ordering during skill execution, not just catch violations afterward.

**Why this research was needed:** The operator asked whether Lang* frameworks (LangChain, LangGraph, LangSmith, LangServe) could solve the "skill not following its own instructions" problem. This page records the evaluation and decision so future sessions don't re-derive it.

## The Lang* family

| Tool | What it is | Relevance |
|---|---|---|
| **LangChain** | LLM workflow library — prompt chains, retrieval, tool calling | Low — it's a prompt-chaining framework, not a control-flow enforcer |
| **LangGraph** | State machine for agents — nodes, edges, conditional routing, shared state | **High** — directly addresses "force steps to execute in order" |
| **LangSmith** | Observability/tracing — logs every step, evaluates quality | Medium — detects skipped steps after the fact, doesn't prevent |
| **LangServe** | Deploys LangChain/LangGraph as APIs | Not relevant |

## Why LangGraph is the right pattern but not the right tool

**LangGraph's core mechanism** is exactly what we need:

- **Nodes** = mandatory steps (merge files → dispatch specialist → parse findings → route to critic)
- **Conditional edges** = "if findings file empty, re-dispatch; if non-empty, proceed"
- **Shared state** = run_dir, findings JSON, dispatch manifest — persisted between nodes
- **Checkpointing** = resume from last completed node if the run crashes

The step-skip problem disappears because the graph structure makes it **impossible to reach the critic node without passing through the specialist node**. The LLM doesn't choose to skip a step — the graph routing forces the transition.

**But we don't need the framework to get the benefit.** A Python script with the same node/edge structure achieves identical enforcement. This is how `close_accounting.py` works today: it runs its own gate logic (13 gates, conditional loop, state machine) and returns results. The skill calls one script, the script enforces the ordering, the LLM never gets a chance to skip a step.

## Why hooks aren't sufficient

Hooks (quality-gate Stop hook, close scanner) are **reactive** — they fire at the end of a turn or at session close. They detect violations after they happen:

- Quality-gate fires at Stop → detects "verification receipt stale" → blocks the response → but the un-merged agy dispatch already burned quota
- Close scanner fires at /close → detects "no AAR artifact" → blocks close → but the session already ran without AAR

**Proactive enforcement** requires code that runs *during* the skill's execution, between steps — not after. That's what wrapper scripts provide: they intercept the step transition (merge → dispatch) and enforce it structurally.

## The decision

**Chosen: wrapper scripts with state-machine structure, not LangGraph.**

| Criterion | LangGraph | Wrapper scripts |
|---|---|---|
| Enforces step ordering | ✅ | ✅ |
| Runs during skill execution | ✅ | ✅ |
| Complexity | Python framework + graph definition + state serialization + debugging surface | 20-50 lines per script |
| Dependency | `pip install langgraph` + langchain | None (stdlib only) |
| Integration with Grok Build | Would need to coexist with TUI's agent loop | Already proven (close_accounting.py, preprocessor.py) |
| Debugging | LangGraph's state graph + Grok's hook layer | Just the script + Grok's hook layer |

The wrapper-script approach is already deployed and proven:
- `close_accounting.py` — 13-gate state machine for /close
- `full_preprocessor.py` — pipeline with 11 stages for /aar
- `merge_files.py` — file merger for cross-model dispatch
- `validate_disconfirmation.py` — structural validator for /www and /tp

Each is ~20-100 lines of Python, uses stdlib only, and structurally enforces what prose instructions cannot.

## The gap that remains

Skills that dispatch to external models (red-team → agy/codex/mmx, /tp → spawn_subagent) still have their step ordering in SKILL.md prose. The next wrapper script to build is `dispatch_cross_model.py` — takes file paths + brief + model slug, internally merges files, dispatches via the appropriate CLI, parses output. The LLM calls one command; the script enforces merge-before-dispatch structurally.

## What was explored and ruled out

- **LangGraph framework** — right pattern, wrong tool for this environment (adds framework complexity without solving anything the wrapper pattern doesn't already solve)
- **LangChain** — prompt chaining, not control flow
- **LangSmith** — observability layer, could detect skipped steps but can't prevent them
- **LangServe** — deployment, not enforcement
- **Hooks only** — reactive, not proactive; catch violations after they cost quota

## Falsifier

If wrapper scripts prove insufficient (too many skills need them, maintenance burden grows, or the ordering logic becomes too complex for simple scripts), reconsider LangGraph. The trigger: ≥5 wrapper scripts enforcing step ordering across different skills, with shared patterns that a framework would simplify.
