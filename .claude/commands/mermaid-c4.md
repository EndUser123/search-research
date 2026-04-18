---
description: "Frontend for the /mermaid-c4 skill."
argument-hint: "<mermaid-c4 question or task>"
---

# /mermaid-c4

Use the `mermaid-c4` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/mermaid-c4/SKILL.md`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("mermaid-c4")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
