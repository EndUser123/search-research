---
type: skill-reference
scope: grok-agents
skill_name: workspace-health
source_path: P:/.agents/skills/workspace-health/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-28
---

# Skill: workspace-health

**Scope:** grok-agents
**Path:** `P:/.agents/skills/workspace-health/SKILL.md`

System health checks and workspace validation for Grok Build. Runs health checks across the workspace: git state, skill catalog integrity, wiki vault health, config validation, hook dispatch chain, and plugin enable-state consistency. Adapted from Claude-side "main" for Grok Build (no CKS, no Claude hooks/settings.json checks; uses index_skills.py --audit and qmd).

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
