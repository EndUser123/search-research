---
title: "Structural success detection over lexical praise — the sycophancy-safe approach"
slug: structural-success-detection-over-lexical-praise
created: 2026-07-31
source: session-019fb933 (/tp critique + operator challenge: "what makes the agent lovable?")
tags: [success-capture, sycophancy, anti-sycophancy, praise-detection, category-error, behavioral-design, capture, notice, slc]
summary: >
  Detecting operator lexical praise ("love this", "great job") to capture
  success patterns is a category error and a sycophancy-amplification vector.
  The correct signal is structural: "a technique was used, it worked, and it
  isn't documented." This distinction was produced by a /tp critique that
  killed the initial proposal and forced a redesign. The corrected approach
  is implemented in /capture category 7, /notice T11, and the AGENTS.md
  "Positive framing" principle.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/thought-partner-standard.md
    type: extends
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: applies
  - target: wiki/concepts/proactive-ai-volunteering-mechanisms.md
    type: related
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: related
---

# Structural success detection over lexical praise

## Decision context

**Why this was needed:** the operator asked "what makes the agent lovable?" Investigation revealed the workspace had 100+ correction memories and zero success memories — a structural asymmetry where the system learns from mistakes but never from successes. The initial proposal was to detect operator lexical praise ("love", "fantastic", "excellent") and route it to a success-capture system.

**The /tp critique killed this approach.** A fresh subagent identified that building praise-reward on a host with active anti_sycophancy protections would directly conflict with those protections and degrade agent behavior. The critique also identified that the evidence (1 "love" + 15 generic praises across thousands of turns) was too sparse to build infrastructure on, and that `/capture` was the wrong home (category error — improvement detection vs success detection have inverted semantic directions).

## The distinction that matters

There are two completely different things conflated under "success":

- **(a) Operator praise** — "good job." Self-reinforcing: the operator's continued use IS the reward. Already encoded as skill retention and system evolution. **Capturing this adds noise.**
- **(b) Structural success** — "this technique worked AND it isn't documented." The real gap: patterns that are load-bearing but invisible, at risk of being lost if the system changes.

The corrected approach detects **(b)**, not **(a)**. This follows [[mechanical-enforcement-over-behavioral-reminder]]: the detection criteria are structural (documentation-gap-shaped), not behavioral (reaction-shaped). The detection criteria are:
1. Non-obvious technique was used (not just "ran the right command")
2. Successful outcome (work completed, operator didn't correct)
3. Not already documented in wiki/skills/AGENTS.md
4. Transferable (generalizes beyond the current task)

Operator lexical praise is **explicitly excluded** from the detection criteria.

## Why lexical praise detection is dangerous

The /tp critique identified these failure modes, in severity order:

1. **Sycophancy amplification** — the killer. Build a system that rewards operator praise and the agent optimizes for praise. This is the documented RLHF proxy-reward problem: optimizing for the proxy (praise) decouples from the true reward (operator success). Directly conflicts with the workspace's anti_sycophancy protections.

2. **False positives** — "Perfect" said sarcastically. "Excellent — now undo that." Lexical detection cannot distinguish praise from sarcasm or directive context.

3. **Survivorship bias** — "I did X and the operator was happy" doesn't mean X caused the happiness. Capturing success without mechanism produces cargo-cult recipes.

4. **Signal dilution** — if every "good" gets captured, high-value patterns get buried in noise.

## What this means for our workspace

The corrected approach is implemented across three mechanisms:

| Mechanism | What it does | Detection method |
|---|---|---|
| `/capture` category 7 | Transferable success patterns | LLM judgment: non-obvious + worked + not documented + transferable |
| `/notice` T11 | Inline mid-conversation trigger | Same structural detection; surfaces "consider formalizing this" |
| AGENTS.md "Positive framing" | Always-on principle | "When you do something well, notice it and formalize it" |

All three detect **documentation gaps** (pattern used + not documented), not **operator reactions**. This is the sycophancy-safe design.

The concept→application gap (captured principles not followed in code) is related but distinct — it cannot be detected by mechanical scan. The scan confirmed that WIKI marker → concept completion is 92% (healthy), but concept → code compliance requires semantic analysis, not grep. This is a limitation of mechanical enforcement, not a gap in the success-capture system. See [[self-improving-agent-systems-techniques-and-workspace-gaps]] for the broader self-improvement landscape and [[proactive-ai-volunteering-mechanisms]] for the research base on proactive agent behavior.

## Falsifier

This approach is wrong if:
- Structural success detection produces zero findings (no patterns are load-bearing-but-undocumented)
- The exclusion of lexical praise causes high-value patterns to be missed (operator praise was actually the only signal)
- The anti_sycophancy concern was overstated (the workspace doesn't actually have active anti_sycophancy protections that would conflict)

## Receipts

- **/tp critique output:** subagent 019fb9df-49ab-7680-8c94-ec5e22b2cc41 (2026-07-31) — identified sycophancy amplification, sparse evidence, category error
- **`/capture` category 7:** `~/.grok/skills/capture/SKILL.md` category table (added 2026-07-31, commit `2eb59f8`)
- **`/notice` T11:** `~/.grok/skills/notice/SKILL.md` trigger table v2.3 (added 2026-07-31, commit `2eb59f8`)
- **AGENTS.md "Positive framing":** `~/.grok/AGENTS.md` "Thought-partner standard" section principle 5 (added 2026-07-31, commit `9222360`)
