---
title: "in claude code, I have a '/deep-research' command.  is it from a repo or is it built in?  It has something to do with wo"
date: "2026-06-30"
mode: "COPILOT"
uuid: "968a74bc-a44a-4424-8761-36307adb7051"
entry_count: 6
---

## Human

in claude code, I have a '/deep-research' command.  is it from a repo or is it built in?  It has something to do with workflows.

## Assistant

`/deep-research` is a **built-in (bundled) workflow** that ships natively with Claude Code — not from a community repo.[1]

## What It Actually Is

It's part of Claude Code's **Dynamic Workflows** system, introduced in v2.1.154.  A dynamic workflow is a JavaScript script that Claude writes and a runtime executes in the background — separate from your interactive session. `/deep-research` is the one pre-bundled workflow Anthropic ships; all others are either ones Claude writes on demand or ones you've saved yourself. 

## What `/deep-research` Does

When you run `/deep-research <question>`, it: 

- Fans out **parallel web searches** across multiple angles of the question
- Fetches and cross-checks each source it finds
- Has independent agents **adversarially vote on each claim** — claims that don't survive cross-checking are filtered out
- Returns a **single cited report** at the end while your session stays responsive throughout

It requires the WebSearch tool to be available and can spawn up to **1,000 agents per run** (with up to 16 concurrent). 

## The `/workflows` Command

`/workflows` is the companion command — it lists all running and completed workflow runs. You can drill into any run to see per-phase agent counts, token totals, elapsed time, and individual agent results. Key controls include `p` to pause/resume, `s` to save the run's script as a reusable command, and `x` to stop. 

## Availability

Requires **Claude Code v2.1.154+** and a paid plan (Pro, Max, Team, or Enterprise). On Pro specifically, you need to enable it from the Dynamic workflows toggle in `/config`.  If workflows are disabled (via `/config`, `settings.json`, or the `CLAUDE_CODE_DISABLE_WORKFLOWS=1` env var), the `/deep-research` command disappears entirely. 

## Custom Workflows

The pattern is extensible — you can ask Claude to write a workflow for any task (or use the `ultracode` keyword trigger), then press `s` in the `/workflows` view to save it as your own slash command. Saved workflows live in `.claude/workflows/` (project-scoped) or `~/.claude/workflows/` (global).  So if you see other `/deep-*` style commands in your environment, those are likely ones you or someone else saved this way.

## Human

I seem to be using it with minimax.  How is that?  Can I use other models?  local lmstudio models?

## Assistant

You're using `/deep-research` with MiniMax because you've **redirected Claude Code to MiniMax's API** by setting environment variables in `~/.claude/settings.json`. `/deep-research` itself is the built-in workflow — but instead of using Anthropic's Claude models, it runs through MiniMax by proxying the request.

## How You're Using MiniMax

MiniMax exposes an **Anthropic-compatible endpoint**, so Claude Code can talk to it by setting three env vars: 

- `ANTHROPIC_BASE_URL`: MiniMax's Anthropic proxy URL (e.g., `https://api.minimax.io/anthropic`)
- `ANTHROPIC_AUTH_TOKEN`: Your MiniMax API key
- `ANTHROPIC_MODEL`: The MiniMax model name (e.g., `MiniMax-M2.5` or `MiniMax-M2.7`)

Example config in `~/.claude/settings.json`: 

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.minimax.io/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your_minimax_api_key",
    "ANTHROPIC_MODEL": "MiniMax-M2.5",
    "ANTHROPIC_SMALL_FAST_MODEL": "MiniMax-M2.5",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "MiniMax-M2.5"
  },
  "model": "MiniMax-M2.5"
}
```

After saving, restart terminal and run `claude` — `/status` will show the MiniMax model in the header. 

## Can You Use Other Models?

**Yes **— you can use any model that supports either:
1. **Anthropic-compatible API** (like MiniMax)
2. **OpenAI-compatible API** (like LM Studio, Ollama, llama.cpp)

## Using Local LM Studio Models

Yes, you can use **local LM Studio models** with Claude Code. The setup is similar but uses LM Studio's OpenAI-compatible endpoint: 

### Step 1: Start LM Studio Server

1. Open LM Studio and load your model (GGUF or MLX)
2. Go to the **Local Server** tab (`<>` icon)
3. Set context size (LM Studio recommends ≥25,000 tokens; increase for better results) 
4. Click **Start Server**
5. Note the port (default: `1234`) and copy the model name exactly as shown 

### Step 2: Configure Claude Code

Set these environment variables in `~/.claude/settings.json`: 

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:1234/v1",
    "ANTHROPIC_AUTH_TOKEN": "lmstudio",
    "ANTHROPIC_MODEL": "your-model-name"
  }
}
```

Key points:
- `ANTHROPIC_BASE_URL` should be your LM Studio server address (e.g., `http://localhost:1234/v1`) 
- `ANTHROPIC_AUTH_TOKEN` can be anything (LM Studio doesn't require auth) — commonly set to `"lmstudio"` 
- `ANTHROPIC_MODEL` should match the model name exactly as shown in LM Studio 

### Step 3: Launch with the Model

From your project folder: 

```bash
cd your-project
claude --model your-model-name
```

Or just run `claude` — it will use the model from `settings.json`.

## Recommended Local Models for Coding

Search for these in LM Studio (they work well for coding): 

- **Qwen Coder** series (e.g., `qwen-2.5-32b`, `qwen-3.5`)
- **Devstral** variants
- **Gemma** models (e.g., `gemma-4-26b`) 

On Apple Silicon, MLX-based models often perform best; GGUF is more portable across Windows/Linux/PC. 

## Other Local Options

You can also use:
- **Ollama** (similar setup, different port) 
- **llama.cpp** 
- **Unsloth** (local LLM backend) 

The principle is the same: point Claude Code at your local server via `ANTHROPIC_BASE_URL`.

## Important Caveat for Local Models

Local models (LM Studio, Ollama, etc.) typically **won't support Dynamic Workflows** (the `/deep-research` system) because:
- Workflows require the JavaScript runtime and agent orchestration that Anthropic's infrastructure provides
- Local models are single-model endpoints, not multi-agent orchestration systems

So `/deep-research` may disappear or not work with local models, even though regular Claude Code commands will. 

If you want `/deep-research` to work, you need:
- **Claude Code v2.1.154+**
- A paid Claude plan (Pro/Max/Team/Enterprise) **OR** a proxy like MiniMax that advertises workflow support
- Workflows enabled in `/config`

MiniMax advertises workflow support, so `/deep-research` works there. Most local models don't, so you'd likely need to use it only with MiniMax or official Claude for the deep research workflow.

***

Want me to walk through the exact steps for your Windows 11 setup with LM Studio?

## Human

Best local models for Claude Code deep research
Does it burn thru api calls?  
How does each agent do the searching?
Since it spawns 100s of agents, what's the best way to configure internet searching?

## Assistant

Let me break down each of your questions:

## 1. Best Local Models for Claude Code Deep Research

**Short answer: Local models don't work with `/deep-research`** because the workflow requires Anthropic's JavaScript runtime and multi-agent orchestration infrastructure that local backends (LM Studio, Ollama, llama.cpp) don't provide. 

However, if you're on **MiniMax** (which advertises workflow support), here are the best options:

### For MiniMax API (with `/deep-research` working):

| Model | Why It's Good | Context Window |
|-------|-------------|----------------|
| **MiniMax-M2.7** | Fastest, cost-effective, beats Opus 4.6 on coding  | 256K+ |
| **MiniMax-M2.5** | Strongest reasoning, leads benchmarks  | 256K+ |
| **MiniMax-M3** | Newest, best for FR/EE  | 256K+ |

### For Pure Local Coding (without `/deep-research`):

| Model | Size | Best For |
|-------|------|----------|
| **Qwen2.5-Coder-32B** | 32B | Strongest open-source coding model  |
| **Devstral** | 12-30B | Code generation, good speed  |
| **Gemma-4-26B** | 26B | Good for PC/Apple Silicon  |

For local coding, you need ≥32GB VRAM for Qwen Coder 32B at good speed, or 16-24GB for 12-30B Q8 models .

***

## 2. Does It Burn Through API Calls?

**Yes — significantly.** Here's why:

### Cost Breakdown

| Component | Rate |
|-----------|------|
| **Web searches** | $10 per 1,000 searches ($0.01/search)  |
| **Token costs** | Standard Claude pricing + token usage for search results  |
| **Session runtime** | $0.08 per session-hour (billed to millisecond)  |

### Why It's Expensive

- `/deep-research` spawns **up to 1,000 agents per run** (16 concurrent) 
- Each agent does **multiple WebSearch calls** (broad initial searches → key sources → deep extraction → follow leads) 
- The workflow repeats searches across **multiple iterations** (1-3 for complex topics, 3-5 for comprehensive research) 
- Plus token costs for **processing all search results** 

For a typical deep research run, you might burn **100-500+ searches** = $1-5 just in search fees, plus significant token costs for all the results.

Average Claude Code users spend **$6/developer/day** (90% under $12/day = ~$150-250/month) . Deep research runs will spike this significantly.

***

## 3. How Does Each Agent Do the Searching?

Each agent uses Claude Code's **`WebSearch` tool** (Anthropic's server-side search, same one Claude chat uses). Here's the workflow:

### Agent Search Strategy 

1. **Broad initial searches** (`WebSearch`)
   - Agent generates search keywords from the research question
   - Issues search requests to Anthropic's `WebSearch` tool
   - Receives page titles and URLs of top search results 

2. **Identify key sources**
   - Agent evaluates which results are most credible
   - Builds a list of promising domains/pages

3. **Deep extraction as needed**
   - Uses `WebFetch` to fetch specific URLs
   - `WebFetch` validates domain against deny-list, fetches HTML, converts to Markdown 
   - Returns just the answer + minimal fetch metadata 

4. **Follow interesting leads**
   - Agent identifies gaps in understanding
   - Spawns sub-queries or spawns new sub-agents for follow-up
   - Repeats the cycle 

### What the Tool Does

```
When you add the web search tool to your API request:
1. Claude decides when to search based on the prompt
2. The API executes the searches and provides Claude with results
3. This process may repeat multiple times throughout a single request
4. At the end, Claude provides a final response with cited sources [cite:web:43]
```

The `WebSearch` tool auto-generates keywords, searches the web, reads relevant content, synthesizes answers, and **automatically includes source URLs as citations** .

***

## 4. Best Way to Configure Internet Searching (Given 100s of Agents)

Since you're using MiniMax (which advertises workflow support), here's the optimal setup:

### Option A: Use Anthropic's WebSearch (What You're Doing)

**Pros:**
- Built into the API — no external setup
- Auto-selects domains, handles caching, returns structured results 
- Supports dynamic filtering (`web_search_20260209`+) 

**Cons:**
- **$0.01/search** — expensive at scale 
- Only works with Anthropic-compatible backends (MiniMax, not local models)

### Option B: Self-Hosted SearXNG (Free Alternative)

For Claude Code with **local models** (no `/deep-research`), use SearXNG via MCP:

**Setup:** 

```bash
# Step 1: Install SearXNG (Docker)
docker pull searxng/searxng
docker run -d -p 8080:8080 --name searxng searxng/searxng

# Step 2: Verify it's working
curl "http://localhost:8080/search?q=your+query&format=json" | jq '.results[:5]'

# Step 3: Add to LM Studio MCP config
# Edit ~/.claude/mcp.json or project's mcp.json:
{
  "searxng": {
    "command": "uvx",
    "args": ["searxng-simple-mcp"],
    "env": {
      "SEARXNG_URL": "http://localhost:8080"
    }
  }
}
```

**Pros:**
- **Free** — no per-search fees
- Privacy-focused metasearch (queries dozens of engines at once) 
- Works with local models (LM Studio, Ollama, llama.cpp)

**Cons:**
- Doesn't work with `/deep-research` (needs Anthropic orchestration)
- Requires manual MCP setup
- Slower than Anthropic's built-in search

### Option C: Hybrid Setup (Best for You)

If you want `/deep-research` to work but minimize costs:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.minimax.io/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your_minimax_api_key",
    "ANTHROPIC_MODEL": "MiniMax-M2.7",
    
    // Optional: Configure domain restrictions to reduce wasted searches
    "ANTHROPIC_ALLOWED_DOMAINS": "github.com,stackoverflow.com,docs.python.org",
    "ANTHROPIC_BLOCKED_DOMAINS": "pinterest.com,instagram.com"
  }
}
```

**Key configuration tips:**
- Set `ANTHROPIC_ALLOWED_DOMAINS` to focus on credible sources — reduces wasted searches 
- Use `ANTHROPIC_BLOCKED_DOMAINS` to filter junk sites 
- Enable dynamic filtering: `web_search_20260209` or later 

### For Local Models Without `/deep-research`

If you want to use local models and still do web searching:

**Add Playwright-based WebSearch MCP to LM Studio:** 

```bash
# Install Playwright MCP
npm install playwright
npm run build

# Add to LM Studio MCP config (~/.claude/mcp.json):
{
  "websearch": {
    "command": "./websearch-mcp",
    "env": {
      // Configures browser instance for searches
    }
  }
}

# Add system prompt to tell model when to use it:
"System: You must use web search if asked a question requiring current data. Do not say you cannot access the internet."
```

***

## Bottom Line for Your Setup

Since you're using **MiniMax with `/deep-research`**:

1. **You're stuck with Anthropic-compatible WebSearch** — it's the only option that works with workflows 
2. **It will burn through API calls** — expect $1-5+ per deep research run just in search fees, plus tokens
3. **Configure domain restrictions** to reduce wasted searches: set `ANTHROPIC_ALLOWED_DOMAINS` to focus on credible sources 

If you want free web searching, you'd need to switch to **local models + SearXNG MCP**, but that means losing `/deep-research` entirely since local models don't support the JavaScript runtime/orchestration.

***

Want me to walk through the exact MiniMax cost-optimization setup for your Windows 11 system?

## Human

Are there repos or other people doing this with non-anthropic models?  What are the best practices?

## Assistant

Yes, there *are* repos and patterns for doing “deep research”-style workflows with non-Anthropic models, including fully local setups. The best practice is: **separate the research orchestration from the model provider**, then plug any LLM (Anthropic, MiniMax, LM Studio, Ollama, OpenRouter, etc.) into that orchestrator.

Below I’ll split into (1) what people are doing, and (2) best practices you’d care about as an architect.

***

## 1. What People Are Doing with Non‑Anthropic Models

### a) Local Deep Research via MCP / Gateways

Several community projects expose a **“deep research” MCP server or gateway** that Claude Code (or Claude Desktop) can call, while the *actual* LLM is local or non‑Anthropic:

- **LearningCircuit/local-deep-research**: MCP server that lets Claude Desktop/Claude Code perform deep research using **any LLM backend** (GLM, Qwen, Gemma, etc.) and tools like SearXNG + MarkItDown.[1]
- You run this MCP server, register it in Claude Code’s MCP config, and the server handles:
  - Iterative search loops
  - Source fetching and Markdown conversion
  - Multi-step research workflow orchestration[2][1]
- People commonly pair it with **GLM‑4.7‑flash, Qwen3 30B, Gemma 3 12B** via LM Studio or Ollama.[2]

There are also video walkthroughs showing **Claude Code + LM Studio/Ollama + local workflow** that spawns hundreds of agents locally “for $0” (tokens free, only your GPU).[3]

### b) Open‑Source Deep Research Frameworks

There are several general frameworks that implement the pattern independent of Claude:

- **gpt‑researcher** and **Open Deep‑Research**: Python/TypeScript frameworks that:
  - Take a question
  - Run iterative search + fetch + summarization loops
  - Maintain a local knowledge store
  - Let you plug in OpenAI‑compatible or local models.[4][5][2]
- These are often wired to:
  - **SearXNG** for search
  - **Firecrawl / MarkItDown** for page → Markdown conversion
  - Any OpenAI‑compatible LLM (OpenRouter, LM Studio, Ollama, etc.)[6]

You can invoke them from Claude Code as external tools (via MCP or via a local CLI that writes results into your repo).

### c) Claude‑Style Deep Research with Other Models

Patterns from Anthropic’s own deep research tooling are being reimplemented for other LLMs:

- Anthropic describes research agents using **WebSearch + WebFetch** tools to:
  - Run broad searches
  - Identify key sources
  - Fetch and convert pages to Markdown
  - Synthesize and cite results in a structured report.[7][8][9][10][11]
- Open‑source projects and blog posts adapt these patterns to:
  - **OpenAI deep research**
  - Local GLM/Qwen/Gemma models
  - Custom agents built on LangChain/LlamaIndex/Parallel Ultra.[12][4]

In short: people are **copying the orchestration pattern**, not the Claude‑specific implementation.

***

## 2. Best Practices for Deep Research with Non‑Anthropic Models

Here’s a distilled set of patterns you can reuse with Claude Code, LM Studio, Ollama, MiniMax, etc.

### a) Separate Orchestrator from LLM Backend

Best practice is to **decouple**:

- The *research workflow* (agents, steps, knowledge store)
- The *LLM provider* (Anthropic, OpenAI, MiniMax, local model)

Use one of these patterns:

- A dedicated **research service** (MCP server or HTTP service) that:
  - Exposes a single “/deep_research” or “research” tool
  - Internally decides which LLM to call, how many sub‑agents to spawn, and how to do search/fetch.
  - Lets Claude Code just say: “Invoke tool `deep_research` with {question}”.
- A **local CLI** (like `local-deep-research`) that:
  - Writes results into your repo as Markdown
  - Claude Code reads the files and continues work.[13][1]

This gives you model‑agnostic orchestration, and you can swap backends (MiniMax, LM Studio, Ollama) without changing the workflow.

### b) Use Metasearch + Fetch Tools (SearXNG + MarkItDown / Firecrawl)

Community setups that work well generally share this stack:[14][15][16][2]

- **Search layer**: SearXNG (self‑hosted metasearch), via:
  - Direct HTTP API (`/search?q=...&format=json`)
  - MCP adapter like `SearxngMCP` / `searxng-simple-mcp`.[17][18][14]
- **Fetch/convert layer**:
  - **MarkItDown** or **Firecrawl** to turn HTML into Markdown/JSON that LLMs can digest.[6][2]
- **LLM layer**:
  - Any OpenAI‑compatible endpoint (LM Studio, Ollama, Gemini‑compatible backends, MiniMax, GLM, etc.).[19][20]

This mimics Anthropic’s **WebSearch + WebFetch** pattern without relying on their proprietary tools.[8][21][7]

### c) Agent Workflow Pattern (for You as an Architect)

Strong repos and guides converge on a similar multi‑step workflow:[22][23][9][10][13]

1. **Planning agent**
   - Breaks the research question into 3–10 sub‑questions.
   - Defines constraints (time, depth, domains, allowed languages).

2. **Search agents (parallel)**
   - For each sub‑question:
     - Generate 3–5 search queries.
     - Call SearXNG with JSON output.
     - Score results (title, snippet, domain reputation).

3. **Fetch agents**
   - For top N results per sub‑question:
     - Call MarkItDown/Firecrawl to fetch/convert pages.
     - Extract relevant sections, discard noise.

4. **Synthesis agents**
   - Summarize each sub‑question.
   - Identify contradictions and knowledge gaps.
   - Propose follow‑up queries.

5. **Adversarial/verification agents**
   - Try to refute the synthesized claims.
   - Check citations, look for more authoritative primary sources (docs, specs, laws).[10][22]

6. **Final reporting agent**
   - Produces a structured, cited report:
     - Sections, tables, assumptions, confidence levels.
     - Stores in Markdown so Claude Code can read/extend it.[23][22][10]

You can implement this orchestrator in Python/TypeScript and surface it as a single tool to Claude Code.

### d) Cost and Resource Best Practices

For **non‑Anthropic backends**, the bottleneck is usually **GPU / CPU**, not per‑search cost. Community guidance:[20][24][25][2]

- Use **smaller, fast local models** for:
  - Search query generation
  - Snippet scoring
  - Simple summarization
- Reserve your **strongest model** (Qwen Coder 32B, GLM 4.7, Gemma 26B) for:
  - Synthesis
  - Adversarial checking
  - Final reporting

Typical patterns:

- “Fast model” (e.g., GLM‑4.7‑flash) for high‑fan‑out tasks (search, snippet summarization).[19][2]
- “Slow model” (e.g., Qwen2.5‑Coder‑32B, Gemma‑4‑26B) for deep synthesis.[26][27]

This matches Anthropic’s own pattern (Sonnet vs Haiku / Fable vs Haiku).[28][29]

### e) Integrating with Claude Code

Best practice from recent guides on **Claude Code + local models**:[30][3][20][19]

- Put model routing in `~/.claude/settings.json` and per‑project `.env`.
- Register your research orchestrator as:
  - An MCP server in `.claude/mcp.json`, or
  - A CLI tool Claude can call (`/tools` or custom command).
- Use a **CLAUDE.md** that explains:
  - The research workflow
  - The tools available (SearXNG, fetcher, research orchestrator)
  - How to call them.[22][23]

This pattern is what Anthropic itself uses for long‑running, multi‑agent scientific workflows.[31][22]

***

## 3. Concrete Best-Practice Checklist (Given Your Use Case)

For “deep research with non‑Anthropic models” in a Claude Code‑centric, local‑friendly stack:

- **Orchestrator**
  - Write a small Python/TS service that owns the workflow (planning, search, fetch, synthesis, verification).
  - Expose a single `deep_research(question, constraints)` tool.

- **Search**
  - Self‑host **SearXNG** (Docker) and query via JSON API.
  - Restrict engines and domains to keep results clean (docs, specs, reputable sources).[15][16][14]

- **Fetch**
  - Use **MarkItDown** or **Firecrawl** for HTML→Markdown.
  - Cache per‑URL to avoid refetching.[2][6]

- **Models**
  - Fast model for search/snippet work (GLM‑4.7‑flash, Qwen3‑Coder smaller variants).
  - Strong model for synthesis/adversarial steps (Qwen2.5‑Coder‑32B, Gemma‑4‑26B).[27][26][2]

- **Claude Code integration**
  - Register orchestrator as MCP or CLI tool.
  - Document the pattern in CLAUDE.md and teach Claude how/when to call it.[23][22]

This gives you most of what `/deep-research` offers, but entirely model‑agnostic and compatible with your local stack.

***

If you tell me whether you prefer Python or TypeScript for the orchestrator, I can sketch a concrete “minimal deep research workflow” structure you could drop into your homelab.

## Human

Comparing Open Deep-Research vs gpt-researcher workflows
Best practices for managing local token usage in research agents

## Assistant

Here’s a concise comparison, then a set of concrete best practices you can apply to your own research agents (Claude Code, local, MiniMax, etc.).

***

## 1. Open Deep‑Research vs gpt‑researcher Workflows

### Core Design Philosophy

- **gpt‑researcher**
  - Designed as an *autonomous long‑form research agent* that runs a recursive deep‑research loop.[1][2]
  - Explicitly aims for **2000+ word** structured reports with headings and section break‑downs.[3]
  - Originally OpenAI‑centric, but now supports multiple LLMs and can run “Deep Research” mode as an advanced workflow.[4][1]

- **Open Deep Research (Together AI / LangChain “open_deep_research” ecosystem)**
  - A more **generic agent workflow** that mirrors commercial deep research offerings (OpenAI Deep Research, Gemini Deep Research).[5][6][3]
  - Emphasizes **plan‑and‑execute**, with optional human‑in‑the‑loop to approve or edit the plan before the heavy search/synthesis phase.[7][5]

### Autonomy vs Human‑in‑Loop

| Aspect               | gpt‑researcher                                    | Open Deep Research / open_deep_research                             |
|----------------------|---------------------------------------------------|----------------------------------------------------------------------|
| Autonomy             | Mostly one‑shot autonomous loop until completion  | Often plan‑and‑execute with optional plan review/approval            |
| Plan review          | Plan is internal; user typically sees only final report | Plan can be exposed; user can edit sections before execution [5][7] |
| Interactivity        | Minimal mid‑run input                             | Supports semi‑autonomous workflows with human feedback               |

Open‑source analyses note that frameworks labeled **“Open Deep Researcher” / “open_deep_research”** tend to adopt a Gemini‑style “plan approval” phase, whereas gpt‑researcher’s Deep Research mode behaves closer to OpenAI’s fully autonomous Deep Research.[3][5][7]

### Workflow Structure

**gpt‑researcher typical flow:**[2][1][4]

1. **Planner agent** breaks the query into sub‑questions.
2. **Researcher agents** run targeted web queries (e.g., via SerpAPI, Tavily) for each sub‑question.[5][2]
3. **Document loader** optionally pulls local docs (PDF, Markdown, CSV, Word, etc.) via `DOC_PATH`.[1]
4. **Publisher module** synthesizes everything into a final report (long‑form, multi‑section).[4][2]
5. Optional **Deep Research mode** repeats search/synthesis iteratively for more depth.[1][4]

**Open Deep Research / open_deep_research flow:**[6][7][5]

1. **Planning phase**:
   - Agent proposes an outline (sections/subtopics).
   - User can approve or edit the plan (optional human‑in‑loop).[7][5]
2. **Execution phase**:
   - For each section, the agent runs search + fetch + summarization loops (using SerpAPI/Tavily or similar).[6][5]
3. **Iteration phase**:
   - Advanced implementations re‑plan based on findings, do multi‑hop reasoning, and refine the report.[2][6]
4. **Final report**:
   - Delivers a structured, cited long‑form document similar to commercial deep‑research agents.[8][6]

**Key practical differences:**

- **Control:** Open Deep Research’s plan‑approval stage reduces wasted work and mis‑aligned focus; gpt‑researcher is more “fire and forget.”[3][5]
- **Integration:** gpt‑researcher ships a ready‑to‑use app, including local document research; Open Deep Research is often shipped as a library or workflow within broader stacks (LangChain, Together AI, etc.).[6][3][1]
- **Token behavior:** gpt‑researcher defaults toward long outputs; Open Deep Research often exposes explicit knobs for section count, depth, and reasoning iterations.[4][3][6]

***

## 2. Best Practices for Managing *Local* Token Usage in Research Agents

Assuming you’re running this in a Claude Code + local/heterogeneous backends environment, the best practices from production agent teams and open‑source projects boil down to:

### a) Tiered Model Selection (Fast vs Strong)

Use **different models for different phases**:[9][10][11]

- **Fast, small model** (e.g., GLM‑4.7‑flash, Qwen3‑Coder‑small):
  - Planning, search query generation
  - Snippet filtering and scoring
  - Lightweight summaries of individual pages
- **Strong, larger model** (e.g., Qwen2.5‑Coder‑32B, Gemma‑26B):
  - Multi‑source synthesis
  - Adversarial verification
  - Final report generation

Teams running multi‑agent workflows report substantial cost reductions by routing *routine* tasks (classification, extraction, snippet summarization) to cheaper models, and reserving premium models for complex reasoning.[10][11][9]

**Design pattern for you:**

- In the orchestrator, define `fast_llm` and `strong_llm` clients.
- Agents are tagged with “budget” and “task type”; router sends them to the appropriate backend.

### b) Agent Roles with Narrow Context

A Reddit case study on an “agentic retrieval protocol” achieved **~60% reduction in token usage** by splitting agents into roles and strictly limiting each agent’s context:[9]

- **Extractor**:
  - Reads raw documents/pages.
  - Outputs structured snippets (key facts, citations) in a compact format.
- **Analyzer**:
  - Reads only the extractor’s snippets.
  - Identifies patterns, contradictions, gaps.
- **Answerer**:
  - Reads analyzer output and a subset of snippets.
  - Produces the final answer/report.

Key insights:

- Don’t share full context with every agent; *route only relevant slices*.
- Give agents a clear schema for documents and snippets, so they can navigate efficiently.[12][9]

For local use, this translates to:

- keep raw HTML/Markdown in disk/db,
- provide agents with **IDs + short summaries**, not full text,
- fetch full text only when truly needed.

### c) Prompt and System‑Context Minimization

Token optimization guidance from multiple sources:[13][14][10][12]

- **Trim system prompts**:
  - Avoid long philosophical instructions; use concise, task‑specific guidance.
  - Prefer structured formats (JSON, bullet lists) over verbose prose.
- **Avoid repeated boilerplate**:
  - Don’t restate big instructions every call; cache system prompts or keep them in separate config.
  - Use environment‑level instructions once, then reference them briefly.

This is especially important for recursive research loops: a verbose system prompt repeated across 200+ calls is a major cost driver.

### d) Subagent Budget Limits and Timeouts

Production agent platforms use **hard budgets per subagent** to prevent runaway recursion:[10]

- Per‑agent `max_tokens` (output) and `max_input_tokens` (context size).
- Per‑agent `runTimeoutSeconds` for long‑running tasks.
- Per‑run caps:
  - Maximum recursion depth.
  - Maximum number of subagents spawned per root query.

For local stacks, you can mimic this by:

- Enforcing `max_tokens` at the client wrapper level (LM Studio/Ollama/OpenRouter calls).
- Tracking aggregate token usage and aborting if a run exceeds a configured budget.
- Logging per‑agent token usage for post‑hoc analysis.

### e) Output Minimization and Summarization Layers

You don’t need full‑text everything in the agent’s context:[13][9][10]

- **Summarize tool outputs before passing to the next agent**:
  - Example: weather API → “Sunny, 75°F, 10% chance of rain” instead of full JSON.[13]
  - For web pages: store full HTML/Markdown, but pass only key bullet points + citations into the agent.
- Use **phase‑based workflows**:
  - Research phase: produce compressed notes, lists of facts, and references.
  - Planning phase: operate over the compressed notes.
  - Implementation/report phase: pull only the necessary notes into context.[12]

This matches the multi‑phase pattern described for agentic systems: research → plan → implement, with new context windows between phases to avoid carrying full history.[9][12]

### f) Monitoring and Budgeting

To keep your homelab or local stack under control:[15][10][13]

- Track token use per:
  - Agent type (searcher, summarizer, synthesizer),
  - Backend (local vs remote),
  - Research session.
- Set **explicit quotas**:
  - “No more than N tokens for planning, M tokens for search, K tokens for final report.”
- Use **adaptive summarization**:
  - When the context gets large, auto‑summarize prior turns and documents, keep only high‑value facts.

For local GPUs, this is about latency and VRAM rather than dollar cost, but the patterns are identical.

***

## 3. Putting This into Your Claude Code / Local Stack

Given your role and preferences, a pragmatic architecture could be:

- A **Python orchestrator** that:
  - Implements both “gpt‑researcher‑style” autonomous deep research and “Open Deep Research‑style” plan‑and‑execute, selecting based on a flag.
  - Uses:
    - SearXNG for search,
    - MarkItDown/Firecrawl for fetch+convert,
    - LM Studio / MiniMax / other backends via OpenAI‑compatible clients.
- Claude Code integration:
  - Expose a single `deep_research` tool via MCP.
  - Let Claude Code call it; orchestrator returns the report and a compact “notes” file for further coding.

Token‑management best practices from above become:

- Tiered model routing in the orchestrator.
- Role‑based agents with narrow context windows.
- Strict per‑agent budgets.
- Summarization at phase boundaries.
- Logging and dashboards (even simple CSV + Grafana) for visibility.

If you’d like, I can outline a concrete agent graph (nodes, edges, and budgets) that marries the best parts of gpt‑researcher and Open Deep Research, tuned for a Claude Code + LM Studio setup.

## Human

Yes, show me an agent graph example for local setups
I want to see a node and edge structure for this workflow

## Assistant

Yes — for a local setup, the cleanest mental model is a **stateful directed graph**: nodes do one narrow job, edges decide what runs next, and a shared state object carries the evolving research context across the workflow. LangGraph’s model maps well here because nodes are computation steps, edges define flow, and conditional edges let you branch or loop when coverage is insufficient.[1][2][3]
## Node structure
A strong local research graph usually separates planning, retrieval, extraction, synthesis, and quality control rather than giving one giant agent the whole job. That matches the common deep-research pattern described across research-agent examples: plan sub-questions, search multiple sources, extract and rank, synthesize, then loop if gaps remain.[4][5][6]

**Example nodes**

- `intake`: Normalize the user question, constraints, time horizon, and output format.[3]
- `planner`: Break the task into sub-questions and search intents.[5][4]
- `query_builder`: Generate focused search queries for each sub-question.[5]
- `search_fanout`: Dispatch parallel searches to SearXNG, Tavily, internal docs, or repo search. Parallel fan-out is a natural graph pattern with multiple outgoing edges from one node.[7][4]
- `result_ranker`: Deduplicate, score relevance, and pick top candidates.[6][5]
- `fetch_extract`: Fetch pages or local files and convert them to compact notes/snippets.[3][6]
- `evidence_store`: Persist normalized evidence objects into shared state, not raw full text everywhere. Shared state is the central “whiteboard” pattern in LangGraph-style systems.[8][3]
- `synthesizer`: Build section-level findings from evidence.[4][5]
- `verifier`: Check contradictions, missing citations, and low-confidence claims.[6]
- `gap_router`: Decide whether to loop back for more research or proceed to report generation; conditional edges are the standard way to express this.[1][2]
- `reporter`: Produce the final structured answer/report with citations.[8][4]
## Edge structure
The edge logic should be mostly linear early on, then conditional later once enough evidence exists to judge quality. A typical research pipeline in LangGraph examples is plan → research fan-out → synthesize → quality-check → loop if needed.[4][5]

```text
START
  -> intake
  -> planner
  -> query_builder
  -> search_fanout
  -> result_ranker
  -> fetch_extract
  -> evidence_store
  -> synthesizer
  -> verifier
  -> gap_router

gap_router -- sufficient_coverage --> reporter --> END
gap_router -- missing_topics ------> query_builder
gap_router -- low_source_quality --> search_fanout
gap_router -- citation_gaps ------> fetch_extract
```

That structure keeps your loops targeted: if the issue is weak sources, go back to search; if the issue is missing detail from already-found sources, go back to fetch/extract; if the issue is uncovered subtopics, regenerate queries. That is usually better than restarting the whole workflow.[1][8][5]
## Parallel subgraph
For local setups, the most useful optimization is to make the middle of the graph a **map stage** over subtopics, then reduce back into shared evidence. LangGraph guidance and examples show parallel research fan-out as one node sending work to many topic-specific paths, then merging before synthesis.[4][7]

```text
planner
  -> topic_1_query -> topic_1_search -> topic_1_extract --
  -> topic_2_query -> topic_2_search -> topic_2_extract --+-> merge_evidence -> synthesizer
  -> topic_3_query -> topic_3_search -> topic_3_extract --
```

This is the right place to use small local models: query generation, snippet triage, and extraction are usually cheaper than synthesis, so they can run on a fast model while `synthesizer` and `verifier` use your stronger model. That division aligns with broader best practice for multi-agent research systems.[6][4]
## Shared state
The graph works best when every node reads and writes a typed shared state instead of passing huge transcripts around. LangGraph examples emphasize a central state object that each node updates with only the fields it owns.[8][3]

A practical local state shape looks like this:

```ts
type ResearchState = {
  question: string
  constraints: {
    maxIterations: number
    maxSourcesPerTopic: number
    budgetTokens: number
    allowedDomains?: string[]
  }
  topics: Array<{
    id: string
    question: string
    status: "pending" | "searched" | "extracted" | "done"
  }>
  queries: Array<{
    topicId: string
    query: string
  }>
  searchResults: Array<{
    topicId: string
    title: string
    url: string
    score: number
  }>
  evidence: Array<{
    topicId: string
    sourceUrl: string
    claim: string
    snippet: string
    confidence: number
  }>
  findings: Array<{
    topicId: string
    summary: string
    openQuestions: string[]
  }>
  quality: {
    sufficientCoverage: boolean
    citationGaps: boolean
    weakTopics: string[]
  }
  report?: string
}
```

The key best practice is that `evidence` stores compact claims/snippets with provenance, while raw documents stay on disk or in a cache. This reduces local token burn and keeps the graph stable as it loops. That same “shared state plus targeted updates” idea is central to graph-based agent workflows.[3][5][8]
## Local-first variant
If you want this tuned for LM Studio/Ollama plus SearXNG, I’d split execution into two tiers. Use a small fast model for `planner`, `query_builder`, `result_ranker`, and first-pass `fetch_extract`; use the strongest available local model for `synthesizer`, `verifier`, and `reporter`. This follows the common research-agent pattern of cheap fan-out plus expensive final reasoning, and it is usually the best tradeoff for local VRAM and latency.[4][5][6]

A concrete routing policy:

- Fast model: planning, search query generation, dedupe, snippet compression.
- Strong model: contradiction analysis, section synthesis, final report.
- Deterministic code: URL dedupe, domain filtering, score thresholds, loop counters.
- Hard guards: max iterations, max sources per topic, max tokens per node.

Would you like the next step as a **LangGraph Python skeleton** or a **TypeScript pseudo-implementation** of this exact graph?
