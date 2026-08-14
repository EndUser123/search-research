---
title: "are there repos that use gemini-cli for youtube video analysis or socials that describe how to do it, that don't require"
date: "2026-03-29"
mode: "COPILOT"
uuid: "04262942-db99-4222-a45f-e444bcf8969a"
entry_count: 2
---

## Human

are there repos that use gemini-cli for youtube video analysis or socials that describe how to do it, that don't require downloading the youtube video first?

## Assistant

Yes—there are a few relevant repos and workflows that use Gemini (often via its API rather than the CLI) to analyze YouTube videos without downloading them first, plus some social‑media posts that describe how to do it.[1][2][3]

***

### Repos that analyze YouTube with Gemini

- **`aviz85/gemini‑youtube‑analyzer`**  
  A GitHub repo that lets you analyze any YouTube video by URL and get AI‑powered insights (e.g., summaries, key topics) using Google Gemini. It hooks into the video page or transcript metadata instead of requiring a full local download.[1]

- **`sohei56/youtube‑summary‑notify‑with‑gemini`**  
  This repo automatically detects new videos from specified YouTube channels, generates summaries using Gemini, and sends notifications (e.g., to Slack or email). It runs against the YouTube channel feed and video metadata, not against downloaded MP4s.[2]

Neither of these is a **pure `gemini‑cli` terminal‑only setup**, but they show the pattern you’d want:  
  - fetch title / transcript / metadata via YouTube Data API or HTML scraping,  
  - pass that text (and optionally frames/audio) to Gemini for analysis.[4][2][1]

***

### Where `gemini‑cli` itself currently stands

- The official `google‑gemini/gemini‑cli` repo has an open feature request for **YouTube‑link support** and local video‑upload, but it is not yet implemented; the CLI currently expects either text or local files, not raw YouTube URLs.[5][6]
- Workarounds shared in the ecosystem (e.g., LinkedIn posts and issues) typically:
  - fetch YouTube transcripts or metadata via other tools,  
  - feed that text into `gemini‑cli` or `gemini‑api` as context.[7][5][4]

***

### Step‑by‑step approach you can reuse

To analyze YouTube/social videos with Gemini **without downloading the MP4**, you can:

1. **Get video text**:  
   - Use the YouTube Data API or an open‑source scraper (e.g., `youtube‑transcript‑api`) to pull title, description, and captions.[3][4]
2. **Combine into context**:  
   - Stitch heading, description, and top‑n chunks of transcript into a single text block.  
3. **Run Gemini‑powered analysis**:  
   - Call the Gemini API (or a wrapper script) with a prompt like:  
     - “Summarize this YouTube video, extract main topics, and list possible viewer questions.”  
   - Or plug that into a `gemini‑cli`‑style agent that takes `-c` context from a pipeline:  
     - `youtube-insights | gemini --prompt "Analyze this video transcript ..."`. [8][4][3]

***

### Social‑media / blog posts that walk through it

- A **Google Codelab** titled *“Build a Gemini‑Powered YouTube Summarizer”* walks you through building a summarizer that consumes YouTube video data and feeds it to Gemini.[3]
- Several LinkedIn posts and YouTube videos describe using Gemini (often via browser extensions or API) to analyze YouTube videos by URL rather than uploaded files, including “YouTube video understanding”‑style prompts.[9][10][11][7]

If you tell me whether you want this as a **pure CLI pipeline** (e.g., `gemini-cli` + shell scripts) or a **small service** (Python/Node microservice), I can sketch a concrete repo‑style layout plus a minimal example that never touches `yt-dlp` or direct MP4 downloads.

## Human

Details on Smitha Kolan Gemini CLI YouTube demo

## Assistant

Smitha Kolan’s demo is not a full standalone YouTube video about `gemini-cli` itself, but a **short, high‑impact walkthrough** where she shows how the Gemini CLI can bootstrap an entire tech‑tutorial project from a single YouTube link.[1][2][3]

***

### What the demo shows

- **Input**: she pastes a YouTube link to a tech tutorial video into the Gemini CLI prompt.[2][1]
- **CLI action**: Gemini CLI then:
  - understands the video’s topic and structure from the URL / metadata (and, if available, linked GitHub repo or description),  
  - scaffolds a project (directories, files, dependencies) that matches the tutorial,  
  - writes or adjusts code to align with what’s shown in the video.[4][3][1]
- **Key trick**: when the GitHub link is missing from the video description, Gemini CLI can **search for the correct repo** and wire it into the project setup automatically.[3][1]

This is framed as a “vibe‑coding” style demo: you give it a YouTube tutorial URL and it gives you a working local project, minus manual copying, file‑naming, or hunting for dependencies.[1][3]

***

### Where you can see it

- **LinkedIn post & screenshot thread**:  
  Smitha published a post titled broadly “I just used the new Gemini CLI to set up an entire tech tutorial project from scratch, giving it only the YouTube link to my video!”; it shows the workflow and results in a narrative + screenshots.[1]
- **Twitter/X recap tweet**:  
  She also summarized the same demo in a viral tweet explicitly saying: “I used the new Gemini CLI and gave it only the YouTube link of a tech tutorial, and it set up the entire project for me, perfectly.”[2][4]
- **Blog/tutorial references**:  
  Several write‑ups (e.g., “Complete Guide to Gemini CLI”) cite her demo as the canonical example of using a YouTube link as the sole input to generate a full project.[5][3]

There isn’t (as of now) a long‑form YouTube video *labelled* “Smitha Kolan Gemini CLI YouTube demo”; the primary artifact is the **LinkedIn/X post + screenshots showing the CLI session** rather than a narrated video walkthrough.[6][2][1]

If you want, I can reconstruct a **minimal CLI script** that approximates her demo flow (YouTube URL → Gemini CLI → project scaffold) using the public API and `gemini-cli` patterns.
