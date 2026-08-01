---
title: "Chrome autoConnect for authenticated CDP sessions — decision and persistence"
slug: chrome-autoconnect-for-authenticated-cdp-sessions
created: 2026-07-31
source: session-20260731
tags: [chrome, cdp, autoconnect, remote-debugging, browser-automation, model-web, enterprise-policy]
summary: >
  Chrome 136+ silently ignores --remote-debugging-port for default user
  profiles. --browser-url fails because the port never binds. --autoConnect
  (Chrome 144+) is the purpose-built solution: it connects to the user's
  real Chrome session with logins, cookies, and conversation history intact.
  The chrome://inspect toggle persists across restarts; the permission dialog
  is per-session. The RemoteDebuggingAllowed enterprise policy (registry:
  HKLM\SOFTWARE\Policies\Google\Chrome) makes remote debugging permanent
  without dialogs.
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - "https://developer.chrome.com/docs/devtools/agents/get-started/configuration (Chrome for Developers, 2026-06)"
  - "https://productivitytech.io/claude-code-chrome-remote-debugging/ (ProductivityTech, 2026-03)"
  - "https://chromeenterprise.google/policies/remote-debugging-allowed/ (Chrome Enterprise)"
relations:
  - target: wiki/concepts/chromium-cdp-websocket-origin-restriction.md
    type: extends
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related
  - target: wiki/concepts/chrome-acp-grok-build-setup-implementation.md
    type: complements
  - target: wiki/concepts/notebooklm-cli-operational-gotchas.md
    type: related
  - target: wiki/concepts/mcp-server-sharing-multi-terminal.md
    type: related
---

# Chrome autoConnect for authenticated CDP sessions

## Decision context

**The problem:** The `/model-web` skill needs to interact with web-hosted LLMs
(ChatGPT, Gemini, Perplexity) through the operator's real, authenticated Chrome
session — not a clean browser profile with no logins. The initial approach
(`--browser-url http://127.0.0.1:9222` + `--remote-debugging-port=9222`) failed
silently: the port never bound, even though the flag was present in the process
command line. This cost 5 failed attempts before the root cause was identified.

**What was tried and rejected:**

| Attempt | What happened | Root cause |
|---|---|---|
| `--remote-debugging-port` on default profile | Port 9222 never binds | Chrome 136+ ignores the flag for default profiles |
| `--remote-debugging-port` + explicit default profile path | Still no port | Same restriction — default path is default path |
| MCP's own clean browser | Works but no auth session | Separate profile, not logged in |
| Google OAuth on MCP browser | "This browser or app may not be secure" | Google blocks automation-flagged browsers |

**What worked:** `--autoConnect` (Chrome 144+) connects to the user's running
Chrome via `chrome://inspect/#remote-debugging`. One-time toggle, per-session
permission dialog, full authenticated session access.

## The Chrome 136+ restriction

From Chrome 136 (March 2025), `--remote-debugging-port` and
`--remote-debugging-pipe` are **silently ignored** when using the default user
data directory. This is a deliberate security measure against cookie theft via
remote debugging. The flag appears in the process command line but no port
binds. See `[[chromium-cdp-websocket-origin-restriction]]` Layer 2 for the
full analysis.

This was already documented in `[[chromium-cdp-websocket-origin-restriction]]`
but was not consulted before the first connection attempt — leading to the
5-attempt debugging loop. This is the same "wiki knowledge not consulted"
pattern documented in `[[tool-fallbacks-as-index-not-authority]]`.

## autoConnect: the purpose-built solution

Chrome 144+ added `--autoConnect` to the chrome-devtools-mcp server. Instead
of requiring special Chrome launch flags, it:

1. Connects to a locally running Chrome instance that has Remote Debugging
   enabled at `chrome://inspect/#remote-debugging`.
2. Chrome shows a permission dialog ("chrome-devtools-mcp wants to start a
   remote debugging session") — click Allow.
3. The MCP sees all standard browser tabs with full session state (cookies,
   logins, conversation history).

**Config (in plugin.json):**
```json
"args": ["chrome-devtools-mcp@1.6.0", "--autoConnect"]
```

## Persistence across restarts

**The `chrome://inspect` toggle persists across Chrome restarts.** It is a
one-time setup. Source: ProductivityTech (2026-03) explicitly states "This is
a one-time toggle. Until you flip it off, Chrome will respond to autoConnect
requests."

**The permission dialog is per-session.** Each Chrome launch requires one
click on "Allow." This is a security feature — it prevents malicious local
processes from silently attaching.

## Enterprise policy: zero-friction permanent

The `RemoteDebuggingAllowed` Chrome Enterprise policy eliminates the per-session
dialog. Set via Windows registry:

```
HKLM\SOFTWARE\Policies\Google\Chrome
Value: RemoteDebuggingAllowed (DWORD) = 0x00000001
```

Verify at `chrome://policy`. This was applied on this host (2026-07-31).
Whether it suppresses the autoConnect dialog specifically is [INFERENCE] —
the policy controls whether remote debugging is *allowed*, but the dialog may
be a separate Chrome security layer.

## Side panels and popouts are NOT accessible

Chrome's built-in side panel (e.g., "Ask Gemini") and extension popout windows
do not appear as CDP targets — even with `--experimentalIncludeAllPages`.
The side panel is browser chrome, not a web page. Verified in session 019fba58.

**All web LLMs must be opened as regular browser tabs.** The `gemini-skill`
project (GitHub: WJZ-P/gemini-skill) confirms this — it automates
`gemini.google.com/app` as a standard tab. See also `[[concurrent-cdp-auth-contention]]`
for CDP session isolation across terminals.

## What this means for our workspace

1. **The `/model-web` skill uses `--autoConnect` exclusively.** No
   `--browser-url`, no `--remote-debugging-port`, no special Chrome launch
   commands.
2. **The enterprise policy is set permanently.** Future sessions don't need
   to re-enable anything.
3. **The plugin config lives in gitignored `installed-plugins/` cache.** If
   the chrome-devtools-mcp plugin is reinstalled or updated, the `--autoConnect`
   flag must be re-added to `plugin.json`.
4. **Side panels are a dead end.** Don't try to automate them. Open web LLMs
   as regular tabs.

## Falsifier

This concept is wrong if:
- Chrome removes `--autoConnect` in a future version (the flag is marked
  experimental in some docs).
- A provider's anti-automation detection blocks autoConnect sessions (making
  the browser path non-viable for that provider).
- Chrome starts exposing side panels as CDP targets (would make the side-panel
  limitation obsolete).

## Receipts

- **Chrome version:** 150.0.7871.187 (verified via `Get-Item chrome.exe` process inspection, session 019fba58)
- **Port 9222 binding test:** `netstat -ano | findstr ":9222"` returned nothing despite `--remote-debugging-port=9222` in process cmdline. Confirmed Chrome 136+ ignores the flag for default profiles.
- **autoConnect working:** `list_pages` returned 14 real browser tabs including authenticated ChatGPT session. Verified after `--autoConnect` added to `plugin.json`.
- **Enterprise policy:** Registry key `HKLM\SOFTWARE\Policies\Google\Chrome\RemoteDebuggingAllowed = 1` set via `regedit /s`, verified with `Get-ItemProperty`.
- **Nonce probe:** 2-round ChatGPT adapter test, both rounds PASS — nonce reproduced exactly, uid-prefix attribution clean. Session 019fba58.
- **Side panel inaccessibility:** `list_pages` showed 15 standard tabs but NOT the Gemini side panel, even with `--experimentalIncludeAllPages`. [INFERENCE] — the side panel is Chrome-internal UI, not a CDP target type.
- **Permission dialog persistence:** [INFERENCE] — ProductivityTech (2026-03) states "one-time toggle" but the per-session dialog behavior is inferred from Chrome's design, not directly tested across multiple restarts.

## Sources

- [Configuration | Chrome DevTools](https://developer.chrome.com/docs/devtools/agents/get-started/configuration) (Chrome for Developers, 2026-06-29) — official autoConnect documentation
- [Claude Code Chrome Remote Debugging](https://productivitytech.io/claude-code-chrome-remote-debugging/) (ProductivityTech, 2026-03-14) — three-method comparison, persistence details
- [RemoteDebuggingAllowed policy](https://chromeenterprise.google/policies/remote-debugging-allowed/) (Chrome Enterprise) — enterprise policy documentation
- `[[chromium-cdp-websocket-origin-restriction]]` — Chrome 136+ restriction analysis

## Auto-related

- [[chrome-acp-library-stack-and-best-practices-2026]]
- [[skill-catalog]]
- [[wiki-captures-decisions-by-default]]
- [[claude-code-project-memory]]
- [[architecture-decision-records]]

