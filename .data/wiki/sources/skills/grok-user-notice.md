---
type: skill-reference
scope: grok-user
skill_name: notice
source_path: C:/Users/brsth/.grok/skills/notice/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-28
---

# Skill: notice

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/notice/SKILL.md`

Adaptive mid-conversation observation surfacing driven by content triggers and motivation scoring (not fixed-rate timers). Uses LLM judgment to detect patterns worth surfacing (error states, task boundaries, unverified diagnoses, contradictions, connections, anticipated needs) and scores each candidate on 8 adapted heuristics from Liu et al. CHI 2025 (Inner Thoughts). Fires when motivation exceeds threshold, not when a timer expires. Cooldown is a safety valve (max 1 per 3 turns), not the pri...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
