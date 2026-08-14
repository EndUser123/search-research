---
title: "You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, "
date: "2026-01-17"
mode: "COPILOT"
uuid: "ad181e37-eb39-445e-861e-02aa0fee5b1b"
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

Claude Code + n8n MCP: cleaned workflow summary (technical domain)[1]

## Core idea

Building n8n automations directly in n8n is treated as a legacy pattern; instead, use **Claude Code** plus the **n8n MCP server** and **n8n Skills** to design, generate, and iteratively refine workflows as part of a broader product ecosystem (frontends, backends, databases, payments).[1]

***

## System components and roles

- **Claude Code**
  - Primary environment for:
    - Planning agent/automation architecture in “plan mode”.
    - Prompt-driven generation of n8n workflows and JSON.
    - Iterative debugging and direct editing of existing n8n workflows through MCP tools.[1]
  - Stores skills as custom instructions that sit *outside* the system prompt so they do not consume context tokens.[1]

- **n8n MCP server (community implementation by czlonkowski)**
  - Not an official n8n MCP; community-built.[1]
  - Exposes:
    - Access to 500+ n8n nodes, their properties, and documentation.[1]
    - A template library with ~2,700 workflows and real‑world examples.[1]
  - Enables Claude Code to:
    - Search nodes and examples.
    - Inspect schemas and prior workflows when designing new automations.
    - Edit or create workflows directly in the connected n8n instance.[1]

- **n8n Skills (Claude Code skills repo)**
  - A set of seven skills that define *how* Claude should use the n8n MCP server.[1]
  - Function as an instruction manual for MCP:
    - Guide tool selection, search patterns, and workflow creation routines.[1]
  - Installed **globally** so they can be reused across any Claude Code project that uses the same n8n MCP server.[1]

- **Target example system**
  - A multimodal “nutrition tracking” and broader “accountability” AI agent:
    - User interacts mainly via Telegram (voice or text).[1]
    - System estimates calories and macro breakdowns and logs them into a database (Supabase).[1]
    - This logging workflow is envisioned as a base layer for future frontends, backends, dashboards, and SaaS packaging with payments.[1]

***

## Setup workflow: linking Claude Code, n8n MCP, and n8n Skills

### 1. Project and MCP config in Claude Code

- Create a new Claude Code project folder (e.g., `n8ncc_tutorial`) and add a file named **exactly** `mcp.json`.[1]
- From the `n8n-mcp` GitHub repo, copy the **“full configuration with n8n management tools”** example and paste it into `mcp.json`.[1]
- Edit configuration values:
  - **n8n API URL**
    - In your n8n instance, copy the base URL *before* `/home` (e.g., `https://your-n8n-hostinger.cloud`).[1]
    - Paste this into the `apiUrl` field and remove any trailing slash so it matches the expected format.[1]
  - **n8n API key**
    - In n8n, go to:
      - Settings → n8n API → Create API key.[1]
    - Copy the key and paste into the `apiKey` field in `mcp.json`.[1]

- OS‑specific command configuration:
  - **macOS / WSL / Unix‑like**
    - Keep the default `command: "npx"` and args from the example.[1]
  - **Native Windows (not WSL)**
    - Change:
      - `command` to `cmd`.[1]
      - `args` to something like: `["/c", "npx", "mcp"]` (described in the video as `for/ cnpx mcp`, but the key is invoking npx via cmd with proper arguments).[1]
    - This is required so the MCP server can be started correctly on native Windows.[1]

- Restart Claude Code:
  - If Claude Code is already running, execute `/exit` then restart so it reloads the new MCP configuration.[1]
  - Run `/mcp` in Claude Code and verify that the `n8n-mcp` server shows as connected.[1]

### 2. Installing n8n Skills into Claude Code

- From the `n8n-skills` GitHub repo:
  - The “install via marketplace” method may not show up in the marketplace or may fail.[1]
  - Use the **manual installation** instructions provided in the repo.[1]

- Recommended installation method:
  - In Claude Code, send a prompt similar to:
    - “I need to install the skills from this repo. Here were the manual instructions they gave me:” followed by pasting the manual install snippet from the GitHub README.[1]
  - Let Claude Code execute the necessary file and config operations to install the skills.[1]
  - After installation, Claude should confirm that **all seven n8n skills** have been installed.[1]

- Repo cleanup and global skills:
  - Manual install clones the entire repo into your current project.[1]
  - To avoid clutter:
    - Prompt Claude Code to remove the cloned `n8n-skills` repo folder from your project while keeping the skills installed globally.[1]
  - Global install means the skills are accessible from any Claude Code project that uses the same environment.[1]

***

## Prompting style and build flow in Claude Code

### 1. Plan mode for new automations

- When starting any new workflow or agent:
  - Switch Claude Code to **plan mode**.[1]
- Usage pattern:
  - Provide a high‑level description of the target automation, including:
    - Interfaces (e.g., Telegram text + voice).[1]
    - Required transformations (e.g., calorie/macro extraction).[1]
    - Storage and integrations (e.g., Supabase logging).[1]
  - Have a back‑and‑forth with Claude in plan mode to:
    - Validate mutual understanding of the goal.
    - Let Claude propose an architecture and node selection.
    - Clarify preferences (model choice, JSON vs direct creation, etc.) *before* it touches n8n.[1]

- Benefits:
  - Claude Code “knows the questions to ask”:
    - Helps non‑technical or semi‑technical users who “don’t know what they don’t know”.[1]
    - Surfaces key decisions (model, credentials, where to deploy the JSON) explicitly.[1]

### 2. How Claude uses MCP and Skills during planning

- Claude Code uses MCP tools to:
  - Call `n8n-mcp` search endpoints like `search_node` repeatedly while planning.[1]
  - Inspect available nodes, properties, and documentation, and look up real‑world workflows in the 2,700‑workflow template library.[1]
- The n8n Skills:
  - Guide Claude on:
    - Which MCP tools to call and in what order.
    - How to interpret n8n node schemas and examples.
    - How to construct coherent workflows rather than blindly calling tools.[1]

### 3. Workflow generation preferences

- During planning, Claude asks:
  - Whether to:
    - Create the workflow directly inside the n8n instance via MCP.
    - Provide the workflow JSON for inspection.
    - Or both.[1]
- Preferred pattern chosen in the example:
  - Generate **both**:
    - A JSON definition of the workflow.
    - A corresponding workflow created automatically inside n8n (subject to payload size limits).[1]

- Large workflow limitation:
  - There is a size limit on API calls for creating/editing workflows; very large or complex workflows with huge JSON payloads may not be created automatically.[1]
  - Simpler workflows can be created directly via the MCP tools with no manual JSON import.[1]

***

## Example: multimodal nutrition tracking automation

### 1. High-level user goal

- User wants:
  - To message an AI system via Telegram (text or voice) about what they ate.[1]
  - System should:
    - Convert voice to text.
    - Estimate calories and break down macros.
    - Log results to a Supabase database.
    - Send a confirmation back on Telegram.[1]
  - This automation is one component of a larger “accountability AI” that:
    - Tracks various user behaviors.
    - Logs all events to a database.
    - Uses a dashboard or web app for visualization and, eventually, SaaS monetization (payments, multi‑user access).[1]

### 2. Claude’s proposed n8n flow

- Nodes and logic described:
  - **Trigger**
    - Telegram trigger node.[1]
  - **Branching**
    - IF node to check if the incoming message is voice or text.[1]
  - **Voice path**
    - If voice:
      - Download voice file.[1]
      - Use Whisper (via OpenAI) to transcribe audio into text.[1]
  - **Processing and logging**
    - Send the text (or transcribed text) to an AI model (OpenAI model chosen; user can later swap to another model like GPT‑4.1 or Claude variant).[1]
    - Extract meal details, calories, and macro breakdown from the model output.[1]
    - Insert the structured data into Supabase.[1]
  - **Feedback to user**
    - Send a confirmation message back to Telegram with summary or acknowledgment.[1]

- Node detail clarity:
  - Claude explains:
    - Which node types will be used.
    - The purpose of each node.
    - What needs to be configured manually (e.g., credentials).[1]

### 3. Post‑creation manual steps for the example

- After Claude reports that it “finished” and has created the workflow inside n8n:
  - Inspect the workflow in the n8n UI:
    - Review Telegram trigger, branch logic, Whisper, Supabase logging, and confirmation nodes.[1]
  - Add and configure credentials:
    - **Supabase**
      - In Supabase:
        - Create a new project.[1]
        - Go to **SQL editor** on the left; paste and run the SQL schema from Claude (from `supabase_schema.sql` Claude generated).[1]
        - For service role secret:
          - Project settings → API keys → Service role API keys → copy “service role secret”.[1]
        - For host URL:
          - Connect → App frameworks → copy the “Next public Supabase URL” and paste into the host field in the Supabase node.[1]
      - Save credentials in the n8n Supabase node.[1]
    - **Telegram**
      - Create a new bot via BotFather (implied; not step‑by‑step in transcript).[1]
      - Add Telegram credentials in the relevant n8n node (bot token etc.).[1]

- Activation and webhook:
  - Activate the workflow in n8n once all credentials are configured.[1]
  - Set the Telegram webhook as described by Claude in its step list (e.g., pointing Telegram to the n8n endpoint).[1]

### 4. Troubleshooting pattern using Claude Code

- When the first test (“I had one slice of pizza”) is sent through Telegram:
  - A Supabase error occurs.[1]
- Troubleshooting steps:
  - Copy the exact error message from n8n.[1]
  - Go back into Claude Code and provide:
    - The error message.
    - Context that this error is from the generated Supabase node in the current workflow.[1]
  - Claude Code’s advantage:
    - It has full context of:
      - The existing workflow graph.
      - Node configurations.
      - The generated schema.[1]
    - No need to manually upload JSON, screenshots, or re‑describe the workflow in a separate chat.[1]

- Root cause and fix (as described):
  - Original Supabase node had **no fields to send**.[1]
  - Claude Code:
    - Uses the MCP edit capability to update the node configuration.
    - Adds the necessary fields for data insertion to Supabase.[1]
  - After update:
    - Retry the “one slice of pizza” input.
    - Workflow runs end‑to‑end:
      - Logs successfully to Supabase.
      - Sends a confirmation message back via Telegram.[1]

- Iteration philosophy:
  - Continue iterating on the workflow (logic, mapping, error handling) until the workflow behavior is satisfactory.[1]

***

## Ecosystem and productization perspective

- Building in Claude Code + MCP shifts the focus from isolated “JSON workflows in a vacuum” to:
  - A **coherent ecosystem**:
    - Workflows in n8n.
    - Frontends and dashboards.
    - Backends and data stores.
    - Payment flows for SaaS.[1]
- Once Claude “knows every workflow, node, and connection” in a project:
  - It can:
    - Add additional workflows that integrate with earlier ones.[1]
    - Help scaffold:
      - Frontends.
      - Additional backend services.
      - Payment integration.[1]
- Example forward path:
  - Current video: create base nutrition tracking workflow via Claude + n8n MCP.[1]
  - Later videos planned:
    - Add frontend UI.
    - Flesh out backend.
    - Integrate payments to turn it into a SaaS.[1]

- Commenter feedback highlights:
  - One user reports:
    - They implemented a more complex weight‑loss workflow including age, weight, activity level, etc. using this method.[1]
    - Setup took ~10 seconds for initial steps and about 2 minutes to create a complete, fully documented workflow.[1]
    - They describe it as working “like a charm.”[1]
  - Another commenter reports:
    - They tried this method versus the built‑in n8n AI chat; in their case, n8n’s own AI chat worked better.[1]
    - They note this as a comparative performance observation, implying Claude + MCP may not always win for all use cases.[1]
  - Another commenter:
    - Reports issues installing the n8n MCP server initially but resolved them with help from Claude and Claude Code.[1]
  - Additional comment:
    - For some creative AI agency workflows (e.g., image manipulation chains), this approach produced extraneous steps (e.g., using a background remover when not needed), but they see high potential for CRM or RAG flows.[1]

- Limitations:
  - When workflows grow very large, token usage and size limits become pain points; a commenter specifically flags that “the problem starts when the workflow is too large and uses too many tokens.”[1]

***

## Operational patterns and setups

### Multi‑entity flows (Claude Code, n8n MCP, n8n, Supabase, Telegram, OpenAI/Whisper)

- **Design in Claude Code, execute in n8n**
  - Flow:
    - Describe the desired automation in Claude Code’s plan mode.[1]
    - Claude:
      - Uses n8n MCP search to identify appropriate nodes and templates.
      - Uses n8n Skills to orchestrate MCP calls.
      - Generates JSON and/or creates the workflow in n8n via MCP.[1]
    - User:
      - Configures credentials and tests the workflow in n8n.[1]

- **n8n MCP + Skills + template library**
  - MCP uses:
    - Node metadata (500+ nodes).
    - Template library (2,700 workflows).
    - Real‑world example schemas.[1]
  - Claude leverages this to:
    - Propose node sequences.
    - Model data shapes for inserts and API calls.[1]

- **Telegram ↔ OpenAI/Whisper ↔ Supabase**
  - End‑to‑end path in the nutrition example:
    - Telegram message (text or voice) → Telegram trigger node.[1]
    - IF node determines whether voice:
      - If yes, download audio → Whisper transcription → text.[1]
    - Text → AI model (OpenAI chosen) to extract structured meal info (calories/macros).[1]
    - Structured data → Supabase insert.[1]
    - Success or relevant info → Telegram confirmation message.[1]

- **Troubleshooting flow**
  - n8n error → copy error → Claude Code prompt:
    - Claude reads current workflow state via MCP.
    - Modifies node configuration (e.g., missing fields in Supabase node) directly in n8n.
    - User retests without manually editing JSON.[1]

### Automation patterns (triggers, pipelines, limits)

- **Triggers**
  - Telegram trigger node as the event entrypoint for user interaction in n8n.[1]

- **Branching pipeline**
  - IF node for modality:
    - Separate voice vs text handling.[1]
  - Voice branch:
    - File download → Whisper transcription → merge into common text path.[1]

- **Pipelines based on MCP templates**
  - Claude uses MCP template library:
    - To propose pipelines that match similar real‑world automations (e.g., existing Telegram or logging setups).[1]
  - This reduces manual design of node order and configuration.[1]

- **Size‑based automation limits**
  - If the JSON definition exceeds n8n API limits:
    - Automatic workflow creation from Claude via MCP may fail or not be feasible.[1]
    - There is an implicit size threshold where manual import or splitting flows becomes necessary.[1]

- **Credential configuration sequence**
  - Recommended operational order:
    - Generate workflow.
    - In Supabase:
      - Create project → run schema SQL → get service role secret and host URL.[1]
    - In n8n:
      - Configure Supabase credentials.
      - Configure Telegram credentials and webhook.
    - Activate workflow → test end‑to‑end.[1]

### Guardrail artifacts and behaviors

- **Skills as guardrail‑like artifacts**
  - The seven n8n skills form a guardrail layer that:
    - Encodes best practices on how Claude should use the n8n MCP server.[1]
    - Prevents naive or inefficient tool usage by serving as an instruction manual.[1]
  - They live outside the system prompt:
    - Acting as persistent, reusable guidance rather than one‑off prompt engineering.[1]

- **Plan mode as a process‑stage guardrail**
  - Before any workflow changes or creation:
    - Use plan mode to:
      - Force Claude to explain intentions.
      - Get user confirmation.[1]
    - This functions as a “review stage” before MCP calls are executed.[1]

- **Human‑in‑the‑loop on credentials and activation**
  - Guardrail pattern:
    - Claude creates workflow structure and schema.
    - Human configures credentials and activates workflows.[1]
  - Ensures:
    - API keys are not auto‑generated or mismanaged by the AI.
    - High‑risk operations (e.g., data writes, external API usage) only occur after human review.[1]

- **Size and token usage as de‑facto guardrail**
  - Extremely large workflows hit API and token limits:
    - Natural forcing function to:
      - Keep flows modular.
      - Reevaluate design when the AI starts using too many tokens.[1]

***

## Practical recommendations

- **Set up Claude Code + n8n MCP + Skills as your primary automation stack**
  - Create an `mcp.json` in a Claude Code project using the full configuration from the `n8n-mcp` repo and wire it to your n8n API URL and API key.[1]
  - Install the seven n8n Skills manually (if marketplace install fails), let Claude perform the manual steps, then remove the cloned repo while retaining global skills.[1]
  - On Windows (non‑WSL), ensure the MCP command is executed via `cmd` rather than `npx` directly in the `command` field.[1]

- **Use plan mode as a default for new workflows**
  - Whenever starting a new automation:
    - Switch to Claude Code plan mode.[1]
    - Describe:
      - Interfaces (e.g., Telegram).
      - Data sources (e.g., Supabase).
      - Desired transformations and outputs.[1]
    - Let Claude:
      - Propose architecture, node choices, and configuration checklist before generating any workflow.[1]

- **Generate both JSON and in‑instance workflows**
  - When Claude asks:
    - Request both JSON and direct creation in n8n.[1]
  - Use the JSON for:
    - Version control.
    - Manual edits if MCP creation fails due to size limits.[1]
  - Rely on in‑instance creation for:
    - Faster iteration and real‑time editing by Claude via MCP when the payload is small enough.[1]

- **Adopt the Telegram → Whisper → Model → Database pattern for multimodal logging**
  - For any “log my activity via chat” use case:
    - Use Telegram trigger, IF node for voice detection, voice download, Whisper transcription, AI model for structuring, and database insert (e.g., Supabase).[1]
    - Send a confirmation message back to the user after successful insertion.[1]

- **Lean on Claude for iterative debugging, not just initial generation**
  - When a node fails (e.g., Supabase insert error):
    - Copy the full error message and send it to Claude Code.[1]
    - Let Claude:
      - Inspect current node configuration via MCP.
      - Fix missing fields or mismatched schemas.
      - Update the workflow directly, then retest.[1]

- **Scope expectations and choose use cases accordingly**
  - Expect that:
    - Claude Code + n8n MCP can get you to an ~80% solution quickly, especially for structured flows like CRM, logging, or RAG pipelines.[1]
    - It may add extraneous steps for certain creative or highly specialized flows; be ready to prune nodes.[1]
    - Very large workflows will run into token and API size limits; split them into smaller, modular flows when this occurs.[1]

- **Treat Skills + plan mode as soft guardrails**
  - Keep n8n Skills installed globally so every project benefits from encoded best practices for MCP usage.[1]
  - Always use plan mode and human review before:
    - Activating new workflows.
    - Connecting high‑risk credentials.
    - Deploying production‑facing automations.[1]
