---
title: "You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, "
date: "2026-02-25"
mode: "COPILOT"
uuid: "11ea7efe-1e9f-4bdf-9185-9727e849e3ac"
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

Here’s a cleaned, rewritten version of the substantive content, focused on technical workflows, configurations, and patterns for Claude Agent Skills and Kenny’s personal assistant setup.[1]

***

## Core concept of Claude Skills

- Claude Skills address a **context engineering** problem: traditionally, all tool schemas and MCP docs are loaded into the system prompt, even though only a small subset is used for any given task, wasting tokens and limiting total capabilities you can load.[1]
- Skills introduce **progressive disclosure**: only a skill’s name and description are initially loaded; the full body (detailed instructions, context, scripts) is only read when the agent decides to use that skill.[1]
- Skills are implemented as a folder containing at minimum a `skill.md` file with YAML front matter (`name`, `description`) plus an instruction body; optional additional context (scripts, markdown, CSVs, other data) can live alongside it.[1]
- The **description** field is crucial: it tells Claude what the skill does and when it should be used, similar to tool descriptions.[1]

***

## Skills vs slash commands vs MCPs

- **Slash commands** and skills both define workflows via prompts, but:
  - Slash commands must be triggered manually by the user.
  - Skills are invoked **autonomously by the agent**, including deciding when to call them and what input arguments to use after gathering context via tools/MCPs.[1]
- Using skills instead of slash commands lets you **offload pre‑work** (research, argument construction, tool calls) from the user to the agent.[1]
- **MCPs** can do everything skills can (tools, resources, prompts), but differ in:
  - Complexity: MCPs require server infrastructure and client wiring; skills are just markdown + optional scripts.[1]
  - Context behavior: MCP tools and docs are usually fully loaded into the system prompt, while skills only expose name/description until invoked.[1]
- Kenny notes that progressive disclosure *could* be implemented for MCPs (only list connected MCPs, then progressively load tools and docs), and he has implemented this pattern in custom agents, but Claude’s default MCP integration does not currently behave this way.[1]

***

## Benefits and design patterns of Skills

- **Token and context efficiency**: by loading only minimal metadata up front, you can pack far more capabilities into one agent than with always‑on tools/MCP schemas.[1]
- **Simplicity**: implementing a skill is “just” building a `skill.md` plus any supporting files; no server to deploy.[1]
- **Power via composition**:
  - Skills can call tools and scripts (e.g., Python, bash).
  - Skills can **leverage other skills**, allowing higher‑level skills to be built on top of default or existing ones instead of re‑implementing functionality.[1]
- Example: an **Excel model builder skill** that uses Anthropic’s default Excel skill, stacking its logic on top of Anthropic’s baseline implementation.[1]

***

## Using Skills in Claude.app (web/desktop)

### Enabling and uploading skills

- In Claude’s UI, skills are managed under **Settings → Capabilities → Skills**.[1]
- Anthropic ships a set of **default skills** (e.g., skill creator, document skills like PDF/Excel/PowerPoint tools) that are initially disabled; you must explicitly enable the ones you want.[1]
- You can **upload custom skills** by providing a ZIP file containing:
  - A top‑level skill folder.
  - A valid `skill.md` with YAML `name` and `description` or upload will fail.
  - Any supporting directories like `scripts/`.[1]
- The same skill folder can be zipped for Claude.app or placed directly under `cloud/skills` for Claude Code, which makes skills portable across environments.[1]

### Example: Cohort analysis skill

- Kenny created a **cohort analysis skill** that:
  - Accepts a CSV of transactions and builds an Excel‑format cohort model from it.[1]
  - Encodes domain‑specific instructions in `skill.md` about how to construct the model.[1]
- Workflow when using this skill in Claude.app:
  - Upload a CSV with ~20,000 transactions from ~1,000 customers.[1]
  - Ask Claude: “Build a cohort model” and rely on the skill for all implicit domain logic.[1]
  - Claude:
    - Inspects the CSV to infer structure.
    - Recognizes the cohort analysis skill as relevant from its description, reads the full skill body, and follows those instructions.[1]
- Output:
  - Produces an Excel file (openable in Google Sheets) with:
    - A raw data sheet plus added derived columns.
    - A model sheet with:
      - Input assumption controls at the top that drive the rest of the model via formulas.
      - Cohort tables (by first transaction date) with metrics like retention matrices, customer counts, transaction counts, average transactions per customer, total revenue, lifetime value (LTV), and CAC‑adjusted LTV.[1]
  - All cells are formula‑driven; adjusting assumptions updates the model live.[1]

### Formula validation scripts

- In the cohort analysis skill’s `scripts/` folder, Kenny includes **Python validation scripts** that:
  - Run after the model’s formulas are inserted.
  - Check that there are **no formula errors** in the spreadsheet.[1]
- The instructions in `skill.md` specify when to invoke these validation scripts, providing an automated sanity check on formula integrity.[1]

***

## Using Skills in Claude Code and Claude Agent SDK

### Directory structure and loading

- In a Claude Code project with a custom agent built using the Claude Agent SDK, Kenny uses the following pattern:[1]
  - A `cloud/` directory containing:
    - Subfolders for `subagents`, `commands`, etc.
    - A **`skills/` folder**, with one folder per skill (e.g., `cohort_analysis/`, `excel/`, `youtube_thumbnail/`). Each skill folder contains its own `skill.md` and optional `scripts/`.[1]
- The same cohort analysis skill used in Claude.app is simply placed here; no changes required, highlighting portability.[1]
- Anthropic’s skills repo (e.g., default Excel skill, document skills for PDFs/docs/PowerPoint/Excel) can be cloned and those skills dropped into `cloud/skills` for reuse.[1]

### Personal assistant context system

- Kenny’s **personal assistant agent** uses an explicit context system based on markdown files and progressive disclosure:[1]
  - A `cloud/context/` directory with a root `claude.md` describing the context system and subsystems.[1]
  - Subdirectories for:
    - `memory/`
    - `projects/`
    - `tools/`
  - Each of these has its own `claude.md` describing how that subsystem works and how context should be managed.[1]
- At startup, the agent:
  - Loads `cloud/context/claude.md` first to understand high‑level context architecture.[1]
  - Then reads the root `claude.md` in each subsystem directory to learn how to use memory, projects, and tools.[1]

### Project‑level context traversal

- Under `cloud/context/projects/`, each project is a folder with its own context:[1]
  - Example: a `YouTube/` project folder.
  - The projects‑root `claude.md` lists all projects and includes brief descriptions for each.[1]
  - Inside `YouTube/`, there is another `claude.md` and additional markdown files like `project_overview.md` and `youtube_studio.md` with deeper details.[1]
- Traversal pattern:
  - Agent starts from `projects/claude.md` to discover available projects and short summaries.[1]
  - When it needs more info on a project (e.g., YouTube), it opens `YouTube/claude.md`.[1]
  - If still more detail is needed, it reads `project_overview.md`, `youtube_studio.md`, etc., progressively loading only what’s required.[1]
- Kenny emphasizes designing this kind of **structured, layered context** so agents can stay token‑efficient while still having rich, discoverable context.[1]

***

## Custom YouTube thumbnail skill

### Skill structure and content

- Kenny’s **YouTube thumbnail skill** lives in a skill folder (under `cloud/skills` or zipped for Claude.app) with a `skill.md` that includes:[1]
  - A `name`.
  - A detailed `description` specifying:
    - What the skill does (create or edit YouTube thumbnails).
    - When it should be used (any time the user asks for a new thumbnail or wants to edit an existing one).[1]
- At the top of the skill body, he includes a **table of contents** listing all relevant context files and what they contain, so the agent can quickly decide what to read.[1]
- He explicitly distinguishes between:
  - **Required reading**: always loaded when the skill is used, e.g.:
    - `design_requirements.md`: detailed thumbnail design rules derived from VidIQ thumbnail optimization lessons, including layout, text, contrast, click‑through considerations, etc.[1]
    - `prompting_guidelines.md`: best practices for prompting the Nano Banana image model, which must always be followed.[1]
  - **Optional assets**: only loaded if relevant, e.g.:
    - Icon library.
    - Headshot images.
    - Template files for thumbnails.
    - These can be located outside the skill folder; the skill can point to arbitrarily located context as long as paths are specified.[1]

### Template usage and progressive disclosure

- A separate file (e.g., `thumbnail_templates.md`) contains:
  - Descriptions of proven thumbnail template patterns that can be reused.[1]
- The agent only reads the template file when it decides to **create from a template**; if it opts to design from scratch, that file is never loaded.[1]
- This is a concrete example of progressive disclosure inside a single skill:
  - Mandatory design requirements and prompting guidelines are always read.
  - Optional assets and templates are conditional, based on the agent’s chosen workflow.[1]

***

## End‑to‑end thumbnail generation workflow

### Research document and prompt setup

- For a specific YouTube episode, Kenny creates a `research.md` (or `.mmd`) file under a YouTube `episodes/` directory.[1]
- He:
  - Searches YouTube for “Claude skills”.
  - Copies the top 5 video results into `research.mmd` as competitor examples.[1]
- He then prompts his personal assistant:
  - Ask for title and thumbnail ideas for a video about Claude skills.
  - Pass the research doc so the agent can analyze top‑ranking videos and thumbnails.[1]

### Context and MCP integration

- The agent’s context system:
  - Checks memories and project context.
  - Navigates to the YouTube project context.\n- The agent calls **YouTube analytics MCP tools** to fetch data on the competitor videos listed in the research doc.[1]
- It:
  - Uses curl commands to download competitor thumbnails.
  - Leverages Claude’s multimodal capability to visually analyze those thumbnails.[1]
- This analysis is used to infer patterns that drive **high CTR thumbnails and titles**, which then inform the concepts it proposes.[1]

### Concept generation

- The agent proposes several **title + thumbnail concept pairs**, including:[1]
  - Example concept: “Cloud skills changed my workflow forever. Here’s how.” (unfair‑advantage angle).[1]
  - Example concept: “The only Claude skills guide you need: from zero to expert.” (complete‑system angle).[1]
- For each option, it gives a short thumbnail concept (not the full Nano Banana prompt yet, just the idea and composition).[1]
- Kenny selects preferred options (e.g., options 1 and 2) and instructs Claude to:
  - Add them to the research doc.
  - Generate the thumbnails using the custom skill.[1]

### Skill invocation and image generation pipeline

- Once instructed to create thumbnails, the agent:
  - Uses the thumbnail skill to:
    - Look up available **thumbnail templates**.
    - Decide which template(s) to apply.[1]
  - Constructs rich prompts for Nano Banana, using:
    - The design requirements file.
    - Prompting guidelines.
    - Any chosen templates and assets (e.g., icons, headshot).[1]
- Execution flow:
  - Claude Code runs terminal commands to invoke the **Gemini CLI**, which connects to the **Nano Banana MCP server** for image generation.[1]
  - For each concept, the agent:
    - Proposes the full prompt and asks Kenny to confirm running it.
    - Upon confirmation, runs the CLI command and generates thumbnails via Gemini + Nano Banana.[1]
- After generation:
  - The agent updates the research document with **file locations** for each generated thumbnail so Kenny has both concepts and asset paths in one place.[1]
- Kenny manually opens the generated images (e.g., via `open` command) to review quality and iterate on prompts as needed.[1]

### Quality and iteration

- Kenny notes that quality can vary:
  - Some thumbnails are weak and need editing or better prompting.
  - Others are strong starting points (e.g., before/after layouts, “Human override” concept, split comparisons).[1]
- Workflow for improvement:
  - Manually review thumbnails to see what worked and what didn’t.
  - Iteratively refine the thumbnail skill’s prompting guidelines and templates.
  - Use Claude to review failures and suggest prompt or skill changes.[1]

***

## Optimizing and iterating on Skills

- When a skill **fails** or behaves unexpectedly, Kenny:
  - Tells Claude (or another coding copilot like Cursor) that the skill failed and why.
  - Provides the expected vs actual output.
  - Asks it to:
    - Review the entire skill (including scripts).
    - Identify probable failure points.
    - Propose improvements.
    - Implement fixes directly.[1]
- This **vibe‑coding** loop is used to iteratively refine skills just like any other codebase, converging toward stable, reliable behavior.[1]

***

## Operational patterns and setups

### Multi‑entity flows (agents, skills, tools, MCPs)

- **Claude.app with custom skills**:
  - User provides data (e.g., CSV).
  - Agent chooses the appropriate skill (e.g., cohort analysis).
  - Skill orchestrates internal tools (Excel skill, validation scripts) to produce a complete model.[1]
- **Personal assistant with project context + skills**:
  - Core agent uses a context system in `cloud/context/` to progressively load memory, project, and tool specs.
  - For YouTube work:
    - Agent navigates from root context → projects → YouTube project → project overview and YouTube studio docs.
    - Agent reads `episodes/research.mmd`.
    - Agent uses YouTube analytics MCP tools to enrich context.
    - Agent calls the YouTube thumbnail skill to generate prompts and images.
    - External image generation is executed via Gemini CLI, which is itself connected to the Nano Banana MCP server.[1]
- **Skill‑on‑skill composition**:
  - Higher‑level skills (e.g., Excel model builder) build on top of Anthropic’s default Excel skill, effectively using that as a lower‑level capability.[1]

### Automation patterns (triggers, pipelines, hooks)

- **Context system bootstrapping**:
  - On startup, the agent automatically:
    - Reads `cloud/context/claude.md`.
    - Reads subsystem root `claude.md` files under `memory/`, `projects/`, and `tools/` before doing any work.
  - This ensures it always understands the current memory/project/tool architecture before acting.[1]
- **Project context traversal**:
  - The agent does not automatically load all project details.
  - Instead, it follows a **phased traversal**:
    - Root projects list → project stub → deeper project docs only when needed.
  - This acts as an implicit hook: more detailed docs are only read when the task requires them, preserving context budget.[1]
- **Skill activation rules**:
  - Skills are only considered when:
    - The user request matches usage criteria stated in the skill description (e.g., “create or edit a YouTube thumbnail”).
    - The agent identifies them as relevant based on metadata; only then does it load the full body of the skill.[1]
- **Validation hook in cohort skill**:
  - After generating a model:
    - The skill instructions require running Python validation scripts to check for formula errors before the model is considered complete.
  - This functions as a **post‑generation guard** to catch failures.[1]
- **Thumbnail generation confirmation**:
  - When the thumbnail skill constructs a Gemini CLI command:
    - Claude asks for explicit user confirmation before executing the command.
    - This separates planning (prompt construction) from execution (calling the external image pipeline).[1]

### Guardrail artifacts (docs, configs, policies)

- **Design requirements doc (YouTube thumbnails)**:
  - Encodes non‑negotiable design rules (layout standards, contrast, copy length, CTR principles) drawn from VidIQ lessons.[1]
  - All thumbnail generations must read and apply these requirements; the skill marks this file as required reading.[1]
- **Prompting guidelines doc for Nano Banana**:
  - Encodes best practices for interacting with the Nano Banana model (structure of prompts, style cues, constraints).[1]
  - Also required reading for every thumbnail generation invocation.[1]
- **Context system docs (`claude.md` files)**:
  - `cloud/context/claude.md`:
    - Defines the overall context system, including subsystems (memory, projects, tools) and how context should be managed.[1]
  - Subsystem `claude.md` files (e.g., under `projects/`, `memory/`, `tools/`):
    - Specify how each subsystem should be used, what files exist, and which to read first.[1]
  - These work as **governance documents** for how the agent navigates and loads context.
- **Skill definitions (`skill.md`)**:
  - Act as both capability definition and **governance** for when/how a skill is allowed to run.
  - They specify:
    - Usage criteria.
    - Required and optional context files.
    - When to call scripts or external tools.
    - Which steps require explicit user confirmation (e.g., running Gemini CLI).[1]

***

## Practical recommendations

- Set up a **skills directory** (`cloud/skills/`) where each skill has:
  - A `skill.md` with a concise `name` and a precise `description` that states when it should be used.
  - An internal table of contents section that labels **required** vs **optional** context files and explains what each contains.[1]
- For complex skills (e.g., reporting, modeling, asset creation), split context into:
  - Always‑read **guardrail docs** (design requirements, prompting guidelines, domain rules).
  - Conditionally‑read assets (templates, examples, external datasets), referenced by path so the agent can decide when to load them.[1]
- Use **progressive disclosure everywhere**:
  - Only load minimal metadata (names/descriptions) into the system prompt.
  - Let the agent decide when to open deeper context or optional files, both in skills and in your project context system.[1]
- Build a **context governance layer**:
  - Create a root `context/claude.md` that defines subsystems (memory, projects, tools) and how context is managed.
  - Add subsystem `claude.md` files describing how to use each subsystem and which docs must be read first.
  - Require your agents to read these governance docs at startup before interacting with user tasks.[1]
- For multi‑agent / multi‑tool pipelines:
  - Chain **skills → tools/MCPs → external CLIs**:
    - Use skills to plan workflows and construct tool/CLI calls.
    - Use MCPs for data retrieval and structured external services.
    - Use CLIs for heavy operations like image generation, and keep these behind explicit user confirmation.[1]
- Add **post‑generation validation hooks** for high‑risk outputs:
  - For spreadsheet or code‑generating skills, write validation scripts (e.g., Python) and make them mandatory at the end of the skill workflow to catch formula or logic errors before outputs are “final”.[1]
- Treat skills as **evolving artifacts**:
  - Whenever a skill misbehaves:
    - Log the failure with expected vs actual output.
    - Use Claude (or your IDE agent) to review the skill and propose edits.
    - Incorporate changes and re‑test, just like normal code review and refactor cycles.[1]
- Centralize your **design and prompting principles**:
  - Keep a single design requirements doc and a single prompting guidelines doc per domain (e.g., thumbnails, finance models).
  - Mark them as required reading in relevant skills and reference them at every process stage where those types of assets are created.[1]
- Prefer **skill‑on‑skill composition** over monolithic skills:
  - Reuse Anthropic’s default skills (e.g., Excel, docs) as lower‑level building blocks.
  - Build domain‑specific orchestrator skills that call these defaults, plus your own scripts, for more advanced workflows.[1]
