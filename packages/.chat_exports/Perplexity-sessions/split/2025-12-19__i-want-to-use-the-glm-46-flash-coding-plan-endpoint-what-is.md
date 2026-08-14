---
title: "I want to use the glm-4.6-flash coding plan endpoint, what is it?"
date: "2025-12-19"
mode: "COPILOT"
uuid: "a46397a2-2648-4c4d-bf27-d3ffceb801ea"
entry_count: 9
---

## Human

I want to use the glm-4.6-flash coding plan endpoint, what is it?

## Assistant

The GLM-4.6 “coding plan” models use the same OpenAI-compatible chat completions endpoint as the rest of Zhipu’s GLM-4.6 API: `https://api.z.ai/v1/chat/completions` (international) or the regional variants documented in your Z account.[1][2][3]

## Core endpoint

For GLM-4.6 (including flash-style coding variants under the Coding Plan), you send a POST request to the OpenAI-style chat endpoint, e.g.:

- **Base URL (global/international)**: `https://api.z.ai/v1/chat/completions`.[2][3]
- **HTTP method**: POST.[4]
- **Auth header**: `Authorization: Bearer <YOUR_Z_API_KEY>`.[1]

In the body, you set the **model** to the coding-plan variant you want, e.g. `"model": "glm-4.6-flash"` once that identifier is listed in your Z model list.[5][1]

### Minimal JSON example

```json
POST https://api.z.ai/v1/chat/completions
Authorization: Bearer YOUR_Z_API_KEY
Content-Type: application/json

{
  "model": "glm-4.6-flash",
  "messages": [
    { "role": "system", "content": "You are a helpful coding assistant." },
    { "role": "user", "content": "Write a Python function to merge two sorted lists." }
  ],
  "stream": false
}
```

This mirrors the OpenAI Chat Completions schema; you can toggle `"stream": true` for token streaming in tools/editors that support it.[3][4]

## Model name & plan linkage

- The **GLM Coding Plan** subscription just unlocks GLM-4.6 and its coding-optimized variants for your key; it does not change the endpoint itself.[6][5][1]
- The exact **model identifier** (e.g. `glm-4.6-flash`, `glm-4.6`, `glm-4.6v-flash`) is visible in your Z.AI dashboard and in any integration (Claude Code, Kilo, Cline, etc.) that lists available GLM models.[5][1]

If you paste your key into a tool that says “GLM AI (international endpoint)”, it is almost always pointing at `https://api.z.ai/v1/chat/completions` and swapping only the `model` field internally.[7][5]

## Human

That's not true.  There's a different endpoing for the coding plan.  And I want to use 4.6V

## Assistant

Perfect. You're correct. For the **GLM Coding Plan**, the endpoint is different from the standard API endpoint:

## GLM-4.6V Coding Plan Endpoint

**Base URL**: `https://api.z.ai/api/paas/v4`[1]

**HTTP Method**: POST to `/chat/completions`

**Authorization**: Bearer token with your Z.AI API key

### Example with GLM-4.6V

```json
POST https://api.z.ai/api/paas/v4/chat/completions
Authorization: Bearer YOUR_Z_AI_API_KEY
Content-Type: application/json

{
  "model": "glm-4.6v",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "https://example.com/image.png"
          }
        },
        {
          "type": "text",
          "text": "Describe this image"
        }
      ]
    }
  ]
}
```

The coding plan endpoint (`https://api.z.ai/api/paas/v4`) is specifically optimized for the Coding Plan subscription and integrates with tools like Claude Code via the `ANTHROPIC_BASE_URL` environment variable.[2][3]

Note: The documentation also shows an `/api/anthropic` variant (`https://api.z.ai/api/anthropic`) for Claude Code compatibility, but the primary paas/v4 endpoint is the coding plan standard.[3]

## Human

4.6v-flash please

## Assistant

The **GLM-4.6V-Flash** coding plan endpoint is:

**Base URL**: `https://api.z.ai/api/paas/v4`

**Model identifier**: `glm-4.6v-flash`

### Example request

```json
POST https://api.z.ai/api/paas/v4/chat/completions
Authorization: Bearer YOUR_Z_AI_API_KEY
Content-Type: application/json

{
  "model": "glm-4.6v-flash",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "https://example.com/image.png"
          }
        },
        {
          "type": "text",
          "text": "Analyze this image"
        }
      ]
    }
  ]
}
```

Use the same `https://api.z.ai/api/paas/v4/chat/completions` endpoint with `"model": "glm-4.6v-flash"` for the flash variant of the vision model through your Coding Plan subscription.

## Human

I can use 4.6V-flash to recreated code that is shown in a video but not described in the transcaript?

## Assistant

Yes, **GLM-4.6V-Flash can handle that use case well**. Since it's a multimodal vision model, you can:

1. **Extract frames from the video** at key moments where code is visible
2. **Pass the image(s) to GLM-4.6V-Flash** via the `image_url` parameter in your request
3. **Ask it to transcribe/recreate the code** shown on screen

### Example approach

```json
{
  "model": "glm-4.6v-flash",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "base64_encoded_frame_or_url"
          }
        },
        {
          "type": "text",
          "text": "Extract and recreate all the code visible in this screenshot. Provide it in a code block with the language specified."
        }
      ]
    }
  ]
}
```

### Strengths for this task

- **Native tool-calling vision model** with strong code understanding
- **Fast (flash variant)** compared to standard GLM-4.6V
- **Cost-effective** under your Coding Plan
- Handles **code syntax highlighting**, **UI elements**, and **context clues** from the visual

### Workflow tip

For longer videos, extract frames at logical breakpoints (when code appears on screen), batch process them, and GLM-4.6V-Flash should reliably reconstruct the code with high fidelity. This aligns with your video content intelligence and analysis work.

## Human

If I wanted to do summarization of the video audio/transcript and the video, would that all go go in "text" prompt value?

## Assistant

No, they would go in **separate content blocks** within the same `messages` array:

### Structure for video + transcript summarization

```json
{
  "model": "glm-4.6v-flash",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": {
            "url": "frame_from_video_1.jpg"
          }
        },
        {
          "type": "image_url",
          "image_url": {
            "url": "frame_from_video_2.jpg"
          }
        },
        {
          "type": "text",
          "text": "VIDEO TRANSCRIPT:\n\n[full transcript or key excerpts here]\n\nBased on these video frames and the transcript above, provide a comprehensive summary of the key concepts, code snippets, and takeaways."
        }
      ]
    }
  ]
}
```

### Key points

- **Multiple `image_url` blocks**: Pass multiple frames/screenshots from the video
- **Single `text` block**: Contains the transcript + your summarization prompt
- **Order matters**: Vision model processes images + text together as context

This lets GLM-4.6V-Flash correlate what it sees visually with what was said, giving you richer summarization that captures both the visual demonstrations and the spoken/written explanations.

For your video content analysis workflows, this approach lets you pass key frames + full or chunked transcripts in one API call.

## Human

I can't pass a video url?  Or an entire video mp4?  I have to do screen shots?

## Assistant

Based on the documentation, **GLM-4.6V supports `Video` as an input modality**, but the specifics on how to pass video files (MP4, etc.) versus frame URLs aren't fully detailed in the quick start.

From what I found:

- **Input Modality**: Video / Image / Text / File listed as supported
- **Examples shown**: Only `image_url` with HTTP URLs in the documentation

**Most likely**:
- You can pass **video URLs** (not local files) directly
- Or you may need to pass **base64-encoded video data** in the request
- The documentation examples only show image frames, suggesting that **frame extraction** is the primary documented approach

Given your use case with video content analysis, I'd recommend:

1. **Try passing a video URL** if you have one hosted online
2. **Fall back to frame extraction** if direct video URLs don't work
3. **Check the full API docs** or **contact Z.AI support** for definitive guidance on MP4 file upload formats

Since you're heavily into video intelligence workflows, this might be worth a quick test with a sample video URL to see if GLM-4.6V-Flash accepts it directly or requires frame preprocessing.

## Human

can it do image generation?  How would I tell it to create an infographic based on information in the transcript?

## Assistant

No, **GLM-4.6V-Flash cannot generate images**. It's a **vision model** (input only)—it can *analyze* images and video, but it cannot *create* them.

For **image generation**, you'd need a separate tool. In the Perplexity ecosystem (which you're using via Comet), you have access to **Perplexity's image generation capabilities**.

### Your workflow options

**Option 1: Two-step with GLM-4.6V-Flash + Perplexity image generation**
- Use GLM-4.6V-Flash to extract key data/structure from the transcript + video
- Feed that output (as a detailed prompt) into Perplexity's image generation tool to create the infographic

**Option 2: Use Perplexity Labs**
Since you're a Pro subscriber, **Perplexity Labs** can handle multi-step projects that include:
- Analyzing transcript/video content
- Generating infographics and visual assets as part of the workflow
- Creating charts, mockups, and images alongside research

Labs uses image generation tools internally and can orchestrate the full pipeline—summarize → structure data → generate infographic—in one project.

**Option 3: Direct image generation API**
If you want direct control, you could use other image generation APIs (DALL-E, Midjourney, Flux, etc.), but that's outside the GLM-4.6V-Flash scope.

For your video content analysis work, **Perplexity Labs** would be the most integrated approach since it combines research synthesis + image generation in one orchestrated project.

## Human

What free options exist?

## Assistant

## Free Image Generation Options

### **Free APIs**

| Option | Features | Notes |
|--------|----------|-------|
| **Pollinations** [1] | Free image generation API | No sign-up required for basic use |
| **Stable Horde** [1] | Distributed image generation | Community-powered, free tier available |
| **Puter.js** [2] | Free, unlimited image generation | Includes DALL-E 2, DALL-E 3, Flux.1, Stable Diffusion models—no API keys needed |
| **ImageRouter** [1] | Free image routing API | Combines multiple models |

### **Free Infographic Generators (specifically)**

| Option | Features | Notes |
|--------|----------|-------|
| **NotePT AI Infographic Generator** [3] | Text-to-infographic | No sign-up, free, multiple styles (flowchart, timeline, data viz) |
| **Infografix** [4] | AI infographic creator | Web/mobile, free, simple text prompts |

### **Open-Source Models (self-host)**

- **FLUX.1 [schnell]**  — Fast, high-quality open model[5]
- **Stable Diffusion 3**[5]
- **Stable Diffusion XL (SDXL) Lightning**[5]
- **DeepFloyd IF**  — Realistic visuals with strong language understanding[6]

### **Recommended Workflow for You**

1. **Extract key data** from transcript using **GLM-4.6V-Flash**
2. **Feed the structured data** into **NotePT AI Infographic Generator** or **Infografix** (completely free, no sign-up)
3. **Alternatively**, use **Puter.js** to call Flux.1 or DALL-E programmatically from your own code

All of these bypass paid APIs entirely. For your video analysis workflow, the **free infographic generators** are the quickest path—just pass them your summarized transcript data and they handle the visual design.

## Human

How can I tell what frames from a video are relevant to send to 4.6v-flash?

## Assistant

Here are the main approaches to identify relevant frames:

### **1. Transcript-Based Extraction (Recommended for you)**

Use **timestamps from your video transcript** to identify key moments:
- Extract frames at timestamps where important concepts are discussed
- Look for phrases like "as you can see," "this shows," "look at the code," "this diagram"
- Skip filler/intro/outro sections

**Tools**: Use FFmpeg or Python's `opencv-python` to extract frames at specific timestamps:

```python
import cv2

video_path = "video.mp4"
cap = cv2.VideoCapture(video_path)

# Extract frame at 5:30 (330 seconds)
cap.set(cv2.CAP_PROP_POS_MSEC, 330000)
ret, frame = cap.read()
cv2.imwrite("frame_530.jpg", frame)
```

### **2. Scene Detection (Automatic)**

Detect **visual changes** indicating new content:
- **Shot detection**: Use `scenedetect` Python library to find scene cuts
- **Optical flow analysis**: Detect when significant visual movement occurs (whiteboard writing, code changes, screen transitions)

```bash
scenedetect --input video.mp4 detect-content --threshold 27
```

### **3. Content-Aware Sampling**

For your video intelligence work, combine:
- **Keyframe extraction**: Every N seconds (e.g., every 10 seconds)
- **Manual review**: Scan thumbnails and pick ones with visible code/diagrams/important visuals
- **Redundancy removal**: Skip duplicate/similar frames (use image hashing or perceptual similarity)

### **4. Multi-Model Approach (Optimal)**

1. **Use GLM-4.6V-Flash iteratively**:
   - Send 5-10 candidate frames + transcript snippet
   - Ask: "Which of these frames are most relevant to understanding [topic]?"
   - GLM-4.6V-Flash ranks them by relevance

2. **Then send only top-ranked frames** for detailed analysis/extraction

### **My recommendation for your workflow**

**Start with transcript timestamps** → extract frames at those moments → optionally use GLM-4.6V-Flash to rank/filter → send final selection for summarization/code recreation.

This is most efficient for your video content analysis use case since you already have transcripts, and it minimizes unnecessary API calls.
