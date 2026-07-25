---
type: skill-reference
scope: grok-user
skill_name: handoff
source_path: C:/Users/brsth/.grok/skills/handoff/SKILL.md
indexed_date: 2026-07-25
---

# Skill: handoff

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/handoff/SKILL.md`

Write a durable handoff document for the work stream the user asks about. Within-session compaction recovery (reads compaction/segment_*.md). Default scope: the current user request's work stream. Notes other outstanding streams if obvious from current context. Cross-session chain (thread_id, parent_handoff_path) is supported structurally but continuation is v0.2. Use for /handoff, handoff, session handoff, continuing work, work brief. argument-hint: "[<topic> | <report-path> | close <path> |...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
