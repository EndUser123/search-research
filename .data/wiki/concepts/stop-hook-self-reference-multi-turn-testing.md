---
title: "Stop-hook self-reference: multi-turn testing"
created: 2026-08-10
source: session-019fe88b
tags: [stop-hook, testing, self-reference, multi-turn, verification, hook-development]
summary: >
  Testing a Stop hook on your own turn creates a self-reference problem: the
  Stop fires at end-of-turn, but you can't observe its decision from within
  the same turn. The solution is multi-turn observation: trigger in turn N,
  observe the result in turn N+1. This is inherent to Stop-hook verification
  and cannot be eliminated within a single turn.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/iterative-cross-model-hardening-loop.md
    type: complements
  - target: wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance.md
    type: related
---

# Stop-hook self-reference: multi-turn testing

## Decision context

The obligation-ledger spike needed live acceptance testing through the real
Grok Build runtime. The Stop hook fires at end-of-turn, reads the transcript,
and makes its decision (block or allow). But the testing agent cannot observe
that decision from within the same turn — by the time the Stop fires, the
agent has already lost control.

## The problem

```
Agent turn N:
    edit hooks/** file (triggers obligation)
    run /review (or don't)
    claim completion
    ↓
Stop hook fires (reads transcript, makes decision)
    ↓
Agent has NO observation of the Stop decision within turn N
```

The transcript records tool calls as they happen, but the Stop hook's scan
window (`last_line` in `quality-gate-{session}.json`) tracks scan position.
The agent can't see what the Stop decided until the next turn starts — at
which point it reads the shadow log or obligation state file.

## The solution: multi-turn observation

```
Turn N: trigger (edit hooks file) + action (run /review or don't)
    ↓ Stop fires, makes decision, writes shadow log + cond-freshness state
Turn N+1: observe results
    - read quality-shadow-{session}.jsonl for the decision
    - read cond-freshness-{session}.json for the obligation state
    - read quality-obligation-{session}.json for continuation state
```

Each test case (block, pass, re-arm) requires one trigger turn + one
observation turn. A full acceptance sequence (cases C, D, E, F, H) needs
5+ turns with Stop fires between each.

## Workarounds that don't work

1. **Dry-run the hook inline:** running `quality_gate/main.py` manually
   via subprocess doesn't produce a real Stop event — the payload
   differs, and the transcript scan window may not include current-turn
   tool calls.

2. **Unit/subprocess tests:** useful for logic verification (the A-O
   matrix), but they don't prove the hook fires through the real Grok
   Build dispatch chain. ChatGPT's verification prompt explicitly
   separated UNIT/SUBPROCESS/REGISTERED/REAL_DISPATCH evidence levels.

3. **Observing within the same turn:** impossible by construction — the
   Stop hook fires after the agent's turn ends.

## What this means for our workspace

Any future Stop-hook development or modification should plan for multi-turn
testing from the start. The testing protocol is:

1. **Trigger turn:** make the edit + take the action + end turn
2. **Observation turn:** read shadow log + obligation state + verify decision
3. **Repeat** for each test case

Session restarts complicate this: the quality-gate state file (`last_line`,
`verification_ran`, `invoked_skills`) carries across restarts within the
same session ID, but a stale `last_line` can cause the scan to miss new
transcript entries. Clearing the state file forces a fresh scan from line 0.

## Falsifier

This pattern is wrong if a mechanism exists to observe the Stop hook's
decision within the same turn (e.g., a post-Stop callback that injects
the decision into the next prompt). As of 2026-08-10, no such mechanism
exists on Grok Build — the Stop decision is terminal for the turn.

## Receipts

- `quality_gate/main.py:162-163` — the early-exit that makes the contract COMPLETION_SCOPED (verified in source)
- `quality_gate/main.py:224` — `_transcript_hooks_mutation_detected` boolean trigger (verified in source)
- Shadow log: `~/.grok/hooks/state/quality-shadow-{session_id}.jsonl` — records Stop decisions for next-turn observation
- State file: `~/.grok/hooks/state/quality-gate-{session_id}.json` — `last_line` scan-window tracking
- Session 019fe88b: 5+ turns with Stop fires between each for live acceptance cases C, D, E, F, H

## Auto-related

- [[skill-graph]]
- [[skill-catalog]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[grok-build-stop-hook-patterns-and-feedback-mechanism]]
- [[sdlc-workflow-improvements-from-session-019fdf3d]]

