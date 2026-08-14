---
title: "In the latest version of claude code, can we use different models in subagents?"
date: "2026-03-20"
mode: "COPILOT"
uuid: "fbaa94ad-7722-4f78-9db6-9622244821f8"
entry_count: 4
---

## Human

In the latest version of claude code, can we use different models in subagents?

## Assistant

Yes. In the current Claude Code experience (via Perplexity Computer), subagents can be configured to use different underlying models for different tasks, and the orchestrator can mix them within one workflow.[1][2]

## How model selection works

- The main “Computer” orchestrator typically runs a strong reasoning model (for example, Opus 4.6) and then delegates subtasks to other models that are better suited for specific work types.[1]
- As of the latest release, Computer explicitly supports **multi‑model orchestration**, assigning different models to different subtasks (e.g., one for research, another for code, another for images/video) inside a single overall run.[2][1]

## Subagents with different models

- Perplexity describes workflows where sub‑agents for research, coding, and content generation each run on distinct model families (Gemini for deep research, a dedicated coding model, specialized image/video models, etc.).[2][1]
- There is also a “Model Council” feature that runs multiple frontier models in parallel for a single task and synthesizes their outputs, which is another form of per‑subtask/per‑agent model differentiation.[2]

## What this means for Claude Code–style usage

- Within the Claude Code–like environment backed by Computer, you can now have **coding subagents** delegated to a dedicated coding model (e.g., GPT‑5.3‑Codex) while planning/reasoning remains on another model.[2]
- The harness is explicitly described as **model‑agnostic** and designed so that users can choose specific models for specific subtasks as token budgets and task types differ.[1]

## Practical implication for you

- If you are wiring Claude Code against Perplexity Computer, design your agent graph assuming:  
  - One orchestrator model for planning.  
  - Multiple subagents, each bound to a different model family based on role (research, coding, creative, etc.).[1][2]
- You should expect the configuration surface to expose per‑skill/per‑subtask model selection rather than forcing a single model across all subagents.[1]

If you share how you are defining subagents today (JSON/YAML/config for Claude Code), a more concrete mapping to this multi‑model setup can be sketched.

## Human

I believe in litellm, you can assign different coding plans to different agents.  Is that true?

## Assistant

Yes, but the terminology is slightly different than what you wrote.

## What LiteLLM actually supports

- LiteLLM lets you define many **model groups** and individual **model deployments**, then call specific groups/models from different agents or tools. Each “agent” can therefore use a different model or group.[1][2][3]
- The Router and Proxy can route calls based on the `model` or `model_name` you pass, so if your higher‑level agent framework associates “Agent A → model group X” and “Agent B → model group Y,” they will effectively have different “coding plans” (models/capabilities) behind them.[2][3][1]

## Agents + LiteLLM in practice

- In typical agent stacks (CrewAI, OpenAI Agents, etc.), the “agent config” has an `llm`/`model` field, and if that LLM is wired through LiteLLM, each agent can point at a different LiteLLM model or group.[4][5]
- LiteLLM’s Agent Gateway (A2A) adds per‑agent tracing and spend tracking, reinforcing the idea that each agent is a distinct entity that can be backed by its own model configuration.[6]

## Clarifying your “coding plans” idea

- FACT: LiteLLM does not natively have a first‑class “coding plan” object per agent; it exposes routing rules and model groups.[1][2]
- CONSENSUS: Most users approximate “different coding plans per agent” by:
  - Binding each agent to a different LiteLLM model group (e.g., `gpt-4o-coder`, `mistral-7b-fast`)  
  - Or using custom routing strategies that look at the agent/task and choose a deployment accordingly.[7][1]

If you describe how you are defining agents (e.g., CrewAI, OpenAI Agents, your own framework), a concrete example of “Agent X → coding plan A, Agent Y → coding plan B via LiteLLM” can be sketched in config or TypeScript/Python.

## Human

Can LiteLLM Proxy route tool calls to different providers for agents

## Assistant

Yes, with an important nuance: LiteLLM Proxy can route **each model/tool call** to different providers, and your agents can *implicitly* get different providers per tool, but the routing is model‑centric rather than “agent‑aware” in the OpenAI tools sense.[1][2][3]

## What LiteLLM Proxy actually does

- LiteLLM Proxy is an OpenAI‑compatible gateway where each configured `model_name` (or model group/alias) points at a specific provider + endpoint (OpenAI, Anthropic, Vertex, Bedrock, Ollama, etc.).[4][5][1]
- Routing decisions (including load‑balancing and fallback) are driven by the **model identifier** and router config (`model_list`, `router_settings`, `model_group_alias`), not by which agent or tool is calling.[3][6]

## How this interacts with tools

- Tool calls in the OpenAI‑style API are just **chat completions with tools/function‑calling**; the tool execution itself is handled by your app, not by LiteLLM.[7][8]
- However, you can:
  - Define different **model entries** in `config.yaml` that point to different providers.[1][4][3]
  - In your agent framework, bind each “tool agent” to a different `model` string; when that agent is invoked to execute a tool, the call to the proxy uses its bound model and thus hits a different provider behind the proxy.[2][9]

So:  
- FACT: LiteLLM Proxy routes by model name → provider; it does not inspect “which agent/tool” at the protocol level.[3][1]
- CONSENSUS: The common pattern is to treat each agent/tool as having its own model string, and let the proxy route those to different providers; this effectively gives you “different providers per tool/agent.”[10][9]

If you share a small snippet of how your agents and tools are wired (OpenAI client vs LangChain/CrewAI vs custom), a concrete `config.yaml` + call pattern can be sketched that yields “tool X → provider A, tool Y → provider B” via LiteLLM.

## Human

so if I have the z.ai coding plan, if I use litellm, the subagents in claude code can use the GLM models instead of Anthropic?

## Assistant

Mostly no: the Z.ai GLM Coding Plan for Claude Code is wired as a **drop‑in replacement for Anthropic models**, not as a separate provider you can freely reassign per subagent via LiteLLM.[1][2][3][4]

## How the GLM Coding Plan works

- The GLM Coding Plan is a subscription that makes GLM‑4.7 (and related GLM coding models) available **inside supported coding tools** such as Claude Code, Cline, Roo Code, etc., with quota managed by Z.ai.[2][1]
- For Claude Code, the Z.ai helper updates Anthropic config (auth token / base URL) so that Claude Code’s Anthropic calls are transparently served by Z.ai’s GLM endpoint instead of Anthropic’s API.[3][4]

## Why LiteLLM does not control these subagents

- In the GLM Coding Plan integration, Claude Code talks to **Z.ai’s Anthropic‑compatible gateway**, not to your own LiteLLM proxy; the plan explicitly “can only be used within specific coding tools” and “cannot be called separately via API.”[1]
- LiteLLM does support Z.ai GLM models as a provider (e.g., `model="zai/glm-4.7"`), but that is for your own API usage; it is **separate** from the closed coding‑plan integration that Claude Code uses.[5][6]

## What you can and cannot do

- You **can**:  
  - Use the GLM Coding Plan so that Claude Code (including its subagents) runs on GLM instead of Anthropic, via the Z.ai integration.[4][2][1]
- You **cannot** (with the official coding plan):  
  - Use LiteLLM to selectively route only some Claude Code subagents to GLM while others stay on Anthropic; the tool just sees “Anthropic,” which is globally redirected to Z.ai’s GLM gateway.[3][1]
  - Call the plan quota from LiteLLM directly; Z.ai docs state coding‑plan quota is only usable inside supported tools, not as a general API.[1]

If you want per‑subagent model routing (e.g., some agents on Anthropic, some on GLM) you would need Claude Code to talk to **your** LiteLLM gateway instead of the Z.ai helper, and then fund GLM usage via standard Z.ai or OpenRouter API, not the coding plan subscription.[6][5][3]
