---
title: "I use claude code on windows 11, but I have access to Chutes.ai, OpenRouter, Gemini CLI and API, Qwen CLI, Perplexity AP"
date: "2026-02-16"
mode: "COPILOT"
uuid: "705813e5-4855-4a7d-b62f-d15f884db962"
entry_count: 3
---

## Human

I use claude code on windows 11, but I have access to Chutes.ai, OpenRouter, Gemini CLI and API, Qwen CLI, Perplexity API, GLM Coding Plan.

I want to make gen ai images and video for my github repos.  What repos can I use that will help me make the media, with the apis I have available.  Free or almost free (subscription) please so I don't spend money on expensive ai models.

## Assistant

You can get a surprisingly good image/video pipeline for GitHub using OpenRouter + local tools, without touching expensive proprietary stuff.[1][2]

## Overall approach

Use:
- OpenRouter for cheap hosted **image** models.[2]
- Local / Colab open-source **video** generators (CogVideoX, Open-Sora, etc.).[3][1]
- ComfyUI or simple Python CLIs as the glue.

Below are concrete repos that fit your APIs and cost constraint.

***

## Image generation repos (OpenRouter, Gemini, Qwen, Perplexity)

These give you programmatic image gen you can script from your Windows workflows.

### 1. OpenRouter image generation + SDKs

- **Docs / model list**: OpenRouter image generation guide shows how to call any model with `output_modalities: ["image"]` and includes examples plus model names like `google/gemini-2.5-flash-image-preview`, `black-forest-labs/flux.2-flex`, etc.[2]
- For code, use:
  - `@openrouter/sdk` (TypeScript/JS) from the docs snippet for basic image gen.[2]
  - Any OpenAI-compatible Python client with the OpenRouter base URL; just set `response_format` / `modalities` per the docs.[2]

This is probably your lowest-friction entry point: one API key, multiple image models, and a simple function like `generate_repo_hero_image(repo_name, features)`.

### 2. ComfyUI with OpenRouter node (local image workflows)

- **Repo**: `gabe-init/ComfyUI-Openrouter_node`.[4]
  - Adds a node to ComfyUI that can call **any** OpenRouter model, including image-capable ones like `google/gemini-2.5-flash-image-preview` (“Nano Banana”).[4][2]
  - Supports multiple image inputs and explicit “image generation support” with prompt-based detection.[4]

Usage pattern for you:
- Run **ComfyUI** locally on Windows.
- Install this OpenRouter node.
- Create workflows:
  - “Generate GitHub README banner.”
  - “Generate architecture diagram style image from prompt.”
- Trigger them via CLI or HTTP from your dev scripts.

This offloads the “prompt → PNG” part to a visual node graph while still using your OpenRouter budget.

### 3. Gemini / Qwen CLIs as image frontends

- **Gemini CLI**: Official Google `gemini-cli` project is open source and actively maintained; you can plug in a Gemini model that supports images if available in your account.[5]
- **Qwen code agent**: `QwenLM/qwen-code` is a multi-protocol agent that works with OpenAI / Anthropic / Gemini-compatible APIs and has a free-tier via Qwen OAuth (1,000 free requests/day).[6]

You could:
- Use Gemini CLI for one-off asset generation from the terminal (“create a 16:9 cover art for this repo”).[5]
- Use `qwen-code` for scripted calls where it writes prompts, calls an image model via OpenRouter / Qwen, and saves images next to the repo.[6]

### 4. Perplexity API clients (mainly for text, maybe images later)

Perplexity has community Go clients like `sgaunet/perplexity-go` and `michaelJyee/perplexity-go` that already handle chat completions and mention image-related flags in closed beta (`return_images`).[7][8]
Right now they’re stronger as **LLM helpers** (e.g., “design me five hero-image prompts”), then you feed those prompts into OpenRouter image models.

***

## Video generation repos (text/image to video)

You’ll need either a GPU box or Colab, but everything below is open-source and free to run.

### 5. CogVideoX: text & image to video

- **Repo**: `zai-org/CogVideo`.[1]
  - Implements CogVideoX-2B and 5B text-to-video and image-to-video models.[1]
  - Designed so CogVideoX-2B can run on free T4 Colab or modest GPUs.[1]

Use cases for your GitHub:
- Short 2–4s loops showing “code morphing into diagrams” as repo intros.
- Image-to-video: feed it the hero image you generated via OpenRouter and animate it.

### 6. Open-Sora

- **Repo**: `hpcaitech/Open-Sora`.[3]
  - Aims at “democratizing efficient video production,” focusing on making high-quality video generation accessible.[3]

This is good when you want slightly longer, more cinematic repo demos (e.g., “AI agents collaborating in a terminal”) and are willing to spin up a beefier GPU instance or Colab Pro.

### 7. ComfyUI + video workflows (HunyuanVideo, etc.)

ComfyUI has community workflows for open-source video models (e.g., HunyuanVideo 1.5) that can run on consumer GPUs (though model weights are large, ~15 GB).[9]
You can:
- Use ComfyUI for both image and video.
- Start from the hero image and apply an image-to-video workflow for subtle motion (camera pan, particle effects).[9]

***

## How to wire this into your existing stack

Given your setup (Claude Code router, Chutes, OpenRouter, Gemini CLI, Qwen CLI, Perplexity, GLM Coding Plan):

- Use **Claude Code** + router to orchestrate:
  - Prompt design for images → call OpenRouter image endpoint or ComfyUI-OpenRouter node.[4][2]
  - Prompt design/storyboards for video → generate scripts + shot descriptions.
- Use **OpenRouter** as the central “cheap images” API, swap models if one gets pricey.[2]
- Use **CogVideoX / Open-Sora** for periodic video exports (short repo trailers) instead of per-commit stuff, to keep GPU time low.[3][1]
- Lean on **Perplexity / Gemini / Qwen** mainly for planning, prompt generation, and captioning, not for the image/video compute itself.[8][7][6]

***

## If you want, next step

Tell me:
- Rough GPU you have locally (VRAM).
- Typical asset types you want (e.g., hero banners, simple animations, code-diagram mashups).

I can then sketch a minimal “media pipeline” repo for you (Python/TS) that glues OpenRouter + ComfyUI + CogVideoX into a single `/gen-media` command per project.

## Human

NVIDIA GeForce RTX 5070 12gb

## Assistant

Your RTX 5070 with 12GB VRAM is solid for ComfyUI image/video workflows—handles Flux/Hunyuan/CogVideoX-2B comfortably, CogVideoX-5B with tweaks (lower res/frames), and LTX-2 easily.[1][2][3]

## Recommended setup

Install **ComfyUI** locally on Windows (portable standalone works great with your Claude Code flows).[1]
Pair it with OpenRouter node for images + local video models.[4]
This keeps everything free/low-cost via your APIs + open models.

## Image workflows (instant, cheap)

Use **ComfyUI + OpenRouter node** for hero banners/diagrams.[4][1]

- **Models**: Flux.2-dev/flex via OpenRouter (cheap credits), or local Flux Schnell (fits 12GB).[1]
- **Workflow**: Load a JSON from NVIDIA RTX Garage (e.g., FLUX.2-dev starter), tweak for repo themes like "cyberpunk code matrix with Python icons".[1]
- **Cost**: Pennies per image on OpenRouter; zero for local.[5]

Example output: 1024x1024 PNGs for READMEs.

## Video workflows (5-15 min/gen)

Focus on **image-to-video** for repo trailers (start from your gen image).[6]
RTX 5070 crushes 720p/6-10s clips; use FP16/quantized for 12GB fit.[2][3]

### Top picks for your GPU

| Model | Repo/Wrapper | Frames/Res | Time on ~RTX 5070 equiv | Notes |
|-------|--------------|------------|-------------------------|-------|
| **CogVideoX-2B** | `kijai/ComfyUI-CogVideoXWrapper` [7] | 49 frames @ 480p | 4-5 min [8] | Text/image-to-video; loops well; max 16GB peak [9] |
| **HunyuanVideo** | ComfyUI Hunyuan nodes (official workflows) [6][10] | 81 frames @ 720p | 8 min [6] | Best img2vid fidelity; fast LoRA variants [11] |
| **LTX-2** | LTX-Video ComfyUI workflow [1][12] | 20s @ 720p+ | ~5 min [12] | Fully open; audio sync possible; RTX-optimized [1] |
| **Open-Sora** | `hpcaitech/Open-Sora` [13] | Short clips | 1 min+ [13] | Basic; viable but slower on 12GB vs 24GB [13] |

- **Start here**: Download Hunyuan img2vid JSON, drop into ComfyUI—it auto-grabs models/VAEs.[6]
- **Pro tip**: Chain image gen → img2vid in one workflow (FLUX image → Hunyuan/LTX motion).[1]

## Quick-start script for your stack

Here's a PowerShell/Python snippet to hook into Claude Code / your CLIs:

```powershell
# Save as gen-repo-media.ps1; run from repo root
$repoName = (git remote get-url origin) -replace '.*\/', ''
$prompt = "Futuristic $repoName dashboard, Python code glowing, cyberpunk style"

# Step 1: Gen image via OpenRouter (use your API key)
curl -H "Authorization: Bearer $env:OPENROUTER_API_KEY" `
  https://openrouter.ai/api/v1/chat/completions `
  -d "{
    'model': 'black-forest-labs/flux-2-flex',
    'messages': [{'role':'user','content':'$prompt'}],
    'output_modalities': ['image']
  }" | jq -r '.choices[0].message.content' | base64 -d > hero.png

# Step 2: Load ComfyUI workflow, queue img2vid via API
# (Point to http://localhost:8188; use kijai wrapper for CogVideoX)
Invoke-WebRequest -Uri "http://localhost:8188/prompt" -Method POST -Body @{
  "prompt" = (Get-Content "hunyuan_img2vid.json" | ConvertFrom-Json)
  "hero.png" = (Get-Content hero.png -Encoding Byte)
} -ContentType "application/json"

# Step 3: Optional: Qwen/Gemini CLI for captions
qwen-cli "Caption this video for GitHub: $prompt"
```

Adapt the ComfyUI API payload from a downloaded workflow JSON.[1]

## Integration with your tools

- **Claude Code hooks**: Add a `/gen-media` command that runs the above, commits PNG/MP4 to `./media/`.
- **OpenRouter**: Handles 90% of images; fallback to local.[5]
- **Perplexity API**: Batch-generate prompts ("10 variants for monorepo viz").
- **Chutes.ai / GLM**: If they have image endpoints, slot in; else use for orchestration.

This gives pro-level repo visuals (e.g., animated code flows) without subscriptions beyond OpenRouter pennies. Test CogVideoX first—your 5070 will eat it.[7][9]

## Human

does notebooklm or gemini apis create videos?  we have the notebooklm mcp server now.

## Assistant

Yes, both NotebookLM (via its MCP server) and Gemini APIs can generate videos, making them viable for your repo media pipeline alongside ComfyUI.[1][2]

## NotebookLM video generation

NotebookLM creates "Video Overviews"—narrated explainer videos with slides, visuals, and AI voices from your sources (PDFs, notes, URLs).[3][1]
With your **NotebookLM MCP server**, you get **programmatic API access**: add sources (Drive/YouTube/text), then generate videos in styles like classroom/documentary/animated.[4][5]
- **Free tier**: Leverages Gemini backend; outputs MP4s downloadable via API.[4]
- **Repo fit**: Feed it repo README/code/docs → auto-generate 1-5min demo videos (e.g., "explainer for my Claude Code hooks"). Customize with steering prompts for audience/tech focus.[1]

Example MCP flow: `generate video overview --style=cinematic --prompt="Summarize this monorepo for devs" --sources=repo_readme.md` → MP4 ready.[4]

## Gemini API video generation

Gemini now includes **Veo 3.1** for native text/image-to-video with audio, portrait/landscape, 4K, extensions, and image guidance.[2][6]
- **Capabilities**: High-fidelity cinematic clips (e.g., "Python code compiling into 3D viz"); poll async operations for MP4 download.[2]
- **Free/low-cost**: Preview tier in Gemini API; fits your CLI/API access.[2]
- **Repo fit**: Script short trailers from prompts like "RTX 5070 rendering ComfyUI workflow"; chain with NotebookLM for narrated versions.[2]

Code snippet from docs (Python):
```python
from google import genai
client = genai.Client()
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    prompt="Animated GitHub repo demo: code → neural net → visuals",
    config=genai.types.GenerateVideosConfig(aspect_ratio="16:9")
)
# Poll until done, then download MP4
```


## Comparison for your setup

| Tool | Video Style | Programmatic? | Cost | Best Repo Use |
|------|-------------|---------------|------|---------------|
| **NotebookLM MCP** [4] | Slides + narration (explainer) | Yes (full API) | Free (Gemini-backed) | Doc-heavy overviews, tutorials |
| **Gemini Veo 3.1** [2] | Cinematic/text-to-video w/ audio | Yes (API/CLI) | Preview free | Creative trailers, animations |
| **ComfyUI (prior)** [7] | Raw img/text-to-video | Local workflows | Free local | Custom motion, unlimited |

**Recommendation**: Use NotebookLM MCP first for "talking head" repo intros (feed your code/docs)—zero extra setup since you have the server. Fall back to Gemini Veo for pure visuals or ComfyUI for GPU-heavy tweaks.[4][2]
Hook into your PowerShell script: add MCP calls before/after OpenRouter images.
