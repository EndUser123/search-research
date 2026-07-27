## Additional domains to add to the porting plan

### Domain 11 — Fleet operations

Managing the AI model fleet: routing tasks by cost/capability, benchmarking
performance, delegating work across agents, monitoring quota.

| Skill | Status | Gap |
|---|---|---|
| `model-benchmark` | ✓ Grok | Covered |
| `grok-parallel` | ✓ Grok | Covered |
| `cost-aware-delegation` | ✗ Claude-only | **Port** — route tasks to cheapest capable model |
| `external-delegation` | ✗ Claude-only | **Port** — delegate to OpenCode/Zen/llama.cpp |
| `agent-performance-analyzer` | ? .agents (may not work on Grok) | **Verify** — check if functional |
| `delegation-packet-runner` | ✓ .agents | Covered |
| `ai-api` | ✗ Claude-only | **Port** — unified LLM API calls |
| `ai-cli` | ✗ Claude-only | **Port** — parallel multi-LLM dispatch |
| `ai-models` | ✗ Claude-only | **Port** — model discovery and analysis |
| `ai-probe-*` (4 skills) | ✗ Claude-only | **Port** — model provider probing |

### Domain 12 — Media pipeline

Content ingestion and transformation: video, audio, images, transcripts.

| Skill | Status | Gap |
|---|---|---|
| `nlm-bulk-ingest` | ✓ Grok (built this session) | Covered |
| `nlm-to-wiki` | ✓ Grok (v3 handoff ready) | Covered |
| `notebooklm` | ✓ Grok | Covered |
| `imagine` | ✓ Grok | Covered |
| `video-vision` (crv) | ✗ Claude-only (cc-skills-media) | **Enable or port** — scene-change keyframe extraction |
| `vision-analysis` | ✗ Claude-only | **Port** — MiniMax M3 vision for per-frame description |
| `yt-nlm` | ✗ Claude-only | **Port** — batch transcript extraction via nlm source content |
| `yt-is` | ✗ Claude-only | **Port** — YouTube channel management |
| `yt-selenium` | ✗ Claude-only | **Port** — Selenium fallback transcript extraction |
| `codebase-to-course` | ✗ Claude-only | **Port** — turn codebase into interactive HTML course |
| `minimax-multimodal-toolkit` | ✗ Claude-only | **Port** — mmx text/image/video/speech/music |
| `minimax-music-gen` | ✗ Claude-only | **Port** — music generation |
| `minimax-music-playlist` | ✗ Claude-only | **Port** — music playlist management |

### Domain 13 — Operator self-improvement

The meta-learning loop that makes the agent fleet smarter over time.

| Skill | Status | Gap |
|---|---|---|
| `aar` | ✓ Grok | Covered |
| `debrief` | ✓ Grok | Covered |
| `dream` | ✓ Grok | Covered |
| `tp` | ✓ Grok | Covered |
| `why` | ✓ Grok | Covered |
| `learn` | ✗ Claude-only | **Port** — lesson capture with novelty detection |
| `reason` | ✗ Claude-only | **Port** — unified reasoning engine |
| `genius` | ✗ Claude-only | **Port** — strategic thought partner |
| `prospect` | ✗ Claude-only | **Port** — mines wiki for actionable improvements |
| `reflect` | ✗ Claude-only | **Port** — structured reflection |
| `skeptic` | ✗ Claude-only | **Port** — AI output validation |
| `truth` | ✗ Claude-only | **Port** — verify claims using evidence |
| `sequential-thinking` | ✗ Claude-only | **Port** — generate/critique/improve loop |
| `tot` | ✗ Claude-only | **Port** — tree-of-thoughts reasoning |
| `ut` | ✗ Claude-only | **Port** — architectural gatekeeper |
| `s` | ✗ Claude-only | **Port** — multi-persona strategy |

All covered on Grok side. Claude-side skills in this domain are thinking
frameworks that overlap with `/tp`, `/why`, and `/red-team` — porting
priority is lower since the function is covered, but the variety of
thinking lenses adds value.

### Updated totals

| Domain | Grok skills | Claude-only | Port priority |
|---|---|---|---|
| Fleet operations | 2 | 8 | P2 (affects multi-model fleet) |
| Media pipeline | 4 | 9 | P2 (nlm-to-wiki v3 needs crv) |
| Operator self-improvement | 5 | 10 | P4 (function covered, variety gap) |
