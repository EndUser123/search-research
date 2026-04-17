---
description: "Chat history search and session chain export."
argument-hint: "<search query or export>"
---

# /chs

Use the `chs` skill as the backing implementation for this command.

- Skill entrypoint: `P:/packages/search-research/skills/chs/scripts/chs_cli.py`
- Primary use: Search chat history, export session chains

Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("chs")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
