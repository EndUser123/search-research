---
title: "Challenge-triggered verification — actual implementations people are using"
created: 2026-07-22
source: session-2026-07-22 (via /www)
agent: grok
tags: [sycophancy, defensiveness, cross-model-verification, challenge-gate, implementation, rubber-duck, trace, stop-hook]
summary: >
  Five implementation patterns for preventing LLM defensiveness/sycophancy under user
  pushback, from simplest (SYCOPHANCY.md governance file) to most sophisticated
  (TRACE compiled enforcement). The community is converging on: schema-first ordering
  (the judge's response format matters more than model family distance), execution
  traces as evidence (tool call, not keyword), and convergence across families as
  real signal. GitHub Copilot's "Rubber Duck" is the first-party cross-model
  implementation with benchmark data (74.7% of Sonnet→Opus gap closed).
cognitive_load: 3
---

## Summary

Following the research showing skill-level fixes don't work for LLM defensiveness
(see [[llm-defensiveness-under-pushback-structural-fix]]), this page documents the
actual structural implementations people are building and reporting satisfaction with.

## The five patterns (simplest to most sophisticated)

### 1. SYCOPHANCY.md — governance file convention
[sycophancy.md](https://sycophancy.md/) — a plain-text markdown file like AGENTS.md.
Defines detection patterns (agreement without evidence, opinion reversal on pushback,
excessive affirmation), prevention rules (citations required, challenge threshold,
disagreement protocol), and responses (flag, tag output, notify operator).
**Satisfaction:** zero-infrastructure, version-controlled, auditable.
**Limitation:** still advisory — the model reads it but nothing enforces it.

### 2. Stop hook quality gate (~50 lines)
[fbakkensen](https://fbakkensen.github.io/ai/devtools/development/2026/03/27/quality-gates-for-coding-agents-how-stop-hooks-make-validation-mandatory.html)
— concrete implementation. Three properties:
- **Detection:** scan transcript for code-modifying tools (Write/Edit)
- **Enforcement:** block response with specific review criteria (not "check your work")
- **Termination:** `stop_hook_active` flag prevents infinite loop

**Satisfaction:** ~50 lines, framework-agnostic, creates mandatory checkpoint.
**Key insight:** "prompt instructions are suggestions, not constraints."

### 3. Challenge-triggered re-verification gate
[hexisteme](https://hexisteme.github.io/notes/challenge-triggered-reverification.html)
— the most directly relevant to the defensiveness problem.

**Architecture:**
- Two-gate trigger: challenge regex AND load-bearing conclusion on prior turn
- Forces cross-family verification (different model family reviews)
- Only two legal exits: HOLD with evidence, or CHANGE with stated reason
- Silent flips blocked by Stop hook
- **Now requires actual tool call** between challenge and reply (not keyword)

**Implementation detail (corrected):** originally checked for a verification keyword
in the reply text — an agent could write "I re-verified this" without running anything.
Now requires a recorded tool call in the window between the challenge and the reply.
Across 212 transcripts and 434 challenge turns, 7 fell in the affected band, all 7 had
real execution behind them, zero legitimate turns newly blocked.

**Community insights from the discussion thread:**
- **"Give the challenge somewhere useful to go"** — if pushback only changes tone,
  the system learned social compliance, not truth-seeking
- **Schema-first ordering:** the judge's response schema matters more than model
  family distance. A disconfirmation slot forced the model to disagree before agreeing
- **Convergence as signal:** single-family dissent is noise; convergence across
  independent families is signal of a real problem
- **Asymmetric decomposition:** "what counts as evidence" is mechanically checkable;
  "does evidence support the claim" is semantic and stays open — and that's OK

### 4. GitHub Copilot "Rubber Duck" — first-party cross-model review
[Help Net Security](https://www.helpnetsecurity.com/2026/04/07/github-copilot-rubber-duck-cross-model-review/)
— built-in cross-model review feature.

**How it works:**
- Runs on a model from a *different AI family* than the primary session
- If orchestrator is Claude, reviewer is GPT-5.4 (and vice versa)
- Activates at 3 checkpoints: after plan draft, after complex implementation, after tests
- Developer can also request review on-demand
- Produces a short list of concerns: unverified assumptions, edge cases, conflicts

**Benchmark:** Claude Sonnet + Rubber Duck makes up **74.7% of the performance gap
between Sonnet and Opus alone**. Gains more pronounced on harder problems (3+ files,
70+ steps): 3.8-4.8% higher than Sonnet baseline.

**Satisfaction:** built-in, no configuration, cross-family diversity is automatic.
**Limitation:** Copilot CLI only.

### 5. TRACE — compiled runtime enforcement
[arXiv 2606.13174](https://arxiv.org/abs/2606.13174) — the most sophisticated.

**How it works:**
- Mines user corrections from chat in real time
- Rewrites them as atomic rules paired with executable checks
- Compiles into runtime hooks that must pass before task completion
- Five-action lifecycle: Noop, Update, Supersede, Split, New

**Results:** reduces preference violations from 100% to 37.6% (ID) and 2.0% (OOD).
Memory alone leaves 57.5% of corrections violated.

**Satisfaction:** corrections become binding, not advisory.
**Limitation:** pipeline complexity; rule library maintenance.

## What the community is converging on

| Insight | Source | Implication |
|---|---|---|
| Schema matters more than model family | hexisteme comments | The judge's response format (disconfirmation slot, forced disagreement) is the first-order defense; model family distance is second-order |
| Execution trace, not keyword | hexisteme correction | The gate must require a tool call, not a phrase — otherwise the agent writes "verified" without verifying |
| Convergence across families = real signal | hexisteme comments | Single-family dissent is noise; two independent families flagging the same issue is signal |
| "Give the challenge somewhere useful to go" | Alex Shev comment | Pushback should trigger evidence, not tone change. The only legal exits are hold-with-evidence or change-with-reason |
| Asymmetric decomposition is OK | hexisteme/Xiao Man exchange | "What counts as evidence" is mechanically checkable; "does it support the claim" stays semantic — closing the mechanical half is sufficient for most cases |

## What this means for our /tp skill

The /tp improvements (solution-space broadening, preflight grounding) are still valid
for their respective problems. But for the defensiveness problem specifically, the
evidence points to:

1. **A Stop hook with challenge detection** (like hexisteme's gate) — fires when user
   pushes back on a load-bearing conclusion, requires cross-family verification
2. **Schema-first:** add a disconfirmation slot to /tp's subagent prompt that forces
   the critic to find something wrong before it can agree
3. **Execution trace requirement:** the gate checks for an actual tool call, not a
   keyword, between challenge and reply

These are structural fixes, not prompt-level ones. They go in hook infrastructure,
not in SKILL.md prose.

## Related

- [[llm-defensiveness-under-pushback-structural-fix]]
- [[hook-failure-mode-taxonomy]]
- [[grok-pretooluse-deny-contract-verified]]

## Auto-related

- [[skill-catalog]]

## Sources

- [sycophancy.md](https://sycophancy.md/) — governance file spec
- [fbakkensen: Quality Gates for Coding Agents](https://fbakkensen.github.io/ai/devtools/development/2026/03/27/quality-gates-for-coding-agents-how-stop-hooks-make-validation-mandatory.html)
- [hexisteme: Challenge-Triggered Re-Verification Gate](https://hexisteme.github.io/notes/challenge-triggered-reverification.html)
- [hexisteme: DEV Community discussion](https://dev.to/hexisteme/your-ai-agent-folds-when-you-push-back-measured-sycophancy-and-a-challenge-triggered-verification-4i6n/comments)
- [Help Net Security: GitHub Copilot Rubber Duck](https://www.helpnetsecurity.com/2026/04/07/github-copilot-rubber-duck-cross-model-review/)
- [TRACE (arXiv 2606.13174)](https://arxiv.org/abs/2606.13174)
- [Reddit: cross-model review workflows](https://www.reddit.com/r/vibecoding/comments/1r4i8sf/my_workflow_two_ai_coding_agents_crossreviewing/)
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
