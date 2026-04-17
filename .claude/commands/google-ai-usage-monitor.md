---
description: "Frontend for the /google-ai-usage-monitor skill."
argument-hint: "<usage monitoring question or task>"
---

# /google-ai-usage-monitor

Use the `google-ai-usage-monitor` skill as the backing implementation for this command.

- Skill entrypoint: `P:/.claude/skills/google-ai-usage-monitor/SKILL.md`


Instructions:
1. Treat `$ARGUMENTS` as the explicit user query when present.
2. If `$ARGUMENTS` is empty, use the current conversation context.
3. Load `Skill("google-ai-usage-monitor")` first.
4. Follow the skill's documented workflow and output contract exactly.
5. Do not recreate the skill's logic manually in this frontend.
