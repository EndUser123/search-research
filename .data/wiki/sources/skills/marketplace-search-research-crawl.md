---
type: skill-reference
scope: marketplace
plugin: search-research
skill_name: crawl
source_path: P:/packages/.claude-marketplace/plugins/search-research/skills/crawl/SKILL.md
grok_enabled: false
claude_enabled: true
indexed_date: 2026-07-29
---

# Skill: crawl

**Scope:** marketplace (plugin: search-research)
**Path:** `P:/packages/.claude-marketplace/plugins/search-research/skills/crawl/SKILL.md`

Ingest websites into QMD wiki collections for semantic search via /search and /explore. Crawls with crawl4ai, dedupes by SHA256, injects [[wikilinks]] to related pages, logs to log.md, and rebuilds the qmd index. Use when adding web docs or articles to the searchable vault.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
