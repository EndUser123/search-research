# 2026-08-10 - Implementation Evaluation Request

- **Created:** 8/13/2026, 7:43:54 AM
- **Exported:** 8/13/2026, 7:43:56 AM
- **Messages:** 5
- **Source:** browser_extension

---

## #1 · assistant

I think you're pointing at something important, and my answer is actually **different today than it would have been six months ago**.

You don't necessarily need to build and host your own cloud service anymore.

OpenAI has been moving toward a model where ChatGPT can:

- 
use connected apps,

- 
call custom tools via MCP,

- 
perform browser/computer-use tasks,

- 
and execute multi-step workflows. [[image]OpenAI Help Center+2[image]OpenAI+2](https://help.openai.com/en/articles/11487775-connectors-in?utm_source=chatgpt.com)

That changes the architecture considerably.

## Option 1 — ChatGPT's built-in computer use (my preferred direction)

If your plan and platform expose Computer Use, then the ideal workflow is almost exactly what you described:

```
You (phone)

↓
ChatGPT

↓
Your Windows PC

↓
Run:
    yt-dlp
    ffmpeg
    whisper
    python
    git
    ripgrep

↓
Analyze results
```

No Azure.

No AWS.

No Google Cloud.

The computation stays on **your own computer**, while ChatGPT remotely orchestrates it (subject to the capabilities available on your account and device). OpenAI has been rolling out desktop computer-use and remote-control capabilities rather than requiring users to build this infrastructure themselves. [[image]OpenAI+2[image]OpenAI+2](https://openai.com/index/chatgpt-for-your-most-ambitious-work/?utm_source=chatgpt.com)

## Option 2 — Custom MCP tool (the one I'd recommend for you)

Given the work we've done on your agentic coding environment, I actually think an MCP tool is the cleaner long-term design.

Instead of exposing `yt-dlp`, expose capabilities:

```
AcquireEvidence
```

Supported inputs:

- 
YouTube

- 
GitHub

- 

- 
Website

- 
Local file

- 
Research paper

Internally it decides whether to use:

- 
yt-dlp

- 
Whisper

- 
OCR

- 
browser extraction

- 
GitHub API

The rest of your system never cares how the evidence arrived.

That's a cleaner abstraction and matches the architectural style you've been developing.

## Option 3 — Small local service

This is what I was describing earlier.

Not cloud.

Just something listening on:

```
https://localhost:8443
```

or

```
http://127.0.0.1:8080
```

ChatGPT calls:

```
AcquireEvidence(video_url)
```

It returns:

```
{
  transcript: ...
  chapters: ...
  references: ...
}
```

Again, no Azure required.

## Would I rent cloud infrastructure?

For you?

Probably **not initially**.

You already have:

- 
a Windows workstation,

- 
local models,

- 
Claude Code,

- 
Codex,

- 
orchestration,

- 
multiple LLM lanes.

Your workstation is a perfectly capable "evidence server."

I'd only move it to Azure/AWS if you later wanted:

- 
24/7 availability,

- 
sharing with teammates,

- 
heavy GPU workloads,

- 
or automation while your PC is off.

## I think there's an even bigger opportunity

I wouldn't build a **YouTube transcript service**.

I'd build an **Evidence Acquisition Platform**.

Imagine telling ChatGPT:

> 
"Review this."

and pasting:

- 
a YouTube URL

- 
a GitHub repo

- 
a PDF

- 
a Stack Overflow page

- 
an RFC

- 
a Reddit discussion

The acquisition layer automatically:

1. 
Determines the source type.

2. 
Chooses the best extractor.

3. 
Retrieves the content.

4. 
Extracts references.

5. 
Fetches those references.

6. 
Returns a normalized evidence bundle.

Then I perform the reasoning over that bundle.

That's much more powerful than "run `yt-dlp`," and I think it fits the architecture you've been evolving remarkably well.

## #2 · user

I do have computer use within the ChatGPT desktop application from OpenAI, don't I? I'm on the Pro subscription. I pay $20 a month.

## #3 · assistant

Based on what you've told me, I think there's a good chance you're mixing together **ChatGPT** and **Codex** capabilities.

The current desktop app combines Chat, Work, and Codex into a single application, and **Computer Use on Windows** is available for eligible users. One of its intended uses is exactly what you described: you can start work on your Windows machine and then continue or steer it remotely from ChatGPT on your phone while the Windows PC remains the host for the files, browser, and shell. [[image]OpenAI Help Center+1](https://help.openai.com/en/articles/6825453-chatgpt-release-notes?utm_source=chatgpt.com)

However, there's an important distinction:

- 
**You**, in this chat on your phone, are talking to **ChatGPT**.

- 
I **don't automatically have access** to your desktop session or permission to operate your computer from here.

If you've started a **Computer Use** session (or a **Work** task that has access to your desktop), then that agent can interact with your Windows machine. If you haven't, I can't simply decide to take over your PC.

### For your YouTube example

If your desktop has Computer Use enabled, then in principle the workflow could be:

1. 
Open the YouTube link.

2. 
Retrieve the transcript (using YouTube, `yt-dlp`, or another installed tool).

3. 
Save the transcript locally.

4. 
Analyze it.

5. 
Follow every repository, paper, and reference mentioned.

That's exactly the kind of task Computer Use is designed to help automate. [[image]OpenAI Help Center](https://help.openai.com/en/articles/6825453-chatgpt-release-notes?utm_source=chatgpt.com)

### What I'd like to explore with you

Given how you've built your AI coding environment, I actually think there's a much more powerful pattern.

Instead of asking:

> 
"Can ChatGPT run `yt-dlp`?"

I'd ask:

> 
**"Can I expose my workstation as a trusted capability provider to ChatGPT?"**

If the answer is yes (through Computer Use, Work, MCP, or a supported plugin), then you gain much more than YouTube transcripts. You effectively get an **evidence acquisition workstation** that can:

- 
retrieve transcripts,

- 
clone GitHub repositories,

- 
search code,

- 
run benchmarks,

- 
inspect PDFs,

- 
execute scripts,

- 
and return structured evidence for analysis.

I think that's a significantly more valuable capability for the workflows you've been building.

One question for you: **When you say you have Computer Use, have you actually used it to control your Windows desktop from your phone already, or have you just noticed that the feature is available in the desktop app?** That will tell us which integration path is most promising.

## #4 · user

I've only heard of the feature being available, so marketing can sometimes be in advance of delivery, that's for sure.

## #5 · assistant

That's a healthy instinct. AI marketing often describes the destination before every account has the feature.

Based on the current documentation, here's what I think is true:

- 
**The ChatGPT desktop app exists** and is actively maintained. [[image]OpenAI Help Center](https://help.openai.com/en/articles/9982051?utm_source=chatgpt.com)

- 
**Computer Use on Windows is a real feature**, not just a concept. OpenAI's release notes describe it as allowing ChatGPT/Codex to see, click, and type in Windows applications, with remote control from ChatGPT on iOS/Android while your Windows machine remains the host. [[image]OpenAI Help Center](https://help-lb.openai.com/en/articles/6825453-chatgpt-kiad%C3%A1si-megjegyz%C3%A9sek?utm_source=chatgpt.com)

- 
**Rollout is feature- and account-dependent.** OpenAI often enables new capabilities gradually, and some require the desktop app to be up to date or to be using the Work/Codex experience rather than a normal chat. [[image]OpenAI Help Center+1](https://help-lb.openai.com/en/articles/20001277-using-the-built-in-browser-in-the-chatgpt-desktop-app?utm_source=chatgpt.com)

For you specifically, I'd verify rather than assume. It should only take a couple of minutes:

1. 
Update the ChatGPT desktop app from the Microsoft Store.

2. 
Look for **Work** or **Codex** in the desktop app.

3. 
See whether you have a **Computer Use** or **Remote Control** option when starting a task.

4. 
From your phone, check whether you can view or continue a task that's running on your Windows PC.

If all four are present, then your original idea becomes very interesting.

## I think there's a high-value experiment for your setup

Instead of building an MCP server or custom HTTP service first, try to answer one question:

> 
**Can ChatGPT Computer Use run a local command and bring the results back into the conversation?**

For example:

```
yt-dlp --write-auto-subs <YouTube URL>
```

or

```
python analyze_transcript.py
```

If that works, then you've effectively gained a general-purpose "evidence acquisition" capability without writing infrastructure.

If it **doesn't** work—perhaps because Computer Use is sandboxed or can't invoke arbitrary local programs—*that's* when I'd pivot to an MCP tool or a small local service.

I actually think this is worth investigating before you build anything. If OpenAI's native Computer Use can orchestrate the kinds of workflows you're interested in, it could eliminate a significant amount of custom engineering. Given how much effort you've put into building orchestration and tooling around AI-assisted development, discovering where the native capabilities end—and where your own extensions begin—could save you a lot of time.
