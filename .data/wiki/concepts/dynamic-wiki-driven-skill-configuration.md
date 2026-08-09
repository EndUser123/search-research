---
title: "Dynamic Wiki-Driven Skill Configuration"
slug: dynamic-wiki-driven-skill-configuration
created: 2026-07-28
category: decision
tags: [wiki, skill-design, dynamic-config, orchestrator, architecture, extensibility]
summary: >
  Skills should read the wiki at runtime for configuration, routing, and
  constraints — not hardcode tables and rules in SKILL.md. The wiki is the
  single source of truth; when knowledge changes, update the wiki concept,
  not every skill that references it. Covers the pattern, benefits,
  implementation, example use cases, and why this scales better than static
  skill files. The use cases are illustrative, not exhaustive — any skill
  that references host-specific knowledge, routing decisions, or accumulated
  wisdom should use this pattern.
agent: grok
host: both
cognitive_load: 2
verification: observed
sources:
  - "Session 019fa276: /www Round 3.5 and ecosystem table converted from static to dynamic"
  - "P:/.data/wiki/concepts/invariants-beat-environment-comfort.md (dynamic invariant source)"
  - "P:/.data/wiki/concepts/concurrent-cdp-auth-contention.md (dynamic invariant source)"
  - "P:/.data/wiki/concepts/social-media-as-structured-research-data-for-ai-agents.md (dynamic source-state)"
relations:
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: related
  - target: wiki/concepts/research-vs-design-vs-architect-skills-and-www-self-assessment.md
    type: related
---

# Dynamic Wiki-Driven Skill Configuration

## Decision context

**The problem:** skills accumulate hardcoded rules, tables, and constraints
in their SKILL.md files. Every time the fleet learns something new (a new
host invariant, a new API limitation, a new routing decision), someone has
to manually edit every skill that references it. This doesn't scale: the
knowledge lives in the wiki anyway, but skills don't read it dynamically —
they reference static copies that drift from the source of truth.

**What this decision changes:** skills query the wiki at runtime for
configuration, constraints, and routing instead of hardcoding tables.
The wiki becomes the single source of truth. SKILL.md files shrink and
stabilize — they describe *how to orchestrate*, not *what the current
state of the world is*.

## The pattern

**Static (old):** SKILL.md contains a hardcoded table of rules.
Adding a new rule requires editing the SKILL.md.

```
# In SKILL.md:
| Invariant | Violation | Safe alternative |
| --cookies-from-browser | cookie contention | --cookies <file> |
| ... (6 rows, manually maintained)
```

**Dynamic (new):** SKILL.md contains a query instruction. Adding a new
rule requires only writing a wiki concept with the right tag.

```
# In SKILL.md:
Query the wiki for host invariants:
  grep -li "host.invariant" P:/.data/wiki/concepts/
Read matching concepts. Extract invariants + violations + alternatives.
Scan recommendations against extracted invariants.
```

The wiki concept carries the actual knowledge:
```
# wiki/concepts/concurrent-cdp-auth-contention.md
tags: [host-invariants, auth, concurrency, ...]
## The pattern: two concurrent nlm login calls invalidate each other...
## Safe alternative: --cookies <file> via export_yt_cookies.py
```

## Benefits

1. **Single source of truth.** Knowledge lives in one place (the wiki
   concept). Skills read it; they don't copy it. No drift.

2. **No skill edits when knowledge changes.** Learn a new invariant? Write
   a wiki concept. Every skill that queries the wiki automatically picks
   it up on the next run. No SKILL.md edits, no version bumps, no cache
   rebuilds.

3. **Skills stay thin.** SKILL.md describes *how to orchestrate* (the
   pipeline phases, the delegation pattern). The *what* (current
   constraints, current source availability, current routing decisions)
   lives in the wiki. This keeps skills stable while knowledge evolves.

4. **Extensibility without ceremony.** New use cases don't require a
   SKILL.md enhancement batch. Write a wiki concept, tag it, done.

5. **Cross-skill reuse.** A wiki concept about multi-terminal isolation
   is read by `/www` (Round 3.5), `/go` (safe-git preflight), `/close`
   (scanner checks), and any future skill that needs it — all from one
   source, no duplication.

## How to implement it

**In SKILL.md:** replace static tables with query + process instructions.

| Component | Static version | Dynamic version |
|-----------|---------------|----------------|
| Constraint table | 6-row markdown table | `grep -li "host.invariant" wiki/concepts/` + read + extract |
| Routing table | 12-row skill mapping | `grep skill-catalog.md` + match findings against descriptions |
| Source availability | Hardcoded "social media = skip" | Query `[[social-media-as-structured-research-data-for-ai-agents]]` for current state |
| Decision frameworks | Hardcoded list | Query wiki for `[decision-frameworks]` tagged concepts |

**In wiki concepts:** tag concepts with discovery-friendly tags.

| Tag | What it signals | Who queries it |
|-----|----------------|---------------|
| `host-invariants` | A constraint that applies to this fleet | `/www` Round 3.5, `/go` preflight |
| `failure-pattern` | A known failure mode + root cause + fix | `/why`, `/aar`, `/www` disconfirmation |
| `decision` | An architectural choice with rationale | `/tp`, `/plan` |
| `reference` | Durable factual knowledge | `/wiki` queries from any skill |
| `skill-ecosystem` | Skill routing / when-to-use guidance | `/www` ecosystem awareness |

**Query mechanism:** `grep` (built-in tool, no external dependency) or
the built-in `grep` tool. Falls back to `ls` + filename matching if grep
returns nothing. The wiki is a flat directory of markdown files — no
special query infrastructure needed.

## Example use cases

These illustrate the pattern. The pattern itself is not limited to these.

### 1. Host invariant checking (already converted)

`/www` Round 3.5 queries the wiki for host invariants instead of a
hardcoded table. When we learned about the stale port-map PID pattern
(today), we wrote `[[concurrent-cdp-auth-contention]]` — the next `/www`
run automatically includes it in the invariant scan. Zero SKILL.md edits.

### 2. Source availability routing

Instead of hardcoding "skip social media" in `/web`, query
`[[social-media-as-structured-research-data-for-ai-agents]]` for the
current free-tier state of each platform. When Reddit's API changes (and
it will), update the wiki concept — `/web`'s routing updates automatically.

### 3. Skill ecosystem routing

Instead of a static 12-row table in `/www`, query the skill catalog
(`wiki/concepts/skill-catalog.md`) for current skills and their
descriptions. When a new skill is added to the fleet, it's automatically
considered for routing suggestions.

### 4. Decision framework library

`/tp` and `/risk` could query the wiki for `[decision-frameworks]`
tagged concepts to discover which mental models are available (FMEA,
ACH, pre-mortem, etc.) instead of hardcoding which lenses to use.

### 5. Failure pattern library

`/why` already queries the wiki for known failure patterns (Step 0.5 in
its pipeline). This is the existing, proven example of dynamic wiki
usage — every new failure pattern written to the wiki makes `/why`
smarter without code changes.

### 6. Open-ended future use cases

Any skill that references accumulated wisdom, current state, or host-
specific knowledge can use this pattern. Examples we haven't built yet:
- `/check` scanning wiki for `[quality-gates]` to know what to verify
- `/close` scanning wiki for `[close-requirements]` to know what to check
- `/go` scanning wiki for `[deployment-patterns]` to know safe paths
- Any new skill querying `[skill-ecosystem]` to know its place in the fleet

The pattern is general: **if a skill hardcodes knowledge that changes, it
should query the wiki instead.**

## When NOT to use this pattern

- **Stable, meta-level instructions** (how to orchestrate, what phases to
  run, how to delegate) — these belong in SKILL.md. They change rarely and
  define the skill's identity.
- **One-off logic** that won't be reused by other skills.
- **Performance-critical paths** where a wiki query adds unacceptable
  latency (rare — grep on ~400 files takes <1s).

## Steelman of the static approach

The static approach (hardcoded tables) has one real advantage: **the skill
is self-contained.** You can read one file and understand everything it
does, without needing to also read the wiki concepts it references. This
is better for skill portability (sharing a skill with someone who doesn't
have the wiki) and for cold-start clarity (a new agent loading the skill
for the first time).

The counterargument: this fleet always has the wiki. Portability to
wiki-less environments is not a current requirement. And the dynamic
approach's query instructions *are* self-documenting — they tell the
reader exactly where to look.

## Receipts

- `~/.grok/skills/www/SKILL.md` Round 3.5 (converted from static table to dynamic wiki query, 2026-07-28)
- `~/.grok/skills/www/SKILL.md` ecosystem awareness section (converted from static 12-row table to dynamic query)
- `~/.grok/skills/why/SKILL.md` Step 0.5 (existing proven example — queries wiki for failure patterns before investigating)
- `P:/.data/wiki/concepts/concurrent-cdp-auth-contention.md` (wiki concept that `/www` Round 3.5 reads dynamically)
- `P:/.data/wiki/concepts/invariants-beat-environment-comfort.md` (wiki concept read dynamically)

## Falsifier

This pattern is wrong if:
- Wiki queries become a performance bottleneck (unlikely at current scale)
- The wiki grows so large that grep returns too much noise (possible at
  ~5000+ concepts; would need tag discipline or a real search index)
- Skills become harder to debug because their behavior depends on wiki
  content that may have changed silently (mitigated by the wiki's
  provenance tracking + `last_updated` timestamps)
- Knowledge drifts in the wiki without being noticed (mitigated by
  `/skill-prune` and retirement checks)

## What this means for our workspace

- **`/www` is the first skill converted** (Round 3.5 + ecosystem table)
- **`/why` already uses this pattern** (Step 0.5 wiki query for failure patterns)
- **`/web`'s routing logic** is a candidate (source availability is dynamic)
- **`/go`'s preflight** is a candidate (host constraints are dynamic)
- **New skills should default to dynamic** unless the knowledge is truly stable

See [[research-vs-design-vs-architect-skills-and-www-self-assessment]]
for the broader skill-thinness principle this supports.
