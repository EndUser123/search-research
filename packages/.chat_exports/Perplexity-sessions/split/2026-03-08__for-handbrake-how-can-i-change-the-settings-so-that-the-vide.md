---
title: "for handbrake, how can I change the settings so that the video size doesn't exceed 1280p?"
date: "2026-03-08"
mode: "COPILOT"
uuid: "f6cdcc62-96bd-4f2f-8e0c-3a0da3bab19a"
entry_count: 1
---

## Human

for handbrake, how can I change the settings so that the video size doesn't exceed 1280p?

## Assistant

**In HandBrake, set the "Resolution Limit" dropdown to 720p in the Picture tab to ensure output video never exceeds 1280x720 pixels (the maximum for 720p), automatically downscaling higher-resolution sources while preserving aspect ratio.**[1]

## Steps to Configure
Load your source video and scan it first to activate the Picture tab.

- Switch to the **Picture** tab.
- Locate the **Resolution Limit** dropdown (under Dimensions).
- Select **720p** (or the closest option like 720p30 if available; it caps at 1280 width / 720 height).[2]
- Leave **Anamorphic** on Automatic for optimal scaling up to the limit. 
- Optionally, enable **Allow Upscaling** only if needed, but the limit still applies. 

Preview the output using the Preview button to verify the dimensions stay at or below 1280 pixels in width or height (scaling maintains proportions).[1]

This works for both landscape and portrait videos by fitting within the limit's bounding box.[3]
