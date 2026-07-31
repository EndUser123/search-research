---
title: Chromium CDP WebSocket Origin Restriction and Python Client Fix
slug: chromium-cdp-websocket-origin-restriction
created: 2026-07-31
source: session-20260730
tags: [cdp, chrome, debugging, comet, websocket, security, python]
summary: >
  Chrome 111+ rejects WebSocket DevTools connections that send an Origin
  header, requiring either `--remote-allow-origins=*` at browser launch or
  `suppress_origin=True` on the Python websocket-client side. Node.js CDP
  libraries work because they don't send Origin headers. This caused a
  multi-restart debugging loop on Comet (Perplexity's Chromium) before the
  fix was identified.
host: grok
agent: grok
cognitive_load: 2
verification: multi-source-verified
sources:
  - "https://developer.chrome.com/blog/remote-debugging-port (Chrome for Developers, March 2025)"
  - "https://github.com/hanzili/comet-mcp (GitHub, 2026)"
  - "Session 019fb5cc (2026-07-30): 403 Forbidden on all CDP WebSocket targets"
relations:
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related
  - target: wiki/concepts/chrome-acp-grok-build-setup-implementation.md
    type: complements
---

# Chromium CDP WebSocket Origin Restriction and Python Client Fix

## Decision context

**The problem:** We needed to read the Chrome ACP extension's console errors
from Comet (Perplexity's Chromium 150 browser) to diagnose why the extension
was failing after a proxy restart. The CDP HTTP API (`/json`, `/json/version`)
worked fine — we could list all 56 targets. But every WebSocket connection
attempt returned `403 Forbidden` with the message: *"Rejected an incoming
WebSocket connection from the http://127.0.0.1:9222 origin. Use the command
line flag --remote-allow-origins=http://127.0.0.1:9222 to allow connections
from this origin or --remote-allow-origins=* to allow all origins."*

This caused a costly debugging loop: 4+ browser restarts trying to find the
right launch flags, when the real fix was on the **client side**, not the
browser side. Related: [[concurrent-cdp-auth-contention]] (CDP session
contention between terminals) and [[chrome-acp-grok-build-setup-implementation]]
(the ACP proxy setup this debugging session was diagnosing).

## The two-layer restriction

### Layer 1: Chrome 111+ WebSocket origin check (the 403)

Starting with Chrome 111 (2023), Chromium rejects WebSocket DevTools Protocol
connections that include an `Origin` HTTP header. This is a security measure
to prevent malicious web pages from connecting to a local CDP port. The HTTP
API endpoints (`/json`, `/json/version`, `/json/list`) remain accessible
without origin checks — only the WebSocket upgrade is blocked.

**Why Node.js CDP libraries work:** libraries like `chrome-remote-interface`
(used by `comet-mcp`) connect via raw TCP WebSocket without setting an
`Origin` header. Chrome only rejects connections that *have* an Origin. This
is why the `comet-mcp` project works with just `--remote-debugging-port=9222`
and no `--remote-allow-origins` flag — it's not that Node.js bypasses the
check; it never triggers it.

**Why Python `websocket-client` fails:** the `websocket-client` library
(`import websocket`) automatically sets `Origin: http://127.0.0.1:<port>` on
every connection. This triggers Chrome's rejection. The fix is:

```python
ws = websocket.create_connection(ws_url, timeout=5, suppress_origin=True)
```

`suppress_origin=True` omits the `Origin` header entirely, matching the
Node.js behavior.

**Setting `origin=""` does NOT work** — Chrome still sees an Origin header
(just empty) and rejects it with a slightly different message.

### Layer 2: Chrome 136+ user-data-dir requirement (separate issue)

From Chrome 136 (March 2025), `--remote-debugging-port` and
`--remote-debugging-pipe` are ignored when using the **default** user data
directory. The `--user-data-dir` flag must point to a non-standard directory.
This is a separate security measure against cookie theft via remote debugging.

**Impact on Comet:** Comet's `chrome_proxy.exe` launcher does NOT strip the
`--remote-debugging-port` flag (as initially suspected). The flag works — but
the debug port is **transient**, dying within seconds of browser startup. The
reliable pattern is: launch with the flag, poll for the HTTP endpoint every
500ms, and capture within the window when the port is alive.

## What this means for our workspace

1. **Use `suppress_origin=True` for any Python CDP WebSocket connection.**
   This is the universal fix. The CDP capture script at
   `P:/tmp/comet_cdp_console.py` has been patched with this fix.

2. **For Comet specifically:** launch via `chrome_proxy.exe` (not `comet.exe`
   directly — the version-specific binary directory only contains helper
   exes). Poll the HTTP endpoint immediately after launch and capture within
   the transient window.

3. **The HTTP API always works** — `/json/list` and `/json/version` are
   available without origin checks. Use them to enumerate targets before
   attempting WebSocket connections.

4. **Alternative to `--remote-allow-origins=*` at the browser:** if you
   control the browser launch, passing `--remote-allow-origins=*` allows all
   origins. But this requires the flag to survive the launch chain, and
   Comet's `chrome_proxy.exe` did not reliably pass it through in testing.

5. **Prefer Node.js CDP tools when available.** The `comet-mcp` MCP server
   and the `chrome-remote-interface` npm library both work out of the box
   because they don't send Origin headers. If a Node.js-based tool exists for
   the task, use it instead of fighting Python's WebSocket defaults. The
   `chrome-devtools` MCP server on this host ([[mcp-server-sharing-multi-terminal]])
   also connects via Node.js without origin issues.

## How to capture Comet extension console errors (the working procedure)

```powershell
# 1. Ensure Comet is closed (clean state)
Get-Process comet -ErrorAction SilentlyContinue | Stop-Process -Force

# 2. Remove stale singleton lock
Remove-Item "C:\Users\brsth\AppData\Local\Perplexity\Comet\User Data\SingletonLock" -Force -ErrorAction SilentlyContinue

# 3. Launch via chrome_proxy.exe with debug port
Start-Process "C:\Users\brsth\AppData\Local\Perplexity\Comet\Application\chrome_proxy.exe" `
  -ArgumentList "--remote-debugging-port=9222"

# 4. Poll for CDP availability (transient window — must be fast)
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Milliseconds 500
  try {
    Invoke-WebRequest -Uri "http://127.0.0.1:9222/json/version" -UseBasicParsing -TimeoutSec 1 | Out-Null
    # CDP is up — run capture immediately
    python P:/tmp/comet_cdp_console.py
    break
  } catch {}
}

# 5. The capture script uses suppress_origin=True on all WebSocket connections
#    Open the target extension sidepanel BEFORE running capture for its errors
```

## Falsifier

This entry would be wrong or obsolete if:
- Chrome removes the origin restriction in a future version (unlikely — it's a
  security feature being tightened, not loosened).
- A future `websocket-client` release defaults to `suppress_origin=True` for
  localhost connections (would make the fix unnecessary but not wrong).
- Comet ships an update that enables remote debugging natively or provides a
  debug API (would make the manual launch procedure obsolete).

## Receipts

- **CDP capture script (`P:/tmp/comet_cdp_console.py`):** line 31 uses
  `websocket.create_connection(ws_url, timeout=5, suppress_origin=True)`.
  This was the fix applied after `origin=""` failed with the same 403.
- **`comet-mcp` cdp-client.ts** (GitHub raw,
  `hanzili/comet-mcp/src/cdp-client.ts`): uses `CDP(options)` from
  `chrome-remote-interface` which connects without setting Origin — this is
  the Node.js pattern that works out of the box.
- **Chrome security blog** (developer.chrome.com/blog/remote-debugging-port):
  official source for the Chrome 136 `--user-data-dir` requirement.
- **Session 019fb5cc terminal log** (`call_d58c7b9e26c54a9797a83372`):
  empirical output showing `origin=""` still gets 403, then
  `suppress_origin=True` succeeding on all targets (124 messages captured,
  17 errors/warnings found).
- **Comet binary structure:** `C:\Users\brsth\AppData\Local\Perplexity\Comet\Application\150.0.7871.230\`
  contains only helper exes (elevated_tracing_service, notification_helper,
  etc.), NOT the main browser binary. The root `comet.exe` IS the main binary;
  `chrome_proxy.exe` is the reliable launcher with flag passthrough.

- [Changes to remote debugging switches to improve security](https://developer.chrome.com/blog/remote-debugging-port) (Chrome for Developers, Will Harris, March 2025) — Chrome 136+ user-data-dir requirement for `--remote-debugging-port`.
- [comet-mcp](https://github.com/hanzili/comet-mcp) (GitHub, hanzili, 2026) — Node.js MCP server that connects to Comet via CDP without `--remote-allow-origins`; uses `chrome-remote-interface` which doesn't send Origin headers.
- Session 019fb5cc (2026-07-30) — empirical verification: `origin=""` fails with 403, `suppress_origin=True` succeeds; `comet.exe` direct launch fails, `chrome_proxy.exe` works.
