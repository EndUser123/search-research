---
title: Chrome ACP → Grok Build Setup — Patches and Customizations
slug: chrome-acp-grok-build-setup-implementation
created: 2026-07-30
tags: [chrome-acp, grok, browser-extension, proxy, patches, comet]
summary: >
  Complete patch inventory and re-apply procedures for the Chrome ACP extension,
 proxy server, and supporting files that bridge Comet browser tabs to Grok Build
  via WebSocket + ACP stdio. Includes the IIFE injection structure, patch placement
  rules, CDP debugging notes, and verification steps.
host: grok
agent: grok
cognitive_load: 3
verification: observed
relations:
  - target: wiki/concepts/chromium-cdp-websocket-origin-restriction.md
    type: complements
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related
---

# Chrome ACP → Grok Build — Patches and Customizations

## Status: SHIPPED 2026-07-31 (working directory lock + tool-result collapse added)
host: grok

## Architecture
Chrome ACP extension ([Areo-Joe/chrome-acp](https://github.com/Areo-Joe/chrome-acp)) bridges browser tabs to a local ACP agent via a WebSocket proxy server. The proxy spawns `grok agent stdio` and translates between the extension's WebSocket protocol and ACP JSON-RPC over stdio. See [[chrome-acp-grok-build-browser-driven-agentic-clis]] for the original research and [[mcp-server-sharing-multi-terminal]] for the multi-terminal MCP sharing pattern.

## Files (not in git — npm node_modules + extension dist)
| File | Location |
|------|----------|
| Proxy server | `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\server.js` |
| File utilities | `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\files.js` |
| MCP handler | `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\mcp\handler.js` |
| CLI launcher | `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\cli\command.js` |
| Extension sidepanel | `P:\packages\chrome-acp\dist\sidepanel-t6n74ra3.js` |
| Proxy launcher | `P:\packages\chrome-acp\start-proxy.bat` |
| Patched backups | `P:\packages\chrome-acp\*.patched.js` + `dist\sidepanel-t6n74ra3.patched.js` |

## Proxy server patches (server.js)
| Patch | Description |
|-------|-------------|
| P1-P2 | `extMethod`/`extNotification` handlers — silently ignore Grok's x.ai/* extension methods |
| P3-P6 | Prompt dedup — suppress identical prompts within 400ms (reduced from 3000ms per review) |
| P8 | Cwd normalization — `.trim()` + `.replace(/([A-Za-z]:)$/, "$1/")` on all 3 session handlers |
| P9-P10 | `BROWSER_RULES` module-level constant, injected via `_meta` on newSession, loadSession, AND resumeSession |
| P17 | Session progress messages — "Starting agent..." → "Agent ready..." → "Creating session..." |
| P18 | Action-first rules — instruct agent to act before deliberating, keep thinking brief |
| P-restart (2026-07-30) | `POST /restart-proxy` endpoint — spawns a detached `restart-proxy.js` helper that waits 2s then relaunches `start-proxy.bat`, then exits. Lets the sidepanel "Restart Proxy" button restart the proxy without a terminal. |
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
| P-cwd-flag (2026-07-30) | Hard-coded `WORKSPACE_ROOT = "P:\\"` in command.js instead of `process.cwd()`. The agent process MUST run from `P:\` so native write/read_file tools enforce the correct workspace boundary. A configurable `--cwd` flag was initially proposed but rejected in favor of hard-coding — a flag is a soft constraint that can be forgotten or bypassed if the proxy is launched by the sidepanel or a different script (which is exactly how the bug manifested). With the hard-code, the CWD is correct regardless of how the proxy is started. Patched copy: `command.patched.js`. Re-apply: `re-apply-patches.ps1`. |

## Extension patches (sidepanel-t6n74ra3.js)
All injected via a single fail-safe `try{...}catch(e){}` IIFE at bundle start. If injection fails, React renders normally.

### IIFE structure (critical for patch placement)
```
try{(function(){
  ... CSS injection ...
  safe(function(){ ... WebSocket error listener ... })();
  setInterval(function(){safe(function(){
    /* Feature 0: permission auto-open (BEFORE popover guard) */
    /* Feature 6: working directory lock (BEFORE popover guard — must run on connection screen) */
    /* --- popover guard: if(po)return; --- */
    /* Feature 1: button injection (AFTER guard — needs connected status bar) */
    /* Features 2-5: resize, file search, thinking/tool toggles, tool-call tagging (AFTER guard) */
  })},800);
})();}catch(e){...}
```

**Patch placement rule:** Features that must work on the pre-connection screen go BEFORE `var po=document.querySelector(...)`. Features that need the connected status bar go AFTER the guard.

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
| **Working dir lock (P-wd-lock)** | Locks `#working-dir` input to `P:\`, sets `readOnly=true`, dims field, updates label to "(locked to P:\)". Uses native value setter + `input` event dispatch to bypass React controlled-input anti-pattern. Runs BEFORE popover guard so it works on connection screen. `dataset.acpLocked` guard prevents re-processing. |
| **Restart Proxy button (P-restart-btn)** | Power icon (⏻) button in status bar. Calls `POST /restart-proxy` on the proxy, waits 2.5s, then reloads the extension. Requires the `P-restart` server endpoint. Lets operator restart the proxy without a terminal — picks up code patches (command.js, server.js) without leaving the browser. |
| **Tool-result collapse (P-collapse-tools)** | Caps `.acp-tc` blocks at `max-height:300px` with `overflow-y:auto` and `scrollbar-width:thin`. A maximize icon button in the floating controls toggles `body.acp-expand-tools` which removes the cap globally. State persists in `localStorage("acp_et")`. Three IIFE edits: CSS rule (mirrors `.acp-hide-thinking`), load-time class restore (mirrors thinking init), toggle button (mirrors thinking toggle in Feature 8). Addresses the "sidepanel sludge" problem where large `browser_read`/file-read/shell results rendered in full and dominated the transcript. Agent still receives full tool results — only the rendered view changes. |

### P-wd-lock implementation notes
- **Why:** The agent process is hard-coded to `WORKSPACE_ROOT = "P:\\"` in command.js. The free-form cwd field created a silent mismatch — file browser and agent process could diverge.
- **Why picklist not free-form:** only `P:\` is valid. A picklist with one locked entry is simpler than validation logic and self-documenting. Future expansion: populate from proxy session metadata if multi-workspace support is added.
- **React bypass:** React controlled inputs fight direct `.value` assignment. Use `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set` (the native setter) + `dispatchEvent(new Event("input",{bubbles:true}))` so React's synthetic event system picks up the change.
- **Reload required:** after patching `sidepanel-t6n74ra3.js`, reload the extension via `chrome://extensions` → Reload, or the reload button in the status bar.

## Key lessons learned (for future third-party bundle patches)
1. **Never replace constructors** (WebSocket) — use prototype addEventListener wrappers
2. **Never override theme colors with !important** — causes black screen in dark mode
3. **Wrap all injected code in try/catch** — if injection fails, host bundle still renders
4. **Normalize type coercions at API boundaries** — Chrome tabs.get() needs integers, models send strings
5. **Pause DOM observers during popovers** — mutations trigger Radix outside-click detection
6. **Run pre-connection features before the popover guard** — the `if(po)return;` guard skips everything after it when a dropdown is open, so features that must work on the connection screen (like the working directory lock) must be placed BEFORE the guard
7. **Use native setters for React controlled inputs** — direct `.value` assignment is silently ignored by React's controlled components; use the prototype's native setter + `dispatchEvent(new Event("input",{bubbles:true}))` to update React state from injected code

## Re-apply procedure
1. Extension files are tracked in git at `P:\packages\chrome-acp\` (config files, patched backups, scripts). Large minified bundles (sidepanel.js, index.js, CSS) are gitignored — regenerated by `re-apply-patches.ps1`.
2. The proxy files are NOT in git — they're in `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\`
3. Backups: `P:\packages\chrome-acp\*.patched.js` and `dist\sidepanel-t6n74ra3.patched.js`
4. After patching: `node --check <file>` on all patched JS files
5. After patching: `python P:/packages/chrome-acp/dist/.pytest_cache/../../tmp/acp-verify/test_patched_files.py` (23 tests) — NOTE: test file is in `P:/tmp/`, may need path fix
6. After sidepanel changes: reload extension via `chrome://extensions` → Reload
7. Proxy restart: `P:\packages\chrome-acp\start-proxy.bat` (or kill node + restart)

## CDP debugging (Comet-specific)
- Comet is Perplexity's Chromium 150 browser. Launch via `chrome_proxy.exe` (not `comet.exe` directly — the version directory only has helper exes)
- Chrome 111+ rejects WebSocket CDP connections with Origin headers. Python `websocket-client` must use `suppress_origin=True`. See [[chromium-cdp-websocket-origin-restriction]]
- CDP capture script: `P:/tmp/comet_cdp_console.py` (NOTE: this is in tmp/ — move to `P:/.agents/scripts/` for persistence)
- The debug port is transient — poll immediately after launch and capture within the window

## Verification
- 23 pytest tests (test_patched_files.py): server.js, files.js, sidepanel
- 5/5 files pass `node --check`
- Proxy health endpoint: ok
- Live confirmed: connection, session creation, file browser (207 items), dotfiles visible, model picker stays open
- P-collapse-tools: syntax-verified (`node --check`), patched backup updated, re-apply script updated. **NOT live-verified** — needs extension reload + DevTools confirmation that `.acp-tc` selector matches rendered tool-result blocks.

## What this means for our workspace

The Chrome ACP bridge is the primary interface for browser-driven agentic CLI work on this host. All patches are documented here so a future session can:
1. **Re-apply patches** after an npm update overwrites the proxy server dist files
2. **Add new sidepanel features** using the correct IIFE placement rules (before/after popover guard)
3. **Debug extension errors** using the CDP capture procedure specific to Comet's security restrictions

The [[concurrent-cdp-auth-contention]] invariant applies: only one terminal drives Chrome ACP at a time. The working directory lock ensures the file browser always matches the agent process root (`P:\`).

## Falsifier

This entry is wrong or obsolete if:
- The chrome-acp project adds native support for custom workspace roots, making P-cwd-flag and P-wd-lock unnecessary
- The extension moves to a different bundler that changes the IIFE injection point
- Grok Build adds a native browser integration that replaces the ACP bridge entirely
- Comet enables remote debugging natively, making the CDP capture procedure obsolete
