---
thread_id: keep-smaller-copy-tui
current_session_id: 019f91d3-2741-7f83-af68-211796180474
parent_handoff_path: none
assignee: grok
status: OPEN
created: 2026-07-24
---

# Keep-Smaller-Copy TUI — work stream handoff

## What this is

`D:\.code\Keep-Smaller-Copy\app.py` — a Textual 8.0.2 TUI for replacing larger
video files with smaller copies. Not a git repo. Settings in `settings.json`.

## What was done this session

- Fixed cross-extension matching (`.mp4` source vs `.mkv` target no longer silently dropped)
- Fixed overlap detection (substring → `os.path.commonpath`)
- Fixed nested-folder scanning (exclude target subtree from source walk instead of blocking)
- Fixed save-on-quit (added `async def action_quit`)
- Fixed Stop button (immediate button reset + mid-walk stop_event checks)
- Added Copy button alongside Move (source preserved with `shutil.copy2`)
- Added Status column (✓ MOV / ✓ CPY / ✓ DEL / ✗ ERR / DRY markers per row)
- Added Switch state labels (ON/OFF text updates in real-time)
- Added Folder video counts on status bar (immediate feedback after Browse)
- Added Transaction log with rotation (5 MB cap, `.log` + `.log.old`, batch headers)
- Applied visual polish from Downloads/app.py (CSS, zebra stripes, styled DataTable)
- Updated README quit-key from `q` to `ctrl+q`

## Red-team audit findings — RESOLVED (plan-execute 2026-07-24)

All 8 findings below were resolved by the 2026-07-24 plan-execute pass.
See "What was done (plan-execute 2026-07-24)" below for the summary.

1. ~~**CRITICAL: Confirmation dialog before destructive operations**~~ → ConfirmOpModal ships
2. ~~**HIGH: Progress counter during scan/move**~~ → ProgressBar wired
3. ~~**HIGH: Swap Source/Target button**~~ → #swap-paths button + handler
4. ~~**HIGH: Dynamic button labels — "Delete Selected"**~~ → Delete mode removed; dynamic "Delete" labels no longer relevant
5. ~~**MEDIUM: Column sorting**~~ → `s` binding sorts by Saved descending
6. ~~**MEDIUM: Search/filter on results table**~~ → `#filter` Input with case-insensitive substring match
7. ~~**MEDIUM: File path display in results**~~ → `p` binding toggles basename ↔ full path
8. ~~**LOW: Export results to CSV/JSON**~~ → `e` binding exports selected rows to CSV

Finding 9 (LOW: theme toggle) remains deferred — see "What is NOT done" below.

## Known issues — RESOLVED (plan-execute 2026-07-24)

- ~~`busy = reactive(False)` should be `var()`~~ → `busy = var(False)` (C-2)
- ~~Inline CSS (80+ lines) should be external `.tcss` file~~ → `app.tcss` + `CSS_PATH` (C-3)
- ~~Workers missing `exit_on_error=False`~~ → all `@work` carry `exit_on_error=False` (C-2)
- ~~Comparison logic trapped in `@work` method~~ → extracted to `core.py` (C-1)

## Key files

- `D:\.code\Keep-Smaller-Copy\app.py` — the TUI (all changes this session)
- `D:\.code\Keep-Smaller-Copy\settings.json` — saved paths/options
- `D:\.code\Keep-Smaller-Copy\keep-smaller-copy.log` — transaction log (new)
- `D:\.code\Keep-Smaller-Copy\docs\refactor-plan-2026-07-24.md` — extraction plan
- `P:\.data\wiki\concepts\textual-tui-best-practices.md` — Textual patterns
- `P:\.data\wiki\concepts\expected-ui-ux-features.md` — tiered UX checklist

## Plan-execute update 2026-07-24

## What was done (plan-execute 2026-07-24)

- ConfirmOpModal before real Move/Copy when dry-run OFF
- ProgressBar during compare + process
- Swap From/To button
- core.py extract + pytest tests/test_core.py
- busy=var(), workers exit_on_error=False
- app.tcss external CSS (main app); FolderBrowser keeps inline CSS
- Sort (s), filter input, path column (p), CSV export (e)
- Delete mode remains removed (no dynamic Delete labels)

## What is NOT done

1. **LOW: In-app theme toggle** (deferred)
2. Optional: DataTable sort by raw bytes (currently sorts displayed size strings)
3. Optional: richer cross-drive move (copy+verify+remove) beyond current WARN path

## Known issues

- Multi-agent: not a git repo — use .snapshots/ per plan Global Constraints
- Theme toggle not shipped
