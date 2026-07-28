---
type: skill-reference
scope: claude-mkt-quickstop
plugin: inkwell
skill_name: query
source_path: C:/Users/brsth/.claude/plugins/marketplaces/quickstop/plugins/inkwell/skills/query/SKILL.md
grok_enabled: n/a
claude_enabled: false
indexed_date: 2026-07-28
---

# Skill: query

**Scope:** claude-mkt-quickstop (plugin: inkwell)
**Path:** `C:/Users/brsth/.claude/plugins/marketplaces/quickstop/plugins/inkwell/skills/query/SKILL.md`

Retrieval-augmented Q&A over the repo's `docs/` tree. Returns a one-paragraph synthesis plus citations (doc path + heading anchor) and per-citation corroboration verdicts. Field shape and ordering are locked at M3; M5 populates the verdicts. allowed-tools: Read, Bash, Glob argument-hint: <question

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
