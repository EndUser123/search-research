---
title: "Reading ChatGPT shared links (and other React Flight SPAs)"
slug: reading-chatgpt-shared-links-js-spa
tags: [web-fetching, scraping, chatgpt, react-flight, tool-selection]
categories: [tool-fallbacks, web-research]
created: 2026-08-10
cognitive_load: 2
host: grok
agent: grok
verification: observed
summary: >
  ChatGPT shared links embed conversation data as React Flight payloads in the
  static HTML body. web_fetch fails because it strips/truncates the script blob,
  not because JS doesn't execute. The optimal tool is ChatPeek (single GET +
  React Flight parser), installed at P:/packages/ChatPeek/. A raw-GET diagnostic
  (one Invoke-WebRequest + grep for content keywords) determines whether any SPA
  needs a browser or just a parser. Browser MCP is the fallback for interactive,
  login-gated, or Cloudflare-challenged paths only.
sources:
  - session 2026-08-10 — Invoke-WebRequest + ChatPeek live test on chatgpt.com/s/t_6a79595...
  - https://github.com/vl3c/ChatPeek — React Flight parser, single-GET design (MIT, accessed 2026-08-10)
  - https://www.npmjs.com/package/chatgpt-share-parser — TS port of ChatPeek
  - https://scrapfly.io/blog/posts/how-to-scrape-chatgpt — Cloudflare + JS rendering context (Scrapfly, 2026-06)
relations:
  - target: wiki/concepts/tool-fallbacks.md
    type: extends
  - target: wiki/concepts/minimal-fix-and-root-cause.md
    type: related
  - target: wiki/concepts/concurrent-cdp-auth-contention.md
    type: related
---

# Reading ChatGPT shared links (and other React Flight SPAs)

## Problem

`web_fetch` (and any markdown-extracting HTTP client) returns a near-empty shell
when pointed at a ChatGPT shared link (`chatgpt.com/s/<id>` or `/share/<id>`).
The conversation text appears absent, so agents reach for a full browser.

## Why `web_fetch` fails — and why a browser is NOT the fix

The conversation data **is in the static HTML body** — serialized as a React
Flight payload inside `window.__reactRouterContext.streamController.enqueue(...)`
calls (a positional-reference format, modern successor to Next.js `__NEXT_DATA__`).

[FACT — `Invoke-WebRequest` to the share URL returned HTTP 200, 489KB, containing
both `reactRouterContext` and the conversation keyword `obligation`. No Cloudflare
challenge. Receipt: session 2026-08-10.]

`web_fetch` fails because its markdown extraction **strips/truncates the `<script>`
blob** holding the serialized payload — not because JS doesn't execute. The data
was served in full to a plain HTTP client. A browser "works" but is a sledgehammer:
it spins up Chrome, captures screenshots/console, and contends for the shared CDP
profile (see [[concurrent-cdp-auth-contention]] — a real host invariant).

Shared links are public-by-design (they carry OG image meta tags for social
preview), so they are served to any HTTP client with a browser UA without a
Cloudflare challenge in normal single-request use.

## Diagnostic: raw GET before tool selection

Before choosing a tool, run **one raw HTTP GET** and grep the body for the
content you need. This single step distinguishes two problems that look identical
but have different optimal solutions:

| Raw GET result | Diagnosis | Optimal tool |
|---|---|---|
| Content keywords present in body (even inside `<script>` tags) | **Parsing problem** — payload is there, your extractor strips it | Parser (ChatPeek) or hand-rolled decode |
| Body is empty shell, no content keywords | **Rendering problem** — payload requires JS execution or a backend fetch | Browser MCP or managed render service |

**The command (PowerShell):**
```powershell
$r = Invoke-WebRequest -Uri "<url>" -UseBasicParsing -TimeoutSec 20 `
     -Headers @{"User-Agent"="Mozilla/5.0 ... Chrome/120.0 Safari/537.36"}
$r.Content.Length           # body size — <50KB usually means shell
$r.Content -match 'reactRouterContext|__NEXT_DATA__|__sveltekit'  # SPA framework marker
$r.Content -match '<expected-content-keyword>'                    # is the text actually there?
$r.Content -match 'cf-challenge|Just a moment'                     # Cloudflare wall?
```

This diagnostic is transferable to **any** SPA. It costs one command (~200ms) and
prevents the most common tool-selection error: reaching for a browser when a
parser would do. Reference: session 2026-08-10 — the raw GET returned HTTP 200,
489KB, with both `reactRouterContext` and the conversation keyword present,
proving the browser was unnecessary before any tool was chosen.

## The best tool: a purpose-built parser

The architecturally-correct tool decodes the embedded React Flight payload from
a single GET. **[ChatPeek](https://github.com/vl3c/ChatPeek)** is the best-in-class:

- **Single GET** with private-window headers — no browser, no retry loop, no backend probing.
- **React Flight parser** for modern `chatgpt.com` shares + legacy fallback for `chat.openai.com`.
- **Message normalization** preserving Markdown tables, code blocks, thoughts, tool outputs, attachments.
- **CLI:** `python ChatPeek.py <share-url>` → writes Markdown to disk.
- **Deps:** `requests` + `beautifulsoup4`. MIT, unit-tested with fixtures, weekly liveness checks.
- Uses only data already embedded in the page — no private-API scraping.

TS port: [`chatgpt-share-parser`](https://www.npmjs.com/package/chatgpt-share-parser).

## Method ranking

| # | Method | For static shared links | Best when |
|---|--------|------------------------|-----------|
| 1 | **ChatPeek / chatgpt-share-parser** | ✅ **Best — single GET + React Flight parse** | Default for reading any completed share |
| 2 | Raw `Invoke-WebRequest` + hand-rolled parse | Works (proven this session) | No extra dep; ~30 lines |
| 3 | Apify `chatgpt-shared-scraper` / `chatgpt-conversation-scraper` | Robust, maintained-for-you | Zero local maintenance; external account OK |
| 4 | `chrome__use_browser` / chrome-devtools MCP | Overkill here | **Interactive** chatgpt.com (live prompts), login-gated, or CF-challenged |
| 5 | firecrawl / Scrapfly (`--render-js`) | Heavier than needed | Sites that genuinely require rendering |
| 6 | `web_fetch` | ❌ Strips/truncates the payload | Static server-rendered HTML only |

## Decision rule (tool selection)

**For `chatgpt.com/s/`, `chatgpt.com/share/`, or any React Router / Next.js `app`-dir
share page:** reach for **ChatPeek** (single GET + parse) first. Do NOT start with
`web_fetch` (strips payload) and do NOT reach for a browser unless the link is
interactive, login-gated, or Cloudflare-challenged.

**Generalization:** any SPA whose payload is embedded as serialized JSON in the
static HTML (React Flight, `__NEXT_DATA__`, SvelteKit `__sveltekit`) is parseable
without a browser. Verify the payload is in the served HTML with a raw GET first;
if present, a parser beats a browser on cost, speed, and host-isolation hygiene.

## When the parser path fails (fall back to browser)

- **Login wall** (`/auth/login` redirect): the share was revoked/made private. No
  tool reads it without the owner's session.
- **Cloudflare interactive challenge**: rare for residential single-requests, but
  datacenter IPs / unusual patterns can trigger it (ChatPeek CI notes this). If it
  fires, fall back to a real browser or a managed scraper (Apify).
- **Format drift**: OpenAI changes the React Flight serialization and the parser
  hasn't caught up. ChatPeek is maintained + fixture-tested; a hand-rolled parser
  breaks first. Pin a version.

## Verified receipt (2026-08-10)

ChatPeek installed at `P:/packages/ChatPeek/` and tested against the `/s/` short-format
link `chatgpt.com/s/t_6a79595fa5e08191be8f903c5e10b4a9`:

```
python P:/packages/ChatPeek/ChatPeek.py https://chatgpt.com/s/t_6a79595fa5e08191be8f903c5e10b4a9
→ Exports/chrome-extensions-for-chapters-t_6a7959.md (13076 bytes, 309 lines, exit 0)
```

Output: clean Markdown with title, timestamp, assistant turn, complete code block,
structured sections — no ChatGPT nav/footer chrome. The `/s/` format (which
ChatPeek's README doesn't explicitly document) works natively. The React Flight
parser handles both `/s/` and `/share/` formats without modification.

**Invocation for fleet use:**
```
python P:/packages/ChatPeek/ChatPeek.py <share-url>
```
Output lands in `P:/packages/ChatPeek/Exports/<slug>-<id>.md`. Deps: `requests` +
`beautifulsoup4` (installed to system Python 3.14).

## What this means for our workspace

**Default routing for AI-tool shared links:** when the operator pastes a
`chatgpt.com/s/`, `chatgpt.com/share/`, `claude.ai/share/`, or similar SPA link,
reach for ChatPeek first — not `web_fetch`, not the browser MCP. The invocation
is one command; the output is clean Markdown on disk. This eliminates the
recurring "web_fetch can't read this" failure and avoids unnecessary browser
contention on this multi-terminal host ([[concurrent-cdp-auth-contention]]).

**[[tool-fallbacks]] is updated** with a STRUCTURAL entry routing shared links
to ChatPeek. Future sessions that check tool-fallbacks before fetching will
find the routing automatically.

**The raw-GET diagnostic generalizes beyond ChatGPT.** Any time `web_fetch`
returns an empty shell, run `Invoke-WebRequest` + grep for the content before
reaching for a browser. The payload may be in the static HTML even when the
markdown extractor strips it. This diagnostic applies to React Flight, Next.js
`__NEXT_DATA__`, SvelteKit `__sveltekit`, and any other framework that embeds
serialized state in script tags.

## Why this is a wiki concept

The operator reads AI-tool shared links constantly (ChatGPT, Claude, Gemini). The
failure class ("web_fetch can't read this") recurs. Pinning the parser-first method
durably prevents re-deriving the failure and prevents the satisficing error of
defaulting to a browser because one is available ([[minimal-fix-and-root-cause]]).

## Receipts

| Claim | Evidence | Source |
|---|---|---|
| React Flight payload is in the static HTML body | `Invoke-WebRequest` returned HTTP 200, 489KB; body contains `reactRouterContext` at line 464 and the conversation keyword `obligation` | Session 2026-08-10, raw GET receipt |
| `web_fetch` strips the payload (not a JS-rendering failure) | `web_fetch` on the same URL returned near-empty; the captured `.html` via browser shows the payload in a `<script>` tag that markdown extractors discard | Session 2026-08-10, `001-navigate.html` line 464 |
| ChatPeek extracts `/s/` format natively | `python ChatPeek.py <url>` → exit 0, 13076 bytes, 309 lines | Session 2026-08-10, live test |
| ChatPeek source implements React Flight parser | `P:/packages/ChatPeek/ChatPeek.py` — single-GET design, `DEFAULT_HEADERS` with private-window UA, `ALLOWED_ASSET_HOST_SUFFIXES` SSRF defense | Source inspection session 2026-08-10, lines 1-80 |
| Cloudflare does not challenge single residential GETs to shared links | Raw GET returned 200 with no `cf-challenge` or `Just a moment` markers | Session 2026-08-10 — [INFERENCE] generalized from one datacenter-free test; datacenter IPs may differ per Scrapfly guide |

## Falsifier

This concept is wrong if (a) `web_fetch` gains a mode that returns raw `<script>`
payloads in full, or (b) ChatGPT shared links move the payload behind a runtime-only
fetch such that it's absent from the static HTML. Track by re-testing a raw GET
against a known share quarterly: if the body no longer contains `reactRouterContext`
or the conversation text, the parser approach is broken and the browser becomes
the default again.

## Auto-related

- [[react-component-library-ecosystem]]
- [[browser-automation-failure-modes-llm-chat]]
- [[model-quota-contention-coordination-fleet-rate-limiting]]
- [[skill-catalog]]
- [[multi-model-ai-workflow-patterns]]

