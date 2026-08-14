---
title: "You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, "
date: "2026-02-25"
mode: "COPILOT"
uuid: "4068c106-5087-4761-82c8-c8b382ebc517"
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
   note that 'cloud' is actually 'claude'.

## Assistant

Below is a distilled rewrite of the *video + comments* focused on technical workflows and operational patterns for Claude **Skills** in a technical/agentic development context.[1]

***

## Core concepts of Claude Skills

- Skills solve a **context engineering** problem: instead of loading all tool schemas and instructions (tools, MCPs, local scripts) into the system prompt, you load only minimal metadata (name + description) and progressively disclose the full instructions only when the agent decides to use that skill.[1]
- A **skill** is just a folder whose minimum requirement is a `skill.md` file with:
  - YAML front matter: `name`, `description` (critical for telling the agent what the skill is and when to use it).
  - Body: detailed instructions, workflows, and any usage patterns.[1]
- Everything else in the folder is optional context: scripts (Python, bash), markdown/text docs, CSVs, other data; all of this can be selectively read by the agent as needed.[1]
- Compared to loading full tool/MCP schemas into the system prompt, skills let you fit **more capabilities** into the same context budget by only loading detailed instructions when the agent invokes that skill.[1]

***

## Progressive disclosure and context engineering

- When a skill is available to an agent:
  - Only the **name + description** from the YAML front matter is initially loaded into the system prompt.[1]
  - If the agent decides to use the skill, it then reads the **body** of `skill.md` and any referenced context files, pulling in detailed instructions only at that moment.[1]
- This is the same general pattern Kenny uses for his **personal assistant** built with the Claude Agent SDK: progressive context traversal through structured `cloud.md` files and folders (memory, projects, tools) instead of dumping everything into the system prompt at once.[1]
- Progressive disclosure with skills enables:
  - Token-efficient access to large instruction sets.
  - Conditional loading of heavy docs/templates/CSV data only when actually relevant to the current subtask.[1]

***

## Skills vs slash commands vs MCPs

- **Slash commands**:
  - Similar to skills in that they encode a predefined workflow prompt.[1]
  - Must be **explicitly triggered by the user** (e.g., `/command`), and the user must provide all required input arguments.[1]
  - Skills are **agent-driven**: the agent decides *when* to call them and *what* arguments/context to gather first (possibly via tools) before invoking the skill.[1]
  - Using skills instead of slash commands offloads more work (research, argument prep) to the agent.

- **MCPs**:
  - Feature set largely overlaps with what you can do with skills: tools, resources (context/data), and prompts mirror scripts, docs, and `skill.md`.[1]
  - Differences:
    - **Complexity**: MCPs require server infrastructure, MCP clients, and wiring, whereas skills are just folders + markdown + optional scripts.[1]
    - **Progressive disclosure**: skills natively only expose minimal metadata to the system prompt and load full instructions on demand; Claude’s current MCP integration instead tends to load all tool schemas and docs into the prompt.[1]
  - Kenny notes you *could* design MCP integrations to use similar progressive disclosure (only announce MCPs, then tools, then docs lazily) and has done this in custom agents, but this isn’t how Claude currently implements MCPs.[1]

- **Key benefits of skills**:
  - Built‑in context efficiency and progressive disclosure handled by Claude’s harness.
  - Simple implementation (just markdown + optional scripts).
  - Ability to **compose/stack** skills, where one skill uses other skills and standard tools.[1]

***

## Using skills in the Claude app (web/desktop)

- Enable skills:
  - Open **Settings → Capabilities → Skills** and toggle built‑in Anthropic skills on as needed.[1]
  - Examples:
    - **Skill creator**: lets you “vibe code” a new skill directly via prompting, seeing Anthropic’s own best practices encoded in the skill.[1]
    - Skills for building MCPs and working with Artifacts.[1]
- Upload custom skills:
  - Prepare a folder containing:
    - `skill.md` at the root with valid YAML front matter (`name`, `description`).
    - Optional subfolders like `scripts/` with Python or bash scripts.[1]
  - Zip that folder.
  - In the Skills section, use **Upload skill** (drag and drop the zip). If `skill.md` metadata is invalid, upload will fail.[1]
- Once uploaded and enabled, the skill is available in new chats automatically.[1]

***

## Example: Cohort analysis Excel skill

Goal: build a **cohort analysis financial model** in Excel/Sheets from a CSV of raw transaction data, with validation of formulas.[1]

- Skill structure:
  - Root: `skill.md` describes how to:
    - Read transaction data.
    - Build cohort‑based tables and metrics in Excel.
    - Use validation scripts to ensure formulas have no errors.[1]
  - `scripts/` folder:
    - Includes Python validation scripts that check the generated Excel model for formula errors after the agent populates formulas.[1]

- Usage in Claude app:
  - Upload the skill zip in Settings → Skills.[1]
  - Start a new chat and upload a CSV file with transactions (in Kenny’s example: ~20,000 transactions from ~1,000 customers).[1]
  - Prompt: “Build a cohort model” (the detailed requirements live inside the skill, not in the user prompt).[1]
  - Claude:
    - Examines the file to understand columns and schema.
    - Detects the cohort analysis skill as relevant.
    - Loads the skill’s body, builds an Excel file, writes formulas, and then runs the validation Python scripts defined in the skill instructions to verify no formula errors.[1]

- Output model structure:
  - One tab contains raw data (matching the input CSV) plus extra computed columns appended (e.g., cohort tags, derived fields).[1]
  - Another tab contains:
    - A small assumptions table at the top with adjustable input parameters (e.g., retention, discount rates, CAC values).[1]
    - Cohort‑based metrics over time:
      - Retention matrix by cohort and period.
      - Customer counts, transaction counts, average transactions per customer, total revenue, and eventually **LTV** and **CAC‑adjusted LTV**.[1]
    - All key cells formula‑based and responsive to changes in the assumptions table (e.g., change a parameter from 10 to 20 or from 10% to 5% and the model recomputes).[1]

- Reliability pattern:
  - After generating formulas, the agent runs validation scripts described in the skill to detect any Excel formula errors before returning the model.[1]
  - This pattern (generation + validation script) is central to Kenny’s approach for robust skills.[1]

***

## Using skills in Claude Code and Agent SDK

- To use skills in a Claude Code project or a custom agent built with the **Claude Agent SDK**, create a `claude/` (or equivalent) configuration folder, and inside it a `skills/` directory.[1]
- For each skill:
  - Create a subfolder under `skills/` containing:
    - `skill.md` at root.
    - Optional `scripts/` and other context files.[1]
  - The same zipped skill that you upload in the web app can be placed here and used by Claude Code and Agent SDK agents; skills are **portable** across environments.[1]
- Example project:
  - Kenny’s personal assistant project has:
    - `claude/` folder containing sub‑directories for **subagents**, **commands**, and **skills**.[1]
    - Skills include:
      - The cohort analysis skill.
      - Anthropic’s default Excel skill (pulled from the public skills repo).
      - A custom **YouTube thumbnail** skill.[1]

***

## Anthropic default skills repo

- Anthropic maintains a **skills repo** with default skills such as:
  - Document skills for PDFs, docs, PowerPoint, Excel.
  - Skill creator and other utility skills.[1]
- Developers can inspect these skills to:
  - Understand recommended structure for `skill.md`.
  - See how Anthropic organizes required vs optional context.
  - Copy or modify these skills into their own `skills/` directory.[1]

***

## Example: YouTube thumbnail skill

This skill encapsulates Kenny’s entire YouTube thumbnail creation workflow, including external tools and templates.[1]

### Skill structure and context

- `skill.md`:
  - YAML: skill **name** and a detailed **description** explicitly stating:
    - What the skill does: create or edit YouTube thumbnails.
    - When the agent should use it: when the user asks to create a thumbnail from scratch or edit an existing one.[1]
  - At the top of the body, a **table of contents** of all relevant context files with inline explanation of what each file contains and when to use it (not just file names).[1]
  - Files in the skill context:
    - **Required reading** (always loaded):
      - `design-requirements.md` (or similar): design rules and constraints drawn from Kenny’s VidIQ lessons, including thumbnail best practices.[1]
      - `prompting-guidelines.md` for the **Nano Banana** image model: best practices and patterns for prompting Nano Banana effectively.[1]
    - **Optional assets** (loaded only if needed):
      - Icons, Kenny’s headshot, template images, stored outside the skill folder but referenced in `skill.md` with descriptions of what they are and when to use them.[1]
      - A templates document listing proven thumbnail templates; only loaded if the agent chooses to generate from a template rather than from scratch.[1]

- Progressive disclosure pattern inside the skill:
  - `skill.md` marks certain files as **mandatory** (e.g., design requirements, prompting guidelines) and others as conditional, depending on whether the agent decides to use templates or certain assets.[1]
  - The agent decides at runtime whether to:
    - Use a predefined thumbnail template (and load the templates file).
    - Or design from scratch (skipping the template file).[1]

### Operational workflow with the thumbnail skill

- Kenny maintains a project structure with a **YouTube folder** containing an `episodes/` directory.[1]
- For each episode, he creates a `research.mmd` file containing:
  - A list of top competitor videos for the topic (e.g., top 5 “Claude skills” YouTube search results with URLs).[1]
- Prompting flow:
  1. He asks the assistant to propose **titles + thumbnail concepts** for a new YouTube video about Claude Skills, pointing the assistant to the `research.mmd` file.[1]
  2. The assistant:
     - Uses the **context system** (see next section) to:
       - Traverse `cloud.md` files for memory and projects.
       - Use the YouTube analytics MCP to fetch metadata and thumbnails for the competitor videos.[1]
     - Because Claude is multimodal, it can inspect competitor thumbnails visually to extract patterns for high CTR designs.[1]
  3. The assistant outputs multiple combined title + thumbnail concepts (e.g., “The only Claude Skills guide you need – from zero to expert”) with short descriptions of the visual concept, but does **not yet** run the thumbnail‑generation skill.[1]
  4. Kenny selects preferred concepts (e.g., options 1 and 2) and asks the assistant to:
     - Add the selected title + thumbnail concepts back into the `research.mmd` document.
     - Then create actual thumbnails using the thumbnail skill.[1]
  5. The assistant:
     - Updates the research doc with the chosen concepts.
     - Invokes the thumbnail skill, which:
       - Loads required design requirements and Nano Banana prompting guidelines.
       - Loads templates or assets as needed.
       - Constructs a detailed prompt.[1]
     - Uses Claude Code’s ability to run terminal commands to:
       - Call a **Gemini CLI**, which is wired to a **Nano Banana MCP** server, to generate thumbnail images.[1]
  6. Outputs:
     - File paths for the generated thumbnails (two versions corresponding to the chosen concepts).
     - Kenny opens them from the terminal to inspect and iteratively refine (via further prompting).[1]

- Observed results:
  - Some generated thumbnails are mediocre and need human editing; others are good starting points, especially with patterns like before/after splits and clear text overlays.[1]
  - Kenny treats the AI outputs as first drafts; he may adjust the prompt or post‑process images (e.g., face swap, emphasis tweaks).[1]

***

## Context system and project organization (personal assistant)

Kenny’s personal assistant uses a structured **context system** to manage memory, projects, and tools via progressive traversal of markdown files.[1]

- Directory layout (within a context folder, e.g., `context/`):
  - `claude.md` (top‑level context controller):
    - Describes how the context system works.
    - Explains that there are subsystems for **memory**, **projects**, and **tools**, each in its own subdirectory.
    - Directs the agent to always read `claude.md` at the root of each subsystem before using it.[1]
  - `memory/claude.md`:
    - Explains how the memory system works; details not fully shown in the transcript, but referenced as something the agent must read first.[1]
  - `projects/claude.md`:
    - Lists all projects with short descriptions.
    - For each project, there is a folder with its own `claude.md` plus additional context files.[1]
  - `tools/claude.md`:
    - Describes available tools and how to use them; again, the agent is required to read this before using tools.[1]

- Example: **YouTube project**:
  - Under `projects/` there is a `YouTube/` project folder with its own `claude.md`, which lists:
    - `project-overview.md` for channel overview and goals.
    - `youtube-studio.md` for detailed operational context.[1]
  - The agent can decide whether it needs to read these deeper files depending on the task.[1]

- Operational pattern:
  - On startup, the assistant reads:
    - Top‑level `claude.md` for context system rules.
    - Then each subsystem’s root `claude.md` (memory, projects, tools) before diving into specific items.[1]
  - As tasks evolve, the agent selectively traverses deeper, reading only the relevant project or memory files, preserving tokens while still giving itself rich context when needed.[1]

***

## Optimizing and iterating on skills

- When a custom skill misbehaves or fails:
  - Kenny treats the process as **vibe coding**:
    - Tell Claude: “The skill failed because of X; here is the expected vs actual output.”
    - Ask it to review the entire skill (including scripts) and identify likely failure points.
    - Have it propose and implement concrete fixes in the skill files.[1]
- This iterative loop is used to:
  - Tighten instructions in `skill.md`.
  - Improve validation logic.
  - Refine prompts for external tools (e.g., Nano Banana).[1]

***

## Operational patterns and setups

### Multi‑entity flows (agents, skills, MCPs, tools)

- **Excel cohort model composition**:
  - Entity A: **Anthropic Excel skill** (default skill).
  - Entity B: **Custom cohort analysis skill** that delegates basic Excel operations to the default skill.
  - Entity C: **Validation scripts** (Python) invoked by the skill instructions.
  - Flow: agent uses the cohort skill → cohort skill leverages the default Excel skill to write formulas and structure the sheet → cohort skill runs Python validators to ensure no formula errors before returning the final artifact.[1]

- **YouTube thumbnail creation pipeline**:
  - Entity A: **YouTube analytics MCP** for retrieving competitor stats and thumbnails.
  - Entity B: **Custom context system** (memory/projects/tools via `claude.md` files) to locate the relevant YouTube project files and episode research doc.
  - Entity C: **YouTube thumbnail skill**, which encapsulates design rules, prompting guidelines, and asset management.
  - Entity D: **Gemini CLI** wired to **Nano Banana MCP** to actually generate images.
  - Flow: user prompt → assistant reads project context and research doc → uses YouTube MCP to fetch competitor data → proposes title + thumbnail concepts → writes selected concepts into research doc → calls YouTube thumbnail skill → skill constructs prompts and triggers terminal commands → Gemini CLI calls Nano Banana MCP → images generated → assistant returns file paths.[1]

- **Personal assistant startup flow**:
  - Entity A: top‑level `claude.md` for the context system.
  - Entity B: subsystem controllers: `memory/claude.md`, `projects/claude.md`, `tools/claude.md`.
  - Entity C: project‑specific `claude.md` and docs (e.g., YouTube project).
  - Flow: assistant starts → reads top‑level context rules → reads each subsystem’s `claude.md` for governance on memory/projects/tools → as tasks require, traverses into specific project docs and skills to load only relevant context.[1]

### Automation patterns (triggers, pipelines, hooks)

- **Skill invocation triggers**:
  - In Claude app and Claude Code, skills are not manually triggered by the user (unlike slash commands); the **agent decides** when to call a skill based on:
    - The skill’s description metadata.
    - The current conversation/task.
  - Example triggers:
    - Any request to build cohort models from transactions data triggers the **cohort analysis skill**.
    - Requests to generate or edit a YouTube thumbnail trigger the **thumbnail skill**.[1]

- **Scheduled/phase‑based context traversal**:
  - On initialization, the assistant always reads:
    - Global context rules (`claude.md`).
    - Then memory/projects/tools controllers before any deeper context, effectively a **startup hook**.[1]

- **Tool + MCP pipelines**:
  - Thumbnail creation uses a pipeline:
    - Claude decides on design → calls a skill → the skill runs **bash commands** via Claude Code → these commands call an external CLI (Gemini) → Gemini is connected to Nano Banana MCP, which generates images.
  - Validation in the cohort skill is implemented as a pipeline step: **post‑generation hook** that runs Python scripts to validate formulas.[1]

- **Human‑in‑the‑loop checkpoints**:
  - Before running certain commands (e.g., the Gemini CLI for thumbnail generation), Claude presents the constructed command and waits for Kenny to approve (e.g., “Yes, run it”).[1]
  - Thumbnail outputs are treated as drafts; Kenny manually reviews, edits, or re‑prompts as needed.[1]

### Guardrail artifacts (docs, configs, policies)

- **Skill metadata and required reading**:
  - Each skill’s YAML `description` acts as a guardrail by defining:
    - The skill’s scope.
    - Conditions under which the agent **should** or **should not** use it (e.g., only when user requests thumbnails from scratch or edits).[1]
  - Required reading files (e.g., design requirements, prompting guidelines) encode hard rules:
    - Thumbnail must follow certain visibility and CTR best practices.
    - Prompts to Nano Banana must follow recommended structures.[1]
  - Enforcement:
    - `skill.md` clearly marks certain docs as “required reading” and instructs the agent to read them **every time** the skill runs.[1]

- **Context system controllers (`claude.md`)**:
  - Top‑level and subsystem `claude.md` files define policies for:
    - How memory is used and updated.
    - How projects are organized and referenced.
    - How tools are to be invoked and in what order.[1]
  - Enforcement:
    - The assistant is explicitly instructed to read these controllers before performing operations in that subsystem, so all subsequent behavior is conditioned on these guardrail docs.[1]

- **Validation scripts as guardrails**:
  - Python validation scripts for the cohort model encode rules like “no Excel formula errors allowed in the final model.”
  - Enforcement:
    - The skill instructions mandate running validators after formula insertion and before returning the artifact, effectively blocking bad outputs from silently passing through.[1]

- **Human approval as a policy**:
  - Certain operations (e.g., running heavy external CLIs, generating images) are gated by a direct user confirmation step in the Claude Code terminal.[1]
  - This keeps high‑impact actions under **reviewer‑only** control rather than allowing fully autonomous execution.[1]

***

## Practical recommendations

- **Set up a skill system with progressive disclosure**:
  - Create a `skills/` folder in your Claude Code or Agent SDK project.
  - For each capability (e.g., financial modeling, thumbnail generation), create a dedicated skill folder with:
    - `skill.md` containing clear `name` and **narrow** `description` specifying exact triggers and scope.
    - A body that lists context files in a short “table of contents,” explicitly marking which docs are **required** vs optional.[1]

- **Use skills to orchestrate other tools instead of stuffing everything into the system prompt**:
  - Move complex workflows out of direct prompts and into skills that:
    - Call MCP tools.
    - Run bash/Python via Claude Code.
    - Load markdown/CSV context selectively.[1]
  - Keep system prompts lean and let skills handle heavy instruction sets.

- **Compose skills on top of existing Anthropic skills**:
  - Import Anthropic’s default skills (e.g., Excel, PDFs) into your project.
  - Build custom skills that:
    - Delegate base operations (spreadsheet manipulation, document parsing) to these defaults.
    - Add domain‑specific logic and validation via additional scripts.[1]

- **Add validation hooks for high‑risk outputs**:
  - For anything formulaic or structural (spreadsheets, code, configs), include:
    - Post‑generation validators (Python scripts or unit tests).
    - Skill instructions that require running validation before returning results.
  - Treat failing validations as blocking conditions that trigger repair attempts, not as warnings.[1]

- **Design a context system with controller docs**:
  - Create a top‑level `claude.md` describing:
    - Your memory, projects, and tools subsystems.
    - Rules for how the agent should read and traverse context.
  - In each subsystem (`memory/`, `projects/`, `tools/`), add a `claude.md` that:
    - Explains what lives there.
    - Defines how the agent should use or update that subsystem.[1]
  - Instruct agents (in their main system prompt or bootstrap context) to always read these controller docs before doing work.

- **Centralize design and prompting guidelines into guardrail docs**:
  - For any repeated artifact type (e.g., thumbnails, reports, dashboards), create:
    - A design requirements doc (what “good” looks like).
    - A prompting guidelines doc for the external model(s) used.[1]
  - Reference these docs in your skills as **mandatory** reading each time they run, so improvements to the docs propagate instantly to all usage.

- **Keep high‑impact external commands under human review**:
  - In skills that call CLIs or external systems:
    - Have the agent print the command and ask “Run? (yes/no)” before execution.
    - Treat these skills as **reviewer/critic** plus command generator, not fully autonomous actors, especially for anything that writes to production systems or expensive APIs.[1]

- **Use research docs plus MCPs for competitive/contextual tasks**:
  - For workflows like content creation:
    - Maintain per‑task research markdown files listing key references (e.g., top competitor URLs).
    - Have skills or agents:
      - Use MCPs to fetch stats/assets from those references.
      - Analyze both text and images when multimodal models are available.
      - Store distilled insights and chosen options back into the same research doc for future runs.[1]

- **Iteratively improve skills via explicit failure reports**:
  - When a skill fails or underperforms:
    - Provide the agent with:
      - The failing output.
      - The expected output.
      - A statement that “this skill failed because of X.”
    - Ask it to audit the entire skill (instructions + scripts), propose fixes, and apply them.
  - Treat skill development as continuous **vibe coding** rather than one‑shot configuration.[1]
