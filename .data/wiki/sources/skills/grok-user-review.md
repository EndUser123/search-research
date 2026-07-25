---
type: skill-reference
scope: grok-user
skill_name: review
source_path: C:/Users/brsth/.grok/skills/review/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-25
---

# Skill: review

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/review/SKILL.md`

Intelligent code/package review with verified findings on disk. Auto-infers target (local diff, branch, PR, or package path) and lenses (correctness, integrity, maintainability, security, architecture). Always writes a run_dir + FINDINGS.md; severity≥risk findings must be verified against source before labeled verified. Use for /review, code review, critical review, package audit, PR review, "review my changes", or when /go routes a review-only task here. when-to-use: > /review, code review, ...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
