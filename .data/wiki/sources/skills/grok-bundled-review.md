---
type: skill-reference
scope: grok-bundled
skill_name: review
source_path: C:/Users/brsth/.grok/bundled/skills/review/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-29
---

# Skill: review

**Scope:** grok-bundled
**Path:** `C:/Users/brsth/.grok/bundled/skills/review/SKILL.md`

Run a reviewer subagent against uncommitted local changes, a named branch, or a GitHub PR. Local and branch modes write a review file plus a summary to disk. PR mode posts the findings as a PENDING GitHub review for the user to inspect and submit through the UI. when-to-use: "Use when asked to 'review', 'code review', 'review my changes', 'review this PR', or '/review'." argument-hint: "[--local | --branch <name> | --pr <number-or-url> | <auto-detect>]"

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
