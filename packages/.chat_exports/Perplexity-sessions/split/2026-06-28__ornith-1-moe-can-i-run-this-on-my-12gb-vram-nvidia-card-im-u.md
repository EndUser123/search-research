---
title: "Ornith-1 MoE, can I run this on my 12gb vram nvidia card?  I'm using windows 11 and lmstudio."
date: "2026-06-28"
mode: "COPILOT"
uuid: "38bff369-aaf3-4c7e-aeee-af53c396b644"
entry_count: 3
---

## Human

Ornith-1 MoE, can I run this on my 12gb vram nvidia card?  I'm using windows 11 and lmstudio.

## Assistant

Short answer: No, Ornith‑1 MoE in its current public forms is too large to run fully on a single 12 GB consumer GPU under Windows 11 + LM Studio; you’d need either a much smaller variant, heavier quantization plus offloading, or a different model altogether.[1][2]

## What “Ornith‑1 MoE” actually is

There are (at least) two relevant Ornith‑1 variants floating around:

- Ornith‑1.0‑397B (massive MoE, ~397 B parameters).  
  For FP16 inference this needs on the order of 865 GB of VRAM; even at INT4 it’s still ~216 GB, well beyond any single consumer card.[1]

- Ornith‑1.0‑35B (MoE ~35 B, with active parameters ~3 B but full experts still heavy).  
  A validated Q3_K_M quant of this 35B model loads at ~16.8 GiB of VRAM, already more than your 12 GB card can hold without significant offloading.[2]

FACT: Any “full Ornith‑1” release today is designed for data‑center scale GPUs or multi‑GPU setups, not a single 12 GB Windows card.[2][1]
CONSENSUS: People on local‑LLM forums describe Ornith‑1 as “in the too‑big tier” for 12–16 GB GPUs unless you accept major compromises.[3]

## 12 GB VRAM and MoE realities

Even though MoE models only activate a small subset of experts per token (e.g., ~3 B active parameters), all experts still have to live somewhere (VRAM or RAM) for normal inference.[4][5]

Key implications:

- MoE often ends up *more* memory‑hungry than a dense model of similar “effective” size, because inactive experts still occupy memory.[4]
- For a 35B MoE like Ornith‑1‑35B, validated Q3 quantization already wants ~17 GB VRAM; Q4 or better will be larger.[2]
- Practical guidance for 12 GB GPUs is: stick to roughly 7–14 B dense models at 4‑bit (Q4) quantization for smooth use, especially on Windows tools like LM Studio.[6][3]

So even if LM Studio could technically offload some experts to CPU RAM, you’d be in a slow, heavily‑offloaded configuration that defeats the purpose of Ornith‑1’s design.[5][7]

## LM Studio + Windows 11 constraints

LM Studio itself is fine on your stack:

- Official guidance: Windows 11, 16 GB+ system RAM, and at least ~6 GB VRAM is a good baseline, with 12 GB cards commonly recommended for 7–14 B models.[8][7][3]
- LM Studio uses GPU offloading but does not (today) expose the kind of fine‑grained MoE expert offload flags you see in llama.cpp (e.g., `--n-cpu-moe`).[7][9]

In practice:

- A 17 GB‑VRAM Q3 Ornith‑1‑35B quant would **not fully fit** on your 12 GB card under LM Studio.[2]
- Trying to load Ornith‑1‑397B locally is simply out of scope (hundreds of GB VRAM at FP16, >200 GB at INT4).[1]

FACT: No mainstream Windows GUI (LM Studio, Ollama‑like tools) currently lists Ornith‑1‑397B or Ornith‑1‑35B as “12 GB‑friendly” downloadable options.[3][6]
SPECULATION (high confidence): Even if someone hacked a 35B MoE quant down further, fitting it into 12 GB with usable speed on LM Studio/Windows would be fragile and uncomfortable.

## What you *can* do on 12 GB instead

Given your hardware and LM Studio, the sweet spot:

- 7–14 B dense models, Q4‑class quantization (e.g., Q4_K_M, Q4_K_S), for coding + general chat.[6][3]
- These typically occupy 5–10 GB VRAM, leaving room for KV cache and OS without OOM.[3][6]

Current, 12 GB‑friendly recommendations (examples):

- Qwen3 14B at Q4_K_M: explicitly described as fitting well on 12 GB while “punching above its size” and offering a huge context window.[3]
- Modern 7–8 B models (Gemma‑like or Llama‑family) at Q4: commonly reported to work on 8–12 GB cards.[10][11][6]

Actionable next steps:

1. In LM Studio’s model browser, filter for ~7–14 B models and 4‑bit quantizations (Q4‑something).  
2. Start with one recommended “12 GB‑friendly” model (e.g., a Qwen or Gemma/GPTQ variant) and watch LM Studio’s live VRAM usage—keep total VRAM utilization below ~90 %.[8][3]
3. If you want to experiment with MoE on 12 GB at all, use llama.cpp directly with flags like `-ncmoe` and `--n-cpu-moe` and a **smaller MoE model** (not Ornith‑1), then tune offload until you’re “just below OOM,” as community guides suggest.[12][9][5]

Confidence: High that Ornith‑1‑397B is impossible on 12 GB locally; high that Ornith‑1‑35B is impractical in LM Studio on 12 GB; high that 7–14 B dense Q4 models are your realistic target.

If you share your exact GPU model (e.g., RTX 3060 12 GB vs something older), I can propose a very specific LM Studio model + settings profile that matches your card and typical context lengths.

## Human

Best local LLMs for 12GB VRAM cards

## Assistant

You can treat a 12 GB card as “7–14 B dense at Q4/Q5, or ~17 B MoE at tight Q4” territory; the best current picks are Llama 4 Scout 17B, Qwen3 14B/8B, and Gemma 3/4 12B, with DeepSeek‑R1/R2 7–8B for reasoning.[1][2][3]

Below I’ll focus on *inference* on a single 12 GB NVIDIA card (e.g., RTX 3060 12 GB) with typical Windows tools like LM Studio or Ollama‑style runners.

## Core recommendations for 12 GB

### General assistant / chat

- Llama 4 Scout 17B (Meta, MoE).  
  Runs at Q4 quantization in ~10 GB VRAM, leaving headroom for KV cache; widely reported as “best overall quality on 12 GB VRAM” as of May–June 2026.[2][3]

- Qwen3 14B (Alibaba).  
  At Q4_K_M it uses ~9 GB VRAM and delivers very strong overall quality and a large context window, so it fits comfortably on 12 GB with good speed.[3][1][2]

- Gemma 3 12B / Gemma 4 12B.  
  Gemma 3 12B sits around ~8 GB VRAM and is highlighted as strong reasoning that runs well on an RTX 3060. Gemma 4 E4B/12B variants are reported around 6–7 GB VRAM at suitable quantization, leaving extra headroom on 12 GB cards.[4][2][3]

CONSENSUS: On 12 GB, Llama 4 Scout and Qwen3 14B are the “default” general assistants people recommend now; Gemma 3/4 12B is the alternative if you like Google‑family behavior.[2][3]

### Coding‑focused models

- Qwen3 8B (general coding).  
  Repeatedly described as the strongest small coding model on consumer hardware; Q5_K_M fits easily on 12 GB and performs very well on HumanEval‑style benchmarks for Python and JS.[1][3][2]

- Qwen‑coder 7B / Qwen2.5‑coder 7B.  
  Community testing finds Qwen‑coder 7B Q8_0 at ~9 GB VRAM extremely fast and pleasant on 12 GB, especially when you value speed over maximum “brain size.”[4]

- Llama 3.3 8B.  
  Often suggested as a “snappier” alternative to Llama 4 Scout when you want shorter latency and are fine with slightly weaker capabilities; fits comfortably on 12 GB at Q4/Q5.[3][2]

FACT: For coding on 12 GB, multiple guides explicitly call out Qwen3 8B as “best small coding model” right now, with Llama 3.3 8B as a solid runner‑up.[2][3]

### Reasoning / math / logic

- DeepSeek‑R1 7B / DeepSeek‑R2 8B.  
  DeepSeek‑R1 7B is specifically recommended as a 12 GB‑friendly chain‑of‑thought reasoning model with ~10–12 tokens/sec; R2 8B at Q4 uses ~5 GB VRAM and is described as “best for math and logic” in 8 B class.[1][3]

- Gemma 3/4 12B.  
  These are also flagged as strong at structured reasoning while staying under ~8 GB VRAM, which is ideal for a 12 GB GPU.[3][4]

SPECULATION (high‑confidence): For debugging, proofs, and complex planning on 12 GB, DeepSeek‑R1/R2 7–8 B or Gemma 3/4 12 B will outperform smaller, speed‑optimized models without blowing VRAM.

## VRAM tiers and what actually fits

Empirical data and recent guides line up roughly like this for a single 12 GB NVIDIA card:

- 7–8 B dense models at Q4/Q5:  
  5–6 GB VRAM, extremely comfortable, leaves room for huge context and KV cache.[1][3]

- 12–14 B dense models at Q4:  
  ~8–9 GB VRAM, still safe on 12 GB with reasonable speed (20–40 tok/s reported for Qwen3 14B on a 3060‑class GPU).[3][1]

- 17 B MoE (Llama 4 Scout) at Q4:  
  ~10 GB VRAM and works well on 12 GB, considered the “best overall quality” model for this VRAM tier.[2][3]

CONSENSUS: With 12 GB, you should usually avoid 24–35 B dense models except at very aggressive quantizations (Q2/Q3) because they either don’t fit or suffer noticeable quality degradation.[5][4]

## Concrete “short list” by use case

Here’s a compact pick‑list summarizing multiple current sources:[4][1][2][3]

| Use case            | Model                | Approx VRAM (Q4/Q5) | Notes                                                                          |
|---------------------|----------------------|----------------------|--------------------------------------------------------------------------------|
| General assistant   | Llama 4 Scout 17B    | ~10 GB               | Best overall quality on 12 GB, large context window.[3][2]          |
| General assistant   | Qwen3 14B            | ~9 GB                | Great balance of quality & speed, big context.[1][2][3]        |
| Fast general chat   | Llama 3.3 8B         | ~6 GB                | Snappier; good with a strict system prompt.[2][3]                   |
| Coding (main)       | Qwen3 8B             | ~5–6 GB              | Best small coding model; strong multilingual.[2][1][3]         |
| Coding (alt)        | Qwen‑coder 7B        | ~9 GB (Q8_0)         | Very fast; good for completions & reviews.[4]                             |
| Reasoning / logic   | DeepSeek‑R1 7B       | ~5 GB (Q4)           | Chain‑of‑thought reasoning; math and logic.[1][3]                    |
| Reasoning / logic   | DeepSeek‑R2 8B       | ~5 GB (Q4)           | Strong math/logic, 8 B class.[3]                                          |
| General/Reasoning   | Gemma 3 12B          | ~8 GB                | Strong at reasoning; runs well on 3060.[3]                                |
| Vision / basic images | Gemma 4 E4B / 12B | ~6–7 GB              | Handles image Q&A, leaves headroom on 12 GB.[2][4]                   |

## How to actually choose and set up

Given your profile (solution architect, likely RTX 3060 12 GB, Windows 11, LM Studio usage), a minimal, actionable plan:

1. Install / open LM Studio.  
   It’s widely recommended as the “first stop” for 12 GB users because it hides quantization + device offload complexity.[2]

2. Pull Qwen3 14B at Q4_K_M as your main assistant.  
   Guides explicitly tell 12 GB users to “download Qwen3 14B at Q4_K_M, talk to it, then adjust if too slow.”[1][2]

3. If Qwen3 14B feels slow, switch to Llama 3.3 8B or Qwen3 8B.  
   Both are confirmed fast and 12 GB‑friendly, with Qwen3 8B best for coding and Llama 3.3 8B better for short, general tasks.[3][2]

4. Add DeepSeek‑R1 7B (or R2 8B) for logic/analysis sessions.  
   Use this when debugging reasoning, math, or complex planning; sources say it’s the “best reasoning model on 12 GB” in the 7–8 B tier.[1][3]

5. Monitor VRAM usage and keep total under ~90 % of 12 GB.  
   This leaves space for KV cache and avoids OOM, especially on Windows where other apps also consume GPU memory.[6][1]

Confidence: High that these models will run comfortably on a single 12 GB NVIDIA card today; medium‑high that Qwen3 14B + Qwen3 8B + DeepSeek‑R1/R2 is an optimal trio for your stack.

Are you primarily optimizing for coding throughput, long‑context project memory, or “best overall reasoning” on that 12 GB card? That will slightly change which of these I’d put first in your local lineup.

## Human

coding primarily.  but I am ok downloading other models.  I hate censorship, like really hate it, so I also need an uncensored model(s) for web searching, chatting, and image/video analysis/gen.

## Assistant

You can cover your needs on 12 GB with two lanes: (1) high‑quality but mostly “normal” coding models (Qwen‑family, etc.), and (2) explicitly uncensored instruction‑tuned models for web‑search, chatting, and media analysis/generation (Dolphin, GLM‑Flash, various Llama‑3 uncensored forks).[1][2][3]

Below I’ll separate: coding, uncensored chat/web, and image/video, with a focus on models that actually fit and run well on a single 12 GB NVIDIA GPU.

***

## Lane 1 – Coding‑first models (12 GB sweet spot)

These are open‑weight models with good benchmarks and relatively sane behavior; you can keep them “uncensored enough” via system prompts and not using safety‑tuned variants.

### Strong primary coding models

- Qwen3 8B (Instruct / Chat / Code‑oriented variants)  
  Multiple recent guides call Qwen3 8B at Q5_K_M “the strongest small coding model available right now” for 12 GB; it fits comfortably, with excellent Python/JS completion quality and speed.[2][4][1]

- Qwen‑coder / Qwen2.5‑coder 7B–14B  
  Community reports highlight qwen2.5‑coder:14b as a top coding model for 12 GB rigs, and Qwen‑coder 7B Q8_0 around 9 GB VRAM as a very fast option if you want ultra‑snappy completions.[5][6]

- Llama 3.3 8B (Instruct)  
  Often recommended as a general low‑latency assistant that also codes well; at Q4/Q5 it uses ~6 GB VRAM and runs great on 12 GB.[4][2]

CONSENSUS: For serious coding on 12 GB, Qwen3 8B (instruct/coder flavor) is the main “best small coding” choice; Llama 3.3 8B and Qwen‑coder 7B/14B are excellent backups.[6][2][4]

### Base models (minimal safety / censorship)

If you want the *least* baked‑in guardrails and are okay with doing your own prompting:

- Qwen3‑8B‑Base  
  Base models are generally “uncensored” in the sense of no safety finetune; Reddit users explicitly point to Qwen3‑8B‑Base as a modern base that still fits in low VRAM setups and can be fine‑tuned or driven via system prompts for coherent coding help.[7]

- Other 7–8 B bases (Gemma / Llama‑family)  
  As of late 2025, users note Qwen, Gemma, and Llama‑family bases run well on 12 GB; you can wrap them with your own instruction patterns rather than relying on safety‑heavy chat finetunes.[8]

FACT: Base models won’t refuse on safety grounds but may need stronger prompting or finetuning to behave like an assistant.[9][7]

***

## Lane 2 – Uncensored models for chat + web search

Here you want models explicitly finetuned to remove refusals and “this may violate our content policy” behavior.

### Uncensored general/chat models that fit on 12 GB

- Dolphin series (Dolphin 2.5 / 3, various base backbones)  
  Dolphin is repeatedly listed among the top uncensored models, with multiple variants optimized for coding, roleplay, and general chat; a recent ranking notes that Dolphin occupies several spots in the top 10 uncensored LLMs used locally and via Ollama.[3][10][9]

- Llama‑family uncensored finetunes (llama2‑uncensored, nous‑hermes, wizard‑vicuna, etc.)  
  Guides on uncensored LLMs specifically mention open Llama‑based uncensored models like `llama2-uncensored`, `nous-hermes-llama2`, and `wizard-vicuna` as easy to run locally, including via Ollama. Most 7–13 B variants will fit easily on 12 GB with Q4/Q5 quantization.[1][9]

- NeuralDaredevil Llama 3 8B Abliterated  
  A LocalLLaMA thread explicitly calls “NeuralDaredevil Llama 3 8b Abliterated” the best uncensored 8B‑class model, with the highest MMLU among uncensored 8B models; it runs fine on 12 GB.[11]

- GLM‑4.7‑Flash “Heretic” / GLM‑4.7‑Flash IQ2  
  A 2026 guide for uncensored models and a local app (`locally-uncensored`) highlight GLM‑4.7‑Flash Heretic / IQ2 30B‑class as “maximum uncensorship” and “strongest 30B class” with IQ2 quant running around 12 GB VRAM and ~198k context; this is exactly targeted at 12 GB uncensored setups.[12][13]

CONSENSUS: Dolphin variants + Llama‑family uncensored forks are currently the mainstream go‑to “I hate censorship” models on local rigs; GLM‑4.7‑Flash Heretic/IQ2 is the heavier “no‑filter, long‑context” choice when you’re willing to push 12 GB hard.[12][3][9]

### How to deploy uncensored for web search / chat

Typical stack for your preferences:

- Use a “normal” coding model (Qwen3 8B or Qwen‑coder) for IDE‑style completions and refactors.  
- Use an uncensored chat model (Dolphin, NeuralDaredevil L3‑8B, GLM‑Flash Heretic/IQ2) for web‑search‑oriented workflows, red‑teaming, and unconstrained analysis.  

Primary cautions (FACT):  

- Uncensored models are explicitly designed to bypass safety constraints; guides warn they will happily attempt to answer highly unsafe questions and can produce offensive or illegal content.[10][9]
- For “AI‑first” systems, you’ll almost certainly want external policy layers or filters around them to avoid accidental misuse, even if *you* dislike censorship—especially once you start automating tasks.

***

## Lane 3 – Local image & video analysis/generation, uncensored

For image/video, you’re typically not using an LLM as the main generator; instead you pair:

- An LLM (for orchestration and prompts), plus  
- Diffusion / video models (Flux, SD, etc.) in tools like ComfyUI, Forge UI, or similar.

### Image generation (uncensored, local)

- Forge UI, ComfyUI, LocalForge AI  
  A 2026 guide on unrestricted image generation says the best unrestricted local generators are Forge UI (easy), ComfyUI (most flexible), and LocalForge AI (one‑click, local only); all run fully offline, no content filters, no logging.[14]

- Stable Diffusion / Flux variants from CivitAI / HuggingFace  
  Users explicitly recommend SD and Flux‑family models on 10–12 GB cards for uncensored image generation, with ComfyUI workflows widely shared.[15][14]

### Video generation

- Tools like `locally-uncensored` desktop app  
  The “locally‑uncensored” GitHub project pitches itself as a local desktop app that can run chat, agent‑mode, image gen, and video gen with models like GLM‑4.7‑Flash IQ2 and Gemma 4 E4B—all locally, uncensored, on 12 GB‑class GPUs.[13]

Given your hardware:

- 12 GB is perfectly fine for SD/Flux‑style image generation; video models will be slower or require smaller configs but are still usable.  
- Your LLM for image/video *analysis* can be one of the uncensored text models above (Dolphin, GLM‑Flash Heretic, etc.); for multimodal you’ll look at Gemma 4 E4B or similar vision‑capable models that fit on 12 GB.[2][13]

***

## Putting it together for your stack

Assuming Windows 11 + LM Studio (and maybe Ollama / command‑line):

1. **Coding lane (primary):**  
   - Install Qwen3 8B (instruct/coder) at Q5_K_M as your main coding model.[4][2]
   - Optionally add Qwen‑coder 14B if you want a larger, still‑12 GB‑friendly coding specialist.[6]

2. **Uncensored chat/search lane:**  
   - Install an uncensored 8B‑class model such as NeuralDaredevil Llama 3 8B Abliterated or a Dolphin variant for fast, uncensored interaction.[11][3]
   - If you want maximum uncensorship + huge context on 12 GB, add GLM‑4.7‑Flash Heretic/IQ2 via something like `locally-uncensored`.[13][12]

3. **Image/video lane:**  
   - Set up ComfyUI or Forge UI with SD/Flux‑family models from CivitAI or HuggingFace for unrestricted image generation.[14][15]
   - Use one of your uncensored LLMs as a “prompt engineer” and analyst around those tools.

4. **Safety / architecture layer (given your background):**  
   - For your own systems, keep a clear separation: “no‑filter” models behind explicit routing and logging, and task‑appropriate models for coding and ordinary work.  
   - Consider an epistemic/safety gate that routes obviously dangerous tasks away from automation, even if the underlying model is uncensored.

Confidence: High that Qwen3 8B + an 8B‑class uncensored Llama/Dolphin + GLM‑4.7‑Flash IQ2 + ComfyUI/Forge UI will all run on a single 12 GB card today; medium‑high that GLM‑Flash IQ2 will be the heaviest but still workable choice.

Are you planning to drive this mainly via LM Studio, or are you open to mixing in Ollama / llama.cpp / a custom Python orchestrator? That choice will change which exact model builds and quant formats I’d recommend first.
