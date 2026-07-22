---
type: skill-reference
scope: grok-project
skill_name: handoff
source_path: P:/.grok/skills/handoff/SKILL.md
indexed_date: 2026-07-21
---

# Skill: handoff

**Scope:** grok-project
**Path:** `P:/.grok/skills/handoff/SKILL.md`

Write a durable handoff document for the work stream the user asks about. Within-session compaction recovery (reads compaction/segment_*.md). Default scope: the current user request's work stream. Notes other outstanding streams if obvious from current context. Cross-session chain (thread_id, parent_handoff_path) is supported structurally but continuation is v0.2. Use for /handoff, handoff, session handoff, continuing work, work brief. argument-hint: "[new <topic> | close <path> | list] (defa...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
