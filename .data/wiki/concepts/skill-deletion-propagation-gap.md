---
title: "Skill deletion propagation gap: stale references survive skill removal"
created: 2026-08-06
source: session-019fce56 (3 instances in one session)
tags: [skill-lifecycle, propagation, depends_on, stale-references, deleted-skill, maintenance, code-orchestrates-model-judges]
agent: grok
host: grok
cognitive_load: 2
verification: observed
summary: >
  When a skill is deleted from the workspace, its references persist in three
  locations: (1) depends_on arrays in sibling skill frontmatter, (2) routing
  tables and escalation suggestions in skill bodies, and (3) wiki concepts that
  reference the skill by name. The deletion removes the SKILL.md but does not
  trigger any propagation step — stale references accumulate silently until
  someone greps for them manually. This session found 3 instances of the same
  pattern: /capture→/tasks, /dream+review+aar+notice→/red-team, plus 160 wiki
  concept references. The fix is a mechanical propagation check: when deleting
  a skill, grep all SKILL.md frontmatter + routing tables + AGENTS.md for the
  old skill name before declaring the deletion complete.
relations:
  - target: wiki/concepts/removal-protocol
    type: extends — adds the propagation step that the removal protocol lacks
  - target: wiki/concepts/propagation-check-after-policy-config-changes
    type: instance-of — skill deletion is a config change that needs propagation
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: related — the propagation check should be a script, not a prose rule
---

# Skill deletion propagation gap

## Decision context

**Why this was needed:** during session 019fce56, three separate propagation
gaps were discovered and fixed — all the same pattern:

1. `/tasks` skill was disabled; `/capture` SKILL.md still listed it in `depends_on` (fixed commit `5aab694`)
2. `/red-team` skill was deleted; 4 skills (dream, review, aar, notice) still listed it in `depends_on`, plus 13 skill files had routing references, plus 52 wiki concepts referenced it (fixed commits `84acde7`, `49468cc`, `ad763d3`, `a663cfb`)

The pattern: deleting a skill's SKILL.md removes the file but does nothing
to update the skills that depend on it, route to it, or document it. The
references become stale silently.

## The three propagation surfaces

| Surface | What breaks | How to check | Example |
|---------|------------|-------------|---------|
| **depends_on arrays** | Skills declare a dependency on a non-existent skill. Consumers reading the dependency graph get broken edges. | `grep "<deleted-skill>" ~/.grok/skills/*/SKILL.md` in frontmatter | `/capture depends_on: [..., tasks]` after /tasks disabled |
| **Routing tables** | Skills suggest the deleted skill as an escalation path. Operators following the suggestion hit a dead end. | `grep "<deleted-skill>" ~/.grok/skills/` across full skill bodies | `/tp` recommending `/red-team` after deletion |
| **Wiki concepts** | Concepts reference the skill by name as a capability. Future queries for that capability find stale references. | `grep "<deleted-skill>" P:/.data/wiki/concepts/` | 52 concepts referencing `/red-team` |

## The fix (mechanical, not prose)

**Current state:** skill deletion is a manual file operation with no propagation step. The removal protocol in `P:/.claude/rules/removal-protocol.md` covers imports, registrations, and tests — but does NOT cover depends_on arrays or routing tables in sibling skills.

**The missing step:** after deleting a skill, run this propagation check:

```powershell
# Check depends_on arrays in all skill frontmatter
grep pattern="<deleted-skill-name>" path="C:/Users/brsth/.grok/skills" glob="*.md"

# Check routing tables and escalation suggestions
grep pattern="<deleted-skill-name>" path="C:/Users/brsth/.grok/skills" glob="*.md"

# Check AGENTS.md
grep pattern="<deleted-skill-name>" path="C:/Users/brsth/.grok/AGENTS.md"

# Check wiki concepts
grep pattern="<deleted-skill-name>" path="P:/.data/wiki/concepts"
```

Each result needs per-reference judgment:
- **depends_on:** remove the entry (mechanical)
- **Routing tables:** replace with the successor skill or `/tp` depending on context (judgment call)
- **Wiki concepts:** historical references can stay with an annotation; active routing refs should be updated

## Why prose rules don't work here

The removal protocol already says "grep imports" and "grep references" — but it's a prose rule that doesn't fire under session pressure. The 3 instances in this session were found by accident (during /todo scans and /risks checks), not because anyone followed the removal protocol.

The structural fix would be a `pre-delete-propagation-check.sh` script that runs the grep automatically and refuses to proceed if stale references exist. This follows the [[code-orchestrates-model-judges-skill-scale]] principle: the check should be code, not a reminder.

## What this means for our workspace

- **Immediate:** when deleting or disabling any skill, always grep all 3 surfaces (depends_on, routing tables, wiki). This session's 3 instances prove the pattern recurs.
- **Structural:** add a propagation-check script to the skill lifecycle. The `propagation_check.ps1` script at `~/.grok/scripts/` partially exists but only checks AGENTS.md — it needs to extend to skill frontmatter and routing tables.
- **Catalog:** after propagation cleanup, re-run `python P:/.data/wiki/scripts/index_skills.py` to rebuild the skill catalog.

## Falsifier

This pattern is wrong if skill deletions are rare — if it only happened once, it's a one-off, not a pattern. Evidence against: the workspace has had at least 4 skill deletions/disablings in the past 2 weeks (/red-team deleted, /tasks disabled, /debrief absorbed into /aar, /check-work → /check). Each one left stale references that were found later.

## Sources

- Session 019fce56 (2026-08-05/06): 3 instances found and fixed
- Commits: `5aab694`, `84acde7`, `49468cc`, `ad763d3`, `a663cfb`
- `P:/.claude/rules/removal-protocol.md` — existing protocol (covers imports/registrations, not depends_on/routing)
