# HANDOFF: directory_policy.json gap — identified but not wired

## Status
RESOLVED 2026-08-10 — shared loader created (scripts/directory_policy_loader.py), Grok PreToolUse enforcement wired (PreToolUse_directory_policy.py), /maintain Step 2e consumes loader (duplicate blocklist removed). See commit 4472d65. Follow-ups: run_terminal_command root mutation enforcement, live verification after reload.

## Follow-up closure (2026-08-11)

Both follow-ups verified closed by session 019fe3ff:

1. **run_terminal_command root mutation enforcement — CLOSED by design.** The hook's own docstring delegates shell-root mutations to `mutation_post.py` (observed-result PostToolUse gate). Receipts: `hooks/quality-gate.json` registers `mutation_post.py` 3× (PostToolUse search_replace|write L46, PostToolUse run_terminal_command L66, PostToolUseFailure L83); active-surface snapshot lists it under PostToolUse (run_terminal_command) and PostToolUseFailure. No separate PreToolUse command-text parsing is intended.

2. **Live verification after reload — DONE (execution receipt).** `~/.grok/active-surface.last.md` (2026-08-11 00:58) lists `quality-gate` → `PreToolUse_directory_policy.py` (matcher `search_replace|write`) under PreToolUse — in live dispatch. Test-fired with synthetic stdin:
   - `write` to `P:/root_level_test.py` (non-allowlisted) → exit 2, `{"decision":"block"}` + descriptive stderr ("not in root allowlist", suggestion "Write to tmp/, docs/, or .staging/").
   - `write` to `P:/tmp/cl002_test_allow.py` → exit 0.
   - `run_terminal_command` (non-gated) → exit 0.
   The `hooks = false` flags in config.toml are `[compat.claude]`/`[compat.cursor]` compat-loader toggles (Claude-side settings.json hooks off), NOT a disable of native `~/.grok/hooks/quality-gate.json` hooks.

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
