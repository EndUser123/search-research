---
title: "Reading ChatGPT shared links (and other React Flight SPAs)"
slug: reading-chatgpt-shared-links-js-spa
tags: [web-fetching, scraping, chatgpt, react-flight, tool-selection]
categories: [tool-fallbacks, web-research]
verified: 2026-08-10
verification: observed-this-session
source:
  - session 2026-08-10 (Invoke-WebRequest + chrome__use_browser on chatgpt.com/s/t_6a79595... link)
  - https://github.com/vl3c/ChatPeek (React Flight parser, single-GET design)
  - https://www.npmjs.com/package/chatgpt-share-parser (TS port)
  - https://scrapfly.io/blog/posts/how-to-scrape-chatgpt (2026-06, Cloudflare context)
related:
  - "[[tool-fallbacks]]"
  - "[[optimal-long-term-solution-not-minimal-fix]]"
  - "[[concurrent-cdp-auth-contention]]"
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
was served完整 to a plain HTTP client. A browser "works" but is a sledgehammer:
it spins up Chrome, captures screenshots/console, and contends for the shared CDP
profile (see [[concurrent-cdp-auth-contention]] — a real host invariant).

Shared links are public-by-design (they carry OG image meta tags for social
preview), so they are served to any HTTP client with a browser UA without a
Cloudflare challenge in normal single-request use.

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

## Why this is a wiki concept

The operator reads AI-tool shared links constantly (ChatGPT, Claude, Gemini). The
failure class ("web_fetch can't read this") recurs. Pinning the parser-first method
durably prevents re-deriving the failure and prevents the satisficing error of
defaulting to a browser because one is available ([[optimal-long-term-solution-not-minimal-fix]]).

## Falsifier

This concept is wrong if (a) `web_fetch` gains a mode that returns raw `<script>`
payloads完整, or (b) ChatGPT shared links move the payload behind a runtime-only
fetch such that it's absent from the static HTML. Track by re-testing a raw GET
against a known share quarterly: if the body no longer contains `reactRouterContext`
or the conversation text, the parser approach is broken and the browser becomes
the default again.
