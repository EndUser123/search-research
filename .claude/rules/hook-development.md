---
description: "Rules for editing hook files in the CSF framework"
alwaysApply: false
---

# Hook Development

## Before Editing Any Hook File

1. Read `P:/.claude/hooks/PreToolUse.py`
2. Search for "DISPATCH CHAIN" comment block
3. Confirm your target file appears in UNIVERSAL or TOOL_HOOKS lists
4. Do NOT edit any `PreToolUse_*.py` file not in the dispatch chain

Quick check:
    grep -n "UNIVERSAL\|TOOL_HOOKS" P:/.claude/hooks/PreToolUse.py | grep -i "target_file"

Dead files (never edit): `PreToolUse_skill_first_gate.py`, `PreToolUse_workflow_steps_gate.py`

## Plugin Hook Naming

Plugin hook scripts must use `{plugin_name}_{event}.py` naming.
See `packages/CLAUDE.md` for the full naming standard and hooks.json format.

## Critical File Recovery Mode

Protected files: hooks/, anti_sycophancy/, validators/, CLAUDE.md, settings.json, __lib/.
If a protected file becomes syntactically invalid after an edit:
1. **Stop patching immediately.** Do not compound edits.
2. Use `git show HEAD:path > path` to restore from last known good state.
3. Verify with `python -c "import <module>"` before continuing.

## Testing

- Run `pytest` in the hooks directory after any hook edit.
- Test file location: `P:/.claude/hooks/tests/`
- Anti-mock stance: test hook behavior against real dispatch, not mocked inputs.
- Blocking hooks must print descriptive stderr on exit(2).

## Blocking Hook stderr Requirement

Any hook that exits with code 2 (block) MUST print a descriptive message to stderr
explaining what was blocked and what action to take. Empty stderr on block is a bug.

## Logging

Hook output goes to `P:/.claude/hooks/.evidence/` and `cc_errors.jsonl`.
Use structured logging. Don't write to arbitrary locations.

## Architecture Details

For dispatch chain architecture, enforcement tier reference, and systemic issue history,
see wiki: `P:/.data/wiki/concepts/` — search for "hook" or "dispatch".
