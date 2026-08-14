---
title: "I would like to edit videos with ai for free, or at least with my llm subscriptions.  What options do I have?  I work on"
date: "2026-06-28"
mode: "COPILOT"
uuid: "0cbcda30-d157-4216-83a7-e6c424bb3c2f"
entry_count: 2
---

## Human

I would like to edit videos with ai for free, or at least with my llm subscriptions.  What options do I have?  I work on windows 11.

## Assistant

You have three main paths: native Windows tools with built‑in AI, browser‑based AI editors that are “free to start,” and DIY workflows where you drive local tools via your existing LLM subscriptions (Claude, etc.). On Windows 11, you can get quite far without paying extra beyond what you already spend on LLMs.[1][2][3]

## Clarify your goals

Concrete question that will change the answer a lot: are you mostly doing  
- talking‑head / tutorial / screen‑record videos, or  
- more cinematic / multi‑camera edits with heavier effects?

I’ll assume you’re in the “YouTube/tutorial/screen‑record” bucket and want fast, semi‑automatic editing with AI.

***

## Native / built‑in Windows options

These are “free” in the sense of being included with Windows or your Microsoft account.

### Clipchamp (Microsoft’s AI video editor)

- Clipchamp is now Microsoft’s main consumer editor and has AI features: auto subtitles, AI voiceovers, removing silences/background noise, social resize, etc.[3]
- It runs in Edge/Chrome or as a Windows 11 app, so it fits nicely into your environment.[3]
- All AI tools in Clipchamp are free for all users, with no separate AI subscription required (watermarks and export limits may depend on account tier, but the AI features themselves are free).[3]

Typical workflow for your use case:
- Import your screen recording / talking‑head footage.  
- Use AI to remove silences and background noise, then auto‑generate subtitles.  
- Reframe/resize for platforms (YouTube, Shorts, etc.) with AI aspect‑ratio tools.  

This is a good “baseline” non‑LLM solution that you can always fall back on.

### Simple non‑AI editors (to pair with LLMs)

- Movie Maker – Video Editor from the Microsoft Store works on Windows 10 and 11 and is optimized for quick social‑style videos.[4]
- Other free editors like CapCut, DaVinci Resolve, Kdenlive, Lightworks, etc. are widely recommended for watermark‑free editing; they’re not inherently LLM‑driven but are solid backends to script or “drive” with LLM help.[5][6]

Use case for you: let the LLM (Claude, etc.) plan the edit, then execute it manually or via scripts in these tools.

***

## Browser‑based “free to start” AI video editors

These rely on cloud AI (including LLMs and other models) and typically give you a free tier with credits.

### Kapwing AI Video Editor

- Kapwing offers an AI video editor where you can trim clips, add subtitles, generate B‑roll, resize, translate, and export up to 4K in the browser.[7]
- It’s free to start and uses a credit system; each AI feature consumes credits, but you can do light editing without paying.[7]

Best fit: fast social clips, auto captions, B‑roll from text, format conversions—good for turning long explanations into polished short videos.

### Adobe Firefly / Premiere AI

- Adobe Firefly has an AI video editor and a “Generate Video” module for upscaling and prompt‑based edits, with a free tier of generative credits tied to a Firefly or Creative Cloud plan.[8]
- Adobe Premiere adds AI assistive features (speech‑to‑text, caption translation, enhance speech, reframing), with some generative tools available on a limited complimentary basis within a Creative Cloud membership.[9]

If you already have Adobe, these can be strong—but they’re not truly free beyond the trial / included credits.

### Spark 1.0 by Vizard

- Spark 1.0 is a video‑understanding LLM that clips videos via simple prompts and is currently free.[10]
- You upload a video, then either let it auto‑find viral clips or ask for specific moments via prompts.[10]

This is useful if you want: “find the best 10 short clips from this hour‑long tutorial” via declarative prompts instead of manual scrubbing.

***

## Using your existing LLM subscriptions for editing

You’re exactly the target user for “LLM‑driven” workflows where local tools + scripts do the heavy lifting and the LLM orchestrates.

### Claude Desktop / OpenAI “Codex” style agents + video skills

- There is a workflow where you install a local agent app (e.g., Codex from OpenAI or Claude Desktop), then connect it to video‑manipulation skills like `video-use` and `hyperframes` (GitHub repos).[1]
- In one tutorial, the author shows using Codex (free agent) or Claude Desktop (requires Claude Code subscription) to automatically install these skills and then perform trimming, editing, and motion graphics based on natural language prompts.[1]

Key properties:
- You keep your video files local on Windows.  
- The LLM (Claude/OAI) reads skill docs and runs commands to cut clips, add overlays, etc., via those tools.[1]
- Your usage of Claude/OpenAI subscriptions powers the orchestration, not an extra SaaS editor subscription.

This meshes well with your agentic patterns: effectively, a local “video agent” that you direct with prompts like “remove mistakes, keep the best takes, export three vertical clips.”

### GitHub “AI video editor” projects (multi‑clip stitching)

- For example, `ai-video-editor` (GitHub) uses an LLM to stitch together multiple videos and do a rough cut automatically.[2]
- Setup typically involves: cloning the repo, setting `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` in `.env`, installing Python dependencies, then specifying input video files and running a script that outputs an edited `ai_output.mp4`.[2]

Why this fits you:
- You can plug in your existing Anthropic/OpenAI keys (you already have LLM subscriptions).  
- You can extend or fork the repo to support your own rules (cut silences, keep slides visible, prefer takes where you mention certain keywords, etc.).  
- It’s 100% local except for API calls to LLMs; no extra SaaS needed.

***

## Free / low‑cost AI utilities around editing

These don’t always “edit” in the full sense, but they solve key parts of the pipeline.

### Clipping & highlights

- Spark 1.0 (above) for prompt‑based clipping and auto “viral” moment extraction.[10]

### Captions, transcripts, and search

- Clipchamp for auto subtitles and captioning on Windows 11 (free AI tools).[3]
- Adobe’s speech‑to‑text in Premiere if you use the trial / membership for richer transcript‑driven editing.[9]

You can also use your LLM subs to clean and structure transcripts: export text from these tools, then let Claude reorganize sections, generate chapter markers, and script B‑roll suggestions.

***

## Practical path tailored to you (Windows 11, LLM‑heavy)

Here’s a concrete plan that keeps extra cost near zero and leans on your subscriptions:

1. **Baseline editor + AI assist (Clipchamp)**  
   - Use Clipchamp on Windows 11 for core timeline editing, AI noise removal, silence removal, and subtitles.[3]
   - Let Claude or another LLM:  
     - Design the edit structure (intro, sections, call‑to‑action).  
     - Generate title cards, lower thirds text, thumbnail concepts, chapter titles.

2. **LLM‑driven local automation**  
   - Pick one GitHub project like `ai-video-editor` and wire it to your Anthropic/OpenAI keys.[2]
   - Use it for automatic rough cuts: feed an hour‑long recording and get a first‑pass trimmed `ai_output.mp4`.[2]
   - Manually refine in Clipchamp/DaVinci afterward.

3. **Agent app with video skills**  
   - Install Claude Desktop on Windows and hook up video skills (`video-use`, `hyperframes`) if you want a full “agent that edits” workflow.[1]
   - Use natural language: “Clean up this folder of takes, remove false starts, keep the best explanations, add motion graphics for key terms.”

4. **Optional: browser AI editor for social clips**  
   - Use Kapwing’s free AI video editor for quick B‑roll generation and social‑ready cuts when credits are available.[7]
   - Use Spark 1.0 to auto‑find best clip moments from long tutorials; export clips and finish them locally.[10]

***

## Assumptions, uncertainty, and next step

- FACT: Clipchamp’s AI tools are free for all users and work on Windows 11.[3]
- FACT: GitHub projects like `ai-video-editor` use LLM APIs (Anthropic/OpenAI) to automate rough cuts, with no additional SaaS fee beyond your API usage.[2]
- FACT: The Codex/Claude desktop + `video-use` / `hyperframes` pattern exists as a demonstrated workflow for AI‑driven local video editing.[1]
- CONSENSUS: For serious, repeatable editing, combining a robust non‑AI editor (Clipchamp/DaVinci) with LLM automation is more flexible than relying solely on SaaS “AI editors.”  
- SPECULATION (medium confidence): Given your skill set, you’ll likely get the most leverage from the GitHub + Claude Desktop route, where you can evolve a custom “video agent” rather than depending on fixed SaaS UX.

If you tell me whether you’re mostly editing long technical videos, short explainer clips, or something else, I can sketch a concrete workflow (tools + scripts + prompt patterns) tuned to that format.

## Human

most of the videos are instructional videos that I want to shorten.  or personal videos I want to make shorter.

## Assistant

You’re basically trying to turn long, mostly single‑speaker instructional or personal videos into concise highlight versions—with minimal manual timeline surgery. The best options on Windows 11 are (1) Clipchamp’s built‑in AI trimming, (2) Spark 1.0 / Vizard for highlight extraction, and (3) a Claude‑powered local agent like `video-use` for fully automated “drop folder, get short video” workflows.[1][2][3]

Below I’ll keep it concrete: what tool, what it’s good for, and an example workflow.

***

## Clipchamp: fast silence‑based shortening (free, built‑in)

Clipchamp’s AI silence removal is designed exactly for “make this talking video shorter without re‑recording.” It automatically finds pauses longer than 3 seconds, lets you approve them, then cuts them out and leaves you with a tighter video.[4][2]

How it works (instructional/personal videos):

- You import your video (screen recording, vlog, tutorial) via the “import media” button or record inside Clipchamp.[2]
- You click the AI suggestions (sparkle icon) → “auto cut / trim and tidy,” which asks you to transcribe the media.[5][2]
- The AI scans for silences and pauses longer than 3 seconds, marks them on the timeline, and shows you a list.[4][2]
- You review the proposed cuts, ignore ones you want to keep, or remove all in one shot; Clipchamp then splits the video and deletes the marked silences.[2][4]
- You can also turn on captions, download an SRT transcript, and export at your chosen resolution.[2]

Best use cases for you:
- You recorded a 30–60 minute tutorial with natural pauses: quickly remove dead air and reduce length by 10–30% without touching the timeline manually.  
- Personal videos (e.g., talking to camera) where you want to keep content but just tighten pacing.

Limitations/assumptions:
- It only removes pauses longer than 3 seconds; shorter filler words and micro‑hesitations stay unless you manually cut.[4][2]
- It doesn’t (yet) reorder content or pick “best moments”—it’s more a “tightener” than a highlight generator.

***

## Spark 1.0 / Vizard: highlight clipping by prompt

Spark 1.0 is a video‑understanding LLM that can find and order the most relevant moments from long videos based on natural language prompts. It’s tailored to turning long podcasts, tutorials, interviews, and vlogs into short highlight clips.[6][7][1]

What it does for you:

- You upload a long instructional or personal video to Vizard.  
- Spark analyzes the entire video “like a human,” recognizing key moments, actions, and emotions.[8][6]
- You type prompts such as “find the 5 most valuable tips about lower body training” or “highlight the moment where I explain how to configure Claude plugins.”[1][6]
- It automatically extracts and orders those moments into short clips, with auto captions and social‑ready formats.[7][6]

Strengths for shortening:

- For tutorials: “turn this 1‑hour session into 10 short clips explaining key steps” is exactly the supported pattern.[6][7]
- For personal videos: you can ask for “the most emotionally significant moments” or “the funniest interactions” and get curated highlights.[8]

Tradeoffs:
- Cloud/online; your videos go to Vizard’s servers.  
- Free/paid boundaries depend on their current plan; Spark 1.0 is described as next‑gen and available via web/mobile, but heavy use may require a subscription.[7][1]

***

## Claude‑driven local agent: `video-use` and similar

Given your LLM subs and agentic workflow interest, this is likely the highest‑leverage path.

### `video-use`: “edit videos with Claude Code”

- `video-use` is an open‑source project that lets coding agents like Claude Code edit videos: you drop raw footage in a folder, chat with the agent, and get `final.mp4` back.[3]
- The idea: you describe how you want to shorten a video (remove false starts, remove pauses > N seconds, keep only segments mentioning specific topics), and the agent orchestrates local tools to produce a shorter cut.[3]

How you’d use it:

- Install `video-use` on Windows 11, point it at a folder containing your raw instructional or personal videos.[3]
- In Claude Code, attach the skill and then prompt:  
  - “Take `session01.mp4`, remove all segments where I’m switching windows or silently reading, keep only explanation segments, target length 10 minutes.”  
- The agent uses ASR and editing utilities under the hood to detect speech, filler, and structure, then outputs an edited shorter video.[9][3]

This can support:
- Automatic removal of filler words and repeated sentences in speech videos via ASR‑based rough cut skills (as referenced by similar tooling like FireRed‑OpenStoryline).[9]
- Custom rules you define (e.g., “drop any segment where I say ‘let me think’ or where the FPS drops below X”).

Pros for you:
- 100% local video files; only LLM calls go out to Anthropic/OpenAI.  
- You can iterate on rules and build a deterministic shortening pipeline as part of your broader agentic architecture.  
- No extra SaaS; just time to wire it up and pay for LLM/API usage.

***

## Other “rough cut” tools worth noting

These are not full AI LLMs but can help shorten without watching everything:

- **Roughcut** is a video editor focused on fast home‑video trimming: you watch each clip once and mark keep/discard, which yields a quick rough edit. This is more manual but optimized for speed on personal videos.[10]

You can combine such tools with LLM‑generated instructions (e.g., Claude plans which segments to keep, you execute them quickly in Roughcut/Clipchamp).

***

## Recommended workflow for your scenario

Given your goal and skill set:

1. **Use Clipchamp to quickly tighten pacing on all instructive/personal videos.**  
   - Run silence removal, review cuts, export a “tightened” base version.[4][2]
   - Use auto captions for accessibility and later search.[2]

2. **Use Spark 1.0 / Vizard when you want highlight reels rather than just shorter versions.**  
   - For a long tutorial: prompt Spark to extract best explanations, demos, or tips and produce 3–10 short clips.[6][7]
   - For personal videos: prompts focusing on key events or emotions.  

3. **Invest in a Claude‑powered `video-use` workflow for repeatable, automated shortening.**  
   - Wire `video-use` into your Claude Code environment on Windows.[3]
   - Define prompt templates like “shorten instructional video to core steps only” and “shorten personal video to key family moments.”  
   - Over time, refine rules (ASR thresholds, filler word catalogs, segment scoring) so the agent does a reliable first cut, and you only do final polish.

***

If you tell me whether you’re okay with cloud upload for personal videos, I can narrow this down to either a purely local agent pipeline or a mixed local/cloud setup and outline step‑by‑step setup for one concrete tool (e.g., `video-use` + Claude Code for shortening).
