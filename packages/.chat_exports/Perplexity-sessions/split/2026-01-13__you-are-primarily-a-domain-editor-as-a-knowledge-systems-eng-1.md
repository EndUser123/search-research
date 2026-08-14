---
title: "You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, "
date: "2026-01-13"
mode: "COPILOT"
uuid: "29b4c3b7-6a8f-414a-a38f-ae2b86d72a64"
entry_count: 1
---

## Human

You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, actionable insights.[1]

Read the entire conversation provided (post + comments). Remove navigation, ads, jokes, and obvious filler. Collapse any redundancy, but do not lose any unique, concrete information that could change how someone works or makes decisions in this domain.[2][1]

Produce a rewritten version of the thread that:

- Keeps every distinct **insight, workflow, configuration, or regimen**, including:
  - Specific sequences of actions, steps, or protocols people follow.
  - Concrete parameter choices (doses, thresholds, settings, schedules, frequencies, tools).[1]
  - Integration details between {artifacts_1}, {artifacts_2}, and {artifacts_3} (e.g., how they are chained or orchestrated).
- Preserves all mentions of **key artifacts** and what people actually do with them:
  - {artifact_type_1}: e.g., tools, agents, drugs, components.
  - {artifact_type_2}: e.g., files, documents, guidelines, protocols.
  - {artifact_type_3}: e.g., automations, policies, hooks, governance mechanisms.
- Removes repeated restatements of the same idea unless a repetition adds a new nuance, constraint, or failure mode.

After the rewrite, add a section called **“Operational patterns and setups”** where you explicitly list:

- **Multi‑entity flows**
  - How multiple {entities} are used together (e.g., “I use {artifact_A} and {artifact_B}, then have {artifact_C} consolidate and apply changes”).[1]
- **Automation patterns**
  - Any described triggers, scheduled runs, pipelines, or hooks that react to events or phases.
  - Any rules that determine when something is reviewer‑only vs allowed to auto‑modify.[3][1]
- **Guardrail artifacts**
  - Named documents, configs, or policies (e.g., {guardrail_doc_1}, {guardrail_doc_2}) and the key rules or principles they encode.
  - How those guardrails are enforced in practice (checks, reviews, blocking conditions).

Add a final section **“Practical recommendations”** that distills the most useful advice into concrete steps another practitioner in this domain could implement, for example:

- “Set up {artifact_or_system} with {N} parallel {entities} and one consolidator that merges and applies decisions.”
- “Add a hook or rule that blocks {undesired_pattern} unless {explicit_condition} is met.”
- “Configure {tool_or_policy} to act as a reviewer/critic only, not an automatic changer, for high‑risk operations.”[1]
- “Centralize principles in a single {guardrail_doc} and reference it in every {process_stage} where decisions are made.”

Format the answer with short sections and bullets. Be concise but do not omit any unique workflow, configuration, regimen, or recommendation from the conversation that could alter how someone operates in this domain.[1]

***

To use it, just fill:

- {domain} → “technical”, “clinical evidence”, “policy”, etc.  
- {artifacts_*}, {entities}, {guardrail_doc_*}, {tool_or_policy}, {undesired_pattern}, {process_stage} with your domain‑specific terms.

## Assistant

This template is designed for a **technical** domain, where the key artifacts are tools/agents, files/configs, and automations/hooks, and the entities are different AI agents, skills, or MCP servers.[1]

***

## Cleaned, rewritten thread (template)

You are primarily a **technical editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, actionable insights.[1]

Your task is to read an entire discussion (post plus comments) and distill it into an operational document. Strip away navigation, ads, jokes, and obvious filler, while retaining any concrete detail that could change how someone designs or operates technical AI systems.[1]

When rewriting, keep every distinct insight, workflow, configuration, or regimen, including:

- Specific sequences of actions, steps, or protocols people follow to get results.
- Concrete parameter choices such as thresholds, limits, schedules, frequencies, tools, and model or environment settings.
- Integration details between:
  - **Tools/agents/components** (e.g., MCP servers, CLI tools, sandboxes, skills).
  - **Files/documents/protocols** (e.g., markdown memories, skill files, configuration docs).
  - **Automations/policies/hooks** (e.g., scheduled jobs, event-triggered pipelines, guardrails, or review flows).  
  Focus especially on how these artifacts are chained or orchestrated in practice.[1]

Preserve all mentions of key artifacts and what people actually do with them:

- **Artifact type 1 (tools/agents/components)**  
  Examples:  
  - LLM agents, MCP servers, CLI tools, sandboxes.  
  - “Tool search” mechanisms, programmatic tool-calling environments.  
  - File system and bash capabilities the agent uses (e.g., grep, glob, git, script execution).[1]

- **Artifact type 2 (files/docs/protocols)**  
  Examples:  
  - Skill files with front matter and references to scripts or markdown.  
  - Markdown memory files (e.g., `claw.md` or task-specific `.md` documents).  
  - Directory structures for skills (flat vs hierarchical/subskills).  
  - Any written guidelines or prompts stored as files and progressively disclosed.[1]

- **Artifact type 3 (automations/policies/hooks)**  
  Examples:  
  - Tool search mechanisms that discover tools on demand instead of preloading schemas.  
  - Automatic clearing of old tool results as context limits are approached.  
  - Flags or configuration switches that change how tools are exposed (e.g., experimental MCP CLI flags to enable tool search).[1]

Remove repeated restatements of the same idea unless a repetition adds a new nuance, constraint, or failure mode, such as:

- New evidence on token savings or accuracy changes from a pattern.
- A specific failure mode (e.g., context bloat, unused tools, degraded performance).
- A distinct way of structuring skills, memory files, or tool orchestration that differs operationally from prior mentions.[1]

***

## Operational patterns and setups

### Multi-entity flows

- Use a **tool search mechanism** plus many MCP servers instead of loading all MCP schemas into context.  
  - The model writes TypeScript or code that discovers and calls MCP endpoints on demand, rather than seeing all tool definitions up front.[1]
- Give the **agent access to a file system and bash**, then treat tools as files:  
  - The agent uses bash (grep, glob, reading/writing files, running scripts, pushing to git) to discover skills, scripts, and configuration documents only when needed.[1]
- Create a **skills directory** in Claude Code and similar systems:  
  - Each skill has front matter that is always visible plus references to other scripts or markdown files.  
  - The agent first sees only the front matter, then reads additional referenced files progressively when it decides they are needed.[1]
- Combine **skills + tool search + file-based memory**:  
  - Tool search discovers the right tool or MCP server at runtime.  
  - Skills provide structured entry points with minimal static context.  
  - File-based memory (markdown files and scripts) acts as long-term knowledge that can be read, updated, and searched on demand.[1]

### Automation patterns

- **On-demand tool discovery**:  
  - Instead of registering all tools up front, use a tool search tool or experimental MCP CLI to dynamically find tools relevant to the current task.  
  - This reduces context from tens of thousands of tokens to a small core, while maintaining access to the full tool library.[1]
- **Programmatic tool calling in a sandbox**:  
  - The model generates code (e.g., TypeScript) that runs in a sandboxed execution environment.  
  - That code then interacts with MCP servers as a TypeScript API, achieving large token savings (up to nearly 99% in some reports) compared to sending tool schemas directly to the model.[1]
- **Progressive disclosure of skills**:  
  - Only the front matter of skills is loaded into static context.  
  - When needed, the agent loads the associated skill file, then follows references to additional scripts or markdown files, pulling them into context incrementally.[1]
- **Automatic trimming of tool results**:  
  - As context approaches limits, older or less relevant tool results are automatically dropped from context, keeping the working set small and current.[1]
- **Ephemeral sandboxes and file systems**:  
  - Short-lived sandboxes spin up with their own ephemeral file systems for reading, writing, and running code.  
  - They are created for complex workflows (e.g., spreadsheets, scripts) and shut down when no longer needed, keeping the environment clean.[1]

### Guardrail artifacts

- **Skill front matter as a control surface**:  
  - The front matter defines what the skill is for, how it should be invoked, and what constraints apply.  
  - Because only front matter is always in context, it effectively acts as a light guardrail for when and how deeper content is fetched.[1]
- **File-based memory and knowledge as explicit, inspectable guardrails**:  
  - Markdown memory files, scripts, and skill documents encode the operational rules, patterns, and preferences.  
  - These can be searched, edited, and version-controlled, making it easier to audit and adjust behavior than opaque embeddings.[1]
- **System prompts plus tool-search flags**:  
  - A small system prompt plus configuration flags (e.g., enabling tool search for MCP) define how tools are discovered and used.  
  - This enforces a pattern where tools are only exposed on demand, limiting accidental overuse and context bloat.[1]

***

## Practical recommendations

- Set up a **skills directory** where each skill has:  
  - Minimal front matter (10–100 tokens) describing its purpose and how to invoke it.  
  - References to scripts and markdown files that are only read when needed, enabling large numbers of skills without context bloat.[1]
- Configure your **agent environment** so that tools become files:  
  - Provide a file system and bash to the agent.  
  - Let the agent use search (grep, glob), file reads, and scripts to discover and load capabilities on demand instead of preloading everything into context.[1]
- Use **tool search or an MCP CLI flag** to discover tools dynamically:  
  - Avoid registering every MCP server schema in the context window.  
  - Let the agent call a tool search mechanism to find the right server or skill only when required.[1]
- Prefer **programmatic tool calling in a sandbox** over direct JSON tool calls for large tool libraries:  
  - Have the model generate code that interacts with MCP servers as APIs in a sandbox, dramatically reducing token usage and improving accuracy on tool-heavy tasks.[1]
- Treat **memory as simple files**, not a complex vector system:  
  - Store knowledge in markdown files and scripts.  
  - Let the agent read, edit, and search them using the file system and bash, keeping retrieval simple and inspectable.[1]
- Enable or implement **automatic context trimming** for tool results:  
  - Drop older or less relevant tool outputs as you approach context limits so the active context stays small and focused.[1]
- Design workflows so that **context is never the main bottleneck**:  
  - Offload long-term knowledge and intermediate results to files.  
  - Use progressive lookup via skills, tool search, and file reads so agents can run for hours and interact with dozens or hundreds of tools without hitting hard context walls.[1]
