---
title: "what's the domain used to create a single file of github repos?"
date: "2026-03-08"
mode: "COPILOT"
uuid: "eadf5652-c953-4f51-9602-1fee2b350c33"
entry_count: 2
---

## Human

what's the domain used to create a single file of github repos?

## Assistant

You’re probably thinking of **`github1s.com`**.

Example: take a repo URL like  
`https://github.com/owner/repo`  
and change the domain to:  
`https://github1s.com/owner/repo`  

This opens the repo in a single-file-like, VS Code-style web view where you can browse the whole codebase without cloning.

To clarify what you’re after: are you looking for a way to *browse* repos in a single-page view, or to *download* an entire repo as a single file (like a zip or bundle)?

## Human

nope, it's to make a repo ingestable for llms.

## Assistant

**The domain is `gitingest.com`.**

Replace "github.com" (or just "hub") in any GitHub repo URL with "gitingest.com" (or "ingest") to generate a single, LLM-optimized text file of the repo's contents.[1][2][3]

This tool concatenates the directory structure, file contents, and summaries into a prompt-friendly format, complete with token counts and stats for easy ingestion into models like Claude or ChatGPT.[4][5]

Example:  
`https://github.com/owner/repo` → `https://gitingest.com/owner/repo`  
It works for subdirs, branches too, and is open-source via coderamp-labs/gitingest.[6][1]

## Alternatives
| Tool/Domain | Trick | Notes |
|-------------|--------|-------|
| gitingest.com | hub → ingest | LLM-focused digest, stats included [2][3] |
| github1s.com | github.com → github1s.com | VS Code viewer (not text export) [prior context] |
| uithub.com | g → u | Similar text extract [6] |

Perfect for your AI/ML workflows with Claude Code and agentic systems.[user-information]
