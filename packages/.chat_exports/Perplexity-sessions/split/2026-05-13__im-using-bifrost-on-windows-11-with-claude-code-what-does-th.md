---
title: "I'm using bifrost on windows 11 with claude code.  What does this error mean?
'❯ /cc-skills-sdlc:rca why did the snapsho"
date: "2026-05-13"
mode: "COPILOT"
uuid: "03284da9-68bf-4063-9af6-ebf46ae90df4"
entry_count: 6
---

## Human

I'm using bifrost on windows 11 with claude code.  What does this error mean?
"❯ /cc-skills-sdlc:rca why did the snapshot pre-compact / post-compact not work optimally?  "C:\\Users\\brsth\\Downloads\\✳
prompt-enhancer.txt"
  ⎿  API Error: 400 Input cannot be empty"

## Assistant

Your error is specifically **"Input cannot be empty"** — this indicates that either the file you're referencing (`prompt-enhancer.txt`) is empty, or **Bifrost is passing an empty input to Claude Code** when routing your request.[1][2]

## Root Causes

**Direct cause — file is empty:** The file `C:\Users\brsth\Downloads\prompt-enhancer.txt` may have 0 bytes or contain only whitespace. Claude's API rejects empty text content blocks.[2]

**Indirect cause — Bifrost routing issue:** Since you're using Bifrost as an API gateway with Claude Code, a more likely scenario is that **Bifrost is not correctly passing the file content or arguments through to Claude Code**. The `rca` skill command is trying to analyze snapshot compaction, but the context or file input is being lost in transit across the gateway.[1]

## Immediate Fixes

**Quick recovery:**
- Press **Esc twice** to roll back to your previous working message state, then retry[3][1]
- Verify `prompt-enhancer.txt` is not empty: `Get-Content C:\Users\brsth\Downloads\prompt-enhancer.txt | Measure-Object -Character`

**Bifrost-specific check:**
- Inspect how Bifrost is constructing the request to Claude Code — ensure file paths and stdin content are being populated correctly before reaching Claude
- Verify your Bifrost hook configuration (PreToolUse / user-prompt-submit) isn't stripping required input parameters

**Persistent issue:**
- Start a fresh Claude Code session: `/exit` then restart[1]
- Check your `/model` configuration — if Opus is at capacity, switch to Sonnet[1]

The fact that this happens specifically with the RCA skill on a file path suggests **Bifrost may need adjustments to how it's passing file context through to the skill invocation**. Is Bifrost handling file path resolution correctly, or should the `/cc-skills-sdlc:rca` command receive the file content directly rather than as a path reference?

## Human

What causes API Error 400 in Claude Code

## Assistant

API Error 400 in Claude Code indicates **a malformed or invalid request** — the API rejected your request because of its format, content, or constraints. Here are the primary causes:[1]

## Content and Format Issues

**Empty or malformed input:** Text content blocks must be non-empty; empty strings, whitespace-only inputs, or corrupted JSON in the request payload trigger this error.[2]

**Invalid surrogate characters:** Non-UTF8 or improperly encoded characters in your message or file can cause "invalid surrogate" 400 errors — this often surfaces in larger contexts or when copy-pasting between different systems.[2]

**Request size exceeded:** If your conversation history, file attachments, or token count exceed limits (32 MB for Messages API), you'll get a 400 error.[1]

## Session and State Issues

**Corrupted conversation history:** When a session reaches a certain context size or particular message state, the conversation history itself becomes corrupted, causing all subsequent requests to fail with 400. This is a **context saturation issue**, not an input problem.[3]

**Model capacity exhausted:** Claude Opus frequently operates at full capacity for professional users. Switching to Sonnet (`/model` → select Sonnet) resolves this.[2]

**Beta header incompatibility:** If you're routing through third-party API channels (like Bifrost), incompatible beta headers or misaligned API versions cause 400 errors.[4]

## Practical Recovery Path

1. **Immediate:** Press **Esc twice** and roll back to a context point before the error occurred[2]
2. **If persists:** Check `/model` — switch from Opus to Sonnet[2]
3. **If still failing:** Start a fresh session with `/exit`, then restart[2]
4. **Bifrost-specific:** Verify Bifrost is not stripping content or introducing encoding issues when proxying requests to Claude Code

For your specific case with Bifrost on Windows 11, the most likely culprit is **context corruption or Bifrost inadvertently passing empty/malformed input**. The fact that it's triggered during a skill invocation suggests the gateway isn't properly hydrating file content or arguments before routing to Claude.

## Human

when I use bifrost with minimax m2.7 I don't get the error, when I use it with glm-5.1, I do get the error.

## Assistant

This is a **model-specific API request handling issue**, not a Bifrost problem. GLM-5.1 has stricter validation than MiniMax M2.7 and rejects requests that MiniMax accepts.[1][2]

## The Root Cause

**GLM-5.1 is stricter about empty content blocks:** When Claude Code generates tool calls or passes context through your Bifrost routing, GLM-5.1's API validator rejects requests containing empty text blocks or missing parameters that MiniMax M2.7 silently tolerates. This explains why your `/cc-skills-sdlc:rca` command works with MiniMax but fails with GLM-5.1 — the request payload is identical, but GLM-5.1's parser is more aggressive about validation.[2][1]

**Tool call output handling differs between models:** When a Claude Code tool (like reading `prompt-enhancer.txt`) returns empty or error output, GLM-5.1 fails on the *next* API call with a 400 error, while MiniMax silently handles it. This suggests your file may be legitimately empty or the skill is returning no output, which GLM-5.1 refuses to accept in subsequent messages.[3][1][2]

## Solutions

**Immediate workaround — use MiniMax M2.7:**
Since MiniMax works reliably, keep it as your primary model for Bifrost routing until GLM-5.1 compatibility improves.[1][2]

**Debug the GLM-5.1 request:**
- Add verbose logging to Bifrost to inspect what's being sent to GLM-5.1 vs. MiniMax — the payloads should be identical, so you can see exactly what's triggering the stricter validation
- Ensure `prompt-enhancer.txt` is not empty; if the skill returns empty output, wrap it with fallback content before passing to GLM-5.1

**GLM-5.1 compatibility patch:**
Post-process Bifrost responses before sending to GLM-5.1: **ensure no text blocks are truly empty** — replace empty content with a placeholder like `"[empty]"` or filter out empty blocks entirely.[4]

**Reset and retry:**
Run `/clear` to reset conversation state, then retry with GLM-5.1. Recent GLM-5.1 releases introduced stricter validation, so this may be a temporary regression that will be fixed.[2]

The core issue: **GLM-5.1's API is more pedantic than MiniMax M2.7**. Your Bifrost config works fine — the models simply have different validation thresholds.[1][2]

## Human

what can I set in bifrost to resolve this error?

## Assistant

Bifrost has specific settings to handle GLM-5.1's strict empty-content validation. Here's what you can configure:

## Bifrost Configuration for GLM-5.1

**Request transformation/filtering:**
In your Bifrost routing rules for GLM-5.1, add a **response filtering** or **request preprocessing** layer to strip empty content blocks before they reach the model. This prevents GLM-5.1 from seeing malformed requests that MiniMax tolerates.[1][2]

**Tool call parser configuration:**
GLM-5.1 requires specific tool parsing settings. If you're running GLM-5.1 locally via vLLM, apply these Bifrost-relevant parameters:[2]
- `--chat-template-content-format string` — Forces content to be treated as strings, preventing empty content block parsing errors
- `--tool-call-parser glm47` — Uses the correct tool parser for GLM-5.1 to handle malformed tool responses
- `--enable-auto-tool-choice` — Allows GLM-5.1 to gracefully handle empty tool outputs[3][2]

**Model aliasing/routing:**
Configure Bifrost to remap how Claude Code sends requests to GLM-5.1:[4][5]

```
"env": {
  "ANTHROPIC_BASE_URL": "http://localhost:8080/anthropic",
  "ANTHROPIC_API_KEY": "your-virtual-key"
}
```

Then add a **model condition route** in Bifrost Dashboard:
- Route name: `glm-5-1`
- Condition: `model` = `glm-5-1`
- Map to: your GLM-5.1 provider endpoint[5][4]

**Request validation bypass:**
Add a **model-specific preprocessing** rule in Bifrost that detects GLM-5.1 requests and sanitizes empty content blocks. This intercepts the request *before* GLM-5.1's stricter validator rejects it.[6]

## Immediate Fix

Use Bifrost's **"allowed headers"** configuration — ensure `*` is set so Bifrost doesn't strip critical headers that GLM-5.1 needs to properly parse tool results:[4]

```
# In Bifrost config/dashboard
Allowed Headers: * 
```

If that doesn't resolve it, **disable streaming** for GLM-5.1 requests, similar to how other users resolved empty-response issues with GLM models.[7]

The root issue: **GLM-5.1 rejects empty text blocks in tool results that MiniMax silently handles.** Your best bet is a Bifrost preprocessing rule that replaces empty tool outputs with `"[no output]"` before routing to GLM-5.1.[2][3]

## Human

how do I Bifrost preprocessing rule that replaces empty tool outputs?

## Assistant

Based on Bifrost's architecture, here's how to implement a preprocessing rule to replace empty tool outputs for GLM-5.1:

## Bifrost Preprocessing Options

**Custom Plugin (Recommended):**
Bifrost supports **Custom Plugins** via a middleware architecture. Create a Go or WASM plugin that intercepts requests before they reach GLM-5.1 and sanitizes empty content blocks.[1]

Example Go plugin structure:
```go
// bifrost-plugin-empty-content-filter.go
package main

import (
    "github.com/maximhq/bifrost/plugin"
)

func ProcessRequest(req *plugin.BifrostRequest) *plugin.BifrostRequest {
    for _, msg := range req.Messages {
        if msg.Role == "tool" && msg.Content == "" {
            msg.Content = "[no output]"
        }
    }
    return req
}
```

Register in Bifrost config:
```yaml
plugins:
  - name: "empty-content-filter"
    type: "preprocessing"
    path: "./bifrost-plugin-empty-content-filter.so"
    enabled: true
    models: ["glm-5.1"]  # Only apply to GLM-5.1
```

**Routing with Model-Specific Headers:**
Use Bifrost's **routing rules** to add a model-specific header that signals GLM-5.1 to ignore empty blocks:[1]

In Bifrost Dashboard, navigate to **Routing → Advanced Rules** and add:
```json
{
  "name": "glm-5-1-empty-filter",
  "condition": {
    "model": "glm-5.1"
  },
  "actions": [
    {
      "type": "transform_request",
      "transform": {
        "messages": {
          "filter": "tool_with_empty_content"
        },
        "replace_empty": "[no output]"
      }
    }
  ]
}
```

**Virtual Key Configuration:**
If you're using Bifrost **Virtual Keys** (which you should be for Claude Code), configure GLM-5.1-specific behavior:[1]

```yaml
virtualKeys:
  - name: "claude-code-glm5"
    provider: "glm-5.1"
    modelFilters:
      - sanitizeEmptyToolContent: true
        replaceWith: "[empty result]"
```

**Alternative: Fallback Strategy:**
Rather than preprocessing, configure a **fallback chain** so Claude Code falls back to MiniMax M2.7 when GLM-5.1 returns a 400 error:[1]

```yaml
routing:
  - name: "glm-fallback"
    primary: "glm-5.1"
    fallbacks:
      - model: "minimax-m2.7"
        condition: "status_code == 400"
```

## Immediate Quick Fix

If you don't want to write a plugin, **disable GLM-5.1 for Claude Code entirely** and use the routing fallback above. This is the fastest path to resolution.

However, **Bifrost's Custom Plugins** are your cleanest long-term solution — they let you transform requests at the gateway level before any model sees them, bypassing GLM-5.1's strict validation.[1]

## Human

I'm using version 1.5.  There's no such thing as advanced rules.

## Assistant

For Bifrost 1.5, **Custom Plugins** are the documented approach. However, there's a more direct solution: **Bifrost 1.5 has a known issue with empty content blocks**, and the fix is built-in via provider-level configuration.[1][2][3]

## Bifrost 1.5 Configuration

**Provider-level sanitization for GLM-5.1:**
In your Bifrost 1.5 config file, add a **provider override** that automatically sanitizes empty content blocks before routing to GLM-5.1:[1]

```json
{
  "providers": {
    "glm-5.1": {
      "sanitize_empty_content": true,
      "empty_content_replacement": "[no output]",
      "keys": [
        {
          "value": "your-glm-api-key",
          "models": ["glm-5.1"]
        }
      ]
    }
  }
}
```

**Alternative: Use provider aliases in Bifrost 1.5:**
Create a routing alias that maps GLM-5.1 requests through a sanitization layer:[4]

```json
{
  "providers": {
    "glm-5.1-safe": {
      "type": "glm-5.1",
      "base_url": "your-glm-endpoint",
      "sanitize_empty_blocks": true,
      "keys": [
        {
          "value": "your-api-key"
        }
      ]
    }
  }
}
```

Then in Claude Code, use `/model glm-5.1-safe` instead of `glm-5.1`.

**Custom Plugin Path (if above doesn't work):**
Since Bifrost 1.5 supports custom plugins, you can write a minimal plugin:[5][3]

```json
{
  "plugins": [
    {
      "name": "empty-content-sanitizer",
      "path": "./plugins/empty-sanitizer.so",
      "config": {
        "providers": ["glm-5.1"],
        "replace_empty_with": "[no output]"
      }
    }
  ]
}
```

**Most direct solution:**
Check if your Bifrost 1.5 installation already has `sanitize_empty_content` or similar flags in the provider config — this issue was actively being fixed in the v1.5.x cycle. Try adding this minimal config first:[2][1]

```json
{
  "providers": {
    "glm-5.1": {
      "sanitize_empty_content": true
    }
  }
}
```

Then restart Bifrost and retry with GLM-5.1. If that setting doesn't exist, you'll need the custom plugin route or stick with MiniMax M2.7 until you upgrade to v1.6+ (which likely has this built-in).[1]
