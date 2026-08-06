---
title: "Risk pattern: config disabled-list bare-name collision"
created: 2026-08-06
source: session-20260728
tags: [risk-pattern, config, collision, disabled-list, skill-naming]
summary: >
  Grok Build's disabled-hooks/disabled-skills lists use bare names that
  match globally. Disabling a plugin skill by name also disables a native
  skill with the same name. The fix is to clean the disabled list before
  creating native skills with names that match disabled plugin entries.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/config-disabled-list-bare-name-collision.md
    type: extends
---

# Risk pattern: config disabled-list bare-name collision

## Pattern

When the config disabled list uses bare skill/hook names (not paths), disabling a plugin skill by name also silently disables any native skill created with the same name. The collision is invisible — no error, no warning, just a native skill that doesn't load.

## Evidence

- **Session 2026-07-28:** a native skill was created with a name that matched a disabled plugin entry. The native skill silently failed to load. No error message surfaced the collision.
- **Root cause:** Grok Build docs (08-skills.md:48): "`disabled` takes skill names." Names, not paths. The match is global across all discovery roots.

## What this means for our workspace

1. Before creating a native skill, check the disabled list for name collisions.
2. During plugin migrations: clean the disabled list BEFORE creating native skills with the same names.
3. This applies to hooks too — the `disabled-hooks` list has the same bare-name matching behavior.
4. When debugging a skill that "should work but doesn't load," the disabled list is the first thing to check — before investigating frontmatter, path, or host issues.

## Falsifier

If Grok Build changes the disabled list to use paths instead of bare names (making collisions impossible), this pattern is obsolete. Check the docs on next Grok version update.

## Related concepts

- [[config-disabled-list-bare-name-collision]] — the original incident with full technical details
- [[plugin-skill-migration-port-absorb-retire]] — migration patterns where this collision commonly occurs
- [[skill-catalog-scope-inconsistency-causes-cascading-read-failures]] — scope inconsistency that makes name collisions worse

## Receipts

- Wiki concept: `config-disabled-list-bare-name-collision.md`
- Grok Build docs: `~/.grok/docs/user-guide/08-skills.md` lines 39-49
