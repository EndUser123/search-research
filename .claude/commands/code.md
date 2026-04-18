---
description: "Frontend for the /code skill."
argument-hint: "<code question or task>"
---

# /code

Use the `code` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/code/SKILL.md`
- Junction target: `P:/packages/cc-skills-sdlc/skills/code`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("code")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
