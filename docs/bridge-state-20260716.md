# Bridge Implementation State — 2026-07-16

## Committed (in order)

| Commit | Hash | Component | Files |
|--------|------|-----------|-------|
| M4 | `a650fe6` | Lane controller foundation | 24 files |
| ADR-1 | `4b5a641` | identity_token on LaneClaim | 2 files |
| ADR-5 | `fc9b9a0` | Phase state machine + watchdog | 2 files |
| Terminal adapter | `a2b843c` | Win32 API, mutex, completion detector | 5 files |
| Fixes | `6482eeb` | Lane-scoped mutex, MessageStorage API | 2 files |
| Hook + abort | `6209061` | bridge_input_lock UPS hook, bridge-abort.ps1 | 4 files |
| ChromeEndpoint | `8fb5d79` | CDP manager, DOM interaction, daemon loop | 3 files |
| DOM selectors | `75774c8` | ChatGPT DOM selectors v1 config | 1 file |

## Tests

152 tests in `tests/ai_lane_controller/` — all passing.

## File tree

```
tools/ai_lane_controller/
  claim.py          — LaneClaim, identity_token, fencing
  phase.py          — Phase SM (IDLE/WFG/WFC) + watchdog recovery
  messages.py       — lane-message.v1 contract
  storage.py        — MessageStorage (atomic, cursor, events)
  endpoints/
    __init__.py
    win_console_api.py        — Win32 Console API wrappers
    input_mutex.py             — Lane-scoped UIMutex
    completion_detector.py     — Screen buffer polling heuristic
    terminal_adapter.py        — Claude side daemon (Path A interactive)
    chrome_endpoint.py         — ChatGPT side daemon
    chrome_endpoint_cdp.py     — CDP connection manager + circuit breaker
    chrome_endpoint_dom.py     — DOM interaction primitives
    dom_selectors/v1.json      — ChatGPT CSS selectors
    bridge_input_lock_hook.py  — Source copy of UPS hook
  .claude/hooks/UserPromptSubmit_modules/
    bridge_input_lock.py       — Registered UPS hook
    registry.py                — +bridge_input_lock in core_hook_modules
  scripts/
    bridge-abort.ps1           — User abort script
```

## Next workstreams

1. **DOM fixture baseline** — `tests/endpoints/fixtures/*.html` snapshots of ChatGPT DOM states (response, input, streaming, error, empty). Each selector tested against its fixture. Blocked until someone inspects ChatGPT's actual DOM and captures the fixtures.

2. **Daemon lifecycle** — start/stop/restart scripts for both daemons (`chrome_endpoint.py`, `terminal_adapter.py`). Windows scheduled task or PowerShell background job.

3. **End-to-end integration test** — simulated flow that exercises the full cycle without a real browser or terminal (mock CDP, mock screen buffer).

4. **Real activation** — user runs ChromeEndpoint with an actual Chrome instance + chatgpt.com session.

## Known limitations

- CDP connection uses HTTP-JSON shim, not WebSocket. Works for basic eval but won't handle StreamingConsoleAPICalled or push events. Upgrade to `websocket-client` for production.
- DOM selectors are **guesses** based on common ChatGPT patterns — not verified against the actual DOM. First real activation will need selector fixes.
- No daemon lifecycle management (no auto-restart on crash).
- Terminal adapter depends on `WriteConsoleInput` — only works on Windows ConPTY/console, not SSH or tmux.
