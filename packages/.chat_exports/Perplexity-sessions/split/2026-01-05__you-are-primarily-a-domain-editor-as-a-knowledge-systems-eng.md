---
title: "You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, "
date: "2026-01-05"
mode: "COPILOT"
uuid: "039d7691-acf6-4541-b8e0-b09b6b13db79"
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

You are primarily a **technical** editor. As a knowledge systems engineer, you synthesize workflows and preserve unique, actionable insights.[1]

Below is a cleaned and rewritten version of the conversation (podcast + comments), with navigation, filler, and jokes removed while keeping all distinct workflows, configurations, parameters, and practices.

***

## Opus 4.5 as primary coding model

- Multiple practitioners report Opus 4.5 is their **primary** model for day‑to‑day engineering, to the point where they would pay significantly and continuously to keep access; one host notes spending 250 USD in 5.5 days and reaching 350 USD total for a month, expecting it could reach 1,000 USD if used unchecked.[1]
- Opus 4.5 is described as a noticeable IQ step above Sonnet 4.5 / 3.5, more reliable at not dropping small details, better at graphics, and better at image understanding for code‑adjacent tasks (e.g., UI screenshots).[1]
- Its planning‑mode experience is called “amazing”; users comfortably throw entire features at it, using it as a starting point even when they previously would have hesitated to offload that work.[1]

**Cost/workflow adaptations**

- Because of the 2× Opus pricing multiplier and high usage, one workflow is:
  - Use GPT‑5.1 Codeex Max in Cursor for many tasks, because it is (at the time) free in that environment.[1]
  - Fall back to Opus 4.5 only when higher reliability or planning quality is needed, effectively cost‑balancing across models.[1]

***

## Multi‑model planning and execution

- A common pattern is to separate **planning** and **execution** across models:
  - Use GPT‑5.1 High/Pro or Opus 4.5 for high‑level analysis and plan generation over large context.[1]
  - Use GPT‑5.1 Codeex Max for tool‑calling, navigation, and concrete implementation steps, as it is tuned for code/tool workflows but less verbose for planning.[1]
- Another workflow is to have Opus 4.5 generate a meta‑prompt/guide, then feed that structured prompt into GPT‑5.1 Codeex Max or back into Opus 4.5 itself to carry out the work.[1]

***

## Context windows, “smart zones”, and degradation

- Two referenced articles (HumanLayer on “context‑efficient backpressure” and AMP on “too much context makes models act drunk” / “smart zone”) underpin the idea that there is a **sweet spot** of context length where model performance is highest.[1]
- As agents run tests, collect verbose logs, and traverse codebases, they can fill context windows to the point where model IQ effectively drops (e.g., “from 150 to 130”), even if still usable.[1]
- Recommended techniques:
  - Be explicit about how much context each step uses; avoid unbounded chat threads.[1]
  - Periodically **clear sessions** and restart with a compact summary instead of letting threads grow indefinitely.[1]
  - Use explicit compaction: ask the model to summarize what has been done, then start fresh with that summary as the new base.[1]

***

## MCP tools and context bloat

- Many people load dozens (50–100) of MCP tools into a single agent, and their schemas, descriptions, and metadata can consume **30–50k tokens** of context before any real work begins.[1]
- This overload makes it harder for the model to:
  - Keep track of which tools exist and when to call them.[1]
  - Maintain high “IQ” across the rest of the task because a large chunk of the window is permanently eaten by tool descriptions.[1]

**Context‑sparing MCP proposal**

- One discussed approach is to treat MCP tools as **code‑level metadata** instead of full descriptions in the prompt:
  - Maintain a file (or code structure) that lists tools and how to call them (names, arguments, endpoints).[1]
  - Let the model write code that selects and invokes tools via that file, instead of including all MCP JSON/schema in the model context.[1]
  - Run the code as a subprocess; the main LLM session waits for the result (handoff loop) rather than holding all tool descriptions in its own context window.[1]
- This preserves a cohesive representation of tool relationships in code while offloading the bulk of metadata out of the LLM context.[1]

**Prompt caching and dynamic MCP loading**

- MCP tool metadata is typically loaded at the start of the conversation and then cached via **prompt caching** to avoid recomputing embeddings.[1]
- Because of caching, you cannot easily add/remove MCPs dynamically mid‑session; doing so would break the cache, which is why selective per‑task MCP loading is not common yet.[1]

***

## Is 200k context “enough”?

- AMP argues that 200k tokens is “plenty” when:
  - You keep threads short.
  - You are very precise with context, functions, and documentation.
  - You re‑reference older threads by ID rather than inlining everything again.[1]
- Under this style (high‑craft “tight threads”), 200k is sufficient for most engineering tasks, especially when:
  - You explicitly control which files and docs are visible.
  - You structure multi‑step workflows across several short conversations.[1]

**Counterpoints and limitations**

- For large, real‑world codebases:
  - 200k does **not** hold “enough code” to show all relevant modules plus diffs and historical changes at once.[1]
  - Agents that rely on search/grep often miss related functionality (e.g., refund flows, edge‑case code) that is not explicitly mentioned in the prompt.[1]
- To expose patterns across the codebase (duplicates, hidden dependencies, inconsistent behavior), sometimes you need to **flood** the model with more code than 200k allows, or at least cycle multiple windows carefully.[1]
- Conclusion among the speakers: 200k can be made to work today with careful compaction and context management, but **larger contexts** will be needed to reach the desired “product engineer across major features” workflow without duplication and blind spots.[1]

***

## Compaction strategies: Auto‑compact vs perpetual compaction

### Manual/explicit compaction

- Autocompaction (e.g., in Claude Code, Autocode, and others) usually follows this pattern:
  - Build up a long thread working on a feature.
  - Compact the conversation: summarize prior steps and decisions.
  - Re‑read key files after compaction because file contents are not compressible; the model re‑ingests them to “catch up”.[1]
- Over time, repeated compact–rebuild cycles increase overhead:
  - More of each new context window is “structural” (summaries + required file re‑loads) and less is free for new work.[1]

### Droid’s “perpetual compaction”

- Droid uses anchored points in the conversation and background compaction so that:
  - The agent prioritizes the most recent phase, compressing older history more aggressively while preserving necessary anchors.[1]
  - Users can conduct **hundreds of turns** in a single session, from planning through building, debugging, and shipping, without manually managing context.[1]
  - One user reported using over **10 million tokens** in a single session, while another in that community reached 100 million tokens.[1]
- Droid extensively leverages caching so that file reads and repeated content do not translate linearly to billable tokens, which keeps apparent cost lower than raw token counts would suggest.[1]

### Trade‑offs

- Perpetual compaction depends on the agent harness to choose which history to compress or drop, which is an evolving, imperfect science.[1]
- More aggressive compaction means:
  - Less explicit control over what is kept.
  - Potential for missing critical earlier details if the compaction heuristics misjudge relevance.[1]

***

## Branching state and reuse of context

### Cursor: Duplicate Chat

- Cursor exposes an explicit **“Duplicate chat”** action:
  - Accessible via three dots at the bottom of a chat; duplicating carries forward the entire context.[1]
  - Typical workflow:
    - Start with a fast, cheap model (e.g., Composer 1) to find files and gather initial analysis (20–30k tokens).[1]
    - Duplicate the chat and switch to Opus 4.5 to generate a detailed plan using that primed context.[1]
    - Duplicate again for other models (e.g., GPT‑5.1 Codeex Max) to execute on specific tasks.[1]
  - For bug fixing:
    - While in a long feature thread (e.g., 50–80k tokens), duplicate the chat to create a branch dedicated to a bugfix, preserving all prior context without re‑explaining anything.[1]
  - Chats can be renamed (e.g., “[bug_fix] description…”) to make later retrieval easier from history.[1]

### Claude Code: “Rewind and resume” as pseudo‑branching

- In Claude Code:
  - Pressing **Esc twice** in the UI lets you revert to a previous message and resume from there, effectively rewinding the thread rather than branching.[1]
  - A pseudo‑branching workaround:
    - Open a new terminal/tab.
    - Open Claude again and use `/resume` to load the same chat into that tab.
    - From there, treat the second tab as a “branch” and continue independently.[1]

***

## System prompts and GPT‑5.1 Codeex Max behavior

- GPT‑5.1 (especially in Codeex harness) is **highly sticky** to system and early instructions:
  - If the system prompt prescribes a certain behavior and the user later asks to violate that constraint, the model often refuses (“I’m forbidden from doing that”) even when the user explicitly changes their mind.[1]
  - Contradictions between system instructions and later user instructions cause persistent refusal or resistance.[1]
- Cursor collaborated with OpenAI to adjust prompting for GPT‑5.1 Codeex Max:
  - They removed or minimized instructions that could contradict user goals.
  - They retained only critical directives (e.g., “use apply_patch tool”) in the harness.[1]
- Because Codex models are trained with certain harness prompts (e.g., Codeex system prompts), they may retain implicit bias toward those behaviors even when used with a lighter prompt elsewhere (“deep‑fried harness effect”).[1]

**Practical use patterns**

- GPT‑5.1 Codeex Max:
  - Very good for tool calling and code navigation.
  - Less verbose and sometimes less ergonomic to talk to than Claude for open‑ended planning.
  - Perceived as slower than Opus 4.5 in some providers due to more intensive internal “thinking time”.[1]
- Recommended prompting pattern:
  - Use another model (often Claude) to **generate or refactor prompts** for GPT‑5.1, making them precise and contradiction‑free.[1]

***

## Gemini 3 Pro usage

- Gemini 3 Pro is widely acknowledged as:
  - Very strong at **visual design** and UI prototyping.
  - Less reliable than GPT‑5.1/Opus/Sonnet for strict instruction following and coding, in many users’ experience.[1]
- Effective workflows:
  - Use Gemini’s web UI / AI Studio to prototype UI:
    - Provide an existing app screenshot.
    - Ask Gemini to redesign or modify the interface.
    - Export the resulting HTML/CSS/JS as a single file.
    - Feed that artifact to another coding model (Opus, GPT‑5.1, etc.) to integrate into the real system.[1]
  - Use Gemini 3 Pro to record screen + voice and visually debug an app:
    - Run Chrome DevTools and Chrome browsing while Gemini systematically scans for bugs.[1]
    - Gemini writes found bugs into a JSON file with status fields for each issue.
    - Claude runs in a loop, reading this JSON and fixing each bug, updating statuses as they are resolved.
    - The JSON is then surfaced in a UI to track open vs fixed defects.[1]
  - Use Gemini 3 Pro to visually inspect an app in a loop and generate bug reports for Claude to fix, effectively splitting “visual QA” and “code fix” across two models.[1]

***

## Prompt engineering practices and meta‑prompting

### Using guides as first‑class artifacts

- A strong pattern is to **import model‑specific prompt guides** (e.g., GPT‑5.1 Codeex Max cookbook) into Opus 4.5 and let Opus turn them into tailored prompts:
  - Paste the guide URL or contents.
  - Provide a rough, unstructured description of the feature or task.
  - Ask Opus to restructure the user’s prompt into a high‑quality, guide‑compliant meta‑prompt.[1]
- Prompt structure:
  - Wrap prompts in XML‑style tags with clear labels (e.g., `<ray_prompt_fix>` … `</ray_prompt_fix>`).
  - This pattern improves the model’s ability to distinguish meta‑instructions from content.[1]

### Iterative plan refinement

- Workflow:
  - Ask Opus 4.5: “Here’s my current plan; ask me more questions about what’s missing and refine it.”
  - Opus then runs multiple rounds of question‑answering to build a high‑quality product requirements document (PRD) or spec.[1]
  - This can involve 3+ turns, resulting in a detailed, markdown PRD that becomes the “source of truth” input to other models.[1]

***

## Git/GitHub workflows without MCP

- Several practitioners prefer using **native git/GitHub CLI** instead of GitHub MCP to avoid context bloat:
  - Use `git` or `gh` on the command line, with the LLM generating and interpreting commands/diffs.[1]
- Example workflows:
  - Regression analysis:
    - Identify commits between a “good” and “bad” state.
    - Use `git diff`, `git show <hash>`, or `gh` commands.
    - Ask the model to analyze diffs for likely regression causes.[1]
  - Partial PR extraction:
    - For a PR containing desirable and undesirable changes, use `gh` to fetch diffs and have the model extract just the needed pieces into a new branch or patch.[1]
  - Commit‑targeted bugfix analysis:
    - Provide a known regression commit hash and ask the model to inspect changes in that commit for likely issues, rather than instrumenting MCPs.[1]
- Commenters echo that models are “great at this workflow” and that direct CLI use is often more efficient than setting up GitHub MCP with all its additional tool metadata in context.[1]

***

## Harness differences and benchmarking

- Harness (agent framework + system prompt) significantly changes behavior even for the **same underlying model**:
  - Example: Running GPT‑5.1 Codeex Max low/medium/high in Cursor vs in Droid with the same prompt yielded different behavior.[1]
  - In Cursor, the model chose fewer files and did limited research before planning.
  - In Droid, the model searched more files and spent more time gathering context before proposing a plan, indicating fewer constraints/conflicts in the harness prompt.[1]
- Benchmarks show:
  - Some harnesses aggressively verify and test their work (e.g., self‑check, run tests, evaluate output), which scores higher on quality but costs more tokens.[1]
  - Subsidized or credit‑based plans often tune agents to go to “completion” once and then **offer** to test/evaluate only if asked, instead of automatically doing so, to save cost.[1]
  - This explains why some technically strong harnesses (e.g., Augment) may feel great but benchmark poorly because they skip thorough self‑checking unless prompted.[1]

***

## Additional user techniques and notes from comments

- Cline agent:
  - One commenter calls Cline a surprisingly good coding assistant that performs strong autocompaction and reliably ensures the todo list actually gets completed.[1]
- Context controls in Claude desktop:
  - A commenter asks whether turning off MCP connectors in the chat interface reduces tools included in context; implication is that fewer tools should reduce context bloat and improve performance.[1]
- General sentiment:
  - Opus 4.5 is widely praised as “astoundingly strong” and “incredible” for coding; some users would accept a price increase and still pay.[1]
  - Gemini 3 is criticized in comments for weak instruction following compared to GPT‑5.1, Opus, and Sonnet for coding tasks.[1]

***

## Operational patterns and setups

### Multi‑entity flows

- **Opus + GPT‑5.1 Codeex Max combo**
  - Use Opus 4.5 or GPT‑5.1 High/Pro to:
    - Analyze the codebase with large context.
    - Generate structured plans and meta‑prompts.
    - Create PRDs and detailed task breakdowns.[1]
  - Then use GPT‑5.1 Codeex Max to:
    - Navigate files.
    - Call tools (edit, apply_patch, run tests).
    - Implement the planned changes.[1]

- **Opus + MCP tools via code generation**
  - Keep MCP metadata in code/files rather than prompts.
  - Let Opus write code that inspects a list of tools and calls the right APIs.
  - Run that code in a subprocess while the primary Opus session monitors and integrates results.[1]

- **Gemini + Claude bug‑hunting loop**
  - Gemini 3 Pro:
    - Uses Chrome DevTools and browsing to visually inspect an app continuously.
    - Logs every bug found into a JSON file with structured fields (e.g., `id`, `description`, `status`).[1]
  - Claude (often Opus 4.5):
    - Runs in a loop, reading the JSON.
    - Attempts to fix each bug in code.
    - Updates statuses in the JSON (e.g., “open” → “fixed”), creating a structured bug‑fix pipeline.[1]

- **Gemini design → other‑model implementation**
  - Gemini 3 Pro:
    - Prototypes a UI via screenshots or text.
    - Outputs HTML/CSS/JS.[1]
  - Opus / GPT‑5.1:
    - Take that artifact and integrate it into the app (routing, state management, backend API wiring).[1]

- **Opus meta‑prompting for other models**
  - Opus 4.5:
    - Ingests GPT‑5.1 Codeex Max prompt guides.
    - Takes rough user goals.
    - Produces a cleaned, structured prompt with XML‑style tags and sections.[1]
  - GPT‑5.1 Codeex Max (or Opus itself) then executes against this meta‑prompt to implement features.[1]

- **Opus + GPT‑5.1 High via RepoPrompt**
  - Opus executes changes in code.
  - A separate “chat” configured with GPT‑5.1 High gets a bird’s‑eye view over relevant files (via RepoPrompt).
  - GPT‑5.1 High reviews Opus’s work, calling out issues that a deep‑context, in‑thread model may miss.[1]

### Automation patterns

- **Perpetual compaction harnesses (Droid)**
  - Automatically compact older parts of the conversation while anchoring key states.
  - Allow very long sessions (10–100M tokens) across planning, building, and debugging phases without manual resets.[1]

- **Plan‑then‑execute harnesses**
  - Some agents:
    - Always start with a planning step.
    - Then run through implementation and testing steps with minimal user intervention.
    - Only propose test/evaluation if prompted, to reduce cost.[1]

- **Cursor duplicate‑chat branching**
  - Explicit command (“Duplicate chat”) used to:
    - Fork off bugfix branches from feature threads.
    - Spin up multiple models (Composer → Opus → GPT‑5.1) over the same primed context.
    - Avoid re‑priming context or re‑explaining tasks.[1]

- **Claude Code partial rewind**
  - Using Esc‑Esc to rewind to a known good point and `/resume` across tabs to simulate branches, letting users explore alternative implementation paths without losing prior work.[1]

- **Git/GitHub CLI‑driven analysis loops**
  - Using `git` / `gh` as the primary automation surface:
    - LLM emits commands to get diffs, logs, and PR contents.
    - LLM analyzes outputs for regressions or candidate fixes.
    - This avoids MCP context overhead and leverages tools the model already knows well.[1]

### Guardrail artifacts

- **Prompt guides and cookbooks (e.g., GPT‑5.1 Codeex Max guide)**
  - These documents encode:
    - Preferred prompting structure (sections, tags, roles).
    - Tool‑calling policies.
    - Reasoning and planning steps.[1]
  - In practice:
    - Imported into Opus 4.5.
    - Transformed into local meta‑prompts.
    - Stored as markdown “source of truth” documents reused across threads and models.[1]

- **Harness system prompts**
  - Codeex harness:
    - Includes instructions like “use apply_patch tool”.
    - Strongly biases tool usage and can conflict with user‑provided tools (e.g., custom edit tools), effectively acting as a hard guardrail.[1]
  - Cursor’s custom prompts for GPT‑5.1 Codeex Max:
    - Carefully pared down to avoid contradictions that cause refusals.
    - Still encode key policies (e.g., required tool usage, safe operations).[1]

- **JSON bug log as a governance artifact**
  - The JSON file produced by Gemini and consumed by Claude:
    - Encodes a workflow policy: bugs must be logged, tracked, and status‑updated through a structured object rather than ad‑hoc chat.
    - Acts as a central artifact for bug lifecycle management, gating fixes and verification steps.[1]

***

## Practical recommendations

**Set up multi‑model roles**

- Use Opus 4.5 or GPT‑5.1 High/Pro as **planner/analyst**, and GPT‑5.1 Codeex Max (or similar) as **executor/tool‑caller**:
  - Planner: reads larger context, designs plans, and creates structured prompts/PRDs.
  - Executor: navigates files and tools to implement the plan.[1]

**Control MCP and context bloat**

- Avoid loading dozens of MCPs into a single session:
  - Group tools by task; only attach the minimal set of MCPs needed for a given workflow.
  - Where possible, keep tool metadata in code or config files that the model queries indirectly, rather than as raw schema in the prompt.[1]
- If using Claude desktop, disable unneeded MCP connectors in the UI so they are not included in context by default.[1]

**Adopt structured compaction**

- For non‑Droid setups:
  - Periodically run explicit compaction:
    - Ask the model to summarize what has been done and why.
    - Start new threads with that summary plus the minimum required files.[1]
  - Cap thread length proactively (e.g., by messages or token count) to stay within the “smart zone”.[1]
- If available, experiment with harnesses that implement **perpetual compaction** (like Droid) for long‑running sessions, but validate quality at deeper turns.[1]

**Use branching and state reuse**

- In Cursor:
  - Use “Duplicate chat” whenever you:
    - Pivot from feature work to bugfixes.
    - Want to try a different model or strategy over the same context.
  - Rename chats with prefixes like `[bug_fix]` or `[design]` to keep history manageable.[1]
- In Claude Code:
  - Use Esc‑Esc and `/resume` in multiple tabs to simulate branches around critical decision points.[1]

**Enforce clear guardrails in prompts**

- Maintain a single, versioned **prompt guide** (guardrail doc) for each major workflow (e.g., “coding harness prompt guide”, “PR review prompt guide”) that encodes:
  - Structure (sections, XML‑style tags).
  - Tool‑usage rules.
  - Constraints (e.g., “never touch file X”, “don’t run destructive commands”).[1]
- Have Opus or another strong planner:
  - Ingest these documents and generate validated prompts for each new task, so contradictions are minimized before they hit strict models like GPT‑5.1 Codeex Max.[1]

**Use Gemini where it’s strongest**

- For design and visual workflows:
  - Use Gemini 3 Pro to:
    - Prototype UI layouts and flows.
    - Record screens while you narrate desired changes.
    - Generate bug JSON logs for Claude to fix.[1]
- Treat these outputs (HTML mocks, JSON bug logs) as **first‑class artifacts** that other models consume, rather than ad‑hoc text.[1]

**Prefer CLI over MCP where possible**

- For git and GitHub:
  - Rely on `git` and `gh` CLI plus model reasoning rather than GitHub MCP in many cases:
    - Use CLI to fetch diffs/commits/PRs.
    - Ask the model to analyze and propose fixes.
  - This avoids adding MCP schemas to every prompt and keeps context lean.[1]

**Separate reviewer vs auto‑modifier roles**

- For high‑risk operations (e.g., large refactors, critical infra changes):
  - Configure at least one model as **reviewer/critic only**:
    - It receives diffs and plans, but does not write directly to the codebase.
    - It flags issues and suggests changes that are then applied by a different agent or by you.[1]
- Use a JSON or markdown artifact (e.g., “review checklist”) as the gate; no changes are applied until that checklist is satisfied.[1]
