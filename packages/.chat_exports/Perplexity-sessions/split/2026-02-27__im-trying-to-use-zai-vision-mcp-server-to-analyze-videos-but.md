---
title: "I'm trying to use z.ai vision mcp server to analyze videos, but I got this response:
'
● ✅ Video Analysis Testing Compl"
date: "2026-02-27"
mode: "COPILOT"
uuid: "41bf6639-2ef1-408e-a076-150150c01821"
entry_count: 3
---

## Human

I'm trying to use z.ai vision mcp server to analyze videos, but I got this response:
"
● ✅ Video Analysis Testing Complete

  Commit: b9104c0 - "docs: document video analysis limitations with zai-mcp-server"

  Test Results Summary

  Discovery: zai-mcp-server video analysis has an 8MB file size limit

  ┌────────────────┬──────────────┬──────────────────┐
  │   Video Type   │ Typical Size │   Compatible?    │
  ├────────────────┼──────────────┼──────────────────┤
  │ Package videos │ 18-45MB      │ ❌ No            │
  ├────────────────┼──────────────┼──────────────────┤
  │ zai-mcp limit  │ 8MB max      │ ✅ If compressed │
  └────────────────┴──────────────┴──────────────────┘

  Tested on:
  - debugRCA: 45MB (technical overview)
  - handoff: 28-33MB (briefing videos)
  - portfolio-media: 18-32MB (concept videos)

  All failed with: Video file size exceeds maximum allowed size (8MB)

  Decision: No Code Changes Needed

  Keep current metadata-only approach because:
  1. ✅ Works for any size video
  2. ✅ Fast and reliable
  3. ✅ No external dependencies
  4. ✅ Practical for typical package videos

  Alternatives rejected:
  - Compress videos to <8MB: Quality loss, extra complexity
  - Segment analysis: Complex, might miss content
  - Custom pipeline: Significant engineering effort

  Files Updated

  1. MEDIA_BEST_PRACTICES.md - Added 8MB limit explanation
  2. docs/VIDEO_ANALYSIS_LIMITATIONS.md - Full analysis with recommendations (153 lines)

  Summary

  zai-mcp-server is perfect for images (diagrams/infographics) with 71% feature coverage, but
   not practical for videos due to file size limits. Current implementation is appropriate -
  videos require manual review."

## Assistant

**The z.ai Vision MCP Server enforces an 8MB file size limit for video analysis, confirming your test results.**  This restriction applies to the `video_analysis` tool, which supports local or remote videos in MP4, MOV, or M4V formats.[1]

## Limit Confirmation
Your package videos (18-45MB) exceed this cap, causing the "Video file size exceeds maximum allowed size (8MB)" error across debugRCA, handoff, and portfolio-media files.  Official docs explicitly state "local/remote ≤8 MB" for video inspection to describe scenes, moments, and entities.[1]

## Workarounds Evaluated
Your decision to stick with metadata-only analysis aligns with best practices—it's reliable, dependency-free, and scales to any video size.  Rejected options like compression risk quality loss; segmentation adds complexity without full coverage.[1]

## Alternatives
- **Remote video URLs**: If hosted online (e.g., YouTube/Vimeo), test `video_analysis` as it supports remote links under 8MB effective size.[1]
- **Frame extraction**: Use FFmpeg in your workflow to pull key frames as images (<8MB each) for `image_analysis` or specialized tools like `ui_to_artifact`.[1]
- **Other MCP servers**: Check Video Parser MCP for deeper analysis without strict limits, or custom Python via `execute_code` for FFmpeg + local vision models.[2]
- **Quota check**: Ensure your Z.ai plan (Lite/Pro/Max) has vision pool remaining; Pro/Max offer more usage.[1]

Your updated docs (MEDIA_BEST_PRACTICES.md, VIDEO_ANALYSIS_LIMITATIONS.md) effectively document this for your Claude Code workflows.[1]

## Human

I'm surprised you didn't suggest using gemini.

## Assistant

You’re right: Gemini is a very natural fit for your use case, especially given the 8MB cap on z.ai’s vision MCP video tool.[1][2]

### Why I didn’t bring it up
The earlier answer stayed scoped to “inside the z.ai vision MCP server + Claude Code” and its immediate alternatives (other MCPs, frame extraction, metadata-only), rather than cross-vendor pipelines. That’s why it focused on z.ai limitations and MCP-compatible workarounds, not external model stacks like Gemini.[3][4]

### Why Gemini makes sense here
- Gemini 2.x/2.5 can take long, large videos (up to GBs via File API) and handle audio + visual jointly, with timestamped reasoning and segment queries.[2][5][1]
- File API limits (20GB paid / 2GB free) wipe out the 8MB constraint that killed your package videos.[2]
- It already supports “upload file(s) → ask questions about content” flows that map nicely to your debugRCA/handoff/portfolio-video analysis needs.[6][7][1]

### How I’d actually recommend you integrate it
Given your workflow, I’d now explicitly suggest:

- Use z.ai vision MCP for images/diagrams and small snippets where staying inside the MCP ecosystem is convenient.[3]
- Add a Gemini-side pipeline for video:
  - Upload videos via Gemini File API (or Vertex/Firestore + Gemini, or Firebase AI Logic) for durable handles.[7][1][6][2]
  - Build a tiny HTTP service that exposes “summarize / segment / Q&A over this video-id,” then wrap that with a simple HTTP MCP server (or custom Claude Code skill).  
- Lean on Gemini’s 1–2M token multimodal context for long-meeting / long-briefing videos where you want dense, timestamped notes and event extraction.[8][5][2]

If you want, next step I can sketch the concrete architecture: Gemini File API + minimal Node/Python service + HTTP MCP definition tailored to your existing debugRCA/handoff package structure.

## Human

what other apis or solutions exist that are free or almost free for video analysis?  We can even do screenshots right?

## Assistant

You have a few good “free or almost free” paths, and yes, screenshot/frame-based analysis is absolutely viable.[1][2]

## 1. Cloud APIs with generous free tiers

These are not “forever free,” but give you a lot of mileage for low-volume analysis:

- **Google Cloud Video Intelligence API** – Label detection, shot/scene detection, object tracking, speech-to-text, explicit content, etc.; has a free quota and then per‑minute pricing.[3][1]
- **Microsoft Azure Video Indexer** – High-level indexing, speaker detection, OCR, topic extraction; has a free trial tier and then pay‑as‑you‑go.[1][3]
- **Amazon Rekognition Video** – Object/scene detection, face matching, people tracking; also offers a free tier for the first N minutes per month.[3][1]
- **Aggregator like Eden AI** – Single API over multiple providers (Google, AWS, etc.) with free credits and the option to swap engines while keeping one integration.[3]

These are good if you want: “Upload video → get structured JSON events/labels” without running models yourself.

## 2. Open-source / self‑hosted stacks (effectively free)

If you’re willing to run things locally or on your own VPS, you can get very close to “free”:

- **Whisper (or local forks) for transcription** – Many OSS tools wrap Whisper for local video transcription; one example is an open-source “VideoTranscriber” with diarization, keywords, Ollama integration, etc.[4]
- **PySceneDetect** – Python + OpenCV scene-cut detection; great for segmenting long videos into shots cheaply.[5]
- **OpenCV / YOLO / MediaPipe** – Classic stack for object detection, pose tracking, etc., all free; you just pay compute.[1]
- **Edit Mind (self-hosted)** – Local open-source video indexing/search tool; uses Whisper, YOLO, face/emotion detection, scene analysis every 2 seconds, and lets you query via natural language.[6]

Given your background, a local stack (Whisper + scene detection + a vision model via Ollama or similar) is probably the sweet spot for “almost free.”

## 3. Screenshot / frame-based pipelines (what you asked about)

Yes, you can absolutely treat videos as a sequence of screenshots and analyze those with any image model:

- **Frame extraction with FFmpeg** – Fully free CLI; you can extract frames every N seconds or at shot boundaries.[2]
- Example: extract one frame every 5 seconds  
  - `ffmpeg -i input.mp4 -vf fps=1/5 frames/frame_%05d.png`[2]
- You can also extract **keyframes (I‑frames)** or use scene detection filters (`-vf "select='gt(scene,0.4)'"`) to only grab “interesting” frames, then feed those into vision models (z.ai MCP, Gemini images, Qwen-VL, etc.).[7][2]

This gives you: cheap, controllable sampling + re‑use of your existing image-analysis tools, at the cost of losing continuous motion/audio unless you also run transcription.

## 4. “Almost free” hosted model hubs

- **Replicate / Hugging Face Inference / similar** – Many video understanding models (action recognition, captioning, CLIP‑over‑frames) exposed via simple APIs; you usually get free credits and then low per‑minute or per‑call pricing.[8][1]
- You can combine: “call a hosted OSS model that expects frames or short clips” + your own FFmpeg segmentation to stay within free tiers.

## 5. How I’d narrow it for your use case

For “debugRCA/handoff/portfolio” style videos where cost matters:

- Use **FFmpeg + screenshots** as the core: extract keyframes/interval frames, analyze with your existing vision stack (z.ai vision MCP, local vision via Ollama, or open-source VL models).[7][2]
- Add **local Whisper** for audio transcripts and then run your usual LLM workflows over the text.[6][4]
- If you need structured, auto‑labeled content occasionally (faces/objects/scenes) and don’t want to build everything, hit **Google Cloud Video Intelligence or Rekognition** only for those specific jobs, staying within or near the free tier.[1][3]

If you tell me your target volume (videos/month, duration) and whether you’re okay running GPU workloads locally, I can propose a concrete architecture: FFmpeg commands, which OSS components to use, and where an MCP wrapper would sit.
