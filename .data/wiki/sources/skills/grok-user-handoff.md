---
type: skill-reference
scope: grok-user
skill_name: handoff
source_path: C:/Users/brsth/.grok/skills/handoff/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-27
---

# Skill: handoff

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/handoff/SKILL.md`

Write a durable handoff document for the work stream the user asks about. Within-session compaction recovery (reads compaction/segment_*.md). Default invocation (no args) enters auto-update mode: scans the session for all work streams, updates existing handoffs from this session with revision blocks, creates new handoffs for uncovered streams, and promotes durable findings to wiki concepts. Named topic mode writes one handoff for the specified stream. Cross-session chain (thread_id, parent_ha...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
