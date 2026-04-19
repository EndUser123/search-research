---
created: '2026-04-11'
sources:
- C:\Users\brsth\Downloads\_History (HL)      │ ❌ Blocked │ YouTube restricts.md
summary: ''
tags: []
---

<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# "History (HL)      │ ❌ Blocked │ YouTube restricts access"

How can I access my youtube history programatically via claude code?

The YouTube Data API v3 does **not** expose watch history — it's a known, intentional restriction. But there are several solid workarounds you can use from Claude Code. Here's the full breakdown:

***

## Why YouTube History is Blocked

YouTube's Data API v3 deliberately omits watch history endpoints. The `Activities` resource once partially exposed this, but Google deprecated history-related activity types. There's no official API endpoint for it.[^1_1]

***

## Your Best Options (Ranked by Practicality)

### 1. Google Takeout Export (Best for Bulk Analysis)

Google Takeout provides your full watch history as structured JSON/HTML:

- Go to **myaccount.google.com/data-and-privacy** → "Download your data" → select **YouTube and YouTube Music** → choose **History** → JSON format
- The export gives you `watch-history.json` with timestamps, video IDs, and titles
- **Claude Code workflow:**

```python
import json

with open("watch-history.json") as f:
    history = json.load(f)

# Each entry has: titleUrl (video URL), title, time, subtitles (channel info)
video_ids = [
    entry["titleUrl"].split("v=")[-1]
    for entry in history
    if "titleUrl" in entry and "watch" in entry.get("titleUrl", "")
]
```

Then batch-fetch metadata via the Data API using those video IDs.

***

### 2. Browser Automation via `youtube-history-scraper` or Playwright

Automate the actual YouTube history page (`youtube.com/feed/history`) using your logged-in browser session:

```python
# Using playwright with persistent browser profile
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch_persistent_context(
        user_data_dir="C:/Users/YOU/AppData/Local/Google/Chrome/User Data",
        channel="chrome",
        headless=False  # use headful to reuse your session cookies
    )
    page = browser.new_page()
    page.goto("https://www.youtube.com/feed/history")
    # scroll and scrape...
```

This reuses your existing Chrome login — no OAuth needed.

***

### 3. YouTube Data API via OAuth (Partial — "Liked" and "Watch Later")

While history itself is blocked, you **can** access related data via OAuth:

```python
# Playlists you can fetch with OAuth:
# - Liked videos (LL)
# - Watch Later (WL)  
# - All your custom playlists

import googleapiclient.discovery

youtube = googleapiclient.discovery.build("youtube", "v3", credentials=creds)

# Liked videos
response = youtube.playlistItems().list(
    part="snippet",
    playlistId="LL",  # Liked Videos
    maxResults=50
).execute()
```


***

### 4. `yt-dlp` with Cookie Extraction (Most Complete Approach)

`yt-dlp` can extract your history if you pass your browser cookies:

```bash
# Export history metadata using cookies from your Chrome session
yt-dlp --cookies-from-browser chrome \
       --flat-playlist \
       -J "https://www.youtube.com/feed/history" \
       > history.json
```

This is the **most powerful** option — works headlessly and integrates cleanly into Claude Code as a subprocess call.

***

### Recommended Stack for Claude Code

Given your setup (Windows 11, PowerShell, Python-first), I'd suggest:

1. **One-time**: Takeout export for historical bulk data
2. **Ongoing**: `yt-dlp --cookies-from-browser chrome` scheduled via a PowerShell task or Claude Code hook to keep a local `history.json` up to date
3. **Enrich**: Feed video IDs into the YouTube Data API v3 to get full metadata (titles, duration, channel, tags, etc.)

This gives you a fully queryable, locally-stored watch history that Claude Code can index, search, and analyze without hitting any API restrictions.

<div align="center">⁂</div>

[^1_1]: https://developers.google.com/youtube/v3/docs

