---
description: "Frontend for the /nlm-skill skill."
argument-hint: "<nlm-skill question or task>"
---

# /nlm-skill

Use the `nlm-skill` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/nlm-skill/SKILL.md`


Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("nlm-skill")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
