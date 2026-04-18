---
description: "Frontend for the /ai-gemini skill."
argument-hint: "<gemini question or task>"
---

# /ai-gemini

Use the `ai-gemini` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/ai-gemini/SKILL.md`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("ai-gemini")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
