---
title: "Web and Social Research State in 2026: Free Tiers, Maintained Tools"
created: 2026-07-20
source: session-2026-07-20
tags: ['research', 'web-search', 'social-media', 'scraping', 'api-limits', 'host-agnostic']
summary: >
  Free-tier state for Reddit, X.com, LinkedIn, YouTube research as of mid-2026. Reddit OAuth via PRAW = 100 QPM free. X.com free API read = effectively dead (1 req/15min). LinkedIn no good free client. YouTube yt-dlp + youtube-transcript-api fully free. Maintained GitHub repos: praw-dev/praw, yt-dlp/yt-dlp, jdepoix/youtube-transcript-api.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
---

## Summary

Reference for what web/social research tools are usable under a "no new spend, no ban risk, OK with self-rate limiting" constraint. Compiled 2026-07-20 from web research (Reddit Data API Wiki, X developer community, LinkedIn scraper roundups) and GitHub repo activity.

## Key Findings

### Reddit — clean win

- **API**: OAuth-authenticated clients get **100 QPM free** per OAuth client. Unauthenticated `.json` endpoints are **10 QPM** (tightening per r/redditdev). Commercial tier is separate pricing.
- **Repo**: `praw-dev/praw` — official, BSD-2-Clause, very actively maintained.
- **Ban risk**: Zero if you stay under 100 QPM and use a real `user_agent` per Reddit API rules.
- **Self-rate limiting**: PRAW `api_request_delay=0.65` (~92 QPM, well under limit).
- **Setup**: Create a "script" app at `https://www.reddit.com/prefs/apps`, store `client_id` and `client_secret` in env, `pip install praw`.

### YouTube — clean win

- **Repos**: `yt-dlp/yt-dlp` (the canonical fork, very actively maintained, handles YouTube's frequent breakage within hours) and `jdepoix/youtube-transcript-api` (Python, maintained).
- **Cost**: $0 for public videos.
- **Ban risk**: yt-dlp forges its own requests, not authenticated as your account. IP-level rate limiting is the only concern. yt-dlp has built-in throttling (`--sleep-interval 5 --max-sleep-interval 15`).
- **Age-restricted caveat**: requires cookies via `--cookies-from-browser chrome` or `cookies.txt`. Self-pace aggressively or your YouTube account could be flagged.

### X.com — most constrained

- **Free API**: post-only. Recent Search on Free tier = **1 request per 15 minutes** (essentially useless). Basic tier = $200/month for ~10,000 reads/month. Pro = $5,000/month (closed to new signups as of mid-2026).
- **Free libraries**: `snscrape`, `twint` — abandoned. `Altimis/Scweet` — last update March 2026, declining reliability. `vladkens/twscrape` — uses cookies, low maintenance.
- **Free working path**:
  - Google site: search via `web-search-prime` (`site:x.com` / `site:twitter.com`) for indexed tweets
  - oEmbed at `https://publish.twitter.com/oembed?url=<tweet_url>` for individual tweet text
  - Chrome MCP with manual login, slow human pacing, single session
- **Reality**: X is the hardest target. The free ecosystem collapsed in 2023-2024 and hasn't recovered. For deep research, expect to use chrome MCP with anti-ban discipline.

### LinkedIn — workable with constraints

- **No good free GitHub repo**. `tomquirk/linkedin-api` is essentially abandoned. `joeyism/linkedin-scraper` uses Playwright but barely maintained.
- **Discovery (free, no risk)**: `web-search-prime` with `site:linkedin.com` returns Google-indexed public profiles/posts/company pages.
- **Specific profile deep-dive**: `firecrawl_scrape` on public profile URL. Many fields are public; full connection list and activity feed require login.
- **Authenticated, low-volume**: Chrome MCP with manual login, single session, slow human pacing (30+ seconds per profile, max 30-50 per session). Do NOT bulk-scrape — LinkedIn aggressively detects automation.
- **Paid services (excluded by constraint)**: Apify, Bright Data, Scrapfly, PhantomBuster, Datablist. All handle anti-ban infrastructure; you give them money, they give you data.

## Related

- [[grok-build-compat-layer-marketplace-plugin-skills]] — the `/web` skill from `search-research` plugin is not invocable; building a Grok-native wrapper or installing the plugin properly is required
- [[are-there-repos-or-solutions-to-claude-code-gettin]] — adjacent: this list is platform-agnostic; that page scopes similar questions to Claude Code tooling

## Auto-related

<!-- auto-managed by wiki_after_write.py -->

## Sources

- session-2026-07-20 — `minimax-search` results for Reddit API rate limits (Reddit Data API Wiki, r/redditdev)
- session-2026-07-20 — `minimax-search` results for LinkedIn scraping without getting banned (CodeWords, GoLogin, Vayne, Datablist)
- session-2026-07-20 — `minimax-search` results for X/Twitter API 2026 pricing (sociavault, blotato, socialcrawl, devcommunity.x.com)
- session-2026-07-20 — GitHub repo activity for `praw-dev/praw`, `yt-dlp/yt-dlp`, `jdepoix/youtube-transcript-api`
