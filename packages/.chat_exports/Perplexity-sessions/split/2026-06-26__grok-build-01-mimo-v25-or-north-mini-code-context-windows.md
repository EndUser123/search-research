---
title: "Grok Build 0.1, MiMo V2.5, or North Mini Code context windows"
date: "2026-06-26"
mode: "COPILOT"
uuid: "aa7f029a-e051-46f9-9b87-f1ee5cd92126"
entry_count: 1
---

## Human

Grok Build 0.1, MiMo V2.5, or North Mini Code context windows

## Assistant

Here are the context window sizes for the three models you asked about:

| Model | Context Window |
|-------|----------------|
| **Grok Build 0.1** | 256K tokens [1][2][3] |
| **MiMo V2.5** | 1M (1,048,576) tokens [4][5][6] |
| **North Mini Code** | 256K tokens [7][8] |

### Key details:

- **Grok Build 0.1** (xAI): 256K tokens, accepts text + image inputs, designed for agentic coding workflows. Can hold an entire mid-sized codebase in memory.[2][3]

- **MiMo V2.5** (Xiaomi): 1M tokens (roughly 2,097 pages of text). Native omnimodal model processing text, images, video, and audio. Testing shows best performance for the first ~110-130K tokens before struggling.[9][6]

- **North Mini Code** (Cohere): 256K tokens (roughly 512 pages of text) with 64K max output. Built for AI coding agents and automated engineering pipelines.[7][8]

**MiMo V2.5 has the largest context window at 1M**, roughly 4× larger than Grok Build 0.1 and North Mini Code's 256K.[5]

For your agentic AI orchestration work, MiMo's 1M context could hold entire codebases, though note the performance degradation beyond ~130K tokens. Grok Build 0.1 is specifically optimized for agentic coding despite the smaller context.[3][9]

What's your primary use case—coding agents, long-horizon orchestration, or something else? This would help determine which context size matters most for your setup.
