---
description: "Frontend for the /universal-skills-manager skill."
argument-hint: "<universal-skills-manager question or task>"
---

# /universal-skills-manager

Use the `universal-skills-manager` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/universal-skills-manager/SKILL.md`


Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("universal-skills-manager")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
