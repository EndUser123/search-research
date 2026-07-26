---
type: skill-reference
scope: grok-agents
skill_name: nlm-bulk-ingest
source_path: P:/.agents/skills/nlm-bulk-ingest/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-26
---

# Skill: nlm-bulk-ingest

**Scope:** grok-agents
**Path:** `P:/.agents/skills/nlm-bulk-ingest/SKILL.md`

Cluster a large list of URLs (YouTube videos, web pages, PDFs) into themed NotebookLM notebooks under the per-notebook source cap, then bulk-add them in one call per notebook with crash-resumable checkpointing. Handles source caps from 50 (free) to 300+ (paid), semantic clustering with bounded cluster size, and the cosmetic first-URL error that panics naive scripts. Use when you have more URLs than one notebook can hold and want them organized by theme rather than dumped in arbitrary chunks.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
