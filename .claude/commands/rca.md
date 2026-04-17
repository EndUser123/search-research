---
description: "Frontend for the /rca skill."
argument-hint: "<root cause analysis question or task>"
---

# /rca

Use the `rca` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/rca/SKILL.md`
- Junction target: `P:/packages/sdlc/skills/rca`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("rca")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
