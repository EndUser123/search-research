---
title: "These handbrake settings are exploding my file sizes larger.  How do I make file sizes smaller and keep at least the sam"
date: "2026-02-02"
mode: "COPILOT"
uuid: "69a1d8ed-1796-4366-b5f8-389c2adf7f5d"
entry_count: 1
---

## Human

These handbrake settings are exploding my file sizes larger.  How do I make file sizes smaller and keep at least the same quality?

## Assistant

You’re currently telling HandBrake’s NVEnc encoder to aim for very high quality, so it’s simply using more bits than the source. To shrink files while keeping them visually the same, you need to relax quality a bit and/or switch to a more efficient encoder.

### What’s happening with your settings

- H.265 NVEnc in **Constant Quality** mode will use “whatever bitrate it needs” to hit that quality level; on easy sources it may be smaller than the original, but on noisy/grainy or already‑compressed sources it can easily overshoot the source bitrate and size.[1][2]
- Hardware NVEnc generally needs more bitrate than software x265 for the same visual quality (it trades compression efficiency for speed), so at the same CQ level NVEnc files are often larger.[3][4]

### Settings to change for smaller files

Try these adjustments on one short test clip and compare visually:

1. **Switch encoder (if you care more about size than speed)**  
   - Video Encoder: **H.265 (x265)** instead of H.265 (NVEnc).  
   - Keep Constant Quality but use **RF 20–22 for 1080p**; HandBrake’s docs recommend RF 20–24 for 1080p, where higher RF = smaller file.[5][6]
   - Preset: **Slow or Medium** (slower = better compression = smaller file at same RF).[4]

2. **If you want to stay on NVEnc (GPU)**  
   - Keep H.265 (NVEnc), Constant Quality.  
   - Increase the CQ/RF value until file sizes are reasonable: if you’re at 20 now, try **22, 24, even 26** and compare a few static and fast‑motion scenes. Higher CQ numbers give smaller files and somewhat lower quality, but in practice many users find CQ ~22–26 fine for 1080p NVEnc.[7][8]
   - Encoder Preset: move one step **slower** than you’re using now (e.g., from Medium to Quality) to regain some efficiency without a big speed hit.[9][4]

3. **Consider a bitrate cap instead of pure CQ**  
   - Switch from Constant Quality to **Avg Bitrate (kbps)**.  
   - For 1080p, start around **3500–5000 kbps** for typical content and adjust based on tests; file size will be roughly `bitrate × duration` so you can predict it easily.[10][1]
   - This prevents runaway file sizes on difficult/grainy sources while still using H.265’s better compression compared to H.264.[1][10]

4. **Avoid unneeded bloat from other settings**  
   - Keep **Resolution** at source or slightly downscale (e.g., 1080p → 720p) if you truly don’t need full HD; lower resolution greatly reduces bitrate needs.[4]
   - Leave filters like **Denoise/Sharpen** off unless you need them; heavy denoise can help compress grainy sources, but it changes the look and costs time—test it on a short segment first.[4]
   - Audio: don’t over‑encode; for stereo, **AAC 128 kbps** is usually transparent and saves a bit versus very high audio bitrates.[10]

### A concrete “baseline” preset to try

For a good quality/size baseline on 1080p TV or web video:

- Encoder: **H.265 (x265)**  
- Framerate: Same as source, Variable  
- Quality: Constant Quality **RF 21**  
- Preset: **Slow**  
- Audio: AAC 128 kbps stereo  

If you must stay on NVEnc:

- Encoder: **H.265 (NVEnc)**  
- Quality: Constant Quality **CQ 24–26**  
- Preset: one notch slower than current (e.g., Quality instead of Medium)  

Encode a 2–3 minute representative sample with old vs new settings and flip between them; if you can’t see a difference at normal viewing distance, keep the smaller files.
