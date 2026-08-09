---
title: "YouTube Watch Later and History Playlist URL Extraction"
slug: youtube-watch-later-and-history-playlist-url-extraction
created: 2026-07-28
category: reference
tags: [youtube, playlist, watch-later, history, yt-dlp, takeout, notebooklm]
summary: >
  Methods to extract YouTube Watch Later and History playlist URLs for
  batch-import into NotebookLM. The YouTube Data API v3 does not expose
  either playlist. yt-dlp with browser cookies is the primary extraction
  tool (--flat-playlist for WL, :ythis for History). Google Takeout provides
  bulk history export as JSON. Chrome extensions (TidyWL 5.0★, Multiselect
  4.0★) are preferred by non-technical users. Critical prerequisite: yt-dlp
  requires an external JS runtime (Deno/Node.js) since late 2025.
cognitive_load: 2
verification: multi-source-verified
agent: grok
relations:
  - "[[notebooklm-cli-operational-gotchas]]"
  - "[[nlm-to-wiki-optimization-opportunities]]"
  - "[[youtube-transcript-extraction-techniques]]"
  - "nlm-bulk-ingest"
  - "[[concurrent-cdp-auth-contention]]"
sources:
  - "Jordan Cooks walkthrough (Jan 2026) — yt-dlp :ythis for history"
  - "demodisc.zone (Aug 2025) — yt-dlp --flat-playlist for Watch Later"
  - "Chrome Web Store — TidyWL 5.0★, Multiselect 4.0★"
  - "GitHub — YTmigrateWL, rbits0/watch-later-extractor, yt-playlist-export"
  - "Reddit r/youtubedl, r/commandline, r/youtube — community sentiment"
  - "yt-dlp wiki/EJS — JS runtime requirement (verified 2026-07-28)"
  - "Google Takeout — watch-history.json format"
---

# YouTube Watch Later and History Playlist URL Extraction

## Decision context

**The problem:** we needed to extract YouTube Watch Later and History playlist
URLs so we can batch-add them to our 3 NotebookLM accounts (`a.hominidae`
paid/300-src, `troup.hominidae` free/50-src, `brsthomson` free/50-src) via
`nlm-bulk-ingest`. The YouTube Data API v3 deliberately does not expose
watch history, and Watch Later uses an opaque playlist format that the API
also cannot access. This concept captures what actually works in 2026 and
what the community recommends.

**What alternatives were explored:** YouTube Data API v3 (confirmed
non-functional for both WL and History), Google Takeout (works but slow +
stale), yt-dlp with cookies (the winner), browser extensions (good for
non-technical use), Playwright/Selenium (too fragile).

**What the research changed:** confirmed yt-dlp as the primary extraction
tool for both playlists, with Google Takeout as the bulk-history fallback.
Surfaced the EJS runtime requirement as a critical prerequisite.

## The constraint that shapes everything

The YouTube Data API v3 **does not expose Watch Later or watch history**.
This is a deliberate, confirmed restriction — the `Activities` resource once
partially exposed history, but Google deprecated those activity types. Watch
Later (`list=WL`) uses an opaque playlist format accessible only via an
authenticated browser session. Every working method requires cookies.

## Multi-terminal isolation (critical for this fleet)

**Never use `--cookies-from-browser chrome` in multi-terminal workflows.**
It reads Chrome's live cookie database — concurrent terminals contend for
the same DB lock, and a cookie refresh in one invalidates the others'
sessions. This is the same failure class as
[[concurrent-cdp-auth-contention]], just at the browser-cookie layer.

**The fix:** each nlm profile has independent Google session cookies that
work across all Google services (YouTube included). Export them to Netscape
format per-profile and use `--cookies <file>`:

```bash
# One-time: export all 3 profiles' cookies to isolated files
python P:/.agents/skills/nlm-to-wiki/scripts/bin/export_yt_cookies.py --all
# → P:/.data/yt-is/state/cookies/cookies-a.hominidae.txt
# → P:/.data/yt-is/state/cookies/cookies-troup.hominidae.txt
# → P:/.data/yt-is/state/cookies/cookies-brsthomson.txt
```

Each terminal/worker uses its own cookie file — no contention, no stale
browser DB. Re-run the export after `nlm login --profile <name>` to refresh.

## Watch Later extraction (ranked by recommendation strength)

### 1. yt-dlp `--flat-playlist` with profile-isolated cookies [HIGH]

The top CLI recommendation on r/youtubedl and Hacker News. Uses isolated
per-profile cookie files instead of the live browser DB:

```bash
yt-dlp --cookies P:/.data/yt-is/state/cookies/cookies-a.hominidae.txt \
       --flat-playlist \
       --skip-download --ignore-errors \
       --print-to-file webpage_url wl-urls.txt \
       "https://www.youtube.com/playlist?list=WL"
```

**Pros:** clean URL-only output, scriptable, **multi-terminal safe** (each
profile uses its own cookie file), pipes directly into `nlm-bulk-ingest`.
**Cons:** cookies need periodic re-export after `nlm login`. **Critical:**
requires EJS runtime since late 2025 — see "EJS prerequisite" below.
**Auth:** `--cookies <file>` (profile-isolated, never `--cookies-from-browser`).
**Scale:** hundreds: fine. Thousands: chunk at 100 per batch.

### 2. TidyWL (Chrome extension) [HIGH for non-CLI]

**5.0★ / 38 reviews** on Chrome Web Store. Purpose-built for Watch Later's
hidden 5000-video cap. Provides dashboard (by channel, topic, duration),
bulk-delete, bulk-move, JSON/CSV export. Client-side only (no server).
**Pros:** best UX, actively maintained, handles the 5000-cap.
**Cons:** browser extension (Manifest V3 risk); piggybacks on YouTube's
internal endpoints (can break on UI changes).

### 3. Multiselect for YouTube™ by Pollux [MEDIUM]

**4.0★ / 872 ratings, 60,000 users.** Works inside YouTube's UI —
multiselect, sort, find-duplicates, export. Cited on Web Apps Stack Exchange
as "the only one that works for the 5000 Watch Later limit."
**Pros:** largest user base, battle-tested.
**Cons:** occasional YouTube UI breakage; export is less clean than yt-dlp.

### 4. YTmigrateWL (Python + Node.js) [MEDIUM]

Two-stage CLI: (1) export WL → CSV via browser cookies, (2) archive into a
timestamped private playlist and optionally clear WL. Posted on r/commandline
(Sep 2025).
**Pros:** built for the export → archive → clear workflow.
**Cons:** heavy stack (Python 3.13+, Node 18+, pnpm); manual cookie paste.

## History extraction (ranked by recommendation strength)

### 1. Google Takeout (bulk archival) [HIGH]

The only complete bulk export. Go to `takeout.google.com` → select
YouTube → "history" → JSON. Returns `watch-history.json` with `titleUrl`
(video URL), `title`, `time`, `subtitles` (channel info).

```python
import json
with open("watch-history.json") as f:
    history = json.load(f)
urls = [e["titleUrl"] for e in history if "titleUrl" in e]
```

**Pros:** complete history, legal, includes timestamps + channel data.
**Cons:** slow (hours to days for large accounts); frequently flagged as
incomplete on Reddit (~2 years of history only); one-shot export (no
continuous sync); files can be GB-scale.
**Freshness:** as of export creation — not real-time.

### 2. yt-dlp `:ythis` selector (incremental/recent) [HIGH]

Near real-time extraction using yt-dlp's undocumented `:ythis` keyword:

```bash
yt-dlp --cookies P:/.data/yt-is/state/cookies/cookies-a.hominidae.txt \
       --flat-playlist --dump-json \
       "https://www.youtube.com/feed/history" \
       > history.json
```

Confirmed working in Jordan Cooks' January 2026 walkthrough. Returns
`title`, `channel`, `original_url`, `upload_date`.
**Pros:** live data, re-runnable, outputs JSON/CSV directly.
**Cons:** no `watched_at` timestamp (only `upload_date`); requires cookies;
needs EJS runtime; rate-limit risk on large history.
**Freshness:** near real-time.

### 3. Playwright/Selenium scraping [LOW]

Drive a real browser to `youtube.com/feed/history`, scroll, extract.
**Pros:** full control over fields.
**Cons:** fragile (DOM changes regularly), expensive, bot detection risk.
**Not recommended** unless you need a specific field yt-dlp doesn't provide.

### 4. YouTube Data API v3 [REFUTED]

Does NOT work for watch history. Confirmed by Google's own docs and every
StackOverflow thread on the topic. The `activities.list` endpoint no longer
returns history-related activity types.

## EJS prerequisite (critical for all yt-dlp methods)

Since late 2025, yt-dlp requires an external JavaScript runtime to solve
YouTube's player signature/throttle challenges. Without it, expect "Requested
format not available," 403, or 429 errors.

```bash
# Install Deno (recommended)
curl -fsSL https://deno.land/install.sh | sh    # Linux/Mac
# Or: winget install DenoLand.Deno                # Windows

# Enable EJS in yt-dlp
yt-dlp --extractor-args "youtube:player-client=ios|web|android:external_downloader=ejs:github" \
       --remote-components ejs:github
```

Add to `yt-dlp.conf` for persistence. See yt-dlp-ejs-requirement and the
yt-dlp EJS wiki for details. Already documented extensively in our workspace
chat-session sources.

## Recommended workflow for our 3-account NotebookLM pipeline

### Step 0: Export profile-isolated cookies (multi-terminal safe)

```bash
# One-time (re-run after nlm login to refresh)
python P:/.agents/skills/nlm-to-wiki/scripts/bin/export_yt_cookies.py --all
```

### Step 1: Extract URLs (per-profile, isolated)

```bash
# Watch Later (per-profile — each terminal uses its own cookie file)
yt-dlp --cookies P:/.data/yt-is/state/cookies/cookies-a.hominidae.txt \
       --flat-playlist --skip-download \
       --print-to-file webpage_url wl-a.hominidae.txt \
       "https://www.youtube.com/playlist?list=WL"

# History (recent, incremental)
yt-dlp --cookies P:/.data/yt-is/state/cookies/cookies-a.hominidae.txt \
       --flat-playlist --dump-json \
       "https://www.youtube.com/feed/history" > history-a.hominidae.json
# Extract URLs: python -c "import json; [print(e['original_url']) for e in json.load(open('history-a.hominidae.json'))]" > history-urls.txt

# History (bulk, one-time — per Google account)
# Request from takeout.google.com → YouTube → history → JSON
# Parse: python -c "import json; [print(e['titleUrl']) for e in json.load(open('watch-history.json')) if 'titleUrl' in e]" > history-bulk-urls.txt
```

### Step 2: Combine + deduplicate

```bash
cat wl-*.txt history-*.txt history-bulk-*.txt 2>/dev/null | sort -u > all-video-urls.txt
```

### Step 3: Distribute across 3 accounts via nlm-bulk-ingest

The `nlm-bulk-ingest` skill clusters URLs into themed notebooks under
the per-notebook source cap. With 3 accounts:

| Account | Capacity | Role |
|---------|----------|------|
| `a.hominidae` (paid) | 300 sources/notebook | Primary — takes the largest clusters |
| `troup.hominidae` (free) | 50 sources/notebook | Secondary — smaller clusters |
| `brsthomson` (free) | 50 sources/notebook | Tertiary — overflow + smaller clusters |

```bash
# Cluster + distribute (nlm-bulk-ingest handles the math)
python P:/.agents/skills/nlm-bulk-ingest/scripts/ingest.py \
    all-video-urls.txt \
    --all --prefix "WL: " \
    --profile a.hominidae \
    --state run.json
```

For the free accounts, run separately with smaller batches (≤50 per notebook).

### Step 4: Sync to wiki via nlm-to-wiki

```bash
python P:/.agents/skills/nlm-to-wiki/scripts/bin/queue_sync.py \
    --enqueue --all-profiles
python P:/.agents/skills/nlm-to-wiki/scripts/bin/queue_sync.py \
    --worker --worker-id w1 --profile a.hominidae
```

## What people like and dislike (community sentiment)

**Likes:**
- yt-dlp's `--flat-playlist` is the developer-community reference answer
- TidyWL gets the highest satisfaction ratings for non-technical users
- Google Takeout is trusted as the canonical bulk method despite slowness
- Export-youtube-playlist.vercel.app (web app, official API) is liked for
  public playlists (no auth needed, 8+ output formats)

**Dislikes:**
- YouTube's hidden 5000-video Watch Later cap (no warning, silent failure)
- Takeout's history incompleteness (~2 years only, recurring complaint)
- Cookie expiration breaking yt-dlp mid-extraction on large lists
- Browser extensions breaking on YouTube UI changes (Manifest V3 casualties)
- No official API for either Watch Later or History (community frustration)

## Falsifier

This concept becomes wrong if:
- YouTube opens an official API endpoint for Watch Later or History (unlikely)
- yt-dlp's `:ythis` selector breaks in a newer version (undocumented, fragile)
- Google Takeout adds real-time history export (would replace yt-dlp for this)
- The EJS runtime requirement is removed (would simplify yt-dlp setup)

## Related

- [[notebooklm-cli-operational-gotchas]] — auth, cookies, bulk-add patterns
- [[nlm-to-wiki-optimization-opportunities]] — 3-worker ceiling, multi-profile
- [[youtube-transcript-extraction-techniques]] — transcript extraction (next step after URL extraction)
- nlm-bulk-ingest — the clustering + batch-add skill that consumes URL lists
- [[concurrent-cdp-auth-contention]] — if running concurrent extractions
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
