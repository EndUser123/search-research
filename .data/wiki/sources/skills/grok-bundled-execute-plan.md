---
type: skill-reference
scope: grok-bundled
skill_name: execute-plan
source_path: C:/Users/brsth/.grok/bundled/skills/execute-plan/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-29
---

# Skill: execute-plan

**Scope:** grok-bundled
**Path:** `C:/Users/brsth/.grok/bundled/skills/execute-plan/SKILL.md`

Execute a PR Plan DAG from a design document. Parses the plan, topologically sorts it, implements PRs in parallel using worktree-isolated subagents, runs mandatory orchestrator-level review, and assembles either a Graphite PR stack or a plain-git branch stack depending on tool availability. when-to-use: Use when asked to "execute plan", "run the plan", "implement the design", or "/execute-plan". argument-hint: "<design-doc-path> [--effort N] [--concurrency N] [--dry-run] [--resume <PLAN_ID>] ...

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
