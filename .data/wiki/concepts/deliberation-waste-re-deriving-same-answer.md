---
title: "Deliberation waste — when re-deriving the same answer burns tokens"
created: 2026-07-21
source: session-2026-07-20/21 (external model analysis of transcript waste)
agent: grok
host: both
tags: [token-efficiency, deliberation, thinking-budget, agentic-workflow, anti-spin, rules-stack, llm-failure-modes]
summary: >
  When an LLM agent re-deliberates a decision it already reached within the
  same turn, restates context already in scope, or re-reads its own rules
  aloud as a thinking exercise, it burns 3-5x the tokens the task required
  without changing the answer. The root cause is rule-stack multiplication:
  multiple rules individually say "verify / cite / name options / act on
  defaults," and the model must weigh all of them before acting on any.
  Defense: single-pass deliberation rule, short-command interpretation,
  thinking budget, and scoped preflight (all shipped to ~/.grok/AGENTS.md).
cognitive_load: 2
---

# Deliberation waste — when re-deriving the same answer burns tokens

## The failure pattern

Token analysis of a real transcript (session 019f821c, 2026-07-20/21)
showed:

| Metric | Value |
|---|---|
| Thinking-to-response ratio | 3.78x overall |
| Worst single turn | 40.1x (15,681 chars think / 391 chars response) |
| Turns where thinking > response | 11 of 20 |
| Result correct? | Yes — the model reached the right answer; it just re-derived it four times |

## The five spinning patterns

1. **Re-deliberating after deciding.** Six consecutive "wait / actually /
   hmm / one more consideration" reversals of a binary decision that
   never changed. The dominant waste pattern.

2. **Reading own rules aloud as a thinking exercise.** Quoting AGENTS.md /
   CLAUDE.md verbatim into thinking to re-derive what the model should do,
   rather than acting on cached knowledge. ~3,000 chars per turn wasted.

3. **Restating context already in scope.** Re-enumerating the entire prior
   turn's analysis (still on screen, still in context) as if deriving it
   fresh.

4. **Hypothetical "what if they meant X" cascades.** Five interpretations
   of a 2-word command ("claim it"), each weighed against the next, zero
   grounded in evidence about what the user meant.

5. **Considering-and-rejecting in parallel.** Listing 5+ options,
   evaluating each, re-evaluating each, picking one — three full passes
   through the same option set in the same turn.

## Root cause: rule-stack multiplication

The AGENTS.md rule stack is internally redundant. Six rules all say
"be a thought partner / don't solution-vend / verify / name options / cite
evidence / act on stated defaults." Each rule individually reasonable;
collectively they create a **deliberation obligation** — the model must
consider every rule before acting on any of them.

Two specific tensions:

- **"Stated-default rule — act, don't ask"** vs **"action_safety —
  confirming is cheap."** The model must weigh which wins per turn.
- **"Preflight is mandatory before non-trivial changes"** vs **"reversible
  config edits don't need preflight."** The model must decide whether the
  current action crosses the threshold.

This is a structural problem, not a model problem. The model is correctly
applying the rules it was given. The rules just multiply each other.

## Defenses shipped (2026-07-21)

All four shipped to `~/.grok/AGENTS.md` § "Deliberation discipline":

### Single-pass deliberation

If you have weighed an option and reached a decision, ship the decision.
Reconsidering the same decision within the same turn without new evidence
is deliberation theater. **Falsifier:** if re-deliberation changes the
answer, cite the new evidence; if no new evidence, the reconsideration
was wasteful.

### Short-command interpretation

A short imperative ("claim it," "ship it," "go") after a proposal means
"do what you proposed." Do not enumerate alternative interpretations
unless the prior context makes the literal reading genuinely ambiguous.

### Thinking budget

Thinking should be proportional to decision complexity, not rule-count.
If thinking exceeds 5x response length, you are likely re-deliberating or
restating context. Stop and ship. Exception: genuine root-cause analysis
where each step produces new evidence.

### Preflight scope narrowing

Preflight is mandatory for capability claims and irreversible changes.
It is NOT required for reversible config edits, doc changes, exploration,
or `[INFERENCE]` claims. This prevents the mandate from forcing
deliberation about whether reversible actions cross the threshold.

## What was NOT changed (deliberately)

- **The preflight mandate itself** — load-bearing for capability claims
- **The verification-receipt rule** — catches real fabrication
- **The ≥2 options rule** — produces better first-turn analysis
- **Rule consolidation** (6 thought-partner rules → 1 block) — deferred
  because merging sections risks introducing cross-artifact consistency
  errors; needs a fresh session with budget for careful review

## Estimated impact

| Fix | Tokens saved per turn | Trigger frequency |
|---|---|---|
| Single-pass deliberation | ~5,000 chars | Every action with a stated default |
| Preflight scope narrowing | ~2,000 chars | Every config edit |
| Short-command interpretation | ~3,000 chars | Every short imperative |
| Thinking budget | ~2,000 chars | Every turn |
| **Total** | **~10-15K chars on busy turns** | — |

The transcript that motivated this analysis was ~60-70% of the tokens it
needed to be. The remaining 30-40% was deliberation waste.

## Relation to existing concepts

- [[fabricated-causal-chain-receipt-required]] — fabrication and
  deliberation waste are complementary failure modes: fabrication ships
  claims without evidence; deliberation waste burns evidence without
  shipping claims. Both are symptoms of the rule-stack multiplication
  problem.
- [[plausible-narratives-substitute-for-verification]] — the broader
  pattern where the model substitutes narrative sufficiency for actual
  verification. Deliberation waste is what happens when the narrative is
  internal (thinking blocks) rather than external (stated claims).

## Auto-related

- [[examples-over-rules-escape-hatch]]
- [[multi-agent-correlated-errors]]
- [[llm-handoff-best-practices]]
- [[operator-collaboration-style-and-leverage]]
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
