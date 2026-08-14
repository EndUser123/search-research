---
title: "Orchestration engine decision: LangGraph for skill pipeline execution"
created: 2026-08-14
source: session-019ffc5c, chat_exports/2026-08-10_-_Kestra_For_LLM_Skills.md
tags: [decision, orchestration, langgraph, skill-pipeline, architecture, agentic-sdlc]
agent: grok
host: grok
cognitive_load: 2
verification: single-source-reasoned
summary: >
  LangGraph chosen as the orchestration engine for the workspace's skill
  pipeline. Selection criterion: maps directly onto the existing /go phase
  architecture (state + nodes + edges + conditional routing + checkpointing
  + interrupts), Python-native (no external server), and provides the
  deterministic enforcement layer that prose rules cannot. Rejected
  alternatives: Plain Python (insufficient enforcement), Kestra (external
  server, overkill for solo), Temporal (excessive complexity).
relations:
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
    type: implements
  - target: wiki/concepts/intent-mode-gated-auto-composition.md
    type: related
  - target: wiki/concepts/skill-step-enforcement-architecture-grok-build.md
    type: resolves
  - target: wiki/concepts/capability-node-architecture.md
    type: composes-with
---

# Orchestration engine decision: LangGraph

## Decision

**LangGraph is the orchestration engine for skill pipeline execution.**

## Selection criterion

Which mechanism most reliably forces the agent to follow the intended
engineering process (design → plan → implement → verify → review → ship),
while adding the least complexity for a solo operator?

## Why LangGraph

| Property | How it fits |
|----------|------------|
| **State + nodes + edges** | Maps directly onto `/go`'s phase architecture — each phase is a node, transitions are edges, state carries evidence between phases |
| **Conditional routing** | `validate_recon() → FAIL → back to recon` is a native LangGraph pattern, not prose |
| **Checkpointing** | Persistent `thread_id` recovers from last successful step after failure — potentially replaces custom session/run identity machinery |
| **Interrupts** | Human-in-the-loop approval for dangerous changes is first-class — state persists while waiting for operator |
| **Python-native** | No external server (unlike Kestra/Temporal); runs inside the existing workspace |
| **Deterministic enforcement** | Python decides whether `validate_recon()` happens, not the LLM — this is the structural fix for prose-rule decay |

## Rejected alternatives

| Alternative | Why rejected |
|-------------|-------------|
| **Plain Python (300-500 lines)** | Sufficient for a single pipeline but doesn't scale to multi-pipeline, multi-skill orchestration. No checkpointing, no interrupts, no state persistence across sessions. |
| **Kestra** | Strongest operational UI but requires an external server. Overkill for one operator. Better suited for 50+ workflows with operators watching dashboards. |
| **Temporal** | Durable workflow runtime with maximum reliability but maximum complexity. Designed for distributed systems at scale, not solo agent orchestration. |
| **n8n** | Visual workflow builder — good for integrations but not designed for evidence-backed state transitions or LLM-in-the-loop execution. |

## How it maps onto the existing architecture

```
USER GOAL
    ↓
CAPABILITY / SKILL GRAPH          ← what must happen? (capability nodes)
    ↓
LANGGRAPH ORCHESTRATION ENGINE    ← how do we execute? (THIS DECISION)
    ↓
MODEL ROUTER                      ← who does it? (existing model pools)
    ↓
TOOL / HARNESS                    ← Claude Code / Grok / PI
    ↓
EVIDENCE                          ← receipts, artifacts, test results
    ↓
GRAPH TRANSITION                  ← state advances or is denied
```

LangGraph replaces the prose-rule enforcement layer:
- Instead of AGENTS.md saying "you must validate recon before implementing"
- LangGraph's Python code checks `validate_recon()` returns PASS before allowing the `implement` node to execute
- The LLM cannot skip the check because it's in the graph, not in the prompt

## The bake-off recommendation

Before broad adoption, test 5-10 existing `/go` transitions encoded as a
LangGraph graph against the current prose-driven orchestration. Success =
measurably fewer skipped capabilities, invalid transitions, and premature
completions. The bake-off was proposed in the Kestra conversation and
remains the validation step before committing the full fleet to LangGraph.

## Steelman (rejected alternative)

Plain Python (300-500 lines) is the strongest rejected option. It's the
simplest baseline, adds no dependencies, and the operator could write it
in one session. LangGraph adds a dependency, a learning curve, and a new
conceptual layer. If the Python baseline passes the same bake-off tests,
it's the better choice by Occam's razor.

**Why the steelman doesn't win:** the operator has already invested heavily
in prose-rule enforcement (hooks, quality gates, Stop scripts) that
approximate what LangGraph provides natively. The prose layer has a ~50%
compliance ceiling under closure pressure. LangGraph's deterministic
enforcement breaks that ceiling structurally — the check runs in Python,
not in the LLM's attention. The dependency cost is justified by the
enforcement gain.

## Falsifier

This decision is wrong if:
- The LangGraph bake-off shows no improvement over plain Python for the
  same /go transitions (the dependency adds cost without benefit)
- LangGraph's checkpointing doesn't compose with the workspace's
  multi-terminal session isolation requirements
- The learning curve exceeds the time saved from replacing prose rules
- The agent finds ways to route around LangGraph's enforcement (e.g.,
  executing tools outside the graph)

## Sources

- `packages/.chat_exports/2026-08-10_-_Kestra_For_LLM_Skills.md` — the bake-off comparison
- `packages/.chat_exports/2026-08-10_-_Explain_Agentic_Skill_Graphs.md` — the layered architecture proposal
- `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md` — the SDLC lifecycle mapping
- `P:/.data/wiki/concepts/skill-step-enforcement-architecture-grok-build.md` — why prose enforcement has a compliance ceiling
- LangGraph docs: state, nodes, edges, persistence, interrupts (docs.langchain.com)
