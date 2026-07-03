# cc-aca-session

ACA Session plugin — session lifecycle hooks for the Agent Control Architecture.

## Responsibility

Session-scoped state management: cleanup at start/end, breadcrumb initialization, TDD state cleanup, PreCompact handling.

## Hooks

| Hook | Lifecycle | Origin |
|------|-----------|--------|
| aca_session_verification_cleanup.py | SessionStart | Migrated from `P:/.claude/hooks/SessionStart_verification_cleanup.py` |
| aca_session_breadcrumb_init.py | SessionStart | Migrated from `P:/.claude/hooks/SessionStart_breadcrumb_init.py` |
| aca_session_cleanup.py | SessionEnd | Migrated from `P:/.claude/hooks/SessionEnd_cleanup.py` |
| aca_session_breadcrumb_cleanup.py | SessionEnd | Migrated from `P:/.claude/hooks/SessionEnd_breadcrumb_cleanup.py` |
| aca_session_tdd_cleanup.py | SessionEnd | Migrated from `P:/.claude/hooks/SessionEnd_tdd_cleanup.py` |
| aca_session_precompact.py | PreCompact | Migrated from `P:/.claude/hooks/PreCompact.py` |

## Not Yet Absorbed

These snapshot plugin hooks are classified as cc-aca-session but remain in the snapshot plugin during the pilot:
- `snapshot_PreCompact.py`
- `snapshot_SessionStart.py`
- `snapshot_SessionEnd_tldr.py`
- `snapshot_UserPromptSubmit.py`

## Architecture

Compatibility wrappers in `P:/.claude/hooks/` delegate to this plugin via import. Settings.json registration unchanged.

## State Paths

Shared state path constants in `__lib/aca_state_paths.py`.
