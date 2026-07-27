---
title: "Grok Build Stop hook patterns: community implementations and the v0.2.107 feedback mechanism"
created: 2026-07-27
source: session-2026-07-27 (/www research on Grok Build hook implementations)
sources:
  - external: https://docs.x.ai/build/features/hooks
  - external: https://x.ai/build/changelog
  - external: https://github.com/Dicklesworthstone/destructive_command_guard
  - external: https://fbakkensen.github.io/ai/devtools/development/2026/03/27/quality-gates-for-coding-agents-how-stop-hooks-make-validation-mandatory.html
  - external: https://agentic-patterns.com/patterns/stop-hook-auto-continue-pattern/
  - external: https://understandingdata.com/posts/claude-code-hooks-quality-gates/
  - external: https://snorkel.ai/blog/the-self-critique-paradox-why-ai-verification-fails-where-its-needed-most/
  - external: https://gist.github.com/judge2020/1ebdf3a03d715f7fd524ba1352819238
tags: [grok-build, hooks, stop-hook, self-correction, verification, critic, quality-gate, feedback-loop]
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
summary: >
  Grok Build Stop hooks are underexplored in the community — only dcg
  (destructive command guard) ships a real implementation. The v0.2.107
  changelog added a "feed feedback back to the model" mechanism that is
  fundamentally different from exit-2-stderr blocking: the hook output
  becomes a new turn, not just a block signal. This enables true
  auto-continue self-correction (test → fail → feed error → retry) without
  the agent having to re-invoke. The fbakkensen quality-gate.ps1 and the
  Agentic-Patterns auto-continue pattern are the two best reference
  implementations, but neither targets Grok Build natively. Key design
  lesson from Snorkel's self-critique paradox: gate only on hard/risky
  turns, not every turn — self-correction degrades easy tasks.
relations:
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: extends
  - target: wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
    type: related
  - target: wiki/concepts/grok-build-stop-hook-agent-text.md
    type: extends
---

# Grok Build Stop hook patterns: community implementations and the v0.2.107 feedback mechanism

## Decision context

**Why this research was needed:** after implementing critic_stop.py and self_correct_loop.py, the question arose: how do other people implement verification/self-correction hooks for Grok Build specifically? The critic_stop.py approach (exit-2-stderr on Stop) duplicates what quality_gate.py already does. The research reveals a fundamentally different mechanism exists (v0.2.107 feedback-to-model) that we're not using.

## Key Findings

### 1. Grok Build v0.2.107: Stop hooks can feed feedback back to the model

The changelog states Stop hooks "can now keep the agent running by feeding feedback back to the model instead of ending the turn." This is NOT the same as exit-2 blocking. With exit-2, the agent sees the stderr message and must decide what to do. With the feedback mechanism, the hook output becomes a new turn — the agent continues automatically with the feedback as context.

This is the mechanism that enables true auto-continue self-correction: hook runs tests → tests fail → hook feeds failure output as feedback → agent sees failures and revises → hook runs tests again → repeat until green or max iterations.

**Status:** the exact wire format for this feedback mechanism is not documented beyond the changelog. The judge2020 gist (reverse-engineered Grok Build source) is the ground truth for how the Stop event dispatches hook output.

### 2. Community implementations are scarce

Only three substantial Grok-Build-native hook implementations exist publicly:

| Implementation | What it does | Hook type |
|---|---|---|
| **dcg** (destructive_command_guard) | PreToolUse regex blocker for destructive commands | PreToolUse |
| **Railway skills** | Auto-approval for CLI/API commands | PreToolUse |
| **quality_gate.py** (this workspace) | Stop hook: verification receipts, scope binding, obligation tracking | Stop |

No public community Stop hook implements self-correction or test-driven auto-continue for Grok Build. The implementations that do exist (fbakkensen, Agentic-Patterns) target Claude Code's hook system, which has the same dispatch contract but different trust model.

### 3. The two best reference patterns (from Claude Code, adaptable to Grok)

**fbakkensen quality-gate.ps1:** scans transcript for Write/Edit operations, blocks with named review criteria. Key innovation: uses `stop_hook_active` as a termination guard to prevent infinite loops. The hook itself doesn't verify — it forces the agent to spawn a review subagent, using the hook only for detection + enforcement.

**Agentic-Patterns "Stop Hook Auto-Continue":** the hook runs the tests itself (not the agent) and injects failures as feedback until green. This is the "deterministic outcomes from non-deterministic processes" pattern — higher runaway-loop risk but stronger enforcement.

### 4. The self-critique paradox (Snorkel)

Empirical finding: self-refine loops **degrade easy tasks** while rescuing hard ones. Direct implication: quality_gate.py should gate only on hard/risky turns (code edits, multi-file changes, architectural decisions), not every turn. Gating every turn produces measured quality degradation on the easy work that doesn't need correction.

### 5. The CRITIC hook is redundant on this workspace

quality_gate.py already does what critic_stop.py does — and more. The CRITIC technique is better implemented as:
- A **library function** (self_correct_loop.py — already shipped) that skills call before claiming completion
- A **module inside quality_gate.py** that adds test-execution to the existing receipt-checking
- NOT a separate Stop hook (would double-fire)

## What this means for our workspace

### What we should do

1. **Investigate the v0.2.107 feedback mechanism.** Read the judge2020 gist to understand the wire format. If the hook can feed output as a new turn (not just block), quality_gate.py could be upgraded to run tests and feed failures back — true auto-continue.

2. **Gate only on risky turns.** Per Snorkel: add a risk classifier to quality_gate.py that only blocks on code edits + architectural changes, not on every response. Reduces the ceremony overhead that dominated this session.

3. **Keep critic_stop.py as a reference, not a hook.** It demonstrates the pattern but shouldn't be wired separately. Merge its test-execution logic into quality_gate.py if test-driven auto-continue is desired.

4. **Keep self_correct_loop.py as a library.** It's the composable form — skills call it, not hooks. This is the right abstraction layer.

## Honest trade-offs

**Like:** the v0.2.107 feedback mechanism could eliminate the multi-turn verify-fail-retry cycle that consumed this session. Instead of the agent claiming done → hook blocks → agent tries again, the hook feeds the error and the agent continues in the same turn.

**Dislike:** auto-continue risks runaway loops (the fbakkensen `stop_hook_active` guard exists for this reason). The Snorkel paradox shows self-correction hurts easy tasks. The wire format is undocumented beyond a changelog line.

## Falsifier

This concept is wrong if:
- The v0.2.107 feedback mechanism doesn't actually work as described (changelog overstates capability)
- The Snorkel paradox doesn't apply to our workspace (all our tasks are "hard" by their standard)
- A community Grok Build plugin ships a better verification hook that makes quality_gate.py obsolete

## Related

- [[self-improving-agent-systems-techniques-and-workspace-gaps]]@extends — CRITIC hook and Self-Correct Loop are from this research
- [[hook-evidence-collection-cost-vs-timeout-tradeoff]]@related — same hook infrastructure, different concern
- [[grok-build-stop-hook-agent-text]]@extends — existing knowledge about Stop hook text format

## Sources

- Grok Build hooks docs — https://docs.x.ai/build/features/hooks
- Grok Build changelog — https://x.ai/build/changelog
- dcg (destructive command guard) — https://github.com/Dicklesworthstone/destructive_command_guard
- fbakkensen quality-gate — https://fbakkensen.github.io/ai/devtools/development/2026/03/27/quality-gates-for-coding-agents-how-stop-hooks-make-validation-mandatory.html
- Agentic-Patterns auto-continue — https://agentic-patterns.com/patterns/stop-hook-auto-continue-pattern/
- James Phoenix quality gates — https://understandingdata.com/posts/claude-code-hooks-quality-gates/
- Snorkel self-critique paradox — https://snorkel.ai/blog/the-self-critique-paradox-why-ai-verification-fails-where-its-needed-most/
- W&B agentic self-correction — https://wandb.ai/site/articles/agentic-ai-self-correction-how-to-build-systems-that-fix-their-own-mistakes/
- judge2020 Grok Build source gist — https://gist.github.com/judge2020/1ebdf3a03d715f7fd524ba1352819238
- impeccable (trust model comparison) — https://github.com/pbakaus/impeccable
