---
name: ytftss
description: YouTube Full Text Search CLI - search, download, and manage video subtitles
version: "1.0.0"
status: stable
category: tools
triggers:
  - /ytftss
aliases:
  - /ytftss

suggest:
  - /build
  - /test
  - /qa
---

# YouTube Full Text Search CLI

Search YouTube channel content, download subtitles, and manage video databases.

## Project Context

### Constitution / Constraints
- Tool usage: External CLI for video content management
- Solo-dev constraint: Personal video research, not enterprise media management

### Technical Context
- CLI tool: ytftss (YouTube Full Text Search)
- Commands: download, search, list, update, embeddings, vsearch, llm, summarize
- Features: Full text search, semantic search, AI summarization

### Architecture Alignment
- Tool wrapper pattern: Claude skill around external CLI
- Research support: Video content discovery and analysis

## Your Workflow
1. Parse ytftss command and arguments
2. Execute appropriate ytftss subcommand
3. Format and display results
4. Provide next-step suggestions

## Validation Rules
### Prohibited Actions
- Do NOT execute without valid URL/channel
- Do NOT claim download success without verification


## Quick Start

```bash
/ytftss download "https://www.youtube.com/@channel"
/ytftss search "machine learning"
/ytftss list --channel "ChannelName"
```

## Core Commands

### download
Download subtitles from channels or playlists.
```bash
/ytftss download <url> [options]
/ytftss download --playlist "<playlist_url>"
/ytftss download --jobs 8 "<url>"
```

### search
Full text search in downloaded content.
```bash
/ytftss search "query"
/ytftss search "query" --channel "ChannelName" --limit 20
```

### list
List channels, videos, and transcripts.
```bash
/ytftss list
/ytftss list --channel "ChannelName"
```

### update
Update subtitles for channels.
```bash
/ytftss update --channel "ChannelName"
```

## AI Features

### embeddings
Enable semantic search with Gemini embeddings.
```bash
/ytftss embeddings --channel "ChannelName"
```

### vsearch
Semantic search using embeddings.
```bash
/ytftss vsearch "semantic query" --channel "ChannelName"
```

### llm
Interactive chat with channel content.
```bash
/ytftss llm --channel "ChannelName" "Your question?"
```

### summarize
Generate AI summary of a video.
```bash
/ytftss summarize "<video_url_or_id>"
```
