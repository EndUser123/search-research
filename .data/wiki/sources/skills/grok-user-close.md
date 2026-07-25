---
type: skill-reference
scope: grok-user
skill_name: close
source_path: C:/Users/brsth/.grok/skills/close/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-25
---

# Skill: close

**Scope:** grok-user
**Path:** `C:/Users/brsth/.grok/skills/close/SKILL.md`

Session close-out orchestrator. Runs close_accounting.py to scan handoffs, wiki, git commits, temp files, git status, and AAR artifacts — resolving all gates mechanically. Emits a summary template with pre-computed gate states. The final report is organized for human scanning: status first, open risks next, then completed work and supporting detail. Loops only when a concrete gap is detected. Use for /close, session end, wrapping up, "anything left?". argument-hint: "[--quick|--deep] [--no-lo...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
