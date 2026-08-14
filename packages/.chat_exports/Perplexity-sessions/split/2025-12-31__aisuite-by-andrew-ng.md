---
title: "aisuite by Andrew Ng"
date: "2025-12-31"
mode: "COPILOT"
uuid: "3dd4cc4e-9c0c-44bb-b2cd-a4e74d74d6eb"
entry_count: 1
---

## Human

aisuite by Andrew Ng

## Assistant

aisuite is an open‑source Python library from Andrew Ng’s team that provides a unified, OpenAI‑style API to call models from many different LLM providers (OpenAI, Anthropic, Google, Hugging Face, Ollama, etc.) via a single client.[1][3]

## What aisuite is

- aisuite is a lightweight Python package that acts as a thin layer over existing provider SDKs, exposing a consistent interface for chat, completions and related operations.[6][1]
- It is designed specifically to make it easy to switch providers or compare models by changing only a model string such as `openai:gpt-4o` or `anthropic:claude-3-5-sonnet-20241022`.[3][8]

## Key capabilities

- **Unified client:** You create a single `Client()` and then call methods like `client.chat.completions.create(...)` regardless of whether the backend is OpenAI, Anthropic, Google, Ollama, or another supported provider.[1][6]
- Provider string routing: Models are addressed as `"provider:model"` (and sometimes additional suffixes like `ollama:llama3.1:8b`), allowing you to redirect traffic to a different provider without code changes elsewhere.[8][3]
- Tool and MCP support: aisuite includes helper layers for tool calls, letting you pass real Python functions and also connect to MCP-based tools with minimal boilerplate.[1]

## Installation and basic use

- Installation is via pip, with optional extras: `pip install aisuite[all]`, plus specific SDKs as needed such as `openai` or `anthropic`.[6][1]
- A minimal pattern is:
  - `import aisuite as ai`  
  - `client = ai.Client()`  
  - Then call `client.chat.completions.create(model="openai:gpt-4o", messages=[...])` or swap the model string to another provider.[6]

## When it’s useful

- Rapid multi‑provider experimentation: Great for benchmarking or A/B testing different LLMs without maintaining multiple bespoke integrations.[5][6]
- Production apps that may need to fall back to or switch between providers over time, since the abstraction isolates most of the integration churn.[5]
- Teaching and demos, where a simple, familiar OpenAI‑style API lowers the barrier to trying multiple vendors.[3][6]

If you share your current multi‑provider setup (SDKs, routing/proxy layer, how you select models), a more concrete mapping to aisuite’s patterns can be sketched.
