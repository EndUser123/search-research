---
title: "/www lifecycle script reference staleness pattern"
created: 2026-08-01
source: session-019f902a-621d-7711-9436-7c6003c57793
tags: [www, lifecycle, staleness, script-reference, plugin-path, skill-design]
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - ~/.grok/skills/www/SKILL.md (line 268, stale reference to wiki_after_write.py + wiki_state.py)
  - P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/ (actual location of scripts)
  - P:/.data/wiki/scripts/ (different scripts live here — append_log.py, index_skills.py, scan_techniques.py)
relations:
  - target: wiki/concepts/skill-design-patterns-reference-overlay-search-intelligence.md
    type: related
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
    type: related
---

# /www lifecycle script reference staleness pattern

## What happened

The `/www` SKILL.md at line 268 referenced `wiki_after_write.py` and `wiki_state.py` as if they were globally available scripts. They are not. These scripts live inside the cc-skills-sdlc plugin's wiki skill at `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/`, not in `P:/.data/wiki/scripts/` (which has different scripts: `append_log.py`, `index_skills.py`, `scan_techniques.py`).

The `/www` SKILL.md instructs the orchestrator to "Run lifecycle tracking (`wiki_after_write.py` + `wiki_state.py`)" — but these scripts are plugin-scoped, and `/www` delegates the write to `/wiki`, so `/www` shouldn't be invoking `/wiki`'s internal lifecycle scripts directly.

## The fix applied

Changed line 268 of `~/.grok/skills/www/SKILL.md` from:

```
Run lifecycle tracking (`wiki_after_write.py` + `wiki_state.py`), confirm `exit_clean: true`, append to `P:/.data/wiki/log.md`.
```

To:

```
Delegate lifecycle tracking (auto-linking, log append, state) to `/wiki` as part of the write — `/www` verifies the wiki concept exists and has the required sections, not `/wiki`'s internal lifecycle scripts.
```

This follows the reference+overlay pattern from `skill-design-patterns-reference-overlay-search-intelligence.md` Pattern 1: `/www` delegates the write to `/wiki`, so it shouldn't reference `/wiki`'s internal lifecycle scripts directly.

## Why this matters

This is a generalizable pattern: user-facing skills should not hardcode plugin-internal script paths. When a skill delegates to another skill, it should delegate the entire sub-workflow including lifecycle tracking, not reference the delegate's internal implementation details. The reference becomes stale when the delegate moves or versions change.

## Falsifier

If `wiki_after_write.py` and `wiki_state.py` are added to `P:/.data/wiki/scripts/` or if `/www` is refactored to call them via a stable interface, this staleness pattern won't recur.

## Receipts

- `~/.grok/skills/www/SKILL.md` line 268 — stale reference verified by reading the file
- `P:/packages/.claude-marketplace/plugins/cc-skills-sdlc/skills/wiki/scripts/` — scripts exist at plugin scope, verified by filesystem search
- `P:/.data/wiki/scripts/` — different scripts live here, verified by listing directory
- Fix applied at Turn 164 of session 019f902a-621d-7711-9436-7c6003c57793
