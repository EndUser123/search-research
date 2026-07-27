---
type: skill-reference
scope: grok-user
skill_name: debrief
source_path: C:/Users/brsth/.grok/skills/debrief/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-27
---

# Skill: debrief

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/debrief/SKILL.md`

Smart session retrospective. Scans the current session for actionable improvements across 5 lenses: root causes, code quality, workflow friction, knowledge gaps, and patterns. Uses model-tier-aware subagent fan-out (5 parallel lens subagents + verifier + critic) with automatic model fallback when primary models are out of quota or unreachable. Produces ranked, evidence-cited findings with suggested actions. Use when: the user says /debrief, "what should we learn", "retrospective", "what went ...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
