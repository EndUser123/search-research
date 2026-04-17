---
description: "Frontend for the /arch skill."
argument-hint: "<architecture question or task>"
---

# /arch

Use the `arch` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/arch/SKILL.md`
- Junction target: `P:/packages/sdlc/skills/arch`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("arch")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate architecture analysis manually in this frontend.
