---
type: skill-reference
scope: claude-cache-ponytail
plugin: ponytail/4.8.4
skill_name: ponytail-review
source_path: C:/Users/brsth/.claude/plugins/cache/ponytail/ponytail/4.8.4/skills/ponytail-review/SKILL.md
indexed_date: 2026-07-23
---

# Skill: ponytail-review

**Scope:** claude-cache-ponytail (plugin: ponytail/4.8.4)
**Path:** `C:/Users/brsth/.claude/plugins/cache/ponytail/ponytail/4.8.4/skills/ponytail-review/SKILL.md`

Code review focused exclusively on over-engineering. Finds what to delete: reinvented standard library, unneeded dependencies, speculative abstractions, dead flexibility. One line per finding: location, what to cut, what replaces it. Use when the user says "review for over-engineering", "what can we delete", "is this over-engineered", "simplify review", or invokes /ponytail-review. Complements correctness-focused review, this one only hunts complexity.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
