---
description: "Frontend for the /planning skill."
argument-hint: "<planning question or task>"
---

# /planning

Use the `planning` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/planning/SKILL.md`
- Junction target: `P:/packages/cc-skills-sdlc/skills/planning`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("planning")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate planning analysis manually in this frontend.
