---
type: skill-reference
scope: grok-user
skill_name: web
source_path: C:/Users/brsth/.grok/skills/web/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-25
---

# Skill: web

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/web/SKILL.md`

Intelligent web research across multiple backends. Every invocation MUST fan out to the mandatory default recipe (minimax-search + web-search-prime + DDG) in parallel, then RRF-merge results. Intent-based routing to Exa, Tavily, Brave, firecrawl, HN Algolia, Stack Exchange, and social platform search is ADDITIVE on top of the default, never a substitute. Research mode with shape= (dos-and-donts, comparisons, anti-patterns, how-tos, facts) and depth= (quick, standard, deep with iterative refin...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
