---
title: "A1111 Ecosystem Python Compatibility & Fork Selection (2026)"
concept_type: reference
tags: [stable-diffusion, a1111, forge-neo, python-compatibility, pytorch, blackwell, gpu-compatibility]
status: active
confidence: 0.90
last_verified: 2026-08-03
verification: multi-source
relations:
  - "nvidia-vram-management-for-local-llm-inference"
  - "quantization-and-memory-optimization-for-local-ai-models"
  - "ai-image-generation-models-and-workflows"
sources:
  - type: source-code
    url: "P:/packages/.github_repos/stable-diffusion-webui/modules/launch_utils.py"
    description: "A1111 master branch launch_utils.py — Python version gate and torch pin"
    quality: 10
  - type: source-code
    url: "https://github.com/Haoming02/sd-webui-forge-classic/blob/neo/modules/launch_utils.py"
    description: "Forge Neo launch_utils.py — Python 3.13 gate, torch 2.13.0+cu130"
    quality: 10
  - type: github-repo
    url: "https://github.com/Haoming02/sd-webui-forge-classic"
    description: "Forge Neo repo — 1607 stars, pushed 2026-08-03, 10 releases in 4 months"
    quality: 9
  - type: nvidia-official
    url: "https://docs.nvidia.com/cuda/blackwell-compatibility-guide/index.html"
    description: "NVIDIA Blackwell Compatibility Guide — CUDA 12.8+ required for Blackwell"
    quality: 10
  - type: reddit
    url: "https://www.reddit.com/r/StableDiffusion/comments/1tt5uiq/does_anyone_else_cant_stand_comfyui_and_prefers/"
    description: "241-upvote thread — community discovers Forge Neo, authentic enthusiasm"
    quality: 7
  - type: reddit
    url: "https://www.reddit.com/r/StableDiffusion/comments/1n7fd2v/introducing_sdwebuiforgeneo/"
    description: "Forge Neo launch thread — maintainer Q&A, extension breakage reports, memory management admission"
    quality: 8
  - type: pytorch-forum
    url: "https://discuss.pytorch.org/t/pytorch-support-for-sm120/216099"
    description: "PyTorch team response on sm_120 support — CUDA 12.8 nightlies"
    quality: 9
---

# A1111 Ecosystem Python Compatibility & Fork Selection (2026)

**Definition:** The A1111 (AUTOMATIC1111 stable-diffusion-webui) ecosystem in 2026 has fragmented into multiple forks with incompatible Python version requirements. Selecting the correct fork depends on three hard constraints: GPU architecture (Blackwell needs CUDA 12.8+/torch 2.7+), Python version (each fork targets a specific minor), and model support needs (Flux/Wan/Qwen require modern forks).

## Decision context

**Why this research was needed:** the operator cloned A1111 master to `P:/packages/.github_repos/stable-diffusion-webui` and asked whether bootstrapping a venv with Python 3.14 (the system default) was appropriate. Investigation revealed (a) A1111 master pins Python 3.10 and torch 2.1.2, (b) the operator's RTX 5070 is Blackwell (sm_120) which torch 2.1.2 cannot address at all, and (c) the ecosystem has fragmented into forks with different Python targets. Research was needed to identify the correct fork + Python combination for this specific hardware.

**What alternatives were explored:** A1111 master (frozen Jul 2024, torch 2.1.2 — incompatible with Blackwell), A1111 dev (active but still Python 3.10 only, torch 2.7.0+cu128 — works on Blackwell but older stack), ReForge (Python 3.7–3.12, author recommends Forge Neo instead), SDNext/vladmandic (Python 3.10–3.12, multi-vendor GPU support but NVIDIA-only benefit irrelevant here), and Forge Neo (Python 3.13, torch 2.13.0+cu130 — optimal for Blackwell).

**What the research changed:** confirmed Forge Neo as the recommended fork for an RTX 5070 system, with documented trade-offs (extension compatibility, memory management, Stability Matrix breakage). A1111 master was eliminated entirely — not because it's unmaintained, but because its torch pin cannot address Blackwell architecture.

## The compatibility matrix

| Fork | Windows Python | Torch / CUDA | Blackwell (sm_120) | Last active | Status |
|------|---------------|-------------|---------------------|-------------|--------|
| **A1111 master** (AUTOMATIC1111) | 3.10 only | 2.1.2 / cu121 | ❌ Cannot run | Jul 2024 (frozen) | v1.10.1 stabilized |
| **A1111 dev** | 3.10 only | 2.7.0 / cu128 | ✅ Works | Mar 2026 | Active commits |
| **ReForge** (Panchovix) | 3.7–3.12 | varies | varies | Jul 2025 | Author recommends Forge Neo |
| **Forge Neo** (Haoming02) | **3.13** | **2.13.0 / cu130** | ✅ Optimal | **Today (active)** | Community-recommended |
| **SDNext** (vladmandic) | 3.10–3.12 | modern | ✅ Works | Jun 2026 | Multi-vendor GPU support |

**No A1111-family fork supports Python 3.14.** PyTorch 2.10+ ships cp314 wheels, but no fork has adopted them as of August 2026.

## The Blackwell constraint (RTX 50-series)

RTX 5070/5080/5090 are Blackwell architecture (compute capability sm_120). This is a **hard constraint**:

- Stock PyTorch pre-2.7 ships kernels only up to sm_90 (Ada Lovelace / RTX 40-series)
- CUDA Toolkit 12.8+ is the minimum for Blackwell (NVIDIA's official Blackwell compatibility guide)
- PyTorch 2.7.0 was the first stable release with native sm_120 wheels
- PyTorch 2.1.2 (A1111 master's pin) predates Blackwell by 2+ years and **cannot address the GPU at all**

This means A1111 master is not merely "old" — it is **architecturally incompatible** with RTX 50-series GPUs. The `torch.cuda.is_available()` check fails before any model loads.

## Forge Neo: known issues (honest assessment)

Source-verified from GitHub issues, Reddit threads, and maintainer responses (Sep 2025–Jun 2026):

### Extension compatibility (Major)
- aDetailer, ReActor, Regional Prompter, Browser+, AnimateDiff break in Neo
- Simple bugs fixed same-day by maintainer; architectural breaks persist
- Community forks exist for some; others remain broken

### Memory management (Major)
- Maintainer BlackSwanTW admitted: "The current memory management is worse than ComfyUI somehow. I'm still working on it"
- 12GB VRAM users report OOM at higher resolutions where ComfyUI runs fine
- Wan 2.2 high+low models likely to OOM

### Stability Matrix breakage (Dealbreaker for launcher users)
- SM update breaks Forge Neo with `module '__main__' has no attribute '__file__'`
- All in-launcher fixes failed; user must abandon SM and manually git clone
- Documented Jun 2026

### Model support uneven (Major for affected users)
- Qwen inpaint broken; Qwen LoRAs don't load
- Wan 2.2 certain model formats unrecognized
- Hidream: "probably not" supported
- Chroma output quality worse than ComfyUI template

### Positive signals
- 241-upvote Reddit thread: "A ForgeUI that gets regular updates? Sign me up asap!"
- 10 releases in 4 months (v2.20 Apr → v2.28.1 Aug 2026)
- 1607 GitHub stars, pushed daily
- Only A1111-family fork with active modern-model support

## Recommended setup for RTX 5070 (12GB VRAM)

1. **Install Python 3.13.x** (separate from system 3.14/3.12)
2. **Clone Forge Neo**: `git clone -b neo https://github.com/Haoming02/sd-webui-forge-classic.git`
3. **Use standalone install** (not Stability Matrix — known breakage)
4. **Point at existing A1111 models** via `configure_a1111_reference()` or `--a1111-reference <path>`
5. **Expect friction** on extensions and high-resolution OOM

## Falsifier

This assessment becomes wrong when:
- A1111 dev adds official Python 3.11+ support (no sign as of Mar 2026)
- Forge Neo shifts beyond Python 3.13 (possible but not documented)
- A new fork emerges targeting Python 3.14 (none exists as of Aug 2026)
- PyTorch cp314 wheels become standard and a fork adopts them (estimated Q3/Q4 2026)

## Cross-references

- [[nvidia-vram-management-for-local-llm-inference]] — VRAM optimization patterns for local inference
- [[quantization-and-memory-optimization-for-local-ai-models]] — NF4/GGUF quantization for low-VRAM
- [[ai-image-generation-models-and-workflows]] — model landscape (Flux, Qwen, SDXL)
