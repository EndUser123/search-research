---
description: "Frontend for the /mermaid-davila7 skill."
argument-hint: "<mermaid-davila7 question or task>"
---

# /mermaid-davila7

Use the `mermaid-davila7` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/mermaid-davila7/SKILL.md`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("mermaid-davila7")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
