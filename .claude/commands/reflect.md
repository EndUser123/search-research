---
description: "Frontend for the /reflect skill."
argument-hint: "<reflect question or task>"
---

# /reflect

Use the `reflect` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/reflect/SKILL.md`
- Junction target: P:/packages/cc-skills-meta/skills/reflect

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("reflect")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
