---
thread_id: verdict-vocabulary-hook-20260809
parent_handoff_path: none
current_session_id: 019fe673-8b5c-7ee0-a22e-f1765ae9860b
current_terminal_id: grok
produced_at: 2026-08-09T21:00:00Z
last_updated_by: 019fe673-8b5c-7ee0-a22e-f1765ae9860b
last_updated_at: 2026-08-09T21:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 1c63a2f
---

# Verdict-vocabulary + recommendation-presence output validator

## Objective

Design and ship a Stop hook (or output validator) that scans `/risk`, `/tp`, and `/design` outputs for two mechanical framing errors: (1) verdict tokens outside the skill's documented vocabulary, and (2) options presented without a single recommended action.

## Status

**OPEN — design needed, not yet implemented.** This is the 4th+ session the closure-pressure pattern has surfaced. The pattern is chronic; the fix is structural (hook), not prose.

## Producing context

- Date: 2026-08-09
- Session: `019fe673-8b5c-7ee0-a22e-f1765ae9860b`
- Trigger: `/aar` headline lesson L1 + `/insight` interaction friction finding
- Host: Grok Build
- Confidence: H (pattern is chronic across 4+ sessions; this session produced 2 instances)

## The problem

Two closure-pressure failure modes recur across sessions despite existing AGENTS.md rules:

### Failure 1: Invented verdict vocabulary

Each skill defines its own verdict vocabulary:
- `/risk`: `PROCEED | FIX FIRST | DON'T DO THIS`
- `/tp`: `PROCEED | REVISE | BLOCK`
- `/design` (reviewer): `0 critical/major` (numeric, not named)

Under closure pressure, the agent invents hybrid verdicts not in the vocabulary:
- "PROCEED WITH CAVEATS" (this session, `/risk` — not in the skill's 3-verdict vocabulary)
- "PROCEED conditionally" (prior sessions)

This is mechanically detectable: the verdict token doesn't match any documented value.

### Failure 2: Options without recommendation

AGENTS.md § "Recommendations" requires: "present alternatives only when there is genuine uncertainty on a real axis... When the path is clear, recommend ONE solution and say so explicitly."

Under closure pressure, the agent presents options without committing:
- "Here are the options..." (without "I recommend X because Y")
- "You could do A, B, or C" (without selecting one)

This is detectable: output contains ≥3 options but no sentence matching the recommendation pattern (`I recommend | the answer is | do X first`).

## Verified facts (with source paths)

1. **[FACT, receipt: this session transcript turn 17]** Operator pushback: "where's your recommendation? Did you present a false choice?" — forced `/risk` verdict from "PROCEED WITH CAVEATS" to "FIX FIRST."
2. **[FACT, receipt: this session AAR report §Headline lessons L1]** "Closure-pressure produces framing failures that prose rules don't prevent." The AAR classified this as GENERAL scope, OBSERVED confidence, chronic across sessions.
3. **[FACT, receipt: `~/.grok/AGENTS.md` § "Recommendations"]** The no-false-choices rule exists and explicitly bans options-without-recommendation.
4. **[FACT, receipt: `/risk` SKILL.md Phase 6 REPORT]** Verdict vocabulary: `PROCEED | FIX FIRST | DON'T DO THIS`. No "PROCEED WITH CAVEATS" variant.
5. **[FACT, receipt: `/tp` SKILL.md Step 3]** Verdict vocabulary: `PROCEED | REVISE | BLOCK`.
6. **[FACT, receipt: `/insight` SKILL.md interaction friction]** Category: Repeated Problems (no learning loop from corrections — the rules exist, they don't fire).

## Open questions

1. **Hook vs output validator?** A Stop hook blocks the turn; an output validator runs post-turn and warns. The hook is stronger but may false-positive on legitimate nuanced verdicts. The validator is advisory but doesn't prevent the error in real-time.
2. **Which skills to cover?** Start with `/risk` and `/tp` (highest verdict-vocabulary violation rate). Extend to `/design` if the pattern recurs there.
3. **Recommendation detection regex?** What pattern matches "I recommend X" vs "you could do X"? Needs tuning to avoid false positives on legitimate multi-option explorations.
4. **Escape hatch?** When the agent has a legitimate reason for a nuanced verdict (e.g., "PROCEED after fixing N items"), should the hook allow a `[JUSTIFIED_VARIANCE]` tag?

## Acceptance criteria

1. Hook (or validator) runs on every `/risk` and `/tp` output
2. Invented verdict tokens produce a block or warning with the allowed vocabulary listed
3. Options-without-recommendation (≥3 options, no recommendation sentence) produce a block or warning
4. False positive rate <10% on a 20-turn sample of legitimate outputs
5. The hook itself has a verdict-vocabulary for its own output (eat your own dog food)

## Suggested skills for the next session

- `/design` to design the hook contract (verdict regex, recommendation pattern, escape hatch)
- `/go` to implement once designed
- `/check` to verify the hook fires correctly on test inputs

## Falsifier

This handoff is wrong if:
- A review of 20 prior sessions shows the verdict-vocabulary violation rate is <5% (the pattern is rarer than this session suggests; the hook isn't worth the complexity)
- The existing AGENTS.md rules fire reliably after a different intervention (e.g., EGDP template, system-prompt change) — making the hook redundant
- The hook's false positive rate exceeds 20% on legitimate outputs (too noisy to ship)

## Related wiki concepts

- [[closure-pressure-assumes-framing-is-right]] (to be written — AAR tacit gap #1)
- [[prior-session-fact-vs-this-session-fact-pattern]] (written this session — adjacent pattern: evidence discipline)
- [[narrative-as-signal]] (broader pattern: plausible narrative substituting for evidence)

## Other outstanding streams

- `review-relay-improvements-impl-20260809` — the 15-unit implementation plan (this hook workstream was surfaced during its /risk assessment but is independent of the relay implementation)

---

## Last user message (verbatim)

```
/handoff
```