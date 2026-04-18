---
description: "Frontend for the /ai-pi-gg-gemma skill."
argument-hint: "<target file or description to review>"
---

# /ai-pi-gg-gemma

Use the `ai-pi-gg-gemma` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/ai-pi-gg-gemma/SKILL.md`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("ai-pi-gg-gemma")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
