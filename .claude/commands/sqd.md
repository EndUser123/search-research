---
description: "Frontend for the /sqd skill."
argument-hint: "<sqd question or task>"
---

# /sqd

Use the `sqd` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/sqd/SKILL.md`
- Junction target: /p/packages/sdlc/skills/sqd

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("sqd")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
