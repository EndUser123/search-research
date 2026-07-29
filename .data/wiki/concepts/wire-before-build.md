---
title: "Wire before build: connecting capabilities is higher-leverage than creating them"
created: 2026-07-29
source: session-2026-07-29
tags: [agent-behavior, skill-design, capability-graph, wiring, integration, pattern]
summary: >
  The dominant waste pattern in a skill-building session is not building
  broken things — it's building correct things that are disconnected from
  the system that would use them. The fix is a mechanical wiring check that
  runs after capability creation: does any existing skill reference the new
  capability? If not, flag "built but not wired."
agent: grok
host: both
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/fix-introduces-regression-by-trading-properties.md
    type: complements
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: related
---

# Wire before build

## Decision context

**The problem:** during a single session, the agent built 7+ new capabilities
(harvest skill, symbol-drift checker, wiki concept, inter-skill convention,
session-pattern analyzer, opportunity scanner, multiple SKILL.md additions).
A retrospective /tp analysis found that most were "correct in isolation but
disconnected from the system that would use them":

- Harvest built but not connected to `/aar` or `/why` (fixed later)
- Wiki concept written but not connected to `/review` (fixed later)
- Convention defined but has zero producers (fixed later)
- Symbol-drift checker built but never run
- 5 SKILL.md additions are untested hypotheses

Each capability was correct. Each was an island.

## Key findings

### The pattern

1. Agent builds capability X (a script, a skill, a wiki concept, a convention)
2. Agent ships and commits
3. Nobody wires X to the skill that should consume it
4. Next session doesn't know X exists (it's not in the capability graph,
   not referenced by any SKILL.md, not discoverable by grep)

The cost: the capability depreciates. A wiki concept nobody queries is
knowledge that decays. A convention with no producers is a contract with
no implementations. A script nobody calls is dead code.

### Why it happens

Action bias under deadline pressure. Building feels productive; wiring feels
like overhead. The agent optimizes for "what can I create next?" instead of
"what have I created that isn't connected yet?"

### The capability graph as the detection mechanism

The wiki's `capabilities.py` maps every skill's `provides` and `consumes`.
Gaps in this graph (consumed but not provided, provided but not consumed,
orphaned capabilities) are mechanical signals of unwired work. The graph is
only as good as the frontmatter, so missing frontmatter is itself a wiring
gap.

## What this means for our workspace

**Structural fix added to `/check` (Step 0.92 wiring audit):** when a session
creates new capabilities (scripts, skills, wiki concepts, conventions), the
check mechanically verifies that at least one existing skill references each
new capability. Gaps are flagged as "built but not wired."

**AGENTS.md rule:** "Workspace knowledge is primary input." Before building
something new, grep the workspace for existing capabilities that solve the
same problem. Before finishing, check whether what you built is wired to its
consumers.

**The question to ask at session midpoint:** "What have I built this session
that isn't connected to anything yet?"

## Falsifier

This pattern is wrong if, within 6 months:
- The wiring audit finds zero gaps (then the pattern was already solved)
- Capabilities built in isolation are consistently discovered and wired by
  future sessions without the audit (then the discovery mechanism is
  sufficient and the audit is unnecessary)
- The capability graph becomes stale or unmaintained (then the mechanical
  detection fails)

## Sources

- Session 2026-07-29 retrospective: 7 capabilities built, 5 initially unwired
- [[fix-introduces-regression-by-trading-properties]] — companion pattern: fixes that trade properties
- [[invariants-beat-environment-comfort]] — behavioral rules don't catch context blindness; mechanical checks do
- [[exploration-vs-execution-intent-signals]] — action bias is the root cause of both unwired work and premature implementation

## Receipts

- `capabilities.py --for-skill harvest` returned nothing until frontmatter was added (verified 2026-07-29)
- `/check` Step 0.92 wiring audit added at `P:/.grok/skills/check/SKILL.md` (commit `666c003`)
- `workspace_opportunity_scan.py` at `P:/.agents/scripts/workspace_opportunity_scan.py`
