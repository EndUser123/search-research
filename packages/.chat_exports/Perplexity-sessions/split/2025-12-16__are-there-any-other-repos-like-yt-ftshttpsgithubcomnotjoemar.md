---
title: "Are there any other repos like [yt-fts](https://github.com/NotJoeMartinez/yt-fts) from github.com?"
date: "2025-12-16"
mode: "COPILOT"
uuid: "6a597b15-be70-48d1-a9ba-3d3540d1f0c4"
entry_count: 1
---

## Human

Are there any other repos like [yt-fts](https://github.com/NotJoeMartinez/yt-fts) from github.com?

## Assistant

### Short answer

Yes. There are several GitHub projects that are conceptually similar to **yt-fts** in that they download YouTube subtitles/transcripts, index them (often in SQLite or a local store), and provide search (full‑text and/or semantic) via CLI or a small app. None are as feature‑complete as yt-fts, but a few are in the same space.

Below is a curated list of the closest matches.

***

## Very close in spirit: local subtitle DB + search

### 1. SubTubular – full‑text search for YouTube subtitles with GUI and CLI

- Repo: **h0lg/SubTubular**[1]
- What it does:
  - Full‑text searches YouTube **titles, descriptions, keywords, and captions** (subtitles)  
  - Can search across multiple videos, playlists, and channels[1]
  - Caches video metadata and subtitles locally so subsequent searches can be done offline and much faster[1]
  - Supports rich query syntax via LIFTI (exact, fuzzy, wildcard, multi‑word phrases, field‑specific queries, complex boolean expressions)[1]
- Interfaces:
  - GUI and CLI tools for searching and managing cache[1]
- Similarities to yt-fts:
  - Focus on **subtitles + metadata search**
  - Local cache/index, designed for repeated search workflows
  - Advanced query syntax (in yt-fts via SQLite FTS; here via LIFTI)

If you want something closest to yt-fts’ “search all captions” behavior but don’t need semantic search/RAG, this is the strongest parallel.

***

### 2. caption_search – personal full‑text search SQLite DB of YouTube captions

- Repo: **SuperSonicHub1/caption_search**[2]
- What it does:
  - Creates a **personal full‑text search SQLite database** of YouTube video captions[2]
  - Provides a **Flask web app** to browse/search those captions[2]
- Interfaces:
  - Web UI (Flask); underlying store is SQLite
- Similarities to yt-fts:
  - Uses **SQLite + full‑text search** for YouTube captions
  - Local, user‑controlled DB
- Differences:
  - Web app centric instead of pure CLI tooling
  - Does not appear to have embeddings/semantic search or LLM integration (at least in the README)[2]

If you like the yt-fts DB model but want a simple web UI rather than CLI, this one is worth a look.

***

## Related but narrower: transcript fetching without search or without DB

### 3. youtube-transcript-fetcher – CLI transcript downloader

- Repo: **stl3/youtube-transcript-fetcher**[3]
- What it does:
  - Command‑line tool in Go that **downloads transcripts** (subtitles) for a given video ID or URL[3]
  - Supports multiple languages and different output options (show text, duration, offset, language; configure output file, etc.)[3]
- Interfaces:
  - CLI only
- Similarities:
  - Automates transcript retrieval from YouTube
- Differences:
  - No local DB, full‑text index, or semantic search; it’s just a robust **fetcher**, not a search system[3]

Good as a building block if you want to roll your own indexing/search pipeline.

***

## Related “subtitle semantic search” work (non‑YouTube‑specific)

These are not YouTube‑only or not CLI‑centric, but are conceptually similar in that they build semantic search over subtitle corpora.

### 4. Semantic-Based-Video-Subtitle-Search-engine

- Repo: **HannahIgboke/Semantic-Based-Video-Subtitle-Search-engine**[4]
- What it does:
  - Builds a **semantic search engine** over a large set of subtitle files (from OpenSubtitles) using NLP + vector embeddings + ChromaDB[4]
  - Includes steps for cleaning, chunking, embedding, and storing in a vector DB, plus a Streamlit frontend[4]
- Similarities:
  - Same basic architecture as yt-fts semantic search: chunk subtitles → embeddings → vector store → semantic queries[4]
- Differences:
  - Focused on **movie/TV subtitles dataset**, not YouTube
  - Web UI (Streamlit) rather than CLI; not tied to yt-dlp

This repo is useful as a design reference for the semantic/RAG side of yt-fts, especially if you plan to customize or extend that part of your own stack.

***

## RAG‑over‑YouTube transcripts (more LLM assistant than general search)

These don’t necessarily give you a reusable caption DB across many channels like yt-fts, but they are “YouTube + transcripts + embeddings + RAG.”

### 5. rag-youtube-assistant

- Repo: **ganesh3/rag-youtube-assistant**[5]
- What it does:
  - Uses YouTube Data API v3 to fetch video data and transcripts on demand[5]
  - Stores structured data in a local database / vector store for RAG‑style Q&A (details in the repo)[5]
- Similarities:
  - YouTube transcript ingestion + embeddings + RAG over content
- Differences:
  - Framed as a **RAG assistant** rather than a generic CLI searcher
  - Likely more session/LLM‑centric; not a long‑lived sqlite FTS corpus in the same way as yt-fts

If you’re looking at yt-fts for its llm/vsearch/summarize commands, this repo is closer in spirit than random transcript fetch scripts.

***

## How these compare to yt-fts

yt-fts’ feature set is unusually comprehensive:

| Aspect                           | yt-fts                                         | Closest others                                                  |
|----------------------------------|-----------------------------------------------|------------------------------------------------------------------|
| Subtitles from channels/plays   | Yes (yt-dlp, bulk channel/playlist)           | SubTubular (channel/playlist), caption_search (depends) [1][2] |
| Local DB                         | SQLite FTS + optional ChromaDB                | caption_search (SQLite FTS), SubTubular (full-text index) [2][1] |
| CLI                              | Yes (download, search, vsearch, llm, summarize) | SubTubular (CLI + GUI), youtube-transcript-fetcher (CLI only)[1][3] |
| Semantic search (embeddings)     | Yes (OpenAI/Gemini; ChromaDB)                 | Semantic Subtitle Engine (OpenSubtitles), rag-youtube-assistant[4][5] |
| Built‑in LLM chat over corpus    | Yes (llm)                                      | rag-youtube-assistant (RAG assistant)[5]                         |
| Summarization by video           | Yes (summarize)                               | Mostly custom in RAG assistants; not in simple fetchers           |

So far, SubTubular and caption_search are the closest “same problem domain, local DB + search over YouTube subtitles” projects, while the semantic subtitle engine and rag-youtube-assistant sit closer on the “semantic search/RAG” side.

***

## If you want more like these

On GitHub, good topic searches that surface this ecosystem:

- `topic:yt-dlp youtube subtitles search`
- `youtube subtitles full text search sqlite`
- `youtube transcript semantic search chromadb`

Filtering on topics like `yt-dlp`, `semantic-search`, `rag`, and `sqlite` tends to pull in the same class of tools that yt-fts sits in.[6]
