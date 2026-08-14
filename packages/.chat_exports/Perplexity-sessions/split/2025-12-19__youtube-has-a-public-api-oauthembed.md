---
title: "youtube has a public api, oauthembed?"
date: "2025-12-19"
mode: "COPILOT"
uuid: "d509efb1-bf8e-43d4-b690-f8b2bbc86be7"
entry_count: 5
---

## Human

youtube has a public api, oauthembed?

## Assistant

Yes, YouTube provides a public Data API (v3) that supports access to public data like videos, playlists, and search results using a simple API key—no OAuth required for read-only public queries.[1][2]

For private user data or write operations (uploads, edits), OAuth 2.0 authentication is mandatory via Google's standard flows.[9][1]

YouTube also offers a separate oEmbed API for embedding public videos, which works without any authentication—just pass a video URL to get embed code.[4]

## Human

How to use YouTube oEmbed for embedding videos

## Assistant

YouTube's oEmbed endpoint allows embedding public videos by fetching embed code via a simple HTTP request, requiring no API key or authentication.[1][2][3]

## Basic Usage
Send a GET request to `https://www.youtube.com/oembed?url=<VIDEO_URL>&format=json` (or XML), where `<VIDEO_URL>` is the full YouTube watch page like `https://www.youtube.com/watch?v=dQw4w9WgXcQ`.[2][3][1]

The response includes an `html` field with a ready-to-use `<iframe>` for embedding.[1][2]

## Example Request and Response
Using JavaScript fetch:
```
fetch('https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=dQw4w9WgXcQ&format=json')
  .then(res => res.json())
  .then(data => document.getElementById('player').innerHTML = data.html);
```
Sample JSON response:
```
{
  "html": "<iframe width=\"480\" height=\"270\" src=\"https://www.youtube.com/embed/dQw4w9WgXcQ?feature=oembed\" ...></iframe>",
  "title": "Rick Astley - Never Gonna Give You Up",
  "provider_name": "YouTube"
}
```


## Parameters
- `format=json` or `xml`: Response format (JSON recommended).[2]
- `maxwidth=480` or `maxheight=270`: Constrains iframe size; YouTube scales responsively.[3]
- `rel=0`: Hides related videos at end (optional, via direct iframe tweaks post-fetch).[4]

Paste the `html` directly into your page for playback.[5][2]

## Human

I thought there was a different one.  you could get video titles and metadata from it.

## Assistant

Yes, YouTube's oEmbed does provide video titles and basic metadata like author, type, and thumbnails alongside the embed HTML—no API key needed.[1][2]

## oEmbed Response Fields
A typical JSON response includes:
- `title`: Video title[2][1]
- `author_name`: Channel name[2]
- `author_url`: Channel URL[2]
- `thumbnail_url` / `thumbnail_width` / `thumbnail_height`: Preview image [ from prior]
- `html`: Embed iframe [ from prior]

Example for `https://www.youtube.com/watch?v=dQw4w9WgXcQ`:
```
{
  "type": "video",
  "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
  "author_name": "RickAstley",
  "author_url": "https://www.youtube.com/user/RickAstley",
  "html": "<iframe ...>",
  "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
}
```
[ from prior][2]

## For More Metadata
Detailed info (description, views, publish date, tags) requires YouTube Data API v3's `videos.list` endpoint with a free API key (public data access, no OAuth).[3][4][1]

Request: `https://www.googleapis.com/youtube/v3/videos?id=VIDEO_ID&key=API_KEY&part=snippet,statistics`[1][7]

## Human

are there other youtube apis that don't need an api key?

## Assistant

YouTube's oEmbed endpoint remains the primary public API that requires no API key, providing basic metadata like titles, author details, thumbnails, and embed HTML for public videos.[11][12][13]

## No Other Keyless APIs
Official YouTube Data API v3 mandates an API key for all endpoints accessing public data such as search, videos.list, or channels—even read-only operations enforce quota tracking and project identification.[1][2][3]

No additional official YouTube APIs exist without keys; alternatives like unofficial scrapers or third-party proxies (e.g., Invidious) carry risks of instability or ToS violations.[4]

## Unofficial Workarounds
- **oEmbed only**: Stick to `https://www.youtube.com/oembed` for title/thumbnail/embed from video URLs.[13][14]
- **Iframe hacks**: Player parameters via `https://www.youtube.com/embed/VIDEO_ID` yield no structured metadata.[15]

For richer data, generate a free API key via Google Cloud Console—it's quick and supports 10,000 units/day.[3][5]

## Human

When to use OAuth versus API key for YouTube API calls

## Assistant

Use an API key for YouTube Data API v3 calls when accessing public data in read-only operations, such as fetching video details, search results, playlists, or channel info—no user-specific access needed.[1][7]

Switch to OAuth 2.0 for private user data (like subscriptions, likes, or analytics) or write actions (uploads, edits, deletions, playlist modifications), as these require user consent and delegated permissions via scopes.[7][1]

## Comparison Table
| Scenario                  | API Key                          | OAuth 2.0 Required              |
|---------------------------|----------------------------------|---------------------------------|
| Public video metadata     | ✅ (e.g., videos.list)          | ❌                              |
| Search public videos      | ✅ (search.list)                 | ❌                              |
| User private playlists    | ❌                               | ✅                              |
| Upload/edit videos        | ❌                               | ✅ (with youtube.upload scope) |
| Channel analytics         | ❌ (if private)                  | ✅                              | [1][7]

Every request needs either an API key or OAuth token; combine them for hybrid apps (key for public reads, OAuth for user writes).[1][7]
