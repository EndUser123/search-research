---
title: "Here is some cli output for a youtube video discovery and transcript/audio download project.  I find the output rather m"
date: "2026-01-08"
mode: "COPILOT"
uuid: "21691996-e1f4-4a9d-9e1d-5491a9015639"
entry_count: 1
---

## Human

Here is some cli output for a youtube video discovery and transcript/audio download project.  I find the output rather messy.  Do you have any suggestions to make it more usable?
Loaded environment variables from P:\projects\yt-fts\.env
[07:50:56] [QUOTA] Computing strategy...
[INFO   ] Loaded 3539 channels from database
[07:50:56] [QUOTA]  AGGRESSIVE mode | 0/40,000 used | 40,000 remaining (100.0%)
[INFO   ] Starting batch download for: C:\Users\brsth\AppData\Local\Temp\tmp9z0xunmo_channels.txt
YouTube Batch Downloader for yt-fts
[07:50:56] [LOAD] C:\Users\brsth\AppData\Local\Temp\tmp9z0xunmo_channels.txt
[07:50:56] [LOAD]   Raw:     3539 lines
[07:50:56] [LOAD]   Filter:  3539 valid
[07:50:56] [LOAD]   Clean:   3538 channels (1 dupes removed)
  Fail-fast: No

Configuration:
  Input: C:\Users\brsth\AppData\Local\Temp\tmp9z0xunmo_channels.txt
  Channels loaded: 3538
  Parallel worker threads: 4
  Mode: ThreadPoolExecutor (single process)
  Language: en
  Browser cookies: firefox
  Delay between channels: 60.0s
[07:50:56] [AUTO-ADJUST] Video jobs auto-adjust enabled (starting at 2)

 Using 4 parallel worker threads
Ready to process 3538 channels in parallel

✓ All migrations up to date
[07:50:56] [START] Initializing 4 worker threads...
📊 Quota: >Key 1: 10,000 remaining | Key 2: 10,000 remaining | Key 3: 10,000 remaining | Key 4: 10,000 remaining
🧵 [4 workers] Processing 3538 channels...
[07:50:56] [PROCESS] Starting [https://www.youtube.com/channel/UCFig7skuwYrCIGy0t](https://www.youtube.com/channel/UCFig7skuwYrCIGy0t)...
[07:50:56] [PROCESS] Starting [https://www.youtube.com/channel/UCQhvDZeUrxPq9p3Sk](https://www.youtube.com/channel/UCQhvDZeUrxPq9p3Sk)...
[07:50:56] [PROCESS] Starting [https://www.youtube.com/channel/UC1weYqfDgX0ALlNOS](https://www.youtube.com/channel/UC1weYqfDgX0ALlNOS)...
[07:50:56] [PROCESS] Starting https://www.youtube.com/channel/UC_x36zCEGilGpB1m-...
No new videos to download
[07:53:54] [PROCESS] Starting [https://www.youtube.com/channel/UCwmf8kPLoppCmp0V5](https://www.youtube.com/channel/UCwmf8kPLoppCmp0V5)...
  ✓ [1/3538] [https://www.youtube.com/channel/UCFig7sk](https://www.youtube.com/channel/UCFig7sk)...
No new videos to download
[07:54:08] [PROCESS] Starting [https://www.youtube.com/channel/UC0C-17n9iuUQPylgu](https://www.youtube.com/channel/UC0C-17n9iuUQPylgu)...
  ✓ [2/3538] [https://www.youtube.com/channel/UCwmf8kP](https://www.youtube.com/channel/UCwmf8kP)...
No new videos to download
[07:54:28] [PROCESS] Starting [https://www.youtube.com/channel/UCLSW9SNdisXSBkdMR](https://www.youtube.com/channel/UCLSW9SNdisXSBkdMR)...
  ✓ [3/3538] ETA 69h 33m [https://www.youtube.com/channel/UCQhvDZe](https://www.youtube.com/channel/UCQhvDZe)...
PS P:\projects\yt-fts>

## Assistant

A few concrete ideas, from smallest change to bigger re-think.

### 1. Normalize the log structure

Right now there’s a mix of styles (emojis, CLI banners, prose). I’d standardize to something like:

`[TIME] [LEVEL] [COMPONENT] message`

Examples:

- `[07:50:56] [INFO ] [INIT ] Loaded 3539 channels from database`
- `[07:50:56] [INFO ] [QUOTA] AGGRESSIVE | used 0/40,000 | remaining 40,000 (100%)`
- `[07:50:56] [INFO ] [DL   ] Worker 1 starting channel UCFig7sk…`
- `[07:53:54] [DONE ] [DL   ] [1/3538] UCFig7sk… (no new videos)`

Consistent columns = much easier to scan or grep.

### 2. Collapse the “header” into a compact block

Your “Configuration” + initial info is great but verbose. You could print it as a single compact block once:

```text
=== yt-fts batch run =====================================
Env:    P:\projects\yt-fts\.env
Input:  tmp9z0xunmo_channels.txt
Chan:   3538 (1 duplicate removed)
Workers:4 (ThreadPoolExecutor)
Lang:   en    Cookies: firefox    Delay: 60s
Quota:  mode=AGGRESSIVE  used=0/40000  rem=40000 (100%)
=========================================================
```

This replaces:

- Multiple `[LOAD]` lines
- Separate “Configuration:” section
- The emoji quota line

### 3. Shorten channel identifiers

Full channel URLs make each line huge. Print:

- A short ID or index
- The URL only once (or on demand)

Example:

```text
[07:50:56] [START] [CH#0001] UCFig7sk…  (https://www.youtube.com/channel/UCFig7sk...)
[07:53:54] [DONE ] [CH#0001] status=no-new-videos
```

Or drop the URL from subsequent lines and just keep the channel key.

### 4. Reduce noise messages

“No new videos to download” repeated as a separate line is noisy. Options:

- Inline it with the completion line:
  - `… [DONE] [CH#0001] no-new-videos`
- Or print only when there *are* new videos, and keep “no-new” silent unless verbose mode is on.

Similarly, `Using 4 parallel worker threads`, `Ready to process 3538 channels in parallel`, and `[START] Initializing 4 worker threads...` are three lines that say nearly the same thing; compress into one:

```text
[07:50:56] [INFO ] [INIT ] 4 workers ready for 3538 channels
```

### 5. Introduce log levels + verbosity flag

Right now everything is effectively INFO. Add levels:

- `DEBUG` (very chatty: thread assignments, precise URLs)
- `INFO` (default: run summary, per-channel results)
- `WARN` (retries, minor issues)
- `ERROR` (hard failures)

Then support `--verbose` / `--quiet`:

- `--quiet`: only WARN/ERROR + final summary
- default: INFO+WARN+ERROR
- `--debug`: everything

### 6. Periodic progress line instead of per-channel spam

With 3.5k channels, per-channel lines get unwieldy. Keep the key ones, but also emit a periodic summary every N seconds:

```text
[07:55:00] [STAT] processed=120/3538  new_videos=14  no_new=106  failures=0  ETA=69h 30m
```

Then your detailed per-channel logs can be limited or pushed to DEBUG.

### 7. Better aligned ETA and counters

This line:

`✓ [3/3538] ETA 69h 33m https://...`

could be made more regular, e.g.:

```text
[07:54:28] [DONE ] [CH#0003] [3/3538] ETA=69h33m result=no-new-videos
```

Consistent bracket/spacing makes scanning with your eyes (and parsing with tools) nicer.

### 8. Colorize by level (optional)

Since you’re on Windows 11, using colorama/rich in Python or similar:

- INFO: default
- DONE/SUCCESS: green
- WARN: yellow
- ERROR: red
- HEADER: dim cyan

This makes failures and key events pop without changing structure.

***

If you’d like, paste a small section of the logger code and I can sketch a concrete “before/after” refactor with a proposed format (e.g., using Python `logging` with custom formatter or rich’s `Console` + `Progress`).
