---
type: skill-reference
scope: grok-user
skill_name: grok-safe-git
source_path: C:/Users/brsth/.grok/skills/grok-safe-git/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-27
---

# Skill: grok-safe-git

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/grok-safe-git/SKILL.md`

Concurrent-safe git preflight and destructive-operation guard for multi-agent workspaces. Use before any file edit in a dirty tree, before commit/stash/reset/ clean/checkout, when other agents may be active, or when the user says /grok-safe-git, safe-git, staged guard, git preflight, or "protect staged work". Degrades cleanly when CWD is not a git repository (non-git mode).

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
