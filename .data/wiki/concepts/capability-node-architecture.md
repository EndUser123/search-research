---
title: "Capability node architecture: lean contracts + design notes for composable skills"
created: 2026-07-28
source: session-2026-07-28
tags: [capability-node, skill-architecture, composition, frontmatter, skill-graph, decision, token-efficiency]
summary: >
  Architectural decision to introduce a two-layer capability node system:
  lean contract files (capabilities/<name>.md) that skills reference for
  I/O and procedure, and design note files (concepts/capability-<name>.md)
  that humans read for context. Skills declare depends_on + consumes in
  frontmatter; the graph script reads these as ground truth. Reduces LLM
  context bloat (35-line contract vs 200-line SKILL.md) and eliminates
  procedural duplication across 18-24 skills per capability.
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - "Session 2026-07-28 operator directive: 'the nodes are objects and we control the definition'"
  - "Graph analysis: P:/tmp/analyze_graph.py (frontmatter-declared hotspot data)"
  - "Industry research: wiki/concepts/skill-dependency-graph-research-2026.md"
relations:
  - target: wiki/concepts/skill-graph.md
    type: grounds
  - target: wiki/concepts/skill-dependency-graph-research-2026.md
    type: extends
  - target: wiki/concepts/capability-wiki-query.md
    type: first-instance
  - target: wiki/concepts/capability-wiki-write.md
    type: first-instance
  - target: capabilities/wiki-query.md
    type: contract-for
  - target: capabilities/wiki-write.md
    type: contract-for
---

# Capability node architecture

## Decision context

**The problem:** 18 skills each describe their own version of "how to write a
wiki concept" — frontmatter format, SCHEMA.md reference, validate_wiki_entry.py,
append_log.py, retirement check. The same ~15-line procedure repeated 18 times
with drift. Similarly, 24 skills describe "how to query the wiki" with slight
variations. When a procedure changes, all copies need manual updates — and this
session proved that propagation fails (11 files had stale references after
web-search-prime was disabled).

**The operator's vision:** "If the nodes are objects and we control the
definition, we can expand the schema anytime we want to meet a new requirement,
thus the standard evolves, maintains backwards compatibility, and minimizes
glue." The node should be a reusable description with inputs and outputs, like
a data map. Skills reference the node with whatever customization glue is
needed. This connects to [[skill-graph]] (the dependency graph that surfaces
duplication hotspots) and the research in [[skill-dependency-graph-research-2026]]
(which found AgentFlow, Skill Manifest Proposal, and Harness Doctrine all
converging on structured frontmatter as ground truth).

## The decision

**Two-layer capability node system:**

1. **Lean contract** (`P:/.data/wiki/capabilities/<name>.md`) — tight,
   procedural, no prose. Contains: inputs, outputs, the execution procedure,
   minimum output shape. Skills reference this path. Designed to be scanned
   in one read by the LLM (~30-35 lines).

2. **Design notes** (`P:/.data/wiki/concepts/capability-<name>.md`) —
   human-facing analysis. Contains: why the node exists, consumer list,
   per-skill glue table (how each skill customizes the capability), quality
   gates, falsifier. Read only when understanding the system, not during
   execution.

**Frontmatter declarations** on all skills:
- `depends_on: [skill-a, skill-b]` — which skills this one delegates to
- `consumes: [ddg, firecrawl, mmx, gh]` — which tools/providers this skill uses
- `provides: [capability-name]` — which capability nodes this skill defines

**Graph script reads frontmatter as ground truth** and uses lexical scan
(regex over SKILL.md body) as a linter for undeclared edges. Skills without
frontmatter still work (backwards compatible — lexical-only extraction).

## Selection criterion

**Token efficiency + extensibility.** The two-layer structure minimizes what
the LLM reads during execution (contract only) while preserving full context
for humans and maintenance (design notes). The schema is extensible — starts
with `depends_on` + `consumes` and can grow to include `inputs`/`outputs`/
`cost`/`latency`/`fallback` fields as requirements emerge.

## Steelman (the rejected alternative)

**Single-layer: put the contract inside the skill's own SKILL.md as a
structured section.** This is simpler — no new directory, no second file. The
contract is right there when you read the skill.

**Why it was reasonable:** fewer files, less indirection, no "where does the
contract live?" question. The skill IS the contract.

**Why we rejected it:** duplication persists. If 18 skills each embed their
own copy of the wiki-write procedure, changing the procedure still requires
18 edits. The whole point is to define it once. A single-layer approach
solves discoverability but not duplication. This is the same propagation-gap
class documented in [[plausible-narratives-substitute-for-verification]] —
when a shared default changes, downstream consumers don't get updated
without structural enforcement.

## What the first two nodes cover

| Node | Contract path | Consumers | What it replaces |
|------|--------------|-----------|------------------|
| wiki-query | `capabilities/wiki-query.md` | 24 skills | Each re-describing grep procedure |
| wiki-write | `capabilities/wiki-write.md` | 18 skills | Each re-describing frontmatter + validation + logging |

## Glue pattern (how skills customize capabilities)

The capability defines WHAT (the procedure). Each skill defines WHEN and WHY
(what triggers it, what pre/post logic wraps it):

- `/why` Step 15: gates wiki-write behind cross-model review before calling it
- `/www` Phase 3: adds decision-context capture before wiki-write
- `/review` Step 6: triggers wiki-write only on systemic pattern detection
- `/close`: calls wiki-query to check gates, never writes

The glue stays in the skill's SKILL.md. The contract stays in the capability
node. They compose without coupling.

## What this means for our workspace

1. **Future capabilities** follow the same two-file pattern. Next candidates
   (from graph analysis): `parallel-subagent-dispatch` (used by /www, /debrief,
   /review, /model-benchmark, /tp), `session-state-extraction` (used by /close,
   /debrief, /tp session).

2. **The schema evolves.** When a capability needs `cost` or `latency` fields,
   add them to the contract. Skills that don't use the new field are unaffected
   (backwards compatible). The operator's principle: "we control the definition."

3. **Token budget improvement.** A skill composing 5 capabilities reads ~150
   lines of contracts instead of 5 full SKILL.md files at ~200 lines each
   (~1000 lines). 85% reduction in context consumption for the composition path.

4. **Maintenance.** Changing a shared procedure (e.g., "how to validate a wiki
   entry") requires editing one contract file, not 18 skill files. The
   propagation-gap class of bug is structurally eliminated for capabilities
   that have been extracted. This is the same principle as
   [[mechanical-enforcement-over-behavioral-reminder]] — structure over prose
   for reliability.

## Falsifier

This architecture is wrong if:
- Skills stop referencing the contract files and revert to inline descriptions
  (the indirection wasn't worth the token savings)
- The frontmatter declarations drift from reality at >20% rate over 3 months
  (measured by the graph linter comparing frontmatter to lexical scan)
- A simpler pattern emerges (e.g., the skills become small enough that
  duplication doesn't matter, or the LLM context window grows enough that
  reading full SKILL.md files is free)

## Receipts

- `P:/.data/wiki/capabilities/wiki-query.md` — first lean contract (15 lines)
- `P:/.data/wiki/capabilities/wiki-write.md` — second lean contract (35 lines)
- `P:/.data/wiki/concepts/capability-wiki-query.md` — first design notes
- `P:/.data/wiki/concepts/capability-wiki-write.md` — second design notes
- `P:/.data/wiki/scripts/build_skill_graph.py` — graph script with frontmatter support
- `P:/tmp/analyze_graph.py` — hotspot analysis that identified wiki as #1 duplication
- 43 skills with `depends_on` + `consumes` frontmatter (100% fleet coverage)
