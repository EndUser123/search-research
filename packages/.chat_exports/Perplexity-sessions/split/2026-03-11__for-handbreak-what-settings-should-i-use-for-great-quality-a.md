---
title: "for handbreak, what settings should I use for great quality at the smallest video size?"
date: "2026-03-11"
mode: "COPILOT"
uuid: "70e9128e-a44c-408a-81c1-70dff43be68a"
entry_count: 2
---

## Human

for handbreak, what settings should I use for great quality at the smallest video size?

## Assistant

Use Constant Quality with H.265 and tune RF instead of chasing a specific bitrate; that gives the best quality per byte in HandBrake.[1][2]

## Core video settings

For “great quality, smallest size” starting points (per‑title you can nudge RF up/down by 1–2):

- Codec: H.265 / HEVC (software x265 gives best compression; NVENC is faster with slightly larger files).[3][4]
- Container: MP4 (good compatibility) unless you need MKV features.  
- Preset: Start from a built‑in H.265 preset (e.g., “H.265 MKV/MP4 1080p30”) and adjust quality only.[4]
- Quality mode: Constant Quality (RF slider), not Average Bitrate.[2][1]
- RF targets (x265 or H.265 NVENC CQ):  
  - 480p: RF 18–22 (start 20).[1]
  - 720p: RF 19–23 (start 21–22).[1]
  - 1080p: RF 20–24 (start 22).[3][1]
  - 4K: RF 22–28 (start 24).[3][1]
Lower RF = higher quality and bigger files; higher RF = smaller files and more artifacts.[1]

### Example for a 1080p source

- Video Encoder: H.265 (x265) or H.265 (NVEnc if you want speed).  
- Framerate: Same as source, Variable or Constant only if you need it.  
- Quality: Constant Quality, RF 22.  
- Encoder Preset: x265 “slow” or “medium” (better compression than “fast” at same RF).[5][4]
- Tune: “film” for typical camera/video footage, “animation” for anime/cartoons.[5]

Slower presets give slightly better quality and smaller size at the same RF but encode more slowly.[4][5]

## Audio and other space savers

- Audio codec: AAC or Opus at 128–160 kbps stereo for most content; drop to 96 kbps for talking‑head video.[6][3]
- Remove extra audio tracks you don’t need (commentary, unused languages).[6]
- Subtitles: Burn in only if required; otherwise keep as soft subs (negligible size).  
- Filters: Avoid heavy denoise unless needed; it can shrink files but changes the look.[4]

## When to use bitrate mode

Use 2‑pass Average Bitrate only if you must hit a specific file size; it is worse for quality/size tradeoff than Constant Quality when you just want “small as possible at good quality”.[7][2]

### Quick reference table

| Goal                          | Key choices                              |
|-------------------------------|------------------------------------------|
| Max compression               | H.265 x265, RF 22–24, preset slow.[1][4] |
| Faster encoding               | H.265 NVENC, RF about 1–2 lower (20–22).[4][8] |
| Guaranteed file size          | 2‑pass Average Bitrate, target kbps.[7][6] |

If you tell me your typical source (resolution and whether it’s action, talking‑head, or screen capture), I can give you concrete RF and preset values tailored to that.

## Human

encoder tune has only none

## Assistant

That’s expected: with **NVENC** selected, HandBrake generally only exposes “Encoder Tune: None”; the film/animation/etc. tunes exist only for the software x264/x265 encoders.[1][2]

### What this means for you

- With H.265 (NVEnc), just leave Encoder Tune at None; quality is controlled by the RF/quality slider, preset, and bitrate, not by tune.[3][1]
- If you want access to “film/animation/grain” tunes, switch Video Encoder to H.265 (x265) instead of NVEnc; then the tune dropdown will populate.[2][4]
- NVENC is mainly about speed; at the same visual quality you’ll usually get slightly larger files than x265, so you may need RF 1–2 steps lower (e.g., RF 20 instead of 22) to match quality.[5][6]

Do you prefer faster encodes (NVENC) or are you willing to wait longer for smaller files and slightly better quality (x265 CPU)?
