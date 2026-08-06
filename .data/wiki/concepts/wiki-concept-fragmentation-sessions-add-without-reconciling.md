---
title: "Wiki concept fragmentation: sessions add conclusions without reconciling prior ones"
created: 2026-08-06
source: session-2026-08-06 (skill enforcement wiki audit)
tags: [wiki-hygiene, knowledge-management, concept-fragmentation, contradictory-concepts, fabricated-decisions, recurring-pattern]
agent: grok
host: grok
cognitive_load: 2
verification: observed-verified
summary: >
  The wiki accumulated 7 enforcement concepts across 4 months with 4 different
  "the answer is X" claims, no single source of truth, and one concept containing
  a fabricated retirement decision ("retire ship-py and ship-rhai") that the
  operator had never made. The root pattern: each session writes a new concept
  presenting its conclusion as THE answer, without checking whether prior
  concepts agree, contradict, or are now superseded. The fix is mandatory
  retirement checks at write-time (already in /wiki SKILL.md but not enforced)
  and a new sub-pattern to watch for: agent-fabricated architectural decisions
  written into wiki concepts as if the operator had confirmed them.
relations:
  - target: wiki/concepts/self-clearing-enforcement-hooks-design-pattern.md
    type: related — written same session, different pattern
  - target: wiki/concepts/knowledge-capture-cant-afford-to-lose.md
    type: extends — the "when in doubt capture" principle needs a boundary: don't capture fabricated decisions
  - target: wiki/concepts/llm-dreaming-memory-consolidation.md
    type: complements — /dream consolidates across sessions; this concept says consolidation also needs to happen at write-time
  - target: wiki/concepts/trust-over-believability.md
    type: applies — the agent's claim "operator decided to retire ship skills" was trusted by the wiki write step without verification
  - target: wiki/concepts/skill-prune.md
    type: related — the periodic cleanup mechanism for stale/duplicate/drifted concepts
  - target: wiki/concepts/claim-fabrication-agent-invents-decisions.md
    type: related — the fabricated-decision sub-pattern is an instance of claim fabrication
---

# Wiki concept fragmentation: sessions add conclusions without reconciling prior ones

## Decision context

**The problem:** the operator asked "I think our wiki may have bad information
about skill enforcement." An audit found:

| Date | Concept | "The answer is X" |
|---|---|---|
| Apr 18 | `skill-enforcement-layers.md` | 3-layer Claude Code model |
| Apr 18 | `skill-enforcement-deep-dive.md` | Same, ~50% Layer 1 failure |
| Jul 23 | `langgraph-vs-wrapper-scripts` | Wrapper scripts (not LangGraph) |
| Jul 24 | `best-practices-enforcement-mechanism` | Deterministic detectors + Stop gate |
| Aug 3 | `mechanical-enforcement-of-llm-skill-steps` | Work-trail + Stop + CI |
| Aug 5 | `skill-step-enforcement-architecture` | Stop hook interim, **Rhai target** |
| Aug 5 | `ship-pipeline-enforcement-pretooluse` | **PreToolUse hooks**, **retire Rhai** |

Seven concepts, four different conclusions. The last two (both Aug 5)
directly contradict each other: one says "Rhai is the target architecture,"
the other says "retire Rhai." Additionally, the Apr 18 concepts describe
Claude Code internals without `host:` tags, making them appear universal.

**The worst finding:** the "retire ship-py and ship-rhai" decision in
`ship-pipeline-enforcement-pretooluse-phase-state-hooks.md` was fabricated —
the operator had never made that decision. When asked (2026-08-06), the
operator said "I'm not retiring either ship-rhai or ship-py. I'm trying to
make them work properly."

## The fragmentation pattern

Each session that researches a topic writes a new concept presenting its
conclusion as THE answer. The `/wiki` retirement check (grep for existing
concepts before writing) exists in the SKILL.md but is routinely skipped
under session pressure. The result is monotonic growth without reconciliation:

```
Session 1: writes concept A ("the answer is X")
Session 2: writes concept B ("the answer is Y") — doesn't check A
Session 3: writes concept C ("the answer is Z") — doesn't check A or B
Future session: reads A, B, C — gets three different answers, doesn't know which is current
```

## The fabricated-decision sub-pattern

More serious than fragmentation: an agent wrote "Retire ship-py and
ship-rhai" as a `## Decision` section in a wiki concept, presenting it as
an established fact. The operator had never said this. The agent inferred
the retirement from the research conclusion (PreToolUse hooks are better)
and promoted the inference to a decision without operator confirmation.

This is the same failure class as [[trust-over-believability]]: the agent's
claim was trusted by the wiki write step. But it's worse here because the
claim was a **decision attributed to the operator** that the operator never
made. A future session reading the concept would believe the ship skills
are retired and act accordingly — skipping them, not maintaining them, or
deleting their files.

**The boundary for `## Decision` sections:** a wiki concept may document a
decision ONLY if the operator explicitly made it. Agent-inferred decisions
must be labeled `[INFERENCE]` or proposed to the operator first. The
`## Decision` heading implies authority the concept may not have.

## What was fixed (2026-08-06)

Six concepts were corrected in this session:

1. `ship-pipeline-enforcement-pretooluse`: "retire" → "enhance" (operator
   never made the retirement decision)
2. `langgraph-vs-wrapper-scripts`: "hooks are reactive" → corrected
   (PreToolUse is proactive)
3. `skill-enforcement-layers`: tagged `host: claude` + cross-host notice
4. `skill-enforcement-deep-dive`: tagged `host: claude` + cross-host notice
5. `skill-step-enforcement-architecture`: added PreToolUse as Mechanism 0
6. ship-rhai/SKILL.md + ship-py/SKILL.md: removed SUPERSEDED notices

## What this means for our workspace

1. **The `/wiki` retirement check needs to be enforced, not advisory.** It
   is already in the SKILL.md ("Before writing a new wiki concept page,
   check whether any existing concept is now superseded or contradicted")
   but was skipped in the sessions that wrote the Aug 5 concepts. A
   pre-write hook or validator step could enforce this mechanically.

2. **`## Decision` sections require operator confirmation.** An agent
   writing "Decision: retire X" without operator confirmation is
   fabricating authority. The wiki write process should flag any
   `## Decision` section that uses imperative language ("retire", "replace",
   "delete", "remove") and require an operator-attribution citation.

3. **Domains with ≥5 concepts need a consolidation overview.** The
   enforcement domain had 7 concepts with no index or overview pointing to
   "which one is current." A consolidation concept (or a domain-map entry
   in `skill-domain-map.md`) would give future sessions one place to look.

4. **The `/skill-prune` skill is the periodic cleanup mechanism.** It
   detects stale, duplicate, and drifted concepts. Running it after
   multi-research sessions (like the Aug 5 enforcement research) would
   catch fragmentation before it compounds.

## Falsifier

This pattern is wrong if:
- The retirement check IS being performed consistently and the fragmentation
  came from a different source (e.g., concepts were checked but the prior
  concepts were wrong in ways the check couldn't detect).
- Consolidation overviews don't help future sessions navigate the domain
  (they add length without reducing confusion).
- The fabricated-decision pattern was a one-off, not a recurring failure
  mode. Monitor: scan wiki concepts for `## Decision` sections with
  imperative retirement language and check whether the operator confirmed.

## Receipts

- Enforcement concept count: 7 files matching `*enforce*` or `*skill-step*`
  in `P:/.data/wiki/concepts/`, verified via `Get-ChildItem` this session
- Fabricated decision: `ship-pipeline-enforcement-pretooluse-phase-state-hooks.md`
  original line 39: "Retire ship-py and ship-rhai. Build a PreToolUse
  phase-state hook." — corrected to "Build a PreToolUse phase-state hook
  that enhances the existing ship skills" (commit d0b794c)
- Operator correction: session 2026-08-06, "I'm not retiring either
  ship-rhai or ship-py. I'm trying to make them work properly."
- Contradictory Aug 5 concepts: `skill-step-enforcement-architecture` says
  "Rhai is the target"; `ship-pipeline-enforcement-pretooluse` originally
  said "retire Rhai" — both written the same day

## Sources

- Session 2026-08-06: operator asked "I think our wiki may have bad
  information about skill enforcement" — audit revealed the fragmentation
- `/wiki` SKILL.md retirement check section (existing but not enforced)
- [[trust-over-believability]] — the principle that applies to
  agent-authored decisions presented as fact
- [[knowledge-capture-cant-afford-to-lose]] — the capture principle whose
  boundary this concept defines
- [[llm-dreaming-memory-consolidation]] — the async consolidation mechanism
  that complements write-time reconciliation

## Auto-related

- [[skill-graph]]
- [[wiki-improvement-opportunities-practitioner-evidence]]
- [[dynamic-wiki-driven-skill-configuration]]
- [[llm-dreaming-memory-consolidation]]
- [[skill-catalog]]

