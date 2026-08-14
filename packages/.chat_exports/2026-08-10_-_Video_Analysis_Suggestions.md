# 2026-08-10 - Video Analysis Suggestions

- **Created:** 8/13/2026, 7:44:03 AM
- **Exported:** 8/13/2026, 7:44:05 AM
- **Messages:** 5
- **Source:** browser_extension

---

## #1 · assistant

The short answer is: **surprisingly few**.

Google currently has a significant advantage because it owns YouTube and has added native support for passing **public YouTube URLs directly** to the Gemini API. The API fetches and processes the video in Google's infrastructure—you don't have to download or transcribe it yourself. [[image]Google AI for Developers+1](https://ai.google.dev/gemini-api/docs/video-understanding?authuser=31&hl=en&utm_source=chatgpt.com)

Here's the current landscape:

| Service | Accept YouTube URL directly? | Video understanding | My recommendation |
| --- | --- | --- | --- |
| Gemini API | ✅ Yes | Excellent | Best option today |
| OpenAI API | ❌ No | Excellent if you upload video | Excellent, but requires preprocessing |
| Anthropic Claude API | ❌ No | Good on uploaded media | Requires download/transcript |
| Mistral/Pixtral | ❌ No | Good | Upload required |
| AWS Bedrock | ❌ No | Depends on model | Upload required |
| Azure OpenAI | ❌ No | Excellent | Upload required |
| Vertex AI (Gemini) | ✅ Yes | Same as Gemini | Enterprise version |

## OpenAI

The OpenAI models are very capable of video reasoning, but they don't currently accept a YouTube URL and automatically fetch the video. The typical workflow is:

```
YouTube URL
      ↓
Download (yt-dlp)
      ↓
Upload video
      ↓
GPT
```

or

```
YouTube URL
      ↓
Transcript
      ↓
GPT
```

This extra step is the biggest disadvantage compared with Gemini.

## Claude

Claude has the same limitation.

It cannot simply receive

```
https://youtube.com/watch?v=...
```

and retrieve the video itself.

Typical pipeline:

```
YouTube
   ↓
yt-dlp
   ↓
Video or transcript
   ↓
Claude
```

Community reports consistently describe this as the normal workflow. [[image]Reddit](https://www.reddit.com/r/claude/comments/1sdbblp/why_cant_claude_access_the_content_of_a_youtube/?utm_source=chatgpt.com)

## Perplexity

Perplexity is an interesting middle ground.

It can often summarize YouTube links because it has its own retrieval pipeline rather than exposing a raw LLM API. However:

- 
this is primarily in the **consumer product**

- 
it is not the same developer experience as Gemini

- 
it is less deterministic for production use

## NotebookLM

NotebookLM can work well with YouTube videos because it integrates deeply with Google services, but it's designed for interactive research rather than as a developer API.

# If you're building an agentic workflow

Given everything we've discussed over the past several months, I'd actually recommend a **hybrid architecture** rather than relying on a single provider.

```
User pastes YouTube URL
          │
          ▼
Capability Router
          │
 ┌────────┴─────────┐
 │                  │
Gemini URL API      non-YouTube
 │                  │
 ▼                  ▼
Video understanding Download/upload
 │                  │
 └────────┬─────────┘
          ▼
Structured JSON
          ▼
Primary reasoning model
(GPT / Claude / local)
          ▼
Your downstream workflow
```

This gives you:

- 
Google's best-in-class ingestion of YouTube content.

- 
Freedom to use GPT, Claude, or your local models for the higher-level reasoning, planning, coding, or critique.

- 
A clean separation between **media acquisition** and **reasoning**, making it easy to swap models later.

## An option I think you'd like

Given the tooling you've been building around Claude Code and your orchestration system, another approach is to create a small **Evidence Acquisition Service** whose only responsibility is to accept arbitrary evidence sources and normalize them.

Instead of every LLM needing to understand YouTube, PDFs, websites, etc., you expose a single API:

```
POST /evidence

{
  "url": "https://youtube.com/..."
}
```

The service determines the appropriate acquisition strategy:

- 
YouTube → Gemini URL API

- 
PDF → OCR/document parser

- 
Web page → URL fetch

- 
GitHub → repository fetch

- 
Local file → upload

- 
Audio → transcription

It then returns a standardized artifact such as:

```
{
  "transcript": "...",
  "chapters": [...],
  "timestamps": [...],
  "frames": [...],
  "summary": "...",
  "metadata": {...}
}
```

Every downstream LLM—Claude, GPT, Gemini, or a local model—consumes the same normalized evidence rather than dealing with source-specific quirks.

For the kind of reliability-focused, model-agnostic orchestration you've been developing, this separation of concerns is likely to scale better than coupling your workflows directly to any one vendor's API.

## #2 · user

I do like the idea a lot, but for now, what local options exist?  I know I can download the video locally, then use ffmpeg (I think) to take snapshots and then have a vision model bascially ocr the images.  But are there models that can analyse the video easily?  I have a 5070 with 12gb ram.

## #3 · assistant

Yes. The local ecosystem has improved dramatically over the last year. With an RTX 5070 (12 GB VRAM), you can run several strong video-understanding pipelines locally, though there are tradeoffs between ease of use, accuracy, and speed.

## Recommendation for your hardware

Given your goals (research, agentic workflows, evidence acquisition), I'd prioritize these options:

| Approach | Quality | Ease | 12 GB VRAM | Recommendation |
| --- | --- | --- | --- | --- |
| Qwen2.5-VL + sampled frames | ★★★★★ | ★★★★☆ | ✅ | Best overall |
| InternVL3 + sampled frames | ★★★★★ | ★★★☆☆ | ✅ | Excellent |
| LLaVA-OneVision | ★★★★☆ | ★★★★☆ | ✅ | Good |
| VideoLLaMA 3 | ★★★★★ | ★★☆☆☆ | Probably | Worth trying |
| OCR every frame | ★★☆☆☆ | ★☆☆☆☆ | ✅ | Only for text-heavy videos |

The biggest surprise is that **you often don't need a video-specific model**.

# Option 1: Qwen2.5-VL (my first choice)

Qwen2.5-VL is currently one of the strongest open multimodal models.

Instead of reading every frame:

```
Video
   ↓
ffmpeg
   ↓
1 frame/sec
   ↓
Qwen2.5-VL
```

or

```
Scene detection
      ↓
Key frames
      ↓
Qwen2.5-VL
```

The model reasons across multiple images in a single prompt.

For many YouTube videos this is almost as good as using a dedicated video model.

Advantages:

- 
Excellent OCR

- 
Charts

- 
UI

- 
Code

- 
Slides

- 
Diagrams

- 
Can answer timeline questions

Works well in 7B and 3B versions.

# Option 2: VideoLLaMA 3

This is an actual video model.

Pipeline:

```
video
    ↓
VideoLLaMA 3
    ↓
summary
Q&A
reasoning
timestamps
```

It understands

- 
motion

- 
events

- 
sequence

- 
actions

- 
temporal relationships

which frame-based systems sometimes miss.

If your videos include demonstrations, this is much stronger.

# Option 3: InternVL3

InternVL has become one of the strongest open multimodal families.

Especially good at

- 
screenshots

- 
software

- 
webpages

- 
PowerPoint

- 
UI walkthroughs

Since many YouTube videos are really just narrated slides or browsers, InternVL is excellent.

# Option 4: LLaVA-OneVision

Very mature.

Supports

- 
multiple images

- 
video frame reasoning

- 
OCR

- 
diagrams

Runs fairly comfortably on consumer GPUs.

# Option 5: VLM + Whisper (very powerful)

Personally, I'd build this instead.

```
video
   │
   ├──► Whisper
   │       │
   │       ▼
   │   transcript
   │
   └──► ffmpeg
           │
           ▼
     key frames
           │
           ▼
     vision model

                ▼
         merge evidence
                ▼
          reasoning model
```

Now your reasoning model sees

- 
transcript

- 
screenshots

- 
timestamps

- 
OCR

- 
detected charts

instead of only pixels.

This is surprisingly close to Gemini for lecture-style videos.

# Better than "one frame per second"

Rather than

```
ffmpeg -r 1
```

I'd recommend scene detection.

```
video
   ↓
PySceneDetect
   ↓
Scene boundaries
   ↓
Representative frame
```

A 30-minute YouTube video might become

- 
120 representative images

instead of

- 
1,800 frames

with almost no information loss.

# An architecture I'd recommend

Knowing the systems you've been designing, I'd separate **evidence acquisition** from **reasoning**.

```
YouTube
     │
     ▼
Video downloader
     │
     ▼
Evidence pipeline
     │
     ├── Whisper
     ├── Scene detection
     ├── OCR
     ├── Key-frame extraction
     ├── Metadata
     └── Optional object detection
               │
               ▼
      Evidence bundle
               │
               ▼
      Any reasoning model
```

This has several advantages:

- 
You only process the video once.

- 
You can swap reasoning models without reprocessing.

- 
Different models can independently verify conclusions from the same evidence.

- 
The evidence bundle can be cached and reused.

## If I were building this today

For a solo developer with your RTX 5070 and an emphasis on reliability rather than chasing benchmark scores, I'd start with:

1. 
**yt-dlp** — download the video.

2. 
**Whisper large-v3 (or faster-whisper)** — generate a high-quality transcript with timestamps.

3. 
**PySceneDetect** — identify scene changes and extract representative frames.

4. 
**Qwen2.5-VL-7B-Instruct** (AWQ/GPTQ or another quantized variant if needed) — analyze the key frames and answer visual questions.

5. 
**A reasoning model** (local or cloud) — combine the transcript and visual observations into summaries, critiques, or structured evidence.

This pipeline is relatively straightforward to automate, fits well within consumer hardware, and avoids processing thousands of redundant frames while preserving most of the useful information in typical YouTube videos.

## #4 · user

What about Mini Max H3

## #5 · assistant

MiniMax H3 is a **very different kind of model** than what you're describing.

It's primarily a **video generation and editing model**, not a "watch a two-hour YouTube video and analyze it" model. It accepts multimodal inputs (text, images, video, audio) to generate or edit short videos—up to about 15 seconds per generation. It excels at reference-guided editing, motion transfer, and multimodal conditioning. [[image]MiniMax+1](https://minimaxi.com/blog/minimax-h3?utm_source=chatgpt.com)

For your use case—**"analyze this YouTube video locally"**—I'd distinguish three categories:

| Model | Generates video | Understands video | Good for long videos? | Local on 12 GB? |
| --- | --- | --- | --- | --- |
| MiniMax H3 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ No | Probably not practical |
| Qwen2.5-VL | ❌ | ⭐⭐⭐⭐⭐ | ✅ Yes | ✅ |
| InternVL3 | ❌ | ⭐⭐⭐⭐⭐ | ✅ Yes | ✅ |
| MiniMax M3 | ❌ | ⭐⭐⭐⭐⭐ | Potentially yes | Maybe, depending on quantization |

## The interesting one is actually MiniMax M3

Given what I know about your workflow, **I'd be more excited about MiniMax M3 than H3**.

MiniMax describes M3 as a native multimodal model with support for image and video inputs, a 1M-token context window, and long-video understanding in addition to coding and agentic capabilities. [[image]MiniMax+1](https://www.minimax.io/models/text/m3?utm_source=chatgpt.com)

That means an architecture like:

```
YouTube
   ↓
yt-dlp
   ↓
Extract video
   ↓
Feed frames/video chunks
   ↓
MiniMax M3
   ↓
Evidence
   ↓
Your orchestrator
```

is much closer to what you're trying to build than H3.

## For your RTX 5070 (12 GB)

If your objective is **local evidence acquisition**, I'd currently rank the options like this:

1. 
**Qwen2.5-VL 7B** — mature, excellent OCR, strong documentation, easy to integrate.

2. 
**MiniMax M3 (quantized)** — very promising because it combines coding, multimodal reasoning, and long context. I'd expect some experimentation to get it running comfortably on 12 GB VRAM.

3. 
**InternVL3** — particularly strong for software UIs, slides, and diagrams.

4. 
**LLaVA-OneVision** — solid and well supported.

5. 
**VideoLLaMA** — best when understanding motion is more important than static content.

## A direction I think is worth exploring

Because you're already building a model-agnostic orchestration system, I wouldn't optimize around a single video model. Instead, I'd investigate a **local evidence acquisition pipeline** that can automatically choose the cheapest tool that preserves the needed information.

For example:

```
Video
   │
   ├── Whisper → transcript
   ├── PySceneDetect → key frames
   ├── OCR (only on frames with text)
   ├── Motion analysis (optional)
   └── Speaker segmentation
          │
          ▼
Structured evidence bundle
          │
          ▼
Any multimodal reasoning model
```

In many educational or software-demo videos, this approach is **more efficient than feeding every frame into a vision model**, and it gives your downstream reasoning models richer, structured evidence to work from.

One thing I'm particularly interested in—and I think it fits your long-term architecture—is whether **MiniMax M3 can consume that structured evidence bundle directly while also acting as the reasoning model**. If it can, it could potentially replace both the vision model and the downstream LLM for many video-analysis tasks, simplifying your pipeline. That's something I'd want to benchmark before committing to a design.
