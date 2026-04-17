---
description: "Frontend for the /notebooklm skill."
argument-hint: "<notebooklm question or task>"
---

# /notebooklm

Use the `notebooklm` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/notebooklm/SKILL.md`
- Junction target: /p/.agents/skills/notebooklm

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("notebooklm")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
