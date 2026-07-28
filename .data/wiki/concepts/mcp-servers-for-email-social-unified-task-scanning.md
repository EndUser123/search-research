---
title: "MCP Servers for Email, Social, and Unified Task Scanning"
slug: mcp-servers-for-email-social-unified-task-scanning
created: 2026-07-28
category: reference
tags: [mcp, email, social-media, reddit, linkedin, twitter, hacker-news, task-management, grok-build, reference]
summary: >
  Survey of installable MCP servers for email scanning (Gmail + Outlook),
  social media reading (Reddit, X, LinkedIn, HN), and unified task lists.
  All are compatible with Grok Build's BYO-MCP feature (stdio or HTTP
  transport). Top picks: codefuturist/email-mcp (multi-provider email,
  83★), karanb192/reddit-mcp-buddy (Reddit, 767★),
  stickerdaniel/linkedin-mcp-server (LinkedIn, 2,929★),
  universal-inbox/universal-inbox (unified GitHub+Linear+Gmail, 58★).
  These eliminate the need to build email/social scanning from scratch.
cognitive_load: 2
verification: multi-source-verified
agent: grok
host: both
sources:
  - "GitHub API star counts and last-push dates (verified 2026-07-28)"
  - "codefuturist/email-mcp — https://github.com/codefuturist/email-mcp (83★)"
  - "karanb192/reddit-mcp-buddy — https://github.com/karanb192/reddit-mcp-buddy (767★)"
  - "stickerdaniel/linkedin-mcp-server — https://github.com/stickerdaniel/linkedin-mcp-server (2,929★)"
  - "rafaljanicki/x-twitter-mcp-server — https://github.com/rafaljanicki/x-twitter-mcp-server (35★)"
  - "erithwik/mcp-hn — https://github.com/erithwik/mcp-hn (74★)"
  - "universal-inbox/universal-inbox — https://github.com/universal-inbox/universal-inbox (58★)"
  - "microsoft/work-iq — https://github.com/microsoft/work-iq (953★)"
  - "rdmgator12/awesome-grok-connectors — https://github.com/rdmgator12/awesome-grok-connectors"
  - "xai-org/plugin-marketplace — https://github.com/xai-org/plugin-marketplace"
relations:
  - target: wiki/concepts/adhd-friendly-unified-todo-workspace-email-scanning.md
    type: extends
  - target: wiki/concepts/social-media-as-structured-research-data-for-ai-agents.md
    type: related
  - target: wiki/concepts/web-research-state-2026.md
    type: refines
---

# MCP Servers for Email, Social, and Unified Task Scanning

## Decision context

**The problem:** the operator needs `/todo` to scan email (2 Gmail + 1
Hotmail) and social sources (Reddit, HN) alongside workspace state. Building
email/social scanning from scratch (IMAP, OAuth, API clients) is expensive
and fragile. The question: do existing MCP servers cover this need?

**What the research found:** yes, comprehensively. The MCP ecosystem has
mature servers for every platform we need, all compatible with Grok Build's
BYO-MCP feature. No custom email/social scanning code is needed — install
the MCP servers, configure auth, and `/todo` calls their tools.

## Email MCP servers

### Top pick: `codefuturist/email-mcp` (83★, May 2026)

Multi-provider IMAP+SMTP with auto-detect for Gmail/Outlook/Yahoo/iCloud.
Multi-account via TOML config. IMAP IDLE watcher for real-time push. AI
triage presets (inbox-zero, GTD, priority-focus). 47 tools, 7 prompts,
6 resources. Docker images available.

**Auth:** app passwords (default) or OAuth2 XOAUTH2 (experimental, Gmail+M365).
**Multi-account:** yes — explicit design goal.
**Install:** `npx -y @codefuturist/email-mcp`

### Alternative: `marlinjai/email-mcp` (16★, Jun 2026)

Unified Gmail + Outlook + iCloud + generic IMAP. PKCE OAuth2 (no Azure/Google
project needed). AES-256-GCM encrypted credential store. Cross-account
email_transfer preserves threading. Batch operations.

**Auth:** OAuth2 PKCE (built-in client) + IMAP app password.
**Multi-account:** yes — unified inbox across providers.
**Install:** `npx -y @marlinjai/email-mcp`

### Multi-Gmail only: `tszaks/ghub` (1★, Jun 2026)

Multi-Gmail aggregation with OAuth onboarding via MCP tools. Per-account
token files. `read_emails`/`search_emails` aggregate across accounts.

## Social MCP servers

### Reddit: `karanb192/reddit-mcp-buddy` (767★, Jul 2026)

Three-tier auth: anonymous (10 rpm, no keys), app-only OAuth2 (60 rpm),
full OAuth2 user (100 rpm). Browse, search, post+comments, user analysis.
In-memory LRU cache. TypeScript, `npx -y reddit-mcp-buddy`.

### X/Twitter: `rafaljanicki/x-twitter-mcp-server` (35★, May 2026)

Official Twitter API v2. ~30 tools: search, timelines, trends, post/delete,
bookmarks, polls. Requires developer.twitter.com credentials. Built-in
rate-limit handling.

**Alternative:** `Xquik-dev/x-twitter-scraper` (170★, Jul 2026) — third-party
hosted API, no X credentials needed, 119 MCP routes. API key auth.

### LinkedIn: `stickerdaniel/linkedin-mcp-server` (2,929★, Jul 2026)

19 tools: profiles, companies, search, feed, inbox, send message. Uses
your own logged-in browser session (persistent profile or cookie import
from Chrome/Edge/Brave). No LinkedIn API key needed. Install via
`uvx mcp-server-linkedin@latest`.

### Hacker News: `erithwik/mcp-hn` (74★) or `paabloLC/mcp-hacker-news` (32★)

Both use the free public HN Firebase API. No auth needed. `mcp-hn` is
simpler (4 tools); `mcp-hacker-news` is broader (11 tools + 3 resources).

## Unified task lists

### `universal-inbox/universal-inbox` (58★, Jul 2026)

Centralizes GitHub + Linear + Gmail notifications into one inbox UI.
Per-item: delete, unsubscribe, snooze, create/link Todoist task.
Self-hosted (Rust + Postgres + Redis). Apache-2.0.

### `microsoft/work-iq` (953★, Jul 2026)

Official Microsoft MCP for M365: Outlook email + calendar + Teams + docs.
`npx -y @microsoft/workiq mcp`. Requires Entra tenant admin consent.
Best for the Hotmail/Outlook account.

## Grok Build integration

All servers install via `grok mcp add`:

```powershell
# Email (multi-provider)
grok mcp add email -- npx -y @codefuturist/email-mcp

# Reddit
grok mcp add reddit -- npx -y reddit-mcp-buddy

# Hacker News
grok mcp add hackernews -- uvx mcp-hn

# LinkedIn
grok mcp add linkedin -- uvx mcp-server-linkedin@latest
```

Auth is configured per-server (env vars, config files, or browser-based
OAuth flows). The shared TTL cache and deferral logic lives in `/todo`'s
orchestration layer, not in the MCP servers themselves.

## What this means for our workspace

**No custom email scanning code needed.** The plan in
[[adhd-friendly-unified-todo-workspace-email-scanning]] proposed building
IMAP+OAuth scanning from scratch. The MCP servers handle all of that.
`/todo` calls the MCP email tools and applies the TTL cache + deferral
logic on top.

**For `/www` research:** the Reddit and HN MCP servers replace the
`site:reddit.com` search workaround documented in
[[social-media-as-structured-research-data-for-ai-agents]]. Full thread
content is accessible via MCP tools, not just search snippets.

## Falsifier

This survey is wrong if:
- The MCP servers don't work with Grok Build's MCP implementation
  (they should — all use stdio or HTTP transport)
- Auth proves too fragile (OAuth tokens expire, LinkedIn DOM changes)
- The servers are abandoned (check stars/push dates before relying)
- Grok Build adds native connectors that make these redundant (possible —
  xAI's chat-side Gmail/Outlook connectors may come to Grok Build)

## Receipts

- `grok mcp list` — current MCP servers (search, context7 only; no email/social yet)
- `grok mcp add --help` — confirms stdio + HTTP transport support
- GitHub API star counts verified 2026-07-28 via Invoke-RestMethod
- `rdmgator12/awesome-grok-connectors` README — documents xAI's 30 built-in chat connectors (separate from Grok Build plugin marketplace)

## Related

- [[adhd-friendly-unified-todo-workspace-email-scanning]] — the /todo design this enables
- [[social-media-as-structured-research-data-for-ai-agents]] — prior research on social data access (this MCP survey refines it)
- [[web-research-state-2026]] — prior state of free-tier access (refined: MCP servers provide a cleaner path than raw APIs)
