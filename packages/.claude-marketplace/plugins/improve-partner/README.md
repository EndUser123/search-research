# improve-partner plugin

Improvement partner plugin. `/improve` is the central manual thought-partner
workflow; three specialist agents support it.

> **Status (task #1052, 2026-07-05):** the 4 inert hooks (UserPromptSubmit /
> PostToolUse / Stop / SubagentStop) and their scripts were deleted — they were
> never wired, never fired, and duplicated live systems (semantic-critic Stop
> aggregator, cc-aca-observability PostToolUse, the 8 UPS injectors, built-in
> SubagentStop evaluator). The genuinely novel ideas they carried
> (deterministic domain classification, file-path severity weighting, the
> review-request artifact shape, Stop-hook cooldown) are preserved at
> `P:/.data/wiki/concepts/improve-partner-novel-ideas.md` for later folding
> into existing live gates. Original code remains in git history.

## Included
- `.claude-plugin/plugin.json`
- `skills/improve/SKILL.md`
- `agents/prompt-specialist.md`
- `agents/workflow-specialist.md`
- `agents/hook-plugin-specialist.md`
- `hooks/hooks.json` (`{"hooks": {}}` — no live hooks; dispatch invariant)
- `OUTPUT_SCHEMA.md`
- `README.md`

## Behavior
- `/improve` is the primary improvement/thought-partner interface.
- Three specialist agents (`prompt-specialist`, `workflow-specialist`,
  `hook-plugin-specialist`) are dispatched by `/improve` when its workflow
  needs a focused review pass.

## Default posture
Suggest mode only — no hooks take control away from the user. `/improve`
surfaces recommendations; the user decides.
