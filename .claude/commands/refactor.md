---
description: "Frontend for the /refactor skill."
argument-hint: "<refactoring question or task>"
---

# /refactor

Use the `refactor` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/refactor/SKILL.md`
- Junction target: `P:/packages/sdlc/skills/refactor`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("refactor")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
