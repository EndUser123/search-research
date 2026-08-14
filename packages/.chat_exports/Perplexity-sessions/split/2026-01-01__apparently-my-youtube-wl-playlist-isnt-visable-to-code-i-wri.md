---
title: "apparently my youtube wl playlist isn't visable to code I write with the youtube api, even with oauth and a token.  How "
date: "2026-01-01"
mode: "COPILOT"
uuid: "686fb07e-6191-43c9-b799-ee55284e670d"
entry_count: 4
---

## Human

apparently my youtube wl playlist isn't visable to code I write with the youtube api, even with oauth and a token.  How do I enable myself to see it via api?

## Assistant

**The YouTube Data API does not allow access to the Watch Later (WL) playlist programmatically, even with OAuth authentication and a valid token.** This restriction has been in place since September 2016, when Google updated the API to prevent retrieval of Watch Later or Watch History playlists.[1][2][3]

## API Limitations
Requests to `playlistItems.list` or `playlists.list` for the Watch Later playlist return empty lists or errors like `watchLaterNotAccessible` and `playlistOperationUnsupported`.[4][5][6]
The `channels.contentDetails.relatedPlaylists.watchLater` field shows "WL" but cannot retrieve actual details or items.[3][1]

## Alternatives
Use Google Takeout to export your Watch Later data manually as JSON.[7]
For custom playlists, ensure OAuth scopes include `https://www.googleapis.com/auth/youtube.readonly` and use `mine=true` in `playlists.list` to list owned playlists.[1]
Browser automation or scraping remains an unofficial workaround, but violates YouTube's terms.[2]

## Human

really?  there's no clever way other than google takeout?

## Assistant

Actually, there are a few clever workarounds depending on your tolerance for unofficial/semi-unofficial methods:

## Browser Cookie-Based Approach (Cleanest)

**`youtube-unofficial` Python library**  — This accesses YouTube's unofficial endpoints by using your browser cookies (Chrome, Firefox, etc.). No OAuth setup needed beyond logging in to your browser:[1][2]

```python
from youtube_unofficial import YouTubeClient

yt = YouTubeClient('chrome', 'Default')  # Uses your Chrome cookies
videos = yt.print_watch_later()  # Get all WL videos
```

Commands available: `print-watch-later`, `remove-watch-later-video-id`, `clear-watch-later`.  This is MIT-licensed and actively maintained.[1]

## MCP Server Approach (Claude-Compatible)

**Radek's YouTube Watch Later MCP Server**  — Designed specifically for AI assistants but works standalone. Uses proper OAuth refresh tokens (one-time setup), then pulls from YouTube's API via the server's internal logic to work around the restrictions:[3]

- Securely stores refresh tokens in environment variables
- Single tool: `get_watch_later_urls` with configurable timeframe
- Works with Claude and other AI assistants

## Private API / Innertube (Advanced)

**youtubei.js** or reverse-engineered Innertube API calls  — YouTube's internal web client API. Works from Python backends but requires reverse-engineering current client signatures. Riskier from a ToS perspective.[4][5]

## Quick Recommendation for You

Given your automation-focused workflow, I'd try **`youtube-unofficial`** first—it's the simplest and leverages your existing browser login. If you want to integrate with Claude Code or an automated system, the **MCP Server** approach is cleaner long-term since it uses legitimate OAuth flows.

Both sidestep Google's API restrictions while staying within reasonable legal/ethical bounds (unlike web scraping).

## Human

Show me the code in python or typescript to use.  Or both actually.

## Assistant

Here's practical code for both Python and TypeScript to access your Watch Later playlist:

## Python (youtube-unofficial)

**Installation:**
```bash
pip install youtube-unofficial
```

**Basic Usage:**
```python
from youtube_unofficial import YouTubeClient

# Initialize with your browser (Chrome, Firefox, etc.)
# Uses your existing login cookies—no OAuth setup needed
yt = YouTubeClient('chrome', 'Default')

# Get all Watch Later videos
yt.print_watch_later()

# Remove a specific video from Watch Later
yt.remove_video_id_from_playlist('WL', 'dQw4w9WgXcQ')

# Clear entire Watch Later queue
yt.clear_watch_later()
```

**JSON Output (for scripting):**
```python
from youtube_unofficial import YouTubeClient
import json

yt = YouTubeClient('chrome', 'Default')

# Get Watch Later with machine-readable output
# Pipe this to a file or process it
import subprocess
result = subprocess.run(['youtube', 'print-watch-later', '--json'], 
                       capture_output=True, text=True)
videos = [json.loads(line) for line in result.stdout.strip().split('\n')]
print(f"Found {len(videos)} videos in Watch Later")
```

***

## TypeScript (Browser Cookie Approach)

Since there's no direct TypeScript library for the unofficial API, here's a practical Node.js + Puppeteer approach:

**Installation:**
```bash
npm install puppeteer node-fetch
```

**Code:**
```typescript
import puppeteer, { Browser } from 'puppeteer';

interface YouTubeVideo {
  videoId: string;
  title: string;
  channel: string;
}

async function getWatchLaterPlaylist(): Promise<YouTubeVideo[]> {
  let browser: Browser | null = null;
  
  try {
    // Launch browser and navigate to Watch Later
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox']
    });
    
    const page = await browser.newPage();
    
    // Navigate to Watch Later playlist
    await page.goto('https://www.youtube.com/playlist?list=WL', {
      waitUntil: 'networkidle2'
    });
    
    // Auto-scroll to load all videos (YouTube lazy-loads)
    await autoScroll(page);
    
    // Extract video data
    const videos = await page.evaluate(() => {
      const videoElements = document.querySelectorAll('a#video-title-link');
      const results: YouTubeVideo[] = [];
      
      videoElements.forEach((el) => {
        const href = el.getAttribute('href') || '';
        const videoId = new URLSearchParams(href.split('?')[1]).get('v');
        const title = el.textContent || 'Unknown';
        const channel = el.closest('ytd-playlist-video-renderer')
          ?.querySelector('yt-formatted-string.style-scope.yt-simple-endpoint')
          ?.textContent || 'Unknown';
        
        if (videoId) {
          results.push({ videoId, title, channel });
        }
      });
      
      return results;
    });
    
    return videos;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
}

async function autoScroll(page: any): Promise<void> {
  await page.evaluate(async () => {
    await new Promise((resolve) => {
      let totalHeight = 0;
      const distance = 1000;
      const timer = setInterval(() => {
        const scrollHeight = document.documentElement.scrollHeight;
        window.scrollBy(0, distance);
        totalHeight += distance;
        
        if (totalHeight >= scrollHeight) {
          clearInterval(timer);
          resolve(null);
        }
      }, 100);
    });
  });
}

// Usage
(async () => {
  try {
    const videos = await getWatchLaterPlaylist();
    console.log(`Found ${videos.length} videos:`);
    videos.forEach(v => {
      console.log(`- ${v.title} (${v.videoId}) by ${v.channel}`);
    });
  } catch (error) {
    console.error('Error:', error);
  }
})();
```

***

## Recommendation for You

**Go with Python** (`youtube-unofficial`) — it's simpler, already maintained, and perfect for your automation needs. Just run:

```bash
youtube print-watch-later --json > watch_later.jsonl
```

Or pipe it directly into your tools.

**TypeScript** is useful if you need it in a Node environment, but the Puppeteer approach is heavier. If you need TypeScript, consider calling the Python script from Node via child_process instead.

## Human

any repos that use code like that?

## Assistant

Here are the best production repos using similar patterns:

## Best Examples

**1. `longpdo/youtube-dl-watch-later-playlist`**  — Direct Python implementation that downloads Watch Later videos:[1]
```
https://github.com/longpdo/youtube-dl-watch-later-playlist
```
Downloads first 100 videos from your WL playlist using similar scraping logic.

**2. `Sleighs/youtube-playlist-web-scraper`**  — TypeScript Puppeteer scraper for playlists:[2]
```
https://github.com/Sleighs/youtube-playlist-web-scraper
```
Full working example of using Puppeteer to scrape YouTube playlist data—similar to the TypeScript code I showed you.

**3. `fineanmol/Youtube-Video-Uploader-Automation`**  — Production TypeScript + Puppeteer for YouTube automation:[3]
```
https://github.com/fineanmol/Youtube-Video-Uploader-Automation
```
More sophisticated example of handling YouTube authentication and browser automation with Puppeteer. Shows patterns for login, navigation, and element selection.

**4. `Tatsh/youtube-unofficial`**  — The main library repo with examples:[4]
```
https://github.com/Tatsh/youtube-unofficial
```
Full source code of `youtube-unofficial`. MIT licensed, actively maintained, shows all the cookie/auth patterns.

**5. `spyesx/watch-later-gist`**  — Browser console one-liner + shell script:[5]
```
https://gist.github.com/spyesx/27cecbe9483c507b9b098d942e98d62b
```
Quick hack—runs in console to extract Watch Later URLs, pipes to `youtube-dl`. Good for understanding the DOM structure.

**6. `ytmusicapi`**  — Python unofficial API for YouTube Music (similar pattern):[6]
```
https://github.com/sigma67/ytmusicapi
```
If you later want to integrate YouTube Music playlists, this shows the cookie-based auth pattern at scale (450+ stars, actively maintained).

## My Recommendation

Start with `longpdo/youtube-dl-watch-later-playlist`  since it directly solves your problem and the code is simpler. Then reference `Tatsh/youtube-unofficial`  for the full library implementation if you need more features.[1][4]

For TypeScript, `Sleighs/youtube-playlist-web-scraper`  is the closest production example using Puppeteer.[2]
