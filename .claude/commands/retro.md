---
description: "Frontend for the /retro skill."
argument-hint: "<retro question or task>"
---

# /retro

Use the `retro` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/retro/SKILL.md`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("retro")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
