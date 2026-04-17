---
description: "Frontend for the /search skill."
argument-hint: "<search query>"
---

# /search

Use the `search` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/search/SKILL.md`
- Junction target: `P:/packages/search-research`

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("search")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the search logic manually in this frontend.
