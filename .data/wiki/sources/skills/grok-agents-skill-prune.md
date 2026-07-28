---
type: skill-reference
scope: grok-agents
skill_name: skill-prune
source_path: P:/.agents/skills/skill-prune/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-28
---

# Skill: skill-prune

**Scope:** grok-agents
**Path:** `P:/.agents/skills/skill-prune/SKILL.md`

Knowledge hygiene for skills and wiki concepts — detect stale, duplicate, and drifted entries. Proposes merges, archives, and promotions. Use when the skill catalog is cluttered, after bulk skill additions, or monthly. Adapted from Claude-side "garden" for Grok Build (qmd + index_skills.py as the inventory layer instead of CKS).

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
