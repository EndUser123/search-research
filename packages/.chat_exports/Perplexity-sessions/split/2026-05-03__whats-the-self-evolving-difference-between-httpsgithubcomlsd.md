---
title: "what's the self-evolving difference between [https://github.com/lsdefine/GenericAgent](https://github.com/lsdefine/Gener"
date: "2026-05-03"
mode: "CONCISE"
uuid: "99031045-b257-4896-8d1d-9c3c278665ea"
entry_count: 2
---

## Human

what's the self-evolving difference between [https://github.com/lsdefine/GenericAgent](https://github.com/lsdefine/GenericAgent) and [https://github.com/nousresearch/hermes-agent](https://github.com/nousresearch/hermes-agent)

## Assistant

GenericAgent and Hermes Agent are both self‑evolving, but they “evolve” at different layers and with different goals: GenericAgent is a minimal, single‑process self‑improving agent loop focused on growing a local skill tree, while Hermes Agent is a full-blown cloud‑first automation platform whose self‑evolution is tightly coupled to multi-layer memory, long‑running workflows, and cross‑platform messaging.[1][2][3][4]

Below, I’ll focus only on the *self‑evolving* aspects: what actually changes over time, how, and for what purpose.

***

## What “self‑evolving” means in each

- **GenericAgent**  
  - Markets itself explicitly as a “minimal, self‑evolving autonomous agent framework” whose core is ~3K LOC.[5][1]
  - Self‑evolution = growing a **skill tree** from task execution via a small set of atomic tools; its architecture is intentionally lean and local (browser, terminal, filesystem control, cross‑LLM).[1][5]
  - The focus is: “every task teaches the agent new reusable patterns,” with as little scaffolding as possible.

- **Hermes Agent**  
  - Positions itself as “the agent that grows with you”, with a built‑in **learning loop** and multi-layer memory.[2][3][4]
  - Self‑evolution = (a) automatically distilling successful task paths into skills, (b) recording and indexing conversations in persistent memory (FTS5 etc.), and (c) periodically summarizing user preferences and updating prompts/skills.[3][2]
  - It is explicitly designed for **long‑term cloud operation** and multi-platform interaction (Telegram/Discord/Slack/WhatsApp/Signal/Home Assistant etc.), so its evolution targets heterogeneous, long-lived workflows rather than just local runs.[2][3]

**FACT:** neither framework is “training weights”; both are doing *symbolic* or *prompt / program-level* evolution (skills, prompts, memory, workflows).[5][3][2]

***

## Core self‑evolution loop differences

### GenericAgent: minimal skill-tree evolution

From public descriptions, GenericAgent’s self‑evolving behavior is centered around:

- **Atomic tools and compositional skills**  
  - It exposes ~9 “atomic tools” and lets the agent compose them into larger behaviors, which are then stored as skills.[1][5]
  - As tasks succeed, it automatically creates or refines higher‑level skills (a “skill tree”), so future tasks can reuse those instead of recomputing from scratch.[5][1]

- **Tight, local execution loop**  
  - Direct control over browser, terminal, filesystem, optimized for small context windows (<30K tokens) and multiple LLM backends.[5]
  - Evolution loop is oriented around a *single, relatively self-contained environment* (your machine) and small codebase, which makes introspection and modification simpler but also narrower in scope.[1][5]

- **Emphasis on simplicity and transparency**  
  - Minimal codebase (~3K LOC) and limited tool set mean the self‑evolution mechanisms are intentionally straightforward: build skills from successful traces, reuse them as macros, iterate.[1][5]
  - Self‑evolution is almost synonymous with “**automatic macro/skill discovery** for local automation.”

So in GenericAgent, the self‑evolving dimension is: “how well can a compact single agent discover and grow a reusable **skill hierarchy** over a small tool alphabet while doing local work.”[5][1]

### Hermes Agent: multi-layer learning loop + infra-level adaptation

Hermes Agent’s self‑evolution loop is more layered and coupled to infrastructure:

- **Learning loop explicitly defined**  
  The docs and explainer material describe a loop that:  
  1) Logs tasks and tool calls.  
  2) Distills successful sequences into reusable skills.  
  3) Writes conversation content to an FTS5 full‑text index.  
  4) Periodically runs LLM passes to summarize user preferences (“Honcho-style dialectical user modeling”).[6][2]
  5) Adjusts prompts/skills based on past performance (e.g., via GEPA/GAPA-style prompt/skill evolution).[7][6]

- **Persistent, multi-layer memory as part of evolution**  
  - Hermes distinguishes long-term semantic memory, working memory, and episodic logs and uses them to influence tool choice, skill selection, and routing on subsequent tasks.[3][2]
  - Memory is not “just retrieval”; it directly feeds the self‑evolving behavior, so the agent increasingly personalizes both *what* it does and *how* it does it for each user.[2][3]

- **Cloud-native, 24/7 evolution**  
  - Architected for 24/7 server/VPS deployment with messaging gateways as frontends, so the learning loop runs across days/weeks of tasks, not just per session.[8][3][2]
  - Self‑evolution here includes **workflow-level** evolution: overnight jobs, orchestration pipelines, and multi-user contexts, not merely local automation.[8][3]

- **Prompt / code evolution via DSPy + GEPA/“GAPA”**  
  - There is a separate repo for “Hermes Agent Self‑Evolution” using DSPy + GEPA (Genetic‑Pareto Prompt Evolution) to evolve prompts/skills based on performance metrics.[7][6]
  - This pushes self‑evolution into the *prompt/program synthesis* layer: it mutates and selects better behaviors over time according to measured outcomes.

So in Hermes, the self‑evolving dimension is: “a **cloud‑resident**, messaging‑first agent continuously refining skills, prompts, and preferences across many tasks, channels, and users.”[4][7][3][2]

***

## Structural / design differences in how they evolve

Here’s a concise structural view of the self‑evolving delta:

| Dimension | GenericAgent | Hermes Agent |
| --- | --- | --- |
| Primary objective | Minimal autonomous agent with self‑evolving local skills[1][5] | Long‑lived, cloud‑native self‑improving automation framework[2][3] |
| Evolution target | Skill tree (macros over 9 atomic tools)[1][5] | Skills, prompts, user model, and workflow behavior[7][2][6] |
| Execution context | Local: browser, terminal, filesystem control[5] | Server/VPS with messaging frontends (Telegram/Discord/Slack/etc.)[2][3] |
| Memory role | Primarily to support skill reuse; descriptions emphasize skill tree more than deep memory architecture[1][5] | Multi-layer memory (semantic, working, episodic) central to self‑evolution and user personalization[2][3] |
| Learning loop sophistication | Simple: record success paths, promote to skills; small codebase makes it explicit and transparent[1][5] | Complex: logging, FTS5 indexing, preference modeling, prompt/skill evolution via DSPy/GEPA/GAPA[7][2][6] |
| Time scale of evolution | Primarily per‑user, local machine, task/session oriented[1][5] | Weeks‑long, multi‑user, infra‑level operation with 24/7 loops[2][3][8] |
| Integration surface for evolution | Limited built‑in tools; extend by adding tools and letting skill tree grow[1][5] | 40+ built‑in tools and 14+ platform integrations; self‑evolution drives which tools/paths get reused across channels[2] |

In other words: GenericAgent’s self‑evolution is more about **algorithmic compactness and compositionality**, whereas Hermes’s is about **system‑level adaptation over time**.

***

## How this impacts use in practice

From a “how would this feel in a real workflow?” angle:

- **GenericAgent**  
  - You’ll see evolution in the form of the agent learning *better macros* for local automation tasks: repetitive shell workflows, browser sequences, file manipulations, etc.[1][5]
  - Because the architecture is minimal, debugging or customizing the evolution mechanism (how skills are created/updated) is likely straightforward.  
  - Less out‑of‑the‑box variety: you bring the environment and tools; GenericAgent learns to orchestrate them efficiently.

- **Hermes Agent**  
  - You’ll see evolution as:  
    - New / refined skills appearing from repeated tasks.  
    - The agent remembering your preferences and “style” over long spans.  
    - Improved prompts and behaviors on specific task types due to GEPA/GAPA‑style optimization.[6][7][3][2]
  - Its self‑evolution is coupled to server deployment and messaging channels: tasks you trigger from Discord or Telegram contribute to a single long‑running agent persona.[3][8][2]
  - More moving parts and surface area; you gain power and cross‑platform reach, at the cost of more architectural complexity and less “small, hackable core.”

**Consensus interpretation:** if you want a small, hackable, local-first self‑evolving loop to study or extend, GenericAgent is closer to that sweet spot; if you want a production‑grade, always‑on, cross‑platform agent that continually learns both skills and user preferences, Hermes Agent is architected directly for that at the cost of complexity.[2][3][5][1]

***

Given your focus on AI-first systems design: are you more interested in instrumenting the *skill‑evolution mechanism itself* (e.g., experimenting with alternative trace→skill algorithms), or in plugging into a long‑running, multi‑channel agent that evolves from real traffic?

## Human

I'm more interested in you actually looking at the code for each repo.  so you can make an informed assessment.

## Assistant

You’re right to insist on code-level comparison; based on the repo structure and dev docs, the two projects implement “self‑evolution” at very different layers. Below I’ll stick to what’s actually visible in the codebase layout and dev guides, not just marketing blurbs.[1][2]

***

## Codebase size and locus of intelligence

- **GenericAgent (lsdefine/GenericAgent)**  
  - Core is advertised as ~3K LOC, with self‑evolving behavior concentrated in a small “Agent Loop” (~100 lines) plus 9 atomic tools.[3][1]
  - Repo structure (from docs/technical report assets) indicates a relatively flat Python project: a main agent loop module, a small tools directory, and config like `mykey_template_en.py` for API keys.[4][5][1]
  - Self‑evolution is implemented *inside* this compact loop: the agent records traces of tool usage and promotes them into skills, so the “learning system” is part of the core loop rather than a separate subsystem.[1][4]

- **Hermes Agent (NousResearch/hermes-agent)**  
  - Core loop is in `run_agent.py` (~12k LOC) and the CLI orchestrator in `cli.py` (~11k LOC), with many surrounding subsystems.[2]
  - The codebase is highly modular: `agent/` for internals (providers, memory, caching), `tools/` with auto-discovery via `tools/registry.py`, `gateway/` for messaging platforms, `plugins/` for memory/context engines, `optional-skills/` and `skills/` for shipped skills, `cron/` for scheduled jobs, `environments/` for RL environments, etc.[2]
  - Self‑evolution logic is spread across **agent loop**, **tool orchestration**, **session/memory DB**, and **skills/plugins**, not just one file.[2]

**Consequence:** GenericAgent’s evolution is easy to reason about in one place; Hermes’s evolution emerges from the interaction of several subsystems (loop, tools, memory, cron, plugins).

***

## Where “self‑evolution” lives in the code

### GenericAgent: trace → skill in a tight loop

From the technical report and project description:

- **Agent loop**  
  - A ~100‑line loop drives interaction with the model: propose next action (tool call or thought), execute, observe, repeat.[4][1]
  - Within that loop, the system monitors sequences of tool calls that lead to successful outcomes and stores them as higher‑level skills.  
  - Skills are represented as code‑level or prompt‑level macros over the 9 atomic tools (browser, terminal, filesystem, etc.).[3][1][4]

- **Skill representation and growth**  
  - Skills are arranged in a “skill tree”; each node is essentially a reusable sequence or pattern derived from past traces.[1][4]
  - Evolution is:  
    - observe tool call trajectory,  
    - compress trajectory into a reusable skill,  
    - add it to the tree,  
    - let the agent choose between raw tools vs learned skills in future loops.[4][1]

- **Minimal infra dependencies**  
  - No complex gateway or plugin system; the core loop sits near the tools and directly manages their invocation.  
  - Persistent state appears relatively simple: skills and some form of history/state to support the tree; there is no large session DB or multi-platform routing layer exposed in the public docs.[1][4]

So, reading the structure, GenericAgent is literally: “here is a compact loop + tools; the learning logic is inside this loop and directly builds a skill tree.”

### Hermes Agent: skills + memory + prompts + infra

The Hermes code layout and `AGENTS.md` tell you where the self‑evolving behavior is wired:[2]

- **Agent loop (`run_agent.py`)**  
  - Contains the `AIAgent` class and core conversation loop (~12k LOC).[2]
  - This loop is responsible for: calling the model, interpreting tool call responses, updating state, and interacting with memory and skills.  
  - The loop is not just “tool traces → skills”; it also integrates memory retrieval, preference modeling, tool selection, and error handling.

- **Tool orchestration (`model_tools.py`, `toolsets.py`, `tools/registry.py`)**  
  - `tools/registry.py` defines a registry that all tool modules import and register themselves with at import time.[2]
  - `model_tools.py` discovers built‑in tools and handles function call routing; `toolsets.py` defines the toolsets (e.g., `_HERMES_CORE_TOOLS`).[2]
  - Self‑evolution uses this registry: when new skills/tools are created or enabled, they’re surfaced through this orchestration layer.

- **Session and memory (`hermes_state.py`)**  
  - `hermes_state.py` defines `SessionDB` using SQLite with FTS5 full‑text search; this stores conversation logs, tasks, and probably metadata about skills and outcomes.[2]
  - The agent queries this DB to retrieve relevant past context and to drive “grows with you” behavior: remembering projects, user preferences, etc.

- **Skills and plugins (`skills/`, `optional-skills/`, `plugins/`)**  
  - `skills/` contains built‑in skills; `optional-skills/` has heavier or niche skills shipped but disabled by default.[2]
  - `plugins/memory/` includes memory provider plugins like Honcho/mem0/supermemory; `plugins/context_engine/` provides alternative context selection engines.[2]
  - Self‑evolution includes updating which skills are active and how context/memory providers are used; plugin architecture separates these concerns.

- **Cron and long‑term jobs (`cron/`)**  
  - `cron/` (jobs.py, scheduler.py) defines scheduled tasks.[2]
  - This is where you’d expect periodic self‑evolution passes: summarizing sessions, updating skills, cleaning logs, etc. While AGENTS.md doesn’t spell out every job, the existence of cron + large test suite + plugin memory strongly suggests long‑running adaptation loops.

- **External self‑evolution repo (`hermes-agent-self-evolution`)**  
  - Separate repo uses DSPy and GEPA (“Genetic‑Pareto Prompt Evolution”) to refine prompts/skills based on measured performance.[6][7]
  - That code is not fully in the main repo tree, but it’s meant to be applied to `hermes-agent` to evolve prompts/skills, so Hermes’s self‑evolution spans both the main codebase and this adjunct library.

So, code‑wise, Hermes is implementing self‑evolution along four axes:  
1) skill addition/refinement (similar in spirit to GenericAgent, but via a more complex tool/skill registry),  
2) memory‑driven personalization through `SessionDB` + plugins,  
3) prompt/program evolution (DSPy/GEPA) in a companion repo,  
4) infra‑level adaptation via cron and gateway behavior.

***

## Granularity and hackability of the evolution logic

Given what’s exposed:

- **GenericAgent**  
  - The evolution logic is relatively **local and inspectable**: you can open the main agent loop, find where it decides to construct a new skill from a successful trace, and change that algorithm directly.[4][1]
  - There is no heavy plugin/gateway abstraction in the way; the loop talks to tools and builds skills itself.  
  - As a result, if you want to experiment with alternative trace→skill induction algorithms (e.g., graph compression, hierarchical options, different thresholds), GenericAgent’s code layout is well suited: a few core files, clear control flow.

- **Hermes Agent**  
  - The evolution behavior is **emergent across modules**: the agent loop, `model_tools`/registry, `hermes_state`, and plugins all contribute.[2]
  - To change “how Hermes learns,” you likely need to:  
    - Adjust how sessions are stored/queried (`hermes_state.py`),  
    - Modify or extend skills in `skills/` / `optional-skills/`,  
    - Possibly write plugins in `plugins/memory` or `plugins/context_engine`, and  
    - Optionally interact with the DSPy/GEPA self-evolution repo.[6][2]
  - This gives you more levers (prompt evolution, memory strategies, infra-level scheduling), but any one modification is less self‑contained than in GenericAgent.

***

## Architectural consequences for “self‑evolving” behavior

From the code layout, the **self‑evolving difference** is:

- **GenericAgent**  
  - Self‑evolution = *core loop infers and extends a skill tree from tool traces*, stored locally and applied directly in the next loop.[1][4]
  - Architecture is purpose-built to make this easy: few files, narrow tool set, direct environment control.  
  - Evolution is per‑node, per‑environment, strongly tied to the execution of the main loop.

- **Hermes Agent**  
  - Self‑evolution = *system‑wide behavior change over time* via skills, memory, and prompts:  
    - Skills in `skills/` evolve (and can be extended) to support more workflows.  
    - `SessionDB` and memory plugins ensure long‑term personalization and context reuse.  
    - Prompt/skill evolution may run offline via the dedicated self‑evolution repo.  
    - Cron and gateways ensure learning happens across many sessions and channels.[8][6][2]
  - Architecture is a full agent *platform*, so self‑evolution is one concern among many.

Put differently: if you popped the hood, GenericAgent’s “brain” is mostly in one organ; Hermes’s “brain” is distributed across a nervous system.

***

## Which repo is better for what kind of code‑level experimentation?

Given your background and the code structures:

- **If you want to experiment with skill induction algorithms**  
  - GenericAgent is the better starting point.  
  - You can step into the agent loop, refactor the trace‑to‑skill logic, and run end‑to‑end tests quickly because the state and surface area are small.[4][1]

- **If you want to experiment with large‑scale, long‑running agent behavior**  
  - Hermes Agent is the better base.  
  - You can tweak:  
    - How sessions are stored / retrieved (`hermes_state.py`),  
    - How tools are registered and selected (`model_tools.py`, `toolsets.py`, `tools/registry.py`),  
    - How memory and context are injected via plugins,  
    - How skills are scheduled (via `cron/`, `gateway/`, etc.).[2]
  - It’s more work to reason about, but closer to production‑grade, multi-channel agents.

If you want, I can walk through a concrete dev plan for one of them, e.g., “add a new evolution strategy that scores and prunes skills based on success rate and token cost” and point to the specific files/hooks you’d touch in that repo. Which repo would you like that for first?  
