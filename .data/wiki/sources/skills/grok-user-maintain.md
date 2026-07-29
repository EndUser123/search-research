---
type: skill-reference
scope: grok-user
skill_name: maintain
source_path: C:/Users/brsth/.grok/skills/maintain/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-28
---

# Skill: maintain

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/maintain/SKILL.md`

Fleet maintenance orchestrator for Grok Build. Three layers: DIAGNOSE (workspace health), ACT (cleanup/rotation/repair), PREVENT (growth limits). Goes beyond the Claude-side "main" skill by fixing problems, not just surfacing them. Runs composable checks (workspace-health, skill-prune, vulture) and adds the missing ACT + PREVENT layers. argument-hint: "[--check | --full | --dry-run | --logs | --artifacts | --data | --handoffs]" user-invocable: true

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
