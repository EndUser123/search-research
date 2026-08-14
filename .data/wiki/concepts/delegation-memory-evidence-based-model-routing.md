---
title: "Delegation memory: evidence-based model routing from historical performance"
created: 2026-08-13
source: packages/.chat_exports/2026-08-10_-_Deferred_capabilities_overview.md
tags: [delegation, model-routing, reliability, evidence-based, telemetry, adaptive-routing, fleet-management]
agent: grok
host: both
cognitive_load: 2
verification: workspace_verified
summary: >
  Track historical delegation performance per (task_type, worker_model) pair
  so the router can make evidence-based decisions instead of static heuristics.
  Phase 1 (evidence collection only) was scoped as a handoff; Phase 2 (rolling
  reliability scores → adaptive routing) is deferred until enough data
  accumulates. The prerequisite chain: workers execute reliably → results
  structured → parent can verify → worktree isolation safe → contracts enforced.
  Only then add orchestration features. "Automating an unreliable process
  produces unreliable automation."
relations:
  - target: wiki/concepts/model-delegation-cheap-models-for-code-edits.md
    type: extends
  - target: wiki/concepts/delegation-optimization-chunking-output-backend-discipline.md
    type: related
  - target: wiki/concepts/delegation-decision-rule-context-dependency.md
    type: related
---

# Delegation memory: evidence-based model routing from historical performance

## Decision context

**The problem:** model routing in the fleet uses static heuristics (model
preferences, known-good slugs, operator directives). These don't adapt to
observed performance. A model that worked well last month may have degraded;
a new model may be better for a task type than the default suggests. Without
historical performance data, routing decisions are guesses.

**The design:** record one append-only history entry per delegation attempt,
then (Phase 2) compute rolling reliability scores per (task_type, worker)
pair to let the router make evidence-based choices.

## The delegation record schema

```json
{
  "task_type": "mechanical_edit",
  "worker": "glm-5-2",
  "duration_seconds": 18,
  "tokens": 7400,
  "verification": "pass",
  "review_comments": 1,
  "retry": false,
  "timeout": false
}
```

Fields:
- **task_type** — mechanical_edit, read_only_extraction, verification_heavy,
  architectural_change, test_writing, etc.
- **worker** — the model slug that executed
- **verification** — pass / fail / partial (did the parent's verification
  gate accept the output?)
- **retry** — did the worker need a second attempt?
- **timeout** — did the worker exceed the timeout?

## Phase 1 (evidence collection — scoped)

Collect data without changing routing decisions. This separation is important:
it lets the system accumulate trustworthy data before teaching the router
anything. If routing changes are coupled with data collection, you can't
distinguish "the data was wrong" from "the routing logic was wrong."

Validation requirements for Phase 1:
- successful execution logged
- worker failures logged (with failure class)
- timeouts logged
- malformed telemetry detected and rejected
- duplicate/concurrent task IDs handled
- partial-write recovery (if the worker writes a file but crashes before
  reporting, the log entry should be reconstructed)
- **absence of invented metrics** — anti-gaming: the worker cannot self-report
  metrics; the parent's verification gate produces them

## Phase 2 (adaptive routing — deferred)

After enough data accumulates (~100 delegations per task_type per worker),
compute:
- **Rolling success rate** (last N delegations, not all-time)
- **Median duration** per task_type
- **Verification pass rate** per (task_type, worker)
- **Timeout rate** per worker

Then the router can make statements like:
- "MiniMax M3 has a 98% first-pass verification rate for mechanical edits."
- "DeepSeek succeeds on extraction but times out on verification."
- "llama.cpp has become more reliable over the last 100 runs than its
  long-term average." (trend detection, not just averages)

This moves routing from static rules to adaptive rules backed by measured
performance, while still allowing inspection of *why* a particular worker was
selected.

## The prerequisite chain

Before adding orchestration features (including adaptive routing):
1. Can workers execute them? (basic reliability)
2. Are results structured? (parseable output)
3. Can the parent verify them? (verification gate works)
4. Is worktree isolation safe? (no cross-session contamination)
5. Are contracts enforced? (hooks/gates fire)

Only after those are solid does adaptive routing make sense. Otherwise you're
optimizing routing to a set of unreliable workers — the router picks the
"best" worker for a task, but "best" is meaningless if all workers fail
unpredictably.

## Falsifier

This is wrong if:
- The historical data is too sparse to produce reliable scores (need ~100
  per task_type per worker for statistical confidence)
- Worker performance is not stable over time (drift makes historical data
  misleading — rolling window mitigates but doesn't eliminate this)
- The verification gate is unreliable (garbage-in: "pass" doesn't mean the
  work was actually good, making all metrics suspect)
- Gaming: workers adapt to maximize the recorded metrics rather than the
  actual task quality

## Sources

- `packages/.chat_exports/2026-08-10_-_Deferred_capabilities_overview.md` — the design conversation
- Related: `[[model-delegation-cheap-models-for-code-edits]]`, `[[delegation-optimization-chunking-output-backend-discipline]]`

## Auto-related

- [[skill-catalog]]
- [[agent-memory-systems]]
- [[llm-dreaming-memory-consolidation]]
- [[user-modeling-for-agentic-clis]]
- [[adaptive-expansion-evidence-triggered-conditional-steps]]

