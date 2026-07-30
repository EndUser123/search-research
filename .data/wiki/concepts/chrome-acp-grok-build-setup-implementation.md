# Chrome ACP → Grok Build — Patches and Customizations

## Status: SHIPPED 2026-07-30 (revised after live testing)
host: grok

## Architecture
Chrome ACP extension (Areo-Joe/chrome-acp) bridges browser tabs to a local ACP agent via a WebSocket proxy server. The proxy spawns `grok agent stdio` and translates between the extension's WebSocket protocol and ACP JSON-RPC over stdio.

## Files (not in git — npm node_modules + extension dist)
| File | Location |
|------|----------|
| Proxy server | `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\server.js` |
| File utilities | `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\files.js` |
| MCP handler | `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\mcp\handler.js` |
| CLI launcher | `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\cli\command.js` |
| Extension sidepanel | `C:\Users\brsth\chrome-acp\dist\sidepanel-t6n74ra3.js` |
| Proxy launcher | `C:\Users\brsth\chrome-acp\start-proxy.bat` |
| Backup dir | `C:\Users\brsth\chrome-acp\*.patched.js` |

## Proxy server patches (server.js)
| Patch | Description |
|-------|-------------|
| P1-P2 | `extMethod`/`extNotification` handlers — silently ignore Grok's x.ai/* extension methods |
| P3-P6 | Prompt dedup — suppress identical prompts within 400ms (reduced from 3000ms per review) |
| P8 | Cwd normalization — `.trim()` + `.replace(/([A-Za-z]:)$/, "$1/")` on all 3 session handlers |
| P9-P10 | `BROWSER_RULES` module-level constant, injected via `_meta` on newSession, loadSession, AND resumeSession |
| P17 | Session progress messages — "Starting agent..." → "Agent ready..." → "Creating session..." |
| P18 | Action-first rules — instruct agent to act before deliberating, keep thinking brief |
| P11 (reverted) | Persistent process — 4 blocking bugs, reverted. See handoff for proper rewrite |

## File utilities patches (files.js)
| Patch | Description |
|-------|-------------|
| P12 | statSync→lstatSync fallback — try statSync (correct type/size), fall back to lstatSync for broken junctions |
| P13 | IGNORED_NAMES — added System Volume Information, $RECYCLE.BIN, $WinREAgent |
| P14 | WATCHER_IGNORE_PATTERNS — bare-directory patterns for Windows system dirs |
| P15 | Removed blanket dotfile filter — .agents, .data, .grok etc. now visible |

## MCP handler patches (handler.js)
| Patch | Description |
|-------|-------------|
| P-tabId | `parseInt(args.tabId, 10)` — coerces string tab IDs to integers (MiniMax-M3 sends strings) |

## CLI launcher patches (command.js)
| Patch | Description |
|-------|-------------|
| P-cwd | `process.cwd().replace(/\//g, "\\")` — normalizes forward slashes to backslashes for consistent Grok session directory encoding |
| P-cwd-flag (2026-07-30) | Added `--cwd` CLI flag so the agent workspace can be pinned regardless of how the proxy was launched. Without this, a proxy started from `C:\Users\brsth\chrome-acp` (e.g., by the sidepanel) sets the agent CWD there, putting `P:\` outside the native tool workspace boundary — causing silent write failures and empty read_file returns for all `P:\` paths. Fix: `(flags.cwd \|\| process.cwd())` in command.js, `--cwd "P:\"` in start-proxy.bat. Patched copy: `command.patched.js`. Re-apply: `re-apply-patches.ps1`. |

## Extension patches (sidepanel-t6n74ra3.js)
All injected via a single fail-safe `try{...}catch(e){}` IIFE at bundle start. If injection fails, React renders normally.

| Feature | Description |
|---------|-------------|
| Echo dedup | `q.content===I\|\|q.content.includes(I)` — handles full and chunked echoes |
| localStorage persistence | Save/load `{proxyUrl, cwd, token}` with try/catch. Cwd normalized on save. |
| Session progress display | Reads `self.__acpStatus` for dynamic spinner text |
| Resize handle | Drag to resize sidebar, width persists in localStorage |
| File search | Filter input at top of file list |
| Reload button | `chrome.runtime.reload()` in header |
| Tool-call toggle | Wrench button to show/hide tool entries |
| Thinking toggle | Brain button to show/hide reasoning text |
| Permission auto-open | Auto-expands collapsible when permission needed |
| Error toast | Passive `addEventListener` wrapper for proxy errors |
| Popover guard | DOM observer pauses when dropdown is open (prevents closing) |
| Theme-safe CSS | No color overrides — only structural CSS, inherits extension theme |

## Key lessons learned (for future third-party bundle patches)
1. **Never replace constructors** (WebSocket) — use prototype addEventListener wrappers
2. **Never override theme colors with !important** — causes black screen in dark mode
3. **Wrap all injected code in try/catch** — if injection fails, host bundle still renders
4. **Normalize type coercions at API boundaries** — Chrome tabs.get() needs integers, models send strings
5. **Pause DOM observers during popovers** — mutations trigger Radix outside-click detection

## Verification
- 19 pytest tests (test_patched_files.py): server.js, files.js, sidepanel
- 5/5 files pass `node --check`
- Proxy health endpoint: ok
- Live confirmed: connection, session creation, file browser (207 items), dotfiles visible, model picker stays open
