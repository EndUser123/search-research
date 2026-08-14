---
title: "for windows 11, what's the easiest way to chop a video up and stich it together and delete segments?"
date: "2025-12-14"
mode: "COPILOT"
uuid: "af239d60-3600-4230-a259-8b0f3d51d8fb"
entry_count: 5
---

## Human

for windows 11, what's the easiest way to chop a video up and stich it together and delete segments?

## Assistant

Microsoft Clipchamp, pre-installed on Windows 11, offers the easiest built-in way to chop videos by splitting clips, delete unwanted segments, and stitch remaining parts together on a timeline.[1][2]

## Quick Start with Clipchamp
Search for "Clipchamp" in the Start menu and launch it. Import your video via the "Your Media" tab, then drag it to the timeline.[3][4]

## Steps to Chop and Delete
Position the playhead at the cut point, click the split icon (scissors) or right-click and select "Split" to divide the clip. Repeat for the end of the unwanted section, select the middle segment, and press Delete.[5][2][1]

## Stitching Clips Together
Drag additional clips or split sections into place on the timeline to arrange them seamlessly. Add transitions if desired between segments.[6][4]

## Export Final Video
Click "Export" in the top right, choose resolution (up to 1080p free), and save. The process preserves original quality without watermarks for basic edits.[4][7]

## Human

It's taking a LONG time to even hit 1% on the import.

## Assistant

Clipchamp can be *painfully* slow to “prepare” files, especially large or highly compressed ones, and sometimes it’s not worth waiting.[1][2]

## Quick triage questions
Before suggesting alternatives, a few things that commonly cause this:
- Very large file (multi‑GB) or long recording, especially screen captures or HEVC/variable‑frame‑rate clips.[3][4]
- Slow or unstable internet: Clipchamp still leans on cloud processing, so imports can crawl if the connection is bad.[5][6]
- Low free space or RAM on the main drive; Clipchamp wants plenty of scratch space and at least 8 GB RAM for smooth behavior.[7][8]

If you tell me:
- file size + codec/source (e.g., OBS, phone, Zoom), and  
- whether it’s on an SSD vs HDD / external drive,  
then more targeted advice is possible.

## Fast local alternative (no cloud)
If Clipchamp is crawling, use a pure desktop editor that just opens the file directly:

- **LosslessCut** (or similar minimal cutter) lets you:
  - Open a file instantly.  
  - Set in/out points, cut out sections, and export without re‑encoding (very fast).[9][10]
- Many “video splitter/merger” tools for Windows 11 behave the same way: split, delete segments, and join in one pass.[10][11]

This workflow avoids the import bottleneck completely and is usually the path of least resistance for simple chop‑and‑stitch jobs.

## If you want to keep using Clipchamp
If you’d rather not switch tools, try the quickest fixes:
- Move the source video to your fastest internal SSD and try again.[8][7]
- Close other heavy apps and browser tabs; ensure at least several GB of free RAM and 20–30% free space on the system drive.[7][8]
- Verify your connection is stable (ideally wired or strong Wi‑Fi).[6]
- If it’s HEVC/phone footage, transcoding once to a “lighter” format (e.g., H.264 MP4 via HandBrake) often makes Clipchamp much snappier.[4]

If you share a rough file size and source, a concrete “use tool X, follow these Y steps” recipe can be laid out.

## Human

12Gb, HDD external,

## Assistant

For a 12 GB file on an external HDD, Clipchamp crawling is expected; it has to read and often preprocess the whole thing, and HDD + USB is the worst‑case combo for that.  For what you want (just chopping and deleting segments), a lightweight, local cutter is going to be dramatically faster.[1][2]

## Recommended tool instead
Use **LosslessCut** for this job:

- It is designed for *large* files and does near‑instant cuts without re‑encoding, using FFmpeg under the hood.[3][4]
- You just drag the video in, mark in/out points, and export the kept segments or remove the unwanted ones.[5][4]

Basic workflow:

1. Install LosslessCut for Windows 11 (from Microsoft Store or its GitHub/releases).[6][4]
2. Move the 12 GB file to your *internal SSD* first if possible; this alone can make scrubbing and cutting much smoother than from external HDD.[2]
3. Open the file in LosslessCut, play to the start of a “keep” section, set start, then set end, and add it as a segment.[4][5]
4. Repeat for each part you want to keep, then export; it will write out the stitched result very quickly since it’s not transcoding.[3][4]

If moving the file to SSD isn’t an option, LosslessCut will still be far less painful than waiting for Clipchamp to finish “preparing” on that external drive.

## Human

I can't install it

## Assistant

That `.appx` build needs a trusted certificate, which you don’t have installed, so Windows refuses to install it.[1][2]

## Use a different LosslessCut build
The easiest path is:

- Download the **portable or zip/exe** version instead of the `.appx` installer.[2][3]
- From the GitHub releases page, grab the Windows `.zip` build, extract it, and run `LosslessCut.exe` directly; no installation or certificate is required.[4][2]

## If you prefer Store-style install
Alternatively, install it from a trusted distributor that handles signing:

- Use the **Microsoft Store listing** for LosslessCut, which is properly signed and installs with one click.[5][4]

Given the certificate error, switching to the portable/zip build is the quickest way to get cutting right now.

## Human

If I'm going to both reencode and chop up a video (handbreak and losslesscut) what order should I do it in?

## Assistant

Do the **LosslessCut chops first, then reencode with HandBrake after**.

## Why this order works best
- LosslessCut is designed to cut your *original* file without reencoding, so you only process the portions you plan to keep instead of transcoding junk you’ll later delete.[1][2]
- Reencoding once at the very end (in HandBrake) avoids multiple quality-loss steps and saves time, since you are encoding a shorter, final file.[3][4]

## Practical workflow
1. Open the raw video in LosslessCut, mark all keep segments, and export a single stitched file (still near‑instant, copy‑based).[5][1]
2. Take that stitched output into HandBrake, set your compression/format settings, and encode once to your delivery format.[4][3]

Only flip the order (HandBrake → LosslessCut) if you explicitly want to normalize codec/format *before* cutting for compatibility reasons.[6][7]
