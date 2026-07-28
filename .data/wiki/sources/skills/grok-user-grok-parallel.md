---
type: skill-reference
scope: grok-user
skill_name: grok-parallel
source_path: C:/Users/brsth/.grok/skills/grok-parallel/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-28
---

# Skill: grok-parallel

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/grok-parallel/SKILL.md`

Fan out independent work across Grok subagents (and worktrees when writes conflict) for research, implementation, testing, and adversarial review. Use for multi-part tasks, parallel investigation, "use subagents", speed runs on independent files, or when the user says /grok-parallel, parallel, fan-out, multi-agent, or worktree agents. When executing multi-task plans, respect depends_on / track order (DAG); only parallelize independent tasks.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
