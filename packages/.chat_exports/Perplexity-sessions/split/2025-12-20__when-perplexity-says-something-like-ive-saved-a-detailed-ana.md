---
title: "When perplexity says something like 'I've saved a detailed analysis to desc-similar-repos.md with implementation paths, "
date: "2025-12-20"
mode: "COPILOT"
uuid: "b3f32b3e-7d1e-43b9-9b74-c86f1a00d93c"
entry_count: 2
---

## Human

When perplexity says something like "I've saved a detailed analysis to desc-similar-repos.md with implementation paths, comparison tables, and specific code patterns from each repo.", what are they talking about?  I don't see where to download it.

## Assistant

That message refers to a *virtual* file name inside the Perplexity workspace context (used by the coding / repo-analysis agents), not to a real downloadable file in your account, so there is nothing you can download directly.[1]

## What that filename means

- Names like `desc-similar-repos.md`, `plan.md`, etc. are used as internal “documents” the agent *pretends* to write to while it reasons about code, repos, or tasks.[1]
- They are a prompt/UX convention to indicate: “a long-form analysis with sections, tables, and examples has been generated as part of this answer.”[1]

## Why you don’t see a download

- Perplexity’s current product surface (site + Comet) does not expose an actual filesystem where those `.md` artifacts live; they are not saved as user-visible files like in VS Code or a Git repo.[1]
- The contents that “would be in” `desc-similar-repos.md` are typically already in the response you just saw (or are compressed into that answer), rather than stored as a separate asset.[1]

## How to actually keep the analysis

To persist it in your own environment you have to:

- Copy the relevant sections from the answer and paste into a local `desc-similar-repos.md` (or whatever name) in your editor.[1]
- Or, if the agent’s answer clearly structures sections (plans, comparison tables, code patterns), copy them verbatim into your repo or notes system and treat that as the canonical file.[1]

## When this might change

- Perplexity’s roadmap (especially around Comet and agentic workflows) suggests deeper integration with “workspace” concepts, so in the future those virtual files might map to real, browsable artifacts.[1]
- As of now, though, those `.md` references are descriptive, not actual downloadable outputs.[1]

## Human

What the best way to get perplexity to create a file for download, rather than display the file contents?

## Assistant

Right now there is no first-class “generate a file and give me a download link” feature in Perplexity’s UI, so the reliable pattern is to have it emit text in a copy-paste-friendly way and then save it yourself. 

## Prompting style that works best

Use very explicit, file-shaped instructions, for example:

- “Generate the full contents of a file named `desc-similar-repos.md`. Do **not** summarize. Output only the file content, starting with the first line of the file and nothing else.”   
- “Create a `requirements.txt` file. Output only the file contents, suitable for copy-paste into a real file.” 

This minimizes extra prose and makes the response trivially copyable.

## How to make manual download painless

- Ask for fenced code blocks around the file so you can one-shot copy it:  
  “Put the entire file contents in a single ```markdown```
- If you need multiple files, request one block per file with clear headings, then copy each block into your editor. 

## What is not supported (today)

- There is no UI button to “export this as `foo.md`” or direct file attachment download from a generated artifact.   
- The earlier “saved to X.md” messaging does not map to an actual downloadable file in your account; it is just a virtual document metaphor.
