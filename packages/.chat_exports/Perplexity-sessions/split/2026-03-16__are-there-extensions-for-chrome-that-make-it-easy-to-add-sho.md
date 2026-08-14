---
title: "are there extensions for chrome that make it easy to add shorts to a playlist?"
date: "2026-03-16"
mode: "COPILOT"
uuid: "4a888d49-3f7b-4b8c-b591-eba730a4eccd"
entry_count: 1
---

## Human

are there extensions for chrome that make it easy to add shorts to a playlist?

## Assistant

Yes, but there is no single “official” or perfect one-click solution yet; most options are either playlist managers that also work for Shorts, or general YouTube UI customizers where Shorts support is partial.[1][2][3]

## Current extension options

These are the closest fits on Chrome right now:

- **PocketTube: YouTube PlayList Manager** – Focuses on organizing and managing playlists (grouping, sorting, filtering, bulk operations) and works with any videos you’ve already added, including Shorts, but it does not add a special “save Short to playlist” button in the Shorts feed itself.[1]
- **YouTube Playlist Tools / similar “playlist duration/sorting” extensions** – Add toolbars on playlist pages for sorting, duration calculation, and loading all videos; they help once the Short is already in a playlist, not at the moment of discovery in the Shorts UI.[2][4]
- **UI / Shorts-focused extensions (Better YouTube Shorts, Autoplay Shorts, etc.)** – These improve playback controls, progress bars, or autoplay behavior for Shorts, but their feature lists do not mention adding Shorts directly to playlists.[5][6]

Community threads and GitHub issues around this (e.g., code-charity/youtube) specifically call out that adding Shorts to playlists from the Shorts UI is still awkward and often requires workarounds like opening the Short as a normal video first.[7][3]

## Practical workflow today

Given what’s currently available:

- On **desktop YouTube**, the most reliable path is to open the Short in the regular watch page (often by tweaking the URL or using “Share → Copy link → open in normal YouTube”) and then use the standard **“Save” / “Save to playlist”** control; extensions then help you manage those playlists afterward.[8][9][7]
- On **mobile**, the YouTube app now exposes a three-dots menu on Shorts with a “Save to playlist” option that works pretty directly, but that doesn’t depend on Chrome extensions.[10][8]

## What this implies

- FACT: There are strong playlist-management and Shorts-UX extensions, but none widely advertised as “one-tap: save any Short to a playlist from the Shorts feed” on Chrome as of early 2026.[3][5][2][1]
- CONSENSUS: Power users either rely on native “Save to playlist” where available or use URL tricks / desktop mode, then lean on playlist tools (PocketTube etc.) for organization.[7][8][3][1]
- SPECULATION (medium confidence): A small, niche extension that injects “Save to playlist” into Shorts might exist but be poorly indexed/marketed; it’s just not showing up in current top Web Store or discussion hits.[11][3]

If your main pain is “one key / one click from Shorts feed to a specific playlist on desktop,” would you be open to a lightweight custom extension or userscript? That’s quite feasible to build and I can sketch the minimal TS/JS needed.
