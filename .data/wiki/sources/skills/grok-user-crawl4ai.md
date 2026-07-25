---
type: skill-reference
scope: grok-user
skill_name: crawl4ai
source_path: C:/Users/brsth/.grok/skills/crawl4ai/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-25
---

# Skill: crawl4ai

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/crawl4ai/SKILL.md`

Ingest websites into QMD wiki collections for semantic search via /wiki. Crawls with crawl4ai (local Python), dedupes by SHA256 + etag, injects [[wikilinks]] to related pages, logs to log.md, and rebuilds the qmd index. Use when adding web docs or articles to the searchable vault.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
