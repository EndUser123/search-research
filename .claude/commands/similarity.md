---
description: "Frontend for the /similarity skill."
argument-hint: "<similarity question or task>"
---

# /similarity

Use the `similarity` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/similarity/SKILL.md`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("similarity")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
