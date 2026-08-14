---
title: "how can I find and download videos and transcripts from odyssee, rumble, and other similar providers and platforms?"
date: "2025-12-21"
mode: "COPILOT"
uuid: "123436bb-1331-492c-a8a6-2ad88be4bf38"
entry_count: 13
---

## Human

how can I find and download videos and transcripts from odyssee, rumble, and other similar providers and platforms?

## Assistant

yt-dlp serves as the most reliable command-line tool for downloading videos from Odysee, Rumble, BitChute, and similar platforms like BitTube, with support for subtitles where available.  Online downloaders and desktop apps provide simpler GUI alternatives for occasional use.  Transcripts are limited natively but can be extracted via subtitles or third-party AI tools post-download.[1][2][3][4][5][6][7][8]

## Command-Line Method (yt-dlp)
Install yt-dlp via pip (`pip install yt-dlp`) or download the binary from GitHub, then use it in PowerShell or terminal—ideal for your automation workflows.[9][10]

- Copy the video URL from Odysee or Rumble.
- Run `yt-dlp <URL>` for video download in best quality.
- Add `--write-subs --write-auto-subs` for subtitles/transcripts (VTT/SRT format if available).[11][12]
- For playlists/channels: `yt-dlp <channel_URL>`.
- Batch scripting: Create PowerShell loops over URL lists for multi-agent video processing pipelines.[13][5]

Platforms confirmed: Odysee, Rumble, BitChute, and 1000+ others per supported sites list.[14][15]

## Online Downloaders
Paste video URLs into free web tools for quick MP4 downloads up to 1080p/4K without installs.[16][1]

- Odysee: expertstool.com/odysee-video-downloader or pastedownload.com.[17][1]
- Rumble: videoproc.com downloader (1-click) or videodubber.ai/rumble/video-downloader.[2][16]
- Others (BitChute): savethevideo or y2bs online tools.[18][19]

Limitations: No native transcripts; max resolution varies; ads/popups common.[3]

## Desktop Software
Use cross-platform apps for batch downloads and format conversion, suiting your video analysis setups.[20][21]

| Tool                  | Platforms Supported          | Key Features                  |
|-----------------------|------------------------------|-------------------------------|
| VideoProc Converter AI | Odysee, Rumble, 1000+ sites | 1-click, subtitles, 4K MP4   |
| 4K Video Downloader   | Rumble, Vimeo alternatives  | Playlists, high-res, no ads  |
| Cisdem Video Converter| Odysee, BitChute            | Batch, audio extraction      | [20][2][3]

## Transcript Extraction
Few platforms offer built-in transcripts; use yt-dlp for subs or AI tools for speech-to-text.[4][6]

- yt-dlp `--write-subs` grabs available captions as text files.[11]
- Post-download: Feed videos to NotebookLM or local Whisper models via Python for full transcripts.
- Rumble-specific: instaskript.com/rumble-transcription (AI, 3 free/day).[6]

Respect copyrights and terms of service for personal use only.[16]

## Human

Best tools to batch download videos from Odysee and Rumble
How to extract high quality video files from blockchain based platforms
Ways to download automatic transcripts from video hosting sites
How to preserve original metadata when downloading videos
Command line tools for downloading from decentralized platforms like LBRY Odysee

## Assistant

yt-dlp stands out as the premier command-line tool for batch downloading high-quality videos from Odysee, Rumble, and LBRY/Odysee blockchain content, with robust support for metadata preservation and subtitles.  For blockchain platforms like Odysee (built on LBRY), yt-dlp extracts original files directly from decentralized sources without transcoding losses.  Automatic transcripts rely on available subtitles, supplemented by post-processing tools.[1][2][3][4][5][6][7][8][9]

## Batch Download Setup
Install yt-dlp (`pip install yt-dlp` or GitHub binary) and ffmpeg for merging/post-processing, then batch via text files or playlists.[10]

- Create `urls.txt` with one Odysee/Rumble URL per line (channels/playlists auto-expand).
- Run `yt-dlp --batch-file urls.txt -f bestvideo+bestaudio --merge-output-format mp4`.
- Odysee channels: Handles up to 1000+ videos; use `--flat-playlist` for lists only.[3][4]
- Rumble playlists: Improved extraction for bulk.[2]

PowerShell script example for automation:
```
Get-Content urls.txt | ForEach { yt-dlp $_ }
```

## High-Quality Blockchain Extraction
Odysee/LBRY stores originals on blockchain; yt-dlp fetches untranscoded versions via claim IDs.[11][9]

- Use `yt-dlp "@channel:claim_id"` for direct blockchain pulls.
- Specify `-f best` or `-f "best[height<=1080]"` for quality control without HD bloat.
- Avoid Odysee web downloader for originals—use yt-dlp or LBRY Desktop for full fidelity.[6][8]

## Transcript Downloads
Few sites auto-generate transcripts; yt-dlp grabs subtitles as proxies (SRT/VTT).[5][7]

- Command: `yt-dlp --write-auto-subs --write-subs --sub-langs all --embed-subs <URL>`.
- Converts to text: `ffmpeg -i video.vtt transcript.txt`.
- No native Odysee/Rumble transcripts—pipe to Whisper: `yt-dlp <URL> --exec 'whisper %o'`.[12]

## Metadata Preservation
Embed original title, uploader, thumbnails, and chapters with post-processing flags.[13][14]

| Flag                  | Purpose                              | Example Usage |
|-----------------------|--------------------------------------|---------------|
| `--embed-metadata`   | Title, desc, tags into MP4/MKV      | Full embed   |
| `--embed-thumbnail`  | Preserve cover art                  | With ffmpeg  |
| `--parse-metadata`   | Custom fields (e.g., from JSON)     | Advanced     |
| `--remux-video mp4`  | Container without re-encode         | Lossless     | [13]

Re-apply to existing files: `yt-dlp --postprocessor-args "ffmpeg:-i input.mp4 -i input.meta -map 0 -map_metadata 1 output.mp4"`.[14]

## Alternatives
- **FastLBRY Terminal**: CLI specialized for LBRY/Odysee batch/channel syncs.[8]
- **Media Downloader**: GUI wrapper for yt-dlp playlists.[1]
- Self-hosted: Integrate into multi-agent via LiteLLM proxy for video pipelines.[10]

## Human

Compare yt dlp and Media Downloader for bulk Odysee downloads
How to download entire Odysee playlists with yt dlp
Best ffmpeg options to keep original video quality
How to embed subtitles and transcripts with yt dlp
Preserve LBRY Odysee metadata when downloading videos

## Assistant

yt-dlp excels for bulk Odysee downloads with superior customization and LBRY protocol support, while Media Downloader offers a user-friendly GUI wrapper around yt-dlp for easier playlist management.  Both handle entire Odysee playlists effectively, but yt-dlp provides direct blockchain access for original quality.  Embed subtitles via yt-dlp flags and preserve metadata with post-processing to maintain LBRY/Odysee details like claim IDs.[1][2][3][4][5][6][7]

## yt-dlp vs Media Downloader
Media Downloader simplifies yt-dlp via GUI for bulk Odysee, supporting subscriptions and concurrent downloads up to 4+ (configurable).[2][5]

| Feature              | yt-dlp (CLI)                     | Media Downloader (GUI)          |
|----------------------|----------------------------------|---------------------------------|
| Bulk Odysee Playlists| Native `--playlist-items all`   | "Get List" then batch download [5] |
| Concurrency         | `--concurrent-fragments 16`     | Default 4, unlimited option    [2] |
| Customization       | Full (formats, metadata)        | yt-dlp presets, less granular  |
| Odysee Rate Limits  | `--sleep-interval 60` for 429 errors | Auto-throttling recommended   [1] |
| Best For            | Automation/scripts (your workflows) | Quick GUI bulk without CLI    |

yt-dlp wins for advanced LBRY preservation; Media Downloader for non-technical bulk.[2]

## Download Full Odysee Playlists
Paste channel/playlist URL into yt-dlp; it auto-expands all videos (up to 1000+ with pagination).[4][8]

- Basic: `yt-dlp "https://odysee.com/@channel:playlist"`.
- Entire channel: `yt-dlp "@channel:b" --download-archive archive.txt` (skips duplicates).[8]
- Rate limit fix: `yt-dlp --playlist-random --sleep-interval 5 --max-sleep-interval 60 <URL>`.[1]
- PowerShell batch: `Get-Content odysee_urls.txt | ForEach { yt-dlp $_ --yes-playlist }`.

## Preserve Original Quality (FFmpeg)
Use yt-dlp's format selection with FFmpeg remuxing—no re-encoding for lossless extraction from LBRY blockchain.[9][4]

- Best original: `yt-dlp -f "bestvideo[ext=mp4]+bestaudio/best" --merge-output-format mp4 --remux-video mp4`.
- No re-encode: `--postprocessor-args "ffmpeg:-c copy -avoid_negative_ts make_zero"`.
- AV1/VP9 passthrough: `-f "bestvideo[vcodec~^avc|vp9|av01]+bestaudio" --recode-video mp4` only if needed. [10][11]

Avoid `-f best` alone for VP9 webm issues in editors.[11]

## Embed Subtitles/Transcripts
yt-dlp downloads and embeds available auto-subs (SRT/VTT) into MP4/MKV containers during merge.[6][12][13]

- Command: `yt-dlp --write-auto-subs --sub-langs en --embed-subs --embed-metadata <URL>`.
- List first: `yt-dlp --list-subs <URL>`.
- Convert VTT to text: `--write-subs --sub-format srt --convert-subs srt`.
- Bulk: Add to playlist commands; auto-deletes temp subs post-embed.[6]

Odysee/Rumble subs limited; use Whisper post-download for full transcripts.[14]

## Preserve LBRY/Odysee Metadata
Capture claim IDs, uploader, blockchain hashes via yt-dlp's metadata embedding from LBRY protocol.[15][7][4]

- Full preserve: `yt-dlp --embed-metadata --embed-thumbnail --parse-metadata "title:%(uploader)s - %(title)s" --add-metadata`.
- LBRY-specific: Downloads include `claim_id`, `permanent_url` in JSON/info.json; embed with `--embed-chapters`.
- Re-apply to files: `yt-dlp --paths temp_dir:. --embed-metadata existing_video.mp4`.
- Output template: `-o "%(uploader)s/%(upload_date)s - %(title)s.%(ext)s"` retains hierarchy.[8]

## Human

Best settings to avoid 429 errors when downloading Odysee in bulk
yt dlp command to download entire Odysee channel recursively
How to use external downloader ffmpeg with yt dlp for Odysee
ffmpeg flags to preserve original codecs and timestamps during merge

## Assistant

yt-dlp handles Odysee 429 errors through sleep intervals and request limits, essential for bulk channel downloads exceeding 1000 videos.  Full recursive channel downloads use playlist expansion with archive tracking to resume safely.  Pair with FFmpeg external downloader and copy flags for lossless merges preserving LBRY codecs/timestamps.[1][2][3][4][5]

## Avoid 429 Errors (Bulk Odysee)
Odysee rate-limits aggressively; add these flags to throttle requests across sessions.[6][1]

- `--sleep-interval 5 --max-sleep-interval 60`: Random sleeps 5-60s between videos.
- `--limit-rate 500K --concurrent-fragments 1`: Caps speed/fragments to mimic human use.
- `--extractor-retries 3 --fragment-retries 3`: Retries on 429 without flooding.
- Full safe command: `yt-dlp --sleep-interval 5 --max-sleep-interval 60 --download-archive archive.txt <channel>`.[2]

Update yt-dlp nightly (`yt-dlp -U`) for Odysee extractor fixes.[1]

## Full Channel Recursive Download
Downloads all videos/pages from `@channel:b` claim, skipping duplicates via archive.[5]

- Basic: `yt-dlp "@channel:b" --yes-playlist --download-archive channel.txt`.
- With quality/metadata: `yt-dlp "@channel:b" -f "bestvideo+bestaudio/best" --embed-metadata --embed-subs --download-archive channel.txt`.
- PowerShell loop for multiple: `Get-Content channels.txt | ForEach { yt-dlp $_ --sleep-interval 10 --download-archive ./archive/$_ }`.

Handles pagination automatically; resume anytime.[7][5]

## External FFmpeg Downloader
Forces FFmpeg for Odysee streams (M3U8/DASH) via `--external-downloader ffmpeg`, improving resume/stability over native.[3][4]

- Command: `yt-dlp --external-downloader ffmpeg --external-downloader-args "ffmpeg:-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 2" <URL>`.
- For merges: Auto-uses FFmpeg post-download; specify `--ppa "ffmpeg:-http_seekable 0"`.
- Odysee benefit: Handles blockchain fragments reliably.[4]

## FFmpeg Merge Flags (Preserve Codecs/Timestamps)
Use `-c copy` for no-reencode passthrough of VP9/AV1 from LBRY originals.[8][9]

| Flag Combo                          | Purpose                              |
|-------------------------------------|--------------------------------------|
| `-c:v copy -c:a copy`              | Copy video/audio codecs lossless    |
| `-avoid_negative_ts make_zero`     | Fix timestamps without drift        |
| `-fflags +genpts`                  | Generate PTS for seamless merge     |
| `-map 0:v:0 -map 1:a:0`            | Select best video/audio streams     | [8]

yt-dlp integration: `--postprocessor-args "ffmpeg:-c copy -avoid_negative_ts make_zero" --merge-output-format mkv`. Retains original timestamps/metadata.[10]

## Human

Stagger downloads with delays and retries in yt dlp
Use aria2c as external downloader with yt dlp for parallelism
Configure retries and backoff to avoid HTTP 429 in scripts
Set up proxy rotation or Tor with yt dlp to bypass rate limits
Combine --download-archive with resumable partial files strategy

## Assistant

yt-dlp staggers downloads via exponential backoff sleeps and configurable retries to handle Odysee 429 errors during bulk operations.  aria2c enables multi-connection parallelism per video while respecting rate limits.  Proxy rotation or Tor bypasses IP bans, combined with --download-archive for resumable partials ensuring no data loss.[1][2][3][4][5][6]

## Anti-429 Settings (Delays/Retries)
Throttle aggressively with random sleeps and backoff; retries respect server hints.[7][8]

- `--sleep-interval 10 --max-sleep-interval 120`: 10-120s random pauses between videos.
- `--extractor-retries 5 --retry-sleep exponential`: Backoff on 429 (doubles each try).
- `--fragment-retries 3 --abort-on-unavailable-fragments`: Stops partials, retries fragments safely.[9][10]
- Full: `yt-dlp --sleep-interval 10 --max-sleep-interval 120 --extractor-retries 5 --download-archive archive.txt <channel>`.

PowerShell: `yt-dlp ... --sleep-requests 1 --sleep-interval 5` for finer control.[1]

## aria2c External Downloader
Install aria2c, then parallelize fragments (16x speed) without sequential bottlenecks.[2][11]

- Command: `yt-dlp --external-downloader aria2c --external-downloader-args "aria2c:-j 16 -x 16 -s 16 -k 1M -c" <URL>`.
- `-j 16`: 16 connections; `-c`: Resume partials; `-x 16`: Max connections per server.
- Odysee: Pairs with `--concurrent-fragments 1` to avoid playlist-level overload.[4]
- Resume: aria2c auto-continues .aria2 partials via `-c`.[11]

## Proxy/Tor Rotation
Rotate IPs via script or services to evade Odysee bans; Tor for free anonymity.[3][5]

- Single proxy: `--proxy [REDACTED]:port` or `socks5://127.0.0.1:9050` (Tor).
- Rotation script (PowerShell):
  ```
  $proxies = @("proxy1:port", "proxy2:port")
  foreach ($url in Get-Content urls.txt) {
    $proxy = $proxies[($i++ % $proxies.Count)]
    yt-dlp --proxy "http://$proxy" $url --sleep-interval 15
  }
  ```
- Tor setup: `tor` service + `--proxy socks5h://127.0.0.1:9050`; renew identity via `ControlPort`.[5]

Use rotating proxy services for bulk.[12][3]

## Archive + Resumable Partials
--download-archive tracks completed URLs; combine with -c/--no-part for safe partial resumes.[13][14]

| Strategy                  | Flags                              | Benefit |
|---------------------------|------------------------------------|---------|
| Archive + Partials       | `--download-archive arc.txt -c`   | Resumes fragments, skips completes [13] |
| No Partials (Safe)       | `--no-part --download-archive`    | Full files only, no .part risks |
| Abort on Fail            | `--abort-on-unavailable-fragments --download-archive` | Prevents partial archive entries [13] |
| aria2c Resume            | `--external-downloader aria2c -c --download-archive` | Multi-thread partial recovery [11] |

Run identical command to resume; cleans .part on success.[15]

## Human

How to implement exponential backoff in yt dlp scripts
Best aria2c options for fragment parallelism with yt dlp
How to rotate proxies automatically for yt dlp downloads
Example wrapper script to cycle proxies per request
How to detect and handle HTTP 429 responses in yt dlp logs

## Assistant

yt-dlp implements exponential backoff natively via `--retry-sleep exponential`, but scripts enhance it with custom delays and 429 detection from verbose logs.  aria2c excels for fragment parallelism with 16-32 connections per video.  Wrapper scripts in PowerShell/Python automate proxy cycling from lists/services, resuming via --download-archive.[1][2][3][4][5]

## Exponential Backoff in Scripts
Use `--retry-sleep exponential` (doubles delay per retry) plus script-level sleeps; parse logs for 429 via grep/Select-String.[6][7]

- Native: `--extractor-retries 10 --retry-sleep exponential --sleep-interval 5 --max-sleep-interval 300`.
- PowerShell detection:
  ```
  $output = & yt-dlp -v $url 2>&1
  if ($output -match "HTTP Error 429") { Start-Sleep (2 ** $retryCount); $retryCount++ }
  ```
- Python wrapper:
  ```python
  import subprocess, re, time
  retry = 0
  while retry < 10:
      result = subprocess.run(['yt-dlp', url], capture_output=True, text=True)
      if re.search(r'HTTP Error 429', result.stderr): time.sleep(2 ** retry); retry += 1
      else: break
  ```

## Optimal aria2c Options
`-x 16 -s 16 -j 16` balances speed/stability for Odysee fragments; add `-c` for resumes.[3][8]

- Full: `--external-downloader aria2c --external-downloader-args "aria2c:-x 16 -s 16 -j 16 -k 1M -c --summary-interval=10 -d %(outtmpl)s"`.
- High parallelism: `-x 32` for gigabit; `--min-split-size 1M` avoids small chunks.
- With yt-dlp: `--concurrent-fragments 4` + aria2c for hybrid speed.[3]

## Automatic Proxy Rotation
Load proxies from file/JSON; cycle per video/channel via script args `--proxy`.[9][10]

- List format (`proxies.txt`): `[REDACTED]:port` one per line.
- yt-dlp-proxy tool: Auto-finds/tests free proxies, runs like `yt-dlp-proxy <args>`.[4][5]
- Rotating service: `--proxy http://gateway:port` (auto-rotates on auth).[9]

## Proxy Cycling Wrapper Script
PowerShell example cycles proxies per URL, with backoff/429 handling for your Windows 11 setup.[11][4]

```
$proxies = Get-Content proxies.txt
$urls = Get-Content urls.txt
$retryCount = 0
foreach ($url in $urls) {
    $proxy = $proxies[$script:i % $proxies.Count]; $script:i++
    $output = & yt-dlp --proxy $proxy --sleep-interval 10 --download-archive archive.txt -v $url 2>&1
    if ($output -match "HTTP Error 429") {
        Start-Sleep (2 ** $retryCount); $retryCount = [math]::Min(10, $retryCount + 1)
        --$script:i  # Retry same proxy
    }
}
```

Python equivalent uses `itertools.cycle(proxies)` in loop.[12]

## Detect/Handle 429 in Logs
Enable `-v`/`--verbose`; grep "HTTP Error 429" in post-process or real-time.[13][1]

| Method              | Command/Logic                     | Action on Match |
|---------------------|-----------------------------------|-----------------|
| Native Retry       | `--extractor-retries 10 --ignore-errors` | Auto-backoff [2] |
| Log Parse (PS)     | `Select-String "429"`            | Sleep + retry |
| `--dump-json`      | Pre-check endpoints              | Skip bad URLs |
| Script Wrapper     | `if stderr.contains('429')`      | Proxy switch + exp sleep [7] |

Combine with `--no-clean-infojson` for debug persistence.[1]

## Human

any repos that do what I'm asking about already regarding non-youtube platforms?

## Assistant

Several GitHub repos provide pre-built yt-dlp wrappers with proxy rotation, aria2c integration, exponential backoff, and 429 handling tailored for non-YouTube platforms like Odysee/Rumble/BitChute.  These automate bulk channel downloads from rate-limited/decentralized sites without custom scripting.[1][2][3][4][5]

## Proxy Rotation Repos
Dedicated tools test/find proxies and cycle them per video for Odysee bulk.[4][5]

| Repo                          | Features                              | Platforms Focus     |
|-------------------------------|---------------------------------------|---------------------|
| MrGrample/yt-dlp-proxy-windows-fix | Auto-tests free proxies, Windows PS script, 429 backoff | Odysee/Rumble [4] |
| Petrprogs/yt-dlp-proxy       | Proxy finder + yt-dlp wrapper, rotation per request | Non-YouTube bulk [5] |
| High-bandwidth proxies topic | yt-dlp examples with rotating high-speed proxies | Video archiving [2] |

Run: `git clone https://github.com/MrGrample/yt-dlp-proxy-windows-fix && ./yt-dlp-proxy.ps1 --channel "@user:b"`.[4]

## Full yt-dlp Wrappers
Combine aria2c, backoff, archives for non-YouTube automation.[6][7]

- **RobertHue/yt_dlp_wrapper**: Script wrapper with retries, proxy lists, log parsing for 429; supports Odysee channels.[7]
- **alexwlchan.net yt-dlp-wrapper**: Personalizable PS/Python with exponential sleep, aria2c args.[6]
- **yt-dlp-proxy tools**: Embed aria2c (`-x 16`), `--download-archive`, custom backoff.[5]

## Platform-Specific Tools
Odysee/LBRY-focused with rate-limit smarts.[3][1]

- yt-dlp issues track Odysee 429 fixes; use nightly builds.[3]
- No single "ultimate" repo, but combine yt-dlp-proxy + aria2c setup from DataHoarder scripts.[8]

Clone MrGrample's for your Windows/PowerShell setup—covers 90% of needs out-of-box.[9][4]

## Human

List repos that integrate yt dlp with aria2c for many sites
Show projects that add proxy rotation to yt dlp for non YouTube sites
Find repos handling HTTP 429 across multiple extractors
Search for examples using yt dlp with impersonate targets in codebases

## Assistant

Several GitHub repos integrate yt-dlp with aria2c for multi-site downloads (including Odysee/Rumble/BitChute), add proxy rotation for non-YouTube rate limits, handle 429 retries across extractors, and use `--impersonate` in codebases.[1][2][3]

## yt-dlp + aria2c Multi-Site Repos
These wrap yt-dlp/aria2c for bulk from 1000+ sites with parallelism.[2][3][4]

| Repo                  | Key Features                          | Sites Supported |
|-----------------------|---------------------------------------|-----------------|
| yutijang/M-Dl        | GUI for aria2c + yt-dlp, torrent too | All yt-dlp (Odysee/Rumble+) [2] |
| deniscerri/ytdlnis   | Android app, aria2c multi-thread     | Full yt-dlp sites [4] |
| JunkFood02/Seal      | Parallel aria2c fragments            | YouTube/non-YouTube [3] |

## Proxy Rotation for Non-YouTube
Scripts cycle proxies per video/channel to bypass Odysee/Rumble 429s.[5][6][7]

- **MrGrample/yt-dlp-proxy-windows-fix**: Auto-tests free proxies, Windows PS, Odysee focus.[6]
- **Petrprogs/yt-dlp-proxy**: Rotation + best-proxy finder for Rumble/BitChute.[8]
- Batch examples in yt-dlp issues: `--max-downloads 100` per proxy.[5]

## 429 Handling Across Extractors
Repos enhance yt-dlp's native backoff for multi-extractor retries.[9][10]

- **yt-dlp core issues (#9427, #7143)**: Requests reattempt 429 instead of skip.[10][9]
- **RobertHue/yt_dlp_wrapper**: Log parsing + exp backoff for all sites.[11]
- **MrGrample/yt-dlp-proxy**: Built-in 429 detection/proxy switch.[6]

## Impersonate Target Examples
Codebases using `--impersonate` (e.g., `chrome110`) to evade blocks.[12][13]

- **yt-dlp/yt-dlp** (core): `yt-dlp --impersonate chrome --list-impersonate-targets`.[1][12]
- **yt-dlp issues (#10422)**: Vimeo/Rumble impersonate fixes.[13]
- Wrappers like Seal/ytdlnis embed `--impersonate browser` in configs.[3][4]

Clone MrGrample/yt-dlp-proxy-windows-fix for your PowerShell/video pipeline—covers aria2c, proxies, 429 for Odysee/Rumble.[1][6]

## Human

How can I know which of those repos is worth looking at for coding ideas?

## Assistant

Focus on a few signals that map to what you care about (non‑YouTube, rate limits, automation) and quickly filter everything else.

## 1. Check repo scope and targets
Open the README and look for explicit mentions of:
- Non‑YouTube sites: “Odysee”, “Rumble”, “BitChute”, “LBRY”, “alt platforms”.[1][2]
- Rate limiting: “429”, “Too Many Requests”, “throttling”, “rate limit”.[3][4][5]
- Network tricks: “proxy rotation”, “Tor”, “residential proxies”.[6][7]

If a repo talks only about “YouTube playlists” and never mentions other extractors or 429s, skip it for your use‑case.

## 2. Inspect commit recency and activity
Use the main repo page and Insights to gauge whether ideas are current:
- Recent commits: active within the last 6–12 months.[8][9]
- Issues/PRs: look for open discussions about Rumble/Odysee/BitChute, aria2c, proxies.[5][10]
- Stars vs. maintenance: a small but recently updated repo is more useful than a popular abandoned one.[11][12]

Discard anything that has not touched network/429/proxy logic since yt‑dlp added `--impersonate` and newer retry handling.[13][14]

## 3. Look at how yt‑dlp is invoked
Search the repo for `yt-dlp` in code/workflows:
- Good signs:
  - Uses `--external-downloader aria2c` with tuned args (`-x`, `-s`, `-j`, `-c`).[9][15]
  - Uses `--retry-sleep exponential`, `--sleep-interval`, `--max-sleep-interval`, `--extractor-retries`.[4][14]
  - Includes `--download-archive`, custom `-o` templates, and metadata/subtitle flags.
  - Has logic around `HTTP Error 429` strings or exit codes in wrapper scripts.[16][17]
- Weak signs:
  - One‑liner `yt-dlp <URL>` with no error handling or delays.
  - Hard‑coded to YouTube formats and assumptions.

You can scan this quickly via GitHub search (`t` + search in repo or `/yt-dlp/` references).[18]

## 4. Evaluate proxy/rotation strategy
For proxy‑centric repos (like the proxy wrappers):[7][6]
- Prefer:
  - Clear separation of concerns: “proxy pool management” vs. “download orchestration”.
  - Configurable proxy lists (file/env/CLI), not hard‑coded.[6]
  - Logic that limits downloads per IP and switches on failure/429.
- Avoid:
  - Blindly rotating proxies on every request (wastes good IPs).
  - No handling of dead proxies or health checks.

If their code just wraps `--proxy $RANDOM` inside a simple loop with no feedback from yt‑dlp logs, it is useful as a minimal example but not architectural inspiration.

## 5. See how they handle 429 and errors
Look in issues and code for 429 references:[14][17][16]
- Good patterns:
  - Treat 429 as a signal to:
    - Sleep with exponential backoff.
    - Switch proxy or back off for that host.
    - Mark that URL as “deferred” rather than failed.
  - Use `--ignore-errors` judiciously and compensate with log/JSON tracking.
- Bad patterns:
  - `--ignore-errors` alone with no logging.
  - No differentiation between 404, 403, 429, and transient network errors.

Repos that explicitly mention “429 handling across multiple extractors” or discuss it in issues are prime sources for design ideas.[19][14]

## 6. Distinguish GUI apps from automation scaffolding
For coding ideas you probably want:
- Wrapper scripts (Python, PowerShell, Go, etc.) that:
  - Read URLs/channels from files or APIs.
  - Orchestrate concurrency, proxies, retries.
  - Persist state beyond what `--download-archive` does.
- GUI/mobile projects are still useful, but mostly for:
  - How they expose yt‑dlp options safely.
  - Their internal “job queue” and worker patterns.[20][21]

If the repo is mainly UI plumbing around a single `yt-dlp` call, treat it as reference for UX, not backend logic.

## 7. Use a short “triage” workflow
For each candidate repo from earlier lists:
1. **Open README**: confirm non‑YouTube scope + rate-limit/proxy keywords.
2. **Check last commit**: within the past year.[8][9]
3. **Search for `yt-dlp` calls**: inspect flags and error handling.
4. **Search for `proxy`, `aria2c`, `429`, `impersonate`**: see if they match your needs.[22][23][24][13]
5. If it passes 1–4, bookmark it as “architecture source”; otherwise mark as “example/snippet only”.

If you want, the next step can be: list 3–5 specific repos from the ones already mentioned and annotate them with “high‑value for architecture” vs “snippet‑level only” so you can prioritize where to read the source first.

## Human

list 3–5 specific repos from the ones already mentioned and annotate them with “high‑value for architecture” vs “snippet‑level only” so you can prioritize where to read the source first.

## Assistant

For your use case (non‑YouTube, rate limits, proxies, aria2c, automation), these are the most relevant picks from what came up so far.

## 1. MrGrample/yt-dlp-proxy-windows-fix – **High‑value for architecture**
Windows‑focused wrapper that discovers and tests proxies, then runs yt‑dlp through them, targeting 429/rate‑limit issues.[1]
Why it is high‑value:
- Has an end‑to‑end flow: proxy discovery → health checks → yt‑dlp invocation.[1]
- Encodes retry and proxy selection logic rather than just a one‑liner around `--proxy`.
- Good reference for how to structure a “manager script” around yt‑dlp for Odysee/Rumble‑like constraints.[1]

What to read:
- Proxy test/selection functions.
- How it builds yt‑dlp command lines and handles errors.

## 2. Petrprogs/yt-dlp-proxy – **High‑value for architecture**
General script for finding and using the best proxies for yt‑dlp, intended to work across many sites, not just YouTube.[2]
Why it is high‑value:
- Focused on proxy pool management and rotation, not UI.[2]
- Shows how to integrate proxy testing, ranking, and rotation with yt‑dlp executions.[2]
- Useful pattern for separating “network strategy” from “download worker”.

What to read:
- Proxy list management and health checking.
- How it decides when to swap proxies and how it passes them into yt‑dlp.

## 3. RobertHue/yt_dlp_wrapper – **High‑value for architecture**
Wrapper designed to orchestrate yt‑dlp runs with additional logic (retries, logging, error handling).[3]
Why it is high‑value:
- Treats yt‑dlp as a worker, adding job management and structured state around it.[3]
- Helpful for thinking about channel/playlist queues, resumability, and log‑based decisions.
- Good blueprint for a more generic “download orchestrator” that you can adapt to Odysee/Rumble.

What to read:
- Job queue / task representation.
- Error and log handling, especially non‑0 exit codes and parsing stderr.

## 4. yutijang/M-Dl – **Snippet‑level only (with a few structural ideas)**
Multi‑downloader that uses aria2c plus yt‑dlp under the hood, mainly focused on UX and combined torrent/http downloading.[4]
Why snippet‑level:
- Primary value is its aria2c + yt‑dlp wiring for multi‑site downloads.[4]
- Good for concrete examples of `--external-downloader aria2c` and tuned arguments.
- Less interesting for your proxy/429/control‑plane concerns.

What to read:
- Where it calls aria2c and how it maps settings to command‑line flags.
- Any abstraction layer over “download backends”.

## 5. deniscerri/ytdlnis (discussion/implementation) – **Snippet‑level only**
Mobile/GUI‑oriented project built on yt‑dlp, with discussions about parallel downloads and download manager behavior.[5]
Why snippet‑level:
- Centered on UX; backend is “one yt‑dlp instance per job” without heavy proxy/rate‑limit logic.[5]
- Still useful for queue/workflow patterns and how they expose yt‑dlp options safely to users.

What to read:
- Download queue and worker management.
- Any config/schema they use to represent yt‑dlp settings.

If you want a minimal starting set: read MrGrample/yt-dlp-proxy-windows-fix and Petrprogs/yt-dlp-proxy first for network/proxy architecture, then skim RobertHue/yt_dlp_wrapper for job orchestration patterns.[3][1][2]

## Human

any other questions I should ask?

## Assistant

A few directions will surface deeper design and implementation ideas than what you have so far.

## 1. Architecture and orchestration
- How do others design a **long‑running downloader service** (daemon/cron or container) around yt‑dlp for multiple sites?[1][2]
- What patterns exist for **job queues and state** (DB vs. flat files vs. `--download-archive`) in open‑source frontends?[3][2]
- How do self‑hosted tools let users **submit URLs/channels via a web UI or API** and map that to yt‑dlp tasks?[2][1]

## 2. Advanced yt‑dlp usage
- How are people using yt‑dlp’s **plugin system and custom extractors/postprocessors** for non‑YouTube platforms?[4][5]
- What are good examples of using `--impersonate`, `--rate-limit`, and `--concurrent-fragments` together for hostile sites?[6][7]
- How do projects structure **config files** for per‑site defaults (Odysee vs. Rumble vs. BitChute)?[8][4]

## 3. Archiving strategy beyond downloading
- What are best practices for **naming, organizing, and tagging** archived videos and transcripts over years?[9][10]
- How do people integrate **checksums, fixity checks, and storage tiers** (fast vs. cold) into video pipelines?[11][9]
- How are transcripts and metadata stored (searchable DB vs. sidecar files) for later retrieval and ML use?[12][9]

## 4. Self‑hosted frontends and APIs
- Which self‑hosted frontends (e.g., youtube‑dl‑server forks, TubeSync‑like tools) already support **non‑YouTube sites**, and how?[1][2]
- How do these tools expose **REST/Web UI** for triggering downloads and monitoring status?[2][1]

## 5. Reliability and observability
- How do serious archives **log, monitor, and alert** on failures across many extractors (429/403/geo blocks)?[13][14]
- What patterns are used for **structured logs/metrics** around yt‑dlp runs (JSON logs, Prometheus, etc.)?[5][15]

If you want, the next step could be: “Given those, propose a concrete architecture for a self‑hosted ‘alt‑platform archiver’ service using yt‑dlp + aria2c + proxy rotation,” and that can be laid out as components plus a minimal MVP task flow.

## Human

Given those, propose a concrete architecture for a self‑hosted ‘alt‑platform archiver’ service using yt‑dlp + aria2c + proxy rotation,” and that can be laid out as components plus a minimal MVP task flow

## Assistant

An effective self‑hosted “alt‑platform archiver” looks like a small distributed system: a web/API front‑end, a job queue, worker processes that wrap yt‑dlp+aria2c, and a proxy/429‑aware network layer.

## Core Components

1. **API + Web UI**
   - Minimal REST API (FastAPI / Express) for:
     - Creating subscriptions (Odysee/Rumble/BitChute channels, playlists, single URLs).
     - Triggering on‑demand downloads.
     - Querying job status and logs.
   - Web UI similar to YTPTube / yt-dlp-web-ui: simple queue view, presets for “alt‑platform archiving,” basic auth.[1][2][3]

2. **Scheduler + Subscription Manager**
   - Cron‑like scheduler (e.g., APScheduler / Celery beat) that:
     - Iterates subscriptions table (channels, playlists, tag searches).[4][5]
     - For each, enqueues a “scan” job that:
       - Runs yt‑dlp in simulate mode with `--force-write-archive` to update seen IDs without downloading everything.[6]
       - Compares against `download_archive` and internal DB to generate download tasks.

3. **Job Queue**
   - Simple queue backed by Redis / Postgres:
     - Job fields: id, URL, site, subscription_id, priority, format_profile, status, retries, last_error.
     - Supports rate‑limited concurrency per site (e.g., `max_concurrent_odysee=1`, `max_concurrent_rumble=2`).

4. **Download Workers (yt‑dlp + aria2c)**
   - Workers pull jobs and spawn yt‑dlp with:
     - `--external-downloader aria2c --external-downloader-args "aria2c:-x 16 -s 16 -j 16 -k 1M -c"` for fragment parallelism.[7][8]
     - `--download-archive /archives/<site>.txt` shared per site.[6]
     - Site‑aware presets: trusted Odysee/Rumble flags, `--impersonate` targets where helpful.[9][10]
   - Worker parses exit code and stderr to:
     - Detect 429/403/5xx and decide on backoff or proxy rotation.[11][12]

5. **Proxy / Network Layer**
   - Proxy pool service (could wrap MrGrample/yt-dlp-proxy/ytp‑dl ideas):[13][14][15]
     - Stores proxies with health/status (OK, throttled, dead).
     - Exposes “get next proxy for site X” and “report result (success/429/error)” APIs.
     - Optionally integrates Tor or commercial rotating proxies.[16][17][18]
   - Worker’s yt‑dlp invocation always includes `--proxy <chosen_proxy>` if pool returns one.

6. **Storage + Metadata Index**
   - Filesystem layout:
     - `/archive/<site>/<channel>/<upload_date>-<slug> [id].ext`
   - DB (SQLite/Postgres) columns:
     - video_id (site‑specific), site, channel, title, upload_date, duration, file_path, transcript_path, checksum, first_seen, last_checked, status.[19][20]

7. **Observability**
   - Structured logs (JSON) from workers capturing:
     - job_id, site, url, proxy_id, exit_code, stderr_snippets, 429 flags.
   - Optional Prometheus exporter: jobs/sec, errors by site, 429 count, proxy health.

## Network / 429 Handling Design

**At yt‑dlp level (per job):**
- Always use:
  - `--retry-sleep exponential --extractor-retries 10` for internal backoff.[12][21]
  - `--sleep-interval 1 --max-sleep-interval 30` between items in a playlist‑job.[22]
- For aria2c:
  - `-x 16 -s 16 -j 16 -c` for parallel/resumable fragments, tuned per bandwidth/site.[8][7]

**At worker level (over jobs):**
- If stderr contains `HTTP Error 429` or similar:
  - Mark the proxy as “throttled” in proxy pool.
  - Put the job back into the queue with:
    - `available_at = now + backoff_delay`, where backoff uses \(2^{attempt}\) capped (e.g., 5–30 min).
  - Increase job.retry_count.

**At scheduler level:**
- Rate‑limit jobs per site (e.g., do not run more than N concurrent Odysee jobs).
- Optional global “cool‑down” if a site crosses a 429 threshold in the last X minutes.

## Proxy Rotation Strategy

- Proxy pool table: id, address, type (HTTP/SOCKS5), region, last_success, last_429, failure_count.[14][15]
- Selection:
  - Per job, choose a proxy with:
    - `failure_count < threshold`, `last_429` older than some cooldown.
  - If none, either:
    - Fall back to no proxy (local IP) or
    - Use a rotating gateway (e.g., residential API).[16]
- Feedback:
  - On job success: increment success counter, decay failure_count.
  - On 429: update last_429, bump failure_count.
  - On network error: bump failure_count; disable proxy temporarily after N errors.

This mirrors patterns in proxy‑based tools like ytp‑dl and the proxy wrappers you looked at.[15][13][14]

## Minimal MVP Task Flow

**Goal:** single‑node service, no fancy GUI, but with scheduling, queue, yt‑dlp+aria2c, `--download-archive`, and simple proxy rotation.

1. **Data model (e.g., Postgres)**
   - `subscriptions`: id, url, site, schedule_cron, enabled.
   - `jobs`: id, subscription_id, url, site, status, retries, next_run_at, proxy_id, last_error.
   - `proxies`: id, address, status, failure_count, last_429.

2. **CLI / Web endpoint to add a subscription**
   - Input: channel/playlist URL for Odysee/Rumble.
   - System infers site from URL and inserts `subscriptions` row.

3. **Scheduler loop (e.g., every 10–15 min)**
   - For each enabled subscription:
     - Run yt‑dlp in simulate mode with `--force-write-archive` + `--download-archive site_archive.txt` to discover new IDs without redownloading.[6]
     - Generate one job per new video (URL built from ID), status `pending`.

4. **Worker loop**
   - Fetch next `pending` job where `next_run_at <= now` and site concurrency limit not exceeded.
   - Get proxy from pool (or `None`).
   - Build yt‑dlp command:
     - Base flags:
       - `--external-downloader aria2c --external-downloader-args "aria2c:-x 16 -s 16 -j 16 -k 1M -c"`
       - `--download-archive /archives/<site>.txt`
       - `--retry-sleep exponential --extractor-retries 10 --fragment-retries 5`
       - Site‑specific `--impersonate` if needed.[23][9]
     - Add `--proxy <proxy>` if selected.
   - Spawn process, capture stdout/stderr.
   - If success:
     - Mark job `completed`, record file_path (from output template).
     - Update proxy stats.
   - If fail:
     - If 429 detected: update proxy as throttled, schedule job with `next_run_at = now + backoff(retries)`, increment retries.
     - If transient network error: similar but shorter backoff.
     - If permanent error (404, removed): mark job `failed_permanent`.

5. **Basic status UI / CLI**
   - List jobs by site/status.
   - View last error/log snippet for debugging pipeline behavior.
   - Show simple metrics: “Completed today by site”.

***

If you want, next step can be: a concrete FastAPI + Redis/Python worker skeleton (file/module outline and key functions) that matches this architecture, tuned specifically for Odysee/Rumble (format presets, impersonate defaults, archive paths).

## Human

Define required telemetry and logging for the archiver service
Design data model and directory structure for archived content
Specify proxy rotation strategy and proxy health checks
Outline aria2c integration and session management details
Describe subscription and feed polling mechanism for channels

## Assistant

For a robust alt‑platform archiver, define telemetry, storage, proxy, downloader, and subscription behavior explicitly so you can evolve it safely.

## Telemetry and logging

Capture enough detail to debug per‑video failures, rate limits, and proxy behavior, without drowning storage.

**Per job (video) log fields**:[1][2]
- job_id, subscription_id, site (odysee, rumble, bitchute, …), URL.
- start_time, end_time, duration.
- worker_id / host.
- yt‑dlp exit_code, aria2c exit_code.
- detected_error_class (none, network, 429, 403, 404, extractor, ffmpeg).
- proxy_id (or “local”), impersonate_target (e.g., chrome120), format_selected (audio+video).[3][4]
- bytes_downloaded, final_file_path, transcript_path.

**Per process log lines:**
- Structured JSON per event:
  - `"event": "job_started" | "job_finished" | "job_retried" | "proxy_banned" | "429_detected"`.
  - Include `job_id`, `site`, `proxy_id`, `attempt`, `backoff_seconds`.
- Capture stderr snippets:
  - First and last N lines of yt‑dlp/aria2c stderr per job, tagged with event.
  - Normalize common strings (“HTTP Error 429”, “Too Many Requests”, “Connection reset”) to error_class.[5][6]

**Metrics (for Prometheus/Grafana later)**:[7][1]
- Counters:
  - `jobs_started_total{site}`, `jobs_completed_total{site}`, `jobs_failed_total{site,error_class}`.
  - `rate_limit_events_total{site}`, `proxy_429_events_total{site,proxy_id}`.
- Gauges:
  - `jobs_in_queue{site}`, `jobs_in_progress{site}`.
  - `active_proxies{site,status}`.
- Histograms:
  - `job_duration_seconds{site}`.
  - `download_bytes{site}`.

## Data model and directory structure

Aim for a model that supports many sites and allows later search/ML on transcripts.

**Database tables (e.g., Postgres)**:[8][9]

`sites`
- id, name (odysee, rumble, bitchute), base_url.

`channels`
- id (UUID), site_id, external_id (e.g., Odysee channel claim), url, title, uploader_name, last_polled_at, enabled.

`subscriptions`
- id, channel_id or arbitrary url, type (`channel`, `playlist`, `single`), schedule_cron, quality_profile, created_at, enabled.[10]

`videos`
- id, site_id, channel_id (nullable), external_id (per‑site video id/claim), url.
- title, description (short snippet or hash), duration, upload_date.
- status (`new`, `queued`, `downloading`, `completed`, `failed_permanent`).
- first_seen_at, last_checked_at.

`artifacts`
- id, video_id, type (`video`, `audio`, `thumbnail`, `transcript`, `metadata`).
- file_path (relative), format (mp4, mkv, srt, vtt, json), size_bytes, checksum, created_at.

`jobs`
- id, video_id, subscription_id, site_id.
- status (`pending`, `running`, `completed`, `failed`).
- attempt_count, last_error, next_run_at, worker_id, proxy_id.

`proxies`
- id, address, type (http, socks5), region, last_success_at, last_429_at, failure_count, status (`healthy`, `cooldown`, `dead`).[11][12]

**Directory layout**:[13][8]
- Root: `/archive`
  - `/archive/<site>/@<channel_slug_or_id>/`
    - `YYYY/YYYY-MM-DD/` (optional date bucket)
      - `<upload_date> - <sanitized_title> [<external_id>].mp4`
      - `<upload_date> - <sanitized_title> [<external_id>].info.json`
      - `<upload_date> - <sanitized_title> [<external_id>].en.srt`
      - `<upload_date> - <sanitized_title> [<external_id>].thumb.jpg`

Example full path:
- `/archive/odysee/@SomeChannel/2025/2025-03-14 - My Video Title [lbry_claim_id].mp4`

Configure yt‑dlp `-o` to match this pattern and keep `.info.json` to sync DB fields later.[14][15]

## Proxy rotation and health checks

Use a small service (or module) that is the single source of truth for proxies.

**Proxy scoring model**:[12][16][11]
- Maintain per‑proxy stats:
  - success_count, failure_count, last_429_at, last_network_error_at, last_used_at.
- Reliability score example:
  - Start at 1.0; subtract 0.2 for each recent network failure; subtract 0.5 for recent 429; slowly decay penalties over time.

**Selection algorithm:**
- For a job for site S:
  - Filter proxies with `status = healthy` and `last_429_at` older than N minutes for S.
  - Sort by reliability score and `last_used_at` (least‑recently used first).
  - If no healthy proxies:
    - Either fall back to no proxy (local IP) or a rotating gateway.[16][17]
- Return chosen proxy_id + address.

**Health updates:**
- On job success:
  - Increment success_count, maybe reduce failure_count.
- On 429:
  - Update last_429_at, increment failure_count, set status to `cooldown` for a cooldown window; per‑site if needed.[18][5]
- On network error (timeout, connect error):
  - Increment failure_count; if over threshold, mark `dead` until manual or periodic recheck.

**Background health checker:**
- Periodic job that:
  - Tests proxies against lightweight endpoints or HEAD requests.
  - Moves `cooldown`/`dead` back to `healthy` if they pass checks.

## aria2c integration and session management

aria2c is the external downloader for fragment‑level parallelism and resume.

**Invocation pattern**:[19][20][21]
- yt‑dlp flags:
  - `--external-downloader aria2c`
  - `--external-downloader-args "aria2c:-x 16 -s 16 -j 16 -k 1M -c --summary-interval=10"`
- Meaning:
  - `-x 16`: max connections per server.
  - `-s 16`: number of splits.
  - `-j 16`: concurrent downloads (per aria2c process).
  - `-k 1M`: piece size.
  - `-c`: continue downloads.

**Session/partial management**:
- Let aria2c manage its `.aria2` partials; ensure workers use stable temp directories per job (e.g., `/tmp/archiver/<job_id>`).
- On success:
  - yt‑dlp/aria2c removes partials; worker moves final files into archive tree.
- On failure:
  - Keep partials and allow re‑run with same command; aria2c `-c` resumes.[22]
- For long paths / Windows quirks, keep paths shorter and use `--paths` or `--no-mtime` as needed.[21]

**Concurrency:**[4][23]
- Globally limit worker concurrency per site; aria2c handles intra‑job concurrency.
- Optionally expose per‑site profiles:
  - Odysee: slightly lower `-x`/`-j` to reduce 429s.
  - Rumble: more aggressive concurrency if tests show it tolerates it.

## Subscription and feed polling

Goal: “subscribe” to channels/playlists across alt platforms and keep them synced.

**Subscription model**:[24][10]
- `subscriptions` row per:
  - Odysee channel URL, Rumble channel URL, BitChute channel, or any playlist/search feed if available.
- Each subscription has:
  - site_id, url, type, schedule_cron, quality_profile, enabled.

**Polling mechanism:**
- Scheduler loop (e.g., every 5–15 minutes):
  - For each enabled subscription:
    - Run yt‑dlp in metadata‑only/simulate mode:
      - Example:
        - `yt-dlp --skip-download --get-id --get-title --get-url --ignore-errors <subscription_url>`
      - Or `--dump-json` per entry and parse.[1][14]
    - For each discovered external_id:
      - If not in `videos` table (or `download_archive`):
        - Insert `videos` row (status `new`).
        - Create `jobs` row (status `pending`).
    - Update subscription.last_polled_at.

**Download archive interplay**:[25][26]
- Maintain per‑site `--download-archive` file (flat text of video IDs).
- Poller can optionally call yt‑dlp with:
  - `--download-archive <site>.txt --skip-download --force-write-archive`
  - This updates the archive with seen IDs; you then cross‑check DB to avoid duplicates.

**Quality profiles:**
- Define named profiles in config (e.g., `original_like`, `1080p_max`, `audio_only`) that translate to yt‑dlp `-f` selectors per site.[15][14]
- Subscription references a profile, worker expands it into actual flags.

***

With these pieces defined, you can now implement a small FastAPI + worker service or a set of Python modules that follow this contract, knowing exactly what to log, how to store outputs, and how network/proxy/aria2c/subscriptions interact.
