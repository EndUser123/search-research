---
title: "You are primarily a **{domain} editor**. As a knowledge systems engineer, you synthesize workflows and preserve unique, "
date: "2026-01-01"
mode: "COPILOT"
uuid: "20ad021f-be24-45db-9b34-8a8179642299"
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

***

## Rewritten thread (insights only)

- Traditional AI agent development in Claude Code often relies on repeatedly editing a single system prompt with rules and constraints, testing, finding edge cases, and manually refining until behavior is acceptable.[1]
- This manual loop encodes insights directly into the system prompt, so the agent does not truly self‑improve across sessions and must relearn the same lessons each time.[1]

- Claude Code **skills** are described as:
  - Efficient with context, composable, portable, and discoverable (can be shared as markdown plus optional scripts, e.g., on GitHub).[1]
  - Plain‑text artifacts that Claude can both read and write, enabling incremental updates over time rather than static instructions.[1]
  - A mechanism to store knowledge outside the model’s weights so reasoning from one session can compound into future work.[1]

- A key unlock is that Claude can modify skills during or after sessions:
  - You can set up a slash command that triggers a retrospective at the end of a coding session.[1]
  - During this retrospective, Claude can review what happened and update the specific skills used in that session.[1]
  - Instead of a manual command, this retrospective/update behavior can be encoded directly in `claude.md` so it runs automatically at chosen times.[1]

- Skills are organized as:
  - A top‑level **skills directory**; each skill lives in its own subdirectory.[1]
  - Each skill directory must contain a `skill.md` file.[1]
  - `skill.md` can reference additional assets (scripts, references, other files) that are available for progressive disclosure when the skill is invoked.[1]

- Skills can be installed in several scopes:
  - Machine‑level (root of your computer) so they are accessible in any project.[1]
  - Project‑level so skills are tied to a specific repository or codebase and can be shared with that repo.[1]
  - Packaged inside a Claude Code plug‑in for easy installation and reuse by others.[1]

- Skill format and invocation:
  - Each skill has a **name** and a **description**; the description is critical because it is what resides in the orchestrator/main thread context and controls when the skill is invoked.[1]
  - Skills can declare which **tools** they are allowed to use and can reference other helpful assets without loading them all at once.[1]
  - Only the short description is kept in the main context; full content and assets are loaded progressively once the skill is actually triggered.[1]

- **Progressive disclosure** behavior:
  - Claude loads all skill names and descriptions into context.[1]
  - Claude then requests matches based on descriptions and asks for confirmation before loading a skill’s full content.[1]
  - This minimizes token usage by only expanding skills when needed.[1]

- Learning loop pattern (continual learning from sessions):
  - Before a new experiment or task, query the **skill registry** to surface:
    - Relevant past experiments.
    - Known failures.
    - Current working configurations.[1]
  - Run the task/experiment using relevant skills.[1]
  - At the end, trigger a **retrospective** phase:
    - Claude reads the entire conversation or session log.
    - Extracts what worked and what failed.
    - Updates the skills by:
      - Directly editing `skill.md` and related files, or
      - Opening a PR if skills live in a Git‑backed registry.[1]
  - This retrospective/update loop can be repeated every session so skills accumulate refined patterns over time.[1]

- Failures and successes as first‑class data:
  - For prior projects (e.g., “open lovable”), a lot of time was spent hand‑tuning a single system prompt with “do this, don’t do that.”[1]
  - The video emphasizes **explicitly documenting failures** so that new sessions can skip previously known bad directions.[1]
  - Because LLMs are non‑deterministic, capturing examples of where behavior “goes off the rails” is valuable, alongside successful examples.[1]
  - Stored failures and successes become structured inputs to improve skills rather than ephemeral debugging info.[1]

- External perspective (Robert Nishihara quote summarized):
  - Skills enable continual learning by letting agents add new skills instead of constantly updating model weights.[1]
  - Compute spent on reasoning can simultaneously generate new skills, rather than being discarded after each task.[1]
  - Knowledge stored outside model weights is:
    - Interpretable (humans can read the skills).
    - Easy to correct and update as plain text.
    - Data‑efficient, similar to in‑context learning.[1]
  - It is straightforward to edit natural‑language skills when behavior is wrong, compared to retraining or post‑training a model with opaque internal state.[1]

- Skills as persistent team memory:
  - Knowledge stored in skills is readable, editable, and shareable across users and projects.[1]
  - Every session’s reasoning can be distilled into skills so behavior improves as the environment changes (e.g., library updates, new tools).[1]
  - Skills are positioned not just as “instructions” but as **persistent team memory** that compounds with every session.[1]

- Getting started and available examples:
  - Anthropic maintains a public **skills repository** on GitHub, with example skills that can be installed and extended.[1]
  - Example skills mentioned:
    - Front‑end design skill.
    - Web app testing skill.[1]
  - With the web app testing skill installed, you can issue a high‑level command like “test my application,” and the skill coordinates tools such as Playwright or a Chrome MCP server to run tests.[1]

- Usage contexts:
  - **Personal workflows**:
    - Create custom skills in natural language tailored to recurring tasks in your day‑to‑day work.[1]
    - Equip skills with the tools they need and let them learn over time from your own successes/failures.[1]
  - **Team/project workflows**:
    - Store project‑specific skills in the repo so any collaborator using Claude Code with skills automatically inherits that project knowledge.[1]
    - Provide plug‑ins or registries to distribute a curated bundle of MCP servers, skills, and hooks as a single configuration.[1]

- Integration beyond Claude Code:
  - Learnings captured in skills (or the retrospective process) can be used to improve core system prompts for agentic systems.[1]
  - A workflow is suggested where failures/successes automatically generate PRs to:
    - Update the system prompt.
    - Update the skill files in Git.[1]
  - This makes system prompts and skills evolve from real usage data instead of ad‑hoc manual edits.[1]

- Community commentary (unique operational concerns):
  - Some users note that Claude can **ignore rules** or that it lacks true long‑term memory, requiring active management to avoid forgetting project context over many interactions.[1]
  - A concern is raised about **context window limits**: continual learning information must be culled and pruned to avoid “context spam” and “context rot,” implying the need for strategies to retire or compress stale skill content.[1]
  - One commenter questions how to avoid the model forgetting what was done on a project “hundreds of times,” reinforcing the importance of persistent external artifacts like skills instead of relying on transient session context.[1]
  - Another commenter notes that in‑context learning may functionally approximate fine‑tuning, supporting the idea that curated skills can replace or reduce formal fine‑tuning in some workflows.[1]
  - A commenter asks whether skills are supported outside Claude Code (e.g., Strands), indicating current limitations in where this pattern can be applied natively.[1]
  - There is also skepticism that this qualifies as “true learning” and concern about scaling, but no specific alternative workflow is offered in the thread.[1]

***

## Operational patterns and setups

### Multi‑entity flows

- **Skill‑orchestrator flow**:
  - The orchestrator (main Claude Code thread) loads only skill names and descriptions into context.[1]
  - When a user request matches a skill description, the orchestrator asks for confirmation, then loads the full skill content and referenced assets as needed.[1]
  - The skill, once loaded, uses its configured tools (e.g., Playwright, Chrome MCP, other MCP servers) to act on the project.[1]

- **Session → registry → retrospective loop**:
  - Before work: query the skill registry to pull in relevant prior experiments, existing working configs, and known failure cases.[1]
  - During work: invoke skills as needed via natural‑language commands or slash commands (e.g., “test my application”).[1]
  - After work: trigger a retrospective command that:
    - Reads the full session transcript.
    - Extracts what worked/failed.
    - Updates skill definitions and related files or opens PRs in a Git‑backed skill repo.[1]

- **Project‑level skills in teams**:
  - Skills live inside the project repo; each collaborator using Claude Code with skills automatically gets the same project‑specific behaviors.[1]
  - Plug‑ins or registries may bundle:
    - Multiple skills.
    - MCP servers.
    - Hooks and configuration into a single installable package.[1]

- **Skills ↔ system prompt co‑evolution**:
  - Skills accumulate structured examples of successes and failures.[1]
  - A separate process (script or agent) can turn those examples into PRs that update the central system prompt for the agent.[1]
  - Over time, both the system prompt and the skills registry reflect real operational experience, not just initial design assumptions.[1]

### Automation patterns

- **Retrospective slash commands**:
  - A slash command is configured to run at the end of a coding session.[1]
  - When invoked, it:
    - Collects the session context (conversation, changes, test results).
    - Calls Claude to extract new learnings.
    - Applies updates to the relevant skills (or opens PRs).[1]

- **Automatic retrospectives via `claude.md`**:
  - Instead of explicitly running a slash command, the same retrospective behavior can be encoded in `claude.md` so it triggers automatically based on defined conditions (e.g., session end, commit, or time‑based triggers).[1]

- **Progressive disclosure as a context‑management policy**:
  - Only short skill descriptions are held in the main context at all times.[1]
  - Full skill content and associated files are lazily loaded when a skill is confirmed for use, reducing context consumption.[1]

- **Git‑backed updates**:
  - Skills stored in a registry or repo can be updated via automatically generated PRs.[1]
  - This allows:
    - Review workflows before changes are merged.
    - Versioning and rollback if a learned update degrades behavior.[1]

- **Testing automation via skills**:
  - A web‑app testing skill can be invoked by a single high‑level command (“test my application”).[1]
  - The skill orchestrates tools like Playwright or Chrome MCP to run tests and report results, hiding underlying complexity from the user.[1]

### Guardrail artifacts

- **`skill.md` files as guardrails and memory**:
  - `skill.md` encodes:
    - The intended behavior.
    - Important rules and constraints for that skill.
    - Links to scripts/tools it can use.[1]
  - Because `skill.md` is plain text:
    - It is easy to audit and correct when Claude learns something undesirable.
    - It can include explicit examples of “do this, don’t do that,” including documented failure patterns to avoid.[1]

- **Skill registry as a governed knowledge base**:
  - The central registry of skills functions as a controlled store of patterns, configurations, and edge cases.[1]
  - Governance is implemented via:
    - PRs and code review before updated skills are merged.
    - The ability to revert specific skill versions if they cause regressions.[1]

- **Context and pruning rules (implied guardrails)**:
  - Comments highlight the need for:
    - Culling/pruning older or noisy “continuous learning” content to prevent context spam and rot.[1]
    - Managing what actually remains in the skill corpus so the context window is not overwhelmed.[1]
  - This implies a guardrail policy where only the most useful and recent failures/successes remain in active skills; older ones may be archived or summarized.[1]

- **Separation of memory vs. weights**:
  - Skills hold interpretable, updateable instructions and patterns outside model weights.[1]
  - This separation acts as a guardrail: behavior changes are made explicitly in text, not hidden in opaque parameter updates, making review and correction straightforward.[1]

***

## Practical recommendations

- Set up a **skills directory** with one subdirectory per behavior, each containing a `skill.md` that defines:
  - A precise, action‑oriented description.
  - The tools it can use.
  - Links to scripts or references for progressive disclosure.[1]

- Install skills at **three levels**:
  - Machine‑level for personal, cross‑project workflows.
  - Project‑level inside each repo for domain‑specific behavior.
  - Plug‑in/registry bundles when you want a shareable package of skills, MCP servers, and hooks for teams.[1]

- Configure the orchestrator to use **progressive disclosure**:
  - Keep only short skill descriptions in context.
  - Require explicit confirmation before loading full skill content and assets.[1]

- Implement a **session retrospective loop**:
  - Before work: query the skill registry for relevant prior experiments, failures, and current working configurations.[1]
  - After work: run a slash command or `claude.md` hook that:
    - Reads the entire session transcript.
    - Extracts successes and failures.
    - Updates `skill.md` files or opens PRs with proposed changes.[1]

- Treat failures as first‑class training data:
  - For each major failure mode, add:
    - A concrete failing example.
    - The corrected behavior.
    - Any rules for when that pattern should be avoided or allowed.[1]
  - Store these in the relevant skill so new sessions automatically skip known bad paths.[1]

- Use **Git‑backed skill registries**:
  - Store skills in version‑controlled repos.
  - Require PR review for any automated or semi‑automated skill updates from retrospectives.[1]
  - Roll back to previous versions when a learned update causes regressions.[1]

- Centralize high‑risk behavior in **review‑only flows**:
  - For operations that could “nuke your project” (e.g., large‑scale code changes, destructive migrations), configure skills to:
    - Generate diffs or PRs only.
    - Never auto‑apply changes without human approval.[1]
  - Reserve fully automated modification for low‑risk tasks such as routine tests or non‑critical refactors.[1]

- Regularly **prune and compress** skill content:
  - Periodically review skills to:
    - Remove obsolete or redundant examples.
    - Summarize older failures/successes into shorter guidance while keeping key edge cases.[1]
  - This limits context growth and mitigates context spam/rot while preserving operational knowledge.[1]

- Extend skills into **system‑prompt evolution**:
  - Use a scheduled or triggered process that:
    - Reads accumulated failure/success data from skills.
    - Proposes PRs to update the system prompt for your agent system.
  - Keep the system prompt focused and high‑level while pushing detailed patterns and examples into skills.[1]

- When using skills in teams, **treat them as shared doctrine**:
  - Document core principles, constraints, and patterns once in the project’s skill set.
  - Ensure every process stage that involves agent decisions references these skills rather than duplicating rules in ad‑hoc prompts.[1]
