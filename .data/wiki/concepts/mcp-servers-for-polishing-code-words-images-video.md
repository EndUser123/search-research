---
title: "MCP Servers for Polishing Code, Words, Images, and Video: Research and Fleet Fit"
created: 2026-07-30
source: session-20260730
tags: [mcp, media-pipeline, video-editing, image-processing, code-quality, writing, kinocut, opencv, mcpolish, agent-capability]
summary: >
  Research into MCP servers that let AI agents polish four media types: video
  (Kinocut — guardrailed FFmpeg editing), images (OpenCV MCP — computer vision
  analysis), code (mcpolish — MCP tool description linting), and words
  (existing skills suffice). The highest-impact additions for this workspace
  are Kinocut + OpenCV MCP, which together close the "actual visual content"
  gap identified when trying to ingest videos into the wiki with frame-level
  insights rather than just transcript summaries.
agent: grok
host: grok
cognitive_load: 2
verification: single-source-verified
sources:
  - https://github.com/KyaniteLabs/kinocut (KyaniteLabs, 2026) — guardrailed video editing MCP server
  - https://github.com/GongRzhe/opencv-mcp-server (GongRzhe, 2026) — OpenCV image/video processing MCP
  - https://github.com/vtensor/mcpolish (vtensor, 2026) — static linter for MCP tool descriptions
  - https://github.com/misbahsy/video-audio-mcp (misbahsy, 2026) — FFmpeg audio/video MCP alternative
  - https://storybook.js.org/docs/ai/mcp/overview (Storybook, 2026) — UI component story generation MCP
relations:
  - target: wiki/concepts/skill-domain-map.md
    type: extends
  - target: wiki/concepts/chrome-acp-grok-build-setup-implementation.md
    type: complements
  - target: wiki/concepts/claude-powered-video-editing-workflows.md
    type: extends
  - target: wiki/concepts/video-to-wiki-pipeline-report-metrics-and-framework.md
    type: complements
---

# MCP Servers for Polishing Code, Words, Images, and Video

## Decision context

The operator asked what repos people like for polishing code, words, pictures,
and videos — specifically in the context of what else to consider for shipping
the Chrome ACP → Grok Build system. The underlying problem: the ACP-driven agent
can read browser tabs and write wiki entries, but when asked to ingest video
content with "actual image and video insights, not just the transcript," it
lacked tools for frame extraction, visual analysis, and video editing. The
research question was: what MCP servers exist that would close this gap and
add polish capabilities across all four media types?

## Video: Kinocut — clear winner

[KyaniteLabs/kinocut](https://github.com/KyaniteLabs/kinocut) is a guardrailed
video editing MCP server for AI agents. Local-first, FFmpeg-powered, free.

**What people like:**
- Preflight guardrails prevent invalid FFmpeg calls before they execute
- "Video Receipts" — structured record of every edit made, for auditability
- Quality gates catch broken outputs (wrong codec, missing audio, corrupt frames)
- Hyperframes — frame-level analysis for extracting insights from specific moments
- Shorts/Reels repurposing built in (auto-crop, vertical format, captions)
- Python client + CLI in addition to MCP interface
- Local-first — no cloud dependencies, works offline

**What people don't like:**
- Relatively new project — limited adoption signal compared to mature tools
- FFmpeg knowledge still helpful for understanding error messages
- No built-in transcription (pairs with Whisper/NotebookLM for that)

**Alternative:** [misbahsy/video-audio-mcp](https://github.com/misbahsy/video-audio-mcp)
covers both audio and video via FFmpeg but lacks the guardrail/receipt system.
Better for simple operations; Kinocut is better for complex editing workflows.

## Image: OpenCV MCP Server

[GongRzhe/opencv-mcp-server](https://github.com/GongRzhe/opencv-mcp-server)
exposes OpenCV's image and video processing capabilities through MCP.

**What people like:**
- Real computer vision — object detection, face recognition, image transforms
- Lets agents analyze what's actually in an image, not just generate new ones
- Works with both static images and video frames
- Complements generation tools (image_gen/image_edit) by adding analysis

**What people don't like:**
- OpenCV dependency can be heavy on Windows
- Limited to what OpenCV supports — no generative AI capabilities
- Documentation is sparse compared to the underlying OpenCV library

**Workflow with Kinocut:** Kinocut extracts frames from video → OpenCV MCP
analyzes them (detect objects, measure quality, identify scenes) → agent writes
wiki entries with visual insights. This closes the gap the operator identified.

## Code: mcpolish — meta-level quality

[vtensor/mcpolish](https://github.com/vtensor/mcpolish) is a static linter for
MCP server tool descriptions.

**What people like:**
- Catches vague, colliding, or misleading tool descriptions before agents pick
  the wrong tool
- Would have caught issues like the tabId type mismatch (string vs integer) if
  the description had specified parameter types clearly
- Fast — pure static analysis, no runtime needed
- PyPI installable: `pip install mcpolish`

**Fit for this workspace:** Run on the Chrome ACP MCP handler to validate
browser_tabs, browser_read, browser_execute descriptions are clear enough for
MiniMax-M3 and other models. Low effort, high signal.

## Words: existing skills suffice

No standout MCP server was found for prose/writing polish. The existing
`/wiki` skill + cross-model review (`/agy`, `/codex`, `/mmx`) already handles
writing quality across the fleet. A dedicated grammar/style MCP would be
redundant. Storybook MCP exists for UI component stories but is only relevant
if polishing the Chrome ACP extension's React UI further.

## What this means for our workspace

| Priority | Tool | Gap closed | Effort | Status |
|----------|------|-----------|--------|--------|
| **High** | Kinocut | Video editing, frame extraction, repurposing | Low (uvx + config.toml) | ✅ Installed + verified (2026-07-30) |
| **High** | OpenCV MCP | Image/frame analysis, object detection | Low (uvx + config.toml) | ✅ Installed + verified (2026-07-30) |
| **Medium** | mcpolish | MCP tool description quality | Trivial (pip + run) | Not installed — one-shot CLI, not a server |
| **Low** | Storybook MCP | UI component testing | Medium | Deferred |

The [[skill-domain-map]] shows Domain 12 (Media pipeline) as ⚠️ underdeveloped
(4 skills, 9 capabilities). Adding Kinocut + OpenCV MCP would materially
strengthen this domain and enable the video-to-wiki pipeline the operator
attempted earlier this session.

The combined workflow would be:
1. Agent reads Perplexity/ChatGPT tab (browser_read) → extracts video URLs
2. Kinocut downloads/edits video, extracts key frames
3. OpenCV MCP analyzes frames (detects what's shown, identifies charts/diagrams)
4. [[nlm-to-wiki]] ingests transcript for text synthesis
5. Agent writes wiki concept combining transcript insights + visual analysis

This connects to the broader [[chrome-acp-grok-build-setup-implementation]]
architecture — the ACP-driven agent needs media tools to fully realize the
browser-driven workflow. The [[claude-powered-video-editing-workflows]]
concept documented Higgsfield MCP for media generation; Kinocut + OpenCV
cover the complementary editing/analysis side.

## Installation + verification (2026-07-30)

Both servers installed and verified live on this Windows 11 host via `uvx`
(ephemeral environments — no global installs). Registered in
`~/.grok/config.toml` under `[mcp_servers.kinocut]` and `[mcp_servers.opencv]`.

**Decisive receipts:**
- **Kinocut** — MCP `video_trim` on a synthetic 4s clip → 2.0s output
  (ffprobe-confirmed), MCP `success: true`. Server reports 161 tools incl.
  Video Receipts, rescue, review/publish gates.
- **OpenCV MCP** — `get_image_stats` on a 320×240 PNG returned real analysis
  (mean 127.35, per-channel stats, histogram); `resize_image` 320×240→160×120
  wrote valid output. 22 tools, no model files needed for basic analysis.

**Critical install caveat:** both broke on first launch with
`ModuleNotFoundError: No module named 'mcp.server.fastmcp'`. Root cause: MCP
SDK 2.0.0 removed `mcp.server.fastmcp`, which these servers import. Fix
(already applied): pin `--with "mcp<2"` in the `uvx` args. See
[[mcp-sdk-2-0-fastmcp-breakage]] for the full pattern — it affects the entire
1.x-era MCP server ecosystem, not just these two.

**OpenCV model files (optional):** basic tools (resize, crop, stats, edge/
contour/feature detection, frame extraction — exactly what the video-to-wiki
pipeline needs) require no model downloads. Only YOLO/DNN object+face
detection need model files in `OPENCV_DNN_MODELS_DIR`. So the analysis
pipeline is ready as-is.

## Falsifier

**Resolved (2026-07-30):** the original Windows-compatibility concern for
OpenCV did **not** materialize — basic image tools (read, stats, resize)
worked on first try on this Windows 11 host. The wiki's stated risk
("OpenCV's history on Windows is mixed") is overstated for basic processing;
it may still apply to the optional DNN-model features, which are untested.

**Remaining risks:**
- If Kinocut's guardrails prove too restrictive for real editing tasks
  (blocking valid operations), the workflow degrades to raw FFmpeg.
- The `mcp<2` pin is load-bearing — if a future `uvx` resolver change or a
  transitive dependency forces `mcp>=2`, both servers break on launch again.
  Drop the pin only after each server publishes a 2.0-compatible release.

If the MCP ecosystem consolidates around a single media-processing server that
subsumes both video editing and image analysis (e.g., a future FFmpeg+OpenCV
hybrid MCP), the separate-tool approach becomes unnecessary overhead.

## Sources

- [KyaniteLabs/kinocut](https://github.com/KyaniteLabs/kinocut) (KyaniteLabs, 2026) — guardrailed video editing MCP server. Features: preflight guardrails, Video Receipts, quality gates, Hyperframes, Shorts/Reels repurposing.
- [GongRzhe/opencv-mcp-server](https://github.com/GongRzhe/opencv-mcp-server) (GongRzhe, 2026) — OpenCV image/video processing MCP. Features: object detection, face recognition, image transforms.
- [vtensor/mcpolish](https://github.com/vtensor/mcpolish) (vtensor, 2026) — static linter for MCP tool descriptions. Catches vague/colliding/misleading descriptions.
- [misbahsy/video-audio-mcp](https://github.com/misbahsy/video-audio-mcp) (misbahsy, 2026) — FFmpeg audio/video MCP alternative. Broader scope, no guardrails.
- [Storybook MCP](https://storybook.js.org/docs/ai/mcp/overview) (Storybook, 2026) — UI component story generation for AI agents.
- [awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers) (punkpeye, 2026) — curated MCP server directory, image generation/editing section.
