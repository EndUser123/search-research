---
title: "Completeness Over Curation in Recommendations"
created: 2026-08-01
source: dream-2026-08-01
tags: [recommendation-discipline, honesty, operator-correction, behavioral-rule]
summary: >
  When asked for recommendations, list EVERY item with positive ROI. Do not
  filter to a curated subset. The operator decides what's worth pursuing.
  Curating down withholds information the operator explicitly asked for.
  This is an honesty-discipline issue, not a presentation preference.
agent: grok
host: grok
cognitive_load: 1
verification: multi-source-verified
sources:
  - session-019fbdfb (2026-08-01, 20 wiki ideas correction)
  - session-019f9aff AAR (2026-07-26, E2/E5 filter-before-enumerate)
relations:
  - target: wiki/concepts/overclaiming-under-exploration-to-recommendation-pressure.md
    type: related
  - target: wiki/concepts/no-question-theater.md
    type: related
  - target: wiki/concepts/thought-partner-standard.md
    type: extends
---

# Completeness Over Curation in Recommendations

## Decision context

**The problem:** When asked "what ideas should we consider?" or "what should we do?", the agent filters to a curated "top N" subset, hiding options with positive ROI. The operator corrected this explicitly: "I don't like it when you hide recommendations from me. I don't want only two, I want all of them that have value."

## Key findings

**Two instances of the same correction:**

1. **Session 019fbdfb (2026-08-01):** Agent presented 20 wiki improvement ideas but recommended only 2 as "highest-value." Operator corrected: show all with positive ROI. Rule added to AGENTS.md § Recommendations. Receipt: commit `e881e91`.

2. **Session 019f9aff AAR (2026-07-26):** Operator pushed back on 8-cluster enumeration, wanting filtered presentation WITH confidence tags. The AAR initially interpreted this as "wants filtered, not exhaustive" — but the current session's correction reveals the nuance: the operator wants ALL items, each tagged with confidence. They don't want pre-curated subsets. Receipt: `P:/docs/aars/aar-019f9aff-20260726.md` episodes E2, E5.

**The root cause:** A helpfulness heuristic ("don't overwhelm the user") misapplied to an operator who wants the full landscape. The operator scans and prioritizes himself; he doesn't need the agent to pre-filter. The helpfulness heuristic is appropriate for end-users who don't know what they want — it is inappropriate for a solution architect directing a fleet of AI agents.

**The fix:** AGENTS.md § Recommendations now states: "When asked for recommendations, list every item with positive ROI. Do not filter to a top-N or hide options you think the operator won't pick." The `/slc` skill flags this as an Honesty drift signal.

## What this means for our workspace

This extends the [[thought-partner-standard]] Honesty principle: withholding information the operator asked for is a form of dishonesty, not helpfulness. The [[overclaiming-under-exploration-to-recommendation-pressure]] concept covers the opposite failure (recommending too early); this concept covers the failure of recommending too few after finding many. The [[no-question-theater]] rule is adjacent: both are about giving the operator the information they need to make decisions.

Every skill that outputs recommendation lists (/tp, /www, /review, /risks, /todo, /capture, /aar, /skill-prune, /harvest, /friction) should include a one-line pointer to this rule in their output format section.

**Implementation status:** Rule added to AGENTS.md § Recommendations (line 561, commit `e881e91`). Drift signal added to `/slc` Step 1 Honesty mapping (commit `e881e91`). The `/tp` critique skill is the highest-risk skill for this failure mode — its output is findings tables where the temptation to present only the "most important" is strongest.

**Trade-off:** completeness costs scanning time. A 20-item list takes longer to read than a 3-item list. But the operator has consistently chosen completeness over brevity — he scans and prioritizes himself, and items 4-20 sometimes contain the highest-value insights that the agent would have filtered out.

**Anti-pattern:** "Here are the two highest-value ideas" when 18 more exist. The operator's exact words: "I don't like it when you hide recommendations from me." This is not a presentation preference — it is a trust violation. The agent decided what was worth the operator's attention, which is the operator's job, not the agent's.

## Falsifier

If the operator consistently ignores items beyond the first 2-3 in a recommendation list (never acts on them, never references them), then curation to a top-N would actually save time and the rule should be relaxed. Monitor: do items 4-20 in recommendation lists get acted on? The current session is a positive signal — the operator explicitly asked for the full list and the `/tp` critique of the full 20-item list produced the most valuable findings of the session.

## Sources

- Session 019fbdfb (2026-08-01): AGENTS.md § Recommendations, commit `e881e91`.
- Session 019f9aff AAR (2026-07-26): `P:/docs/aars/aar-019f9aff-20260726.md` E2, E5.

## Auto-related

- [[portable-ai-brain-pattern]]
- [[multi-model-ai-workflow-patterns]]
- [[government-debt-and-fiscal-policy]]
- [[premature-closure-narrative-sufficiency-external-approaches]]
- [[youtube-api-search-list-only-endpoint-for-title-to-video-id]]

