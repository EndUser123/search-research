---
description: "Frontend for the /learn skill."
argument-hint: "<learn question or task>"
---

# /learn

Use the `learn` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/learn/SKILL.md`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("learn")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
