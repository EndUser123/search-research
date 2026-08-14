---
title: "with losslesscut, how do I create segments with scene detection?"
date: "2025-12-16"
mode: "COPILOT"
uuid: "b8dcdce9-f476-4f99-817b-b3dcf1a2dd27"
entry_count: 1
---

## Human

with losslesscut, how do I create segments with scene detection?

## Assistant

LosslessCut can auto-detect scene changes and then turn those into segments via its “Detect scene change” tool; after detection, you convert the detected cut points into segments and export.[1][2]

## Where the scene detection lives

- Open your file in LosslessCut and make sure the main video track is selected.[1]
- Open the tools menu (wrench icon or “Tools” in the top menu, depending on version).[1]
- Look for an item labeled something like “Detect scene change” (distinct from “Detect black scenes” or “Detect silence”).[3][1]

## Running scene detection

- In the “Detect scene change” dialog, set or accept the default sensitivity/threshold parameters; higher sensitivity finds more cuts but can create false positives.[4][3]
- Run the detection; LosslessCut scans the whole file and generates cut points at frames where the image changes enough to count as a scene change.[3][4]
- When it completes, you should see a list of detected timestamps or markers on the timeline where scenes change.[5][1]

## Turning detections into segments

- Use the option in that dialog or in the tools menu to “Create segments from scene changes” or similar; in current builds, LosslessCut can “divide timeline into segments” based on automatic detection.[2][1]
- This will create a segment between each pair of adjacent scene-change markers, effectively giving you one segment per detected shot/scene.[4][1]
- Inspect and manually trim or delete any segments where detection missed or added unwanted cuts; scene detection is known to struggle with fades and low-contrast material.[5][4]

## Exporting the scene-based segments

- Once the segments look right, choose Export and make sure “Cut by segments” (or “Export segments as separate files”) is enabled so each segment becomes its own file.[5][1]
- Export using the default lossless mode (no re‑encode) unless you specifically need re‑encoding for format changes.[2][1]

If you tell which OS and LosslessCut version you are on, a more version-specific click-path (exact menu names and buttons) can be outlined.
