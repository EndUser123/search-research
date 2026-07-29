---
type: skill-reference
scope: grok-user
skill_name: grok-verify
source_path: C:/Users/brsth/.grok/skills/grok-verify/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-29
---

# Skill: grok-verify

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/grok-verify/SKILL.md`

Evidence-first completion gate: refuse "done/fixed/verified" claims until scope, tests, runtime path, and dirty-tree checks pass. Use before claiming work is complete, after implementation waves, before handoff, or when the user says /grok-verify, verify, verify-before-done, definition of done, or "are we done". Supports non-git trees (skips git hygiene; requires edit-then-verify receipts).

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
