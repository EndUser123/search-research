---
title: "I'm using the PI agent harness on Windows 11.  Are there repos or plugins or extensions that can do deep research?  Can "
date: "2026-06-25"
mode: "COPILOT"
uuid: "88d82798-d9f2-496e-afa2-ebb316193516"
entry_count: 9
---

## Human

I'm using the PI agent harness on Windows 11.  Are there repos or plugins or extensions that can do deep research?  Can they compete with ChatGPT, Claude, or Perplexity?

## Assistant

I now have enough comprehensive data. Let me write the answer.

## Pi Agent Deep Research: Packages, Capabilities & Honest Comparison

The Pi agent harness has a **growing, real ecosystem of deep research extensions** — but how they compare to ChatGPT Deep Research, Claude, or Perplexity depends heavily on which package you pick and what model you route through it.

***

## The Pi Package Landscape for Research

Pi's extension model is intentionally minimal (4 built-in tools: read/write/edit/bash), so all research capability comes from packages you install. The official package catalog at `pi.dev/packages` lists several research-focused options as of June 2026:[1][2]

### Tier 1 — Full Deep Research Workflows

**`@quintinshaw/pi-dynamic-workflows`** (18K downloads/month, v2.8.0)[3]
This is the most capable and widely used option. One install adds `/deep-research`, `/adversarial-review`, and a full subagent orchestration engine:[3]
- Fans out research tasks across **up to 16 concurrent subagents** in parallel
- Bundles **real web search, source cross-checking, and cited reports**
- **Real model routing**: small/medium/big tier dispatch so cheap lookups use cheap models and synthesis uses a bigger one
- **Journaled resume** — interrupted runs replay finished agents from state; no re-burn of tokens
- Git worktree isolation per subagent (parallel agents can touch the same files without clobbering)
- Interactive `/workflows` TUI for live monitoring, pause/restart, and cost accounting
- The `/adversarial-review` command vets findings through skeptical reviewer subagents

```bash
pi install npm:@quintinshaw/pi-dynamic-workflows
/reload
/deep-research "What are the leading approaches to LLM context compression in 2026?"
```

**`@forecastx/deep-research`** (v0.1.1, lower download count — newer/niche)[4]
Simpler but purpose-built, exposing two callable tools:
- `deep_research(query)` — 5+ web searches, structured markdown output, 1–3 min
- `super_deep_research(query)` — multi-phase with planning, 8–15 searches, 3,000–8,000 char report, 2–5 min
- Spawns a Pi subprocess per research run; all steps streamed live; reports saved to `~/.forecastx-reports/<id>/`
- Lets you override the research model per-run via `RESEARCH_MODEL` env var (e.g., `claude-sonnet-4`, `gpt-4o`, `deepseek-chat`)[4]

**`@firstpick/pi-skill-deep-research`**[5]
Deterministic two-phase research with schema/policy validation — designed for high-stakes, fact-checked queries requiring multi-source evidence. More rigidly structured than the others; closer to an epistemic gating pattern than a free-form research loop.

### Tier 2 — Search Infrastructure (Required by Tier 1)

**`pi-web-access`** (113K downloads/month, v0.12.0, updated June 24 2026)[6]
The de-facto search backbone for the ecosystem. Key capabilities:
- Zero-config start: Exa MCP search with no API key required[6]
- Provider fallback chain: OpenAI → Exa → Brave → Parallel → Tavily → Perplexity → Gemini API → Gemini Web[6]
- GitHub URLs cloned locally (real file contents, not scraped HTML)
- YouTube/local video understanding via Gemini (transcripts, visual descriptions, frame extraction)
- PDF extraction, JS-heavy page bypass via Jina Reader fallback
- Configures cleanly via `~/.pi/web-search.json`; providers keyed individually[6]

You can route `web_search` to Perplexity API, Tavily, or Exa depending on query type — recency filters, domain whitelists, and batch query support are all available.[6]

### NVIDIA AI-Q — Enterprise-Grade Option

If you need enterprise data sources (internal docs, regulated-industry data) rather than the open web, NVIDIA's **AI-Q Blueprint** is available as an open-source skill installable into Pi:[7]
- Four-stage pipeline: intent classifier → human-in-loop clarifier → shallow researcher → deep researcher
- Exposes the whole pipeline as a single skill via `SKILL.md` at `.agents/skills/aiq-research/`[7]
- Keeps sensitive data local; designed for healthcare, finance, government use cases
- Self-hostable Docker Compose or Helm deployment[7]

***

## Honest Competitive Assessment

This is where you need to separate **architecture capability** from **benchmark performance**. Current benchmarks paint a specific picture:

### Benchmark Reality (DeepResearch Bench, June 2026)

The DeepResearch Bench evaluated deep research agents across 100 PhD-level tasks in 22 fields:[8]

| System | Overall Score (RACE) | Citation Accuracy | Avg. Effective Citations |
|---|---|---|---|
| Gemini-2.5-Pro Deep Research | **48.88** | 81.4% | **111.21** |
| OpenAI Deep Research | 46.98 | — | ~49 |
| Perplexity Deep Research | 42.25 | **90.24%** | — |
| Grok Deeper Search | 40.24 | 83.6% | — |
| Claude-3.5-Sonnet w/Search | 28.48 | **94.04%** | — |

Perplexity also released its own **DRACO Benchmark** (June 2026) showing state-of-the-art performance on factual accuracy, breadth/depth, and citation quality — with the lowest latency of tested systems at 459 seconds vs. 592–1,808 seconds for competitors. Onyx (open-source, self-hostable) is reportedly ranked #1 on **DeepResearch Bench** by one analysis, ahead of OpenAI Deep Research  — though this appears to be a different evaluation run, so treat as SPECULATIVE without independent verification.[9][10]

### Where Pi-Based Research Stands

**FACT:** Pi's deep research packages are architecturally competitive — parallel subagents, adversarial review, real model routing, and web search. This is not toy capability.[3]

**FACT:** Their actual output quality is almost entirely determined by the **model you route through Pi** and the **search provider you configure**. Pi using Claude Sonnet 4 + Perplexity API search can produce research comparable to Perplexity Pro. Pi using a weak local model via Ollama will not.[11]

**CONSENSUS:** The dedicated closed platforms (ChatGPT Deep Research, Perplexity, Gemini) still have structural advantages — they have fine-tuned their models and pipelines specifically for research tasks, their citations have been validated at scale, and they have tighter feedback loops. Pi gives you more **control and composability**, not better out-of-box research quality.[12][13]

**PRACTICAL CEILING:** Perplexity is fastest and most citation-accurate for discovery; ChatGPT Deep Research produces the most polished synthesis reports; Gemini 2.5 Pro leads on raw benchmark scores. A Pi workflow using strong models can match or exceed individual dimensions but is unlikely to consistently beat the specialized platforms across all dimensions.[13]

***

## Recommended Setup for Windows 11

Given your background in multi-model routing and Bifrost:

```bash
# Core install
pi install npm:pi-web-access
pi install npm:@quintinshaw/pi-dynamic-workflows

# Configure providers in ~/.pi/web-search.json
{
  "exaApiKey": "exa-...",         # zero-config fallback even without this
  "perplexityApiKey": "pplx-...", # best citation quality  
  "tavilyApiKey": "tvly-...",     # best for RAG-style structured retrieval
  "provider": "auto"
}

# Then in Pi:
/deep-research "your question here"
# or trigger via keyword: just say "workflow" or "workflows" in a message
```

For **model routing**, `@quintinshaw/pi-dynamic-workflows` lets you configure `/workflows-models` to map small/medium/big tiers to your available models — so synthesis-phase agents can use Claude Opus 4 or GPT-5 while scan-phase agents use a cheaper model. This is where Pi genuinely exceeds the closed platforms: **you own the routing logic**.[3]

The `/adversarial-review` command is worth using for high-stakes research — it runs a separate reviewer subagent that challenges the primary findings, which aligns with your epistemic gating interests.[3]

***

## Bottom Line

Pi's deep research ecosystem is **real and usable**, not experimental. `@quintinshaw/pi-dynamic-workflows` with `pi-web-access` and a strong backend model (Claude Sonnet 4 or GPT-4o via Bifrost) will get you research quality close to Perplexity Pro on many queries — with full local control, no data leaving your infrastructure, and composable routing you can customize. The gap versus the specialized platforms is real but narrowing, and for your use case (local, controlled, agentic) the tradeoff is often worth it.[11][13][3]

## Human

Are there repos for using Googles NotebookLM as a deep research or even simply for research in PI?  Can it integrate with any of the options above?

## Assistant

Short answer: there isn’t a first‑class, official “NotebookLM for Pi” package yet, but there *are* usable building blocks. You can wire NotebookLM into Pi via an unofficial Python API or an MCP server, and then call it from Pi’s deep‑research workflows with a bit of glue code.

***

## What Exists Today Around NotebookLM

### 1. Unofficial Python API / Skill Library

The main building block is `notebooklm-py`, an unofficial Python library and CLI for automating Google NotebookLM:[1][2]

- Fully async Python library plus CLI for **bulk importing sources** (URLs, PDFs, YouTube, Google Drive) into notebooks.  
- Supports **chat / RAG** over a notebook with citations, plus generation of study guides, flashcards, mind maps, and “research mode” that does web+Drive search and auto‑imports findings.[2]
- Explicitly designed to integrate with **AI agents like Claude Code, Codex, and others** via an “agent skill” abstraction.[1]

FACT: This gives you a programmable surface over NotebookLM’s capabilities, even though Google does not expose an official API yet.[3][2]
SPECULATION (high confidence): Because it is reverse‑engineered, there is a non‑zero risk of breakage if Google changes the internal RPC protocol, so you should treat it as “best‑effort,” not hard infrastructure.

### 2. NotebookLM MCP Server

There is also a **NotebookLM MCP server** that exposes notebooks to any MCP‑compatible client:[4]

- Written in TypeScript, deployed via `npx notebooklm-mcp-server start`.[4]
- Lets agents **read, search, and manage your notebooks as tools**, essentially treating NotebookLM as a remote, structured knowledge base.[4]
- First‑class integrations right now are shown for Claude Desktop, VS Code via Cline/MCP, Antigravity, Gemini CLI, and Claude Code skills.[4]

FACT: Pi intentionally does *not* implement MCP in the core harness — it keeps a minimal tool interface (read/edit/write/bash) and leaves protocols like MCP to extensions. So you cannot just drop an MCP server in and have Pi pick it up automatically.[5]

***

## What Does *Not* Exist (Yet)

From current docs and the Pi package catalog:

- No package named `pi-notebooklm`, `@something/notebooklm`, or similar shows up in the **Pi package index** or on the main `pi` repo as an official skill.[6][7]
- The headline deep‑research packages (`@quintinshaw/pi-dynamic-workflows`, `@forecastx/deep-research`, `@firstpick/pi-skill-deep-research`, `pi-web-access`) all talk about search providers like Exa, Perplexity, Tavily, Brave, Parallel, Gemini, but **none list NotebookLM as a provider**.[8][9][10]

So: there is **no plug‑and‑play, documented Pi skill that wraps NotebookLM** today. Integration is possible, but you’ll be doing the wiring yourself.

***

## Integration Options With Pi’s Research Stack

Given what you already have (Pi + `pi-web-access` + deep research workflows), you essentially have two sensible patterns.

### Option A: Treat NotebookLM as an External Research Engine

Use NotebookLM as a **sidecar research environment** that Pi can call via scripts, then pull structured results back into your Pi deep‑research report.

Concrete wiring on Windows 11:

1. **Install the NotebookLM Python library/CLI** globally or in a venv:

   ```bash
   pip install notebooklm-py
   ```

   This gives you:
   - `notebooklm` CLI for importing sources, running research, and exporting summaries.  
   - A Python API you can call from scripts.[2][1]

2. **Expose it to Pi via `bash` tools**:

   Pi already has a `bash` tool; the deep‑research packages can call shell commands. You can write a thin wrapper script like:

   ```bash
   # notebooklm_research.sh
   notebooklm research \
     --notebook-id "$NOTEBOOK_ID" \
     --query "$1" \
     --format json
   ```

   Then call it from Pi deep‑research workflows as a step (e.g., a “specialist agent” that runs NotebookLM and feeds the JSON back for synthesis).

3. **Integrate into `@quintinshaw/pi-dynamic-workflows`**:

   - Define a **custom workflow step** that runs the shell script and returns structured JSON.  
   - Use that step as a *source‑of‑truth subagent* in parallel with the usual web search (Exa / Perplexity / Tavily via `pi-web-access`).[10][8]
   - In the synthesis phase, the “big model” agent reconciles NotebookLM summaries + web sources into the final report.

How it competes:

- For **closed‑corpus research** (e.g., your own PDFs/Drive docs), NotebookLM will be stronger than generic web search: near‑zero hallucination on those docs and better notebook‑level coherence.[3]
- For **open‑web discovery**, you still depend on `pi-web-access` + your configured search providers for breadth and recency. NotebookLM then acts as a curator and summarizer on top of what you import.[10]

### Option B: Implement a Pi Skill Around the Python API

If you want first‑class “NotebookLM” tools inside Pi (so they show up like any other tool, with JSON schemas), you can wrap `notebooklm-py` as a Pi skill:

1. **Create a Pi skill repo** (e.g., `pi-skill-notebooklm`) following the examples in `pi-skills`.[11]

2. Implement tools like:

   - `notebooklm_import_sources(sources: string[]) -> { notebook_id }`  
   - `notebooklm_query(notebook_id: string, query: string) -> { answer, citations[] }`  
   - `notebooklm_briefing(notebook_id: string, topic: string) -> { outline, summary }`

   Each tool calls into the Python library using Node’s `child_process` (or you write the skill in TypeScript and have it talk HTTP to a local notebooklm-py microservice).

3. **Install as a user skill**:

   ```bash
   git clone https://github.com/you/pi-skill-notebooklm ~/.pi/agent/skills/pi-skill-notebooklm
   ```

   Pi will autodiscover tools from `SKILL.md` / `skill.json` per its skill conventions.[11]

4. **Use in deep‑research workflows**:

   - `@forecastx/deep-research` and `@firstpick/pi-skill-deep-research` are designed to call arbitrary tools as part of their multi‑step loops.[9][12]
   - You can configure them to:  
     - First, import your source set into a NotebookLM notebook.  
     - Then, run NotebookLM queries as one of the evidence‑gathering phases.  
     - Finally, synthesize with your usual big model.

This is a bit more work upfront but gives you **reusable tools** and keeps everything inside Pi instead of via ad‑hoc shell calls.

***

## Can NotebookLM Integrate With the Packages You Mentioned?

Let’s go through them explicitly:

- **`pi-web-access`**: This is a web search provider router for engines like Exa, Perplexity, Tavily, Gemini Web, Brave, etc. It does not currently list NotebookLM as a provider, and NotebookLM is not a generic web search engine; it’s a notebook‑centric RAG product.[3][10]
  → Integration path is *indirect*: use `pi-web-access` to discover sources, then feed those sources into NotebookLM via notebooklm‑py.

- **`@quintinshaw/pi-dynamic-workflows`**: Built for exactly this kind of composability. It supports custom subagents and shell/tool invocations as steps.[8]
  → Yes, it can integrate — you add a NotebookLM step as a subagent and then use `/deep-research` or `/workflows` to orchestrate around it.

- **`@forecastx/deep-research`**: The package focuses on a general deep‑research pipeline (planning + web search + synthesis) and doesn’t mention NotebookLM, but its design (Pi subprocess + streaming) doesn’t prevent additional tools.[9]
  → Practically, you’d either fork it or wrap it with your own script that also calls NotebookLM.

- **`@firstpick/pi-skill-deep-research`**: This one is about deterministic schemas and adversarial validation; it is *compatible* with additional tools but doesn’t ship NotebookLM hooks itself.[12]
  → Again, custom integration rather than built‑in support.

So the answer is:

- There is **no out‑of‑the‑box “NotebookLM backend” option** for these packages today.  
- But all of them can *consume* NotebookLM as another evidence source if you wire it in via Pi tools or shell scripts.

***

## Constraints and Caveats

- **Unofficial status & TOS**: `notebooklm-py` and the MCP server rely on reverse‑engineered protocols. That may violate Google’s terms of service, and it may break when NotebookLM’s internal APIs change. You should treat this as experimental or personal‑use tooling, not something to deploy inside a regulated enterprise without a legal review.[2][4]

- **No local execution**: All NotebookLM processing is done on Google’s side using Gemini; you’re not reducing external data dependencies, just consolidating them into the Google ecosystem. If your main goal with Pi is local or air‑gapped operation, NotebookLM is the opposite direction.[13][3]

- **Auth & multi‑account complexity**: Running NotebookLM automations headless usually means either:
  - Long‑lived tokens / cookies managed by the Python library, or  
  - Some headful login flow to obtain initial credentials.[2]
  This is more fragile than, say, using Perplexity or Tavily via API keys.

***

## Practical Next Step for You

Given your profile (solution architect, multi‑model routing, strong Python):

1. Experiment with **Option A (sidecar)** first:
   - Install `notebooklm-py`.  
   - Create a small “Pi <-> NotebookLM” glue script that:  
     - Reads the current Pi workspace (`bash` + `find` or `git ls-files`),  
     - Uploads key docs into a NotebookLM notebook,  
     - Runs a `research` query,  
     - Writes results to `notes/notebooklm-summary.md`.  
   - Have your `/deep-research` workflow treat that file as one of its local sources.

2. If you like the ergonomics, promote it to **Option B (first‑class skill)**:
   - Wrap the Python calls in a Pi skill with typed tools, so Pi can call “`notebooklm_query`” directly as a tool in its deep research planning phase.

If you tell me whether you prefer a pure‑TypeScript skill or a Python microservice that Pi hits over HTTP, I can draft a concrete skeleton (directory layout + minimal code) for a `pi-skill-notebooklm` you can drop into `~/.pi/agent/skills`.

## Human

I don't care if it's python or typescript.  typescript seems to be more common in PI plugins?

## Assistant

Yes — **TypeScript is the more natural default for Pi plugins/extensions**. Pi itself is overwhelmingly TypeScript, its extension system is TypeScript-first, and most public examples and extension guides are written that way.[1][2][3]

## Why TypeScript fits Pi

Pi’s own repo is about 94% TypeScript, and Pi describes extensions as TypeScript modules that can register tools, commands, keyboard shortcuts, events, and TUI behavior.  Public extension examples and guides also frame Pi extensions as TypeScript code, not Python plugins.[2][4][5][3][1]

That matters because a NotebookLM integration for Pi is less about “what language can call NotebookLM?” and more about “what language matches Pi’s extension surface?” On that question, TypeScript is the path of least resistance.[3][2]

## Python vs TypeScript

Here’s the practical tradeoff for your case:

| Option | Best for | Strengths | Weak spots |
|---|---|---|---|
| TypeScript Pi extension | Native Pi integration | Matches Pi extension model, easier tool/command registration, more examples in ecosystem [3][2][4] | You may still need to call an external service for NotebookLM |
| Python sidecar | Fastest NotebookLM experimentation | Strong existing NotebookLM automation library via `notebooklm-py` [6][7] | Feels less native in Pi, more glue code and process management |
| TypeScript + local HTTP wrapper | Best long-term architecture | Native Pi extension plus clean separation of concerns; can wrap NotebookLM MCP/REST servers [8][9] | Slightly more setup up front |

## Best architecture

For **Pi + NotebookLM**, I would default to a **TypeScript Pi extension that talks to a local service**, not a pure Python plugin. That gives you a native Pi interface while preserving flexibility underneath.[8][2][3]

The cleanest variants are:

- **TypeScript extension -> NotebookLM MCP/REST server**: best if you want a reusable adapter layer and future support for other clients. Repos like `roomi-fields/notebooklm-mcp` and `moodRobotics/notebooklm-mcp-server` are already TypeScript-based and expose NotebookLM over MCP or HTTP-style interfaces.[9][8]
- **TypeScript extension -> Python subprocess using `notebooklm-py`**: best if you want fastest proof of concept and are comfortable with Python handling auth/session quirks.[6][7]

## Recommendation

Given your Pi use case, I’d choose **TypeScript for the Pi-facing layer** and stay agnostic underneath. That gives you Pi-native commands/tools now, while letting you swap the backend between `notebooklm-py`, an MCP server, or a REST wrapper later.[2][8][3]

A good minimal design would be:

- `notebooklm_import_sources`
- `notebooklm_query`
- `notebooklm_research_brief`
- `/notebooklm-sync`
- `/notebooklm-ask`

That keeps the Pi extension thin and deterministic, which is usually the right design for agent harness integrations.

## Uncertainty

The one caveat is that NotebookLM automation in the current ecosystem appears to rely on unofficial or reverse-engineered integrations rather than a stable public Google API. That makes the backend the fragile part, regardless of whether your Pi layer is TypeScript or Python.[7][8][9][6]

My confidence is **high** that TypeScript is the better default for Pi extensions, and **medium-high** that the best implementation pattern is TypeScript-on-top with either a Python or TypeScript NotebookLM backend.

Would you like a concrete `pi-skill-notebooklm` skeleton in TypeScript, or a fuller design that plugs into `@quintinshaw/pi-dynamic-workflows`?

## Human

full design

## Assistant

Yes — for a **full NotebookLM-in-Pi design**, I’d make the Pi-facing layer TypeScript and keep NotebookLM behind a local adapter boundary. That is the cleanest fit with Pi’s extension model and with `@quintinshaw/pi-dynamic-workflows`, which already generates JavaScript orchestration scripts and fans work out to subagents.[1][2][3]

## Architecture

Pi is minimal by design and expects custom capability to come from TypeScript extensions, skills, and packages rather than from a large built-in feature surface.  Dynamic Workflows specifically works by having Pi generate a small JavaScript orchestration script that coordinates parallel subagents and returns a synthesized result, which makes a research-sidecar pattern a natural fit.[2][3][4][1]

Recommended shape:

| Layer | Tech | Responsibility |
|---|---|---|
| Pi extension | TypeScript | Registers Pi tools, slash commands, config, and workflow glue. [2][3] |
| Pi skill | Markdown + optional scripts | Teaches the agent when to use NotebookLM and when not to. [5][6] |
| NotebookLM adapter | TypeScript or Python service | Handles auth/session, notebook CRUD, source import, query, and export. [7][8][9] |
| Research workflow integration | `@quintinshaw/pi-dynamic-workflows` | Parallelizes web search, NotebookLM corpus analysis, adversarial review, and synthesis. [1] |
| Search layer | `pi-web-access` | Open-web discovery and retrieval before import into NotebookLM. [10] |

The key design choice is this: **NotebookLM should not replace your web research layer**. NotebookLM is strongest as a grounded corpus reasoner over imported material, while `pi-web-access` and the normal deep-research flow remain better for broad discovery and fresh-source collection.[10][11]

## Operating model

Use a two-track research pipeline:

1. **Discovery track**: Pi uses `pi-web-access` and existing deep-research workflows to find candidate sources, URLs, PDFs, repos, and videos.[1][10]
2. **Grounding track**: Selected sources are imported into a NotebookLM notebook, then Pi queries NotebookLM for citation-backed synthesis over that curated corpus.[9][7][8]
3. **Synthesis track**: Dynamic Workflows runs a final synthesis agent that merges open-web findings with NotebookLM-grounded findings and flags conflicts.[1]

That gives you a practical split:
- **Web providers** answer “what sources should I look at?”
- **NotebookLM** answers “what do these selected sources say together?”
- **Pi orchestration** answers “which result do I trust, and what should the final report say?”

## Components

### 1. Pi extension package

Build a package such as `@yourorg/pi-notebooklm`. Pi packages can bundle extensions, skills, prompts, and themes, and Pi extensions are TypeScript modules with access to tools, commands, events, and TUI features.[3][2]

The extension should register these **tools**:

- `notebooklm_create_notebook`
- `notebooklm_list_notebooks`
- `notebooklm_import_sources`
- `notebooklm_query`
- `notebooklm_generate_briefing`
- `notebooklm_export_notes`
- `notebooklm_sync_workspace_sources`

And these **commands**:

- `/notebooklm-new`
- `/notebooklm-sync`
- `/notebooklm-ask`
- `/notebooklm-brief`
- `/notebooklm-open`
- `/notebooklm-research`

Suggested tool contracts:

```ts
type SourceInput =
  | { type: "url"; url: string }
  | { type: "pdf"; path: string }
  | { type: "youtube"; url: string }
  | { type: "gdrive"; id: string }
  | { type: "text"; title: string; content: string };

interface CreateNotebookInput {
  title: string;
  folder?: string;
  tags?: string[];
}

interface CreateNotebookOutput {
  notebookId: string;
  title: string;
}

interface ImportSourcesInput {
  notebookId: string;
  sources: SourceInput[];
  dedupe?: boolean;
}

interface ImportSourcesOutput {
  imported: Array<{ sourceId: string; title: string; status: "ok" | "skipped" | "failed" }>;
}

interface QueryNotebookInput {
  notebookId: string;
  query: string;
  mode?: "qa" | "research" | "compare" | "outline";
  citationMode?: "required" | "preferred";
}

interface QueryNotebookOutput {
  answer: string;
  citations: Array<{ sourceId: string; title: string; locator?: string }>;
  followups?: string[];
}
```

Keep the extension thin. It should mainly do validation, config lookup, error normalization, and transformation between Pi tool schemas and the adapter API.

### 2. Pi skill

Create a `notebooklm-research` skill that teaches the model:
- Use NotebookLM when the user has a bounded corpus, repeated follow-up questions, or wants grounded synthesis over imported materials.[6][5]
- Use `pi-web-access` first when the topic is broad, recent, or poorly specified.[10]
- Use Dynamic Workflows when you need parallel source gathering, adversarial review, or multi-perspective synthesis.[1]
- Never treat NotebookLM as proof of truth; compare its answer with source-level evidence and open-web findings.

This skill is important because Pi’s behavior is shaped heavily by skills and prompt engineering rather than only by tool registration.[5][2]

### 3. NotebookLM adapter

You have two viable backend choices:

| Adapter | Pros | Cons |
|---|---|---|
| `notebooklm-py` sidecar | Mature for automation, already oriented toward research workflows. [7][8] | Python runtime, unofficial protocol, more cross-process glue. [7][8] |
| TypeScript MCP/REST server | More uniform with Pi stack, easier packaging on Windows, good long-term shape. Repos exist exposing NotebookLM over MCP or HTTP. [12][13][9] | You still depend on unofficial automation underneath. [13][9] |

My recommendation is:

- **Phase 1**: TypeScript Pi extension calling a **local REST adapter**.
- **Phase 2**: Adapter implemented by whichever NotebookLM backend is currently most reliable.
- **Phase 3**: Optional support for both backends behind one interface.

Use an internal adapter interface like:

```ts
interface NotebookLMAdapter {
  health(): Promise<{ ok: boolean; backend: string }>;
  createNotebook(input: CreateNotebookInput): Promise<CreateNotebookOutput>;
  listNotebooks(): Promise<Array<{ notebookId: string; title: string }>>;
  importSources(input: ImportSourcesInput): Promise<ImportSourcesOutput>;
  query(input: QueryNotebookInput): Promise<QueryNotebookOutput>;
  exportNotes(notebookId: string): Promise<{ markdown: string }>;
}
```

That decouples Pi from NotebookLM implementation churn, which is important because current automation appears unofficial and therefore fragile.[7][8][13][9]

## Workflow integration

`@quintinshaw/pi-dynamic-workflows` is the best match for deep research because it already supports parallel subagents, cross-checking, and synthesis through generated JavaScript orchestration.[1]

A good `/notebooklm-research` workflow would look like this:

### Phase A: Plan
- Break the user request into:
  - discovery questions
  - corpus questions
  - validation questions
- Decide whether a notebook exists already or must be created.

### Phase B: Discover
- Use `pi-web-access` to gather authoritative sources.[10]
- Score and filter by freshness, authority, and relevance.
- Extract importable source candidates.

### Phase C: Ground
- Import the best candidates into NotebookLM via `notebooklm_import_sources`.[8][7]
- Run 2 to 4 structured NotebookLM prompts:
  - factual extraction
  - consensus/disagreement extraction
  - missing-information detection
  - briefing outline

### Phase D: Adversarial review
- Spawn a reviewer subagent that challenges:
  - unsupported claims
  - overconfident synthesis
  - stale sources
  - source monoculture
- If needed, route back to discovery for more sources.[1]

### Phase E: Synthesize
- Final agent merges:
  - open-web findings
  - NotebookLM-grounded findings
  - explicit uncertainties
- Produce:
  - short answer
  - evidence table
  - action steps
  - unresolved questions

Pseudo-orchestration:

```ts
const discovery = await parallel([
  webResearch("authoritative sources for topic"),
  webResearch("recent developments topic"),
  webResearch("primary docs topic"),
]);

const selected = rankSources(discovery, { authority: 0.5, freshness: 0.3, relevance: 0.2 });

const notebook = await notebooklm.createNotebook({ title: task.title });
await notebooklm.importSources({
  notebookId: notebook.notebookId,
  sources: selected.map(toSourceInput),
  dedupe: true,
});

const [facts, disagreements, gaps] = await parallel([
  notebooklm.query({ notebookId: notebook.notebookId, query: task.factualPrompt, mode: "research", citationMode: "required" }),
  notebooklm.query({ notebookId: notebook.notebookId, query: task.disagreementPrompt, mode: "compare", citationMode: "required" }),
  notebooklm.query({ notebookId: notebook.notebookId, query: task.gapPrompt, mode: "outline", citationMode: "required" }),
]);

const critique = await adversarialReview({ discovery, facts, disagreements, gaps });

return synthesize({ discovery, facts, disagreements, gaps, critique });
```

## Windows 11 deployment

For your environment, I would keep installation simple:

### Pi package
- npm package containing:
  - `extensions/notebooklm.ts`
  - `skills/notebooklm-research/SKILL.md`
  - optional prompt templates
  - optional scripts for health checks

### Local adapter service
Run as one of:
- `node dist/server.js`
- `uvicorn notebooklm_adapter:app`
- `docker compose up` if the backend needs browser/session helpers

### Config
Store in a simple local config file or env:

```json
{
  "adapterBaseUrl": "http://127.0.0.1:4319",
  "defaultNotebook": "research-default",
  "autoImportWorkspaceDocs": false,
  "maxSourcesPerRun": 20,
  "requireCitations": true
}
```

### Auth/session
This is the highest-risk area. Current NotebookLM automation approaches appear to depend on unofficial integrations, browser automation, or reverse-engineered RPC behavior rather than a stable public API.  Design for:[13][9][7][8]
- explicit health check
- explicit reauth command
- session expiry handling
- clear “degraded mode” fallback to normal Pi web research

## Tool behavior rules

To keep the system robust, define these rules in the skill and extension:

- **NotebookLM is not used by default** for broad or highly time-sensitive topics.
- **NotebookLM is preferred** when:
  - there is a user-provided corpus,
  - the user wants repeated exploration of the same source set,
  - the task requires grounded synthesis over many long documents.
- **Citations required** for NotebookLM answers that affect the final report.
- **Freshness gate**: if sources are older than the user’s need, rerun discovery.
- **Conflict gate**: if NotebookLM and web synthesis disagree, surface both rather than collapsing to one answer.

Those rules fit your stated preference for epistemic caution and explicit uncertainty.

## UI and command ergonomics

Because Pi is interactive, the extension should expose lightweight commands that keep state visible without hiding complexity.[4][2]

Recommended commands:

- `/notebooklm-new "topic"` → creates notebook and pins it as current
- `/notebooklm-sync` → imports current selection, file list, or URLs
- `/notebooklm-ask "question"` → asks current notebook and returns citation-backed answer
- `/notebooklm-brief "topic"` → generates concise research memo from current notebook
- `/notebooklm-research "query"` → full workflow: discover, import, ground, critique, synthesize

Good TUI affordances:
- current notebook indicator
- adapter health status
- import progress
- source counts
- last sync timestamp
- warning badge when auth/session is stale

## Failure modes

The main risks are not in Pi; they are in the NotebookLM backend.

| Failure mode | Likely cause | Design response |
|---|---|---|
| Auth expires | Browser/session-based automation | Add `health()` and `/notebooklm-login` or `/notebooklm-reauth`; fail gracefully. [9] |
| Source import fails | Unsupported source type or throttling | Retry per-source, continue partial import, mark failures clearly. |
| NotebookLM answer lacks citations | Backend limitation or prompt issue | Reject final use unless `citationMode` is satisfied. |
| Results are stale | Imported corpus outdated | Trigger discovery refresh and re-import via `pi-web-access`. [10] |
| Backend breaks after Google change | Unofficial API drift | Keep adapter swappable; do not bind Pi directly to one repo. [7][8][13] |

## Repo layout

I’d structure it like this:

```text
pi-notebooklm/
  package.json
  README.md
  src/
    extension.ts
    commands/
      notebooklm-new.ts
      notebooklm-sync.ts
      notebooklm-ask.ts
      notebooklm-brief.ts
      notebooklm-research.ts
    tools/
      create-notebook.ts
      import-sources.ts
      query-notebook.ts
      export-notes.ts
    services/
      adapter-client.ts
      source-normalizer.ts
      source-ranker.ts
      citation-validator.ts
      workspace-scanner.ts
    types/
      notebooklm.ts
      config.ts
  skills/
    notebooklm-research/
      SKILL.md
      examples.md
  prompts/
    grounded-synthesis.md
    disagreement-check.md
  examples/
    workflow-integration.md
```

This keeps the Pi package clean: extension/tool glue in TypeScript, research policy in the skill, and backend interaction behind a client boundary.

## Recommendation

My recommendation is:

1. Build a **TypeScript Pi package** first because Pi extensions and ecosystem patterns are TypeScript-first.[2][3]
2. Put NotebookLM behind a **local adapter API** so backend churn does not leak into Pi.[7][8][13]
3. Integrate with **`@quintinshaw/pi-dynamic-workflows`** for the actual deep-research orchestration because its JavaScript fan-out model is already aligned with this architecture.[1]
4. Keep **`pi-web-access`** in the loop for discovery; NotebookLM should be a grounded corpus layer, not your only research engine.[10]
5. Add explicit **uncertainty, citation, freshness, and conflict gates** because NotebookLM automation currently appears unofficial and potentially brittle.[9][8][7]

Confidence:
- **High** that TypeScript should be the Pi-facing implementation language.[3][2]
- **High** that Dynamic Workflows is the right orchestration substrate.[1]
- **Medium** that NotebookLM backend stability will be acceptable long-term, because current integrations appear unofficial.[8][13][7]

Would you like the next step to be a concrete package scaffold with file-by-file code skeletons, or the workflow prompt/skill definitions first?

## Human

complete package

## Assistant

I created a **complete starter package scaffold** for a TypeScript-first `pi-notebooklm` integration, including extension entrypoint, commands, tools, service layer, config/types, a Pi skill, reusable prompts, and a workflow integration example. The package is structured to keep Pi stable while putting NotebookLM behind a replaceable local adapter boundary, which is the safest design given today’s unofficial NotebookLM automation landscape.[1][2][3]

## What’s included

The scaffold includes:
- TypeScript package metadata and build config.
- Pi-facing commands such as `notebooklm-new`, `notebooklm-sync`, `notebooklm-ask`, `notebooklm-brief`, and `notebooklm-research`.
- Tool handlers for notebook creation, source import, querying, and note export.
- Services for adapter access, citation enforcement, source normalization, source ranking, and workspace document scanning.
- A `notebooklm-research` skill plus prompt templates for grounded synthesis and disagreement checking.

This matches Pi’s TypeScript-oriented extension model and is designed to plug into `@quintinshaw/pi-dynamic-workflows` rather than replacing your existing research stack.[4][5][1]

## Important caveat

What I generated is a **package scaffold**, not a guaranteed drop-in production package. The missing piece is the local NotebookLM adapter implementation and the exact Pi package registration surface for your installed Pi version, because NotebookLM integration currently appears to rely on unofficial or reverse-engineered interfaces and Pi package APIs may vary by release.[2][3][5][6]

So the current state is:
- **Done**: architecture, file layout, interfaces, command/tool skeletons, skill, prompts.
- **Not done yet**: concrete adapter server, end-to-end Pi runtime verification, packaging details against your exact Pi build.

## Best next step

The fastest way to make this real is to build the **adapter next**, then wire the package to your local Pi install for validation. I’d recommend one of these two paths:

- **Path A:** I generate a local REST adapter spec and starter implementation for `notebooklm-py`.
- **Path B:** I generate the Pi-specific package registration glue for your exact installed Pi version and extension API surface.

Which one do you want first: **adapter server** or **Pi runtime wiring**?

## Human

I want the best results

## Assistant

For the **best results**, don’t optimize for “pure Pi-native” or “pure NotebookLM.” Optimize for **research quality under uncertainty**: use Pi for orchestration, web search for discovery, and NotebookLM for grounded synthesis over curated sources. That hybrid design is stronger than a NotebookLM-only package or a Pi-only search workflow because NotebookLM excels at reasoning over trusted sources, while Pi’s extension system and Dynamic Workflows are built for composable tooling and parallel research orchestration.[1][2][3]

## Best architecture

The strongest setup is:

- **Pi TypeScript extension** as the control plane, because Pi’s extensibility system is TypeScript/JavaScript-first and officially supports custom tools, commands, UI hooks, and lifecycle integration.[4][1]
- **NotebookLM adapter service** as the data plane, because there is no general public consumer NotebookLM API, while community tooling exposes it via Python, REST, or MCP.[5][6]
- **Dynamic Workflows + pi-web-access** for discovery, parallelization, critique, and synthesis, because Pi packages are meant to be composed rather than monolithic.[7][8]

That means the “best results” path is **not** the smallest implementation. It is the most robust one:
1. Discover sources with normal web research.
2. Curate only the best sources.
3. Import them into NotebookLM.
4. Query NotebookLM for citation-backed synthesis.
5. Run adversarial review in Pi.
6. Merge findings into a final result with explicit uncertainty.

## Best backend choice

If the goal is **highest practical output quality**, I would choose this backend order:

| Role | Best choice | Why |
|---|---|---|
| Pi integration layer | TypeScript extension | This matches Pi’s official extension model and gives you the cleanest long-term package. [4][1] |
| NotebookLM execution backend | REST adapter over a proven automation layer | More stable operationally than coupling Pi directly to browser automation or MCP semantics. [9][6] |
| Initial NotebookLM engine | `notebooklm-py` or a mature REST wrapper around it | It is explicitly positioned as agent-ready and workflow-oriented. [10][6] |
| Optional second backend | MCP server | Good fallback and good for interoperability, but I would not make it the only backend. [9][11] |

Why REST-first? Because your Pi package should not care whether the backend is Python, browser automation, or MCP. A stable local HTTP contract gives you the cleanest separation and the easiest swap path when Google changes NotebookLM internals.[9][6]

## Best package design

If you want the best results rather than the fastest scaffold, the package should have **three** packages or modules, not one:

### 1. `@yourorg/pi-notebooklm`
Pi extension package in TypeScript. Responsibilities:
- register tools
- register commands
- keep local notebook context
- validate outputs
- enforce citation rules
- integrate with Dynamic Workflows

### 2. `@yourorg/notebooklm-adapter-contract`
Shared TypeScript types for:
- notebook CRUD
- source import
- query responses
- citations
- health/auth state
- artifact generation

This avoids schema drift between Pi and the adapter.

### 3. `notebooklm-adapter`
Standalone local service:
- Python or Node implementation
- HTTP endpoints
- auth/session management
- retries/backoff
- backend-specific quirks hidden behind one stable contract

That structure is better than a single all-in-one package because NotebookLM is the unstable boundary, not Pi. Pi should remain the stable shell.[1][5]

## Best workflow design

A high-quality research workflow should have four explicit modes.

### Mode 1: Discovery
Use `pi-web-access` or other web tooling to find authoritative and recent sources before NotebookLM is involved. NotebookLM now has its own Deep Research and web discovery capabilities, but Pi is still better placed to coordinate external sources, repo analysis, and multi-tool ranking under your control.[2][12]

### Mode 2: Corpus build
Import only the shortlisted sources:
- official docs
- papers
- PDFs
- repo URLs
- YouTube lectures
- internal notes
- Drive or doc assets supported by NotebookLM

NotebookLM supports multiple source types and is designed to stay grounded in the material you provide.[3][2]

### Mode 3: Grounded analysis
Ask NotebookLM to produce:
- factual extraction
- consensus/disagreement maps
- issue briefs
- gaps in evidence
- comparison summaries with citations

NotebookLM’s value is that it can provide source-grounded, citation-backed answers over the imported corpus.[9][3]

### Mode 4: Skeptical synthesis
Use Pi to:
- challenge NotebookLM claims
- compare NotebookLM output to raw sources and open-web findings
- surface uncertainty
- produce the final answer or report

This is the part most “deep research” tools underdo. Your architecture should make the skeptical pass a first-class phase, not an optional afterthought.

## What I would actually build

If I were optimizing for your use case, I would build this exact stack:

### Pi package
- `notebooklm_create_notebook`
- `notebooklm_import_sources`
- `notebooklm_query`
- `notebooklm_export_notes`
- `notebooklm_generate_briefing`
- `/notebooklm-new`
- `/notebooklm-sync`
- `/notebooklm-ask`
- `/notebooklm-brief`
- `/notebooklm-research`
- `/notebooklm-status`
- `/notebooklm-reauth`

### Adapter endpoints
- `GET /health`
- `GET /auth/status`
- `POST /auth/login`
- `POST /notebooks`
- `POST /notebooks/list`
- `POST /sources/import`
- `POST /query`
- `POST /briefing`
- `POST /export/notes`

### Quality gates
- Reject NotebookLM answers with zero citations when `requireCitations=true`.
- Reject final synthesis if fewer than `N` high-authority sources were imported.
- Mark stale corpus if imported source set is older than a threshold.
- Force disagreement review when NotebookLM synthesis conflicts with open-web findings.
- Store an import manifest so every claim can be traced to a known notebook/source set.

That gives you better epistemic control than most off-the-shelf “deep research” wrappers.

## What to avoid

If your goal is best results, I would **not** do these:

- **Do not bind Pi directly to a single NotebookLM MCP server** as your only backend. MCP is useful, but it is not the best long-term stability boundary here.[11][9]
- **Do not skip open-web discovery** and rely only on NotebookLM Deep Research. NotebookLM’s built-in Deep Research is useful, but your best results will come from Pi orchestrating multiple source pipelines under explicit rules.[2][3]
- **Do not hardwire backend-specific response shapes into Pi commands.** Keep an adapter contract layer.
- **Do not trust citations blindly.** Citation presence is necessary, not sufficient; Pi should still critique alignment between claim and source.

## Recommendation

So the highest-quality answer is:

- **TypeScript for the Pi package**
- **REST adapter as the stable backend boundary**
- **`notebooklm-py` or a mature REST service as the first adapter implementation**
- **Dynamic Workflows for orchestration**
- **pi-web-access for discovery**
- **explicit citation, freshness, and disagreement gates**

That is the design most likely to produce the **best real research results**, not just the neatest plugin architecture. Pi gives you the control plane, NotebookLM gives you grounded corpus reasoning, and the adapter keeps the fragile part replaceable.[8][4][5][3][2]

My confidence is **high** on the architecture choice, **medium-high** on using REST as the primary boundary, and **medium** on long-term NotebookLM backend stability because current general-access automation remains unofficial outside enterprise/API-specific paths.[5]

The right next build step is **the adapter contract plus a real adapter implementation**, then tighten the Pi package to that concrete interface.

## Human

proceed

## Assistant

I proceeded with the **best-results architecture** and created a fuller monorepo scaffold: a Pi package, a shared adapter contract, and a local NotebookLM adapter server scaffold. That structure is the right direction if your priority is research quality and long-term maintainability rather than a quick one-file plugin.[1][2][3]

## What’s now included

The generated scaffold contains three layers:

| Package | Purpose |
|---|---|
| `packages/pi-notebooklm` | Pi-facing TypeScript package with commands, tools, skill, prompts, and workflow glue. |
| `packages/notebooklm-adapter-contract` | Shared TypeScript request/response types for a stable adapter boundary. |
| `packages/notebooklm-adapter` | Local HTTP adapter server scaffold that Pi can call. |

This is the right separation because Pi’s extension system is TypeScript-first, while NotebookLM access currently appears to require unofficial or wrapper-based automation rather than a standard public API.[2][3][1]

## Quality improvements over the first scaffold

This version is materially better than the first package because it adds:
- a **stable contract layer** between Pi and NotebookLM,
- a **local adapter server scaffold** instead of only a client,
- **citation gates** on query and briefing outputs,
- a **minimum-import guard** so low-source runs can fail fast,
- a **status command** and adapter health endpoint,
- clearer workflow separation for NotebookLM-grounded analysis versus normal discovery.[4][5]

That aligns with your preference for explicit uncertainty handling and skeptical gating instead of optimistic “it probably works” integration.

## What is still not finished

Important: this is still a **high-quality scaffold**, not a finished production package. The main missing piece is the **real NotebookLM backend implementation** behind the adapter, plus exact Pi registration code matched to your installed Pi build and extension API surface. Pi definitely supports custom tools and commands through extensions, but extension/package APIs can vary by docs version and runtime packaging expectations.[6][1][2]

So the current status is:

- **Done**: architecture, repo layout, contracts, package boundaries, core command/tool shape, quality gates, adapter HTTP shape.
- **Pending**: real NotebookLM auth/session logic, source import plumbing, actual query execution, integration testing, and exact Pi runtime registration details.

## Best next move

If you want the **best results**, the next implementation step is not more package scaffolding. It is to build the **real adapter** against one backend and then wire Pi to that concrete interface.

The highest-value next options are:

- **Option 1: Real adapter implementation using `notebooklm-py`** — likely the fastest path to actual functionality because it is explicitly positioned as an agent-ready NotebookLM automation layer.[7]
- **Option 2: Real adapter implementation using an MCP/REST NotebookLM server** — better if you want a more interoperable TypeScript-friendly boundary from the start.[5][8][9]

My recommendation is **Option 1 first, with the REST contract you now have**, because it gives you a working backend sooner while preserving the ability to swap in an MCP or Node-based backend later.[5][7]

## Recommendation

The best path from here is:

1. Implement the adapter endpoints against one real NotebookLM backend.
2. Add end-to-end smoke tests.
3. Then tighten the Pi package registration against your actual Pi install.
4. Then integrate with `pi-web-access` and `@quintinshaw/pi-dynamic-workflows` for the full research loop.[10][11][1]

That order maximizes actual research quality and minimizes wasted plugin work around a backend that may still shift.

Would you like me to proceed with the **real adapter implementation targeting `notebooklm-py`**?

## Human

yes, please continue till I have everything I need

## Assistant

I continued and added the pieces you’d actually need next: a Windows-oriented install guide, architecture notes, Pi setup notes, an environment template, a PowerShell backend check script, and a `notebooklm-py` backend scaffold behind the adapter boundary. This is now much closer to a usable implementation path than a bare plugin skeleton, and it follows the right separation because Pi officially supports TypeScript extensions and `notebooklm-py` is positioned as an agent-ready, unofficial NotebookLM automation layer rather than a stable public Google API.[1][2][3][4]

## What you have now

You now have a monorepo scaffold with:

- a **Pi package** for commands/tools/skills,
- a **shared adapter contract**,
- a **local adapter server**,
- a **`notebooklm-py` backend shim**,
- **Windows install docs**,
- **Pi-specific integration notes**, and
- **PowerShell scripts** for local verification.

That is the correct “best results” direction because it separates the stable Pi-facing surface from the unstable NotebookLM automation layer, which matters since there is still no general public consumer NotebookLM API and community solutions rely on wrappers or undocumented behavior.[4][5][1]

## Important reality check

You do **not** yet have a guaranteed production-ready end-to-end system. The current backend shim is intentionally conservative and still contains placeholder logic where real `notebooklm-py` calls must be wired in. That was the right move, because pretending to finish unsupported API details without verifying the exact live library surface would be lower quality than leaving an explicit integration seam.[2][1][4]

So, specifically:

- **Done**: package architecture, contracts, adapter boundary, docs, scripts, and a backend scaffold shaped for `notebooklm-py`.  
- **Still needed**: exact `notebooklm-py` method bindings, runtime validation on your Windows machine, and final Pi registration against your installed Pi version.[6][3][1]

## Best next action

The highest-value next step is now very clear: implement the adapter against the **actual installed `notebooklm-py` API surface**, then test it locally on your machine. `notebooklm-py` documents installation modes including browser-enabled installs and headless/server-oriented installs, so it is the right first backend to target.[7][2]

Use this sequence:

1. Install `notebooklm-py` in a dedicated virtual environment.[2]
2. Verify import and auth/session behavior locally.
3. Inspect the installed library’s real classes/functions.
4. Replace the adapter placeholder scripts with real calls.
5. Smoke-test adapter endpoints.
6. Then build and load the Pi extension against that concrete backend.[3][6]

## Recommendation

For **best results**, I would stop generating more scaffolding and switch to **live integration mode** on your machine. The remaining work is no longer architecture; it is environment-specific binding and validation. That is also where the biggest uncertainty sits, because NotebookLM automation depends on unofficial mechanisms and can change underneath you.[5][4]

The practical next move is:

- install `notebooklm-py`,
- inspect its current Python API,
- and bind the adapter methods to it one by one.

Would you like me to continue by generating the **exact commands and inspection steps you should run on Windows 11** to bind this scaffold to your installed `notebooklm-py`?

## Human

yes

## Assistant

Yes. The next step is to bind your scaffold to the **real installed `notebooklm-py` API on your Windows 11 machine**, because `notebooklm-py` supports Windows 10/11, recommends Python 3.10+, and explicitly distinguishes browser-enabled installs from headless/server installs.  Pi also supports loading custom extensions directly from a file during development, so you can validate the adapter before worrying about final package polish.[1][2][3]

## Setup commands

Run these in PowerShell from the monorepo root.

### 1. Create and activate a Python environment

```powershell
py -3.11 -m venv .venv
.\\.venv\\Scripts\\Activate.ps1
python -m pip install --upgrade pip
pip install "notebooklm-py[browser]"
```

That install mode is the documented recommendation for AI-agent and end-user workflows, while plain `pip install notebooklm-py` is the documented path for library users or headless/server cases.[1]

### 2. Inspect the actual installed package

Do **not** assume method names from examples or memory. Inspect the live package surface first.

```powershell
python - <<'PY'
import inspect
import notebooklm_py

print("module:", notebooklm_py)
print("module file:", getattr(notebooklm_py, "__file__", None))
print("top-level names:")
for name in sorted(dir(notebooklm_py)):
    if not name.startswith("_"):
        print(" -", name)
PY
```

Then inspect likely client classes or factories:

```powershell
python - <<'PY'
import inspect
import notebooklm_py

for name in sorted(dir(notebooklm_py)):
    if name.startswith("_"):
        continue
    obj = getattr(notebooklm_py, name)
    if inspect.isclass(obj) or inspect.isfunction(obj):
        print(f"\\n=== {name} ===")
        try:
            print(inspect.signature(obj))
        except Exception:
            pass
        try:
            print(inspect.getdoc(obj)[:1200] if inspect.getdoc(obj) else "(no docstring)")
        except Exception:
            print("(doc unavailable)")
PY
```

This is the most important step. `notebooklm-py` is unofficial, so the exact API shape matters more than any blog or wrapper example.[4][5]

## Find the right entry points

You are looking for functions/classes that map to your adapter contract:

- notebook creation
- notebook listing
- source import
- query/chat
- briefing/export
- auth/session bootstrap

Use these targeted searches:

```powershell
python - <<'PY'
import inspect
import notebooklm_py

keywords = ["notebook", "source", "import", "query", "chat", "ask", "research", "brief", "auth", "login"]
for name in sorted(dir(notebooklm_py)):
    if any(k in name.lower() for k in keywords):
        print(name)
PY
```

If the top-level module is thin, inspect submodules:

```powershell
python - <<'PY'
import pkgutil
import notebooklm_py

print("submodules:")
for m in pkgutil.iter_modules(notebooklm_py.__path__):
    print(" -", m.name)
PY
```

Then inspect the likely submodules:

```powershell
python - <<'PY'
import importlib, inspect, pkgutil, notebooklm_py

for m in pkgutil.iter_modules(notebooklm_py.__path__):
    mod = importlib.import_module(f"notebooklm_py.{m.name}")
    print(f"\\n### notebooklm_py.{m.name}")
    for name in sorted(dir(mod)):
        if not name.startswith("_"):
            obj = getattr(mod, name)
            if inspect.isclass(obj) or inspect.isfunction(obj):
                print(" -", name)
PY
```

## Verify auth/session strategy

The installation guide explicitly distinguishes:
- browser-enabled usage via `notebooklm-py[browser]`, and
- headless/server usage via plain install plus a `storage_state.json` approach.[1]

So you need to determine which mode actually works best on your machine.

### Browser-enabled validation

```powershell
python - <<'PY'
import notebooklm_py
print("Imported notebooklm_py successfully")
print("Now inspect docs/classes for browser or auth helpers")
PY
```

If the library exposes a login/bootstrap helper, use that first. If not, inspect for storage-state or browser/session classes. Search for those terms explicitly:

```powershell
python - <<'PY'
import importlib, inspect, pkgutil, notebooklm_py

terms = ["storage", "state", "browser", "playwright", "cookie", "auth", "session", "login"]
for m in pkgutil.iter_modules(notebooklm_py.__path__):
    mod = importlib.import_module(f"notebooklm_py.{m.name}")
    hits = [name for name in dir(mod) if any(t in name.lower() for t in terms)]
    if hits:
        print(f"\\nnotebooklm_py.{m.name}")
        for hit in hits:
            print(" -", hit)
PY
```

Your goal is to answer this before editing code:
- Does `notebooklm-py` want a browser session?
- Does it want a storage-state file/string?
- Does it expose a direct client constructor with auth parameters?

## Bind the adapter incrementally

Do **not** try to wire every endpoint at once. Replace placeholders one by one.

### Step A: Health check

Open:

`packages/notebooklm-adapter/src/backend/notebooklm-py.ts`

Start by making `health()` real. For example, if import succeeds and the relevant client/auth object initializes, return:

```ts
{ ok: true, backend: "notebooklm-py", authState: "ready" }
```

If the library requires storage state and none is present, return:

```ts
{ ok: true, backend: "notebooklm-py", authState: "reauth-required" }
```

That gives `/notebooklm-status` meaningful output immediately.

### Step B: List notebooks or create notebook

Next bind the easiest real operation you find from inspection:
- `listNotebooks()`, or
- `createNotebook()`

Whichever method is more obvious in the installed API should be the first real call. Don’t force notebook creation first if listing is easier.

### Step C: Import sources

After basic notebook operations work, bind `importSources()`. Since `notebooklm-py` is described as supporting notebook management, source ingestion, conversational querying, and research workflows, this is a core supported use case.[6]

Handle source types conservatively:
- URL
- PDF path
- YouTube URL
- text blob

If a source type is unsupported by the live API, reject it explicitly rather than pretending success.

### Step D: Query

Only after notebook CRUD and import are real should you bind `query()`. `notebooklm-py` is described as providing programmatic conversational querying and research workflows, so this should exist somewhere in the installed API surface.[6]

When you wire this:
- keep `citationMode` in the adapter contract,
- reject empty citations if your package config requires them,
- return raw follow-ups if the library exposes them.

## Test each endpoint locally

After each binding change:

### 1. Build the adapter

```powershell
npm --workspace packages/notebooklm-adapter run build
```

### 2. Start the adapter

```powershell
node packages/notebooklm-adapter/dist/server.js
```

### 3. Hit the endpoint in a new PowerShell window

Health:

```powershell
Invoke-RestMethod http://127.0.0.1:4319/health
```

Create notebook:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri http://127.0.0.1:4319/notebooks `
  -ContentType "application/json" `
  -Body '{"title":"Pi Test Notebook"}'
```

Import sources:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri http://127.0.0.1:4319/sources/import `
  -ContentType "application/json" `
  -Body '{"notebookId":"YOUR_NOTEBOOK_ID","sources":[{"type":"url","url":"https://example.com"}]}'
```

Query:

```powershell
Invoke-RestMethod `
  -Method POST `
  -Uri http://127.0.0.1:4319/query `
  -ContentType "application/json" `
  -Body '{"notebookId":"YOUR_NOTEBOOK_ID","query":"What does this source say?","mode":"research","citationMode":"required"}'
```

## Wire Pi only after adapter tests pass

Once the adapter is real enough that `health`, `create/list`, `import`, and `query` work from PowerShell, then build the Pi package.

```powershell
npm --workspace packages/pi-notebooklm run build
```

During development, Pi examples show loading an extension file directly with `--extension`, and Pi docs/examples also show copying extensions into the Pi extension directory for auto-discovery.[2][3]

So use one of these development paths:

```powershell
pi --extension .\\packages\\pi-notebooklm\\dist\\extension.js
```

or place the built extension where your Pi install expects extension auto-discovery.[2]

Then test in Pi:

- `/notebooklm-status`
- `/notebooklm-new "Test Notebook"`
- `/notebooklm-sync <notebookId>`
- `/notebooklm-ask <notebookId> "Summarize the imported sources"`

## Debugging priorities

Use this order when something fails:

1. **Import failure**  
   Can Python import `notebooklm_py`? If not, fix the venv or install first.[1]

2. **Auth/session failure**  
   Determine whether the library expects browser flow or storage-state JSON. The installation guide explicitly distinguishes these modes.[1]

3. **API shape mismatch**  
   Re-run live inspection and update the backend bindings; do not trust guessed method names.[5][4]

4. **Pi integration failure**  
   Verify the adapter independently first, then the built extension entrypoint, then Pi command registration. Pi supports direct extension loading for testing.[3][2]

## Recommended working style

For best results, work in this exact loop:

- Inspect live `notebooklm-py` API.
- Bind one adapter method.
- Test with `Invoke-RestMethod`.
- Move to the next method.
- Only then load Pi against the extension.

That sequence minimizes false assumptions and fits your “accuracy over speed” preference better than trying to finish the whole integration in one shot.

## What I’m most confident about

- **High confidence**: `notebooklm-py` is the right first backend to target for a Windows 11 local integration because it explicitly supports Windows and documents install modes for agent, browser, and headless usage.[1]
- **High confidence**: Pi direct extension loading is the right development loop before packaging.[3][2]
- **Medium confidence**: the exact `notebooklm-py` methods you’ll find, because that must be verified from the installed package rather than assumed from summaries.[4][5]

Paste me the output of the first two Python inspection commands, and I can map those results directly to the adapter methods you already have.
