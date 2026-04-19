<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I'm trying to use z.ai vision mcp server to analyze videos, but I got this response:

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

**The z.ai Vision MCP Server enforces an 8MB file size limit for video analysis, confirming your test results.**  This restriction applies to the `video_analysis` tool, which supports local or remote videos in MP4, MOV, or M4V formats.[^1_1]

## Limit Confirmation

Your package videos (18-45MB) exceed this cap, causing the "Video file size exceeds maximum allowed size (8MB)" error across debugRCA, handoff, and portfolio-media files.  Official docs explicitly state "local/remote ≤8 MB" for video inspection to describe scenes, moments, and entities.[^1_1]

## Workarounds Evaluated

Your decision to stick with metadata-only analysis aligns with best practices—it's reliable, dependency-free, and scales to any video size.  Rejected options like compression risk quality loss; segmentation adds complexity without full coverage.[^1_1]

## Alternatives

- **Remote video URLs**: If hosted online (e.g., YouTube/Vimeo), test `video_analysis` as it supports remote links under 8MB effective size.[^1_1]
- **Frame extraction**: Use FFmpeg in your workflow to pull key frames as images (<8MB each) for `image_analysis` or specialized tools like `ui_to_artifact`.[^1_1]
- **Other MCP servers**: Check Video Parser MCP for deeper analysis without strict limits, or custom Python via `execute_code` for FFmpeg + local vision models.[^1_2]
- **Quota check**: Ensure your Z.ai plan (Lite/Pro/Max) has vision pool remaining; Pro/Max offer more usage.[^1_1]

Your updated docs (MEDIA_BEST_PRACTICES.md, VIDEO_ANALYSIS_LIMITATIONS.md) effectively document this for your Claude Code workflows.[^1_1]
<span style="display:none">[^1_10][^1_11][^1_12][^1_13][^1_14][^1_15][^1_3][^1_4][^1_5][^1_6][^1_7][^1_8][^1_9]</span>

<div align="center">⁂</div>

[^1_1]: https://docs.z.ai/devpack/mcp/vision-mcp-server

[^1_2]: https://mcpmarket.com/server/video-parser

[^1_3]: https://www.npmjs.com/package/@z_ai/mcp-server

[^1_4]: https://docs.z.ai/devpack/quick-start

[^1_5]: https://www.reddit.com/r/mcp/comments/1nz9ukx/built_an_mcp_server_that_adds_vision_capabilities/

[^1_6]: https://docs.z.ai/devpack/mcp/zread-mcp-server

[^1_7]: https://www.reddit.com/r/ClaudeAI/comments/1hb6m8x/is_there_a_size_limit_to_how_many_files_claude/

[^1_8]: https://www.reddit.com/r/ZaiGLM/comments/1p2mcja/zai_launches_web_reader_mcp_server_for_pro_max/

[^1_9]: https://blog.devgenius.io/fixing-glm-4-7-image-parsing-in-claude-code-add-the-z-ai-vision-mcp-server-f1c275d7cf3f

[^1_10]: https://docs.z.ai/devpack/mcp/reader-mcp-server

[^1_11]: https://github.com/router-for-me/CLIProxyAPI/issues/885

[^1_12]: https://www.latent.space/p/ainews-zai-glm-5-new-sota-open-weights

[^1_13]: https://github.com/lbjlaq/Antigravity-Manager/blob/main/docs/zai/mcp.md

[^1_14]: https://www.youtube.com/watch?v=lctDoa5M880

[^1_15]: https://hackernoon.com/multi-modal-mcp-servers-handling-files-images-and-streaming-data


---

# I'm surprised you didn't suggest using gemini.

You’re right: Gemini is a very natural fit for your use case, especially given the 8MB cap on z.ai’s vision MCP video tool.[^2_1][^2_2]

### Why I didn’t bring it up

The earlier answer stayed scoped to “inside the z.ai vision MCP server + Claude Code” and its immediate alternatives (other MCPs, frame extraction, metadata-only), rather than cross-vendor pipelines. That’s why it focused on z.ai limitations and MCP-compatible workarounds, not external model stacks like Gemini.[^2_3][^2_4]

### Why Gemini makes sense here

- Gemini 2.x/2.5 can take long, large videos (up to GBs via File API) and handle audio + visual jointly, with timestamped reasoning and segment queries.[^2_2][^2_5][^2_1]
- File API limits (20GB paid / 2GB free) wipe out the 8MB constraint that killed your package videos.[^2_2]
- It already supports “upload file(s) → ask questions about content” flows that map nicely to your debugRCA/handoff/portfolio-video analysis needs.[^2_6][^2_7][^2_1]


### How I’d actually recommend you integrate it

Given your workflow, I’d now explicitly suggest:

- Use z.ai vision MCP for images/diagrams and small snippets where staying inside the MCP ecosystem is convenient.[^2_3]
- Add a Gemini-side pipeline for video:
    - Upload videos via Gemini File API (or Vertex/Firestore + Gemini, or Firebase AI Logic) for durable handles.[^2_7][^2_1][^2_6][^2_2]
    - Build a tiny HTTP service that exposes “summarize / segment / Q\&A over this video-id,” then wrap that with a simple HTTP MCP server (or custom Claude Code skill).
- Lean on Gemini’s 1–2M token multimodal context for long-meeting / long-briefing videos where you want dense, timestamped notes and event extraction.[^2_8][^2_5][^2_2]

If you want, next step I can sketch the concrete architecture: Gemini File API + minimal Node/Python service + HTTP MCP definition tailored to your existing debugRCA/handoff package structure.
<span style="display:none">[^2_10][^2_11][^2_12][^2_13][^2_14][^2_15][^2_16][^2_17][^2_9]</span>

<div align="center">⁂</div>

[^2_1]: https://ai.google.dev/gemini-api/docs/video-understanding

[^2_2]: https://ai.google.dev/gemini-api/docs/video-understanding.md.txt

[^2_3]: https://docs.z.ai/devpack/mcp/vision-mcp-server

[^2_4]: https://mcpmarket.com/server/video-parser

[^2_5]: https://developers.googleblog.com/gemini-2-5-video-understanding/

[^2_6]: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/video-understanding

[^2_7]: https://firebase.google.com/docs/ai-logic/analyze-video

[^2_8]: https://www.datastudios.org/post/google-gemini-multimodal-input-in-2025-vision-audio-and-video-capabilities-explained

[^2_9]: https://gemini-api.apidog.io/doc-965861

[^2_10]: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com

[^2_11]: https://developers.googleblog.com/en/gemini-2-5-video-understanding/

[^2_12]: https://www.youtube.com/watch?v=Mot-JEU26GQ

[^2_13]: https://gemini.google/overview/video-generation/

[^2_14]: https://ai.google.dev/gemini-api/docs/video-understanding?hl=vi

[^2_15]: https://ai.google.dev/gemini-api/docs/models

[^2_16]: https://blog.google/products-and-platforms/products/gemini/gemini-3/

[^2_17]: https://cloud.google.com/use-cases/multimodal-ai


---

# what other apis or solutions exist that are free or almost free for video analysis?  We can even do screenshots right?

You have a few good “free or almost free” paths, and yes, screenshot/frame-based analysis is absolutely viable.[^3_1][^3_2]

## 1. Cloud APIs with generous free tiers

These are not “forever free,” but give you a lot of mileage for low-volume analysis:

- **Google Cloud Video Intelligence API** – Label detection, shot/scene detection, object tracking, speech-to-text, explicit content, etc.; has a free quota and then per‑minute pricing.[^3_3][^3_1]
- **Microsoft Azure Video Indexer** – High-level indexing, speaker detection, OCR, topic extraction; has a free trial tier and then pay‑as‑you‑go.[^3_1][^3_3]
- **Amazon Rekognition Video** – Object/scene detection, face matching, people tracking; also offers a free tier for the first N minutes per month.[^3_3][^3_1]
- **Aggregator like Eden AI** – Single API over multiple providers (Google, AWS, etc.) with free credits and the option to swap engines while keeping one integration.[^3_3]

These are good if you want: “Upload video → get structured JSON events/labels” without running models yourself.

## 2. Open-source / self‑hosted stacks (effectively free)

If you’re willing to run things locally or on your own VPS, you can get very close to “free”:

- **Whisper (or local forks) for transcription** – Many OSS tools wrap Whisper for local video transcription; one example is an open-source “VideoTranscriber” with diarization, keywords, Ollama integration, etc.[^3_4]
- **PySceneDetect** – Python + OpenCV scene-cut detection; great for segmenting long videos into shots cheaply.[^3_5]
- **OpenCV / YOLO / MediaPipe** – Classic stack for object detection, pose tracking, etc., all free; you just pay compute.[^3_1]
- **Edit Mind (self-hosted)** – Local open-source video indexing/search tool; uses Whisper, YOLO, face/emotion detection, scene analysis every 2 seconds, and lets you query via natural language.[^3_6]

Given your background, a local stack (Whisper + scene detection + a vision model via Ollama or similar) is probably the sweet spot for “almost free.”

## 3. Screenshot / frame-based pipelines (what you asked about)

Yes, you can absolutely treat videos as a sequence of screenshots and analyze those with any image model:

- **Frame extraction with FFmpeg** – Fully free CLI; you can extract frames every N seconds or at shot boundaries.[^3_2]
- Example: extract one frame every 5 seconds
    - `ffmpeg -i input.mp4 -vf fps=1/5 frames/frame_%05d.png`[^3_2]
- You can also extract **keyframes (I‑frames)** or use scene detection filters (`-vf "select='gt(scene,0.4)'"`) to only grab “interesting” frames, then feed those into vision models (z.ai MCP, Gemini images, Qwen-VL, etc.).[^3_7][^3_2]

This gives you: cheap, controllable sampling + re‑use of your existing image-analysis tools, at the cost of losing continuous motion/audio unless you also run transcription.

## 4. “Almost free” hosted model hubs

- **Replicate / Hugging Face Inference / similar** – Many video understanding models (action recognition, captioning, CLIP‑over‑frames) exposed via simple APIs; you usually get free credits and then low per‑minute or per‑call pricing.[^3_8][^3_1]
- You can combine: “call a hosted OSS model that expects frames or short clips” + your own FFmpeg segmentation to stay within free tiers.


## 5. How I’d narrow it for your use case

For “debugRCA/handoff/portfolio” style videos where cost matters:

- Use **FFmpeg + screenshots** as the core: extract keyframes/interval frames, analyze with your existing vision stack (z.ai vision MCP, local vision via Ollama, or open-source VL models).[^3_7][^3_2]
- Add **local Whisper** for audio transcripts and then run your usual LLM workflows over the text.[^3_6][^3_4]
- If you need structured, auto‑labeled content occasionally (faces/objects/scenes) and don’t want to build everything, hit **Google Cloud Video Intelligence or Rekognition** only for those specific jobs, staying within or near the free tier.[^3_1][^3_3]

If you tell me your target volume (videos/month, duration) and whether you’re okay running GPU workloads locally, I can propose a concrete architecture: FFmpeg commands, which OSS components to use, and where an MCP wrapper would sit.
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://www.byteplus.com/en/topic/88852

[^3_2]: https://www.gumlet.com/learn/ffmpeg-extract-frames/

[^3_3]: https://www.edenai.co/post/top-free-video-analysis-tools-apis-and-open-source-models

[^3_4]: https://www.reddit.com/r/opensource/comments/1id0gnd/open_source_video_transcription_tool_local_ai/

[^3_5]: https://github.com/Breakthrough/PySceneDetect

[^3_6]: https://www.youtube.com/watch?v=YrVaJ33qmtg

[^3_7]: https://playbooks.com/skills/benchflow-ai/skillsbench/ffmpeg

[^3_8]: https://is4.ai/blog/our-blog-1/top-20-best-free-ai-tools-2025-48

[^3_9]: https://www.reddit.com/r/LocalLLM/comments/1nvt4yc/can_anyone_recommend_opensource_ai_models_for/

[^3_10]: https://focalml.com/blog/ai-video-analysis-tools-you-can-use-in-2025-for-content-breakdown/

[^3_11]: https://testguild.com/api-testing-tools/

[^3_12]: https://www.byteplus.com/en/topic/88852?title=top-10-free-video-analysis-tools-apis-and-open-source-models

[^3_13]: https://github.com/bdougie/vision

[^3_14]: https://www.koyeb.com/blog/best-multimodal-vision-models-in-2025

[^3_15]: https://www.opus.pro/blog/best-scene-cut-detection-tools-for-editors

