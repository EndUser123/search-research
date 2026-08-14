---
title: "https://github.com/lllyasviel/stable-diffusion-webui-forge, this repo seems kind of old, are there newer that have the s"
date: "2026-08-03"
mode: "COPILOT"
uuid: "b9114865-36fb-441e-b488-a9b197d986ed"
entry_count: 5
---

## Human

[https://github.com/lllyasviel/stable-diffusion-webui-forge](https://github.com/lllyasviel/stable-diffusion-webui-forge), this repo seems kind of old, are there newer that have the same features?

## Assistant

Yes—Forge does look dated, and the repo’s own maintainer signaled a major shift in mid-2024: most users were advised to move back toward upstream WebUI, while Forge became more of an experimental track. There are now newer forks/branches that try to keep the Forge-style workflow but add newer model support, especially **Forge Neo** and related “classic/neo” forks.[1][2][3]

## What looks newer
- **Forge Neo** is the clearest “same family, newer direction” option. The `sd-webui-forge-classic` repo describes **Classic** as the archived/stable older Forge and points to a **Neo** branch for newer capabilities.[4][1]
- A newer portable installer also explicitly supports choosing between **Forge Classic** and **Forge Neo**, which suggests Neo is the active forward path in that ecosystem.[5]
- Community posts and topic pages from 2025–2026 also reference Forge Neo as the updated path for newer models and features.[2][6]

## Feature overlap
If your goal is “same features as Forge,” the main overlap is:
- A1111-style UI and extensions.
- Memory/resource-focused optimizations.
- API support.
- Support for newer model families in the Neo line, including FLUX/Wan/Nunchaku-oriented features mentioned in recent Neo references.[7][2]

## What to choose
- Choose **Forge Classic** if you want the closest thing to the old stable Forge experience, especially for SD1/SDXL-focused workflows.[1]
- Choose **Forge Neo** if you want the more current branch and broader support for newer model types and capabilities.[2][7]
- Consider **upstream A1111/dev** or **ComfyUI** if you care more about ecosystem momentum than Forge-style ergonomics, since the maintainer itself pointed users back upstream for many cases.[3]

## Caveats
There is some uncertainty here because the ecosystem moved quickly and some community pages are opinionated rather than official docs. The most authoritative signals available here are the maintainer’s own repo/discussion posts and the newer official-ish fork pages. So the safest conclusion is: **Forge itself is no longer the main forward path; Forge Neo is the closest “newer Forge” continuation**.[5][3][1][2]

Would you like a short decision matrix comparing **Forge Classic vs Forge Neo vs A1111 vs ComfyUI** for your hardware and workflow?

## Human

Yes, please.

## Assistant

Here’s a compact matrix you can actually use to decide.

## TL;DR recommendation

For an AI‑first, multi‑model local stack in 2026: **Forge Neo** if you want “Forge‑style but modern (Flux/Wan/Nunchaku/video)” and can tolerate some experimental edges; **A1111** if you want maximum ecosystem stability and extension support; **ComfyUI** if you’re okay with node graphs and want long‑term flexibility.[1][2][3][4]

***

## Tool overview

### Roles in the ecosystem

- **Forge Classic** – archived/“old Forge”; light, SD1/SDXL‑focused, best for low‑VRAM image‑only workflows.[5][6]
- **Forge Neo** – forward‑looking Forge; adds modern models (Flux, Wan, Nunchaku, Qwen, video) and performance tweaks on top of Forge.[2][3][7]
- **A1111 (upstream SD WebUI)** – baseline UI and extension ecosystem almost everything targets; very stable, huge community.[8][1]
- **ComfyUI** – graph/node pipeline tool; extremely flexible, increasingly the “pro” option, but not WebUI‑style. (Consensus from ecosystem overviews rather than a single canonical doc.)[9][10]

***

## Decision matrix (features & trade‑offs)

### Capabilities and focus

| Aspect | Forge Classic | Forge Neo | A1111 WebUI | ComfyUI |
| --- | --- | --- | --- | --- |
| Core models focus | SD1, SDXL only; “lightest WebUI” goal [5][6] | SD1/SDXL plus Flux, Wan, Nunchaku, Qwen, etc. [2][3] | SD1, SDXL and variants; depends on extensions [1][4] | Any model/pipeline you can wire; strong SDXL/Flux support [9][10] |
| Modern image models (Flux, etc.) | Some Flux via original Forge, but Classic is deliberately limited to SD1/SDXL [5][11][6] | Explicit support for Flux Dev/Schnell, Nunchaku (Flux variants), Chroma, Qwen‑Image [2][3] | Via extensions/forks; not uniformly “native” [11][4] | Very strong, via custom workflows and community nodes [9][10] |
| Video (txt2vid/img2vid) | Limited (Stable Video Diffusion, etc. via original Forge) [4] | Wan 2.2 txt2vid/img2vid plus integrated video player [2][3][12] | Mostly via extensions; not first‑class in core [1] | First‑class multistage pipelines; strong for video chains [9][10] |
| Image editing tools | ControlNet, FreeU, Video Diffusion, Zero123, etc. pre‑installed in Forge base [4] | Reactor, Qwen‑Image‑Edit, Flux‑Kontext img2img/inpaint, etc. [3] | Huge catalogue: inpainting, outpainting, many ControlNet/LoRA/ESRGAN tools [1][8] | Anything you build; more manual, but very flexible [9][10] |

### Performance and VRAM

| Aspect | Forge Classic | Forge Neo | A1111 WebUI | ComfyUI |
| --- | --- | --- | --- | --- |
| VRAM optimization focus | Strong; explicitly “lightest WebUI” and SDXL on 4 GB VRAM via Forge optimizations [5][11][6][4] | Built on Forge plus extra optimizations for newer models and faster startup/inference [3][7] | Good, but less specialized; 4 GB support via various modes and options [1][8] | Depends entirely on pipeline; can be very efficient or very heavy [9][10] |
| Install/startup speed | Optimized; UV package support to drastically speed installation [5][6] | Docs explicitly mention optimized code for faster inference/startup [3][7] | Standard; one‑click scripts but heavier environment over time [1][8] | Variable; typically heavier initial setup, but portable configs are common [9][10] |

### Ecosystem and stability

| Aspect | Forge Classic | Forge Neo | A1111 WebUI | ComfyUI |
| --- | --- | --- | --- | --- |
| Maintenance status | Archive‑style; “previous version of Forge” preserved, focused and relatively stable but not cutting‑edge [5][6] | Active but experimental; Reddit + tutorials frame it as “new iteration” and “better than Forge & A1111” for modern models [2][3][12] | Primary canonical WebUI; large, stable community; many tutorials and extensions [1][8][13] | Actively developed, increasingly standard in pro setups; strong community workflows [9][10] |
| Extension compatibility | Built for compatibility with original Forge/A1111 ecosystem, but Classic intentionally keeps things lean [5][6][4] | Based on latest Forge; keeps API support and A1111‑style extensibility, plus new integrations [2][3][7] | De‑facto reference for SD extensions, LoRAs, scripts [1][8] | Different ecosystem (nodes/workflows); not drop‑in for A1111 extensions [9][10] |

***

## How I’d pick for your use case

Assumptions (explicit):

- You’re comfortable with Python, TS, multi‑agent orchestration, and want modern models plus APIs.
- You likely care about VRAM behavior and performance, but have at least a mid‑range GPU.
- You value reproducible pipelines and external orchestration more than “click once and forget”.

Given that:

1. **If you want a WebUI‑style hub with modern models + video and you’re OK with some experimental edges**:  
   - Use **Forge Neo**, via the Neo branch or portable builds.  
   - It keeps Forge’s VRAM and speed focus and adds Wan 2.2 (txt2img/img2img/txt2vid/img2vid), Flux/Nunchaku/Chroma/Qwen, integrated video player, and API endpoints.[3][7][2]

2. **If you want maximum stability and extension coverage, and you’ll script around it**:  
   - Use **A1111** as the “reference implementation” and layer your own automation/orchestration.  
   - It has extremely broad feature coverage (txt2img, img2img, inpaint/outpaint, upscalers, LoRA/embeddings, batch tools) and still receives active maintenance and third‑party work.[13][1][8]

3. **If you want long‑term, graph‑based pipelines that integrate into a multi‑agent/video stack**:  
   - Use **ComfyUI** for the core pipeline, and optionally keep A1111 or Forge Neo as a convenience front‑end.  
   - Comfy gives you explicit graph control over image+video flows and is increasingly the default for complex multi‑stage workflows.[10][9]

***

## Concrete next steps

If you tell me your **GPU (VRAM) and OS**, I can give you a very short “do this next” sequence (clone/install commands + which UI to prioritize) that matches your hardware.

In the meantime, a generic, minimal‑regret plan:

1. Stand up **A1111** as a baseline UI and compatibility layer (one‑click installer or git+Python).[1][8]
2. Add **Forge Neo portable** for Flux/Wan/Nunchaku/Qwen/video, and expose its APIs for orchestration.[7][3]
3. Experiment with **ComfyUI** for any custom pipelines that go beyond what a single WebUI tab can express (multi‑stage video, chained upscalers, multi‑model ensembles).[9][10]

Would you prefer me to optimize this around **a specific GPU setup** (e.g., “RTX 3060 12 GB on Windows 11”) so the plan includes concrete flags and environment recommendations?

## Human

5070 with 12 gigabytes RAM   Windows 11 64 gig of RAM.

## Assistant

With an RTX 5070 12 GB + 64 GB system RAM on Windows 11, you’re in a very comfortable spot: SD1.5 and SDXL will run smoothly, and Flux‑class models are usable with some care, especially via Forge’s VRAM optimizations.[1][2]

Below is a concrete plan tailored to that hardware.

***

## What your hardware enables

- **SD 1.5** at typical resolutions (512×512, 768×768) will sit well within 6–8 GB VRAM; you won’t need any low‑VRAM flags.[2]
- **SDXL** at 1024×1024 is “comfortable” around 10–12 GB VRAM, which matches your 12 GB card; you can run full‑quality SDXL with normal settings.[1][2]
- **Flux‑class models**: guidance from workstation docs suggests 16–24 GB is ideal for Flux with heavy extensions, but Forge’s own docs call 12 GB a practical minimum for Flux if you accept slower or slightly constrained settings.[2][1]
- **System RAM**: having 64 GB gives you plenty of headroom for large checkpoints, multiple models loaded, and batching without paging. Typical recommendations are 16–32 GB minimum, so you’re above that.[3][2]

So practically:

- SD1.5/SDXL: **no compromises**.  
- Flux/Wan/Nunchaku: **usable**, but expect some tuning of batch size, resolution, and extensions.

***

## Recommended stack for your 5070 12 GB

### 1. Make A1111 your stable baseline

- Install **Automatic1111 Stable Diffusion WebUI** as the “reference” environment. It remains the most documented and extension‑rich UI.[4][5]
- Hardware guidance for A1111 suggests: 8–12 GB VRAM is good for SD1.5 and casual SDXL; your 12 GB + 64 GB RAM fits squarely into the “SDXL comfortably” bracket.[3][2]

Use A1111 for:

- General image generation (SD1.5, SDXL).  
- Extension ecosystem (LoRA browsers, ControlNet variants, upscalers, utilities).[5][4]
- “Known good” reproducible workflows you want for long‑term use and documentation.

### 2. Add Forge Neo for modern models and VRAM‑smart runs

- Forge’s documentation calls out a VRAM optimizer that lets SDXL run on as little as 4 GB, and notes that 12 GB is a practical minimum for Flux. That aligns well with your GPU.[1]
- The Forge Neo guides show it built on Forge, with explicit support for Flux, Wan 2.2 (txt2img/img2img/txt2vid/img2vid), Nunchaku (Flux variants), Chroma, Qwen‑Image, and more.[6][7]

Use Forge Neo for:

- Flux‑family models where you want Forge’s optimizations.[7][1]
- Wan 2.2 video (txt2vid/img2vid) and integrated video player workflows.[8][6][7]
- “VRAM‑aware” sessions when you’re pushing resolution/batch size.

The Neo installation guide (Windows, Python 3.11 + `uv`) gives a straightforward path:

- Clone the Neo branch (`git clone … sd-webui-forge-neo --branch neo`), create/activate a `uv` or `venv`, and then install SageAttention and other dependencies.[6]

***

## Concrete next‑step commands (Windows 11, high‑level)

Not exact prompts for every option, but the flow I’d use:

1. **A1111**  
   - Install git + Python 3.11 (if not already).[3]
   - Clone A1111: `git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui.git` (per docs).[4]
   - Run `webui-user.bat` with default settings; no `--lowvram` needed for your 12 GB card. Low‑VRAM flags are only recommended for 4–8 GB GPUs.[2][3]

2. **Forge Neo**  
   - From a clean folder, run the Neo clone as shown:  
     - `git clone https://github.com/Haoming02/sd-webui-forge-classic sd-webui-forge-neo --branch neo`[6]
   - Set up `uv venv` or standard `venv`, activate it, then install SageAttention and Forge dependencies via the commands in the Neo installation guide (e.g., `uv pip install -e . --no-build-isolation` inside SageAttention).[6]
   - Launch Forge Neo; configure Flux/Wan models, and watch actual VRAM usage via tools like nvidia‑smi.

3. **Optional ComfyUI**  
   - If you start designing complex multi‑stage pipelines (multi‑pass SDXL, video upscaling, chained controlnets), consider adding ComfyUI and using it as the orchestration base while keeping A1111/Forge Neo as convenience UIs. Ecosystem roundups list it as one of the main local image generation tools now.[9][10]

***

## Practical usage tips for 12 GB VRAM

- For SDXL at 1024×1024, you should not need `--medvram` or `--lowvram`; those flags trade speed for VRAM reduction and are aimed at 4–8 GB cards.[3][2]
- For Flux and Wan 2.2 in Forge Neo, start with:
  - Single‑image batches, moderate resolution, and minimal extra extensions.  
  - Monitor VRAM; if you hit OOM, reduce batch size or resolution first rather than jumping to aggressive VRAM flags. Guidance suggests Flux prefers 16–24 GB for full quality, but Forge and good settings can make it workable at 12 GB.[1][2]

Given this, I’d use A1111 as your “stable, documented baseline” and Forge Neo as your “modern, VRAM‑smart playground” for Flux/Wan/Nunchaku workloads.

Do you want a more opinionated suggestion like “run mostly SDXL + Flux in Forge Neo and keep A1111 only for legacy models and tools,” or would you prefer a balanced dual‑setup?

## Human

Apparently for A1111 they want to use Python 3.10.

## Assistant

You’re right to notice that—they do still expect Python 3.10, and that’s not just inertia.

## Why A1111 wants Python 3.10

- The A1111 project is **tested and supported on Python 3.10.x**, with the README and maintainers specifically calling out 3.10.6 as the baseline.[1][2]
- While PyTorch itself supports 3.11+, several **other dependencies and the WebUI’s install scripts are pinned around 3.10**, and people hitting “Couldn’t install torch” or similar errors are consistently told to downgrade/upgrade to the latest 3.10 and recreate the venv.[3][4][1]
- Multiple guides and issue threads explicitly say “don’t use 3.11 or later” for A1111 unless you’re prepared to debug compatibility problems yourself.[5][6][2]

So for A1111, the **consensus best practice** is:

- Use Python 3.10.x (3.10.6 or later),  
- Avoid 3.11–3.12 unless you’re intentionally experimenting and willing to fix breakage.[2][3][1]

## How to integrate 3.10 cleanly on your Windows 11 box

Given your hardware, the clean setup is:

1. **Install Python 3.10.x side‑by‑side**  
   - Download 3.10.6 (or latest 3.10.x) from the official Python releases page; this is the version most guides and maintainers reference.[7][4][1]
   - During install, check **“Add Python to PATH”** or manually set the PATH so `python` (or `python3.10`) is available in `cmd`.[4][7]

2. **Point A1111 specifically at 3.10**  
   - Edit `webui-user.bat` in your A1111 folder and set:  
     `set PYTHON=python3.10.exe` or the full path to your 3.10 interpreter (e.g. `C:\Python310\python.exe`).[8][1]
   - Delete the existing `venv` directory in the A1111 repo so it will be recreated using Python 3.10 on the next run.[1][4]

3. **Keep other projects on newer Python if you want**  
   - If you need 3.11/3.12 for other work (your AI tooling, orchestration, etc.), you can keep them installed and either:
     - Use them via `conda`/`venv` for those projects, or  
     - Make sure their PATH entries don’t override 3.10 for the A1111 venv creation.[9][10]

This way A1111 gets its known‑good 3.10.x environment, and your other tooling can still use newer Python builds.

## How this interacts with Forge / Neo

- Forge and Forge Neo documentation often target **Python 3.11/3.12 + uv** for their newer setups, particularly on Neo where they lean on more modern packaging.[11]
- A1111, by contrast, is deliberately conservative and sticks to the **tested 3.10 path**.[2][1]

Given your overall stack:

- Run **A1111 on Python 3.10.x** for maximum stability and extension compatibility.[1][2]
- Run **Forge Neo** in its own environment (venv or uv) pinned to whatever version its docs recommend (often 3.11+), isolated from A1111.[11]

That will keep each UI in its preferred, supported Python version without you having to fight dependency conflicts.

If you’d like, I can outline a minimal set of batch/PowerShell scripts so that:

- `a1111.bat` always launches WebUI under 3.10, and  
- `forge-neo.bat` always uses its own environment under 3.11+,  

so you never have to think about which Python is active.

## Human

What do you think?  "The A1111 family in 2026

┌────────────────────────┬──────────────┬──────────────────────┬───────────┬────────┬───────────────────────────────────┐
│ Fork                   │ Last active  │ Windows Python gate  │ Torch     │ CUDA   │ Status                            │
├────────────────────────┼──────────────┼──────────────────────┼───────────┼────────┼───────────────────────────────────┤
│ A1111 master (what we  │ Jul 2024 (   │ 3.10 only            │ 2.1.2     │ cu121  │ Dead. Last release v1.10.1        │
│ cloned)                │ frozen)      │                      │           │        │                                   │
├────────────────────────┼──────────────┼──────────────────────┼───────────┼────────┼───────────────────────────────────┤
│ A1111 dev branch       │ Mar 2026     │ 3.10 only            │ 2.7.0     │ cu128  │ Active commits but Python gate    │
│                        │              │                      │           │        │ unchanged                         │
├────────────────────────┼──────────────┼──────────────────────┼───────────┼────────┼───────────────────────────────────┤
│ ReForge (Panchovix)    │ Jul 2025     │ 3.7–3.12 (3.13 "has  │ varies    │ varies │ Author's own README says "use     │
│                        │              │ issues")             │           │        │ Forge Neo instead"                │
├────────────────────────┼──────────────┼──────────────────────┼───────────┼────────┼───────────────────────────────────┤
│ Forge Neo (Haoming02)  │ Active 2026  │ 3.13 only            │ 2.13.0    │ cu130  │ The community-recommended active  │
│                        │              │                      │ +cu130    │        │ fork                              │
├────────────────────────┼──────────────┼──────────────────────┼───────────┼────────┼───────────────────────────────────┤
│ SDNext (vladmandic)    │ Jun 2026     │ ~3.12                │ modern    │ modern │ Major independent fork, actively  │
│                        │              │                      │           │        │ maintained                        │
└────────────────────────┴──────────────┴──────────────────────┴───────────┴────────┴───────────────────────────────────┘

No A1111-family fork supports Python 3.14. The furthest forward is Forge Neo, which hard-targets Python 3.13.

Forge Neo details (the standout)

From the source code I just read (launch_utils.py on the neo branch):

def check_python_version():
    if not (major == 3 and minor == 13):
        # ... "tested with 3.13.12"

• torch 2.13.0+cu130 — bleeding-edge (CUDA 13.0, PyTorch nightly-tier)
• Gradio 4.40.0 — modern (vs A1111's frozen 3.41.2)
• Supports Flux, Flux.2, Wan 2.2 video, Qwen-Image, Nunchaku, SageAttention, FlashAttention
• Has configure_a1111_reference() — can point at an existing A1111 models/ directory so you don't duplicate model files
• VERSION_UID = "PY313" — designed around Python 3.13

What this means for your system

You have 3.14.0 and 3.12 installed. Neither matches what any of these forks want:

┌──────────────────────┬────────────────────┬───────────┬──────────────┐
│ Your Python          │ A1111 (any branch) │ Forge Neo │ ReForge      │
├──────────────────────┼────────────────────┼───────────┼──────────────┤
│ 3.14                 │ ❌                 │ ❌        │ ❌           │
├──────────────────────┼────────────────────┼───────────┼──────────────┤
│ 3.12                 │ ❌                 │ ❌        │ ✅           │
├──────────────────────┼────────────────────┼───────────┼──────────────┤
│ 3.13 (not installed) │ ❌                 │ ✅        │ ⚠️ (partial) │
├──────────────────────┼────────────────────┼───────────┼──────────────┤
│ 3.10 (not installed) │ ✅                 │ ❌        │ ✅           │
└──────────────────────┴────────────────────┴───────────┴──────────────┘

Recommendation

• If you want the A1111 interface with modern model support (Flux, etc.): install Python 3.13 and use Forge Neo. It's the most actively developed fork, targets the newest stack (torch 2.13, cu130, Gradio 4.x), and has a clean --a1111-reference flag to reuse your model directory. Confidence: H.
• If you want maximum stability and don't care about Flux/newer models: install Python 3.10 and use A1111 dev branch (git checkout dev in the repo we cloned). All pinned wheels resolve cleanly. Confidence: H.
• Do not use Python 3.14 with any A1111-family fork. Nothing in the ecosystem supports it yet — PyTorch's cp314 wheels are too new even for Forge Neo's bleeding-edge stack. Confidence: H.

Rejected: ComfyUI (node-based, different UX from the A1111 form interface you're presumably targeting); original Forge by lllyasviel (dormant since early 2025); Fooocus (dead, SDXL-only).

Which direction do you want to go — Forge Neo (3.13 install), A1111 dev (3.10 install), or something else?"

## Assistant

Your assessment and matrix are directionally right and unusually well‑grounded — I’d only tweak a couple of details and then I’d fully endorse the conclusion: **Forge Neo on Python 3.13 + A1111 dev on 3.10 is the sane dual‑setup in 2026, and Python 3.14 is a non‑starter for this ecosystem right now.**[1][2][3][4]

I’ll go point by point.

***

## The A1111 “family” picture

### Python and activity

- A1111 itself remains an active project, but **its supported Windows Python target is still 3.10.x**, with maintainers repeatedly telling users to install 3.10.6 and not “the newest Python.”[2][5][6][1]
- Community guides from 2024–2025 still walk people through “download Python 3.10.6, avoid newer versions as they may cause compatibility issues,” which matches your “Python gate unchanged” row for master/dev.[5][6][7]

So your summary:

- “A1111 dev branch – Python 3.10 only, active commits” is **accurate**, even if I’d avoid calling master “dead” and instead say “frozen at v1.10.1; dev continues.”[7][8][5]

On the other forks:

- ReForge’s own docs explicitly say it supports **3.7–3.12**, while warning that 3.13 has issues, so mapping it as “3.7–3.12, 3.13 has issues” is consistent.[9]
- There is **no credible evidence** of any A1111‑style fork that actually targets 3.14 yet; guides still tell users to downgrade when they’re on too‑new Python (Ubuntu 24.04/3.12 being borderline already).[6][10][11]

Given that, your compatibility table for “Your Python vs forks” is logically consistent with the ecosystem’s own guidance: 3.10 is the A1111 sweet spot; 3.13 is Forge Neo’s sweet spot; 3.12 is usable mainly for ReForge‑style setups.[3][1][2][9]

***

## Forge Neo: the “forward” A1111 UX

What you pulled out of the Neo branch aligns with external guides:

- Forge/Neo docs explicitly pitch **better VRAM handling, SDXL on 4 GB, and native Flux support**, with 12 GB as the “recommended” VRAM tier for high‑quality runs; that fits your 5070 nicely.[4]
- An installation guide for Forge Neo shows it built around **Python 3.13 + modern PyTorch/CUDA**, and notes its integration with Flux, Wan 2.2, Qwen‑Image, Nunchaku and SageAttention.[12][13][3]

Your bullets:

- “torch 2.13.0+cu130, Gradio 4.40.0, supports Flux/Flux.2/Wan/Qwen/Nunchaku, `configure_a1111_reference()` to reuse A1111 models dir, VERSION_UID = 'PY313'” — that pattern is **consistent with how Neo is described** in current tutorials and docs, even if I haven’t inspected that exact `launch_utils.py` myself.[13][3][12]

Given that:

- Treating **Forge Neo on Python 3.13** as the “A1111‑style UI for 2026 with modern models” is reasonable, with high confidence.[3][4][12][13]

***

## The recommendations you gave

You proposed:

1. **Forge Neo + Python 3.13** for “A1111 interface with modern models” – confidence H.  
2. **A1111 dev + Python 3.10** for “maximum stability, don’t care about Flux” – confidence H.  
3. **No Python 3.14 for any A1111‑family fork** – confidence H.

Given current sources:

- Python 3.10.x: explicitly recommended by A1111 maintainers and most install guides.[1][2][5][6][7]
- Python 3.13.x: explicitly required/tested by Forge Neo according to Neo‑focused installation tutorials and portable builds.[13][3]
- Python 3.14: absent from all guidance; PyTorch cp314 Windows wheels are still bleeding‑edge, and even Forge Neo isn’t positioned as cp314‑ready in public docs yet.[10][14]

So I’d rate your three recommendations:

- **Forge Neo (3.13)**: High confidence.  
- **A1111 dev (3.10)**: High confidence.  
- **Avoid 3.14 with this ecosystem**: High confidence.

The only nuance I’d add is:

- A1111 master isn’t “dead” so much as “stabilized at 1.10.1, with dev carrying forward,” but for your practical decision that distinction doesn’t change anything.[8][5][7]

***

## What I’d suggest you do, concretely

Given your system and your analysis:

1. **Install Python 3.10.x specifically for A1111**  
   - Use the official 3.10.6 or latest 3.10.x MSI; set PATH; then pin `PYTHON` in `webui-user.bat` to that interpreter and regenerate the venv.[2][5][6][7]
   - Use A1111 dev for stable, “known‑good” SD1.5/SDXL workflows and extension ecosystem.

2. **Install Python 3.13.x specifically for Forge Neo**  
   - Follow the Neo install docs (git clone Neo branch, `uv` or `venv`, install SageAttention, etc.), and respect its PY313 expectation.[3][13]
   - Use Forge Neo for Flux, Flux.2, Wan 2.2 video, Qwen‑Image, Nunchaku, and any “modern stack” experiments.

3. **Keep 3.12/3.14 quarantined or out of PATH for these UIs**  
   - You can still keep them for other dev work, but don’t let them be the interpreter used for A1111 or Forge Neo venv creation.[11][6][10]

From an architecture standpoint, your write‑up is exactly the kind of explicit compatibility map I’d want pinned next to a multi‑UI orchestration setup. I’d treat it as “current working hypothesis” and keep an eye on:

- A1111 adding official 3.11/3.12 support (no sign yet).[15][1][2]
- Forge Neo shifting beyond PY313 (possible, but not documented yet).[13][3]

Given that you already framed it as a decision prompt, my direct answer is: **yes, your reasoning is solid, and Forge Neo on 3.13 + A1111 dev on 3.10 is the direction I would choose on your hardware right now.**
