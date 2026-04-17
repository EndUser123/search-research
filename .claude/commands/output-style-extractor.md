---
description: "Frontend for the /output-style-extractor skill."
argument-hint: "<output-style-extractor question or task>"
---

# /output-style-extractor

Use the `output-style-extractor` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/output-style-extractor/SKILL.md`


Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("output-style-extractor")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
