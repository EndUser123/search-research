---
name: workspace-health
description: >
  System health checks and workspace validation for Grok Build. Runs health
  checks across the workspace: git state, skill catalog integrity, wiki vault
  health, config validation, hook dispatch chain, and plugin enable-state
  consistency. Adapted from Claude-side "main" for Grok Build (no CKS, no
  Claude hooks/settings.json checks; uses index_skills.py --audit and qmd).
host: both
---

# /workspace-health — Workspace health and validation

Run health checks across the Grok Build workspace. Single command that
surfaces infrastructure problems before they cause silent failures.

## When to use

- Session start (after prior session touched workspace)
- Monthly maintenance
- After bulk changes (plugin installs, skill additions, wiki bulk ingest)
- When something feels off ("why isn't X working?")

## When NOT to use

- Mid-task debugging — use `/debugging-and-error-recovery` instead
- Skill-specific issues — use `/skill-prune` instead
- File recovery — use `/recover` instead

## Health checks (Grok Build adapted)

| Check | What it validates | Command |
|---|---|---|
| **git_state** | Uncommitted files, stale dirty files, submodule consistency | `python P:/.agents/scripts/git_state_check.py` + `python P:/.agents/scripts/dirty_age.py` |
| **skill_catalog** | Duplicate skills, disabled-in-Grok count, orphan script references | `python P:/.data/wiki/scripts/index_skills.py --audit` |
| **wiki_vault** | Broken wikilinks, orphan pages, stale concepts, validation failures | `python P:/.data/wiki/scripts/wiki_health_check.py --json` |
| **config_toml** | `~/.grok/config.toml` parses, no contradictory settings | `python -c "import tomllib; tomllib.load(open(...))"` |
| **plugin_consistency** | `[plugins].disabled` (Grok) vs `enabledPlugins` (Claude) don't conflict | Cross-check both config files |
| **qmd_index** | QMD collection is healthy, no corrupted embeddings | `qmd collection info --collection wiki` |
| **handoff_drift** | Open handoffs with `head:DRIFT` (stale `accurate_as_of_head`) | `python ~/.grok/skills/handoff/__lib/list_handoffs.py --head $(git rev-parse HEAD)` |
| **nlm_auth** | NotebookLM auth is valid (probe, not `--check` which lies) | `nlm notebook list --profile codex --quiet` (exit 0 = healthy) |
| **disk_space** | P:\ and ~/.grok have reasonable free space | `Get-PSDrive P`, `Get-PSDrive C` |

## Output format

```
=== WORKSPACE HEALTH ===
Score: XX/100 (HEALTHY | WARNING | CRITICAL)

git_state:         ✓ 0 stale files, 0 submodule issues
skill_catalog:     ⚠ 204 duplicates, 237 disabled-in-Grok, 187 orphan refs
wiki_vault:        ✓ 206 concepts, 0 broken links
config_toml:       ✓ parses cleanly
plugin_consistency: ⚠ cc-skills-media disabled in Grok, enabled in Claude
qmd_index:         ✓ wiki collection healthy
handoff_drift:     ⚠ 3 handoffs with head:DRIFT
nlm_auth:          ✓ profile codex valid
disk_space:        ✓ P: 245GB free, C: 89GB free

=== RECOMMENDATIONS ===
1. Run /skill-prune to address 204 duplicate skill entries
2. Re-verify 3 handoffs with stale HEAD references
3. Decide on cc-skills-media: disable in Claude too, or enable in Grok?
```

## Grok Build differences from Claude Code

| Aspect | Claude Code ("main") | Grok Build (this skill) |
|---|---|---|
| Config file | `~/.claude/settings.json` | `~/.grok/config.toml` (TOML, not JSON) |
| Hooks | Claude hook system | Grok hook system (command + http only) |
| CKS | Constitutional Knowledge System | N/A — use qmd + wiki instead |
| Skills health | Duplicate trigger detection | `index_skills.py --audit` |
| Plugin state | `enabledPlugins` (opt-in) | `[plugins].disabled` (opt-out) |
| Health script | `main_health.py` (single script) | Composed checks (no single script — each check is independent) |

## References

- `P:/.data/wiki/scripts/index_skills.py --audit` — skill catalog auditor
- `P:/.data/wiki/scripts/wiki_health_check.py` — wiki vault health
- `P:/.agents/scripts/git_state_check.py` — git state cross-repo check
- `P:/.agents/scripts/dirty_age.py` — stale dirty file detection
- Adapted from Claude-side `main` skill (cc-skills-utils)
