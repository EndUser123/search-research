---
type: skill-reference
scope: grok-user
skill_name: crawl4ai
source_path: C:/Users/brsth/.grok/skills/crawl4ai/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-29
---

# Skill: crawl4ai

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/crawl4ai/SKILL.md`

Ingest websites into the wiki vault as searchable markdown. Crawls with crawl4ai (local Python), dedupes by SHA256 + etag, injects [[wikilinks]] to related pages, and logs to log.md. Use when adding web docs or articles to the searchable vault.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
