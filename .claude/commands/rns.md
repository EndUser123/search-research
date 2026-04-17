---
description: "Frontend for the /rns skill."
argument-hint: "<rns question or task>"
---

# /rns

Use the `rns` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/rns/SKILL.md`
- Junction target: `P:/packages/rns`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("rns")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
