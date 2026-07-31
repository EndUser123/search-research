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
    /* Feature 8: HEADER control buttons next to theme toggle (BEFORE guard — always visible incl. pre-connection) */
    /* --- popover guard: if(po)return; --- */
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
| Permission auto-open | Auto-expands collapsible when permission needed |
| Error toast | Passive `addEventListener` wrapper for proxy errors |
| Popover guard | DOM observer pauses when dropdown is open (prevents closing) |
| Theme-safe CSS | No color overrides — only structural CSS, inherits extension theme |
| **Working dir lock (P-wd-lock)** | Locks `#working-dir` input to `P:\`, sets `readOnly=true`, dims field, updates label to "(locked to P:\)". Uses native value setter + `input` event dispatch to bypass React controlled-input anti-pattern. Runs BEFORE popover guard so it works on connection screen. `dataset.acpLocked` guard prevents re-processing. |
| **Header control buttons (Feature 8, consolidated 2026-07-31)** | 5 buttons (Reload extension, Restart proxy, Toggle tool calls, Toggle thinking, Expand tool results) injected next to the **theme toggle** in the header. Anchor: iterates `button[data-slot="dropdown-menu-trigger"]` and matches the one whose `span.sr-only` text contains "Toggle theme" — NOT a querySelector first-match (which grabbed the wrong dropdown trigger, e.g. model picker, on the disconnected screen — the root cause of the prior "buttons don't appear" bug). Buttons are inserted as siblings of the theme-toggle wrapper in the header flex row, cloning the theme toggle's className for native styling. `dataset.acpCtrl` guard prevents duplicates. Runs BEFORE the popover guard so buttons render on the pre-connection screen too. **Replaces** the old Feature 1 status-bar injector and the broken first-match Feature 8 — single source of truth, no drift. |
| **Tool-result collapse (P-collapse-tools)** | Caps `.acp-tc` blocks at `max-height:300px` with `overflow-y:auto` and `scrollbar-width:thin`. The "Expand tool results" button in the header (Feature 8) toggles `body.acp-expand-tools` which removes the cap globally. State persists in `localStorage("acp_et")`. CSS rule mirrors `.acp-hide-thinking`. Addresses the "sidepanel sludge" problem where large `browser_read`/file-read/shell results rendered in full and dominated the transcript. Agent still receives full tool results — only the rendered view changes. |

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
8. **querySelector first-match is the wrong anchor when multiple dropdown triggers exist** (2026-07-31) — the sidepanel has several `button[data-slot="dropdown-menu-trigger"]` elements (theme toggle, model picker, etc.). A `querySelector(...)` grabs the first in DOM order, which on the disconnected screen was NOT the theme toggle, so injected buttons silently failed to anchor. Fix: iterate `querySelectorAll` and match by discriminative text content ("Toggle theme"). Generalizes: when anchoring into a third-party Radix UI, never assume a single match for a `data-slot` — always filter by visible label.
9. **Consolidate, don't accumulate** (2026-07-31) — the prior session added a second button injector (Feature 8) alongside an existing one (Feature 1) instead of extending it, producing duplicate/diverged buttons. This is the same anti-pattern as parallel prompt injection. One injector, one source of truth; extend it when adding a button.
10. **PowerShell corrupts large non-UTF-8 byte sequences** (2026-07-31) — `[System.IO.File]::ReadAllText` with UTF8 encoding replaces invalid byte sequences in the 13MB minified JS bundle with U+FFFD replacement chars (+35KB). Use Python's `read_bytes()`/`write_bytes()` for any file operation on the sidepanel bundle. This is the Class C escalation tier from AGENTS.md: when PowerShell string handling is unreliable for large files, switch to Python byte-level operations.
11. **Extract the patch, track the patch, ignore the artifact** (2026-07-31) — for third-party bundles you inject into, extract your custom code into a tracked standalone file and have re-apply prepend it. Don't track the 13MB bundle (unreadable diffs) and don't leave the patch untracked (disk-failure loss). The IIFE extraction model gives readable diffs + git recovery + no repo bloat.

## Re-apply procedure
1. Extension files are tracked in git at `P:\packages\chrome-acp\` (config files, patched backups, scripts, **and the extracted IIFE**). Large minified bundles (sidepanel.js, index.js, CSS) are gitignored — the IIFE is extracted to `patches/sidepanel-iife.js` (tracked, ~10KB, readable) and prepended by `re-apply-patches.ps1`.
2. The proxy files are NOT in git — they're in `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\`
3. Tracked patch sources: `P:\packages\chrome-acp\*.patched.js` (proxy files) and `patches\sidepanel-iife.js` + `patches\prepend_iife.py` (sidepanel). The deprecated `dist\sidepanel-t6n74ra3.patched.js` backup is gitignored but kept on disk as a safety net.
4. After patching: `node --check <file>` on all patched JS files
5. After patching: `python P:/tmp/acp-verify/test_patched_files.py` and `test_re_apply_patches.py` (39 tests total)
6. After sidepanel changes: reload extension via `chrome://extensions` → Reload
7. Proxy restart: `P:\packages\chrome-acp\start-proxy.bat` (or kill node + restart)

### Sidepanel IIFE extraction model (2026-07-31)
The sidepanel's custom code is a self-contained IIFE (`try{(function(){...})();}catch(e){...}`) prepended to the 13.6MB third-party minified bundle. The IIFE is extracted to `patches/sidepanel-iife.js` (tracked in git). The re-apply script calls `patches/prepend_iife.py` (Python, byte-level) to strip any existing IIFE and prepend the tracked version — **idempotent and encoding-safe**. PowerShell's `ReadAllText` corrupts non-UTF-8 byte sequences in the minified bundle (+35KB of replacement chars), so the sidepanel operation MUST use the Python helper, not PowerShell string operations. Byte-identical round-trip proven: SHA256 of extract+prepend output matches the source bundle exactly.

## CDP debugging (Comet-specific)
- Comet is Perplexity's Chromium 150 browser. Launch via `chrome_proxy.exe` (not `comet.exe` directly — the version directory only has helper exes)
- Chrome 111+ rejects WebSocket CDP connections with Origin headers. Python `websocket-client` must use `suppress_origin=True`. See [[chromium-cdp-websocket-origin-restriction]]
- CDP capture script: `P:/tmp/comet_cdp_console.py` (NOTE: this is in tmp/ — move to `P:/.agents/scripts/` for persistence)
- The debug port is transient — poll immediately after launch and capture within the window

## Verification
- 24 pytest tests (test_patched_files.py): server.js, files.js, sidepanel — includes `test_button_injection_uses_theme_toggle_anchor` and `test_no_redundant_status_bar_injector`
- 5/5 files pass `node --check`
- All 4 sidepanel copies (live, .patched backup, user-dir, user-dir backup) hash-identical after consolidation
- Proxy health endpoint: ok
- Live confirmed: connection, session creation, file browser (207 items), dotfiles visible, model picker stays open
- P-collapse-tools + Feature 8 header consolidation: syntax-verified (`node --check`), all copies synced, pytest green. **NOT live-verified** — needs extension reload + DevTools confirmation that (a) the 5 buttons appear next to the theme toggle on the disconnected screen, and (b) `.acp-tc` selector matches rendered tool-result blocks.

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
