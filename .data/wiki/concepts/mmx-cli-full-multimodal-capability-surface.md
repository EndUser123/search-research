---
title: "mmx-cli full multimodal capability surface: not chat-only"
created: 2026-08-04
updated: 2026-08-04
source: session-2026-08-04 (/www research on mmx after operator challenged chat-only characterization)
sources:
  - https://github.com/MiniMax-AI/cli (2,022 stars, MIT, last pushed 2026-08-04)
  - https://minimax-ai.chat/guide/minimax-cli/ (community guide, verified 2026-07-17)
  - https://www.marktechpost.com/2026/04/12/minimax-releases-mmx-cli-a-command-line-interface-that-gives-ai-agents-native-access-to-image-video-speech-music-vision-and-search/
  - https://platform.minimax.io/docs/token-plan/minimax-cli (official docs)
  - https://deepwiki.com/MiniMax-AI/cli (DeepWiki architecture overview)
tags: [mmx, minimax, multimodal, cli, capability-surface, fleet-routing, benchmark]
agent: grok
host: grok
cognitive_load: 2
verification: multi-source-verified
summary: >
  mmx-cli is MiniMax's official agent-first CLI exposing 7 capability areas:
  text chat, web search, vision, speech synthesis, image generation, video
  generation, and music generation. The /mmx Grok skill only surfaces 3 of 7
  (chat, search, vision) — the generation capabilities (speech, image, video,
  music) are accessed via tool-fallbacks.md or the minimax-multimodal-toolkit
  skill, not via the /mmx conductor skill. Benchmarking mmx requires treating
  generation tasks as a separate workload class from LLM inference.
relations:
  - target: wiki/concepts/tool-fallbacks.md
    type: refines
  - target: wiki/concepts/capability-cross-model-second-opinion.md
    type: refines
  - target: wiki/concepts/execution-path-based-model-routing-grok-build.md
    type: complements
---

# mmx-cli full multimodal capability surface

## Decision context

The operator asked whether codex, agy, and mmx have functionality worth
benchmarking. The initial response characterized mmx as a "chat-only HTTP
API wrapper with no filesystem access" — based on reading only the `/mmx`
Grok skill SKILL.md, which focuses on cross-model second opinions. The
operator challenged this. Running `mmx --help` and researching the tool
externally revealed the characterization was wrong: mmx is a full
multimodal platform CLI with 7 capability areas.

## Receipts

- **`mmx --help` output** (run this session, 2026-08-04): lists 10 resources:
  auth, text, speech, image, video, music, search, vision, quota, config, file.
  This is the primary evidence for the capability surface.
- **[[tool-fallbacks]]** lines 30-37: already documents `mmx image generate`,
  `mmx video generate`, `mmx speech synthesize` as fallback tools.
- **[[capability-cross-model-second-opinion]]** line 38: `/mmx` described as
  "HTTP API (chat-only)" — this is accurate for the /mmx SKILL scope but
  misleading about the CLI's full surface.
- **skill-catalog.md**: `minimax-multimodal-toolkit` skill covers
  text/image/video/speech/music — a separate skill from `/mmx`.

## The actual capability surface

Verified via `mmx --help` on this host (2026-08-04):

| Resource | Command | What it does | Benchmarkable as LLM inference? |
|----------|---------|-------------|-------------------------------|
| `text` | `mmx text chat` | Text generation (chat) | ✅ Yes — directly comparable to HTTP/PI/OC |
| `search` | `mmx search query` | Web search via MiniMax's index | ❌ No — search backend, not inference |
| `vision` | `mmx vision describe` | Image understanding | ❌ No — multimodal, different workload |
| `speech` | `mmx speech synthesize` | Speech synthesis (TTS) + voice cloning | ❌ No — generation task |
| `image` | `mmx image generate` | Image generation | ❌ No — generation task |
| `video` | `mmx video generate` | Video generation (async) | ❌ No — generation task |
| `music` | `mmx music generate` | Music generation + cover art | ❌ No — generation task |
| `file` | `mmx file upload/list/delete` | File storage on MiniMax platform | ❌ No — utility |
| `quota` | `mmx quota show` | Usage quota display | ❌ No — utility |
| `auth` | `mmx auth login/status/refresh/logout` | OAuth + API key authentication | ❌ No — utility |

## What went wrong with the original characterization

The `/mmx` Grok skill SKILL.md scopes itself to 3 capabilities (chat, search,
vision) because its domain is "cross-model second opinion" — it's a conductor
for routing prompts to MiniMax for a different model perspective. The other
4 capabilities (speech, image, video, music) exist as separate skills:

- **`minimax-multimodal-toolkit`** (`cc-skills-media` plugin) — text, image,
  video, speech, music generation
- **`private-uncensored-text-to-speech`** — references `mmx speech synthesize`
  as the TTS fallback
- **`tool-fallbacks.md`** — lists `mmx image generate`, `mmx video generate`,
  `mmx speech synthesize` as fallback tools

Reading only the `/mmx` skill gave an incomplete picture. The actual tool has
7 capability areas, not 3. The skill is a subset, not the full surface.

The broader pattern: the `/mmx` Grok skill, [[capability-cross-model-second-opinion]],
[[execution-path-based-model-routing-grok-build]], and [[tool-fallbacks]] all
reference mmx — but each only documents the subset relevant to its own scope.
No single concept documented the full surface until this one.

## External usage patterns

mmx-cli (GitHub: MiniMax-AI/cli, 2,022 stars, MIT license, last pushed today)
was released April 2026. MiniMax positions it as their **recommended** interface
for AI agents — they recommend it over their own MCP server ("💡 Recommended:
MiniMax CLI (mmx-cli)").

Practitioners use it primarily as a **multimodal generation pipeline** for
agent workflows. The most common use cases documented externally:
- Image generation from agent prompts (Cursor, Claude Code)
- Speech synthesis and voice cloning
- Video generation (async, takes minutes)
- Music generation

The text chat and search capabilities — what our fleet uses — are secondary
use cases in the broader ecosystem but are the primary use case for our
cross-model second opinion routing.

## What this means for our workspace

1. **Benchmarking mmx text chat** is the only capability directly comparable
   to our existing dispatch latency benchmark. It would compare the mmx CLI
   transport vs the HTTP API path for MiniMax-M3.

2. **Generation capabilities need their own benchmark** if we want to measure
   them. They have fundamentally different latency profiles (seconds to
   minutes), success criteria (was the artifact generated?), and cost models
   (per-generation). They don't fit in the current prompt→response latency
   matrix.

3. **The `/mmx` skill undersells the tool.** The skill only routes chat +
   search + vision. If the operator wants to generate images, video, or
   speech, they should use the `minimax-multimodal-toolkit` skill or
   call mmx directly — not `/mmx`.

4. **mmx is NOT a MiniMax model benchmark path.** For comparing MiniMax-M3
   latency across dispatch paths, `mmx text chat` is equivalent to the CLI
   paths (codex exec, agy -p) — it adds CLI overhead on top of the API call.
   The HTTP path in the existing benchmark already measures the pure API
   latency for MiniMax-M3.

## Falsifier

This entry is wrong if:
- MiniMax changes mmx-cli to remove capabilities or change the skill surface
- The generation capabilities become irrelevant to the fleet's workflow
- mmx text chat adds significant overhead that makes it a meaningfully
  different transport than the HTTP API (if so, benchmarking it becomes
  valuable for routing)

## Sources

- [MiniMax-AI/cli](https://github.com/MiniMax-AI/cli) (GitHub, 2,022★, MIT, last pushed 2026-08-04) — official repo, `mmx --help` output
- [MiniMax CLI Guide](https://minimax-ai.chat/guide/minimax-cli/) (minimax-ai.chat, verified 2026-07-17) — community documentation
- [MiniMax CLI Docs](https://platform.minimax.io/docs/token-plan/minimax-cli) (platform.minimax.io) — official platform docs
- [MarkTechPost](https://www.marktechpost.com/2026/04/12/minimax-releases-mmx-cli-a-command-line-interface-that-gives-ai-agents-native-access-to-image-video-speech-music-vision-and-search/) (MarkTechPost, 2026-04-12) — launch coverage
- [DeepWiki](https://deepwiki.com/MiniMax-AI/cli) (DeepWiki, updated 2026-06-12) — architecture overview
