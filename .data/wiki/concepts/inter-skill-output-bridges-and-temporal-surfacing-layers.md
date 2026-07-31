---
title: "Inter-skill output bridges and temporal surfacing layers"
created: 2026-07-31
source: session-20260731
tags: [skill-design, skill-composition, inter-skill-contract, surfacing, workflow-automation, temporal-layering, reusable-pattern]
summary: >
  Two reusable patterns for the skill fleet: (1) inter-skill output bridges —
  one skill emits a structured output section another skill knows how to consume,
  creating composition without coupling; (2) temporal surfacing layers — the same
  check (e.g., workflow automation opportunity) caught at three timeframes
  (per-turn, mid-conversation, session-end) by three different mechanisms, so a
  catch missed at one layer has two more chances. Both patterns emerged from the
  /tp→/www confidence-gap bridge built session 2026-07-31.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "session 019fb49b (2026-07-31): /tp→/www confidence-gap bridge implementation"
relations:
  - target: wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md
    type: extends
  - target: wiki/concepts/coupling-inventory-as-mandatory-design-section.md
    type: related
  - target: wiki/concepts/producer-consumer-contract-drift-in-skill-chains.md
    type: complements
  - target: wiki/concepts/proactive-ai-volunteering-mechanisms.md
    type: extends
  - target: wiki/concepts/extract-moves-not-conditions-tp-enhancements.md
    type: refines
---

# Inter-skill output bridges and temporal surfacing layers

## Decision context

**Why this was needed:** during session 2026-07-31, the operator noticed that
the agent had good ideas (skill composition opportunities, workflow automation
patterns) but only surfaced them when explicitly asked. The specific trigger:
the operator manually routed `/tp`'s low-confidence items to `/www` for
research. The agent executed without volunteering "this composition could be
automated." When asked `/tp does it make sense to add this as a default?`, the
agent produced a strong proposal immediately — the analysis capacity was there,
it just wasn't being volunteered.

This raised two questions: (1) how do skills compose without coupling? (2) how
do we make the agent surface composition opportunities automatically? Both
questions have generalizable answers worth capturing.

## Pattern 1: Inter-skill output bridges

**The pattern:** Skill A emits a structured output section with a stable name
and format. Skill B knows to look for that section and consume it directly,
rather than re-deriving the targets from session context. The bridge is the
named section — it creates composition without code coupling.

**Concrete instance (this session):**

- `/tp` emits `## Research-ready targets (for /www)` with format:
  `N. <claim> — current: [INFERENCE], upgrade via: <what evidence would confirm>`
- `/www` in confidence-gap mode checks for that section first. If present, it
  reads the targets directly instead of scanning the session for low-confidence
  items.

**Why this works without coupling:**

- `/tp` doesn't know `/www` exists — it just emits targets when it has them
- `/www` doesn't call `/tp` — it reads the section if present, scans session if not
- The contract is one-directional and optional: `/tp` can emit without `/www`
  present, `/www` can scan without `/tp` having run

**Generalizes to other skill pairs:**

| Producer | Output section | Consumer | When it fires |
|---|---|---|---|
| `/tp` | Research-ready targets | `/www` | Critique produces [INFERENCE]/[UNKNOWN] items |
| `/why` | Root cause + evidence trail | `/harvest` | RCA surfaces unrealized obligation |
| `/check` | Unverified claims list | `/review` | Verification finds claims lacking receipts |
| `/review` | Architecture findings | `/refactor` | Review surfaces coupling/debt |
| `/preflight` | Constraint conflicts table | `/design` | Discovery finds neighboring artifacts with conflicts |
| Any skill | Wiki-worthy findings (`WIKI:` markers) | `/wiki` | Session boundary capture |

**The rule for adding a new bridge:** the producer emits a named section with
a stable format. The consumer reads it if present, falls back to its own
detection if not. The section name is the contract — no imports, no function
calls, no shared state. This is the same architecture as Unix pipes (stdout →
stdin), applied at the skill-protocol level.

**Contrast with code coupling:** a bad version would be `/tp` calling
`/www.research(targets)` — that couples the skills at the code level, creates
a dependency graph, and makes independent evolution harder. The bridge pattern
keeps them independent — `/tp` evolves its target format, `/www` evolves its
consumption logic, and the only shared contract is the section name.

## Pattern 2: Temporal surfacing layers

**The pattern:** the same check (e.g., "did the operator manually do something
a skill composition could automate?") runs at three timeframes via three
different mechanisms. A catch missed at one layer has two more chances.

**Concrete instance (this session):**

| Layer | Mechanism | When it fires | What it catches |
|---|---|---|---|
| Per-turn | AGENTS.md step 8 (workflow automation check) | End of every turn | Manual skill routing, manual re-derivation, manual triggering |
| Mid-conversation | `/notice` T9 trigger | When motivation score exceeds threshold | Operator manually bridges two skills mid-session |
| Session-end | `/tp session` standing skill-composition question | At session review | Composition patterns from the full session arc |

**Why three layers and not one:** each layer has a different failure mode that
the others compensate for:

- **Per-turn (AGENTS.md):** fires every turn but is prose — can be skipped under
  execution pressure. Compensated by /notice (mechanical trigger) and /tp session
  (session-level scan).
- **Mid-conversation (/notice):** is a skill with motivation scoring — can be
  suppressed by cooldown or hard-skip patterns (acceleration mode, mid-implementation).
  Compensated by per-turn (fires regardless of /notice state) and /tp session.
- **Session-end (/tp session):** catches everything but only once per session — if
  the composition opportunity was early in the session and the operator forgot by
  session-end, it's missed. Compensated by the earlier layers.

This mirrors the three-layer enforcement pattern documented in
[[coupling-inventory-as-mandatory-design-section]]: writer self-polices →
reviewer blocks → critical friend catches. The insight there applies here:
"removing any layer leaves a gap."

**Generalizes beyond workflow automation:** any check that must fire reliably
should be layered temporally, not just structurally. The temporal dimension
(per-turn vs mid-session vs session-end) is orthogonal to the structural
dimension (which skill runs the check). Both matter.

## Pattern 3: Concrete-pattern-over-vague-question

**The pattern:** replacing open-ended reflection questions ("what should I
surface?") with concrete trigger patterns ("did the operator just manually
route /tp output to /www?") dramatically improves firing reliability.

**Why this matters:** open-ended questions require the model to decide what
counts as "surface-worthy" every turn — a judgment call that degrades under
execution pressure. Concrete patterns are match operations: "does the current
turn match this specific shape?" The match is reliable; the judgment is not.

**The AGENTS.md step 8 implementation:** three specific patterns to match:

1. Manual skill routing → "This composition could be automated"
2. Manual re-derivation → "The wiki already covers this"
3. Manual triggering → "This could be a hook/skill automation"

Each pattern is a concrete thing to check, not an open-ended prompt. This is
the same principle as `/tp session`'s transcript scan: instead of asking "what
friction happened?", scan for specific exit-code patterns and let the evidence
drive the finding.

**Generalizes to:** any behavioral rule that currently lives as a vague
question. The upgrade path: identify the concrete patterns the question is
trying to catch, replace the question with a pattern checklist.

## What this means for our workspace

**For skill authors:** when building inter-skill composition, use the bridge
pattern (named output section consumed optionally by the downstream skill),
not code coupling. The bridge keeps skills independent and lets composition
emerge from protocol, not dependency.

**For surfacing reliability:** layer checks temporally. A single-layer check
(only per-turn, only /notice, only /tp session) will miss catches that a
three-layer system catches. The cost of three layers is ~3 extra lines per
check; the value is catching composition opportunities that would otherwise
require the operator to notice and ask.

**For AGENTS.md rules:** vague questions ("what should I surface?") are
necessary but insufficient. Pair each with concrete pattern checks that fire
reliably where the question degrades. The question provides coverage for novel
patterns; the concrete checks provide reliability for known patterns.

## Falsifier

These patterns are wrong if, within 6 months:

- The bridge contracts create maintenance burden (format drift between producer
  and consumer with no detection) — then the coupling was not actually avoided
- The three-layer surfacing produces zero catches that a single layer would have
  missed — then the temporal layering adds complexity without value
- The concrete-pattern checks become stale (the patterns no longer match because
  workflows evolved) and no one updates them — then they're worse than the vague
  question because they fire with false confidence
- The bridge pattern is never reused for a second skill pair — then it was a
  one-off, not a generalizable pattern

## Sources

- Session 019fb49b (2026-07-31): `/tp`→`/www` confidence-gap bridge implementation
- Session 019fb49b (2026-07-31): three-layer surfacing (AGENTS.md + /notice T9 + /tp session)
- `~/.grok/AGENTS.md` "automate user meta-actions" standing goal
- [[coupling-inventory-as-mandatory-design-section]] § "Why three layers and not one"
- [[visible-output-contracts-for-behavioral-skill-steps]] — the producer-consumer pattern at the skill-step level
- [[proactive-ai-volunteering-mechanisms]] — the research foundation for /notice

## Receipts

- `~/.grok/skills/tp/SKILL.md` § "Research-ready targets" (added 2026-07-31, commit `86e7c03`) — the /tp output bridge
- `~/.grok/skills/www/SKILL.md` § "Phase 1a+ — Session-confidence scan" (added 2026-07-31, commit `86e7c03`) — the /www consumer side
- `~/.grok/AGENTS.md` § "Per-turn thought-partner protocol" step 8 (added 2026-07-31, commit `bc89b06`) — per-turn workflow automation check
- `~/.grok/skills/notice/SKILL.md` T9 trigger table + type constraint + confidence floor exception (added 2026-07-31, commit `bc89b06`) — mid-conversation surfacing
- `~/.grok/skills/tp/SKILL.md` § "Standing skill-composition question" (added 2026-07-31, commit `bc89b06`) — session-end surfacing
