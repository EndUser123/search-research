---
title: "Textual + Python TUI pitfall checklist: predictable bugs to head off"
created: 2026-07-28
source: session-019fa94d (/www research after KSC bugs)
sources:
  - https://textual.textualize.io/guide/workers/
  - https://textual.textualize.io/guide/screens/
  - https://textual.textualize.io/api/screen/
  - https://docs.python.org/3/library/shutil.html
  - https://alexwlchan.net/2019/atomic-cross-filesystem-moves-in-python/
tags: [textual, python, pitfall, checklist, thread-safety, modal, shutil, ffprobe, io-safety]
host: both
agent: grok
verification: multi-source-verified
cognitive_load: 3
summary: >
  Checklist of predictable bugs in Textual TUI apps on Python 3.14,
  categorized by subsystem. Each entry maps to a real bug found in
  Keep-Smaller-Copy (session 019fa94d). Use this as a pre-flight review
  checklist before shipping any Textual app.
---

# Textual + Python TUI pitfall checklist

## How to use this

Before shipping a Textual TUI app, scan each section against your code.
Every item below maps to a real bug found in Keep-Smaller-Copy.

---

## 1. Workers / threading (the #1 source of bugs)

| # | Pitfall | What happens | Fix |
|---|---------|-------------|-----|
| W1 | **`query_one` from thread worker** | Worker calls `self.query_one("#x")` directly — Textual is single-threaded for UI | Capture widget values on UI thread; pass as args to worker |
| W2 | **Worker doesn't set `busy`** | No spinner, Stop disabled, user can trigger overlapping workers | Set `self.busy = True` at start; `False` in `finally` via `call_from_thread` |
| W3 | **`exclusive=True` doesn't actually cancel** | Textual cancels the worker object but the thread keeps running — stale results overwrite new ones | Use a generation counter; check before writing results |
| W4 | **No `exit_on_error=False`** | Worker exception crashes the entire app | Add `exit_on_error=False` to `@work` |
| W5 | **Shared state mutated during worker** | UI thread clears `_candidates` while worker iterates it → IndexError | Snapshot data before starting worker |

**Golden rule:** From `@work(thread=True)`, use `call_from_thread` for ALL UI access — including `query_one`, reactive var sets, and widget property reads.

## 2. ModalScreen / dismiss

| # | Pitfall | What happens | Fix |
|---|---------|-------------|-----|
| M1 | **Double dismiss → ScreenStackError** | Esc pressed twice; or binding fires after modal already closed | Wrap `self.dismiss()` in try/except `ScreenStackError` |
| M2 | **Esc binding on app leaks into modal** | App-level `("escape", "reset")` fires while FolderBrowser is open | Use `ModalScreen` (blocks app bindings) or check `self.screen_stack` depth |
| M3 | **dismiss(None) vs dismiss(False)** | Caller treats `None` and `False` differently — Cancel returns `None`, Confirm returns `True`/`False` | Be explicit: always dismiss with a typed value; caller checks for `None` separately |

## 3. Reactive vars / state

| # | Pitfall | What happens | Fix |
|---|---------|-------------|-----|
| R1 | **Manual state calls duplicate the watcher** | Code sets `button.disabled = True` AND `watch_busy` also sets it — two owners | Pick one: either reactive watcher OR manual calls, never both |
| R2 | **`watch_*` fires before `on_mount`** | Setting reactive in `__init__` triggers watcher before widgets exist | Use `set_reactive()` in constructor; or defer to `on_mount` |
| R3 | **Mutable collection mutation not detected** | `self.list.append(x)` doesn't trigger watchers | Use `self.mutate_reactive()` after mutation, or reassign `self.list = new_list` |

## 4. File I/O (the #2 source of bugs)

| # | Pitfall | What happens | Fix |
|---|---------|-------------|-----|
| F1 | **Delete before copy** | `os.remove(old)` then `shutil.copy2(new)` — if copy fails, data is LOST | Copy to temp → verify → `os.replace` → then remove old |
| F2 | **Non-atomic write** | `open(path, 'w')` crashes mid-write → corrupt file | Write to temp + `os.replace` (same directory = same volume = atomic) |
| F3 | **`shutil.move` cross-volume silently copies** | Not atomic across drives; crash leaves partial file at destination + deleted source | Check `st_dev`; copy+replace+unlink manually for cross-volume |
| F4 | **Windows file locking** | File open in another app → `shutil.move` copies but can't delete source → silent duplicate | Catch `WinError 32`; warn user |
| F5 | **Orphan temp file on copy failure** | Chunked copy raises mid-file → `.tmp` left behind; outer except doesn't know the tmp path | Clean up tmp in the exception handler; or use `try/finally` inside the copy function |
| F6 | **Pasted Windows paths include quotes** | Explorer copies `"C:\path"` with surrounding quotes; `os.path.isdir` fails | `.strip('"').strip("'")` at every path read site |

## 5. ffprobe / subprocess

| # | Pitfall | What happens | Fix |
|---|---------|-------------|-----|
| S1 | **10s timeout per call, no caching** | 100 candidates × 2 calls × 10s = 33 min worst case | Cache results; parallelize; or skip duration matching for large sets |
| S2 | **ffprobe not installed** | `get_duration` silently returns `None` → duration column shows "n/a" | Check at startup (already done in KSC); warn in UI |

## 6. DataTable

| # | Pitfall | What happens | Fix |
|---|---------|-------------|-----|
| D1 | **Sort by formatted string** | `table.sort("saved")` sorts "1.5 GB" < "500 MB" lexicographically | Sort raw values in Python; rebuild table |
| D2 | **Filter clears selection** | `table.clear()` + `selected_rows = set()` loses user's deselections | Preserve marks per-candidate; only hide rows |
| D3 | **Sort lost after filter** | `_filter_changed` rebuilds table without re-applying sort | Track sort state; re-apply after rebuild |

## 7. Settings / persistence

| # | Pitfall | What happens | Fix |
|---|---------|-------------|-----|
| P1 | **Tests clobber real settings** | Test calls `_save_current_settings` → overwrites user's config with temp paths | `conftest.py` monkeypatches `CONFIG_FILE` |
| P2 | **Non-atomic settings write** | Crash during `json.dump` → corrupt `settings.json` → silent loss of saved paths | Atomic write: temp + `os.replace` |
| P3 | **Silent corruption recovery** | `json.JSONDecodeError` → return `{}` with no warning | Backup corrupt file before returning empty |
| P4 | **Settings lost on X-button close** | `on_unmount` fires after widgets are dismantled; `query_one` fails silently | Save on `Input.Changed` (every keystroke), not on exit; guard with `_loading` flag during startup restore |
| P5 | **Input.Changed fires during startup** | Restoring saved paths in `on_mount` triggers `Changed` → 30+ saves on launch | `_loading = True` in `__init__`; set `False` at end of `on_mount` |

## 8. Windows-specific

| # | Pitfall | What happens | Fix |
|---|---------|-------------|-----|
| W1 | **Case-sensitive dict keys** | `Video.mp4` and `video.mp4` are different keys on Windows NTFS (case-insensitive FS) | Lowercase basename keys on `sys.platform == "win32"` |
| W2 | **`os.startfile` for opening Explorer** | Works on Windows; needs `open`/`xdg-open` on other platforms | Platform check (already done in KSC) |
| W3 | **Network drive drop** | `os.listdir` raises `OSError` not just `PermissionError` | Catch `OSError` broadly in folder browser |

---

## Quick pre-flight checklist (paste into review)

```
[ ] No query_one from @work(thread=True) — all via call_from_thread or args
[ ] All @work workers set busy=True/False
[ ] exclusive=True workers have generation counter for stale rejection
[ ] @work has exit_on_error=False
[ ] ModalScreen.dismiss wrapped in try/except ScreenStackError
[ ] No os.remove before shutil.copy — use temp + os.replace
[ ] Copy exception handler cleans up .tmp files
[ ] Settings save uses atomic write (temp + os.replace)
[ ] Settings save on Input.Changed (not just on exit)
[ ] _loading flag suppresses Input.Changed during startup restore
[ ] conftest.py isolates CONFIG_FILE and LOG_FILE
[ ] DataTable sort uses raw values not formatted strings
[ ] Filter preserves selection marks
[ ] Case-insensitive basename matching on Windows
[ ] Strip quotes from pasted paths at every read site
[ ] os.walk has onerror handler (silent skip permission-denied dirs)
[ ] FolderBrowser catches OSError (not just PermissionError)
```

## Related concepts

- [[textual-tui-best-practices]] — architecture patterns (workers, reactive, CSS)
- [[io-safety-review-lens]] — review lens for delete-before-copy patterns
- [[tui-testing-strategy-python-textual]] — 4-layer testing stack
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
