---
title: "Grok Build Compat Layer Does Not Surface Marketplace Plugin-Bundled Skills"
created: 2026-07-20
source: session-2026-07-20
tags: ['grok-build', 'compat-layer', 'skills', 'discovery', 'host-grok']
summary: >
  The `compat.claude.skills = true` (and similar for cursor/codex) cells in `~/.grok/config.toml` scan `~/.claude/skills/<name>/SKILL.md` directly. They do NOT scan plugin-bundled `skills/` directories under `~/.claude/plugins/<plugin>/skills/` or marketplace plugin source at `P:/packages/.claude-marketplace/plugins/<name>/skills/`. Result: a plugin can be 'enabled' in `grok inspect` while its skills are not invocable as slash commands.
agent: grok
host: grok
cognitive_load: 3
verification: local-only
---

## Summary

Empirical finding (2026-07-20): the Claude-side `search-research` plugin shows up as `enabled` in `grok inspect --json` with `provides: skills=16 agents=1`. The plugin's `skills/web/SKILL.md` exists at `P:\packages\.claude-marketplace\plugins\search-research\skills\web\SKILL.md`. But `/web` does not appear in the slash-command autocomplete, and `grok inspect --json` `skills` section does not list a skill named `web`. The user cannot invoke it.

## Key Findings

- **What gets surfaced as skills.** Per `grok inspect --json` skills-section source breakdown:
  - `~/.grok/skills/<name>/SKILL.md` (user-scope Grok skills)
  - `~/.agents/skills/<name>/SKILL.md` (user-scope agent skills)
  - `~/.grok/bundled/skills/<name>/SKILL.md` (Grok-bundled skills)
  - `~/.claude/skills/<name>/SKILL.md` (Claude-compat individual skill files — 8 of these total)
  - `~/.claude/plugins/cache/...` (cached plugin skills from installed plugins)
  - `~/.grok/installed-plugins/<plugin>/skills/<name>/SKILL.md` (firecrawl, superpowers — these DO surface because they are properly installed)
- **What does NOT get surfaced.** Marketplace plugin source at `P:\packages\.claude-marketplace\plugins\<plugin>\skills\<name>\SKILL.md`. These exist on disk but the compat layer does not scan them. The `search-research` plugin's 16 skills are all in this category.
- **Symptom.** The plugin shows as enabled in the plugins section of inspect. Its skills do not appear in the skills section. Slash commands derived from those skills (`/web`, `/web --fetch-urls`, etc.) are not invocable.
- **Workarounds.**
  - Build a Grok-native skill at `~/.grok/skills/<name>/SKILL.md` (highest-priority location per `08-skills.md`).
  - Install the marketplace plugin properly via `grok plugin install <github-url>` so its skills get copied to a recognized installed-plugin path.
  - Manually copy the SKILL.md to `~/.grok/skills/<name>/SKILL.md`.

## Related

- [[grok-build-plan-mode-structured-thinking]] — adjacent: building a delegation-aware `/plan` user-level skill is hidden by built-in `/plan` priority
- [[grok-build-cc-aca-actually-enabled]] — the cc-aca-* enforcement fires regardless of the compat-layer skill gap
- [[operator-collaboration-style-and-leverage]] — operator-side context for choosing when to build native vs install compat

## Auto-related

<!-- auto-managed by wiki_after_write.py -->

## Sources

- session-2026-07-20 — `grok inspect --json` skills-section source listing
- session-2026-07-20 — direct read of `P:\packages\.claude-marketplace\plugins\search-research\skills\web\SKILL.md`
- session-2026-07-20 — attempt to invoke `/web` produced no autocomplete match
