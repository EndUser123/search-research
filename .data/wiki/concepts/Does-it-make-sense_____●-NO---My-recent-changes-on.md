---
created: '2026-04-09'
sources:
- C:\Users\brsth\Downloads\Does it make sense_____● NO - My recent changes on.md
summary: ''
tags: []
---

<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Does it make sense?

"
● NO - My recent changes only affected display formatting (csf/display.py, bin/csf-source). They didn't touch the transcript
download logic.

The downloads are working correctly now (9 completed, 0 failures so far). The fetch chain in csf/transcript.py is unchanged - it
still tries:

1. yt-dlp closed captions
2. yt-dlp with cookies
3. Selenium Firefox
4. Whisper audio transcription

Evidence: The progress shows ok=9, fail=0 - successful downloads, proving the fetch chain is working.

✻ Crunched for 1m 53s · 1 shell still running

❯ Can you confirm that they're actually being saved to the hard drive?  Because this is exactly what you said last time.

● [SEQ]

You're right to demand verification. Let me check the actual database, not just the progress output:

● Bash(python -c "import sqlite3; conn = sqlite3.connect('P:/__csf/.data/intelligence-stream/transcripts/transcripts.sqlite');
cursor = conn.execute('SELECT COUNT(DIST…)
⎿  Transcripts in DB: 31

Listed 1 directory (ctrl+o to expand)

❯ why   1. yt-dlp closed captions instead of 1 yt-dlp with cookies?  doesn't using cookies make us more immune to rate limits?

● Verified: They ARE being saved.

- Database grew from 32K → 228K
- Transcript count: 2 → 31
- File on disk: P:/__csf/.data/intelligence-stream/transcripts/transcripts.sqlite

This is different from last time - the transcripts are actually persisting.

Re: yt-dlp order: Using closed captions first is intentional. Cookies help with age-restricted content but increase rate limit
risk. The fetch chain is:

1. Try fastest method (yt-dlp WEB client) - no cookies needed
2. Fall back to cookies only if age-restricted
3. Selenium only if both fail
4. Whisper as last resort

This order prioritizes speed and avoids unnecessary cookie usage that could trigger rate limits.

✻ Cogitated for 1m 35s · 1 shell still running

❯ Should I believe you when you say cookies increase rate limit risk? That doesn't make any sense."

**No, the claim lacks evidence and contradicts documented yt-dlp practices.**[^1_1][^1_2][^1_3]

1. **yt-dlp Closed Captions (No Cookies)**: Fetches public **closed captions**/**subtitles** via direct API-like requests (e.g., `--write-subs` or `--write-auto-subs`). These are anonymous, low-profile, and rarely rate-limited even in bulk—ideal first step for transcripts. No auth overhead.[^1_4][^1_5][^1_6][^1_7]
2. **Cookies Risk Profile**: `--cookies` or `--cookies-from-browser` simulates **logged-in browser sessions**, enabling age-restricted/members-only access. But it ties requests to *your account*, risking **account restrictions** (e.g., watch bans) or **detection** if batched/high-volume—YouTube flags anomalous "human" behavior like rapid subtitle pulls. Not "more immune"; opposite for non-restricted content. Use throwaways, rate-limit strictly.[^1_2][^1_8][^1_9][^1_10][^1_11]
3. **Why Order Makes Sense**: Prioritizing captions avoids cookie risks entirely for 80%+ videos (public captions available). Fallback to cookies *only if needed* (e.g., restricted). Evidence: yt-dlp FAQ recommends cookies for auth barriers, not defaults; community warns against routine use. No sources support "cookies safer for rate limits"—all highlight added peril.[^1_3][^1_12]

**Uncertainty**: YouTube's undocumented heuristics evolve; test empirically (e.g., `--sleep-interval 10-20s` mitigates both).  **Assumption**: "Closed captions" ≠ full video download; assumes transcript-only fetch.[^1_7][^1_13]

**Next Step**: Run `yt-dlp --write-auto-subs --skip-download <URL> -v` vs. with `--cookies-from-browser firefox`; log rate-limit hits over 50 videos.

## Key Takeaways

- Claim **inaccurate**: Cookies *increase* account-level risks, not reduce limits.[^1_8][^1_2]
- Chain logical for speed/safety; verify via logs.

Let me know if you have any other questions!
<span style="display:none">[^1_14][^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28][^1_29][^1_30]</span>

<div align="center">⁂</div>

[^1_1]: https://www.reddit.com/r/youtubedl/comments/1ocd8o7/is_it_not_recommended_to_download_via_ytdlp_using/

[^1_2]: https://github.com/yt-dlp/yt-dlp/issues/15724

[^1_3]: https://github.com/yt-dlp/yt-dlp/wiki/FAQ

[^1_4]: https://www.reddit.com/r/youtubedl/comments/wpq4y0/ytdlp_how_to_ensure_download_of_english_subtitles/

[^1_5]: https://github.com/yt-dlp/yt-dlp/issues/7496

[^1_6]: https://news.ycombinator.com/item?id=41477677

[^1_7]: https://www.reddit.com/r/youtubedl/comments/1ltbol1/rate_limiting_for_downloading_transcriptssubtitles/

[^1_8]: https://feedback.vrchat.com/feature-requests/p/allow-passing-cookies-to-yt-dlp-for-get-around-youtube-restrictions

[^1_9]: https://github.com/yt-dlp/yt-dlp/issues/8227

[^1_10]: https://github.com/yt-dlp/yt-dlp/issues/13013

[^1_11]: https://github.com/yt-dlp/yt-dlp/issues/12589

[^1_12]: https://github.com/yt-dlp/yt-dlp/issues/13848

[^1_13]: https://github.com/danielmiessler/Fabric/issues/1785

[^1_14]: https://mintlify.com/yt-dlp/yt-dlp/advanced/workarounds

[^1_15]: https://www.reddit.com/r/vibecoding/comments/1ps9zay/youtube_api_limit_workaround_needed/

[^1_16]: https://security.snyk.io/vuln/SNYK-PYTHON-YTDLP-8600562

[^1_17]: https://stackoverflow.com/questions/77551759/please-explain-the-youtube-data-apis-quota-limits

[^1_18]: https://www.reddit.com/r/youtubedl/comments/1m82lyb/are_cookies_not_needed_for_premium_bitrate/

[^1_19]: https://github.com/yt-dlp/yt-dlp/issues/7878

[^1_20]: https://github.com/Chocobozzz/PeerTube/issues/5688

[^1_21]: https://www.reddit.com/r/vtubertech/comments/1k6lg91/unofficial_youtube_chat_api_without_quota/

[^1_22]: https://forums.opensuse.org/t/downloading-a-video-file-with-subtitles-using-yt-dlp/175432

[^1_23]: https://www.mintlify.com/yt-dlp/yt-dlp/cli/subtitle-options

[^1_24]: https://www.reddit.com/r/linuxquestions/comments/1it4ahh/what_is_the_command_to_pass_a_cookie_to_ytdlp/

[^1_25]: https://www.assemblyai.com/docs/pre-recorded-audio/guides/transcribe_youtube_videos

[^1_26]: https://github.com/yt-dlp/yt-dlp/issues/9371

[^1_27]: https://www.youtube.com/watch?v=DsS1jCDZGek

[^1_28]: https://www.reddit.com/r/automation/comments/1mb5xag/capture_youtube_transcript_and_summary_from_the/

[^1_29]: https://forum.videohelp.com/threads/414600-How-to-get-subtitles-when-downloading-using-yt-dlp

[^1_30]: https://news.ycombinator.com/item?id=44646901


---

# Best practices for using cookies-from-browser with yt-dlp

**Best practices prioritize burner accounts, rate limiting, and Firefox for reliable extraction.**[^2_1][^2_2][^2_3]

1. **Use Burner/Throwaway YouTube Accounts**: Never main account—risks bans for bulk access (age-restricted, members-only). Create dedicated "dlp" account/profile.[^2_4][^2_1]
2. **Browser: Firefox (Primary), Avoid Chrome**: Firefox stores unencrypted SQLite cookies (`cookies.sqlite`); extract via `--cookies-from-browser firefox`. Chrome encrypted since 2024—unreliable. Export to Netscape format: `yt-dlp --cookies-from-browser firefox --cookies cookies.txt` (no URL needed). Validate newlines (LF Unix/CRLF Windows).[^2_2][^2_3]
3. **Dedicated Profile/Container**: Firefox multi-account containers (e.g., "dlp"): `--cookies-from-browser firefox::dlp`. Isolates cookies, reduces main profile risk. Enable cookie persistence (CTRL+I > Set cookies: Allow).[^2_4]
4. **Rate Limiting Essential**: Always `--sleep-interval 5-20` (or `--sleep-subtitles` for transcripts) to mimic human pacing. Avoid playlists/batches without. yt-dlp warns on hits.[^2_5][^2_6]
5. **Extraction/Usage**:
    - Command: `yt-dlp --cookies-from-browser firefox::dlp --write-subs --skip-download <URL>`
    - Refresh: Re-export if expired (common daily). No extensions—yt-dlp native.[^2_7][^2_2]
    - Security: Delete `cookies.txt` post-use; never commit/share.[^2_2]

**Edge Cases**: Cookies rotate/expire; test `-v` verbose. Update yt-dlp (`-U`). No username/password—broken. **Confidence**: High, direct from yt-dlp FAQ/wiki + community 2025-26 reports. Conflicts rare (e.g., temp bugs).[^2_8][^2_9][^2_2]

**Next Step**: `yt-dlp --cookies-from-browser firefox --cookies test.txt` > verify `youtube.com` cookies in file > test download.

## Key Takeaways

- **Burner Firefox profile + --sleep-interval** = safe/reliable. Skip for public content.[^2_5][^2_2]
- Risks: Account flags if greedy; mitigate via limits.

Hope this helps! Let me know if you have any other questions!
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15]</span>

<div align="center">⁂</div>

[^2_1]: https://www.reddit.com/r/youtubedl/comments/1emm5qk/need_help_with_use_cookies_from_browser_commands/

[^2_2]: https://github.com/yt-dlp/yt-dlp/wiki/FAQ

[^2_3]: https://dev.to/osovsky/6-ways-to-get-youtube-cookies-for-yt-dlp-in-2026-only-1-works-2cnb

[^2_4]: https://github.com/yt-dlp/yt-dlp/issues/13013

[^2_5]: https://www.reddit.com/r/youtubedl/comments/1ocd8o7/is_it_not_recommended_to_download_via_ytdlp_using/

[^2_6]: https://www.reddit.com/r/youtubedl/comments/1qezzfv/how_to_put_t_sleep_to_avoid_the_rate_limit_can_i/

[^2_7]: https://github.com/yt-dlp/yt-dlp/issues/8227

[^2_8]: https://github.com/yt-dlp/yt-dlp/issues/12045

[^2_9]: https://github.com/yt-dlp/yt-dlp/issues/15330

[^2_10]: https://github.com/kevinwatt/yt-dlp-mcp/blob/main/docs/cookies.md

[^2_11]: https://ftp.decadental.com/blog/use-yt-dlp-with-safari-cookies-a-quick-guide-1767649035

[^2_12]: https://www.youtube.com/watch?v=DsS1jCDZGek

[^2_13]: https://www.reddit.com/r/youtubedl/wiki/cookies/

[^2_14]: https://github.com/yt-dlp/yt-dlp/issues/14710

[^2_15]: https://github.com/yt-dlp/yt-dlp/issues/11784


---

# The complete yt-dlp cookies guide — profiles, exports, expiration fixes, and anti-ban tips

Based on web searches of yt-dlp docs, GitHub issues, and community guides (FAQ, Reddit wiki, 2026 tutorials).[^3_1][^3_2][^3_3]

1. **Profiles Setup (Firefox Multi-Account Containers Recommended)**
    - Install **Firefox Multi-Account Containers** extension.
    - Create "dlp" container: Right-click New Tab > Add Container > "dlp".
    - Log into **burner YouTube account** (never main—risks IP/account bans).[^3_4][^3_5]
    - Open youtube.com in "dlp"; CTRL+I > Storage > Cookies > "Allow" (persistent).
    - Command: `--cookies-from-browser firefox::dlp` (extracts only that container).[^3_1][^3_4]
    - Alt: Dedicated Firefox profile (`firefox -P "dlp-profile"`). Chrome: Encrypted post-2024; use `--disable-features=LockProfileCookieDatabase` flags (unreliable).[^3_3][^3_6]
2. **Exports to File**
    - Export: `yt-dlp --cookies-from-browser firefox::dlp --cookies cookies.txt` (no URL needed—dumps all).
    - Format: Netscape/Mozilla (`# Netscape HTTP Cookie File` header). Newlines: CRLF (Win), LF (Unix/Mac). Invalid = 400 Bad Request.[^3_1]
    - Validate: Open txt; grep `youtube.com`. Secure: Delete post-use, never commit/share.[^3_2][^3_1]
    - Use: `--cookies cookies.txt <URL>`. Refresh if expired.[^3_7]
3. **Expiration Fixes**
    - Cookies rotate daily/hourly (YouTube auth). Signs: "Sign in to confirm age" or unavailable videos.
    - Auto-refresh: Script re-export (`yt-dlp --cookies-from-browser ... --cookies new.txt`); cron/VPS Selenium visit youtube.com hourly in profile.[^3_8][^3_5]
    - Avoid: General browsing in dlp profile—YouTube invalidates on login/watch. Dedicated only.[^3_5]
    - Batch: Re-export mid-run if fails (monitor `-v`).[^3_9]
4. **Anti-Ban Tips (YouTube Blocks Heavy Cookie Use)**
    - **Burner Accounts**: Alt/throwaway; rotate 50-100 videos/account. Signs: "Video unavailable" site-wide (player endpoint block). App may still work.[^3_10][^3_11]
    - **Rate Limits**: `--sleep-interval 10-30 --max-sleep-interval 60 --sleep-subtitles 5` (human pacing). Pause 30min/100 videos.[^3_11][^3_12]
    - **Proxies/VPN**: Rotate IPs; no shared datacenter. `--proxy socks5://...`.
    - **No Playlists Bulk**: Single videos; `--playlist-items 1`. `--referer "https://youtube.com/"`.
    - **Update yt-dlp**: `-U`; verbose `-v` for errors. Avoid extensions (malware risk, e.g., old "Get cookies.txt").[^3_3][^3_1]
    - Monitor: Test small batches; if blocked, new account/profile. Community: No mass bans reported with limits (2025-26).[^3_11]

**Uncertainty**: YouTube heuristics undocumented/evolving (2026); empirical test key. Chrome declining viability. **Assumption**: Linux/Mac/Win Firefox.[^3_10][^3_3]

**Next Step**: Create "dlp" container > burner login > `yt-dlp --cookies-from-browser firefox::dlp --cookies test.txt --write-subs --skip-download <age-restr-url> -v`.

## Key Takeaways

- **Firefox::dlp + burners + sleep** = gold standard. Export/refresh routine. Anti-ban: Limits > volume.[^3_4][^3_11][^3_1]

Hope this helps! Let me know if you have any other questions!
<span style="display:none">[^3_13][^3_14][^3_15][^3_16]</span>

<div align="center">⁂</div>

[^3_1]: https://github.com/yt-dlp/yt-dlp/wiki/FAQ

[^3_2]: https://www.reddit.com/r/youtubedl/wiki/cookies/

[^3_3]: https://dev.to/osovsky/6-ways-to-get-youtube-cookies-for-yt-dlp-in-2026-only-1-works-2cnb

[^3_4]: https://github.com/yt-dlp/yt-dlp/issues/13013

[^3_5]: https://www.reddit.com/r/youtubedl/comments/1jc0buu/cookies_expiring_while_downloading_videos/

[^3_6]: https://github.com/mpc-qt/mpc-qt/issues/134

[^3_7]: https://www.reddit.com/r/youtubedl/comments/1emm5qk/need_help_with_use_cookies_from_browser_commands/

[^3_8]: https://github.com/yt-dlp/yt-dlp/issues/12009

[^3_9]: https://www.youtube.com/watch?v=DsS1jCDZGek

[^3_10]: https://github.com/yt-dlp/yt-dlp/issues/10085

[^3_11]: https://www.reddit.com/r/youtubedl/comments/1n0jmhx/has_anyone_here_gotten_banned_for_passing/

[^3_12]: https://www.reddit.com/r/youtubedl/comments/1qezzfv/how_to_put_t_sleep_to_avoid_the_rate_limit_can_i/

[^3_13]: https://github.com/kevinwatt/yt-dlp-mcp/blob/main/docs/cookies.md

[^3_14]: https://github.com/yt-dlp/yt-dlp/issues/11914

[^3_15]: https://www.devkantkumar.com/blog/yt-dlp-ultimate-guide-2026

[^3_16]: https://www.youtube.com/watch?v=tsFfPLtDUjs


---

# Why YouTube detects yt-dlp cookie usage despite precautions — detection patterns, evolving blocks since 2024, and countermeasures from advanced users

**YouTube detects via behavioral heuristics on **InnerTube/player API**, not just cookies—despite precautions.**[^4_1][^4_2][^4_3]

1. **Detection Patterns**
    - **High-volume requests**: 50-100+ videos/account triggers "/player" endpoint blocks ("Video unavailable"). Cookies valid, but account/IP flagged.[^4_2][^4_4][^4_5]
    - **Non-human patterns**: No JS execution, fixed UA, rapid sequential calls (no delays). "Sign in to confirm you're not a bot" prompt.[^4_6][^4_1]
    - **Bot checks fail**: yt-dlp skips challenges (e.g., proofs); temp cookies work briefly, then invalidate. Datacenter/VPN IPs auto-blocked.[^4_3][^4_7]
    - **Expiration traps**: Cookies "expire" minutes-hours post-use if unused in browser; active requests required.[^4_8]
2. **Evolving Blocks Since 2024**
    - **2024**: Player endpoint bans for heavy cookie accounts (web broken, app works).[^4_2]
    - **Dec 2024-Jan 2025**: Mandatory cookies for *all* videos (even public); "bot confirm" rampant. InnerTube changes.[^4_1][^4_3]
    - **2025-26**: Faster invalidation (daily/hourly); playlist/channel bulk hits harder. Chrome encryption breaks exporters. Firefox/SQLite safest.[^4_7][^4_5]
    - Consensus: Anti-scraper escalation; yt-dlp nightly lags.[^4_9][^4_10]
3. **Countermeasures from Advanced Users**
    - **Rotate burners aggressively**: 20-50 videos/account; new profile/container per batch. VPS? Residential proxies.[^4_5][^4_2]
    - **Humanize requests**: `--sleep-interval 15-60 --max-sleep-interval 120 --sleep-subtitles 10`. `--referer https://youtube.com/`. Random UA (`--extractor-args "youtube:UACountry=US"`). `--cookies-from-browser firefox::dlp` + pre-visit youtube.com.[^4_11][^4_5]
    - **Auto-refresh cookies**: Script: Export > sleep > re-login headless Selenium in container > re-export. Cron every 4h.[^4_8][^4_1]
    - **Fallbacks**: `--extractor-retries 5 --fragment-retries 10`. No-cookies first (public/captions). OAuth experiments (unstable).[^4_9]
    - **Advanced**: Multi-proxy pools; mimic browser JS (yt-dlp `--player-client player`); monitor issues nightly. Datacenter? Switch residential.[^4_3][^4_7]

**Uncertainty**: Undocumented heuristics; varies by region/account age (newer riskier). Test small. **Assumption**: Transcript/video fetch (same endpoints).[^4_2]

**Next Step**: `--cookies-from-browser firefox::dlp --sleep-interval 20 -v <playlist>` > log "player" errors > rotate if >50.

## Key Takeaways

- **Detection**: Volume + patterns > cookies alone. **Blocks**: Escalated 2024-26 on InnerTube. **Fixes**: Sleep/rotate/refresh.[^4_5][^4_1][^4_2]

Hope this helps! Let me know if you have any other questions!
<span style="display:none">[^4_12][^4_13][^4_14][^4_15]</span>

<div align="center">⁂</div>

[^4_1]: https://github.com/yt-dlp/yt-dlp/issues/12045

[^4_2]: https://github.com/yt-dlp/yt-dlp/issues/10085

[^4_3]: https://github.com/yt-dlp/yt-dlp/issues/12219

[^4_4]: https://www.reddit.com/r/DataHoarder/comments/1dg1qlr/youtube_seems_to_be_blocking_accounts_that_are/

[^4_5]: https://www.reddit.com/r/youtubedl/comments/1n0jmhx/has_anyone_here_gotten_banned_for_passing/

[^4_6]: https://www.reddit.com/r/youtubedl/comments/1kngk36/ytdlp_always_requires_cookies/

[^4_7]: https://dev.to/osovsky/6-ways-to-get-youtube-cookies-for-yt-dlp-in-2026-only-1-works-2cnb

[^4_8]: https://github.com/yt-dlp/yt-dlp/issues/8227

[^4_9]: https://github.com/yt-dlp/yt-dlp/wiki/FAQ

[^4_10]: https://github.com/yt-dlp/yt-dlp/issues/11784

[^4_11]: https://mintlify.com/yt-dlp/yt-dlp/advanced/workarounds

[^4_12]: https://www.reddit.com/r/youtubedl/wiki/cookies/

[^4_13]: https://www.linkedin.com/posts/ranas-mukminov_youtube-activity-7380576328074432512-goxf

[^4_14]: https://feedback.vrchat.com/feature-requests/p/allow-passing-cookies-to-yt-dlp-for-get-around-youtube-restrictions

[^4_15]: https://github.com/JunkFood02/Seal/issues/2159
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
