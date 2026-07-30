---
type: skill-reference
scope: grok-agents
skill_name: fmea
source_path: P:/.agents/skills/fmea/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-29
---

# Skill: fmea

**Scope:** grok-agents
**Path:** `P:/.agents/skills/fmea/SKILL.md`

Failure Modes and Effects Analysis for pipelines and systems. Scans a target directory's Python scripts, identifies I/O boundaries (shared directories, external APIs, state files, caches, databases, subprocess calls), and for each boundary generates a structured FMEA table with severity × occurrence × detection ratings and RPN (Risk Priority Number). Catches component-level failures that narrative pre-mortems miss.

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
