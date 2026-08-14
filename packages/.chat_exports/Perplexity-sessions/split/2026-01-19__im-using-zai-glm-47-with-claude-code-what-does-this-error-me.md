---
title: "I'm using z.ai glm-4.7 with Claude Code.  What does this error mean?
  ⎿  API Error: 400 {'type':'error','error':{'messa"
date: "2026-01-19"
mode: "COPILOT"
uuid: "669483e0-4750-4b7d-aeea-9c372213d3f1"
entry_count: 1
---

## Human

I'm using z.ai glm-4.7 with Claude Code.  What does this error mean?
  ⎿  API Error: 400 {"type":"error","error":{"message":"Operation
     failed","code":"500"},"request_id":"20260120004603521702667b55427f"}

## Assistant

**The error indicates a server-side issue with Z.AI's GLM-4.7 API during a request from Claude Code.**[1]

## Error Breakdown
HTTP 400 typically signals a client-side parameter error in Z.AI's API, but the nested business "code":"500" and "message":"Operation failed" point to an internal server error.  This mismatch occurs because Z.AI wraps server faults (true 500s) in 400 responses for their Anthropic-compatible endpoint used by Claude Code.[2][3][1]

## Common Causes
- Transient server overload or processing failure on Z.AI's end, especially under high load with GLM-4.7.[1]
- Integration glitches in Claude Code setups, like invalid prompts, timeouts, or config mismatches (e.g., ~/.claude/settings.json).[4][2]
- Rate limits, expired GLM Coding Plan subscription, or account issues triggering backend failures.[1]

## Fixes
Retry the request after a short wait, as server errors often resolve quickly.  Verify Claude Code config: ensure ANTHROPIC_AUTH_TOKEN is your Z.AI API key, ANTHROPIC_BASE_URL is "https://api.z.ai/api/anthropic", and models map correctly (e.g., GLM-4.7 for sonnet/opus).  Run `claude update` for the latest version, check `/status` in-session, or re-run the Z.AI env script: `curl -O "https://cdn.bigmodel.cn/install/claude_code_zai_env.sh" && bash ./claude_code_zai_env.sh`.  If persistent, contact Z.AI support with request_id "20260120004603521702667b55427f".[2][1]
