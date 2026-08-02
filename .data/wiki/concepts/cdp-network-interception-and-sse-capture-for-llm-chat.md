---
title: "CDP Network interception and SSE capture for LLM chat interfaces"
slug: cdp-network-interception-and-sse-capture-for-llm-chat
created: 2026-08-02
source: session-20260802
tags: [cdp, network-interception, sse, llm-chat, model-web, browser-automation, chrome-devtools-mcp, agent-browser, openclaw, browserpilot]
summary: >
  Chrome DevTools MCP has 2 Network tools (list_network_requests, get_network_request)
  but cannot intercept or mock requests (GitHub #848). Modern LLM chat UIs (ChatGPT,
  Gemini) use fetch-based SSE, not native EventSource — so CDP's
  Network.eventSourceMessageReceived never fires. The recommended approach for
  real-time response capture is a window.fetch shim injected via evaluate_script.
  Parallel raw CDP (Fetch domain) alongside the MCP server is viable but heavier.
  Three external tools assessed (OpenClaw relay, BrowserPilot, agent-browser) are
  real but architecturally mismatched for authenticated browser-LLM bridge use.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
sources:
  - "https://github.com/ChromeDevTools/chrome-devtools-mcp/issues/848 (Network interception feature request, open)"
  - "https://alexandrubagu.github.io/blog/chrome-devtools-mcp-vs-agent-browser.html (tool comparison, 2026-03)"
  - "https://dev.classmethod.jp/en/articles/codex-app-cdp-chatgpt/ (CDP capture of ChatGPT SSE)"
  - "https://medium.com/@dimakynal/sniffing-sse-traffic-with-nodriver-and-why-cdp-network-will-betray-you-1c766b420e4d (SSE interception techniques)"
  - "https://chromedevtools.github.io/devtools-protocol/tot/Network/ (CDP Network domain spec)"
  - "GitHub API verification of openclaw/openclaw (384,939 stars), vercel-labs/agent-browser (39,759 stars), ai-naymul/BrowserPilot (~170 stars)"
relations:
  - target: wiki/concepts/browser-automation-failure-modes-llm-chat.md
    type: extends
  - target: wiki/concepts/chrome-autoconnect-for-authenticated-cdp-sessions.md
    type: complements
  - target: wiki/concepts/parallel-cdp-mcp-servers-openchrome.md
    type: related
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related
  - target: wiki/concepts/multi-llm-aggregator-landscape.md
    type: related
---

# CDP Network interception and SSE capture for LLM chat interfaces

## Decision context

**The problem:** the `/model-web` skill extracts LLM responses by DOM scraping
(take_snapshot → find newest assistant message → verify nonce). This is fragile —
UI redesigns, streaming partial responses, and rate-limit walls all break
extraction. The question: can CDP's Network domain give us cleaner response
capture at the API level, bypassing DOM scraping entirely?

**Secondary question:** a Perplexity research result proposed three external
tools (OpenClaw browser relay, BrowserPilot, agent-browser) as CDP enablers
for agentic CLIs. Are any of them useful for our stack?

## What we found

### 1. chrome-devtools-mcp Network tools — observation only, no interception

The MCP server exposes exactly 2 Network tools:

| Tool | What it does | Limitation |
|---|---|---|
| `list_network_requests` | Lists requests since last navigation; filter by `resourceTypes: ["Fetch", "XHR", "EventSource", "WebSocket"]` | Metadata only — URL, status, type, size, timing |
| `get_network_request(requestId)` | Returns full request + response body (inline or to `.network-response` file) | Wraps `Network.getResponseBody` — blocks until stream closes |

**No interception capability.** GitHub issue #848 (open since Jan 2026) requests
network request interception and URL replacement. The feature has not been
shipped. No `Fetch.enable` / `Fetch.requestPaused` access through MCP.

Source: GitHub issue #848, chrome-devtools-mcp tool reference docs.

### 2. The SSE trap: fetch-based streaming breaks CDP's SSE event

Modern LLM chat UIs (ChatGPT, Gemini, Claude) stream responses via **fetch-based
SSE** (`fetch()` + `response.body.getReader()` with `text/event-stream` MIME),
NOT the native `EventSource` API.

This matters because CDP's `Network.eventSourceMessageReceived` event — the
ideal per-message SSE capture — **only fires for native `EventSource` connections**.
For fetch-based SSE, it never fires. Confirmed in Chromium issue 40659493.

Available alternatives:
- `Network.getResponseBody` — works but blocks until the entire stream closes
  (10-60s for typical LLM responses). Loses all streaming benefit.
- `Network.dataReceived` — fires for raw chunks but doesn't respect SSE framing.
  Requires manual buffering and parsing. Higher overhead, lower reliability.
- `Fetch.enable` + `Fetch.requestPaused` — can intercept and stream, but this
  domain is NOT exposed through chrome-devtools-mcp. Would require parallel raw
  CDP session.

Source: classmethod.jp walkthrough of Codex App's CDP capture of ChatGPT;
Medium article on SSE interception with nodriver; CDP protocol spec.

### 3. Recommended approach: JS window.fetch shim via evaluate_script

**The only method that captures real-time fetch-based SSE AND stays inside the
MCP boundary.** Inject a shim that patches `window.fetch` early, uses
`response.body.tee()` to fork the stream, parses SSE frames, and exposes data
on `window.__sseCapture` for polling.

```javascript
// Inject via evaluate_script before sending the prompt
const originalFetch = window.fetch;
window.__sseChunks = [];
window.fetch = async function(...args) {
  const response = await originalFetch.apply(this, args);
  if (response.headers.get('content-type')?.includes('text/event-stream')) {
    const [body1, body2] = response.body.tee();
    // Return body1 to the page (transparent)
    // Read body2 for our capture
    (async () => {
      const reader = body2.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        window.__sseChunks.push(decoder.decode(value));
      }
    })();
    return new Response(body1, {
      headers: response.headers,
      status: response.status,
      statusText: response.statusText
    });
  }
  return response;
};
```

After sending the prompt, poll `window.__sseChunks` to read the streaming
response incrementally.

**Caveat:** SPA navigations (navigating to `newChatUrl`) require re-injection.
The shim must be re-injected after each navigation. This is a 1-call addition
to the existing protocol.

Source: Medium article on SSE interception; dev.to MV3 extension guide;
recommended by the nodriver/zendriver documentation.

### 4. Parallel raw CDP alongside MCP — viable but heavier

The MCP server connects to Chrome via CDP. A second CDP client (Python websockets,
nodriver, Selenium 4) can attach to the same browser via the debug port.
Multiple CDP sessions per browser are allowed; per-page sessions are independent.

This unlocks the full CDP Fetch domain (request interception, response
streaming) but adds infrastructure complexity. **Defer until the JS-shim path
proves insufficient.**

Source: chrome-devtools-mcp troubleshooting docs; CDP spec.

### 5. External tools assessed — real but architecturally mismatched

| Tool | Exists? | Stars | Architecture | Match for our use case? |
|---|---|---|---|---|
| **OpenClaw** (`openclaw/openclaw`) | ✅ Verified | 384,939 | Personal AI assistant runtime; browser relay is one of 25+ channels | ❌ Its relay (port 18792) is designed for OpenClaw's own agent, not external CLIs. Adds a dependency layer without solving our pain points. |
| **BrowserPilot** (`ai-naymul/BrowserPilot`) | ✅ Verified | ~170 | Vision-first scraper (Gemini + Patchright/Playwright fork) | ❌ Complete alternative product, not a building block. Launches own browser. No authenticated session reuse. |
| **agent-browser** (`vercel-labs/agent-browser`) | ✅ Verified | 39,759 | Rust CLI, Playwright-based, Chrome for Testing | ❌ Launches own browser. Has network interception + mocking but can't connect to our authenticated Chrome. Architecture mismatch. |
| **OpenClaw Browser Relay** (`audichuang/openclaw-chrome-extension`) | ✅ Verified | 1 | Chrome extension, CDP relay on port 18792 | ❌ Community fork (1 star). Official OpenClaw extension exists separately. Adds relay layer to what we already do directly. |

**Key finding:** all three tools Perplexity recommended are REAL (not hallucinated).
Perplexity's descriptions were substantially correct. But none of them match our
use case (connect to the operator's authenticated Chrome session from a
multi-terminal agentic CLI fleet). Our existing chrome-devtools-mcp +
`--autoConnect` + `--experimentalPageIdRouting` stack is more purpose-built
than any alternative.

**OpenClaw wiki correction:** the wiki concept
`ai-thought-partner-landscape-and-tp-improvements-2026.md` states OpenClaw has
"280K GitHub stars." The actual count (verified 2026-08-02 via GitHub API) is
**384,939**. The 280K figure is stale (from ~April 2026), not hallucinated.
The "self-hosted AI agent workforce" framing is correct.

## What this means for our workspace

1. **The JS fetch-shim approach is the highest-ROI enhancement for /model-web.**
   It provides real-time SSE response capture (the fragile step in our current
   protocol) using a tool we already have (`evaluate_script`). No new
   dependencies. Stays inside the MCP boundary. Must be re-injected after
   navigation.

2. **`list_network_requests` should be added as a post-hoc verification step.**
   After each prompt submission, filter for `Fetch`/`XHR` resource types to
   verify the conversation API was called with status 200. This catches silent
   submit failures (where the framework sent empty state) at the network level,
   complementing the existing DOM-level Step 3.5 verification.

3. **Do not adopt OpenClaw, BrowserPilot, or agent-browser.** All are real,
   well-maintained projects. None match our architecture. Our stack is more
   purpose-built for the authenticated browser-LLM bridge use case.

4. **Defer parallel raw CDP.** If the JS-shim approach proves insufficient for
   edge cases (e.g., sites that override `window.fetch` after injection), a
   parallel CDP session with Fetch domain is the escalation path. This is
   viable but adds infrastructure complexity.

5. **Update the wiki's OpenClaw star count** from 280K to ~385K (or add a
   `last-verified: 2026-08-02` date).

## Falsifier

This concept is wrong if:
- Chrome DevTools MCP ships native network interception (making the JS shim
  unnecessary). Track GitHub issue #848.
- ChatGPT/Gemini migrate to native `EventSource` (making
  `Network.eventSourceMessageReceived` viable). Unlikely — fetch-based SSE
  is the industry trend for POST-based streaming.
- A provider's anti-automation measures detect the `window.fetch` override
  (treating it as a bot signal). Not currently observed but worth monitoring.
- agent-browser or OpenClaw add `connectOverCDP()` support to attach to
  existing Chrome sessions (changing the architecture-match verdict).

## Receipts

- **GitHub issue #848:** open feature request for network interception in
  chrome-devtools-mcp. Confirms the capability gap.
- **classmethod.jp walkthrough:** reproduces CDP capture of ChatGPT's fetch-based
  SSE stream. Shows `text/event-stream` from `/backend-api/f/conversation`.
- **Medium (nodriver writeup):** explicitly recommends JS fetch-shim over CDP
  Network events for fetch-based SSE. Documents why
  `eventSourceMessageReceived` doesn't fire.
- **GitHub API:** `openclaw/openclaw` = 384,939 stars; `vercel-labs/agent-browser`
  = 39,759 stars; `ai-naymul/BrowserPilot` = ~170 stars. All verified 2026-08-02.
- **Blog comparison:** alexandrubagu.github.io compares chrome-devtools-mcp vs
  agent-browser. Confirms agent-browser has network mocking but is
  Playwright-based (own browser).
- **Chrome DevTools Protocol spec:** Network domain and Fetch domain documentation.

## Sources

- [Network Request Interception #848](https://github.com/ChromeDevTools/chrome-devtools-mcp/issues/848) — chrome-devtools-mcp, open feature request
- [Chrome DevTools MCP vs agent-browser](https://alexandrubagu.github.io/blog/chrome-devtools-mcp-vs-agent-browser.html) — tool comparison (2026-03)
- [CDP capture of ChatGPT SSE](https://dev.classmethod.jp/en/articles/codex-app-cdp-chatgpt/) — classmethod.jp, Codex App implementation walkthrough
- [Sniffing SSE traffic with nodriver](https://medium.com/@dimakynal/sniffing-sse-traffic-with-nodriver-and-why-cdp-network-will-betray-you-1c766b420e4d) — SSE interception technique analysis
- [Chrome DevTools Protocol spec](https://chromedevtools.github.io/devtools-protocol/tot/Network/) — Network domain reference
- [Intercept SSE in Chrome Extensions MV3](https://dev.to/wilow445/how-to-intercept-server-sent-events-in-chrome-extensions-mv3-guide-23kb) — extension-based SSE interception

## Auto-related

- [[browser-automation-failure-modes-llm-chat]] — the DOM-level failure modes this concept's JS-shim approach addresses at the network level
- [[chrome-autoconnect-for-authenticated-cdp-sessions]] — the connection layer this concept builds on
- [[parallel-cdp-mcp-servers-openchrome]] — parallel browser sessions (alternative to single-tab sequential)
- [[concurrent-cdp-auth-contention]] — multi-terminal invariant all CDP tooling must respect
- [[multi-llm-aggregator-landscape]] — broader landscape of multi-LLM tools
