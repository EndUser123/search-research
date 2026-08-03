---
thread_id: social-media-scraping-architecture-20260802
parent_handoff_path: docs/handoffs/session-019fbf77-20260802/HANDOFF.md
current_session_id: 019fbf77-8fe7-7070-bccd-e12f5d1807d8
current_terminal_id: grok-main
produced_at: 2026-08-02T20:30:00-06:00
status: open
handoff_type: implementation
---

# Handoff: Social media scraping architecture

## Objective

Wire twscrape (X.com) into the /www Phase 2b practitioner signal pass,
completing the social media data extraction stack. The research is done
(see [[social-media-data-extraction-landscape-2026]]); this is the
implementation work.

## Status: OPEN — research complete, implementation not started

## Producing context

Session 2026-08-02 investigated the social media scraping landscape after
the Reddit MCP was fixed with OAuth credentials. The operator asked whether
/model-web (Chrome CDP) could help with social media scraping, which led
to researching Puppeteer/Playwright/CDP comparisons and the broader tool
landscape.

## What was decided

1. **twscrape is the tool for X.com** — async Python CLI, GraphQL endpoints,
   account pool rotation, returns structured JSON. Same pattern as
   ddgs_search.py.
2. **Browser automation is the fallback for unknown platforms** —
   chrome-devtools-mcp already covers this via /model-web. Playwright MCP
   deferred (22 tool descriptions overhead not justified yet).
3. **The existing stack already covers most platforms** — Reddit MCP,
   yt-dlp, HN Algolia, firecrawl. Only X.com is missing.

## Tasks

### NEXT-1: Install twscrape and set up X.com account pool
- `pip install twscrape`
- Add X.com account to twscrape's pool (`twscrape add_account`)
- Verify: `twscrape search "AI agents" --limit 5`
- Acceptance: returns structured JSON with tweet text + engagement metrics

### NEXT-2: Wire twscrape into /www Phase 2b
- Add twscrape call alongside Reddit MCP and HN Algolia in the
  practitioner signal pass section of www/SKILL.md
- Pattern: `twscrape search "<topic> experience" --limit 10`
- Acceptance: /www runs that include X.com data in Phase 2b output

### NEXT-3: Update /web SKILL.md routing
- Add X.com routing rule: `twscrape` first, DDG site-search as fallback
- Similar to the Reddit routing rule pattern

### LATER-1: Evaluate Playwright MCP if anti-reflow becomes a problem
- Only install if chrome-devtools-mcp proves insufficient for a specific
  platform with dynamic DOM (infinite scroll, lazy-load)
- Trigger: documented case where CDP extraction fails due to reflow

### LATER-2: Evaluate cdp-browser for anti-bot-protected platforms
- Only needed if standard CDP gets detected and blocked
- Reference: dao-ai/cdp-browser (Bézier mouse, anti-detection injection)

## Related artifacts

- Wiki concept: [[social-media-data-extraction-landscape-2026]]
- Updated: [[web-research-state-2026]] (twscrape assessment corrected)
- Parent handoff: session-019fbf77-20260802 (revision 4)

## Falsifier

This handoff is obsolete if twscrape's GraphQL endpoints get blocked by
X.com before implementation, or if a free X.com API tier returns. In that
case, re-evaluate using browser automation (chrome-devtools-mcp) for X.com
instead.
