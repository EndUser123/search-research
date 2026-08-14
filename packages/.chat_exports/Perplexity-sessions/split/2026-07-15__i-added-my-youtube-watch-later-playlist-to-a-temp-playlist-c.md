---
title: "I added my youtube Watch Later playlist to a temp playlist called watch-later-temp.  How can I download the url list?  I"
date: "2026-07-15"
mode: "COPILOT"
uuid: "e3f96524-2308-4ed4-9cb6-d1f80f06e193"
entry_count: 4
---

## Human

I added my youtube Watch Later playlist to a temp playlist called watch-later-temp.  How can I download the url list?  I do have yt-dlp on my windows 11 pc if that helps, or we can use any other method you recommend.

## Assistant

You can export all video URLs from that `watch-later-temp` playlist using yt-dlp’s metadata output and a small script; no manual copying needed.[1]

Below is a minimal, reliable approach tailored for Windows 11 + PowerShell and your existing yt-dlp setup.

## Approach overview

- Use yt-dlp with the playlist URL to dump JSON metadata (no actual downloads).[1]
- Parse that JSON to extract each video’s URL and write them to a text/CSV file.[1]
- This works even for large playlists (your 4,934 videos) as long as YouTube doesn’t hard-block the account/IP.[1]

I’ll give you two concrete variants:

1. Pure PowerShell + yt-dlp CLI.  
2. Python script using yt-dlp’s Python API (closer to your preferred architecture).

***

## Get playlist URL and basics

Your temp playlist URL is:

- `https://www.youtube.com/playlist?list=PLYd3hV748pE0`  (from your current tab).[1]

On Windows 11, you can run yt-dlp from either:

- PowerShell 7 (your usual CLI).
- Command Prompt (if you prefer for testing).

Assumption (medium confidence): yt-dlp is already up to date and has a JS runtime configured for modern YouTube, since you’ve been using it for transcripts and complex formats; if not, you may want to update it first to minimize extraction errors.[2]

***

## Option 1 – PowerShell + yt-dlp CLI

This is the fastest “just get URLs into a file” method.

### Step 1: Dump playlist metadata as JSON

In PowerShell 7:

```pwsh
cd C:\path\to\where\you\want\files

yt-dlp `
  "https://www.youtube.com/playlist?list=PLYd3hV748pE0" `
  --skip-download `
  --flat-playlist `
  --dump-json `
  > playlist.json
```

What this does:  

- `--skip-download` avoids video files; we only want metadata.[2]
- `--flat-playlist` stops yt-dlp from resolving each individual video fully; it returns one item per entry with basic info (id, title, URL). This is lighter and sufficient to build URLs.[2]
- `--dump-json` outputs one JSON object per playlist entry; redirecting to `playlist.json` stores all of them.[2]

Edge cases / assumptions (medium confidence):

- If you see rate-limit or JS errors, you may need your usual JS runtime configuration (`--extractor-args` etc.), but for URL-only extraction it’s often fine without full JS.[2]
- If some entries are private/deleted, they may be missing or have minimal data; that’s expected.[2]

### Step 2: Extract URLs into a text file (PowerShell)

Now parse `playlist.json` and write only URLs:

```pwsh
Get-Content .\playlist.json |
  ForEach-Object {
    $obj = $_ | ConvertFrom-Json
    $obj.url
  } | Set-Content .\playlist_urls.txt
```

Result:

- `playlist_urls.txt` will contain one URL per line like:  
  - `https://www.youtube.com/watch?v=19xCOJxWU0A`  
  - `https://www.youtube.com/watch?v=KftTfxaAqbM`  
  - …up to ~4,934 entries.[1]

If you want CSV with title + URL:

```pwsh
Get-Content .\playlist.json |
  ForEach-Object {
    $obj = $_ | ConvertFrom-Json
    [PSCustomObject]@{
      Title = $obj.title
      Url   = $obj.url
    }
  } | Export-Csv .\playlist_urls.csv -NoTypeInformation -Encoding UTF8
```

Now you have a `playlist_urls.csv` file usable in other tooling.

***

## Option 2 – Python script using yt-dlp API

Since you prefer Python + yt-dlp API for long-term systems, here’s a small script that stays in that pattern.

### Step 1: Install yt-dlp (if needed)

In PowerShell:

```pwsh
python -m pip install -U yt-dlp
```

### Step 2: Python script to dump URLs

Create `export_playlist_urls.py`:

```python
import yt_dlp

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLYd3hV748pE0"
OUTPUT_TXT = "playlist_urls.txt"
OUTPUT_CSV = "playlist_urls.csv"

ydl_opts = {
    "skip_download": True,
    "extract_flat": True,  # flat playlist
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(PLAYLIST_URL, download=False)

entries = info.get("entries", [])

# Write plain URL list
with open(OUTPUT_TXT, "w", encoding="utf-8") as f_txt:
    for e in entries:
        url = e.get("url")
        if not url:
            continue
        f_txt.write(url + "\n")

# Optional: write CSV with title + url
import csv

with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f_csv:
    writer = csv.writer(f_csv)
    writer.writerow(["title", "url"])

    for e in entries:
        url = e.get("url")
        title = e.get("title", "")
        if not url:
            continue
        writer.writerow([title, url])

print(f"Wrote {len(entries)} entries to {OUTPUT_TXT} and {OUTPUT_CSV}")
```

Run it:

```pwsh
python .\export_playlist_urls.py
```

Notes (high confidence):

- `extract_flat=True` gives each entry without resolving full video details, which is efficient and enough for URLs.  
- `entries` is a list of playlist items, each with `url` and `title` (and id, etc.).[2]
- If you later want per-video metadata (upload date, duration, etc.) you can drop `extract_flat` and iterate, but that will be heavier.[2]

***

## Using the URL list for further automation

Once you have `playlist_urls.txt` or `playlist_urls.csv`, you can:

- Feed that list into your transcript/downloader pipeline (yt-dlp API + YTA + Whisper).[3][2]
- Apply “oldest added first” deletion logic if you pair YouTube UI automation (e.g., Selenium/Playwright) with this list and your Watch Later ordering logic.
- Store this snapshot as a “frozen” watch-later backlog for later batch processing.

***

## Confidence and assumptions

- FACT (cited): You can extract playlist entries and URLs using yt-dlp’s `--flat-playlist`/`extract_flat` options and `--dump-json` or API `extract_info`.[2]
- CONSENSUS (high confidence): For large playlists, flat extraction is more robust than resolving each video; rate-limit issues mainly arise when pulling full video details or media.[2]
- SPECULATION: If YouTube introduces stricter JS challenges or auth requirements for large playlists, some entries might fail; however, for unlisted/user playlists like yours, they typically remain accessible via yt-dlp with an up-to-date build. Confidence: medium, based on current 2026 patterns.[2]

***

Would you prefer to standardize on the PowerShell + CLI variant for this, or integrate the Python API version into your existing transcript/export pipeline so this becomes a reusable “export Watch Later snapshot” step?

## Human

It only grabbed 100 urls, but we have 4934 in the playlist.

## Assistant

The 100‑URL cap is coming from yt-dlp’s default playlist page limit, not from YouTube or your script; we need to tell yt-dlp to crawl all pages.[1][2]

Below is a minimal adjustment for both the PowerShell/CLI and Python API variants to get all ~4,934 entries.

***

## Why you only got 100

yt-dlp treats playlists as paginated and, by default, only fetches the first page or a limited number of items unless configured otherwise.[2]

YouTube’s HTML clearly shows the playlist has 4,934 videos, but your current invocation is only returning the first page (≈100 items).[1]

Key assumption (high confidence based on typical behavior):

- You either used `--max-downloads 100`, or more likely you hit yt-dlp’s internal default page size limit when extracting a playlist without extra options.[2]

So we need to explicitly tell yt-dlp:

- “Do not cap playlist items”  
- “Walk all pages until the playlist is exhausted”

***

## Fix for PowerShell + yt-dlp CLI

Change your command to **disable playlist limits** and allow full pagination:

```pwsh
yt-dlp `
  "https://www.youtube.com/playlist?list=PLYd3hV748pE0" `
  --skip-download `
  --flat-playlist `
  --dump-json `
  --playlist-end 0 `
  > playlist.json
```

Key pieces:

- `--playlist-end 0` means “no upper bound, go until the end of the playlist.”[2]
- `--flat-playlist` still uses light entries, but yt-dlp will now follow all pages.[2]
- We still redirect all JSON objects to `playlist.json` and

## Human

PowerShell 7.6.3
Active code page: 65001
PS P:\> cd C:\Users\brsth\Downloads
PS C:\Users\brsth\Downloads> yt-dlp `
>>   "https://www.youtube.com/playlist?list=PLYd3hV748pE0" `
>>   --skip-download `
>>   --flat-playlist `
>>   --dump-json `
>>   > playlist.json
PS C:\Users\brsth\Downloads> yt-dlp `
>>   "https://www.youtube.com/playlist?list=PLYd3hV748pE0" `
>>   --skip-download `
>>   --flat-playlist `
>>   --dump-json `
>>   --playlist-end 0 `
>>   > playlist.json

Usage: yt-dlp [OPTIONS] URL [URL...]

yt-dlp: error: playlist end "0" must be must be greater than or equal to playlist start "1"
PS C:\Users\brsth\Downloads>

## Assistant

The error is because yt-dlp expects `--playlist-end` to be a positive integer ≥ `--playlist-start`, so `0` is invalid. It’s also not the right way to remove the 100‑item cap.[1]

The core issue: your current invocation is effectively limiting to the **first 100 items** in the playlist, even though the HTML clearly shows 4,934 videos.  We want yt-dlp to walk the **entire playlist**, not just the first page.[2]

Below are adjustments that should give you all 4,934 URLs, with minimal changes.

***

## Fix the PowerShell + CLI invocation

### 1. Drop any implicit limit flags

First, confirm you’re not accidentally using any limiting options:

- `--max-downloads`  
- `--playlist-end 100` or similar  
- an old yt-dlp version with a bug around pagination

Your current command:

```pwsh
yt-dlp `
  "https://www.youtube.com/playlist?list=PLYd3hV748pE0" `
  --skip-download `
  --flat-playlist `
  --dump-json `
  > playlist.json
```

is conceptually correct, but yt-dlp is only giving ~100 entries, which suggests a pagination/limit behavior.[1]

### 2. Use explicit playlist range with a large end

Instead of trying `0` (which is invalid), give yt-dlp a very large end index. It will stop at the real playlist end (4,934) anyway.[1]

Try:

```pwsh
yt-dlp `
  "https://www.youtube.com/playlist?list=PLYd3hV748pE0" `
  --skip-download `
  --flat-playlist `
  --dump-json `
  --playlist-start 1 `
  --playlist-end 10000 `
  > playlist.json
```

Here:

- `--playlist-start 1` – start at the first item.[1]
- `--playlist-end 10000` – large upper bound, but yt-dlp will stop at 4,934.[1]

If this works, `playlist.json` should contain one JSON line per playlist entry; a quick check is:

```pwsh
(Get-Content .\playlist.json).Count
```

You want to see **4,934** or very close (minus any deleted/private items).[2]

***

## If you still see ~100 items

If the count is still ~100 after the above, that points to version or playlist extraction behavior.

### 1. Check yt-dlp version

Run:

```pwsh
yt-dlp --version
```

If it’s not recent, update:

```pwsh
python -m pip install -U yt-dlp
```

Newer yt-dlp builds have better playlist pagination and YouTube handling.[1]

### 2. Try non-flat playlist (heavier but more “normal” path)

Sometimes `--flat-playlist` uses a different code path that’s more prone to page caps. You can drop `--flat-playlist` and let yt-dlp resolve each entry fully. It’s slower, but should walk the whole playlist.[1]

```pwsh
yt-dlp `
  "https://www.youtube.com/playlist?list=PLYd3hV748pE0" `
  --skip-download `
  --dump-json `
  --playlist-start 1 `
  --playlist-end 10000 `
  > playlist_full.json
```

Then check the count:

```pwsh
(Get-Content .\playlist_full.json).Count
```

If you get ~4,934 lines, we’re good; you can then extract URLs:

```pwsh
Get-Content .\playlist_full.json |
  ForEach-Object {
    $obj = $_ | ConvertFrom-Json
    $obj.webpage_url  # or $obj.url, depending on structure
  } | Set-Content .\playlist_urls.txt
```

Note: in non‑flat mode, the field is often `webpage_url` rather than `url`.[1]

***

## Python API fallback (more control, same goal)

Given your preference for Python + yt-dlp API, this avoids CLI argument surprises and makes pagination behavior more transparent.

```python
import yt_dlp

PLAYLIST_URL = "https://www.youtube.com/playlist?list=PLYd3hV748pE0"

ydl_opts = {
    "skip_download": True,
    # Try flat first; if it still returns ~100, drop this line
    "extract_flat": True,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    info = ydl.extract_info(PLAYLIST_URL, download=False)

entries = info.get("entries", [])
print("Entries:", len(entries))

urls = []
for e in entries:
    # For flat: e.get("url")
    # For non-flat: e.get("webpage_url")
    url = e.get("url") or e.get("webpage_url")
    if url:
        urls.append(url)

with open("playlist_urls.txt", "w", encoding="utf-8") as f:
    for u in urls:
        f.write(u + "\n")

print("Wrote", len(urls), "URLs")
```

Run this, check the printed `Entries:` count:

- If it’s ~4,934, you’re done.  
- If it’s ~100, remove `"extract_flat": True` and run again; that switches to full extraction.[1]

***

## Confidence and assumptions

- FACT (cited): yt-dlp requires `--playlist-end` ≥ `--playlist-start`, and `0` is invalid.[1]
- CONSENSUS (high confidence): For large YouTube playlists, setting `--playlist-end` to a large number and/or using non-flat extraction is the standard way to force full pagination.[1]
- SPECULATION (medium): Your current 100‑item limit is likely due to either a default cap or an older yt-dlp build; updating and explicit playlist range should resolve it.[1]

***

When you run the updated command with `--playlist-end 10000`, what `Count` do you get for `playlist.json`? If you can paste that number, we can decide whether to keep flat extraction or flip to the Python API path as the long-term solution.

## Human

yes that worked after I updated yt-dlp and used the flat-playlist command again.

## Assistant

Great, that means you now have a full JSON dump for all ~4,934 playlist entries and we can safely turn it into a clean URL list (and optionally title/URL CSV).[1][2]

Below are concise next steps and a couple of useful variants.

***

## Extract URLs from the JSON file

Assuming your successful command was something like:

```pwsh
yt-dlp `
  "https://www.youtube.com/playlist?list=PLYd3hV748pE0" `
  --skip-download `
  --flat-playlist `
  --dump-json `
  > playlist.json
```

You can now extract URLs in PowerShell:

```pwsh
Get-Content .\playlist.json |
  ForEach-Object {
    $obj = $_ | ConvertFrom-Json
    $obj.url
  } | Set-Content .\playlist_urls.txt
```

Result:

- `playlist_urls.txt` contains one video URL per line for the entire playlist snapshot.

Quick sanity check:

```pwsh
(Get-Content .\playlist_urls.txt).Count
```

You should see close to 4,934 (minus any deleted/private entries).[1]

***

## Optional: Title + URL as CSV

If you want something more structured (good for later processing):

```pwsh
Get-Content .\playlist.json |
  ForEach-Object {
    $obj = $_ | ConvertFrom-Json
    [PSCustomObject]@{
      Title = $obj.title
      Url   = $obj.url
    }
  } | Export-Csv .\playlist_urls.csv -NoTypeInformation -Encoding UTF8
```

This gives you:

- `playlist_urls.csv` with columns `Title` and `Url`.

You can open it in Excel, import into Python, or feed into your transcript/downloader pipeline.

***

## Using the URL list going forward

Now that you’ve verified yt-dlp can see all entries for `watch-later-temp`, you can:

- Treat `playlist_urls.txt` as a frozen snapshot of your Watch Later backlog for batch download/transcript work.[2][3]
- Feed it directly into your existing Python/yt-dlp or YTA + Whisper pipeline.  
- Re-run the same flow in future if you want updated snapshots (e.g., weekly).

If you later want richer metadata (duration, upload date, channel, etc.), you can either:

- Switch from `--flat-playlist` to full extraction (`--dump-json` without `--flat-playlist`), or  
- Move to the Python API and call `extract_info` with `extract_flat=False` to capture more fields.[2]

***

Do you want to extend this now to grab extra metadata (e.g., duration, publish date, channel, and maybe “position in playlist”) for use in a more advanced backlog management workflow, or is the URL list enough for your current task?
