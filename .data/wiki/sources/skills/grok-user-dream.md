---
type: skill-reference
scope: grok-user
skill_name: dream
source_path: C:/Users/brsth/.grok/skills/dream/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-29
---

# Skill: dream

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/dream/SKILL.md`

Offline memory consolidation for the LLM agent fleet. Reads the last 90 days of handoffs, AAR artifacts, and the www-ledger; synthesizes cross-session patterns; proposes ADDITIONS (new wiki concepts), CONTRADICTIONS (drift detection across the existing wiki + ADRs), and RETIREMENTS (dormant in v1 — activates when the wiki accumulates stale concepts). Manual trigger only in v1. Non-destructive: writes a candidate proposal to P:/docs/dreams/YYYY-MM-DD-dream.md; the operator promotes via the exi...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
