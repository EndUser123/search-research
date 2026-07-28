---
type: skill-reference
scope: grok-agents
skill_name: nlm-to-wiki
source_path: P:/.agents/skills/nlm-to-wiki/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-28
---

# Skill: nlm-to-wiki

**Scope:** grok-agents
**Path:** `P:/.agents/skills/nlm-to-wiki/SKILL.md`

Sync NotebookLM notebook content into the wiki vault as SCHEMA-compliant concept pages with full 4-hop provenance (concept → notebook → cluster → original source URL). v3 exports raw source transcripts via `nlm source content` (not NotebookLM synthesis), clusters them into sub-topics within each notebook, and synthesizes a concept page per sub-topic with per-claim citations. Optional vision enrichment for high-scene-change videos via crv. Branches as `refines` on collision with existing conce...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
