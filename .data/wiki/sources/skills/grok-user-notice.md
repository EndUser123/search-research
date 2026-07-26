---
type: skill-reference
scope: grok-user
skill_name: notice
source_path: C:/Users/brsth/.grok/skills/notice/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-26
---

# Skill: notice

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/notice/SKILL.md`

Mid-conversation high-confidence observation surfacing. Fires when mechanical triggers match (error state, task boundary, stuck-loop pattern) or on manual invocation. Strictly gated: global cooldown (max 1 per 10 turns), type constraint (contradictions / drift / recurring friction only), confidence floor (≥2 source instances), hard-skip patterns (acceleration mode, first turn, mid-implementation). Output is one line or silence. Use when the operator says /notice, "did you notice anything?", o...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
