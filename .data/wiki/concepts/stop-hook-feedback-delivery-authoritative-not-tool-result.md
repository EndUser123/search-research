---
title: "Stop-hook feedback delivery: authoritative user-prompt, not untrusted tool-result"
created: 2026-07-26
source: session-019f9d1f (/www research on Stop-hook self-correction loop)
sources:
  - https://news.ycombinator.com/item?id=47895029 (HN: "Claude 4.7 is ignoring stop hooks", 90+ comments)
  - https://www.arthur.ai/column/what-is-a-self-correction-loop-for-ai-agents (Arthur AI, Jun 2026)
  - https://www.agentic-patterns.com/patterns/stop-hook-auto-continue-pattern/ (Stop Hook Auto-Continue Pattern)
  - C:/Users/brsth/.grok/docs/user-guide/10-hooks.md (Grok Build hooks reference, lines 248-262)
  - Session 019f9d1f transcript (Stop-hook block observed and captured)
tags: [stop-hook, feedback-delivery, self-correction-loop, prompt-injection-defense, user-prompt, tool-result, agent-compliance, hook-mechanics]
agent: grok
host: grok
cognitive_load: 3
verification: directly-verified
summary: >
  When a Stop hook exits with code 2 + stderr, Grok Build delivers the stderr
  text to the agent as a `<user_query>` continuation prompt — the authoritative
  instruction channel, NOT as an untrusted tool-result. This means the model
  SHOULD treat Stop-hook feedback as binding instruction to act immediately,
  not as a suggestion to evaluate. When the agent stops and waits for the
  operator after a Stop-hook block, it is a behavioral failure (the model
  didn't follow the instruction), NOT a structural delivery problem. The
  HN thread "Claude 4.7 is ignoring stop hooks" was about JSON stdout
  delivery (which degrades to tool-result context); exit code 2 + stderr
  is the stronger mechanism that our quality_gate already uses. The fix is
  an AGENTS.md rule recognizing Stop-hook `<user_query>` as same-turn
  continuation instruction, not a code change to the delivery mechanism.
relations:
  - target: wiki/concepts/stop-hook-scope-binding-fix-design-decisions
    type: extends — that page documents scope-binding; this documents delivery mechanism
  - target: wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance
    type: applies — the principle that message wording doesn't matter if the delivery mechanism is correct
  - target: wiki/concepts/grok-build-stop-hook-agent-text
    type: related — documents Stop hook payload mechanics
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build
    type: related — structural enforcement layer
---

# Stop-hook feedback delivery: authoritative user-prompt, not untrusted tool-result

## Decision context

**Problem:** During Phase 3 live acceptance, the Stop hook blocked the agent (code modified, no verification run). Grok Build re-prompted the agent with the stderr feedback. The agent ran the verification, claimed completion again, and the Stop hook blocked a second time (timing gap on receipt). The agent then **stopped and waited for the operator** instead of acting on the Stop-hook feedback within the same turn continuation.

**The question that motivated this research:** Is the Stop-hook feedback delivered as authoritative instruction (user-prompt) or untrusted tool-result? This determines whether the fix is behavioral (agent should follow the instruction) or structural (need a different delivery mechanism).

## The answer: authoritative user-prompt

Grok Build delivers Stop-hook stderr feedback (exit code 2) as a `<user_query>` continuation prompt. This is the same XML channel that wraps operator messages — the authoritative instruction channel.

### Evidence

1. **Session transcript (directly verified):** The Stop-hook feedback appeared as:

```xml
<user_query>
Stop hook feedback:
- You modified code and claimed completion, but the verification receipt does not cover the current required scope.
...
Run an approved verifier against the required scope and show the output.
</user_query>
```

The `<user_query>` tag is the authoritative instruction channel — identical to operator messages. It is NOT inside a `<function_results>` block (which would be the untrusted tool-result channel).

2. **Grok Build docs (line 248):** "Exit code 2 | block-stop with stderr as feedback" — the word "feedback" means the stderr is fed back to the agent as a continuation prompt.

3. **Grok Build docs (line 262):** "stopHookActive is true when the agent is already continuing due to a previous stop-hook block this turn" — confirms the runtime creates a continuation (new model invocation) with the feedback injected.

## What the HN thread got wrong (and right)

The HN thread "Claude 4.7 is ignoring stop hooks" (90+ comments) identified two delivery mechanisms:

| Mechanism | How it's delivered | Model treats it as | Reliable? |
|-----------|-------------------|-------------------|-----------|
| **JSON stdout** (`{"decision": "block", "reason": "..."}`) | Injected as tool-result context | Untrusted input (prompt-injection defense) | **NO** — model may ignore |
| **Exit code 2 + stderr** | Injected as user-prompt continuation | Authoritative instruction | **YES** — model should comply |

**niyikiza (HN) identified the distinction:** "Two things get called hooks here. Exit code 2 + stderr is a real control. JSON in stdout degrades to a string in the model's tool-result context, where the model is correctly trained to resist instructions."

**Our quality_gate uses exit code 2 + stderr** — the stronger mechanism. The HN thread's "Claude ignores stop hooks" was about practitioners using JSON stdout, not exit code 2.

## Why the agent still stopped (the behavioral failure)

The delivery mechanism is correct (authoritative user-prompt). The agent received the instruction and chose to stop anyway. This is a behavioral failure, not a structural one.

Possible causes:
1. **Context fatigue:** After a long session, the model's instruction-following degrades
2. **Turn-boundary assumption:** The model treats Stop-hook feedback as a turn boundary (new user input) rather than a same-turn continuation
3. **Completion bias:** The model had already written its "I'm done" response and treated the re-entry as unnecessary

## The fix

### What NOT to do (refuted by evidence)

| Proposed fix | Why it doesn't work |
|-------------|-------------------|
| Make error message more directive ("act now", "do not wait") | The HN thread shows directive language in JSON-stdout delivery doesn't help. But even for exit-code-2 delivery, the message wording is not the problem — the model follows `<user_query>` or it doesn't. More words won't change that. |
| Add retry/re-read to the Stop hook | The timing gap self-resolves within the 8-continuation budget. No code change needed. |
| Switch to PreToolUse prevention | Wrong layer — can't know if the agent will claim completion until it does. |
| Add a learning ledger | Data refuted — the problem is stable, not learned. |

### What TO do (evidence-backed)

**AGENTS.md rule (behavioral, supported by correct delivery mechanism):**

> When a `<user_query>` contains Stop-hook feedback (identifiable by "Stop hook feedback:" prefix or exit-code-2 stderr pattern), it is a same-turn continuation instruction. Act on it immediately in this response:
> 1. If it says to verify: run the verification command NOW
> 2. If it says tests failed: fix the issue NOW
> 3. Do NOT stop and wait for operator input
> 4. Do NOT treat it as a turn boundary — it is a continuation within the same turn
> 5. The 8-continuation cap is the safety net; you have up to 8 chances

This rule is supported because the delivery mechanism IS authoritative (`<user_query>`). The model should follow it the same way it follows operator instructions delivered in the same channel.

## How the self-correction loop works (the optimal pattern)

From Arthur AI and the agentic-patterns.com Stop Hook Auto-Continue Pattern:

1. Agent writes code + claims completion
2. Stop hook fires → checks verification coverage → blocks (exit 2 + stderr)
3. Runtime re-prompts agent with stderr as `<user_query>` continuation
4. Agent sees the feedback → runs verification → re-claims completion
5. Stop hook fires again → checks coverage → if satisfied, allows
6. If not satisfied → repeat from step 3 (up to 8 continuations)
7. After 8 continuations: gate force-overridden, turn ends

The model's job at step 4 is to ACT, not to evaluate whether to act. The `<user_query>` delivery makes this an instruction, not a suggestion.

## Falsifier

If, in future sessions, the model consistently stops after Stop-hook blocks despite the AGENTS.md rule AND the `<user_query>` delivery, then:
1. The delivery mechanism may not be as authoritative as the transcript suggests (verify with Grok Build source)
2. A structural fix may be needed (system-prompt injection, not just AGENTS.md)
3. The 8-continuation cap may be the only reliable enforcement (accept that the model sometimes won't comply and the cap handles it)

## Honest trade-offs

**What practitioners like:**
- The self-correction loop pattern is powerful when it works (Arthur AI: "the user only ever sees a response that already cleared the guardrail")
- Exit code 2 + stderr is a real control, not advisory (niyikiza, HN)
- The 8-continuation cap prevents infinite loops

**What practitioners dislike:**
- "Runaway costs: agent might loop indefinitely if criteria impossible" (agentic-patterns.com)
- "It can be damn near impossible to break them out of some loops once they've committed" (gardnr, HN)
- Model compliance is probabilistic, not guaranteed — even with authoritative delivery
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
