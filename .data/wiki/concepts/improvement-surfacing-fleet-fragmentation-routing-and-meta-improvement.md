---
title: "Improvement-surfacing fleet: fragmentation, routing, and the meta-improvement layer"
created: 2026-07-31
source: session-20260731
tags: [skill-design, meta-improvement, skill-routing, fragmentation, continual-improvement, kaizen, skill-fleet, coordination]
summary: >
  The workspace has 12+ skills that surface improvement ideas across 5 timeframes
  (per-turn, mid-session, session-end, cross-session, fleet-level). They overlap
  significantly with no routing entry point. The SkillRouter paper (Alibaba 2026,
  arXiv:2603.22455) shows that at 80K skills, full-text body is a 31-44pp stronger
  routing signal than metadata — suggesting our skill catalog needs richer indexing
  as it grows. The existing wiki concept [[self-improving-agent-systems-techniques-and-workspace-gaps]]
  documents 5 gaps; this concept adds a 6th: improvement-surfacing coordination.
  The Kaizen framing (continuous improvement as a system, not a collection of tools)
  provides the lens: each skill owns one detection layer, the routing is explicit,
  and the improvement backlog flows through a single triage path.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - "https://arxiv.org/html/2603.22455v3 (Zheng et al., Alibaba Group, Mar 2026) — SkillRouter: full-text body is critical routing signal at 80K skill scale"
  - "https://kaizen.com/insights/intersection-ai-kaizen-continuous-improvement/ (Kaizen Institute, 2024) — AI + Kaizen symbiosis for continuous improvement"
  - "P:/.data/wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md — existing 5-gap analysis"
relations:
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: extends
  - target: wiki/concepts/inter-skill-output-bridges-and-temporal-surfacing-layers.md
    type: complements
  - target: wiki/concepts/proactive-ai-volunteering-mechanisms.md
    type: related
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: related
---

# Improvement-surfacing fleet: fragmentation, routing, and the meta-improvement layer

## Decision context

**Why this was needed:** during session 2026-07-31, the operator asked "/wiki
what skills do we have that can surface improvement ideas?" The inventory
revealed 12+ Grok-native skills that surface improvements, with significant
overlap and no single routing entry point. The operator then asked "/www how
can we improve our improvement ideas, or the skills that surface them?" — a
meta-improvement question: how do we make the improvement-detection fleet
itself better?

The existing wiki concept [[self-improving-agent-systems-techniques-and-workspace-gaps]]
documents 5 gaps (improvement kata, self-evolving skills, proactive anticipation,
curiosity-driven exploration, "could you be wrong" prompt). But it doesn't
address the coordination problem: when 12 skills detect the same kind of
thing, how do they avoid redundancy without losing coverage?

## The current fleet (as of 2026-07-31)

### Mid-session (real-time)

| Skill | Surfaces | Trigger |
|---|---|---|
| `/notice` | Workflow automation (T9), connections (T7), anticipated needs (T8), unverified diagnoses (T6) | Content-triggered, motivation-scored |
| `/friction` | Interaction friction + workflow automation gaps | Operator-invoked, transcript scan |

### Session-end

| Skill | Surfaces | Scope |
|---|---|---|
| `/tp session` | 3 standing questions: composition, propagation, improvement + CROSS-DOMAIN NOTICES | Broadest session scan |
| `/debrief` | 5 lenses: root causes, code quality, workflow friction, knowledge gaps, patterns | Subagent fan-out |
| `/aar` | Value accounting, opportunity landscape, continual-improvement governance | Deep retrospective |

### Cross-session

| Skill | Surfaces | Timeframe |
|---|---|---|
| `/harvest` | Unrealized obligations, error patterns, cross-session pattern detection | Event-sourced |
| `/dream` | Cross-session patterns from 90 days of artifacts | Offline, operator-promoted |
| `/skill-dev` | Skill marginal contribution from retrospective evidence | Per-skill measurement |
| `/maintain` | Workspace health: git, catalog, wiki, config, hooks | Fleet diagnostic |
| `/todo` | Unfinished work, unreviewed research, open threads | ADHD-friendly prioritized list |

### The overlap matrix

| Function | Overlapping skills | Problem |
|---|---|---|
| Session-level improvements | `/tp session` ↔ `/debrief` ↔ `/aar` | Three skills scanning same session |
| Mid-session friction | `/notice` ↔ `/friction` | Two skills detecting real-time friction |
| Open obligations | `/harvest` ↔ `/todo` | Two skills surfacing unfinished work |
| Skill quality | `/skill-dev` ↔ Claude-side `skill-audit` | Two skills evaluating skill health |
| Cross-session patterns | `/dream` ↔ `/harvest` | Two skills synthesizing across sessions |

## What the research says

### SkillRouter (Alibaba, arXiv:2603.22455) — routing at scale

The SkillRouter paper studies skill routing with ~80K skills and finds:

1. **Full-text body is a critical routing signal.** Removing the skill body
   causes 31-44 percentage point drops in routing accuracy across BM25,
   encoder-only, and reranker baselines. Name + description alone is
   insufficient when skills overlap heavily.

2. **False-negative filtering is essential in homogeneous pools.** When
   multiple skills serve the same function, mined negatives inevitably
   include functionally-equivalent skills. Treating them as negatives
   corrupts the contrastive signal.

3. **Listwise reranking beats pointwise by 30.7pp.** Once the pool is
   narrowed to similar candidates, the router must compare candidates
   against each other, not score each independently.

**Applicability to our fleet:** our ~100-skill fleet is far smaller than
80K, but the overlap problem is the same in miniature. `/tp session`,
`/debrief`, and `/aar` are functionally overlapping skills for
session-level improvement detection. The SkillRouter finding suggests
that as the fleet grows, a formal routing layer (not just the skill
catalog's name+description metadata) will be needed to prevent the
operator from having to know which tool to invoke.

**Applicability check:** our fleet is ~100 skills, not 80K. The 31-44pp
body-vs-metadata gap may not apply at our scale — name+description may
be sufficient routing at 100 skills. The finding is directional (richer
indexing helps), not quantitatively transferable. The false-negative
filtering and listwise comparison insights DO apply: our overlapping
skills ARE functionally equivalent, and the operator must compare them
against each other to pick the right one.

### Kaizen + AI — improvement as a system

The Kaizen framing provides a different lens: continuous improvement is
not a collection of tools, it's a *system* with:
- **Detection** (find waste/friction) → our `/notice`, `/friction`, `/tp session`
- **Triage** (prioritize what to fix) → our `/todo`, `/harvest`
- **Implementation** (make the change) → our `/go`, `/refactor`
- **Verification** (confirm it worked) → our `/check`, `/review`
- **Consolidation** (capture learning) → our `/wiki`, `/aar`

The Kaizen system's strength is the *flow* between layers — each step
feeds the next. Our fleet has strong individual layers but weak flow
between them. `/notice` detects friction but doesn't feed `/harvest`.
`/tp session` finds composition opportunities but doesn't feed `/skill-dev`.
The inter-skill output bridges pattern (documented in
[[inter-skill-output-bridges-and-temporal-surfacing-layers]]) is the
mechanism for improving the flow.

## The 6th gap (extends the existing 5-gap analysis)

[[self-improving-agent-systems-techniques-and-workspace-gaps]] documents
5 gaps: (1) improvement kata, (2) self-evolving skill engine, (3) proactive
anticipation, (4) curiosity-driven exploration, (5) "could you be wrong?"
prompt. This concept identifies a 6th:

**Gap 6: Improvement-surfacing coordination.** The fleet has 12+ skills
that surface improvements, but no routing layer, no shared backlog, and
no dedup mechanism. An idea surfaced by `/notice` mid-session won't appear
in `/tp session` unless re-detected. An improvement found by `/debrief`
won't reach `/skill-dev` unless manually routed. The skills detect well
individually but don't compose into a continuous-improvement system.

## What this means for our workspace

### Short-term (coordination without new skills)

The inter-skill output bridges pattern (from this session) is the lightest
coordination mechanism. Each improvement-surfacing skill emits its findings
as structured output sections that downstream skills can consume:

| Producer | Output section | Consumer |
|---|---|---|
| `/notice` | `Note:` observation (one-liner) | `/tp session` (reads notes from transcript) |
| `/tp session` | Actionable recommendations + harvest items | `/harvest`, `/skill-dev`, `/wiki` |
| `/debrief` | 5-lens findings | `/harvest`, `/wiki` |
| `/aar` | Opportunity landscape + dispositions | `/harvest`, `/todo` |

This is already partially working: `/tp session` writes to `harvest/pending/tp.json`,
`/harvest` reads from it. Extending this pattern to all improvement-surfacing
skills creates a shared improvement backlog without a new skill.

### Medium-term (routing layer)

As the fleet grows, a routing entry point becomes necessary. The `/todo`
skill is the closest existing candidate — it already scans the workspace
and produces a prioritized list. Extending `/todo` to also scan for
improvement opportunities (not just unfinished work) would create a single
entry point: "what should I work on?" → `/todo` routes to either unfinished
work or improvement opportunities.

### What NOT to do

**Do not build a new "meta-improvement orchestrator" skill.** The fleet
already has too many overlapping skills. Adding another coordinator skill
increases the overlap problem rather than solving it. The fix is routing
and output bridges between existing skills, not a new skill on top.

## Falsifier

This analysis is wrong if, within 6 months:

- The 12+ improvement-surfacing skills are consolidated to 3-4 (the overlap
  was real and the solution was dedup, not coordination) — then the routing
  problem was self-solving
- The skills already compose well enough that the operator never experiences
  the fragmentation (the overlap is theoretical, not practical) — then the
  problem doesn't need solving
- A new skill IS needed despite the "don't build a new skill" guidance, and
  it works better than extending existing skills — then the guidance was wrong
- The SkillRouter finding doesn't apply at our scale (~100 skills) and
  metadata-only routing is fine — then the "richer indexing" recommendation
  is premature

## Receipts

- `P:/.data/wiki/concepts/skill-catalog.md` — the 12+ skills inventoried in this concept (lines 35-77)
- `~/.grok/skills/notice/SKILL.md` T9 trigger (added 2026-07-31, commit `bc89b06`) — workflow automation detection
- `~/.grok/skills/tp/SKILL.md` § CROSS-DOMAIN NOTICES (3 standing questions, added 2026-07-31) — session-end composition/propagation/improvement scan
- `P:/.data/wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md` — the existing 5-gap analysis this extends
- `P:/.data/wiki/concepts/inter-skill-output-bridges-and-temporal-surfacing-layers.md` (written this session) — the output-bridge coordination pattern
