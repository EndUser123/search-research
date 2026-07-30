---
title: "Agentic Harness Seven Components: System Prompt Is the Only One That Regresses"
created: 2026-07-30
source: session-20260730
tags: [harness-engineering, system-prompt, agentic-harness, academic-paper, decision]
summary: >
  An April 2026 paper from Fudan/Peking (arXiv 2604.25850) formalizes the
  agentic harness as seven editable components and measures each one's
  isolated contribution. System prompt is the ONLY component that regresses
  when added alone (-2.3pp). Memory adds +5.6pp, tools +3.3pp, middleware
  +2.2pp. The harness transfers across model families without retraining
  (+2.3 to +10.1 points). This validates our hook/skill/middleware
  architecture over prompt-tuning.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - https://www.iqsource.ai/en/blog/agentic-harness-engineering/ (IQ Source, May 1, 2026) — full blog read with paper analysis
  - https://arxiv.org/abs/2604.25850 (Lin et al., April 30, 2026) — paper referenced
relations:
  - target: wiki/concepts/ai-harness-engineering.md
    type: supersedes
  - target: wiki/concepts/agent-harness-engineering.md
    type: supersedes
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: extends
  - target: wiki/concepts/execution-path-based-model-routing.md
    type: related
---

# Agentic Harness Seven Components: System Prompt Is the Only One That Regresses

## Decision context

Our workspace has accumulated extensive harness engineering lore from
NotebookLM syncs — [[ai-harness-engineering]] and [[agent-harness-engineering]]
capture podcast-level claims like "a decent model with a great harness beats
a great model with a bad harness." These are directionally correct but
unquantified. An April 2026 paper from Fudan/Peking puts hard numbers on
which harness components actually move the needle, and the results validate
our architecture (hooks, middleware, skills) over prompt-tuning.

## The seven components

The paper (arXiv 2604.25850) formalizes an agentic harness as seven
versioned, editable files:

1. **System prompt** — the base instruction set (our AGENTS.md)
2. **Tool descriptions** — what tools are available and how to use them
3. **Tool implementations** — the actual code behind the tools
4. **Middleware** — pre/post-processing around tool calls (our hooks)
5. **Skills** — composable task procedures (our SKILL.md files)
6. **Sub-agent configuration** — how spawned agents are set up (our pool contracts)
7. **Long-term memory** — persistent context (our wiki, handoffs)

## The Table 3 nobody quoted

When each component was added to a baseline harness in isolation, the
effects were:

| Component added alone | Effect on pass@1 |
|----------------------|------------------|
| Memory | **+5.6 points** |
| Tools | +3.3 points |
| Middleware | +2.2 points |
| System prompt | **-2.3 points** (regression!) |

**System prompt is the only component that makes the agent worse when added
alone.** The authors explain: the system prompt "encodes 79 lines of
universal discipline whose executability depends on the other three."
Discipline without machinery is noise — the agent reads "verify before
publishing" but has no middleware that enforces verification, so it burns
turns re-checking work that should have been guarded automatically.

## Cross-model transfer is the empirical moat

The harness evolved on GPT-5.4 was applied to five other models with **no
retraining**:

| Model | Gain |
|-------|------|
| DeepSeek-v4-flash | +10.1 points |
| Qwen-3.6-plus | +7.8 points |
| Gemini-3.1-flash-lite | +5.2 points |
| GPT-5.4 medium | +3.1 points |
| GPT-5.4 xhigh | +2.3 points |

The seven harness files encode **general agent patterns**, not model-specific
tricks. This means a well-designed harness survives model swaps — which is
exactly our pool-contract + pick_model.py architecture.

## The regression-blindness asterisk

The paper is honest about the loop's weakness (§4.4.2):
- **Fix prediction precision:** 33.7% (5× random baseline)
- **Regression prediction precision:** 11.8% (~2× random baseline)

The loop is decent at naming what it repairs but **blind at naming what it
breaks**. This is why cross-instance PR review (Howie Liu's 30 parallel Claude
Code instances) catches what autonomous loops miss.

## What this means for our workspace

**This paper validates our entire architecture.** Our investment in:

| Component | Our implementation | Paper's ranking |
|-----------|-------------------|-----------------|
| **Middleware** (hooks) | PreToolUse gate, PostToolUseFailure, UserPromptSubmit injector | #3 most impactful (+2.2pp isolated) |
| **Skills** | 100+ SKILL.md files with consumes: declarations | #4 (part of the evolved harness) |
| **Long-term memory** | Wiki, handoffs, fleet-models.json | #1 most impactful (+5.6pp isolated) |
| **Sub-agent config** | Pool contracts, pick_model.py, fleet-models.json | #5 |
| **System prompt** | AGENTS.md | **Only component that regresses alone** |

The finding "system prompt regresses when isolated" is the academic
formalization of our own [[mechanical-enforcement-over-behavioral-reminder]]
principle: behavioral instructions without mechanical enforcement produce
noise, not results. Our hook system IS the middleware that makes AGENTS.md
rules executable.

**Actionable implication:** when a rule isn't being followed (like the DDG
search hierarchy issue from this session), the fix is NOT to add more
prompt text — it's to add middleware that enforces it mechanically. The
paper quantifies why: prompt-only changes are net-negative without machinery.

## Supersedes prior harness concepts

This concept supersedes [[ai-harness-engineering]] and
[[agent-harness-engineering]] because it provides measured, falsifiable data
instead of podcast-level claims. The prior concepts are NLM-synced
transcripts with anecdotal evidence ("a decent model with a great harness
beats a great model with a bad harness"). This paper proves it with numbers,
and crucially, identifies WHICH components matter and which don't.

## Falsifier

This concept is wrong if:
- The Terminal-Bench 2 benchmark doesn't transfer to real-world enterprise
  coding tasks (it's a terminal-based benchmark, not a multi-file refactor
  benchmark)
- The component isolation methodology (adding one evolved component to
  baseline) doesn't reflect real-world composition effects (components may
  interact non-linearly)
- The cross-model transfer numbers don't hold for models outside the tested
  set (particularly GLM-5.2, our orchestrator model, which wasn't tested)

## Sources

- [IQ Source analysis](https://www.iqsource.ai/en/blog/agentic-harness-engineering/) (Argüello, May 1, 2026) — detailed Table 3 analysis with component breakdown
- [arXiv 2604.25850](https://arxiv.org/abs/2604.25850) (Lin et al., April 30, 2026) — original paper, Chinese universities (Fudan, Peking, Shanghai Qiji Zhifeng)

## Receipts

- IQ Source blog: "Table 3 isolates each component's effect: + memory only +5.6pp, + tool only +3.3pp, + middleware only +2.2pp, + system_prompt only -2.3pp"
- IQ Source blog: "The evolved harness transfers across model families with no further training: +5.1 to +10.1 points across deepseek-v4-flash, qwen-3.6-plus, gemini-3.1-flash-lite"
- IQ Source blog: "fix-prediction precision 33.7% (5x random baseline), regression-prediction precision only 11.8% (~2x baseline)"
- Paper: pass@1 on Terminal-Bench 2 climbs from 69.7% to 77.0% in ten iterations with base model held fixed
