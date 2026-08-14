---
title: "why do I keep getting this error in claude code v2.1.96+ on windows when using glm 4.x and 5.x?

  ⎿  API Error: 400 {'e"
date: "2026-04-08"
mode: "COPILOT"
uuid: "a5079cf0-adcb-4a1b-9438-d106e89bca64"
entry_count: 3
---

## Human

why do I keep getting this error in claude code v2.1.96+ on windows when using glm 4.x and 5.x?

  ⎿  API Error: 400 {"error":{"code":"1210","message":"Invalid API parameter, please check the
     documentation."},"request_id":"20260409051917d0cc3c1677c34aa5"}

## Assistant

This error (Zhipu AI GLM code 1210) indicates invalid API parameters sent to their `/api/coding/paas/v4/chat/completions` endpoint, often due to mismatches between Claude Code's OpenAI/Anthropic-style requests and GLM's stricter schema. Claude Code v2.1.96+ on Windows integrates GLM 4.x/5.x via env vars like `ANTHROPIC_DEFAULT_OPUS_MODEL=glm-5` and Z.ai API key, but common issues include unsupported fields (e.g., images, certain tool formats, extra_body like `chat_template_kwargs`), context length exceeds (e.g., >200k tokens), or messages structure errors.[1][2][3]

## Likely Causes
- **Parameter mismatches**: Claude Code sends Anthropic-specific params (e.g., system prompts, tool_choice) not fully compatible without GLM Coding Plan config; Z.ai is OpenAI-compatible but rejects extras like vision or concurrent tools.[4][5]
- **Context/token limits**: Requests hit GLM-5's ~200k-204k limit, triggering 1210 instead of explicit errors.[2][3]
- **Windows-specific**: WSL path/env issues or unconfigured `~/.claude/settings.json` fail model mapping (e.g., default to unsupported GLM variant).[6][2]
- Consensus: Frequent in Claude Code/GLM since GLM-5.1 release; retries or `/clear` work temporarily, but root is param validation.[7][4]

## Fixes (Test in Order)
1. Edit `~/.claude/settings.json` (use `claude doctor` or `vim ~/.claude/settings.json` in WSL/PowerShell):
   ```
   {
     "env": {
       "ANTHROPIC_BASE_URL": "https://api.z.ai/api/coding/paas/v4",
       "ANTHROPIC_API_KEY": "your-z.ai-key",
       "ANTHROPIC_DEFAULT_OPUS_MODEL": "glm-5",
       "ANTHROPIC_DEFAULT_SONNET_MODEL": "glm-4.7"
     }
   }
   ```
   Restart Claude Code; run `/status` to verify.[2]
2. Disable images/tools: Set env `DISABLE_VISION=1`; avoid MCP/tools or complex prompts initially.[8]
3. Clear session (`/clear`) and retry; if persists, check Z.ai dashboard for quota/plan expiry (code 1309).[9][4]
4. Update Claude Code: `npx @anthropic-ai/claude-code@latest` (native Windows support improved post-2025).[6]

Confidence: High (matches 10+ reports); if GLM plan expired, renew at z.ai/subscribe. Next step: Share your `~/.claude/settings.json` (redact key) or full request logs for exact param diff. What GLM model/version exactly (e.g., glm-5.1)?[1][2]

## Human

GLM-5 context length limits and how to avoid exceeding

## Assistant

GLM-5 (Zhipu AI/Z.ai) supports a 200K token context window (precisely ~202,752 tokens in many configs), with up to 128K output tokens. Exceeding triggers errors like 1210 (invalid param, often misreported for context) or 1261; Claude Code hits this via cumulative chat history/tools/images.[1][2][3][4][5]

## Model Variants
| Variant   | Input Context | Max Output | Notes [6][7] |
|-----------|---------------|------------|------------------------|
| GLM-5    | 200K-202K    | 128K      | Standard; Coding Plan optimized |
| GLM-5.1  | 202K         | 128K      | Long-horizon tasks; auto-cache |
| GLM-4.x  | 128K-202K    | Varies    | Lower for "air" variants |

## Avoidance Steps
- Monitor tokens: Use Claude Code `/status` or Z.ai dashboard; prioritize recent/important context first.[8]
- Compact history: Run `/clear`, `/compact`, or set env `CONTEXT_PRUNE=true` in `~/.claude/settings.json`; enable auto-compaction at 95K-120K reserved.[9]
- Segment prompts: Split large files/codebases; leverage caching (1/5 cost for prefixes).[10][8]
- Limit params: Set `max_tokens=4096` initially; disable vision/tools if unused (`DISABLE_VISION=1`).[11]

Next step: In Claude Code, run `/status` now and share token count. Free tier quotas cap effective context (e.g., 700 input/min).[1][11]

## Human

What are best practices for context caching in GLM-5

## Assistant

GLM-5 context caching is automatic and implicit: Z.ai detects identical/highly similar content (e.g., repeated system prompts, prefixes) across requests, reusing computations at 1/5 input cost ($0.20/M tokens cached read; storage free). Cache hits show in `usage.prompt_tokens_details.cached_tokens`; ideal for multi-turn chats, RAG, or coding sessions like Claude Code.[1][2][3]

## Key Benefits
- Cost: Cached input ~80% cheaper vs. fresh.[3][1]
- Speed: Skips reprocessing repeated prefixes.[1]
- Scope: Works on GLM-5/5.1/4.x via `/api/coding/paas/v4/chat/completions`; TTL ~24h or session-based.[4][1]

## Best Practices
- **Prefix consistency**: Place stable system prompts/context first; repeat exactly for hits (e.g., "You are a data analyst...").[3][1]
- **Multi-turn optimization**: Reuse prefixes in chats; segment >100K docs and chain summaries.[1][3]
- **Monitor usage**: Check `cached_tokens` in responses; aim for 20-50% hit rate in long sessions.[1]
- **Claude Code tweaks**: Use `npx` version (avoids standalone cache bugs); `/compact` or `--no-resume` to preserve hits; set `cache_control: null` implicitly.[5][4]
- **Avoid misses**: No manual config needed; minimize variations (e.g., no dynamic injections mid-prefix); test with identical curl requests.[1]

Confidence: High (official docs primary); Claude Code bugs (e.g., sentinel replacement) can force misses—switch to `npx @anthropic-ai/claude-code@latest`. Next step: Log a multi-turn response and inspect `usage` for `cached_tokens`.[5][1]
