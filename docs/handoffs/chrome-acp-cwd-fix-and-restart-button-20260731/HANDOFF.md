---
thread_id: chrome-acp-cwd-fix-and-restart-button-20260730
parent_handoff_path: none
current_session_id: 019fb4f0-95a4-7a50-8e76-a498830376d8
current_terminal_id: 019fb4f0
produced_at: 2026-07-31T04:10:00Z
status: open
handoff_type: investigation
accurate_as_of_head: a311303b60fbc813c889b9d39ea7c9d2556a25d6
---

# Chrome ACP: CWD fix, restart button, and the assert-without-investigating behavioral pattern

## Last user message (verbatim)

> "You're right to push back. I was guessing about Chrome's reload behavior. Let me actually investigate instead of asserting." we must kill this behavior.

## Objective

Two intertwined items:

1. **Chrome ACP patches (infrastructure):** CWD hard-code in command.js (fixes vanishing writes + empty read_file), `/restart-proxy` endpoint + sidepanel button (restart proxy from browser), proxy-down detector banner. Patches are written, syntax-verified, pytest-verified. **Not yet verified live** — proxy has not been restarted to confirm runtime behavior. Buttons not visible to operator after extension reload (unresolved — see Open items).

2. **Behavioral pattern to kill:** The agent asserted "reloading the extension doesn't reload the sidepanel" without testing it. When the operator pushed back ("Are you sure because I don't believe you"), the agent investigated, found the patched code was correctly in the loaded file, and realized it didn't actually know why buttons weren't showing. The operator wants this assert-before-investigate behavior structurally prevented.

## Background

The Chrome ACP proxy (`@chrome-acp/proxy-server`) bridges browser tabs to `grok agent stdio`. A session transcript from the Chrome ACP extension (using M3) revealed vanishing writes, empty read_file, fabricated cancel signals, and quoting failures. Root cause diagnosis: the proxy used `process.cwd()` as the agent's working directory, and when launched from `C:\Users\brsth\chrome-acp` (by the sidepanel), the agent CWD was wrong — putting `P:\` outside the native tool workspace boundary.

## What was shipped this session

### MCP server installs (earlier in session, committed)
- Kinocut (video editing MCP) — installed via `uvx --from kinocut --with "mcp<2" kino`, verified on real video trim operation. Committed `6e50eaa`.
- OpenCV MCP (image analysis) — installed via `uvx --with "mcp<2" opencv-mcp-server`, verified on real image stats + resize. Committed `6e50eaa`.
- Wiki concept `mcp-sdk-2-0-fastmcp-breakage.md` created — MCP SDK 2.0.0 removed `mcp.server.fastmcp`, breaking all 1.x-era servers. Committed `6e50eaa`.

### Chrome ACP patches (later in session, NOT yet committed — files are in npm node_modules)
1. **`command.js`** (P-cwd-flag): Hard-coded `WORKSPACE_ROOT = "P:\\"` instead of `process.cwd()`. This is the core fix — agent process must spawn from `P:\` so native tools enforce the correct workspace boundary.
2. **`server.js`** (P-restart): Added `POST /restart-proxy` endpoint — spawns detached `restart-proxy.js` helper, exits old process, helper relaunches `start-proxy.bat` after 2s delay.
3. **`sidepanel-t6n74ra3.js`** (P-restart-btn): Added power icon (⏻) button in status bar — calls `/restart-proxy`, waits 2.5s, reloads extension. Also added Feature 7: proxy-down detector that polls `/health` and shows red banner with startup instructions when proxy is unreachable.
4. **`restart-proxy.js`**: New helper script — detached spawn that waits 2s then runs `start-proxy.bat`.
5. **`re-apply-patches.ps1`**: Updated to cover all 3 patched files (command.js, server.js, sidepanel).
6. **`start-proxy.bat`**: Reverted to original (no `--cwd` flag needed since command.js hard-codes it).

### Verification
- pytest suite (`P:/tmp/test_chrome_acp_patches.py`): 28/28 passed — unit-behavior tests for all 5 files.
- node --check: all JS files pass syntax validation.
- PowerShell parse: `re-apply-patches.ps1` valid.
- **NOT verified live:** proxy not restarted; CWD fix not confirmed at runtime; restart button not confirmed working; button visibility issue unresolved.

### Wiki updates (committed)
- `chrome-acp-grok-build-setup-implementation.md`: P-cwd-flag, P-restart, P-restart-btn entries added. Committed `f7a4771`.

## Open items

### O1: Buttons not visible after extension reload (UNRESOLVED)
The operator reloaded the extension but doesn't see the injected buttons. The patched JS is confirmed present in the file Chrome loads (`sidepanel-t6n74ra3.js` — only copy, correct content, syntax valid, last modified 2026-07-30 8:43 PM). The proxy is running (health check returns 200 OK). The code structure is intact (Feature 7 runs before the popover guard, Feature 1 button injection runs after — no control-flow breakage detected). 

**What was NOT investigated:** the live DOM state. The button injection searches for spans containing "Connected"/"Disconnected"/"Error" to find the status bar, then looks for a div container with ≥2 children including buttons. If this DOM search fails (status bar not rendered yet, different class names, React not mounted), buttons never get created. The agent could not inspect the live DOM from this session.

**Next step:** Have the Chrome ACP agent (or the operator) open DevTools on the sidepanel, check: (a) does the `__acpUI` flag exist on `self`? (b) are there console errors? (c) what does the status bar DOM look like? (d) does the working-dir lock (Feature 6) work — if yes, injection runs; if no, the whole IIFE fails.

### O2: Proxy not restarted with patched code (NOT DONE)
The running proxy is still the old code (PID 3204, CWD `C:\Users\brsth\chrome-acp`, no `/restart-proxy` endpoint). The CWD fix, restart endpoint, and all patches need a proxy restart to take effect. After restart, verify `proxy.log` shows `CWD: P:\` and have the agent do a write + read_file to `P:\tmp\` to confirm vanishing-write fix.

### O3: Fabricated cancel bug (NOT FIXED — separate issue)
`server.js` lines 486-489 (duplicate-prompt suppression) and 517-525 (disconnect handler) both produce `stopReason: "cancelled"` without the operator clicking cancel. The operator confirmed they didn't cancel — the agent was killed by a disconnect or dedup trigger. This is a trust-integrity bug: command errors are silently relabeled as user cancels. Fix would be in `server.js` — distinguish disconnect/tool-error from genuine cancel. Lower priority than O1/O2.

### O4: The assert-without-investigating behavioral pattern (OPERATOR PRIORITY)
The operator explicitly said "we must kill this behavior" — referring to the agent asserting "reloading the extension doesn't reload the sidepanel" as fact without testing it. When pushed, the agent investigated and found it didn't know the actual cause.

This is a specific instance of [[premature-closure-narrative-sufficiency-external-approaches]] / [[narrative-as-signal-anti-dismissal-rule]], but sharper: the agent asserted a specific platform-behavior claim ("Chrome reloads the service worker but not the sidepanel") from training-data memory, without any tool call to verify. The existing wiki concepts cover "plausible narratives closing the loop" — but the specific failure mode is **asserting runtime/platform behavior from memory instead of testing it.**

**Candidate wiki concept:** `asserting-runtime-behavior-from-memory-not-testing` — the pattern where the agent states "X works this way" about browser/platform/CLI behavior from training data rather than from a verification receipt. The fix is structural: any claim about how a tool/platform/runtime behaves must either be backed by a test in the current session or labeled `[INFERENCE]` / `[UNKNOWN]`.

**What's needed next session:**
1. Promote the behavioral pattern to a wiki concept (or extend an existing one)
2. Consider whether a hook/gate could catch this (claims about runtime behavior without a tool-call receipt)
3. The operator's quote is the acceptance criteria: the agent should investigate before asserting, every time

## Related wiki concepts

- `chrome-acp-grok-build-setup-implementation.md` — patch registry (P-cwd-flag, P-restart, P-restart-btn)
- `chrome-acp-grok-build-browser-driven-agentic-clis.md` — original architecture research
- `mcp-servers-for-polishing-code-words-images-video.md` — MCP server install decisions
- `mcp-sdk-2-0-fastmcp-breakage.md` — MCP SDK 2.0 breakage pattern
- `premature-closure-narrative-sufficiency-external-approaches.md` — parent pattern for O4

## Key files (read-first)

- `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\cli\command.js` — WORKSPACE_ROOT hard-code
- `C:\Users\brsth\AppData\Roaming\npm\node_modules\@chrome-acp\proxy-server\dist\server.js` — /restart-proxy endpoint
- `C:\Users\brsth\chrome-acp\dist\sidepanel-t6n74ra3.js` — button injection + proxy-down detector
- `C:\Users\brsth\chrome-acp\restart-proxy.js` — detached spawn helper
- `C:\Users\brsth\chrome-acp\re-apply-patches.ps1` — re-apply script
- `P:/tmp/test_chrome_acp_patches.py` — pytest verification suite
- `P:/.data/wiki/concepts/chrome-acp-grok-build-setup-implementation.md` — patch registry

## Falsifier

If the CWD fix doesn't resolve the vanishing-write issue (i.e., writes still vanish after proxy restart with `WORKSPACE_ROOT = "P:\\"`), then the workspace-boundary inference is wrong and the root cause is elsewhere (possibly a Grok Build tool-layer bug, not a CWD-boundary issue). The live test after restart (write to `P:\tmp\` + read back) is the discriminating test.

If buttons don't appear after close-and-reopen of the sidepanel (not just extension reload), then the injection code has a DOM-search bug that needs debugging in DevTools.

## Acceptance criteria

1. Proxy restarted with patched code — `proxy.log` shows `CWD: P:\`
2. Agent can `write` to `P:\tmp\` and `read_file` it back successfully (no vanishing)
3. Sidepanel shows 4 buttons (↻ 🔧 💡 ⏻) in the status bar
4. ⏻ button successfully restarts the proxy (proxy exits + relaunches)
5. Red banner appears when proxy is down, with startup command
6. Behavioral pattern wiki concept written and the pattern is named so future sessions can reference it
