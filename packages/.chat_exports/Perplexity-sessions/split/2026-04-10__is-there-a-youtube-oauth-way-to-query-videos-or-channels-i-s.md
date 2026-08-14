---
title: "Is there a YouTube OAuth way to query videos or channels?  I seem to recall there's some other API that's not RSS and no"
date: "2026-04-10"
mode: "COPILOT"
uuid: "4aef9f30-cc6f-4ca5-843e-db17f7134175"
entry_count: 4
---

## Human

Is there a YouTube OAuth way to query videos or channels?  I seem to recall there's some other API that's not RSS and not YouTube API v3. It's something public.

## Assistant

You're likely thinking of **Invidious API**. It's a free, open-source YouTube frontend with a public JSON API that doesn't require OAuth or API keys. You can query channels, videos, playlists, and search directly without authentication.[1][2]

## Invidious API Overview

Invidious provides read-only access to public YouTube data via REST endpoints. Key endpoints include:[1]

- `GET /api/v1/videos/:id` — Get video details (title, description, view count, comments, captions)
- `GET /api/v1/channels/:channelId` — Query channel info
- `GET /api/v1/search` — Search for videos, channels, playlists with filtering by date, duration, features
- `GET /api/v1/playlists/:playlistId` — Fetch playlist contents
- `GET /api/v1/trending` — Get trending videos by category/region
- `GET /api/v1/comments/:videoId` — Retrieve comments sorted by top or new

All responses are JSON and require no authentication.[1]

## No OAuth needed

Unlike YouTube Data API v3 which requires OAuth for most operations, Invidious is explicitly designed for public data access without keys or credentials. You make simple HTTP GET requests to any public Invidious instance.[3][1]

## Practical consideration

Public Invidious instances are community-maintained. Two reliable options noted in 2024: **rss.youtube.com** (Node.js service on GitHub Pages) and **invidious-feed.net** (Debian-based with daily security updates). You could also self-host the Invidious project if you need guaranteed uptime.[4][3]

For production use, YouTube Data API v3 with a simple API key is more stable than relying on third-party instances, but Invidious is perfect for quick prototyping or when you need zero authentication overhead.

## Human

What protocols do these files use?

## Assistant

Based on the files, here are the protocols these TypeScript services use:

## HTTP/HTTPS

The primary protocol is **HTTP/HTTPS** for REST API calls. Specifically: - `youtubeService` fetches video metadata via **oEmbed API** using `https://www.youtube.com/oembed?url=...&format=json`[1]
- Requests are made with `fetch()` standard Node.js API[1]
- All YouTube URLs are normalized to HTTPS (e.g., `https://www.youtube.com/watch?v=...`)[2][3]

## JSON-RPC style (Gemini API)

The system communicates with **Google Gemini API** using HTTP POST with JSON payloads:[1]

```
ai.models.generateContent(model, contents, config)
```

Responses are parsed as JSON with `responseMimeType: application/json`. Error handling includes JSON parsing, validation, and AI-assisted repair when responses are malformed.[1]

## Rate-Limiting Protocol

The codebase implements sophisticated **backpressure/throttling** via two request queues:[4][5]

- **Primary queue** (`mainRequestQueue`): Dynamic delays starting at 4.5s, scaling down on success (×0.95) but backing off to 61s on HTTP 429/quota errors[5]
- **Thumbnail queue** (`requestQueue`): Fixed 1,100ms delay (~54 requests/minute)[4]

Both use async Promise-based queuing with exponential backoff logic.[5]

## No WebSocket/gRPC

There's no WebSocket, gRPC, or streaming protocol—this is pure REST + JSON request/response.

**Key insight**: The system treats rate-limiting as a **protocol-level concern**, not just error handling. Quota errors (429, `resourceExhausted`) trigger hard backoff, while success automatically optimizes throughput. This is API rate-limit negotiation built into the request chain itself.[5]

## Human

How do those files determine YouTube channels or YouTube videos on those channels?

## Assistant

The files use **three distinct methods** to identify YouTube videos and channels:

## 1. Regex Extraction (URL Parsing)

The system extracts video and playlist IDs using regex patterns:[1][2]

**Video ID extraction** — 11 character pattern from multiple URL formats:[2][1]
```
/(?:[?&]v=|\/embed\/|\/shorts\/|youtu\.be\/)([\\w-]{11})/
```

This captures from `watch?v=`, embedded videos, YouTube Shorts (`youtu.be/`), and shorts URLs.[1][2]

**Playlist ID extraction** — Captures list parameter:[2][1]
```
/[?&]list=([\\w-]+)/
```

Both raw IDs are then reconstructed into canonical URLs like `https://www.youtube.com/watch?v=VIDEO_ID`.[1][2]

## 2. oEmbed API Metadata

For **video titles, descriptions, and channel names**, the system calls YouTube's oEmbed endpoint:[3]

```
https://www.youtube.com/oembed?url={encoded_video_url}&format=json
```

This returns metadata including:[3]
- `title` — video title
- `author_name` — **channel name**
- `author_url` — **channel URL** 
- `thumbnail_url` — video thumbnail

The files cache oEmbed results (`oEmbedCache`) to avoid redundant API calls.[3]

## 3. Gemini AI Extraction (Playlist Parsing)

For **playlist contents**, the system uses Google Gemini to parse HTML:[3]

1. Passes playlist URL to Gemini with a prompt requesting: original URL, HTML `<title>` tag, and first video URL[3]
2. Gemini extracts first video from each playlist[3]
3. Results are cached in `playlistMetaCache`[3]
4. Then oEmbed is called on the first video to get channel metadata[3]

## Channel Resolution Gap

**Critical limitation**: These files **cannot directly resolve channel names from video IDs alone**. The system extracts channel info only via oEmbed's `author_name` field, which requires the full video URL or video data already fetched. There's a function `findVideoIdByDetails(title: string, channel: string)` that asks Gemini to reverse-lookup a video ID given a title and channel name, but this is **forward-only** — given video, get channel; not given channel, get all videos.[3]

To enumerate all videos on a channel, this system would need to either:
- Use YouTube Data API v3 (which you mentioned avoiding)
- Use Invidious API (which supports `/api/v1/channels/{channelId}` endpoints)
- Have Gemini fetch the channel page HTML and parse video listings

The current architecture is **video-centric**, not channel-centric.[3]

## Human

Any new protocols from these files?

## Assistant

No new network protocols. These are **React/Solid.js UI components** (`.tsx` files) with no direct API calls or network I/O.[1][2][3][4][5][6][7][8]

## What's in these files

**UI-only layer** — These components handle user interactions and state rendering:[3][6][7]
- **SourceUrlsPanel**: Textarea for pasting YouTube URLs, file upload (`.txt`), drag-drop support[6]
- **DiscoveredItemsPanel**: Displays fetched videos/playlists with search/filtering, selection checkboxes[3]
- **StagedVideoListItem**: Individual video cards with status badges ("Detecting...", "Analyzing...", "Completed")[7]
- **DiscoveredItem**: Video/playlist preview with link to YouTube[4]

## Data flows (no new protocols)

The UI components receive data via props and invoke callback handlers (`handleUrlSubmit`, `handleStageSelectedItems`, etc.). These callbacks wire to the service layer (`youtubeService`, `urlParsingService`) you saw earlier — still HTTP/HTTPS + Gemini JSON-RPC, rate-limited queues.[9][10][6][3]

**File drag-drop** is handled client-side with native DOM events, not a custom protocol:[6]
```tsx
onDragOver, onDragLeave, onDrop
```

No WebSocket, gRPC, or streaming here — pure event-driven state management (Solid.js signals/stores).
