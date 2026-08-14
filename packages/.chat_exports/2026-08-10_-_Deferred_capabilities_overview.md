# 2026-08-10 - Deferred capabilities overview

- **Created:** 8/13/2026, 7:43:43 AM
- **Exported:** 8/13/2026, 7:43:45 AM
- **Messages:** 4
- **Source:** browser_extension

---

## #1 · user

Selected text

## #2 · assistant

That deferred work is where the system evolves from **"a safe interactive delegation tool"** into **"an autonomous delegation infrastructure."** It is also where the complexity increases significantly.

Here's how I would break it down.

| Capability | Current state | Deferred capability |
| --- | --- | --- |
| Interactive delegation | ✅ Live | — |
| One bounded worker | ✅ Live | — |
| Parent verification | ✅ Live | — |
| Automatic resume | ❌ | Deferred |
| Cancellation | ❌ | Deferred |
| Fleet telemetry | ❌ | Deferred |
| Multiple concurrent workers | Limited | Deferred |
| Long-running orchestration | Limited | Deferred |

## 1. Resume

Right now the flow is essentially:

```
Parent
    ↓
launch worker
    ↓
wait
    ↓
worker returns
```

If the parent dies, closes, crashes, or loses its session, the conversation is effectively over.

A resume system would instead create durable execution state:

```
Parent
    ↓
create task record
    ↓
launch worker
    ↓
persist state
    ↓
Parent crashes
```

Later:

```
new parent
    ↓
discover task
    ↓
reconnect
    ↓
continue
```

That sounds simple, but it requires solving questions like:

- 
Which worker owns the task?

- 
Is it still alive?

- 
Has it already finished?

- 
Has another parent already resumed it?

- 
Are artifacts complete or partially written?

Those are distributed-systems problems.

## 2. Cancellation

Interactive cancellation is easy.

```
Ctrl+C
```

Real cancellation isn't.

Suppose MiniMax is halfway through editing.

What should happen?

```
cancel
```

Does that mean:

- 
kill immediately?

- 
let it finish current file?

- 
preserve worktree?

- 
delete worktree?

- 
archive artifacts?

- 
release provider reservation?

A robust cancellation protocol needs explicit states.

For example:

```
Running

↓

Cancel Requested

↓

Worker acknowledges

↓

Cleanup

↓

Cancelled
```

rather than

```
kill process
hope for the best
```

## 3. Telemetry

Today you know:

> 
the task succeeded

Telemetry asks much richer questions.

For example:

```
How often does MiniMax timeout?

Average runtime?

Average tokens?

Average retries?

Failure rate?

Prompt size?

Verification pass rate?

Cost?
```

Eventually you want dashboards like:

```
MiniMax

92% success

5% timeout

3% schema failure

18 sec average

$0.001 average cost
```

versus

```
DeepSeek

81%

12% timeout
```

Without telemetry you're routing based mostly on intuition.

With telemetry you can optimize objectively.

## 4. Batch execution

Currently:

```
Task A

↓

wait

↓

Task B
```

Batch orchestration would allow:

```
Task A

Task B

Task C

Task D

↓

collect

↓

verify

↓

merge
```

Now you have issues like:

- 
concurrency limits

- 
provider quotas

- 
scheduling

- 
dependency graphs

- 
retries

- 
starvation

- 
prioritization

## 5. Fleet management

Right now you're essentially managing one worker.

Eventually you might have:

```
MiniMax

DeepSeek

Qwen

llama.cpp

OpenAI

Claude
```

all executing simultaneously.

Now you need:

```
Who is busy?

Who is idle?

Which provider is down?

Who timed out?

Who exceeded quota?
```

That's a fleet.

## Why it was deferred

I think this was the right decision.

Your current implementation answers the foundational questions first:

- 
Can the parent generate good packets?

- 
Can workers execute them?

- 
Are results structured?

- 
Can the parent verify them?

- 
Is worktree isolation safe?

- 
Are contracts enforced?

Those are prerequisites.

Only after those are solid does it make sense to add orchestration features. Otherwise you'd be automating an unreliable process.

# One addition I'd put on the roadmap

There's one capability I think deserves to be elevated ahead of large-scale fleet management:

## Delegation Memory

Instead of only tracking *running* tasks, track *historical performance*.

For every delegation, record something like:

```
{
  "task_type": "mechanical_edit",
  "worker": "MiniMax M3",
  "duration": 18,
  "tokens": 7400,
  "verification": "pass",
  "review_comments": 1,
  "retry": false,
  "timeout": false
}
```

After a few hundred delegations, the router can make evidence-based decisions:

- 
"MiniMax has a 97% first-pass rate on boilerplate edits."

- 
"DeepSeek times out on verification-heavy tasks."

- 
"Zen is consistently fastest for read-only extraction."

- 
"llama.cpp performs well on local refactors but struggles with large architectural changes."

That lets routing improve based on real outcomes rather than static heuristics. It also fits well with your emphasis on evidence and verification: the router isn't just making decisions—it can explain *why* it chose a worker, backed by observed performance rather than assumptions.

## #3 · user

yes good idea, please do that.

## #4 · assistant

Done.

I've created a Codex handoff that turns this into a concrete implementation task rather than just an architectural idea.

The implementation is intentionally scoped to **evidence collection only**. It does **not** change routing decisions yet. That separation is important because it lets you accumulate trustworthy data before teaching the router anything.

The handoff requires the implementing agent to:

- 
Add durable **Delegation Memory** to the live `codex-external-delegation` package.

- 
Record one append-only history entry per delegation attempt.

- 
Capture:

- 
task type/class

- 
selected worker/provider/model

- 
duration

- 
timeout/retry/failure class

- 
result-contract status

- 
verification outcome

- 
worktree/scope outcome

- 
token/cost values **only if actually reported**

- 
artifact and task identifiers

- 
Define:

- 
writer

- 
storage location

- 
reader/query interface

- 
authority

- 
freshness rules

- 
failure behavior

- 
retention policy

- 
Ensure telemetry failures never hide successful task execution.

- 
Add recovery and corruption handling.

- 
Add tests for:

- 
successful execution

- 
worker failures

- 
timeouts

- 
malformed telemetry

- 
duplicate/concurrent task IDs

- 
partial-write recovery

- 
absence of invented metrics

- 
Add a reporting command that summarizes historical performance by model and task type (success rate, timeout rate, median duration, verification pass rate).

- 
Require verification using the actual CLI/runner path, not only unit tests.

One refinement I'd recommend after this lands is a **Phase 2** that turns the history into a true decision engine. Rather than just storing telemetry, it would calculate rolling reliability scores and confidence intervals, allowing the router to make evidence-based choices such as:

- 
"MiniMax M3 has a 98% first-pass verification rate for mechanical edits."

- 
"DeepSeek succeeds on extraction tasks but exceeds timeout targets on verification."

- 
"llama.cpp has become more reliable over the last 100 runs than its long-term average."

At that point, routing can gradually move from static rules to adaptive rules backed by measured performance, while still allowing you to inspect exactly *why* a particular worker was selected. That, in my view, is where the system starts becoming genuinely self-improving without relinquishing human control.
