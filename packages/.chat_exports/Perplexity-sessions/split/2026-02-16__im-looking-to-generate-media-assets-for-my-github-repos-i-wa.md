---
title: "I'm looking to generate media assets for my github repos.  I was using NotebookLM for slides, infographics, banner, vide"
date: "2026-02-16"
mode: "COPILOT"
uuid: "0011867d-6aed-4622-b3ec-4bd354aa3fc0"
entry_count: 5
---

## Human

I'm looking to generate media assets for my github repos.  I was using NotebookLM for slides, infographics, banner, video explaations, etc, but NotebookLM isn't great for all of it.  It likes to obscure text in the video with art work.  I had this chat below.  What do you think are good solutions?
"
● Based on the research, here are the visual style options for NotebookLM videos:

  NotebookLM Visual Styles - Research Summary

  Built-in Visual Styles

  NotebookLM offers these pre-built styles:

  ┌─────────────┬───────────────────────────────────────────────────┐
  │    Style    │                     Best For                      │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ whiteboard  │ Technical explanations, diagrams, clean aesthetic │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ classic     │ Professional, business presentations              │
  ├─────────────┼───────────────────────────────────────────────────┤
  │ auto_select │ Let NotebookLM choose based on content            │
  └─────────────┴───────────────────────────────────────────────────┘

  Additional styles (less suitable for technical content):
  - watercolor, retro_print, heritage, paper_craft, kawaii, anime

  McKinsey-Style Custom Prompt

  Based on the research, a McKinsey-style description you can use:

  --style "Minimalist corporate design with clean lines, data visualization aesthetics, professional color
  palette of navy blue and white with gold accents, geometric patterns, clear hierarchy, sans-serif
  typography, generous white space"


  Or for your PBS Nova technical style:

  --style "Clean technical diagrams with solid backgrounds, high contrast, no decorative elements, geometric
  boxes and arrows, professional sans-serif fonts, data visualization aesthetic, generous white space, navy
  and gray color scheme"


  Recommendation

  For technical package documentation, whiteboard is the most effective built-in style because it:
  - Emphasizes clarity over decoration
  - Works well with diagrams and flowcharts
  - Minimizes visual noise that could obscure text

  The visual style alone won't fix text readability issues - that's more about content density and
  NotebookLM's rendering limitations. For dense information, Reports are better than videos.

  ---
  Recommended Solution & Next Steps

  Recommended Solution: Use the whiteboard visual style with your existing PBS Nova conceptual-level prompt.
  The whiteboard style aligns best with technical documentation and minimizes decorative elements that could
  obscure text.

  Next Steps

  Would you like me to:
  1. Update the video generation prompt in SKILL.md to use a McKinsey-inspired custom style description
  2. Test regenerate the portfolio-media video once the rate limit clears
  3. Focus on generating diagrams (mind maps, infographics) instead of videos for better text readability
  4. Create a McKinsey-style template prompt for all future video generations

  Which should I tackle first?

✻ Cooked for 1m 22s

❯ Are we not already using the whiteboard style? Is there a way to optimize the whiteboard style?

● Yes, looking at the current SKILL.md, you're already using --style whiteboard for videos.

  The whiteboard style is already the best choice for technical content - it emphasizes clarity and diagrams
  over decoration. The issues you're experiencing (text obscuration, too much detail) aren't fixed by visual
  style - they're content/prompt issues.

  Whiteboard optimization is limited because NotebookLM controls:
  - How it overlays text on visuals
  - How much detail it includes from sources
  - What it considers "video-worthy" content

  What you CAN control:

  1. Content density in sources - Less detailed source material = less chance of cluttered visuals
  2. Prompt specificity - Your current prompt already does this well ("stay at conceptual level", "no
  step-by-step")
  3. Artifact selection - For dense information, Reports > Videos

  Practical optimization:

  The whiteboard style is already optimized for your use case. If text is still being obscured, it's likely:
  - NotebookLM's rendering limitation (not fixable via style)
  - Too much content in the briefing doc being pulled into visuals

  Suggestion: Try reducing the briefing doc to just 3-4 key concept paragraphs instead of full documentation.
  Less source content = cleaner visual rendering.

  Would you like me to create a minimal "concept-only" briefing doc template for future video generations?

❯ Does z.ai and glm offer video or image or audio generation?

● GLM (Zhipu AI / bigmodel.cn):
  - Image: Yes - GLM-4V and CogView models can generate images
  - Audio: Yes - TTS (text-to-speech) capabilities available
  - Video: No native video generation

  Z.AI (OpenRouter wrapper):
  - Acts as an API router to multiple providers
  - Video/image/audio capabilities depend on which underlying model you route to
  - Example: Can route to Flux/SDXL for images, but no direct video generation

  For comparison with NotebookLM:
  - NotebookLM generates videos because it has specialized "Video Overview" feature - it's not just an LLM,
  it's a content-to-video pipeline
  - GLM/Z.AI are primarily text/image models - they don't have the explainer video workflow that NotebookLM
  has

  Bottom line: If you want explainer videos from documentation, NotebookLM is still the best option despite
  the rendering quirks. The alternatives would require building your own video pipeline (script generation →
  TTS → visuals → video assembly).

❯ /research explainer video generation options that are soley notebooklm.

● Bash(research "explainer video generation AI tools documentation to video alternatives 2025" --mode tavily
      --depth comprehensive)
  ⎿  Error: Exit code 127
     /usr/bin/bash: line 1: research: command not found

● Bash(python -m research_skill.cli "explainer video generation AI tools documentation to video alternatives
      2025" --mode tavily --depth comprehensive)
  ⎿  Loaded environment variables from P:\\__csf\\.env
     Loaded environment variables from P:\\__csf\\.env
     🔍 Researching: explainer video generation AI tools documentation to video alternatives 2025
     … +17 lines (ctrl+o to expand)
  ⎿  (timeout 2m)

● Web Search("NotebookLM video overview unique features documentation to video alternatives 2025")
  ⎿  Did 0 searches in 15s

● Explainer Video Generation Tools - Research Summary

  What Makes NotebookLM Unique

  NotebookLM's Video Overview is a unique feature that:
  - Generates 6-7 minute AI-narrated videos with ~20 slides
  - Works directly from your uploaded documents, PDFs, charts
  - Uses AI to synthesize information into video format
  - Integrated into Google's NotebookLM ecosystem
  - Launched July 2025 - very new feature

  Alternatives to NotebookLM

  ┌───────────────────────────┬─────────────────────────────────────────────────┬─────────────────┐
  │           Tool            │                    Best For                     │     Pricing     │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://gamma.app](https://gamma.app)         │ Presentation-to-video, polished slides          │ Freemium        │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://beautiful.ai](https://beautiful.ai)      │ Auto-formatted presentations, design automation │ Freemium        │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://tome.pm](https://tome.pm)           │ Story-driven presentations, AI narration        │ Freemium        │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://synthesia.io](https://synthesia.io)      │ AI avatars + text-to-video                      │ Paid (~$30/mo)  │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://heygen.com](https://heygen.com)        │ AI avatar videos, lip-sync                      │ Paid            │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://fliki.ai](https://fliki.ai)          │ Text-to-video with stock footage                │ Freemium        │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://pictory.ai](https://pictory.ai)        │ Blog/article to video                           │ Paid            │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://invideo.io](https://invideo.io)        │ Template-based video creation                   │ Freemium        │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://descript.com](https://descript.com)      │ Video editing, text-based editing               │ Freemium        │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://loom.com](https://loom.com)          │ Screen recording + AI editing                   │ Freemium        │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://runwayml.com](https://runwayml.com)      │ AI video generation, creative visuals           │ Paid            │
  ├───────────────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ [https://socialsightai.com](https://socialsightai.com) │ Generative AI video                             │ Paid/Aggregator │
  └───────────────────────────┴─────────────────────────────────────────────────┴─────────────────┘

  Key Differentiator: NotebookLM

  What NotebookLM does that others don't:
  - Reads YOUR documentation directly - no manual script writing
  - Grounded in your sources - citations back to original docs
  - No manual slide creation - auto-generates from text sources
  - Integrated with research workflow - part of the notebook ecosystem

  Most alternatives require you to:
  1. Manually write the script
  2. Create slides yourself
  3. Upload voiceover or use TTS
  4. Assemble everything

  NotebookLM automates all of this from your uploaded documents.

  Best for Technical Documentation

  For package documentation like portfolio-media:

  1. NotebookLM - Best for "upload and go" from existing docs
  2. Gamma - Best for manual but polished presentation creation
  3. Beautiful.ai - Best for clean, auto-formatted slides
  4. Tome - Best for narrative-driven explanations

  ---
  Recommended Solution & Next Steps

  Recommended Solution: NotebookLM remains the best option for automated explainer videos from technical
  documentation because it's the only tool that reads your docs and generates video without manual
  intervention. The visual issues you're experiencing (text obscuration, detail level) are prompt/content
  problems, not tool limitations.

  Next Steps

  Would you like me to:
  1. Create a minimal "concept-only" source template for NotebookLM to reduce visual clutter
  2. Test Gamma.app as an alternative (requires manual slide creation but better visual control)
  3. Focus on Reports + Mind Maps instead of videos for portfolio-media package
  4. Generate a new video with a more aggressive "high-level only" briefing doc

  Which should I tackle first?

  ---
  Sources:
  - [https://support.google.com/notebooklm/answer/16454555?hl=en](https://support.google.com/notebooklm/answer/16454555?hl=en)
  - [https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-video-overviews-studio-up](https://blog.google/innovation-and-ai/models-and-research/google-labs/notebooklm-video-overviews-studio-up)
  grades/
  - [https://www.pcmag.com/picks/best-ai-video-generator](https://www.pcmag.com/picks/best-ai-video-generator)
  - [https://zapier.com/blog/best-ai-video-generator](https://zapier.com/blog/best-ai-video-generator)
  - [https://massv.io/blog/best-ai-video-generator/](https://massv.io/blog/best-ai-video-generator/)

✻ Cooked for 1m 7s

❯ we have several ai subscriptions: gemini, glm, openai, chutes, openrouter.  surely there are repos that
   do everything already, or can be assembled to do everything you mentioned.

● Good point! Let me research open-source repos that leverage those APIs for doc-to-video workflows.

● Bash(python -m research_skill.cli "github repository documentation to video AI pipeline open source gemini
      openai" --mode github --depth comprehensive)
  ⎿  Loaded environment variables from P:\\__csf\\.env
     Loaded environment variables from P:\\__csf\\.env
     🔍 Researching: github repository documentation to video AI pipeline open source gemini openai
     … +12 lines (ctrl+o to expand)

● Web Search("github "doc to video" "text to video" openai gemini open source 2025")
  ⎿  Did 0 searches in 16s

● zread - search_doc (MCP)(repo_name: "google/gemini-python", query: "video generation text to video tutorial
                          example", language: "en")
  ⎿  Error: MCP error -400: {"error":{"code":"1210","message":"{\\"code\\":1001,\\"msg\\":\\"target not found,
     error: repo not found\\"}"}}

● Web Search("github gemini-ai generative-ai-python video generation example code")
  ⎿  Did 0 searches in 14s

● Web Search("github "doc to video" "presentation to video" automated python openai tts MANIM 2024 2025")
  ⎿  Did 0 searches in 23s

● Web Search("manim python text to video automation openai tts github")
  ⎿  Did 0 searches in 14s

● Found some great repos! Here's what's available:

  ---
  Open Source Doc-to-Video Solutions

  Direct Matches (Manim-based)

  Repo: [https://github.com/mateolafalce/topic2manim](https://github.com/mateolafalce/topic2manim)
  Description: Auto educational video generator
  Stack: Manim + AI + TTS
  ────────────────────────────────────────
  Repo: [https://github.com/rohitg00/manim-video-generator](https://github.com/rohitg00/manim-video-generator)
  Description: GPT → Manim code → video
  Stack: OpenAI GPT + Manim
  ────────────────────────────────────────
  Repo: [https://github.com/ManimCommunity/manim-voiceover](https://github.com/ManimCommunity/manim-voiceover)
  Description: Official voiceover plugin
  Stack: Manim + TTS
  ────────────────────────────────────────
  Repo: [https://github.com/marcelo-earth/generative-manim](https://github.com/marcelo-earth/generative-manim)
  Description: LLM-powered video generation
  Stack: GPT-4/Claude + Manim
  ────────────────────────────────────────
  Repo: [https://github.com/makefinks/manim-generator](https://github.com/makefinks/manim-generator)
  Description: LLM with code-reviewer loop
  Stack: Auto-refinement

  Google Gemini Video

  ┌──────────────────────────────────────────────────────┬─────────────────────────┬─────────────────┐
  │                         Repo                         │       Description       │      Stack      │
  ├──────────────────────────────────────────────────────┼─────────────────────────┼─────────────────┤
  │ [https://github.com/2b3pro/GeminiGenerator](https://github.com/2b3pro/GeminiGenerator)            │ Video via Veo2/Veo3 API │ Gemini + Veo    │
  ├──────────────────────────────────────────────────────┼─────────────────────────┼─────────────────┤
  │ [https://github.com/GoogleCloudPlatform/generative-ai](https://github.com/GoogleCloudPlatform/generative-ai) │ Official examples       │ Gemini + Python │
  └──────────────────────────────────────────────────────┴─────────────────────────┴─────────────────┘

  ---
  What You Can Build With Your Subscriptions

  Your Stack:
  ├── Gemini → script generation, Veo video
  ├── GLM → script generation, understanding
  ├── OpenAI → GPT-4 scripts, TTS narration
  ├── OpenRouter → model routing
  └── Chutes (likely Coze/Douyin) → ???

  Pipeline:
  Documentation → LLM (script) → Manim (visuals) → OpenAI TTS (audio) → FFmpeg (render)


  ---
  Recommended Solution

  Build a simple pipeline:

  1. Script: Use your existing OpenAI/GLM to generate narration script from package docs
  2. Visuals: Use topic2manim or generative-manim as base - already does the heavy lifting
  3. Audio: OpenAI TTS (you already have)
  4. Render: Manim → MP4

  Option: Fork [https://github.com/mateolafalce/topic2manim](https://github.com/mateolafalce/topic2manim) - it's the closest to "upload doc → get video" and
  already handles AI + TTS + Manim."

## Assistant

NotebookLM's whiteboard style and prompt tweaks help with text clarity, but open-source Manim-based pipelines offer better control for technical GitHub repo assets like banners, infographics, and explainer videos using your subscriptions (Gemini, OpenAI, GLM, OpenRouter).[1][2]

## Top Repo Recommendations
These leverage your APIs for doc-to-video without NotebookLM's rendering quirks. All are Python-based, runnable on Windows 11 with your RTX 5070 for local rendering.[2][3]

| Repo | Key Features | API Fit | Stars/Activity |
|------|--------------|---------|---------------|
| [rohitg00/manim-video-generator](https://github.com/rohitg00/manim-video-generator) | Text prompt → GPT script → Manim visuals → MP4; web UI + Docker. | OpenAI (GPT + TTS). | 133 stars; active.[2] |
| [makefinks/manim-generator](https://github.com/makefinks/manim-generator) | Agentic LLM loop (code writer + reviewer); handles complex docs. | OpenRouter/Claude (configurable to OpenAI/GLM). | 15 stars; 2025 updates.[3] |
| [mateolafalce/topic2manim](https://github.com/mateolafalce/topic2manim) | Topic/doc → full educational video; AI script + Manim + TTS. | GPT/OpenAI; easy fork for Gemini. | Referenced in 2026 posts; educational focus.[4] |
| [ManimCommunity/manim-voiceover](https://github.com/ManimCommunity/manim-voiceover) | Add TTS/voiceover to any Manim scene; Whisper timing. | OpenAI TTS/Azure; pairs with above. | Official plugin; mature.[5] |
| [HarleyCoops/Math-To-Manim](https://github.com/HarleyCoops/Math-To-Manim) | Text/images → math/physics animations; study notes too. | Flexible LLM integration. | 1.1k stars; high activity.[6] |

## Pipeline for Your Workflow
1. Feed repo README/docs to OpenAI/GLM via OpenRouter for conceptual script (use your neutral prompting from prior chats).[7]
2. Generate Manim code with Gemini or Claude (e.g., via makefinks repo's agent loop).
3. Render locally with Manim + manim-voiceover (OpenAI TTS); FFmpeg for final MP4.[5]
4. For images/banners: OpenRouter → Flux/SDXL, then ComfyUI locally.[8]

This assembles "everything" from repos above—no new subs needed. Fork topic2manim as starter; it's closest to NotebookLM automation.[4]

## Quick Start Script
Install Manim: `pip install manim manim-voiceover`. Test with rohitg00 repo (Docker-friendly for your multi-terminal setup).[2]

For infographics/slides: Gamma.app or Beautiful.ai as low-effort alternatives, but Manim excels for technical diagrams.[ from prior chat]

## Human

Is there other information from me that might you optimize the solution?  If yes, what prompt should I give Claude Code (using GLM 5 model).

## Assistant

Yes—there’s a bunch of context that would let Claude/GLM optimize this a lot more, and you can pull it out with one structured “requirements interview” prompt.

Here’s a prompt you can paste into Claude Code (using GLM 5) to have it ask you the right questions and then summarize the answers into a spec it can reuse.

***

### Prompt for Claude Code (GLM 5)

You are helping me design an automated media-generation pipeline for my GitHub repos (images, diagrams, banners, explainer videos, and possibly audio) using APIs I already have (Gemini, GLM, OpenAI, Chutes, OpenRouter, NotebookLM MCP, plus local tools like Manim/FFmpeg/ComfyUI). Use an interview → spec pattern.

1. First, ask me concise, targeted questions in sections to gather everything you need.  
2. Then, produce a single structured specification you can reuse in later prompts.

Follow this structure:

1) MEDIA GOALS  
Ask:  
- What kinds of assets do I actually want per repo (e.g., README hero banner, architecture diagrams, animated explainer, social-thumbnail, favicon/logo, slides)?  
- For each asset type, what’s the priority (must-have vs nice-to-have)?  
- Do I care more about speed/automation or about fine visual control and polish?

2) STYLE & BRAND CONSTRAINTS  
Ask:  
- Preferred visual style(s) (e.g., “PBS Nova”, “McKinsey slideware”, “whiteboard technical”, “retro terminal”, etc.).  
- Color palettes (brand colors, light vs dark, acceptable background colors).  
- Typography preferences (sans vs mono vs serif; any specific fonts if known).  
- Tone of voice for scripts (e.g., neutral, slightly friendly, no hype, audience: senior engineers vs juniors vs PMs).  
- Any hard “no”s: no stock-photo people, no animations behind text, no emojis, no busy backgrounds, etc.  
- Any good examples/links of visuals/scripts I like (YouTube channels, slide decks, GitHub READMEs).

3) REPO TYPES & CONTENT SHAPES  
Ask:  
- What kinds of repos do I have (libraries, CLIs, agents, infra, experiments)?  
- Typical README structure (e.g., intro, features, quickstart, architecture, examples).  
- Which sections should drive visuals/scripts (e.g., use “Concepts” and “Architecture” but ignore “Install” commands)?  
- Any repo-specific quirks (multi-project monorepo, internal vs public, heavy math vs mostly architecture)?

4) TECH CONSTRAINTS & STACK  
Ask:  
- Confirm hardware: GPU (model, VRAM), OS (Windows 11), and tolerance for long local renders.  
- Which APIs I actually want to lean on for:  
  - text + scripts (OpenAI vs GLM vs Gemini)  
  - images (OpenRouter models? which ones if I have preferences)  
  - video (NotebookLM vs Gemini Veo vs local Manim/CogVideoX)  
  - TTS (OpenAI vs something else).  
- Any cost constraints (e.g., “stay on cheap OpenRouter tiers”, “no >$X/month tools”).  
- My preferred glue stack (Python-only, or Python + TS, CLI-first, etc.).  
- How I want to trigger this (manual CLI, git hook, CI job, or one-off script).

5) PIPELINE UX & OUTPUT FORMAT  
Ask:  
- What’s my ideal developer experience? Examples:  
  - One CLI like `gen-media --repo ./path --kind banner,video`  
  - A per-repo config file (e.g., `media.yaml`) checked into the repo  
  - Per-asset JSON specs generated by an AI assistant.  
- Where should outputs go (e.g., `./media/`, `./docs/assets/`, `./static/`)?  
- Preferred resolutions/aspect ratios (e.g., 1920×1080 for video, 1200×630 for social).  
- How much human review do I want in the loop vs full auto?

6) NOTEBOOKLM-SPECIFIC PREFERENCES  
Ask:  
- For NotebookLM videos, what specifically bothers me (e.g., artwork over text, hype tone, pacing, length)?  
- What’s the acceptable trade-off: keep using NotebookLM only for script drafts, or still for full video when okay?  
- How minimal should the “concept-only source” be (e.g., 3–5 paragraphs, bullet summary, etc.)?  
- What script structure do I like (hook → 3–5 sections → recap, or problem → approach → implementation → demo)?

Once you’ve collected all answers, output a single “MEDIA PIPELINE SPEC” in this format:

- Persona & Audience  
- Global Visual Style & Tone Rules  
- Asset Types & Per-Asset Requirements  
- Repo Classification Rules (how to choose which assets for which repos)  
- Tooling Choices (which model/tool per step, with fallbacks)  
- Execution Interface (CLI commands or script entrypoints)  
- NotebookLM Usage Rules (when to use, what prompts, what source format)  

Make it precise enough that you (or another model) can later:  
- Generate concrete prompts for NotebookLM, Gemini, OpenAI, etc.  
- Propose a directory layout and config file schema.  
- Sketch actual Python/TS CLI code to implement the pipeline.

Ask your questions in numbered sections, wait for my answers, then give me the final spec.

## Human

---
  MEDIA PIPELINE SPEC

  Version: 1.0
  Generated: 2025-02-16
  Status: Ready for implementation


  ---
  Persona & Audience

  ┌──────────────────┬────────────────────────────────────────────────────────┐
  │    Attribute     │                         Value                          │
  ├──────────────────┼────────────────────────────────────────────────────────┤
  │ Primary audience │ Mixed: senior engineers, juniors, PMs, technical users │
  ├──────────────────┼────────────────────────────────────────────────────────┤
  │ Tone             │ PBS Nova clinical — neutral, analytical, no hype       │
  ├──────────────────┼────────────────────────────────────────────────────────┤
  │ Authority level  │ Speak with certainty about code; no hedging            │
  ├──────────────────┼────────────────────────────────────────────────────────┤
  │ Content depth    │ Conceptual (WHAT/WHY), not tutorial (HOW)              │
  └──────────────────┴────────────────────────────────────────────────────────┘

  ---
  Global Visual Style & Tone Rules

  Style Defaults (configurable per-repo)

  visual_defaults:
    style: "technical_clean"
    colors: "auto_detect"  # Derive from repo/theme or use neutral slate/blue
    background: "light"    # Light mode default; dark via flag
    font: "sans"           # Inter/Roboto/system-ui; mono for code only
    decoration: "minimal"  # No overlays, no floating elements, no art

  Prohibited Patterns

  prohibited:
    hype_words: ["amazing", "revolutionary", "unlock", "smart", "clever",
                "brilliant", "well", "effectively", "powerful"]
    hedge_words: ["implies", "suggests", "indicates", "likely", "probably",
                 "seems like", "I think"]
    visual_blocking: ["overlays", "decorations behind text", "busy backgrounds",
                     "animations that obscure text"]
    content_patterns: ["code snippets in video", "step-by-step tutorials",
                       "file/module names", "installation commands"]

  Required Patterns

  required:
    script_frames: ["The package provides...", "Components include...",
                    "The architecture handles...", "Use cases involve...",
                    "One consideration is...", "This means that..."]
    visual_clarity: "All text fully readable at all times; solid backgrounds"

  ---
  Asset Types & Per-Asset Requirements

  ┌──────────────────────┬──────────┬────────────────────┬───────────────────────┬───────────────────────┐
  │        Asset         │ Priority │ Default Resolution │     Primary Tool      │       Fallback        │
  ├──────────────────────┼──────────┼────────────────────┼───────────────────────┼───────────────────────┤
  │ README banner        │ Must     │ 1200×200           │ NotebookLM/NotebookLM │ DALL-E via OpenRouter │
  ├──────────────────────┼──────────┼────────────────────┼───────────────────────┼───────────────────────┤
  │ Explainer video      │ Must     │ 1920×1080 (16:9)   │ NotebookLM            │ Manim + TTS           │
  ├──────────────────────┼──────────┼────────────────────┼───────────────────────┼───────────────────────┤
  │ Architecture diagram │ Must     │ 1200×800 (any)     │ NotebookLM Mind Map   │ Mermaid CLI           │
  ├──────────────────────┼──────────┼────────────────────┼───────────────────────┼───────────────────────┤
  │ Social thumbnail     │ Must     │ 1200×630 (OG)      │ NotebookLM/DALL-E     │ OpenRouter image      │
  ├──────────────────────┼──────────┼────────────────────┼───────────────────────┼───────────────────────┤
  │ Slides/PDF           │ Nice     │ 1920×1080          │ NotebookLM Slide Deck │ Manim export          │
  ├──────────────────────┼──────────┼────────────────────┼───────────────────────┼───────────────────────┤
  │ Logo/favicon         │ Nice     │ 512×512 / 32×32    │ DALL-E                │ OpenRouter image      │
  ├──────────────────────┼──────────┼────────────────────┼───────────────────────┼───────────────────────┤
  │ Audio overview       │ Nice     │ N/A                │ NotebookLM Audio      │ OpenAI TTS            │
  └──────────────────────┴──────────┴────────────────────┴───────────────────────┴───────────────────────┘

  Asset-Specific Rules

  Video (NotebookLM):

  - Duration target: 3-5 minutes
  - Conceptual level only (problem → components → architecture → use cases)
  - Visual style: whiteboard
  - No code, no installation steps


  Diagrams:

  - Mind maps for component hierarchies
  - Infographics for feature summaries
  - Mermaid for architecture (rendered via mmdc)


  Banners:

  - Include package name + one-line purpose
  - Clean typography, minimal illustration
  - Legible at small sizes


  ---
  Repo Classification Rules

  def classify_repo(repo_path: Path, readme_content: str) -> RepoType:
      """Determine which assets to generate based on repo type."""

      if is_cli_tool(readme_content):
          return RepoType.CLI  # banner + diagram + quick explainer

      elif is_library(readme_content):
          return RepoType.LIBRARY  # banner + diagram + full video

      elif is_agent_or_skill(readme_content):
          return RepoType.AGENT  # banner + diagram + audio overview

      elif is_infrastructure(readme_content):
          return RepoType.INFRA  # diagram + docs (minimal video)

      else:
          return RepoType.DEFAULT  # banner + diagram

  Content Extraction Rules

  source_sections:
    include:
      - "What is {package}?"
      - "Why {package}?"
      - "Architecture"
      - "Components"
      - "Design patterns"
      - "Use cases"
      - "Concepts"

    exclude:
      - "Installation"
      - "Quickstart"
      - "API reference"
      - "CLI commands"
      - "Examples"  # Use for diagrams, not video

  ---
  Tooling Choices

  Text & Script Generation

  ┌────────────────────┬───────────────┬──────────────────┬───────────────────┐
  │        Task        │    Primary    │     Fallback     │       Notes       │
  ├────────────────────┼───────────────┼──────────────────┼───────────────────┤
  │ Script outline     │ OpenAI GPT-4o │ GLM-4            │ Fast, cheap       │
  ├────────────────────┼───────────────┼──────────────────┼───────────────────┤
  │ Script refinement  │ Claude Sonnet │ Gemini 2.5 Flash │ Quality           │
  ├────────────────────┼───────────────┼──────────────────┼───────────────────┤
  │ Concept extraction │ GLM-4         │ OpenAI           │ Good at structure │
  └────────────────────┴───────────────┴──────────────────┴───────────────────┘

  Image Generation

  ┌───────────────┬───────────────────────────┬─────────────┬───────────────┐
  │     Task      │          Primary          │  Fallback   │     Notes     │
  ├───────────────┼───────────────────────────┼─────────────┼───────────────┤
  │ Banners/logos │ DALL-E 3 (via OpenRouter) │ FLUX.1      │ Quality       │
  ├───────────────┼───────────────────────────┼─────────────┼───────────────┤
  │ Diagrams      │ NotebookLM                │ Mermaid CLI │ Context-aware │
  ├───────────────┼───────────────────────────┼─────────────┼───────────────┤
  │ Thumbnails    │ FLUX.1                    │ SDXL        │ Speed         │
  └───────────────┴───────────────────────────┴─────────────┴───────────────┘

  Video Generation

  ┌────────────────────┬────────────────────┬────────────────────┬────────────────────┐
  │        Task        │      Primary       │      Fallback      │       Notes        │
  ├────────────────────┼────────────────────┼────────────────────┼────────────────────┤
  │ Explainer video    │ NotebookLM Video   │ Manim + OpenAI TTS │ Best for docs      │
  ├────────────────────┼────────────────────┼────────────────────┼────────────────────┤
  │ Animations         │ Manim (local, GPU) │ CogVideoX          │ RTX 5070 capable   │
  ├────────────────────┼────────────────────┼────────────────────┼────────────────────┤
  │ Quick social video │ NotebookLM Brief   │ Skipping           │ Use static instead │
  └────────────────────┴────────────────────┴────────────────────┴────────────────────┘

  Audio

  ┌───────────────────┬──────────────────┬────────────┬─────────────┐
  │       Task        │     Primary      │  Fallback  │    Notes    │
  ├───────────────────┼──────────────────┼────────────┼─────────────┤
  │ Narration         │ NotebookLM Audio │ OpenAI TTS │ Natural     │
  ├───────────────────┼──────────────────┼────────────┼─────────────┤
  │ Voiceover (Manim) │ OpenAI TTS       │ ElevenLabs │ Paid option │
  └───────────────────┴──────────────────┴────────────┴─────────────┘

  Cost Optimization

  preferences:
    free_first: true
    paid_tier: "cheapest viable"
    monthly_budget: "use included subscriptions first"

  routing:
    text: "GLM (free/cheap via subscription)"
    images: "OpenRouter free tiers first"
    video: "NotebookLM (free) → Manim (free, local)"

  ---
  Execution Interface

  Primary CLI

  # Generate all assets for a repo
  gen-media --repo ./path/to/package

  # Generate specific assets
  gen-media --repo ./path --kind banner,video,diagram

  # Force regeneration
  gen-media --repo ./path --force

  # Preview mode (dry run)
  gen-media --repo ./path --dry-run

  # Custom output dir
  gen-media --repo ./path --output ./media


  Per-Repo Config (optional)

  # media.yaml (checked into repo root)
  name: mypackage
  assets:
    banner: true
    video: true
    diagram: true
    thumbnail: true

  style:
    colors: ["#1e293b", "#3b82f6"]  # Custom brand colors
    dark_mode: true

  video:
    max_duration: 240  # seconds
    style: whiteboard

  Output Structure

  repo/
  ├── media/
  │   ├── banner.png              # 1200×200
  │   ├── thumbnail.png           # 1200×630
  │   ├── logo.png                # 512×512
  │   ├── logo-favicon.ico        # 32×32
  │   ├── explainer.mp4           # 1920×1080 video
  │   ├── architecture.png        # 1200×800 diagram
  │   ├── slides.pdf              # Presentation
  │   └── audio-overview.mp3      # Audio only
  └── media.yaml                  # Config (optional)


  ---
  NotebookLM Usage Rules

  When to Use NotebookLM

  use_notebooklm_when:
    - Source documentation exists (README, docs/)
    - Conceptual explanation needed
    - Grounded citations required
    - Free option preferred

  use_alternatives_when:
    - No docs (code-only repos)
    - Custom visual style required
    - NotebookLM rate-limited
    - Fine-grained control needed

  NotebookLM Prompt Template

  # For Video Generation
  nlm video create <notebook-id> \\
    --format explainer \\
    --style whiteboard \\
    --focus "PBS Nova style: Stay at CONCEPTUAL level. Explain:
  1) What problem this package solves
  2) Major components and their roles
  3) Overall architecture and data flow
  4) Key design patterns
  5) When to use this package vs alternatives

  DO NOT: Show code, mention file names, do step-by-step tutorials,
  use hype words (amazing, revolutionary, smart, clever),
  or hedge words (implies, suggests, likely, probably).

  VISUALS: All text fully readable. No overlays, no decorations,
  no art behind text. Solid backgrounds only.

  Speak with authority: 'The package provides...', 'This component
  handles...', 'The architecture handles...'" \\
    --confirm


  Source Format for NotebookLM

  # Concept-Only Source Template

  ## What is {package}?

  {Single paragraph overview}

  ## Why {package} exists?

  {Problem statement, 2-3 sentences}

  ## Key Components

  - **Component A**: {Purpose, 1 sentence}
  - **Component B**: {Purpose, 1 sentence}
  - **Component C**: {Purpose, 1 sentence}

  ## Architecture

  {High-level flow, 2-3 sentences. No code.}

  ## When to Use

  {Use cases, 2-3 bullet points}

  ## Design Patterns

  {Key patterns, 2-3 bullets}

  Script Structure

  Hook (10-15s): "This is {package}. It solves {problem} by {approach}."

  Body (3-4 min):
    - Problem context
    - Component overview
    - Architecture flow
    - Use cases

  Recap (15-20s): "Use {package} when {condition}. Alternatives include {X, Y}."


  ---
  Implementation Checklist

  1. Phase 1: CLI skeleton + repo classifier
  2. Phase 2: NotebookLM integration (video, diagrams, audio)
  3. Phase 3: Fallback tools (Manim, Mermaid, DALL-E via OpenRouter)
  4. Phase 4: Config system (media.yaml)
  5. Phase 5: Optimization (caching, parallel generation)

  ---

## Assistant

You’ve already given almost everything needed; the missing pieces are implementation preferences and a slightly more concrete “build brief” for the CLI and pipelines.

Here are the extra bits of info that would meaningfully optimize the solution, plus a prompt you can drop into Claude Code (GLM 5) to turn that spec into working code.

***

## What additional info would help?

You’ve fully nailed product requirements; what’s left are *implementation* constraints and preferences:

- Language/runtime boundaries  
  - How much of `gen-media` must be pure Python vs Python + Node/TS?  
  - Any hard bans (e.g., no Docker, no Poetry, no Conda; prefer uv/pdm/pipx)?

- Integration with your existing monorepo  
  - Where should this live (e.g., `tools/gen_media/`, top-level `media/` package)?  
  - Any shared config conventions you already use (`.csf`, `config.toml`, etc.)?  

- CI and hooks  
  - Should `gen-media` be CI-only (GitHub Actions), local-only, or both?  
  - Should it auto-run on tag / release, or only on explicit command?

- Authentication and secrets  
  - How you want to centralize API keys for OpenRouter, OpenAI, Gemini, GLM, NotebookLM MCP (single `.env` vs per-project)?  
  - Any existing secret-management you want reused?

- Minimal viable subset  
  - In what order should we actually build features? For example:  
    - Phase 1 real target: `banner + architecture diagram` only.  
    - Phase 2: explainer video (NotebookLM only).  
    - Phase 3: Manim fallback.  
  - This avoids over-building in v1.

If you answer those, Claude/GLM can generate code that drops straight into your monorepo with fewer refactors.

***

## Prompt for Claude Code (GLM 5) to generate the implementation

Paste this into Claude Code, then answer its questions when it asks. It will use your MEDIA PIPELINE SPEC as the authoritative requirements doc.

```text
You are an expert Python/TypeScript tooling architect working inside a large monorepo. I will give you a full MEDIA PIPELINE SPEC that describes how to generate media assets (banners, diagrams, explainer videos, etc.) for my GitHub repos using NotebookLM, OpenRouter/OpenAI, GLM, Gemini, Manim, Mermaid, and local tools.

Your tasks:

1) Ingest the MEDIA PIPELINE SPEC (below) as the authoritative product requirements.
2) Ask me ONLY the additional implementation questions you truly need, in three short sections:
   A. Repo & tooling integration
   B. Secrets/config management
   C. MVP scope & rollout
3) After I answer, design a concrete implementation plan AND generate starter code.

Use these strict guidelines:

- Language & stack
  - Primary implementation in Python 3.11+.
  - CLI via `typer` or `click` (ask me which I prefer).
  - Config as `media.yaml` (as described in the spec) plus sensible defaults when missing.
  - Assume Windows 11 dev environment; GitHub Actions for CI is allowed but optional.

- Interfaces to build
  - A Python package `media_pipeline` with:
    - `classifier.py` – implements `classify_repo(...)` and section extraction per spec.
    - `notebooklm_client.py` – thin wrapper around my existing NotebookLM MCP CLI.
    - `images.py` – wrappers to OpenRouter / DALL-E / FLUX.1.
    - `video.py` – NotebookLM video trigger + Manim fallback stub.
    - `config.py` – load/merge defaults + `media.yaml`.
    - `cli.py` – implements the `gen-media` CLI exactly as in the spec.
  - Proper separation of “planning” vs “execution”: first compute a media plan, then run it.

- Behavioural rules to respect (from the spec)
  - Persona & audience, tone (PBS Nova clinical, no hype, authoritative).
  - Global visual constraints (no overlays, solid backgrounds, conceptual level only).
  - Asset table priorities and resolutions.
  - Repo classification rules and `source_sections.include/exclude`.
  - Tooling choices: default to free/cheap routes, NotebookLM first for video, Manim as fallback.

- What I want as output (after I answer your questions)
  1) A short IMPLEMENTATION PLAN:
     - Directory layout for the new package.
     - List of Python modules and their responsibilities.
     - Sequence diagram-style description (in text) of the end-to-end flow for `gen-media --repo ./path`.
  2) Initial CODE SKELETONS:
     - `media_pipeline/cli.py` with Typer/Click commands wired up (no heavy logic).
     - `media_pipeline/config.py` with default config + load from `media.yaml`.
     - `media_pipeline/classifier.py` with stubs for `classify_repo` and `extract_relevant_sections`.
     - `media_pipeline/notebooklm_client.py` with a stub that shells out to a `nlm` CLI command using the prompt template and concept-only source.
  3) A TODO list (ordered) for filling in the rest:
     - NotebookLM integration details.
     - OpenRouter image call placeholders.
     - Manim + TTS fallback hooks.
     - CI integration (optional).

Here is the MEDIA PIPELINE SPEC (treat this as read-only product requirements, do not rewrite it, only reference it):

[PASTE THE FULL MEDIA PIPELINE SPEC HERE]
```

If you want, I can next help you refine that prompt specifically for `typer` vs `click`, or add a follow-up prompt that takes Claude’s first draft of `cli.py` and hardens it (logging, error handling, dry-run planning, etc.).

## Human

I'm surprised there isn't already a repo for this kind of requirement.

## Assistant

You’re right to be surprised; there are adjacent pieces, but nobody has shipped exactly what you specced.

Most existing projects either do a **single leg** of the flow or target a different use case:

- NotebookLM-style clones and automators focus on “PDF to podcast/video” or study aids, not repo-aware multi-asset pipelines.[1][2][3]
- README→video tools like README2Video turn a README into a promo clip, usually via a single web app, not a programmable CLI that also does banners, diagrams, and audio in one pass.[4]
- Diagram generators focus only on diagrams in READMEs (PlantUML, Mermaid, kmoskwiak/readme-diagram) and don’t touch thumbnails, videos, or NotebookLM integration.[5]
- There are open NotebookLM implementations and “open notebook” projects, but they mainly reproduce NotebookLM’s UI/workflow, not orchestrate multiple external APIs per repo.[6][3][7]
- Code2Video / Manim-based tools handle “code or topic → animation/video”, but they’re not wired into repo classification + banner + social thumbnail + audio the way your MEDIA PIPELINE SPEC is.[8][9]

So your spec is effectively a **product-level integration layer** across tools that currently live in silos. The gap is:

- No opinionated, repo-first CLI (`gen-media`) that:  
  - classifies repo type from README,  
  - extracts conceptual sections,  
  - calls NotebookLM for conceptual video/audio,  
  - calls image models for banners/thumbnails,  
  - falls back to Manim/Mermaid when needed,  
  - and writes a consistent `media/` tree as part of the repo.

That breadth plus your strict style/tone constraints is what makes it novel; most OSS projects stop at “cool demo” rather than “boring but complete devtool.”[5][4]

If you build this as a clean Python CLI with pluggable backends, it would genuinely fill a gap—especially for people already using NotebookLM or its open-source counterparts.

## Human

● I have the MEDIA PIPELINE SPEC from our previous conversation. Before I design the implementation, I have 3
  short sections of clarification questions:

  ---
  A. Repo & Tooling Integration

  A1. Where should media_pipeline live?
  - As a new package in P:/packages/media-pipeline/
  - As a module within portfolio-media package
  - As a standalone CLI in P:/__csf/src/commands/media-gen/
  - Other: _______

  A2. CLI framework preference?
  - typer (modern, type-friendly, my preferred recommendation)
  - click (battle-tested, more verbose)
  - No preference — you decide

  A3. Existing NotebookLM integration?
  - You have portfolio-media/src/portfolio_media/providers/notebooklm.py — should I:
    - Reuse this directly
    - Extract a shared wrapper both can use
    - Build fresh in media_pipeline with different interface

  ---
  B. Secrets & Config Management

  B1. API keys — where do they live?
  - Environment variables (OPENAI_API_KEY, OPENROUTER_KEY, etc.)
  - P:/__csf/.env (loaded via python-dotenv)
  - A ~/.media_pipeline/config.toml
  - Other: _______

  B2. media.yaml — required or optional?
  - Optional — sensible defaults if missing
  - Required — fail if not present
  - Generate default on first run

  B3. Output directory — what if user doesn't specify --output?
  - Default to ./media/ in repo root
  - Default to ./docs/assets/
  - Configurable in media.yaml

  ---
  C. MVP Scope & Rollout

  C1. MVP feature scope — what's the minimum viable first version?
  - Just NotebookLM video + diagram (you already have this working)
  - Video + diagram + banner (add image generation)
  - Full asset suite (all 7 asset types)

  C2. Testing strategy — how do you want to validate this works?
  - Run on portfolio-media package itself first
  - Run on a dummy test repo
  - Dry-run mode that prints what would be generated

  C3. Iteration approach — after initial skeleton:
  - You'll manually refine each module
  - You want me to fill in stubs progressively
  - You'll use TDD (write tests first)

  ---
  Answer A1-C3 briefly and I'll produce the implementation plan + code skeletons.

❯ make suggestions for my review.

● Answers

  A1. New package in P:/packages/media-pipeline/

  A2. typer

  A3. Extract shared wrapper — both portfolio-media and media_pipeline should use the same NotebookLM client

  B1. P:/__csf/.env (python-dotenv)

  B2. Optional — sensible defaults if missing

  B3. Default to ./media/ in repo root; configurable in media.yaml

  C1. NotebookLM video + diagram + banner (extend what you have)

  C2. Run on portfolio-media package itself first

  C3. You'll manually refine each module; I provide skeletons + TODO list

  ---
  Now let me search for existing code to reference before building.

● Searched for 6 patterns, read 5 files (ctrl+o to expand)
  ⎿  Loaded __csf\\CLAUDE.md

● Good context on existing patterns. Now I'll create the implementation plan and code skeletons.

  ---
  IMPLEMENTATION PLAN

  Directory Layout

  P:/packages/media-pipeline/
  ├── pyproject.toml
  ├── README.md
  ├── src/
  │   └── media_pipeline/
  │       ├── __init__.py
  │       ├── __main__.py          # Entry point for `python -m media_pipeline`
  │       ├── cli.py               # Typer CLI commands
  │       ├── config.py             # Config loading + defaults
  │       ├── classifier.py         # Repo classification + section extraction
  │       ├── planning.py           # Media plan computation
  │       ├── providers/
  │       │   ├── __init__.py
  │       │   ├── base.py           # Abstract base class
  │       │   ├── notebooklm.py     # NotebookLM wrapper (shared)
  │       │   ├── images.py         # OpenRouter/DALL-E wrapper
  │       │   └── video.py          # Video generation (NotebookLM + Manim fallback)
  │       └── prompts/
  │           ├── __init__.py
  │           └── templates.py      # PBS Nova style templates
  └── tests/
      ├── __init__.py
      ├── test_cli.py
      ├── test_classifier.py
      └── test_config.py


  Module Responsibilities

  ┌─────────────────────────┬───────────────────────────────────────────────────────────────┐
  │         Module          │                        Responsibility                         │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────┤
  │ cli.py                  │ Typer command parsing, orchestrates classify → plan → execute │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────┤
  │ config.py               │ Load media.yaml, merge with defaults, validate                │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────┤
  │ classifier.py           │ Detect repo type, extract relevant sections from README       │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────┤
  │ planning.py             │ Compute which assets to generate based on repo type + config  │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────┤
  │ providers/notebooklm.py │ Create notebook, add sources, generate video/diagram/audio    │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────┤
  │ providers/images.py     │ Generate banners/logos via OpenRouter                         │
  ├─────────────────────────┼───────────────────────────────────────────────────────────────┤
  │ providers/video.py      │ Orchestrate NotebookLM video or Manim fallback                │
  └─────────────────────────┴───────────────────────────────────────────────────────────────┘

  End-to-End Flow

  gen-media --repo ./path --kind banner,video

  1. CLI validates repo path exists
  2. Classifier analyzes repo:
     - Reads README.md
     - Detects repo type (LIBRARY, CLI, AGENT, INFRA)
     - Extracts relevant sections (Concepts, Architecture, excludes Install)
  3. Planner builds media plan:
     - Based on repo type + --kind flag + media.yaml
     - Determines which assets to generate
     - Selects tools for each asset
  4. Executor runs plan:
     - For each asset: invoke appropriate provider
     - NotebookLM: create/reuse notebook → add concept-only source → generate → download
     - Images: call OpenRouter with prompt → save to ./media/
  5. Report results: success/fail per asset, output paths


  ---
  CODE SKELETONS

● Bash(mkdir -p "P:/packages/media-pipeline/src/media_pipeline/providers"
      "P:/packages/media-pipeline/src/media_pipeline/prompts" "P:/packages/media-pipeline/tests")
  ⎿  Done

● Write(packages\\media-pipeline\\pyproject.toml)
  ⎿  Wrote 1 lines to packages\\media-pipeline\\pyproject.toml
       1 [project]
       2 name = "media-pipeline"
       3 version = "0.1.0"
       4 description = "Automated media asset generation for GitHub repos"
       5 readme = "README.md"
       6 requires-python = ">=3.11"
       7 license = {text = "MIT"}
       8 authors = [
       9     {name = "CSF Development"}
      10 ]
  ⎿  Interrupted · What should Claude do instead?

❯ areyou implementing?  I have to review the solution first, then the plan.

● No — I'm presenting the plan for YOUR review first. I created the pyproject.toml and directories, but I
  haven't written the core code yet.

  Here's the plan for you to review:

  ---
  MEDIA PIPELINE IMPLEMENTATION PLAN

  1. Directory Structure (already created)

  P:/packages/media-pipeline/
  ├── pyproject.toml          ✅ Created
  ├── README.md               ⏳ To write
  ├── src/
  │   └── media_pipeline/
  │       ├── __init__.py     ⏳ To write
  │       ├── __main__.py     ⏳ To write
  │       ├── cli.py          ⏳ To write (Typer commands)
  │       ├── config.py       ⏳ To write (media.yaml + defaults)
  │       ├── classifier.py   ⏳ To write (repo type detection)
  │       ├── planning.py     ⏳ To write (media plan computation)
  │       ├── providers/
  │       │   ├── __init__.py
  │       │   ├── notebooklm.py   ⏳ To write (shared wrapper)
  │       │   ├── images.py       ⏳ To write (OpenRouter)
  │       │   └── video.py        ⏳ To write (NotebookLM + Manim)
  │       └── prompts/
  │           ├── __init__.py
  │           └── templates.py    ⏳ To write (PBS Nova templates)
  └── tests/                   ✅ Directory created


  2. Module-by-Module Design

  cli.py — Typer entry point

  # Commands:
  gen-media --repo ./path                    # Generate all configured assets
  gen-media --repo ./path --kind banner,video # Specific assets
  gen-media --repo ./path --dry-run          # Show plan, don't execute
  gen-media --repo ./path --output ./media   # Custom output dir
  gen-media --repo ./path --force            # Regenerate existing

  config.py — Config loading

  # Defaults if media.yaml missing:
  DEFAULT_CONFIG = {
      "assets": {"banner": True, "video": True, "diagram": True},
      "style": {"colors": "auto", "background": "light", "font": "sans"},
      "output_dir": "./media/",
  }
  # Load from media.yaml if present, merge with defaults

  classifier.py — Repo analysis

  class RepoType(Enum):
      LIBRARY = "library"    # Full video + diagrams
      CLI = "cli"           # Diagram + quick explainer
      AGENT = "agent"       # Diagram + audio overview
      INFRA = "infra"       # Diagram only, minimal video
      DEFAULT = "default"   # Banner + diagram

  def classify_repo(readme_content: str) -> RepoType
  def extract_relevant_sections(readme: Path) -> dict  # include/exclude per spec

  providers/notebooklm.py — Shared wrapper

  class NotebookLMClient:
      # Extract reusable methods from portfolio-media's provider
      async def create_notebook(title: str) -> str  # returns notebook_id
      async def add_source(notebook_id: str, content: str) -> bool
      async def create_video(notebook_id: str, focus_prompt: str) -> dict
      async def create_diagram(notebook_id: str, diagram_type: str) -> dict
      async def download_artifact(notebook_id: str, artifact_type: str, output: Path) -> dict

  providers/images.py — OpenRouter wrapper

  class ImageGenerator:
      async def generate_banner(package_name: str, description: str, output: Path) -> dict
      async def generate_thumbnail(package_name: str, output: Path) -> dict
      # Uses OPENROUTER_API_KEY from .env

  prompts/templates.py — PBS Nova prompts

  CONCEPT_ONLY_SOURCE_TEMPLATE = """# What is {package}?
  ...

  ## Key Components
  ...
  """

  VIDEO_FOCUS_PROMPT = """PBS Nova style: Stay at CONCEPTUAL level...
  [Full spec prompt from earlier]
  """

  3. Shared NotebookLM Provider Strategy

  Instead of duplicating code:
  1. Extract common NotebookLM CLI logic to media-pipeline
  2. portfolio-media imports from media-pipeline.providers.notebooklm
  3. Both use the same nlm CLI wrapper

  4. Flow Sequence

  1. User runs: gen-media --repo ./portfolio-media
  2. cli.py validates path, loads config
  3. classifier.py analyzes README, returns RepoType.LIBRARY + extracted sections
  4. planning.py builds plan: [banner, diagram, video] based on repo type
  5. For each asset:
     - banner → providers/images.py → OpenRouter → ./media/banner.png
     - diagram → providers/notebooklm.py → mind_map → ./media/architecture.png
     - video → providers/notebooklm.py → video → ./media/explainer.mp4
  6. Report: Success/Failed per asset with paths


  ---
  TODO List (Ordered)

  1. Core skeletons — __init__.py, config.py, cli.py stubs
  2. Classifier — Repo type detection + section extraction
  3. NotebookLM client — Extract from portfolio-media, make reusable
  4. Image generation — OpenRouter stubs (can fill later)
  5. Planning — Map repo type → asset list
  6. Templates — PBS Nova prompts
  7. Integration — Wire end-to-end flow
  8. Testing — Run on portfolio-media itself

## Assistant

You’re in a good spot: that plan is solid; I’d just tighten scope and interfaces so v1 is small, testable, and doesn’t overcommit.

Here are focused suggestions you can feed back into Claude/GLM as “review comments.”

***

## 1. Narrow the MVP assets

For v1, I’d explicitly lock scope to:

- Banner (single static image)  
- One architecture diagram (PNG)  
- One explainer video (NotebookLM only, no Manim fallback yet)

Comment to give Claude:

> Treat Manim fallback, thumbnails, logos, slides, and audio as Phase 2+.  
> Phase 1 assets are strictly: `banner.png`, `architecture.png`, `explainer.mp4`.

This keeps `providers/video.py` very thin at first (just delegating to NotebookLM).

***

## 2. Make the plan/execution split explicit

Right now “planner vs executor” is implied, not concrete. I’d have Claude add:

- `planning.py`  
  - `plan_media(repo_info, config, kinds) -> list[PlannedAsset]`  
- `executor.py`  
  - `execute_plan(plan, providers, output_dir)`

Review comment:

> Add `executor.py` and a `PlannedAsset` dataclass so `cli.py` can:  
> 1) build a plan, 2) show it in `--dry-run`, 3) execute it.  
> Keep providers stateless and injected into the executor.

***

## 3. Tighten config behavior

Make the config contract explicit so you don’t fight implicit defaults later:

- `media.yaml` optional; if missing, behave as:
  - assets: banner + video + diagram = true  
  - output_dir: `./media`  
  - style: your defaults from the spec.

Review comment:

> In `config.py`, expose:
> - `load_config(repo_root: Path) -> MediaConfig`
> - `resolve_output_dir(config, cli_output_override) -> Path`
> and document the exact precedence: CLI flag > media.yaml > defaults.

***

## 4. Design the NotebookLM client API before coding

You’ll reuse it across `portfolio-media` and `media-pipeline`, so its interface should be boring and stable:

Suggested high-level API:

```python
class NotebookLMClient:
    def __init__(self, env: Optional[Mapping[str, str]] = None): ...

    def ensure_notebook(self, title: str) -> str: ...
    def sync_concept_source(self, notebook_id: str, concept_text: str) -> None: ...

    def generate_video(self, notebook_id: str, focus_prompt: str) -> Path:
        """Returns path to downloaded mp4."""

    def generate_mindmap_image(self, notebook_id: str, output: Path) -> Path:
        """Mind map/diagram to PNG."""
```

Review comment:

> Please design `NotebookLMClient` to hide all `nlm` CLI details and only expose:
> - `ensure_notebook`
> - `sync_concept_source`
> - `generate_video`
> - `generate_mindmap_image`
> Then refactor `portfolio-media` to import this class instead of duplicating logic.

***

## 5. Simplify `providers/images.py` for v1

For the banner, keep the interface very small and text-only:

```python
class ImageGenerator:
    def generate_banner(self, package_name: str, tagline: str, output: Path) -> Path:
        ...
```

The generator can internally:

- Build a PBS-Nova-ish, technical-clean prompt.  
- Route to OpenRouter’s default high-quality model.

Review comment:

> For MVP, only implement `generate_banner(package_name, tagline, output)`.  
> Thumbnails/logos can be left as TODOs with clear stubs.

***

## 6. Constrain classifier output shape

You already have repo types; make sure you also standardize the content extraction:

```python
@dataclass
class RepoInfo:
    root: Path
    repo_type: RepoType
    package_name: str
    tagline: str
    concept_text: str        # filled from “What/Why/Components/Architecture”
```

Review comment:

> Have `classifier.analyze_repo(path: Path) -> RepoInfo`, where `RepoInfo` includes:
> - `package_name`
> - `tagline` (one-line purpose)
> - `concept_text` for NotebookLM
> This keeps downstream providers simple (no re-reading README).

***

## 7. Logging and dry-run

Ask Claude to bake in:

- `--verbose` flag.  
- Dry-run output that prints the `PlannedAsset` list clearly.

Review comment:

> In `cli.py`, implement:
> - `--dry-run`: print a table of planned assets (type, tool, output path) and exit 0.  
> - `--verbose`: basic logging via `logging` module, no custom framework.

***

If you want, you can paste these as a follow-up message in Claude Code like:

> “Here is my review of the implementation plan. Please update the plan and skeletons accordingly before writing any more files: …”

That will nudge it toward a small, composable v1 that’s easy to refactor as you live with it.
