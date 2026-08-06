---
title: "Research quality principle: quality is the constraint, efficiency is the method, time is not the constraint"
created: 2026-07-30
source: session-019fb189
tags: [quality-principle, efficiency, operator-directive, standing-policy, www, delegation, methodology]
summary: >
  Standing operator directive: research must be thorough and uncensored — take
  as much time as it needs. Efficiency means distributing work optimally (1
  question per agent, structured output, fast backends), NOT doing less research,
  capping output, or rushing conclusions. The three delegation rules exist to
  eliminate waste (serial execution, wrong backends, context bloat), not to
  limit depth. Citing a faster path to a shallow answer is worse than a slower
  path to the right answer.
agent: grok
host: grok
cognitive_load: 1
verification: operator-stated
relations:
  - target: wiki/concepts/delegation-optimization-chunking-output-backend-discipline.md
    type: governs — the delegation rules serve this principle, not the reverse
  - target: wiki/concepts/research-applicability-checking-dont-cite-without-verifying-assumptions.md
    type: complements — quality research includes checking applicability, not just speed
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: related — rushing to conclusions is premature closure
---

# Research quality principle

## Decision context

**Why this was needed:** during session 019fb189, the operator observed that /www research runs were slow (5-8 min per agent). The agent's response was to cap output to terse numbered lists and reduce search depth. The operator corrected: the fix should be better task distribution (parallel agents), not less research. Later, the operator wrote the delegation-optimization wiki concept from session observations without doing external research first, and was corrected again. Both errors share a root: optimizing for speed at the expense of quality, when the operator's priority is the reverse.

This principle exists to prevent the recurring confusion between "efficiency" (eliminating waste in HOW research is done) and "censorship" (reducing WHAT research is done to save time). The delegation rules ([[delegation-optimization-chunking-output-backend-discipline]]) are the HOW — they serve this principle, not the reverse.

The principle matters because the agent has a documented bias toward closure ([[reactive-pattern-matching-and-closure-pressure]]): under pressure to finish, it cuts depth to reach a clean ending. The operator's quality bar is higher than the agent's default. Without this principle stated explicitly, the agent will optimize for speed over quality every time — not because it doesn't care about quality, but because closure pressure pulls toward "done" and nothing structural counterbalances it.

The principle also matters for the /www skill specifically: Round 3.25 (applicability check) and Round 2b (practitioner signal) add wall-clock time. Without this principle, the agent is tempted to skip them. With it, the agent knows that skipping a 30-second applicability check to save 30 seconds is the wrong trade — it risks hours of building on an inapplicable premise.

## The directive (operator-stated, session 019fb189)

**Quality is the constraint. Efficiency is the method. Time is not the constraint.**

1. **Want better quality research, not censored research.** The operator wants comprehensive findings. Don't cap output, minimize depth, or truncate findings to save time.
2. **Not the wrong conclusion research.** Don't rush to a conclusion because it's fast. The right answer matters more than the fast answer. This includes running the Round 3.25 applicability check — citing inapplicable research produces wrong conclusions.
3. **It needs to take as much time as it needs.** No time pressure on research depth. If a topic needs 8 searches instead of 5, do 8.
4. **As long as we are efficient with it.** Efficiency means: distribute work across parallel agents (1 question per agent), use fast backends (DDG first), avoid expensive operations (full page fetches) unless load-bearing. Efficiency eliminates waste, not depth.

## What efficiency IS

| Efficient (do this) | Inefficient (eliminate this) | Why the inefficient version wastes time |
|---|---|---|
| 6 narrow agents in parallel, 3-5 searches each | 2 broad agents serially, 9-15 searches each | Serial execution means wall-clock = sum of all searches, not max of the slowest |
| DDG for search (free, fast, no quota) | Built-in web_search for routine queries | web_search burns Grok quota at ~2 RPS fleet-wide, hits 429s under parallel load |
| Abstract-only for papers; full fetch for 1-2 top sources | Full-fetch every arxiv page | Each fetch 10-30s + massive context cost; most full-page content doesn't change findings |
| Structured findings (technique/source/relevance, 2-4 sentences) | Raw search dumps OR terse lists | Dumps bloat context → compaction → quality loss. Terse lists lose signal the operator values. |
| Chunked revision turns (critical → majors → minors) | 32 issues in one turn | 32 issues × ~4 tool calls = ~128 tool calls in one subagent turn; exceeds context/timeout limits |

The key insight: every "inefficient" pattern wastes time without producing better findings. The "efficient" pattern produces the SAME findings (or better, because the agent isn't context-bloated) in less wall-clock. Efficiency doesn't sacrifice quality — it removes waste that degrades quality.

## What efficiency is NOT

These are the patterns that cut quality under the guise of "efficiency." They are forbidden:

- ❌ **Doing fewer searches** — fewer searches means fewer sources, which means narrower findings. The operator wants comprehensive coverage, not minimum viable.
- ❌ **Capping output length** — the operator said "I don't mind getting more info than less." Capping output to save context is censoring the research.
- ❌ **Truncating findings** — each finding should be complete enough to act on. Truncating to fit a format constraint loses the actionable detail.
- ❌ **Skipping the applicability check to save time** — Round 3.25 exists because citing inapplicable research produces wrong conclusions. Skipping it trades 30 seconds of checking for hours of building on a false premise.
- ❌ **Rushing to a conclusion** — the agent's fatigue or session length is not a reason to stop researching. See [[reactive-pattern-matching-and-closure-pressure]]: closure pressure makes the agent want to finish; the principle says quality is more important than finishing.
- ❌ **Citing research without verifying it applies** — the [[research-applicability-checking-dont-cite-without-verifying-assumptions]] pattern exists for this exact failure. Citing the martingale result unconditionally (as I did this session) is the canonical example.

The distinction between "efficient" and "censored" is: efficient eliminates WASTE (serial execution, wrong backends, context bloat); censored eliminates DEPTH (fewer searches, shorter findings, skipped checks). Waste reduction improves quality by freeing context and wall-clock for more work. Depth reduction degrades quality by removing information.

## The common confusion

When the operator says "/www has slowed down," the correct response is "let's distribute the work better" — NOT "let's do less research." The delegation optimization rules ([[delegation-optimization-chunking-output-backend-discipline]]) exist to serve THIS principle. They are the means; quality is the end.

Session 019fb189 demonstrated the confusion three times:

**Instance 1:** The operator said research was slow. The agent capped output to terse numbered lists and reduced search depth. The operator corrected: "I don't mind getting more info than less, that's probably more useful." The cap was the wrong optimization — it cut quality to save time, when the right fix was to parallelize the same amount of work.

**Instance 2:** The agent wrote the delegation-optimization wiki concept from session observations without doing external research. The operator corrected: "you haven't done the research to have a good idea of what delegation optimization is to agents, you made an assumption that your previous work was perfect." The agent jumped to writing without researching — efficiency without quality.

**Instance 3:** The agent ran a /www cycle on delegation optimization but forgot to apply Round 3.25 (the applicability check it had added to the skill earlier the same session). The operator corrected: "the '/www' skill is supposed to have a research assumptions challenge step." The rule existed; it didn't fire.

All three instances share a root cause: the agent optimizes for "done" over "right" under session-length pressure. This principle is the structural countermeasure. It doesn't add a new step — it establishes the priority ordering that governs when steps can be skipped (never, for quality-affecting steps) and when they can be parallelized (always, for independent work).

This connects to [[reactive-pattern-matching-and-closure-pressure]]: the agent pattern-matched "slow" → "do less," when the correct pattern was "slow" → "distribute better." It also connects to [[problem-first-systems-decomposition]]: the agent didn't understand the problem (distribution inefficiency) before jumping to a solution (cap output). And it connects to [[premature-closure-narrative-sufficiency-external-approaches]]: the agent closed on "cap output" as the answer without checking whether the operator agreed.

## Receipts

- Operator (session 019fb189): "I don't mind getting more info than less, that's probably more useful, but we need to be more efficient with how we distribute tasks."
- Operator (session 019fb189): "Remember I want better quality research, not censored research, not the wrong conclusion research, and it needs to take as much time as it needs, as long as we are efficient with it."

## What this means for our workspace

1. **No skill should cap research depth to save time.** If research is slow, optimize the distribution (parallel agents, fast backends), not the depth.
2. **The delegation rules are the means; this principle is the end.** Don't invert them — the rules exist to enable MORE research faster, not LESS research faster.
3. **When the operator says "this is slow," the question is "how do we distribute better?" not "how do we do less?"**
4. **This applies to /www, /design, /go, /risk, /review, and any skill that does research or analysis.**
5. **AGENTS.md should reference this principle** so it loads in every session, not just when a /www run happens.
6. **The /www SKILL.md should state this principle at the top** so the agent never confuses "distribute better" with "do less."
7. **The verification gate ([[self-reflection-in-llms-fails-without-external-evidence]]) applies here:** the agent can't self-assess whether its research is "good enough" — it needs external checks (applicability, disconfirmation, operator feedback). Skipping checks to save time trades 30 seconds for hours of rework.
8. **When the operator says research is slow, they mean distribution, not depth.** The correct response is parallelize, not truncate.

## Falsifier

If research produced under this principle is consistently lower quality than rushed research (measured by operator corrections, missed findings, wrong conclusions), the principle is wrong. But this is unlikely — the principle simply states that quality is the goal and efficiency is the method, which is axiomatic for research.
