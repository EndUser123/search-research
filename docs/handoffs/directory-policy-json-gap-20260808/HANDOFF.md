# HANDOFF: directory_policy.json gap — identified but not wired

## Status
OPEN — investigation + implementation needed

## Objective
Wire the directory-policy hook into Grok Build's live dispatch. The hook was identified by a sibling session (019fdf3d) as existing in config but not in active dispatch. It needs to be either activated or removed.

## Context
- A sibling session analyzed the directory-policy.json hook and found it is NOT in live dispatch on Grok Build
- `config.toml` has zero references to any directory-policy hook
- The active-surface snapshot confirms the hook is not firing
- Claude side: the policy IS consumed (`__lib/path_validator.py`, `pre_tool_use_logic.py:414`)
- Grok side: zero references — the hook exists as a file but is dead code
- The /tp lenses recommended advisory mode (log violations, don't deny) as the initial deployment

## Key questions
1. Should the hook be wired into live dispatch? (AGY recommended advisory mode)
2. Where does it live — `~/.grok/hooks/` or plugin hooks?
3. What does the policy enforce? (Directory access restrictions per terminal/session)

## Acceptance criteria
- Decision made: activate (advisory mode) or remove
- If activate: wired into config.toml or settings, tested with a sample session
- If remove: file deleted, references cleaned up

## Suggested next invocation
```
/go Investigate the directory_policy.json hook at ~/.grok/hooks/ — it exists but is not in live dispatch. Decide: activate in advisory mode or remove. Check config.toml and the active-surface snapshot for confirmation.
```

## References
- Session 019fdf3d analysis (sibling session)
- Active-surface snapshot at `~/.grok/active-surface.last.md`
