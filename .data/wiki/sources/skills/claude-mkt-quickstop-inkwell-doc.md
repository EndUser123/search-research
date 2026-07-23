---
type: skill-reference
scope: claude-mkt-quickstop
plugin: inkwell
skill_name: doc
source_path: C:/Users/brsth/.claude/plugins/marketplaces/quickstop/plugins/inkwell/skills/doc/SKILL.md
indexed_date: 2026-07-23
---

# Skill: doc

**Scope:** claude-mkt-quickstop (plugin: inkwell)
**Path:** `C:/Users/brsth/.claude/plugins/marketplaces/quickstop/plugins/inkwell/skills/doc/SKILL.md`

Scaffold a new doc under `docs/` from a Diátaxis template, or update an existing one and bump its `updated:` date. Suggests `## Related` candidates and refreshes the FTS5 index on write. allowed-tools: Read, Write, Edit, Bash, Glob argument-hint: <topic> [--template <name>] [--from-code <path>]

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
