---
title: "Do you understand the below solution?  'In claude code, I'm using the anthropic subscription. But I have other provider "
date: "2026-03-21"
mode: "COPILOT"
uuid: "10d80311-9243-4989-bd8e-dece2550d93d"
entry_count: 4
---

## Human

Do you understand the below solution?  "In claude code, I'm using the anthropic subscription. But I have other provider subscriptions available. How can I use my other subscripts with claude code subagents, and leave the main cli orchestrator using the anthropic models?"

---

So every terminal has a unique port that they must map the Anthropic Base URL to? And then when we use a sub-agent, the proxy will detect the sub-agent name and automatically route it to the correct provider and model.

Can we have multiple openai compatible providers at the same time in a proxy config, so that different subagents can use different models from different openai compatible providers?

## Assistant

Yes, I understand what you’re describing—and it’s completely feasible with the right proxylayer. The core idea is:

- The main Claude Code “cli orchestrator” talks to Anthropic via your Anthropic subscription.  
- Subagents route through the **same** proxy, but the proxy routes them to different providers/models based on subagent name, not by terminal port.

Below are the key pieces and whether your statements are correct.

***

### 1. Terminal ports vs. routing

> “So every terminal has a unique port that they must map the Anthropic Base URL to?”

No. You don’t need a **unique port per terminal**. Instead:

- You run **one proxy** (e.g., a local `http://localhost:4000`‑style service) that exposes an OpenAI‑compatible‑ish endpoint.  
- Every Claude Code instance (in any terminal) is configured to send its traffic there via `ANTHROPIC_BASE_URL` or similar proxy settings.[1][2][3]
- The proxy then decides:  
  - If the request is from the **main orchestrator**, send it to Anthropic.  
  - If it’s from a **named subagent**, route it to another provider (OpenAI, DeepSeek, local‑LLM, etc.).[4][5][1]

Effectively: **one proxy, many terminals**, and the proxy uses headers / URLs / request‑body patterns (including subagent name) to route, not terminal ports.

***

### 2. Multiple OpenAI‑compatible providers in one proxy

> “Can we have multiple OpenAI‑compatible providers at the same time in a proxy config, so that different subagents can use different models from different OpenAI‑compatible providers?”

Yes, and this is already a common pattern in LLM‑proxy tools:

- **LiteLLM Proxy** and **LM‑Proxy** let you define multiple providers (OpenAI, Anthropic, DeepSeek, local‑LLM, etc.) behind a single front‑end `/chat/completions`‑style endpoint.[6][7]
- You can configure **model‑to‑provider mappings**, e.g.:  
  - `gpt‑4o` → `https://api.openai.com`  
  - `glm‑4‑plus` → `https://zai.zhipu.ai`  
  - `qwen‑plus` → Aliyun’s OpenAI‑compatible endpoint.[8][6][4]

You can then:

- In your proxy config, map:  
  - `code‑reviewer` → `provider=openai, model=gpt‑4o`  
  - `data‑analyst` → `provider=zai, model=glm‑4‑plus`  
  - `documentation‑writer` → `provider=deepseek, model=deepseek‑chat`.[5][9][8]

So: **yes**, you can have multiple OpenAI‑compatible providers active at once, and different subagents can use different models from different providers via the same proxy.

***

### 3. How subagents get routed

Claude Code sends subagent requests over the same HTTP‑based channel as the main orchestrator, just with different metadata (e.g., subagent name embedded in the prompt or in a header).[10][11][5]

Your proxy can:

- Parse the request to detect whether it’s from the **main session** (orchestrator) or a **subagent** by name or role.[5]
- For main orchestrator: forward to Anthropic.  
- For subagent `X`: pick provider/model from your mapping table and rewrite `model` and `base_url` accordingly.[4][1][8]

This is effectively what projects like `claude‑code‑proxy` or LiteLLM‑based setups do.[1][4][5]

***

### 4. What you’d typically do in practice

A minimal concrete sketch:

1. Spin up a proxy (e.g., LiteLLM or custom) on `http://localhost:4000`.[6][1]
2. Configure each terminal’s Claude Code to route via that proxy (set `ANTHROPIC_BASE_URL=http://localhost:4000`).[2][3]
3. In the proxy config:

   ```yaml
   # LiteLLM‑style pseudocode
   model_list:
     - model_name: "main-claude"
       litellm_params:
         model: "anthropic/claude-3-opus"
     - model_name: "code-reviewer"
       litellm_params:
         model: "openai/gpt-4o"
     - model_name: "data-analyst"
       litellm_params:
         model: "zai/glm-4-plus"
   ```

4. From Claude Code, spawn subagents with predictable names (`code‑reviewer`, `data‑analyst`, etc.), and the proxy auto‑routes those to the right provider/model.[10][8][5]

***

If you tell me which stack you’re already using (e.g., LiteLLM, LM‑Proxy, or a custom Python proxy), I can give you a concrete config snippet and runtime wiring for your multi‑provider, multi‑subagent setup.

## Human

Doesn't the chat history I showed you state what repo we are using?

## Assistant

You’re right to be skeptical here, but: **no, this chat history does not contain any explicit pointer to a specific repo** that you’re using for the proxy / multi‑provider setup.

What *is* in the chat so far is:

- Your **goal** (use Anthropic for the main orchestrator, other paid providers for subagents via a proxy).  
- A **high‑level pattern** (per‑subagent routing inside a proxy, not per‑terminal port).  

But there is **no visible mention of a concrete repo name, GitHub URL, or project identifier** for the proxy or agent stack you’re running (e.g., some custom `claude‑code‑proxy`, `liteLLM‑based‑router`, or your own MCP server).[1][2][3]

So right now I’m reasoning entirely from **first principles + generic tooling** (LiteLLM, generic HTTP proxies, Claude Code’s subagent model), not from a known repo config.  

If you paste:

- The repo URL you’re using, or  
- A snippet of the proxy config / agent definitions (e.g., LiteLLM `config.yaml`, your `ANTHROPIC_BASE_URL` wiring, or agent‑names),

then I *can* answer against that specific repo and tell you exactly how to wire “orchestrator on Anthropic, each subagent on its own provider.”

## Human

claude-code-proxy

## Assistant

Yes. Given that you’re using **`claude-code-proxy`**, you are almost certainly referring to **one of the existing `claude-code-proxy` repos** that already support multi‑provider routing (the most relevant one for your goal is `seifghazi/claude-code-proxy`, which explicitly supports **agent‑level routing to different LLM providers**).[1][2][3]

Below is how this fits your original question:

***

### 1. What `seifghazi/claude-code-proxy` does

The proxy:

- Intercepts Claude Code requests and forwards them to Anthropic by default.[2]
- Optionally lets you **route specific agents to different providers** (e.g., route `code-reviewer` to GPT‑4o on OpenAI, while everything else still goes to Anthropic).[2]

This is exactly the pattern you described:  
**main orchestrator → Anthropic**,  
**subagents → their own providers** (including multiple OpenAI‑compatible backends at once).[1][2]

***

### 2. Can you have multiple OpenAI‑compatible providers at once?

Yes, in this setup:

- The proxy config (`config.yaml` or env vars) can define multiple upstream providers (OpenAI, Azure, local‑LLM‑via‑Ollama, etc.).[3][1][2]
- The agent‑routing section maps **agent names** (or labels) to specific models/providers, e.g.:[2]

  ```yaml
  agent_routing:
    - agent_name: code-reviewer
      provider: openai
      model: gpt-4o
    - agent_name: data-analyst
      provider: openrouter
      model: z-ai/glm-4.5-air
  ```

So different subagents can indeed use different models from different OpenAI‑compatible providers while the orchestrator still uses Anthropic.[4][3][2]

***

### 3. How to wire this with Claude Code

Typical wiring:

1. Run the proxy (Docker or local) on a fixed port, e.g., `http://localhost:3001`.[2]
2. In all terminals, set:

   ```bash
   export ANTHROPIC_BASE_URL=http://localhost:3001
   claude
   ```

   This makes **all** requests (including subagents) go through the proxy.[5][2]

3. The proxy:
   - For **main orchestrator traffic**, forwards to `ANTHROPIC_FORWARD_URL` (Anthropic).[2]
   - For requests with matching agent names, rewrites `model` and `base_url` to point at the configured provider (OpenAI, Azure, OpenRouter, etc.).[3][2]

***

### 4. What you should confirm in your setup

Since there are **multiple** `claude-code-proxy` repos (e.g., `seifghazi/`, `kiyo-e/`, `fuergaosi233/`, etc.), please confirm:

- Which exact repo you’re running:  
  - `seifghazi/claude-code-proxy` (best fit for named agent routing)?[2]
  - Or `kiyo-e/fuergaosi233` (more focused on OpenAI‑/<model> mapping via env vars)?[1][3]

If you paste:

- the repo URL, and  
- a snippet of your `config.yaml` or proxy env vars,

I can give you a **concrete, minimal config** that:

- Leaves the orchestrator on Anthropic, and  
- Routes each subagent to a specific OpenAI‑compatible provider and model.

## Human

but I can have two providers that are openai compatible in the same proxy config, pointing to different models?

## Assistant

Yes. You can absolutely configure **two (or more) OpenAI‑compatible providers** in the same `claude-code-proxy`‑style proxy, each pointing to different models.[1][2][3]

### 1. What “OpenAI‑compatible” means here

Many backends speak the OpenAI‑style API (`/chat/completions`, `model` field, etc.) but sit at different URLs:

- OpenAI proper (`api.openai.com`)  
- OpenRouter, Azure OpenAI, Antigravity, local‑LLM via Ollama, etc.[4][5]

Your proxy can treat **all of these as separate “OpenAI‑compatible” providers** reachable via different base URLs.[2][1]

***

### 2. How to configure multiple providers in one proxy

In a typical `claude-code-proxy`‑style config (or LiteLLM‑based proxy), you do:

1. Define upstream providers (each with its own URL and key):[1][2]

   ```yaml
   upstream_providers:
     - name: openai
       base_url: https://api.openai.com
       api_key: ${OPENAI_API_KEY}
     - name: openrouter
       base_url: https://api.openrouter.ai
       api_key: ${OPENROUTER_API_KEY}
   ```

2. Define models from those providers:[3][2]

   ```yaml
   models:
     - model_name: gpt-4o
       provider: openai
       model: gpt-4o
     - model_name: glm-4-plus
       provider: openrouter
       model: z-ai/glm-4.5-air
   ```

3. Then route subagents to those models by name (not by terminal or port):[2]

   ```yaml
   agent_routing:
     - agent_name: code-reviewer
       model: gpt-4o
     - agent_name: data-analyst
       model: glm-4-plus
   ```

Result:  
- The orchestrator still goes to Anthropic.  
- `code‑reviewer` talks to `gpt‑4o` on OpenAI.  
- `data‑analyst` talks to `glm‑4‑plus` on OpenRouter (or any other OpenAI‑compatible backend).[3][2]

***

### 3. Answer to your direct question

> “Can I have two providers that are OpenAI‑compatible in the same proxy config, pointing to different models?”

**Yes.** The standard pattern is:

- One proxy front‑end (`ANTHROPIC_BASE_URL=http://localhost:3001`).[6][2]
- Multiple OpenAI‑compatible backends (`openai`, `openrouter`, `azure`, `ollama`, etc.).[4][1]
- Each subagent mapped to a specific `<provider>/<model>` tuple via config.[2][3]

If you tell me **which exact `claude-code-proxy` repo and config format** you’re on (YAML vs env‑vars, `seifghazi/` vs `kiyo‑e/`), I can give you a minimal, copy‑paste config fragment that wires exactly:  
“orchestrator → Anthropic, subagent A → provider X, subagent B → provider Y”.
