---
description: "Frontend for the /sqa skill."
argument-hint: "<sqa question or task>"
---

# /sqa

Use the `sqa` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/sqa/SKILL.md`
- Junction target: /p/packages/sdlc/skills/sqa

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("sqa")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
