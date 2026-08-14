---
title: "How can I make more images like that shown in the youtube video, locally for free?"
date: "2026-06-19"
mode: "COPILOT"
uuid: "b98acfd0-918a-4a35-a5df-a65b679d12ec"
entry_count: 3
---

## Human

How can I make more images like that shown in the youtube video, locally for free?

## Assistant

You can make similar images locally for free with **Stable Diffusion** tools, and the easiest path is usually ComfyUI, Fooocus, or Krita AI Diffusion rather than building anything from scratch. ComfyUI has official getting-started docs for local generation, Fooocus is open-source and runs offline, and Krita AI Diffusion is a free plugin that lets you generate and edit inside Krita.[1][2][3]

## Best local stack

For a beginner-friendly setup, I’d pick one of these:

- **Fooocus**: easiest “type prompt, get image” experience, fully local and open-source.[1]
- **ComfyUI**: best if you want control, workflows, and automation later.[2]
- **Krita AI Diffusion**: best if you want to edit images in a painting app and use inpainting/outpainting.[3]

If your goal is just “make more images like this,” ComfyUI or Fooocus is usually the fastest route, while Krita becomes useful once you want to refine results instead of only generating from text.[2][3][1]

## What you need

To run local image generation well, a GPU helps a lot. One source notes that running AI locally in Krita is recommended with at least 6 GB of video memory. If you only have CPU, LocalAI can generate images on CPU too, but that will generally be much slower than GPU-based Stable Diffusion workflows.[4][5]

## Practical setup path

A sensible free workflow is:

1. Install **ComfyUI** or **Fooocus** locally.[1][2]
2. Download a model checkpoint such as an SDXL or other compatible checkpoint inside the tool.[6][2]
3. Start with a simple prompt, generate, then iterate on prompt, aspect ratio, and steps.
4. If you want to edit specific areas, move to **Krita AI Diffusion** for inpainting/outpainting.[3]

ComfyUI’s docs explicitly walk through loading a checkpoint and running the first generation locally. That makes it a good default if you want a path that can later scale into more advanced automation.[2]

## Legal and safety note

You can generate similar *style characteristics* locally, but you should avoid copying a specific person’s face or making non-consensual sexual deepfakes. If the reference is just a general aesthetic, you’re safe to mimic lighting, pose, composition, and color palette; if it is an identifiable person, that becomes a different category entirely.

## Best next step

If you want the shortest path on Windows 11, start with **Fooocus** for simplicity or **ComfyUI** for control. If you want, I can give you a **local-only Windows setup checklist** with the exact downloads, GPU requirements, and a first prompt template.[1][2]

## Human

I don't want to create exact images, or use the exact likeness of the person, but I do want to create uncensored images.  What's the easiest way to do that locally for free?

## Assistant

The easiest local-free path is **Fooocus** if you want the simplest “prompt → image” workflow, or **ComfyUI** if you want more control and eventually want batch generation or automation. Both are free and local; Fooocus is explicitly offline/open-source, while ComfyUI’s official docs walk through local first-generation setup on Windows.[1][2]

## What to use

- **Fooocus**: easiest to start, best for fast experimentation, less setup friction.[2]
- **ComfyUI**: best for power users, workflows, and scaling into repeatable pipelines.[3][1]
- **Krita AI Diffusion**: best if you want to edit, inpaint, or outpaint inside a drawing app instead of only generating from text.[4]

For your goal, I would start with **Fooocus** unless you already know you want a node/workflow system. That choice gives you the lowest setup burden and still keeps everything local and free.[1][2]

## Good model choice

If you want “uncensored” in the practical sense of fewer platform restrictions, the key is to use a local checkpoint you control rather than a hosted service. Community guidance and official setup docs point to downloading a model checkpoint into the local app and generating on your own hardware.[3][1]

A more accurate framing is: you can generate **less filtered local images**, but you should still avoid using a real person’s likeness or making non-consensual sexual images. I can help with safe adult-themed aesthetics, but not with person-specific sexual deepfakes.

## Hardware reality

Local image generation is much easier with an NVIDIA GPU, and one source notes Krita AI Diffusion is intended for computers with decent specs and at least 10 GB of disk space for the plugin setup. If you only have CPU, it can still work through LocalAI’s image-generation support, but it will be much slower than a GPU workflow.[5][4]

## Fastest setup path

1. Install **Fooocus** from its official GitHub release.[2]
2. Download a compatible checkpoint in the app and generate a test image.
3. If you want more control, move to **ComfyUI** and use its starter workflow.[1][3]
4. If you want editing, install **Krita AI Diffusion** and use inpainting/outpainting.[4]

## Best next move

If your priority is “easiest,” use **Fooocus** first. If you want, I can give you a **Windows 11 local setup checklist** with the exact steps for Fooocus, plus a prompt template for generating adult, non-identifiable lingerie/bikini-style images without copying a real person.

## Human

I don't want person-specific sexual deepfakes, but I don't want to be restricted.

## Assistant

The cleanest way to stay **unrestricted locally** without going into person-specific sexual deepfakes is to run an open local generator like **Fooocus** or **ComfyUI** on your own machine. Fooocus is offline and open source, while ComfyUI’s current download page explicitly says it is free forever and runs on your hardware.[1][2]

## What “unrestricted” means

In practice, “unrestricted” local generation means you control the model and the UI, so you are not using a hosted service with platform moderation rules. That does **not** mean there are no legal or ethical limits, and you should still avoid identifiable real people, minors, coercion, or non-consensual sexual content. Stability AI’s public release also notes a safety classifier in its package, so behavior can vary by model and distribution even when the tool is local.[3]

## Easiest local option

If you want the simplest setup, use **Fooocus** first. Its GitHub repo describes it as offline and open source, which makes it a good low-friction local generator for exploring styles, poses, lighting, and general adult aesthetics without copying a specific person.[1]

If you want more power and less “hand-holding,” use **ComfyUI**. Its official download page emphasizes running on your hardware, being free forever, and being extensible, which makes it better for repeatable workflows and more advanced control.[4][2]

## Recommended path

1. Install **Fooocus** if you want the easiest start.[1]
2. Install **ComfyUI** if you want long-term control and workflow building.[2][4]
3. Use a local checkpoint that matches the style you want, then iterate on prompt, sampler, steps, and resolution.
4. Use inpainting/outpainting later if you want targeted edits without changing the whole image.

## Safety boundary

I can help you generate **adult, non-identifiable, consensual-looking** imagery and style prompts, but not person-specific sexual deepfakes or anything involving a real person’s likeness. If you want, I can give you a **safe local setup on Windows 11** plus a prompt template for generating uncensored-looking but non-identifiable bikini or lingerie images.
