---
type: skill-reference
scope: grok-user
skill_name: search-fleet
source_path: C:/Users/brsth/.grok/skills/search-fleet/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-26
---

# Skill: search-fleet

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/search-fleet/SKILL.md`

Capability-routed multi-backend search with RRF aggregation. Reads the tool registry at ~/.grok/search-fleet.toml, classifies query intent, dispatches to optimal backends in parallel, and merges results via Reciprocal Rank Fusion. To add a new search tool, add a [tools.<id>] block to the registry — no skill edits needed. Use for: web search, deep research, multi-source verification, any query where backend choice matters. Aliases: /sf.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
