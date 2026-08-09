---
title: "Delegation Decision Rule: Context-Dependency, Not Just Quota"
created: 2026-07-30
source: session-20260730
tags: [delegation, orchestrator, model-selection, context-management, decision]
summary: >
  The decision to delegate work off the orchestrator (GLM-5.2) is governed by
  whether the work product needs to live in the orchestrator's working memory
  — not just by quota isolation. Delegate when the output is a self-contained
  artifact (file written, test run, search results) that can be summarized back
  without losing decision-relevant signal. Keep on the orchestrator when the
  reasoning process must inform future turns or when the operator needs to see
  the evolution in real time. Over-isolating the orchestrator destroys its
  value: the accumulated context IS the orchestrator's strength.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - Operator directive, session 20260730 — "we don't want to over-isolate the orchestrator"
relations:
  - target: wiki/concepts/delegation-optimization-chunking-output-backend-discipline.md
    type: refines
  - target: wiki/concepts/model-role-assignment-public-vs-custom-benchmarks.md
    type: extends
  - target: wiki/concepts/execution-path-based-model-routing.md
    type: related
---

# Delegation Decision Rule: Context-Dependency, Not Just Quota

## Decision context

Session 20260730 explored when and why to use different models than the
orchestrator (GLM-5.2). The initial framing was quota isolation: GLM has
~1600 calls per 5h window, every tool call burns one, so delegate to
preserve quota. But the operator corrected: **"probably don't want to over-
isolate the orchestrator. We do want to delegate for certain when we don't
need context for the task outcome to progress in the orchestrator's memory."**

This is a more precise rule than "delegate to save quota." It reframes
delegation as a **context-management decision**, not a quota-conservation
tactic. The orchestrator's value IS its accumulated context — stripping
work out of that context without reason destroys the property that makes
GLM-5.2 the right orchestrator (Tau2 #1 on multi-turn coherence).

## The decision rule

**Delegate when ALL of:**
1. The output is a **self-contained artifact** (file written, test passed/failed,
   search results gathered, code implemented) — not a reasoning process
2. The work product can be **summarized back** to the orchestrator without
   losing decision-relevant signal (the orchestrator needs the *result*, not the
   *process*)
3. The work **won't inform future turns** in ways that require the reasoning
   chain to be in conversation memory

**Keep on orchestrator when ANY of:**
1. The reasoning process must inform the next decision (iterative development
   where each step's outcome shapes the approach)
2. The operator needs to **see the evolution** in real time (debugging,
   design iteration, exploring tradeoffs)
3. The task needs **conversation history** that only the parent has
4. The output is a **durable knowledge artifact** (wiki concept, handoff, ADR)
   where quality and contextual grounding matter

## Worked examples from session 20260730

| Task | Delegate or keep? | Why |
|------|-------------------|-----|
| Writing `fleet_quota.py` line-by-line with iterative fixes | **Keep** (even though quota-expensive) | Each fix informed the next decision; operator was watching the evolution; reasoning needed in context |
| Running `ruff check` 15 times | **Delegate** | Each ruff result is self-contained; orchestrator needed only "clean" or "N errors"; the process doesn't inform future turns |
| `/www` research subagents | **Delegate** (already is) | Search results are self-contained artifacts; summarized back as structured findings |
| Writing a wiki concept | **Keep** | Durable artifact where quality + contextual grounding matter; the reasoning chain shapes the content |
| Parallel exploration (grep, read, list across files) | **Delegate** | Read-only scanning; results are summarizable; context firewall benefits from separation |
| Decomposing a task into subtasks | **Keep** | Orchestration reasoning; Tau2 #1 matters here |

## Why over-isolation is the failure mode

The temptation (observed this session) is to treat delegation as pure
quota optimization: "move everything possible off GLM to preserve quota."
This is wrong because it ignores the second condition of the rule: **the
work product must be summarizable without losing decision-relevant signal.**

When the orchestrator delegates iterative development — where each step's
outcome determines the next step's approach — the subagent returns a final
artifact, but the orchestrator has lost the reasoning chain that produced
it. If the operator then asks "why did you structure it this way?" or
"change the approach," the orchestrator has to re-read the file to
reconstruct what it would have known if it had done the work inline.

The counter-failure: doing everything inline (the actual failure this
session) burns quota on mechanical work (running linters, fixing test
assertions) where the orchestrator genuinely doesn't need the process in
memory. The right balance is task-dependent, guided by the three
conditions above.

## Relationship to quota isolation

Quota isolation remains a valid **secondary** reason to delegate — but it
should never be the **primary** driver. The primary driver is whether the
task needs to live in orchestrator context. If it does, quota cost is
acceptable (that's what GLM quota is for). If it doesn't, delegation is
correct — and the quota savings are a bonus, not the reason.

See [[delegation-optimization-chunking-output-backend-discipline]] for the
HOW of delegation (chunking, routing, structured output, backend selection).
This concept answers the prior question: WHEN to delegate at all.

## What this means for our workspace

- Skills that dispatch subagents should frame the decision as
  context-management, not quota-conservation
- The orchestrator should NOT reflexively delegate all code writing —
  iterative development where the reasoning chain matters stays on the
  parent. Pure "write to spec" or "run until passing" work delegates.
- The spawn gate and quota cache infrastructure built this session
  ([[execution-path-based-model-routing-grok-build]]) remains valid as mechanical
  enforcement — it prevents wasted spawns on exhausted/serde-broken models
  regardless of the delegation decision
- Pool contracts ([[coding-model-pool-tier-1-tier-2]],
  [[mechanical-model-pool]]) remain the source of truth for which model to
  use when delegation IS appropriate

## Falsifier

This rule is wrong if:
- Telemetry shows that delegating iterative development (violating the rule)
  produces outcomes the operator rates as good — meaning the context-loss
  penalty is smaller than assumed
- Quota exhaustion becomes so frequent that even context-dependent work MUST
  be delegated to avoid session-stopping — meaning quota isolation overrides
  context-management as the binding constraint
- A future Grok Build feature (e.g., `updatedInput` on PreToolUse) enables
  transparent model injection that preserves context while using a different
  model — making the delegation decision moot

## Receipts

- Operator statement: "probably don't want to over-isolate the orchestrator.
  But we do want to delegate for certain when we don't need context for the
  task outcome research development or can progress to be in the orchestrator
  memory" (session 20260730)
- Session evidence: inline `fleet_quota.py` development was 20+ turns of GLM
  quota — but each fix informed the next decision, so keeping it on the
  orchestrator was context-appropriate despite quota cost
- Session evidence: 15× `ruff check` runs were NOT context-appropriate —
  self-contained results that could have been a delegated subagent
