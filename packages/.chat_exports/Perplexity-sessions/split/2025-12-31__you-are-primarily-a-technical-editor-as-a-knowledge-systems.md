---
title: "You are primarily a technical editor. As a knowledge systems engineer, you synthesize workflows and preserve unique insi"
date: "2025-12-31"
mode: "COPILOT"
uuid: "acb8749f-0b27-4b43-a32a-2a1671943c15"
entry_count: 1
---

## Human

You are primarily a technical editor. As a knowledge systems engineer, you synthesize workflows and preserve unique insights.

Read the entire conversation provided (post + comments). Remove navigation, ads, jokes, and repeated points. Collapse any redundancy, but do not lose any unique, concrete information that could change how someone works.

Produce a rewritten version of the thread that:

Keeps every distinct insight, workflow, or configuration detail.

Preserves all mentions of tools, agents, actions, and integrations (e.g., GitHub actions, zen-mcp, codex, Copilot, MCP, hooks, CLAUDE.md, pre-commit, etc.) and what people actually do with them.

Removes repeated restatements of the same idea unless they add a new nuance.

After the rewrite, add a section called “Operational patterns and setups” where you explicitly list:

Multi-model review flows (e.g., “I use zen-mcp and have all 3 review the code, then have Claude consolidate and apply fixes”).

Automation patterns (GitHub auto-review actions, agents/skills triggered at the end of each dev phase, hooks that detect ‘fallback’/‘backwards compatible’ code, pre-commit checks referencing code-patterns.md).

Guardrail artifacts (CLAUDE.md, .claude/development-principles.md, code-patterns.md) and the key rules they encode.

Add a final section “Practical recommendations” that distills the most useful advice into concrete steps another developer could implement (e.g., “Set up zen-mcp with three reviewers and a Claude consolidation agent”, “Add a hook to block ‘fallback’ code paths”, “Configure codex or similar as a PR reviewer only, not auto-fixer”).

Format the answer with short sections and bullets. Be concise but do not omit any unique workflow or recommendation from the conversation.

## Assistant

The page you’re viewing is a standalone blog post without a visible comment thread, so there is no broader “conversation” to condense beyond the article itself. The rewritten version below keeps every distinct workflow, pattern, and configuration detail from the post, minus navigation and boilerplate.[1]

***

## Rewritten thread (condensed content)

LLMs used in coding agents (like Claude Code) are **stateless**: they do not retain knowledge of your codebase between sessions and only know what is in the current context window. Agent harnesses typically require explicit memory management, and `CLAUDE.md` / `AGENTS.md` is the one file injected into every conversation by default, making it the main mechanism to onboard the agent to your project.[1]

This has three consequences for coding workflows:[1]
- At the start of each session, the agent knows nothing about your codebase.  
- You must re-tell it anything important every session.  
- `CLAUDE.md` is the preferred way to do that.

### What `CLAUDE.md` should encode

`CLAUDE.md` is for onboarding Claude to your codebase and should focus on three things:[1]

- **WHAT**:  
  - Tech stack, frameworks, languages.  
  - Project and repo structure, including monorepos: apps, shared packages, what each part is for, and where to look for things.[1]

- **WHY**:  
  - Purpose of the project.  
  - High-level function of each major component or directory.[1]

- **HOW**:  
  - How Claude should work on the project: e.g., use `bun` instead of `node`.[1]
  - How to run tests, typechecks, compilation steps.  
  - How to verify changes.

The article warns not to stuff every possible command and instruction into `CLAUDE.md`, because this degrades performance and makes Claude more likely to ignore the file.[1]

### Why Claude often ignores `CLAUDE.md`

Claude Code injects a system reminder alongside `CLAUDE.md` content in the user message that says:[1]
> “IMPORTANT: this context may or may not be relevant to your tasks. You should not respond to this context unless it is highly relevant to your task.”

As a result:[1]
- Claude ignores `CLAUDE.md` when it judges it irrelevant to the current task.  
- The more non-universal instructions you put in, the more likely it is to be ignored.  

The post suggests Anthropics likely added this because many `CLAUDE.md` files had lots of brittle, one-off “hotfix” instructions that hurt performance, so instructing Claude to ignore broadly inapplicable content improved overall output quality.[1]

### Instruction count and model limits

The article cites research suggesting:[1]
- Frontier “thinking” LLMs can consistently follow about **150–200 instructions**.  
- Smaller models deteriorate much faster as instruction count grows, with **exponential** decay in instruction-following quality, while larger frontier thinking models show more **linear** degradation.  
- LLMs bias toward instructions at the **start** (system prompt and `CLAUDE.md`) and the **end** (latest user messages) of the prompt.  
- As instruction count increases, quality drops **uniformly** across instructions, not just for later ones.[1]

For Claude Code specifically:[1]
- The system prompt alone contains roughly **50 individual instructions**.  
- This can already consume a large fraction of the instructions a model can reliably honor before considering rules, plugins, skills, or user prompts.  

Therefore, `CLAUDE.md` should:[1]
- Contain as few instructions as possible.  
- Include only instructions that are **universally applicable** to the tasks you run with the agent.

### Length and applicability of `CLAUDE.md`

The post emphasizes that LLMs perform best when the context window is filled with **focused, relevant** context such as examples, related files, tool calls, and tool outputs rather than generic background. Since `CLAUDE.md` is present in every session, its contents must be broadly relevant.[1]

Guidance:[1]
- Avoid including niche, task-specific things (e.g., “how to structure a new database schema”) in `CLAUDE.md`, because they distract the model when working on unrelated tasks.  
- Prefer short files: community consensus is **under ~300 lines**, and shorter is better.[1]
- At HumanLayer, the root `CLAUDE.md` is **under 60 lines**.[1]

### Progressive disclosure pattern

To keep `CLAUDE.md` concise but still allow rich guidance for complex projects, the article recommends **Progressive Disclosure**:[1]

- Keep task-specific instructions in separate markdown files with self-descriptive names, for example:[1]
  - `agent_docs/building_the_project.md`  
  - `agent_docs/running_tests.md`  
  - `agent_docs/code_conventions.md`  
  - `agent_docs/service_architecture.md`  
  - `agent_docs/database_schema.md`  
  - `agent_docs/service_communication_patterns.md`

- In `CLAUDE.md`, include:[1]
  - A list of these files with brief descriptions.  
  - Instructions telling Claude to decide which files are relevant and read them before working.  
  - Optionally: instructions for Claude to propose which documents it wants to read and wait for human approval before opening them.

Additional guidance:[1]
- Prefer **pointers** to sources, not copies: avoid embedding code snippets in these doc files as they drift out-of-date quickly.  
- Use `file:line` references pointing Claude to authoritative code locations instead.[1]
- This pattern conceptually mirrors **Claude Skills**, which also encapsulate structured capabilities, though those are more focused on tool use than instruction text.[1]

### Claude is not a linter

One recurring misuse is treating Claude as a code style enforcer:[1]

- Do **not** use `CLAUDE.md` to store extensive code style guidelines.  
- “Never send an LLM to do a linter’s job”: LLMs are slow and expensive compared to deterministic linters and formatters.[1]
- Style guidelines add many instructions and code snippets that are often irrelevant to most tasks, hurting both instruction following and context utilization.[1]

Instead:[1]
- Rely on deterministic tools (linters, formatters) for style and basic correctness.  
- Let the LLM learn style **in context** from the existing codebase, which is often sufficient when you have coherent patterns.

Suggested automation with Claude Code features:[1]
- Use a **Claude Code `Stop` hook** that runs your formatter and linter, then presents the resulting errors back to Claude for it to fix, instead of having Claude search for formatting issues by itself.[1]
- Use a linter that can automatically fix issues (the post specifically likes **Biome**) and carefully tune rules to maximize safe auto-fix coverage.[1]

Alternate pattern:[1]
- Create a **Slash Command** that:  
  - Includes your code guidelines.  
  - Points Claude at relevant diffs (e.g., from version control) or `git status`.  
- Use that command when you explicitly want guideline enforcement, keeping implementation work and formatting/style checks separate, which tends to improve both.[1]

### Do not auto-generate `CLAUDE.md`

Many harnesses (Claude Code and others using OpenCode) can auto-generate `CLAUDE.md` / `AGENTS.md` via commands like `/init`. The article strongly recommends against this:[1]

- `CLAUDE.md` is one of the **highest leverage configuration points** in the harness, as it affects every phase of the workflow and every artifact produced.[1]
- A bad line of code is local damage; a bad line in an implementation plan can cause a lot of bad code; a bad line in a research plan can cause many bad plan lines and even more bad code.[1]
- A bad line in `CLAUDE.md` can contaminate all of those phases systematically.[1]

Therefore:[1]
- Manually author and carefully review every line in `CLAUDE.md`.  
- Treat it as a critical artifact that should not be blindly generated by the model or a harness helper.[1]

### Final key points from the article

The post ends with six summarized principles:[1]
- `CLAUDE.md` is for onboarding Claude: define **WHY**, **WHAT**, and **HOW** of the project.  
- **Less is more**: include as few instructions as necessary.  
- Keep content **concise and universally applicable**.  
- Use **Progressive Disclosure**: instruct Claude how to find additional information instead of embedding everything in `CLAUDE.md`.  
- Claude is not a linter; favor linters, formatters, and harness features like **Hooks** and **Slash Commands**.  
- `CLAUDE.md` is a high-leverage artifact; avoid auto-generation and craft it deliberately.[1]

***

## Operational patterns and setups

### Multi-model and multi-context patterns

- Use **Progressive Disclosure** instead of a single bloated `CLAUDE.md`:[1]
  - Keep a small, universally relevant `CLAUDE.md`.  
  - Push task-specific detail into separate markdown files (`agent_docs/*.md`) and let the agent pull them on demand.  

- Treat **Claude Skills** as analogous to these instruction bundles, but focused on tool usage rather than written guidelines.[1]

### Automation patterns

- **Stop hook for formatting and linting**:[1]
  - Configure a **Claude Code `Stop` hook** that automatically runs linters and formatters at a defined stage.  
  - Feed resulting errors back to Claude, asking it to fix only what deterministic tools already identified.  
  - Prefer a linter/formatter with safe auto-fix capability (e.g., **Biome**) and tune rules for maximum safe auto-application.

- **Slash Commands for guidelines**:[1]
  - Implement a **Slash Command** that:  
    - Embeds your code guidelines (style conventions, patterns).  
    - Points to diffs, `git status`, or specific paths, so Claude can focus style review on actual changes.  
  - Use this command when you explicitly want guideline enforcement, separate from normal implementation work.[1]

### Guardrail artifacts and encoded rules

- **`CLAUDE.md` / `AGENTS.md`**:[1]
  - Purpose: high-level onboarding of the agent to the codebase.  
  - Encodes:  
    - Project **WHY** (goals).  
    - Project **WHAT** (stack, structure, key components).  
    - Project **HOW** (commands for tests/build, execution environment).  
  - Rules: should be short, universally relevant, and not overloaded with one-off instructions.

- **Task-specific docs (e.g., `agent_docs/*.md`)**:[1]
  - `building_the_project.md`: how to build.  
  - `running_tests.md`: how to run tests.  
  - `code_conventions.md`: code style and patterns.  
  - `service_architecture.md`: architectural overview.  
  - `database_schema.md`, `service_communication_patterns.md`: detailed data/communication design.  
  - Rules: referenced from `CLAUDE.md` with instructions to the agent on when/how to read them; they should prefer `file:line` pointers over inline code.

- **External linters/formatters** (e.g., Biome):  
  - Guardrail role: enforce deterministic style and correctness rules, with carefully tuned auto-fix behavior.[1]

***

## Practical recommendations

- Keep `CLAUDE.md` **short and universal**:  
  - Limit it to project WHY/WHAT/HOW, and avoid embedding niche workflows or one-off fixes.[1]
  - Aim well under 300 lines; treat ~60 lines as a good target for the root file.[1]

- Use **Progressive Disclosure** for depth:  
  - Create `agent_docs/` (or similar) with focused files like `building_the_project.md`, `running_tests.md`, `code_conventions.md`, etc.[1]
  - In `CLAUDE.md`, list these files and instruct Claude to select and read the relevant ones before working, or to propose a list for human approval.

- Prefer **pointers over copies**:  
  - In agent-facing docs, reference `file:line` locations instead of pasting code snippets, so the model always reads current, authoritative code.[1]

- Treat Claude as **implementation and reasoning**, not a linter:  
  - Use deterministic linters/formatters (e.g., Biome) for style and basic correctness.[1]
  - Configure them to auto-fix safe issues and run them via scripts or hooks.

- Add a **Claude Code Stop hook** for quality loops:  
  - At a suitable point in the workflow, run your formatter and linter in a Stop hook and feed any errors back to Claude to fix.[1]

- Add a **Slash Command** for style review:  
  - Create a command that bundles your style guidelines and points Claude at diffs or `git status`, so you can trigger a focused style pass on demand rather than forcing style rules into every interaction.[1]

- Do **not** auto-generate `CLAUDE.md`:  
  - Avoid `/init`-style generation; hand-craft `CLAUDE.md` and review each line as a high-leverage control point over the entire coding harness.[1]
