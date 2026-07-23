---
type: skill-reference
scope: claude-cache-local
plugin: search-research/0.1.123
skill_name: crawl
source_path: C:/Users/brsth/.claude/plugins/cache/local/search-research/0.1.123/skills/crawl/SKILL.md
indexed_date: 2026-07-23
---

# Skill: crawl

**Scope:** claude-cache-local (plugin: search-research/0.1.123)
**Path:** `C:/Users/brsth/.claude/plugins/cache/local/search-research/0.1.123/skills/crawl/SKILL.md`

Ingest websites into QMD wiki collections for semantic search via /search and /explore. Crawls with crawl4ai, dedupes by SHA256, injects [[wikilinks]] to related pages, logs to log.md, and rebuilds the qmd index. Use when adding web docs or articles to the searchable vault.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
