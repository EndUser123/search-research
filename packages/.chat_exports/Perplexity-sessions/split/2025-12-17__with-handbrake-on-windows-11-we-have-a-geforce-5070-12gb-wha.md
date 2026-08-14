---
title: "with handbrake on windows 11, we have a geforce 5070 12gb.  What preset can I use to take full advantage of my gpu?"
date: "2025-12-17"
mode: "COPILOT"
uuid: "4a05daf6-0a81-4659-9ae8-7e9c1ba7e894"
entry_count: 3
---

## Human

with handbrake on windows 11, we have a geforce 5070 12gb.  What preset can I use to take full advantage of my gpu?

## Assistant

Use the **AV1 NVENC** encoder with the **Fast** preset in HandBrake to fully leverage your GeForce RTX 5070's 12GB VRAM and NVENC hardware acceleration on Windows 11.[1][2]

This setup supports RTX 50-series GPUs like the 5070, delivering fast encoding speeds with excellent quality and smaller file sizes compared to H.264 or H.265.[2]

## Recommended Settings
Select from HandBrake's built-in presets under the Hardware category, such as **H.265 NVENC 2160p 4K** or **H.265 NVENC 1080p**, then customize as follows for AV1:[2]

- **Video Codec**: AV1 (NVENC)
- **Encoder Preset**: Fast (balances speed and quality; try Slowest for marginal gains if needed)[3][2]
- **Quality (CQ)**: 22 (adjust 20-24 based on source; lower for higher quality)[3]
- **Filters**: Disable all (they force CPU fallback and slow encoding)[3]

## Enable GPU Acceleration
In HandBrake Preferences > Video, ensure **NVIDIA NVENC** is checked (requires driver 570+).[2]

High CPU usage may persist for filters, audio, and syncing, but NVENC handles core encoding.[2]

## Performance Tips
- Use NVDEC for decoding if no filters are needed.
- Test with your footage; RTX 5070 excels at 4K AV1.[3][2]

## Human

This OK?  Some of the settings you described are "Not Available".

## Assistant

Yes, that setup is fine and you are already using your GPU correctly with NVENC.

## What in your screenshot matters

- **Video Encoder: AV1 (NVEnc)** – This is exactly what you want; it uses the RTX 5070’s hardware encoder.[1]
- **Quality: Constant Quality 20 CQ** – A CQ around 18–22 is a sweet spot for AV1; 20 is a good default.[2]
- **Framerate: Same as source / Variable Framerate** – Safe default unless you specifically need constant FPS for editing or streaming.[3]

## Encoder options explanation

- **Encoder Preset: Medium** – On modern NVENC (including 50‑series), Medium is a solid balance of quality and speed; Fast/Medium/Slow mostly trade small quality differences for encode time.[1]
- **Encoder Tune: None** – Correct unless you have a specific latency or lossless use‑case; leaving this at None is recommended.[1]
- **Profile/Level: Auto** – Letting HandBrake pick these is recommended for compatibility and to avoid unnecessary constraints.[1]

## Why some options show “Not Available”

Certain HandBrake options only appear for specific codecs, driver versions, or HandBrake versions, and many CPU‑only x264/x265 controls are intentionally hidden for NVENC encoders.  That does not mean you are missing performance; NVENC exposes a smaller, fixed set of encoder controls, and your current panel contains the key ones you actually need.[4][1]

## Human

Anything here?

## Assistant

Leaving every filter **Off** (exactly as in your screenshot) is ideal for GPU‑accelerated encoding if the source already looks fine.[1]

Filters like detelecine, deinterlace, denoise, sharpen, and deblock are all CPU‑heavy and will slow things down or even force decoding back to the CPU, which reduces the benefit of NVENC.[2][1]
