---
title: "Skill naming convention: short imperative names"
created: 2026-08-06
source: session-20260806
tags: [skill-design, naming-convention, operator-preference, convention]
summary: >
  Skills should use short imperative names (/brain, /risk, /tp, /go) not long
  descriptive names (/brainstorming, /risks, /thought-partner, /grok-sdlc).
  The operator speaks in short imperatives; skill names should match that
  speech pattern. Long names add typing cost without discoverability benefit
  when autocomplete and the skill catalog handle discovery.
agent: grok
host: grok
cognitive_load: 1
verification: operator-confirmed
relations:
  - target: wiki/concepts/skill-rename-propagation-checklist.md
    type: complements
  - target: wiki/concepts/skill-lifecycle-toolkit.md
    type: refines
---

# Skill naming convention: short imperative names

## Decision context

**Why this was needed:** the operator corrected two skill names in the same session — `/brainstorming` → `/brain` and `/risks` → `/risk`. Both corrections went the same direction: shorter, singular, imperative. The operator stated the principle explicitly: "it should be '/risk'" and "just like we should have '/brain', not '/brainstorming'." Without a recorded convention, future skill creation would continue producing long names that the operator would have to correct.

## The convention

| Principle | Example | Counter-example |
|---|---|---|
| **Short** — one word when possible | `/brain`, `/risk`, `/tp`, `/go` | `/brainstorming`, `/thought-partner` |
| **Singular** — not plural | `/risk`, not `/risks` | Matches the pattern: one skill, one name |
| **Imperative** — verb or noun that reads as a command | `/check`, `/review`, `/ship` | `/checking`, `/code-review-process` |
| **Matches operator speech** — the name the operator would type in flow | `/tp`, `/go`, `/risk` | `/critical-friend-dialogue` |

**Discoverability is not a naming concern.** The skill catalog (session-start listing + `skill-catalog.md`) and slash autocomplete handle discovery. The name doesn't need to describe the skill — it needs to be the short token the operator reaches for.

## Steelman (the rejected alternative)

Long descriptive names (`/brainstorming`, `/thought-partner`, `/code-review`) have a real advantage: a new user or agent who has never seen the skill can infer its purpose from the name alone. `/tp` is opaque; `/thought-partner` is self-documenting. `/brain` could mean anything; `/brainstorming` is specific.

This argument loses for this workspace because:

1. The operator is the sole user and already knows what each skill does — the name is a recall key, not a description.
2. Skill descriptions in the catalog provide the discoverability that long names would provide. The `description:` field in SKILL.md frontmatter is the right place for "what does this skill do," not the skill name.
3. Short names reduce typing friction in flow-state operation. The operator types `/tp` dozens of times per session; `/thought-partner` would be measurable friction.

## What this means for our workspace

1. **New skill creation:** default to one-word imperative names. If the natural name is two words, abbreviate (`/tp` not `/thought-partner`). Only go long if the short form is genuinely ambiguous with another skill.
2. **Existing skills:** rename when touched for other reasons. Don't batch-rename — do it opportunistically when editing a skill for another purpose, to avoid propagation churn.
3. **Plugin skills:** shadow with short-name user-scope copies when the plugin uses a long name and the skill is frequently invoked. This is the `/brain` pattern: the plugin still has `brainstorming`, but `~/.grok/skills/brain/SKILL.md` shadows it.
4. **Propagation is the cost:** renaming a skill means updating every reference across both repos (AGENTS.md, sibling SKILL.md files, wiki concepts, skill catalog). The `skill-rename-propagation-checklist.md` concept documents the full procedure. Budget 5-10 minutes per rename for propagation.

## Falsifier

If short names cause collision or confusion — two skills with similar short names that the operator or an agent can't distinguish — the convention should be relaxed. The specific test: if `/go` and `/get` both existed and were frequently confused, or if `/tp` and `/tr` were mistyped regularly, the convention is too aggressive. Also: if a new operator joins who is NOT familiar with the skills, the self-documenting value of long names may outweigh typing economy.

## Related concepts

- [[skill-rename-propagation-checklist]] — the mechanical procedure for propagating a rename across all files
- [[skill-lifecycle-toolkit]] — broader skill lifecycle including creation, migration, and retirement
- [[agentic-sdlc-skill-lifecycle-architecture]] — how skills chain through SDLC stages; naming affects routing
- [[plugin-skill-migration-port-absorb-retire]] — when plugin skills are migrated to native, the naming convention applies

## Receipts

- Session 2026-08-06: operator said "it should be '/risk'" after seeing `/risks` (plural) in the skill catalog
- Session 2026-08-05: operator confirmed `/brainstorming` → `/brain` rename with no pushback
- The pattern holds across all operator-created skills: `/go`, `/tp`, `/ask`, `/why`, `/aar`, `/risk`, `/brain`, `/check`, `/ship`, `/close`, `/wiki`, `/web`, `/www`, `/dream` — all one or two tokens, all imperative

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[agent-config-directory-taxonomy]]
- [[claude-code-skills-and-mcp-integration]]
- [[claude-code-hooks-system]]

