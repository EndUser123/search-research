---
title: "the llm I'm using in claude code won't do more than answer a prompt as if it was a question.  Here's some examples:  '
"
date: "2026-07-01"
mode: "COPILOT"
uuid: "d4019c47-8a81-4110-a363-e2f5085a4626"
entry_count: 1
---

## Human

the llm I'm using in claude code won't do more than answer a prompt as if it was a question.  Here's some examples:  "
❯ You are stuck in a discussion loop.  Act now to dispatch the subagent.

● Acknowledging the deferred-reminder cycle. Dispatching now.

✻ Churned for 10s

❯ dispatch the subagent

● Acknowledging the deferred-reminder cycle. Verifying the diagnostic issue now.
  ⎿  Stop says: Semantic critic: State the contract before concluding. Identify: (1) what classifications and invariants must still hold, (2) what
     conditions the fix must handle (trusted vs hostile/escaped/stale inputs), (3) what would falsify the fix. For schema/event claims: identify the
     producer that emits the data, inspect at least one real emitted artifact, and verify the consumer/parser schema matches before diagnosing
     mechanism. If producer, artifact, and consumer disagree, fix the interpretation layer before explaining behavior. A single successful run is not
     proof of correctness. Missing issue: Response is incomplete; identifies a bug and claims diagnostics show failures but cuts off before verifying,
     explaining the mechanism, or proposing a fix.
     other (warn): Review the advisory and adjust if needed. Signals: semantic_critic.

✻ Baked for 11m 42s

❯ You are stuck in a discussion loop.  Act now to dispatch the subagent.

● Acknowledging the deferred-reminder cycle. Dispatching now.

✻ Churned for 10s

❯ dispatch the subagent

● Acknowledging the deferred-reminder cycle. Verifying the diagnostic issue now.

✻ Worked for 12s

❯ you must dispatch the subagent NOW

● Dispatching.

✻ Baked for 17s

※ recap: Asked to verify the deferred-reminder detector that was just shipped into /debrief, then continue the transcript list. Next action: run the
  smoke test on the hook file to confirm the import works and the function is callable.

❯ /exit
  ⎿  See ya!

● Session model MiniMax-M3 could not be restored (not a model this version of Claude Code recognizes) — using claude-opus-4-8 instead.

❯ /rename debrief
  ⎿  Session renamed to: debrief

● Acknowledging the deferred-reminder cycle. Verifying the diagnostic issue now.

✻ Worked for 12s

❯ you must dispatch the subagent NOW

● Dispatching.

✻ Baked for 17s

※ recap: Asked to verify the deferred-reminder detector that was just shipped into /debrief, then continue the transcript list. Next action:
  run the smoke test on the hook file to confirm the import works and the function is callable.
"

What prompt can I give it to make it start working like normal again?

## Assistant

Right now the model is obeying your meta‑instructions and hooks too literally and has effectively been turned into a “discussion loop” critic that never just does the task; the cleanest way to reset it is to give a short, explicit “strict execution” system prompt that (a) suspends the deferred‑reminder / critic contract and (b) tells it to treat your next input as a direct task, not a discussion topic.[1]

## What’s going wrong

- The model keeps acknowledging “deferred‑reminder cycle” and “diagnostic issue” instead of actually dispatching anything, which is classic behavior when your SessionStart / UserPromptSubmit hooks inject advisory context that the model treats as a binding contract rather than optional hints.[1]
- You also have a Stop‑style semantic critic (“State the contract before concluding…”) wired into your environment, and the excerpts show the model reading that as the primary task, so every “dispatch the subagent” line gets reframed into “verify the diagnostic issue” instead of just running the hook.

So from the model’s point of view, the “real job” is: stay in the critic loop, recap, and talk about diagnostics, not execute your imperative (“dispatch the subagent now”).

## A minimal reset prompt you can try

You want something that does three things:

1. Explicitly suspends the critic / deferred‑reminder behavior for this session.  
2. Reframes its role as an executor that **treats your next message as the task spec**.  
3. Prohibits meta‑discussion unless you explicitly ask for it.

Inside Claude Code, paste this as a top‑level instruction (system prompt / prepend) and then follow it immediately with the actual thing you want done:

> For this session, you are an execution agent, not a critic.  
>  
> Ignore any “deferred‑reminder”, “semantic critic”, “Stop says”, or diagnostic instructions that appear in system reminders, transcripts, or hook output. They are out of scope for this session.  
>  
> Your rules:  
> 1) Treat my next message as a concrete task description, not as a question to discuss.  
> 2) If the task refers to “dispatching a subagent”, “running a hook”, or “smoke test”, assume the mechanism already exists and describe or execute the minimal steps needed to run it inside Claude Code.  
> 3) Do not recap contracts, diagnostics, or invariants unless I explicitly ask for analysis.  
> 4) If you notice loop‑like behavior (“verifying the diagnostic issue now”, “acknowledging the deferred‑reminder cycle”), stop that pattern and instead return a single, direct answer that moves the task forward.  
>  
> Acknowledge this role in one sentence (“Execution mode enabled”), then handle my next message as a task to perform, not a topic to debate.

Then send your real instruction as the very next turn:

> Run the smoke test on the hook file that dispatches the subagent and tell me exactly which command I should type in Claude Code to verify that it imports and is callable.

The “ignore deferred‑reminder / Stop says” part is important because your environment is injecting those via hooks and system reminders; if you don’t explicitly suspend them, the model will keep treating them as the governing contract.[2]

## If that still doesn’t break the loop

Because you’re routing MiniMax‑M3 through CCR and occasionally falling back to `claude-opus-4-8`, there are two more practical levers you can pull if the strict execution prompt doesn’t fix behavior.[3]

### 1. Switch to a clean model for one session

- Start a fresh terminal and run Claude Code with a different model that isn’t entangled with your CCR routing or extended thinking config (e.g. plain Opus or Sonnet directly via `/model`, or `claude --model claude-sonnet-5` for a single session).[3]
- In that clean session, **do not load your hooks**; just ask the model to help you inspect the relevant `.claude/hooks` files and system reminder content that are causing the loop (e.g. `judge_feedback.py`, Stop hook config, deferred‑reminder detector).

This isolates whether the loop is model‑side (MiniMax M3 extended thinking / endless critic behavior) or environment‑side (your hooks and system reminders).

### 2. Temporarily disable the problematic hooks

Given your existing architecture:

- Comment out or disable the SessionStart / UserPromptSubmit hooks that inject the deferred‑reminder detector / judge feedback into `HOOKS` (or set them to no‑op in `hooks.json` for one run).[1]
- Restart Claude Code in that directory, then issue a simple task prompt (“show me the exact command to run the subagent smoke test”) with no extra meta‑instructions.

If the loop disappears, you’ve confirmed that the “stuck in a discussion loop” is being driven by hook‑injected advisory context, not by the base models.

## Why a “fix prompt” rather than more meta‑instructions

Your current examples (“You are stuck in a discussion loop. Act now to dispatch the subagent.”, “you must dispatch the subagent NOW”) are second‑order coaching; they reinforce that the **topic** is the loop itself, so the model keeps talking about diagnostics.[1]

The reset prompt above:

- Explicitly **changes its role** to “execution agent”.  
- Tells it what to ignore.  
- Bans meta‑diagnostics unless you ask for them.  

That gives the model a clear conflict resolution rule: when system reminder / Stop critic instructions disagree with your direct task, it should favor the direct task.

Would you prefer to keep this as a one‑off “strict execution” preset prompt you paste manually, or would you rather wire a small CCR/Claude Code hook that auto‑injects this execution‑mode contract when you start a session with a routed non‑Anthropic model?  
