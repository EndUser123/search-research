---
type: skill-reference
scope: grok-user
skill_name: tasks
source_path: C:/Users/brsth/.grok/skills/tasks/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-29
---

# Skill: tasks

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/tasks/SKILL.md`

Read and write Claude Code's persistent task store at ~/.claude/tasks/project-main-tasks/. Use when the user asks to track cross-session work items, list open tasks, mark tasks done, or check task status. Tasks persist across sessions because they're plain JSON files in the operator's home directory; Grok Build, Codex, Agy, and Claude Code all see the same data without coordination. argument-hint: "list | show <id> | add <subject> | done <id> | status <id> <pending|in_progress|completed>"

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
