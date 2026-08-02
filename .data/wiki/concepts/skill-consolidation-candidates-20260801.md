---
title: "Skill consolidation candidates — safe removals"
created: 2026-08-01
source: session-019f902a-621d-7711-9436-7c6003c57793
tags: [skill-consolidation, deprecated-skills, cleanup, dead-alias]
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - ~/.grok/skills/check-work/SKILL.md (deprecated)
  - ~/.grok/skills/code-review/SKILL.md (deprecated, disable-model-invocation: true)
  - ~/.grok/skills/grok-go/SKILL.md (active compat alias — do NOT remove)
  - ~/.grok/skills/grok-sdlc/SKILL.md (active compat alias — do NOT remove)
  - ~/.agents/skills/verification-before-completion (junction into superpowers repo — do NOT remove)
relations:
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
    type: related
---

# Skill consolidation candidates — safe removals

## Safe to remove (deprecated, no active references)

| Skill | Status | Why safe |
|---|---|---|
| `check-work` | `status: deprecated` | `/check` is strict superset; not referenced by path in any living doc |
| `code-review` | `status: deprecated`, `disable-model-invocation: true` | `/review` absorbed the maintainability lens inline |

## NOT safe to remove (active compatibility aliases)

| Skill | Status | Why not safe |
|---|---|---|
| `grok-go` | Active compat alias | Makes `/grok-go` work; removing breaks the alias |
| `grok-sdlc` | Active compat alias | Makes `/grok-sdlc` and `/sdlc` work; removing breaks the alias |

## NOT a duplicate (junction into superpowers repo)

| Path | Status | Why not safe to remove |
|---|---|---|
| `~/.agents/skills/verification-before-completion` | Junction → `P:/packages/.github_repos/superpowers/skills/verification-before-completion` | Not a duplicate — it's the same file exposed through two namespaces. Removing the junction breaks the `.agents` namespace path. Using `shutil.rmtree` would follow the junction and delete source files in the repo. |

## What this means for our workspace

The `/close` scanner flagged these as consolidation candidates but didn't distinguish between safe and unsafe removals. The scan also incorrectly classified `grok-go` and `grok-sdlc` as "dead" — they are active compatibility aliases that make `/grok-go` and `/sdlc` work. The `/close` scanner's classification needs updating to check whether deprecated skills have active aliases before recommending removal.

## Falsifier

If `grok-go` or `grok-sdlc` are no longer referenced by any alias or path, they become safe to remove. If `verification-before-completion` is no longer needed as a junction (the superpowers repo is removed or the skill is consolidated), the junction can be removed.

## Receipts

- `~/.grok/skills/check-work/SKILL.md` — `status: deprecated` confirmed by reading frontmatter
- `~/.grok/skills/code-review/SKILL.md` — `status: deprecated`, `disable-model-invocation: true` confirmed by reading frontmatter
- `~/.grok/skills/grok-go/SKILL.md` — active compat alias, makes `/grok-go` work
- `~/.grok/skills/grok-sdlc/SKILL.md` — active compat alias, makes `/grok-sdlc` and `/sdlc` work
- `~/.agents/skills/verification-before-completion` — junction confirmed by `fsutil reparsepoint query`
