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
1. `ls P:/.claude/skills/` for local skills
2. `ls P:/packages/.claude-marketplace/plugins/` for plugin skills
3. Grep SKILL.md files for the capability name
4. Check wiki at `P:/.data/wiki/`

## Decision Rule

If a skill matches the user's request, invoke it via Skill tool BEFORE generating any other response about the task.
