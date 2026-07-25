---
type: skill-reference
scope: grok-user
skill_name: marketplace-bridge
source_path: C:/Users/brsth/.grok/skills/marketplace-bridge/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-25
---

# Skill: marketplace-bridge

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/marketplace-bridge/SKILL.md`

Pulls AI-skill listings from four public marketplaces (SkillsMP, SkillHub, ClawHub, skills.sh), fetches each skill's SKILL.md (and related files when available) into a temporary staging directory, and produces a manifest the user can review before deciding what to install. Use when the user wants to discover or compare skills across marketplaces without committing them to Grok or Claude yet. Invoke with /marketplace-bridge-fetch <query>. The output directory is meant for analysis (security sc...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
