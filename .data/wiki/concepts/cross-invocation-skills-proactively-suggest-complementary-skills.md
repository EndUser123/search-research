---
title: "Cross-invocation: skills proactively suggest complementary skills"
created: 2026-07-31
source: session-019fb177 (/recap ↔ /handoff enhancement)
tags: [skill-design, cross-invocation, proactive, skill-graph, transferable-pattern, routing]
summary: >
  When two skills share data sources but serve different purposes (retrospective
  vs forward-looking, detection vs resolution, measurement vs improvement), each
  should detect when the other adds value and proactively suggest it. The operator
  shouldn't have to know which skill to invoke next — the skills should tell them.
  First implementation: /recap suggests /handoff when pending work is detected;
  /handoff suggests /recap when session complexity is high. The general pattern
  applies to other complementary pairs.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "Session 019fb177: /recap ↔ /handoff enhancement"
relations:
  - target: wiki/concepts/meta-level-proactivity-three-fixes-skill-graph-mapping.md
    type: refines
  - target: wiki/concepts/skill-usability-audit-cold-read-critique.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# Cross-invocation: skills proactively suggest complementary skills

## Decision context

**Why this was needed:** after enhancing `/recap` with retrospective synthesis and `/handoff` with a complexity check, the agent noticed the pattern: "these two skills share the same data source (session transcripts) but serve different time orientations. Each should detect when the other adds value and suggest it." The operator asked: how do we proceed with generalizing this?

**The decision:** capture the pattern as a wiki concept and let the meta-checkpoint (AGENTS.md Q4: "did I map this across the skill graph?") drive future integrations. Do NOT batch-edit every skill pair now — each integration is better made by a future session that's actually working on the target skill and has real context for what the cross-invocation should look like.

## The pattern

Two skills are **complementary** when they share a data source or domain but serve different purposes. When skill A finishes and its output contains signals that skill B would add value, skill A should actively suggest skill B — with the specific topic/path extracted, not a passive routing table.

### Identified complementary pairs

| Pair | Shared domain | Different purpose | Cross-invocation |
|------|--------------|-------------------|------------------|
| `/recap` → `/handoff` | Session transcripts | Retrospective (backward) vs continuation (forward) | `/recap` suggests `/handoff <topic>` when pending work detected; `/handoff` suggests `/recap` when session is complex |
| `/recap` → `/debrief` | Session transcripts | Catch-up vs improvement extraction | `/recap` suggests `/debrief` when operator corrections detected |
| `/recap` → `/wiki` | Session knowledge | Catch-up vs durable capture | `/recap` suggests `/wiki` when transferable patterns not yet captured |
| `/tp` → `/review` | Adversarial analysis | Critique vs verified findings on disk | Potential: `/tp` could suggest `/review` when the critique surfaces code-quality findings that need source verification |
| `/why` → `/handoff` | Failure investigation | Root cause vs continuation | Potential: `/why` could suggest `/handoff` when the RCA reveals work that needs continuation |
| `/check` → `/close` | Verification | Per-concern verification vs session close | `/check` could suggest `/close` when all concerns pass |
| `/harvest` → `/wiki` | Unrealized value | Obligation recovery vs knowledge capture | `/harvest` could suggest `/wiki` when recovered value includes transferable knowledge |
| `/aar` → `/handoff` | Session review | Lessons vs continuation | `/aar` already produces handoff-ready output; could suggest specific `/handoff` topics from opportunity landscape |

### Design principle

The cross-invocation is **advisory, not gating**. Skill A works fine without skill B. The suggestion is about quality, not correctness. The operator decides whether to follow it.

The suggestion is **active, not passive**. Not a routing table at the bottom ("for X, use /Y"). Instead, a specific recommendation at the end of the output: "This session has 3 pending work items. Run `/handoff ship-receipt-enhancements` to create continuation handoffs."

### Anti-pattern: over-coupling

If every skill suggests every other skill, the suggestions become noise. The pattern fires only when the complementary skill's value is **evident from the current skill's output** — not speculative. "Pending work detected" is evident. "You might want to review this" is speculative.

## Steelman of the rejected alternative

**Rejected: batch-edit all identified pairs now.**

**Why it was reasonable:** front-loading ensures consistency. Every skill gets the pattern at the same time. No skill is left behind.

**Why it loses:** each cross-invocation is better designed by a session that's actually working on the target skill. The `/recap → /handoff` suggestion was designed correctly because we had deep context on both skills from this session. A batch edit to `/check → /close` made without context on `/check`'s current output format would produce a generic suggestion that doesn't match real output.

The meta-checkpoint (Q4: "did I map this across the skill graph?") ensures future sessions that touch `/check`, `/review`, `/why`, etc. will ask "should this cross-invoke?" The pattern propagates organically, one skill at a time, with real context.

## Falsifier

This pattern is wrong if:
- The suggestions are always ignored (the operator never follows them) — meaning the detection logic is wrong or the suggestion adds no value
- The suggestions create noise (too many fire for a single invocation) — mitigated by the "evident from output" constraint
- The complementary pairs identified above turn out not to be complementary in practice — discoverable when a future session touches the pair and finds no natural cross-invocation point
- The meta-checkpoint doesn't reliably fire on future sessions — the behavioral gap returns, and the pattern doesn't propagate

## What this means for our workspace

The pattern is captured. The first implementation (`/recap ↔ /handoff`) is shipped and committed. Future integrations happen when future sessions touch the target skills — driven by the meta-checkpoint Q4, not by a batch-edit campaign.

The `/skill-dev` Mode 2 Step 7 (graph-projection) is the scheduled mechanism for catching pairs that haven't been integrated yet: when `/skill-dev improve` runs on a skill, Step 7 scans for complementary skills and proposes cross-invocations as improvement candidates.

Related: [[meta-level-proactivity-three-fixes-skill-graph-mapping]] — the parent concept. Cross-invocation is a specific application of "map this across the skill graph" to the skill-routing domain. This is the same [[mechanical-enforcement-over-behavioral-reminder]] principle: a passive routing table is a behavioral signal (low compliance); an active suggestion with extracted topic is closer to mechanical enforcement (the suggestion fires when the condition is detected). The [[skill-usability-audit-cold-read-critique]] technique applies to cross-invocation tables too — a fresh agent should be able to read the suggestion and know exactly what to do.

## Receipts

- `/recap` cross-invocation: `skills/recap/SKILL.md` § "Cross-invocation" (commit `1f38689`)
- `/handoff` complexity check: `skills/handoff/SKILL.md` § "Default invocation" Step 0 (commit `1f38689`)
- Meta-checkpoint Q4: `~/.grok/AGENTS.md` § "Meta-checkpoint before claiming DONE" (commit `6a58fa2`)
- `/skill-dev` Step 7: `skills/skill-dev/SKILL.md` § "Step 7 — Graph-projection" (commit `6a58fa2`)
