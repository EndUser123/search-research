---
description: "Skill types, routing, contract authority, and anti-forgetting protocol"
alwaysApply: true
---

# Skill Protocol

## Skill Types

| Type | Definition | Examples |
|------|-----------|----------|
| EXECUTION | Performs a concrete action | /bf, /refactor, /gto |
| KNOWLEDGE | Retrieves information | /search, /wiki |
| PROCEDURE | Guides a multi-step workflow | /migrate-skill-contract |

## Execution Skill Protocol

1. Skill loaded → cite one piece of evidence the task is in that skill's domain
2. If no clear evidence, answer directly with first-principles tools instead
3. Execute the skill's workflow

## Routing Spine

Slash commands (`/skill-name args`) invoke the Skill tool immediately.
Do not replicate skill logic manually. Do not guess skill names.

## Contract Authority Packet

When a skill defines a contract (input schema, output format, required artifacts):
- The skill's SKILL.md is the authoritative source
- CLAUDE.md references are pointers, not overrides
- Conflicts: SKILL.md wins over CLAUDE.md

## Anti-Forgetting Checklist

Before claiming a skill or workflow doesn't exist:
1. **Check the session skill catalog** (the system reminder at session start lists all invocable skills with absolute paths) — this is the authoritative registry
2. **Check `P:/.data/wiki/concepts/skill-catalog.md`** — the durable on-disk catalog maintained by `index_skills.py`, covering all scopes including `~/.grok/installed-plugins/`, `~/.claude/plugins/cache/`, and marketplace sources
3. **Do NOT use filesystem grep to check skill existence** — ripgrep silently skips gitignored directories (`installed-plugins/`, `plugins/cache/`), producing false negatives. Reference incident 2026-07-28: grep for `name: brainstorming` returned zero matches because `installed-plugins/` is gitignored; the skill existed and was in the catalog the entire time.
4. If filesystem search is still needed after the catalog: use `list_dir` or `Get-ChildItem -Recurse`, not `grep`/`rg`

## Decision Rule

If a skill matches the user's request, invoke it via Skill tool BEFORE generating any other response about the task.
