---
title: "Role-by-Role Delegation: What the Orchestrator Keeps vs Delegates"
created: 2026-07-30
source: session-20260730
tags: [delegation, orchestrator, model-selection, roles, reference]
summary: >
  Reference table for which task roles stay on the orchestrator (GLM-5.2) vs
  which delegate to subagents. Governed by context-dependency (not just quota
  isolation) and task-fit (validated by operator experience — M3 as orchestrator
  is maddening). The orchestrator's value IS its accumulated context; over-
  isolation destroys that value.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - Operator directive, session 20260730
relations:
  - target: wiki/concepts/delegation-decision-rule-context-dependency.md
    type: extends
  - target: wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md
    type: extends
  - target: docs/designs/2026-07-30-quota-aware-model-routing.md
    type: related
---

# Role-by-Role Delegation: What the Orchestrator Keeps vs Delegates

## Decision context

Session 20260730 explored in detail what roles the orchestrator should keep
vs delegate. The operator asked directly: "What tasks does the orchestrator
invoke? Planning, coding, searching, researching, other? You tell me." This
reference table captures the answer durably.

## Roles that stay on the orchestrator (GLM-5.2)

| Role | Why it must be GLM-5.2 |
|------|----------------------|
| Intent interpretation | Needs conversation context only the parent has |
| Task decomposition | Tau2 #1 — the whole point of using GLM as orchestrator |
| Framing decisions | "Is this the right approach?" — the operator's thought partner role |
| Composing subagent results | Needs full context to integrate divergent findings |
| Writing durable artifacts | Wiki concepts, handoffs, ADRs — quality matters, context matters |

## Roles that delegate to subagents

| Role | Why different | Model pool | Selection basis |
|------|--------------|------------|-----------------|
| Code review / critique | Same-model reviewing its own work is same-lens. Cross-family diversity catches more. | Critic pool | Task-fit (diversity) + quota isolation |
| Code implementation | Any decent coding model works. GLM quota better spent orchestrating. | Coding pool (free: or-ling-3-flash-free, nim-openai-gpt-oss-20b) | Quota isolation primarily |
| Web research / search | Search-then-summarize is mechanical. No reasoning depth needed. | Mechanical pool | Quota isolation |
| Parallel exploration | Read-only scanning (grep, read, list). Fast, cheap models do this fine. | Mechanical pool | Quota isolation + parallelism |
| Formatting / structured output | M3 is IFBench #1 globally. For JSON, tables, strict constraint adherence. | minimax-m3 | Task-fit (IFBench #1) — the one role where M3 genuinely wins |
| Cross-model second opinion | The entire point is a different lens. GLM reviewing GLM defeats it. | /agy (Gemini), /codex (GPT-5), /mmx (MiniMax) | Task-fit (diversity is the product) |
| Mechanical bulk work | Format conversion, extraction, classification, running linters. | Mechanical pool | Quota isolation |

## The judgment-call role

| Role | Decision |
|------|----------|
| **Deep reasoning subagent** | For /tp critique: use a fresh-lens model (different family from parent). For /why root cause: use GLM-5.2 itself (strongest analysis needed). |
| **Iterative code development** | Keep on orchestrator if each step informs the next (per [[delegation-decision-rule-context-dependency]]). Delegate if it's "write to spec" or "run until passing." |

## Execution path selection

When delegating, three execution paths are available (not just spawn_subagent):

| Path | Best for | Model control | Overhead |
|------|----------|---------------|----------|
| `spawn_subagent` with model | Read-only exploration, research | Explicit model param | ~26K AGENTS.md context injection |
| `opencode run --model=X` | Write-capable implementation, tool-rich tasks | Model flag | Owns context management |
| `mmx text chat --model=X` | Mechanical bulk, formatting | Model flag | Chat-only, no file access |
| `agy run` / `codex` | Cross-model second opinion | Per-CLI config | Separate quota pools |

The orchestrator should pick the execution path based on task type, not
default to spawn_subagent reflexively. See
[[execution-path-based-model-routing-grok-build]] for the full architecture.

## What this means for our workspace

- GLM-5.2 is the orchestrator. Do not switch to M3 for orchestration
  (operator experience: "M3 drives me nuts as orchestrator").
- Delegation discipline is the primary quota conservation lever — not the
  spawn gate (which is reactive), not the injector (which is a nudge).
- Pool contracts contain the judgment context for model selection. The
  orchestrator reads them before spawning; the gate catches violations
  after.
- The delegation decision rule governs when to delegate at all
  (context-dependency), separate from which model to delegate to (pool
  contracts).

## Falsifier

This table is wrong if:
- Telemetry shows that specific delegated roles (e.g., code implementation)
  produce worse outcomes than the orchestrator doing them inline — meaning
  task-fit doesn't hold for that role at our scale
- A future Grok Build feature (updatedInput on PreToolUse) makes the
  execution-path selection moot by enabling transparent model injection

## Receipts

- Operator statement: "What tasks does the orchestrator invoke? planning,
  coding, searching, researching, other? you tell me" (session 20260730)
- Operator statement: "M3 drives me nuts as an orchestrator" (session 20260730)
- Pool contracts: `P:/.data/wiki/capabilities/{coding,reasoning,mechanical,critic}-model-pool.md`
- Delegation rule: `P:/.data/wiki/concepts/delegation-decision-rule-context-dependency.md`

## Related concepts

- [[delegation-decision-rule-context-dependency]] — the when-to-delegate rule this table operationalizes
- [[delegation-optimization-chunking-output-backend-discipline]] — the how-to-delegate rules (chunking, routing, structured output)
- [[model-role-assignment-public-vs-custom-benchmarks]] — why GLM-5.2 is orchestrator and M3 is not
- [[execution-path-comparison-spawn-opencode-pi-cli]] — which execution path to use for each delegated task
- [[execution-path-based-model-routing-grok-build]] — the three-layer architecture
