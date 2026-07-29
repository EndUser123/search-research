---
type: skill-reference
scope: grok-agents
skill_name: config-audit
source_path: P:/.agents/skills/config-audit/SKILL.md
grok_enabled: true
claude_enabled: n/a
indexed_date: 2026-07-29
---

# Skill: config-audit

**Scope:** grok-agents
**Path:** `P:/.agents/skills/config-audit/SKILL.md`

Audit and optimize Grok Build configuration (AGENTS.md, config.toml, plugin settings, MCP servers) against best practices. Scans all configuration files, scores them against a rubric, and proposes targeted improvements. Adapted from Claude-side "claudit" for Grok Build (AGENTS.md instead of CLAUDE.md, config.toml instead of settings.json, no Claude-specific hooks/plugins).

> This is a lightweight pointer for semantic search. The authoritative source
> is the SKILL.md file at the path above. Regenerate with
> `python P:/.data/wiki/scripts/index_skills.py`.
