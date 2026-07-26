---
type: skill-reference
scope: claude-cache-local
plugin: cc-skills-lab/1.0.16
skill_name: simplify-enhanced
source_path: C:/Users/brsth/.claude/plugins/cache/local/cc-skills-lab/1.0.16/skills/simplify-enhanced/SKILL.md
grok_enabled: n/a
claude_enabled: true
indexed_date: 2026-07-26
---

# Skill: simplify-enhanced

**Scope:** claude-cache-local (plugin: cc-skills-lab/1.0.16)
**Path:** `C:/Users/brsth/.claude/plugins/cache/local/cc-skills-lab/1.0.16/skills/simplify-enhanced/SKILL.md`

Wrapper around the built-in /simplify that adds a false-positive-resistant code-reuse pass. Invokes the built-in first (reuse + simplification + efficiency + altitude + apply), then runs a discrimination-scale duplicate detector the built-in cannot guarantee.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
