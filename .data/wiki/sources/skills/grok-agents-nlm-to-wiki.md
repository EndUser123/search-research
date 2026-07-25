---
type: skill-reference
scope: grok-agents
skill_name: nlm-to-wiki
source_path: P:/.agents/skills/nlm-to-wiki/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-25
---

# Skill: nlm-to-wiki

**Scope:** grok-agents
**Path:** `P:/.agents/skills/nlm-to-wiki/SKILL.md`

Sync NotebookLM notebook content into the wiki vault as SCHEMA-compliant concept pages with full 4-hop provenance (concept → notebook → cluster → original source URL). Uses Report + Data-Table artifacts (not chat) for structured, citable extraction. Branches as `refines` on collision with existing concepts rather than overwriting. Composes with nlm-bulk-ingest via --from-clusters for full round-trip from raw URL list to wiki concepts.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
