---
title: "Synchronous review → direct write — when staging adds nothing"
created: 2026-07-25
source: session-2026-07-25-why-skill-multi-model
tags: [knowledge-management, review-pattern, staging, wiki-workflow, feedback-loop, design-decision]
summary: >
  For knowledge-capture loops (e.g., /why → wiki concept), staging
  (write to inbox/draft → review → promote to canonical) is only worth
  the complexity when review is ASYNCHRONOUS. When review is SYNCHRONOUS
  at write time, the review IS the gate — staging adds a second location
  to track, a second state to manage, and a promotion step that duplicates
  the review's filter. Pattern: mechanical-gate (write threshold) →
  synchronous cross-model review → direct write to canonical OR drop.
  No staging directory. No operator-as-gatekeeper (the review is the gate;
  operator can delete post-hoc if wrong). Produced by applying
  multi-producer synthesis to /why Step 15; operator corrected the
  synthesis's initial "staging" proposal on these grounds.
agent: grok
host: both
cognitive_load: 2
verification: observed
sources:
  - session-019f9a89 (5-model /why synthesis + operator correction, 2026-07-25)
  - C:/Users/brsth/.grok/skills/why/SKILL.md (v3 Step 15 implementation)
relations:
  - target: wiki/concepts/multi-producer-cross-model-synthesis.md
    type: produced-by — this decision came out of that methodology
  - target: wiki/concepts/inline-conditional-over-dispatch-for-skill-design.md
    type: sibling — produced by the same methodology run
  - target: wiki/concepts/instruction-to-state-closure-gap-obligation-ledger.md
    type: complements — both target "stated intent must produce action"
---

# Synchronous review → direct write — when staging adds nothing

## Decision context

**The problem behind this principle:** `/why` Step 15 (feedback-to-wiki loop) had three candidate designs on the table:

1. **Defer to operator-invoked /wiki** — operator manually promotes findings. Problem: relies on operator memory (the biological-backstop anti-pattern AGENTS.md warns against). Findings evaporate.
2. **Auto-write directly to canonical `concepts/`** — no gate. Problem: unreviewed findings pollute `/wiki query` results; future investigations inherit errors.
3. **Auto-write to `inbox/` staging with `draft` flag → review → promote** — the Git staging-area pattern. Preserves findings without polluting canonical. Initial synthesizer recommendation.

The operator pushed back on (3): "if a [synchronous cross-model review] answers the question well, why do we need to stage?" The synthesis had implicitly assumed async review. Synchronous review dissolves the case for staging.

## The principle

**Staging earns its keep ONLY when review is async OR the reviewer can't run.** When review is synchronous at write time, the review IS the gate — staging adds a second location to track, a second state to manage, and a promotion step that duplicates the review's filter. Drop staging in that case.

| Review timing | Without staging | With staging |
|---|---|---|
| Synchronous, passes | write to canonical ✅ | redundant overhead |
| Synchronous, fails | drop finding | redundant (already dropping) |
| Async (review later) | drop finding = evaporation, OR write unreviewed to canonical = contamination | **preserves finding for retry** |
| Reviewer unavailable | drop = evaporation, OR contaminate | preserves for retry |

Staging's only real job: **fallback for async review or reviewer-unavailable**. Not the primary design.

## The synchronous-review-direct-write pattern

```
1. MECHANICAL GATE (write threshold) — runs first, milliseconds
   - Classification is in the wiki-worthy set (e.g., architecture,
     recurring model-behavior)
   - Has a falsifier (not a tautology)
   - Has a verification receipt (Tier 1 or Tier 2 claim backing it)
   - Named abstractly (pattern name, not incident name)
   - Cross-session reusable
   If any fails → SKIP (finding stays in session output only).

2. SYNCHRONOUS CROSS-MODEL REVIEW — runs if gate passes (~30-60s)
   - Independent model (cross-family preferred) answers N yes/no
     questions: generalizes? receipt real? falsifier falsifiable?
   - All "yes" → write. Any "no" → drop. "Modify" → apply, then write.

3. WRITE OR DROP — runs after review
   - All-pass → write directly to canonical with `status: reviewed`.
   - Any-fail → drop. Note in output: "rejected by review (reason)".

4. OPERATOR ROLE
   - NOT a gate. Operator is informed, not asked.
   - Can delete post-hoc if wrong (canonical is mutable).
   - The mechanical gate + cross-model review ARE the quality filters.
```

## Why this works (and staging doesn't, for sync review)

### 1. Synchronous review IS the gate

The entire point of staging is "we don't trust the write-time filter, so we delay canonical promotion until a separate review." If the write-time filter is a real review (cross-model, structured questions, drop-on-fail), the trust is already there. Staging becomes a second gate that runs the same filter one more time.

### 2. Staging duplicates state

With staging, a finding has THREE states: `draft` (in inbox) → `reviewed` (in inbox, post-review) → `promoted` (in canonical). The promotion step is a `git mv` + flag flip. That's three states to track, three failure modes (lost inbox, never-reviewed, never-promoted). Synchronous review collapses to TWO states: dropped or written. Simpler.

### 3. Operator-as-gatekeeper is the wrong shape

Operator memory and attention are the scarce resources. A design that requires the operator to review and promote each finding is a design that lets findings evaporate (operator forgets) or pile up (operator dreads the backlog). Synchronous cross-model review automates the judgment; the operator can veto post-hoc without being the bottleneck.

### 4. Async-review fallback is a separate problem

Staging IS the right answer when the reviewer is genuinely async (e.g., the operator wants to read every finding themselves before it goes to canonical, and they're willing to wait). But that's a different workflow than "the skill captures findings automatically." For the auto-capture case, synchronous review is the right shape; staging is the wrong shape.

## Worked example — /why Step 15 (v3)

**v2 design (operator-confirm):**
```
1. Finding passes classification threshold
2. Ask operator: "Write wiki concept?"
3. If yes, invoke /wiki
```

Problem: operator forgets → finding evaporates (the evaporation problem this whole step exists to solve).

**Initial synthesis proposal (staging):**
```
1. Finding passes mechanical gate
2. Write to wiki/inbox/<slug>.md with status: draft
3. Promotion review (cross-model) → status: reviewed
4. Operator approves → git mv to wiki/concepts/<slug>.md
```

Problem: redundant state if review is synchronous. Operator-as-gate still present.

**v3 design (synchronous review → direct write):**
```
1. Finding passes mechanical gate (15a: 5 criteria)
2. Synchronous cross-model review (15b: glm or codex, 3 yes/no questions)
3. All-pass → write directly to concepts/ with status: reviewed
   Any-fail → drop. Reviewer unavailable → drop.
4. Operator informed, not asked.
```

Same quality filter, half the states, no operator bottleneck.

## When staging DOES win (the steelman)

- **Review is genuinely async** — e.g., operator-curated wiki where every concept must be read by a human before going to canonical. Synchronous review can't substitute for human reading.
- **Reviewer availability is unreliable** — if the cross-model pool is frequently down (serde errors, quota), staging preserves findings for retry. The /why v3 design accepts evaporation in this case ("if it becomes frequent, revisit") rather than adding the staging complexity preemptively.
- **The canonical store is read by downstream automations with high false-positive cost** — e.g., if `/check` automatically enforces every concept in canonical, a wrong concept is worse than a missing one. Staging prevents the wrong concept from landing. (Note: this argues for stronger review at write time, not necessarily for staging — but staging is one valid answer.)
- **Legal/compliance requires human sign-off** — outside the scope of this workspace, but worth naming.

These were not the case for /why → wiki: the reviewer pool has at least 3 working cross-family members (glm, codex, parent-inherited), and the wiki has no high-false-positive-cost downstream automation yet. So synchronous review won.

## Falsifier

This pattern is wrong if, within 6 months:
- **Wrong concepts consistently land in canonical** despite passing both gates — the mechanical gate is too loose OR the cross-model review is rubber-stamping. Fix: tighten the gate, switch reviewer model, or fall back to staging.
- **Reviewer unavailability becomes the dominant failure mode** — the drop-on-unavailable rule causes evaporation at scale. Fix: add inbox as a fallback (preemptively, this time — not preemptively the first time around).
- **The mechanical gate is so strict that nothing ever passes** — Step 15 never fires. Fix: relax the criteria.
- **The operator ends up manually promoting every concept anyway** — the synchronous review isn't trusted; staging + operator-as-gate would have been more honest about who the actual reviewer is.

## What this means for our workspace

- **Apply this pattern to any skill that auto-writes to canonical state** (/why → wiki, /aar → dispositions, /debrief → action items, future /check rules).
- **Mechanical gate first, cross-model review second, direct write third.** No staging.
- **Track reviewer-unavailable rate.** If it rises, revisit (staging may earn its keep).
- **Do not apply to operator-curated workflows** where the human IS the reviewer by design. Staging is correct there.

## Methodology roots

- Produced by applying [[multi-producer-cross-model-synthesis]] to /why Step 15
- Initial synthesis proposed staging; operator pushed back ("if A3's review is synchronous, why do we need to stage?")
- Synthesis updated: staging only earns its keep for async review; drop it for sync
- See `/why` SKILL.md Step 15 for the implemented version
- Related to [[instruction-to-state-closure-gap-obligation-ledger]] — both target "stated intent must produce action in the same turn"
- Related to [[no-question-theater]] (referenced from `~/.grok/AGENTS.md`) — operator-as-gatekeeper is question theater; the gate is the review

Sibling: [[inline-conditional-over-dispatch-for-skill-design]] — the other design decision from the same synthesis run. Both are instances of "prefer the simpler design when the simpler design's failure mode is already covered by another gate."
