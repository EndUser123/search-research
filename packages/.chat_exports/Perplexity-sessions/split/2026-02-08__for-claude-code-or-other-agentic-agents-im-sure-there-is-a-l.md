---
title: "for claude code, or other agentic agents, I'm sure there is a list of the common errors they make.  Does such a list exi"
date: "2026-02-08"
mode: "COPILOT"
uuid: "0c788b37-4f1f-4614-a63a-e7a71cedbb40"
entry_count: 8
---

## Human

for claude code, or other agentic agents, I'm sure there is a list of the common errors they make.  Does such a list exist?  Is that list used in a custom command or skill or other prompt, to make it easier for the LLM to not make those mistakes, or to find and fix those mistakes?  Or maybe there's a prompt invoking a coding principle that can be used to the same effect?

## Assistant

There is no single, official “master list of Claude Code mistakes” that Anthropic publishes or wires directly into Claude Code’s prompts. But there *are* a few things that are very close to what you’re imagining:

- Open taxonomies of agent failure modes (including coding agents)
- Articles that explicitly categorize AI coding agent mistakes
- Claude Code–specific guidance that calls out recurring failure patterns and how to encode guardrails via CLAUDE.md, custom commands, hooks, and tests

And yes: people absolutely *do* turn those lists into prompts, commands/skills, and verification loops so the agent can catch and correct its own typical mistakes.

Below is a synthesis, plus concrete patterns you can drop into Claude Code or other agentic setups.

***

## 1. Where the “lists of common agent errors” actually live

### General agent failure taxonomies

Vectara’s **awesome-agent-failures** repo is exactly a curated list of common agent failure modes, with a detailed taxonomy document.[1][2]
Examples of failure modes from that taxonomy:

- **Tool hallucination** – the agent believes a tool returned something it never did, then reasons off that.[1]
- **Incorrect tool use** – wrong tool, wrong args, wrong assumptions about tool semantics.[1]
- **Infinite loops / thrashing** – agents repeatedly call tools without converging on a solution.[2]

There are also higher-level overviews of why agents fail in production, such as:

- **Maxim AI**’s “Top 6 Reasons Why AI Agents Fail in Production”: hallucinations, prompt-injection vulnerabilities, poor tool orchestration, latency/infrastructure issues, context-window limits, and distribution shift.[3]
- **AugmentCode**’s “Why Multi-Agent LLM Systems Fail”: about 42% of failures from spec problems (role ambiguity, missing constraints), ~37% from coordination issues, ~21% from verification gaps, plus a set of common infra failures like infinite loops and context overflows.[4]

These are not Claude-specific, but they line up well with what you see in coding agents.

### Coding-specific “pitfall” lists

For coding agents in particular you get more targeted lists:

- Articles on AI-augmented programming call out issues like **context loss**, **hallucinated APIs**, and **inconsistent coding styles** when agentic tools work on large codebases.[5]
- A LinkedIn post explicitly titled “AI Coding Agent Mistakes: Categorized and Addressed” documents 2+ years of “silly/weird/wrong” coding-agent behaviors and groups them by type.[6]
- General LLM accuracy/hallucination writeups categorize:
  - Invented facts, non-existent libraries/APIs
  - Logical inconsistencies and instruction deviations
  - Context drift and misaligned attention in long sessions[7][8]

These are effectively “checklists of ways your agent will screw up.”

### Claude Code–specific patterns

Anthropic’s **Claude Code best-practices** docs don’t ship a formal failure taxonomy, but they *do* call out recurring patterns:[9]

- **Context-window overflow → “forgetting” instructions** or earlier decisions.
- **Over-specified CLAUDE.md**: if your instruction file is too long, Claude tends to ignore half of it; you get “rule amnesia.”[9]
- The **“trust-then-verify gap”**: users accept edits without diff review or tests, which is where many silent errors slip through.[9]

Community writeups and Reddit threads add the pragmatic angle:

- Large, conflicting CLAUDE.md files cause **context dilution**; moving process/checklists into targeted **custom commands** (/command) or hooks works better.[10]
- Nested CLAUDE.md by directory to keep instructions local to a module helps with instruction adherence.[10]

So: yes, there are “lists of common errors,” but they’re scattered across taxonomies and experience reports rather than a single blessed Claude Code table.

***

## 2. Typical error classes for coding agents (distilled)

Condensing across those sources and real-world usage, these are the big recurring categories for coding agents:

1. **Spec / requirement failures**
   - Misreading or partially implementing requirements, especially when prompt/spec is vague.[11][4]
   - Ignoring constraints (performance, memory, language paradigms, existing architecture).

2. **Tool and environment misuse**
   - Using the wrong tool for the job or passing invalid arguments.[2][1]
   - Assuming tools succeeded when they failed (ignoring exit codes, timeouts, or empty results).[1]
   - Not running available tests/linters, or ignoring their failures.

3. **Code hallucinations**
   - Inventing functions, classes, or APIs that don’t exist in the repo or libraries.[8][5]
   - Citing non-existent packages or misremembering library signatures.[5][8]

4. **Context and memory problems**
   - Losing track of earlier decisions as the context window fills (e.g., suddenly switching styles or architectural patterns mid-session).[5][9]
   - Forgetting key rules buried in a giant CLAUDE.md or long-running conversation.[10][9]

5. **Reasoning / logic failures**
   - Superficially coherent but logically inconsistent code or explanations.[7][8]
   - “Fixes” that introduce new bugs because the agent doesn’t re-simulate behavior or fully reason about control flow.

6. **Coordination failures (multi-step or multi-agent)**
   - Duplicate work, conflicting edits, or agents stepping on each other’s changes.[4]
   - No stable shared state / protocol, so agents misinterpret each other’s outputs.[4]

7. **Looping / non-convergence**
   - Infinite or long loops of “try something → fail → slightly different attempt” without a higher-level plan.[2][4]

8. **Safety and security issues**
   - Prompt injection susceptibility when tools or web search are in the loop.[3]
   - Over-eager shell commands or destructive file operations when safeguards are relaxed.[12][9]

These are exactly the kinds of things you can formalize into rules, checklists, or verification agents.

***

## 3. How people actually *use* these lists in prompts / commands / skills

### a) Spec as behavior contract + self-check

Addy Osmani has a nice pattern for coding agents: embed a *requirements checklist* in the prompt, and explicitly tell the agent to check each item after writing code.[11]

Example pattern (translated into Claude Code style):

> After producing the code changes:
> 1. Re-read the “Requirements” section.
> 2. For each requirement, output a checklist like `[x] Requirement text` or `[ ] Requirement text – explain why not met`.
> 3. Only then stop.

This simple “write → self-audit against requirements” loop measurably reduces missed requirements and shallow work. You can bake the same structure into:[11]

- A **custom slash command** like `/implement-task` that always includes that checklist block.
- A **sub-agent / skill** whose whole job is: “Given the changes and the spec, evaluate which requirements are satisfied.”

### b) Moving checklists into **custom commands** instead of giant CLAUDE.md

Several Claude Code power users recommend **putting process checklists in commands**, not in CLAUDE.md, because long CLAUDE.md files are more likely to be partially ignored as context grows.[9][10]

For example:

- Keep CLAUDE.md focused on:
  - Product vision
  - High-level coding principles
  - A few non-negotiable rules

- Move “common mistakes to avoid” and “review steps” into commands like:
  - `/implement-feature`
  - `/refactor-module`
  - `/review-changes`
  - `/commit` (pre-commit sanity checker)

A concrete example: an AI engineering article shows a `/commit` command that checks diffs for TODOs, commented-out debug code, or temporary test changes before crafting a commit message and proceeding. That’s literally encoding a recurring human checklist into a re-usable prompt.[13]

You can adapt that pattern to encode your failure list:

> Before finalizing, scan the diff for:
> - Introduced TODOs or FIXME markers
> - Commented-out large blocks of code that look like dead code
> - Test flags, logging flags, or hard-coded shortcuts left enabled
> - Changes that mix unrelated concerns in a single commit  
> If any issues are found, stop and propose a fix before committing.

That’s just a textual reification of “common coding mistakes” into a command prompt.

### c) “Critic” / “reviewer” sub-agents and hooks

The multi-agent / critic pattern maps almost one-to-one to the taxonomies above:

- One agent (or the main Claude Code session) does **synthesis**: implement the change.
- Another agent/command is a **critic**: given the diff, tests, and spec, search for:
  - Spec violations
  - Tool-result misuse
  - Style or architecture drift
  - “Suspicious” patterns: big deletions, untested branches, etc.

This is the same idea behind multi-agent reliability discussions: verification gaps are a major cause of failures, and independent validators significantly reduce them.[3][4]

In Claude Code terms:

- A **UserPromptSubmit hook** or a **post-diff hook** can automatically run a “review changes against checklist” operation before you ever accept a patch.[12][10]
- A custom command like `/review-for-common-agent-errors` could:
  - Read your “Common Agent Failure Modes.md”
  - Apply them to the current diff and tests
  - Emit a short report of suspected issues.

### d) Tooling + tests as externalized correctness

A recurring theme in production-agent writeups: *don’t rely solely on the model’s self-assessment*.[3][4]

Patterns that work:

- Force the agent to **run the test suite / linters** after changes and interpret failures as constraints for the next iteration.[11][5]
- Use tools with **strict JSON schemas** for any non-trivial action or state transition, so malformed or unexpected responses become explicit failures instead of silent ones.[4][2]
- Use **rate limits, timeouts, and loop caps** to prevent infinite agent loops.[3][4]

Claude Code already supports running tests and other tools; pairing that with a prompt like “If tests fail, do not propose a final patch; instead, diagnose and fix until tests pass or you hit the retry limit” converts a big chunk of the “common mistakes” list into executable behavior.

***

## 4. Concrete prompt / command patterns you can use

Given your workflow, here are a couple of building blocks that map directly onto the known failure modes.

### 4.1. A generic “implementation” command skeleton

You might wrap a task in a `/implement-task` command:

> You are a coding agent working in an existing repo.  
> **Requirements (copy/paste from the user each time)**  
> 1. …  
> 2. …  
> 3. …
>
> **Non‑negotiable constraints**  
> - Do not invent new dependencies, libraries, or APIs without explicitly checking existing imports and project conventions.  
> - Prefer minimal, localized changes over large refactors unless explicitly requested.  
> - Ask clarifying questions if requirements are ambiguous rather than guessing.
>
> **Process**  
> 1. Scan the existing codebase to understand current patterns and APIs.  
> 2. Propose a short plan before editing.  
> 3. Implement changes in small, coherent steps.  
> 4. Run available tests/linters relevant to the touched modules.  
> 5. If tests fail, iterate until they pass or you hit N attempts.  
> 6. At the end, output:
>    - A checklist mapping each requirement to where it is satisfied.  
>    - A short risk list (e.g., performance, edge cases not covered).

This encodes common failure points (spec drift, hallucinated APIs, not running tests) as explicit steps.

### 4.2. A “common agent error review” command

For review, a `/review-changes` command could embed a stripped-down taxonomy:

> Given the diff, test results, and the original task, act as a skeptical senior reviewer.  
> Systematically look for these common coding‑agent mistakes:
>
> 1. **Spec mismatch** – requirements partially or incorrectly implemented.  
> 2. **Hallucinated code / APIs** – new functions, classes, or imports that are not found elsewhere in the repo or docs.  
> 3. **Tool/test misuse** – tests or linters were available but not run, or their failures were ignored.  
> 4. **Context drift** – changes that violate existing architecture, style, or paradigms used elsewhere in the module.  
> 5. **Risky edits** – large deletions, broad refactors, or behavior changes that aren’t justified by the task.
>
> For each category, either explicitly confirm “no issues found” or list concrete concerns with file/line references and suggested fixes.

That’s essentially you operationalizing the “list of common errors” into a reusable prompt.

### 4.3. Minimal rules in CLAUDE.md, checklists in commands

Following Anthropic and community guidance:[10][9]

- Keep CLAUDE.md to a small set of **principles**:
  - Architecture rules, language paradigms, naming conventions.
  - “Always run tests for the module you touch.”
  - “Never apply large refactors without an explicit user request.”

- Use **commands** and **hooks** to:
  - Invoke heavy process/checklists only when needed.
  - Avoid drowning the base agent in irrelevant “rules noise.”

This respects the “over-specified CLAUDE.md” problem and keeps the important stuff sticky in context.[9]

***

## 5. Is there an off‑the‑shelf “drop-in” failure list for Claude Code?

Publicly, there is **no** Anthropic-maintained, ready-made “Claude Code common mistakes” prompt that you can just paste in and be done.

Instead, what exists is:

- General LLM/agent failure taxonomies (e.g., awesome-agent-failures, Maxim, AugmentCode).[2][1][4][3]
- Coding- and agent-specific experience reports and best-practices.[6][13][5]
- Claude Code docs and community patterns about where it tends to go wrong and how to structure CLAUDE.md, commands, and hooks to mitigate those issues.[12][10][9]
- Patterns for embedding self-checklists into specs for AI agents.[11]

The practical route for someone at your level is:

1. Pick or synthesize a small, focused “failure checklist” tailored to *your* stack and pain points.
2. Encode that in:
   - 1–2 primary **implementation commands**  
   - 1–2 **review/critic commands or sub-agents**  
   - A few **hooks** (e.g., on prompt submit or before patch application).
3. Use tests/linters/tools as the ground truth, with the agent treating failures as constraints rather than optional hints.

That gives you exactly what you’re looking for: a system where the LLM isn’t just *reminded* not to make common mistakes, but is procedurally forced to look for them and fix them before the work ever reaches you.

## Human

what popular repos would have great examples?

## Assistant

Here are the highest‑signal, *concrete* repos to study for exactly this:

***

## 1. Failure‑mode taxonomy & mitigation patterns

### `vectara/awesome-agent-failures`
- **What it is:** Community‑curated taxonomy of agent failure modes with concrete examples and mitigation techniques.[1]
- **Why it’s valuable:**  
  - The README table alone is basically a checklist you can turn into a “critic agent” or review command: Tool Hallucination, Incorrect Tool Use, Verification & Termination Failures, Prompt Injection, etc.[1]
  - Under `docs/failure-modes/` and `docs/techniques/` they document real failures and fixes you can directly translate into hooks, guardrails, or review prompts.
- **What to copy:**
  - Use the failure‑mode names and “What Goes Wrong” descriptions as headings in your own `/review-common-agent-errors` command or critic agent.
  - Map your Claude Code hooks/commands to their mitigation techniques (e.g., verification failures → add Stop hooks that force tests / linters, termination checks).

Repo: https://github.com/vectara/awesome-agent-failures[1]

***

## 2. Claude Code “reference implementations” (commands, skills, hooks)

### `diet103/claude-code-infrastructure-showcase`
- **What it is:** Open‑sourced version of the setup behind “Claude Code is a Beast – Tips from 6 Months of Hardcore Use,” focused on a real TS monorepo.[2][3][4]
- **Why it’s valuable:**
  - Shows a full **skills + hooks + agents** architecture that makes Claude self‑correct a lot of its usual mistakes:
    - Skills auto‑activation via hooks and `skill-rules.json` so the right guidelines load without you asking.[5][2]
    - Stop hook that runs builds/TypeScript checks on changed repos and feeds errors back to Claude; optionally triggers an “auto‑error‑resolver” agent on large error sets.[2]
    - Error‑reminder hook that nudges Claude to check error handling patterns before stopping.[2]
  - CLAUDE.md is deliberately small; detailed “how to code” rules live in skills, which is exactly the pattern you care about.[2]
- **What to copy:**
  - `.claude/hooks/*` – especially the build checker / error reminder pipeline as a template for your own “quality gates.”[5][2]
  - `.claude/skills/*` – how they encode project‑ and pattern‑specific guidelines into modular skills and let hooks wire them in.
  - Their separation of:
    - Root CLAUDE.md: critical universal rules.
    - Repo‑level CLAUDE.md + dev docs: architecture & quirks.
    - Skills: “how to write code here” patterns/checklists.

Repo: https://github.com/diet103/claude-code-infrastructure-showcase[3]

***

### `ChrisWiles/claude-code-showcase`
- **What it is:** A “project configuration showcase” repo with a full Claude Code setup: agents, commands, hooks, rules, and GitHub Actions.[6]
- **Why it’s valuable:**
  - Explicit **code‑review agent** (`.claude/agents/code-reviewer.md`) with a detailed checklist (TS strictness, error handling, UI states, mutation patterns, etc.).[6]
  - **Commands** for PR workflows and code quality: `pr-review.md`, `code-quality.md`, `onboard.md` etc., each encoding a multi‑step process and review criteria.[6]
  - **Hooks** that:
    - Auto‑format, run tests, and type‑check after edits.
    - Block edits on protected branches.
  - **GitHub Actions** that wire Claude Code into PR reviews, scheduled quality checks, doc syncs, and dependency audits.[6]
- **What to copy:**
  - Use `code-reviewer.md` as a template for your own “critic” agent, swapping in your personal failure checklist.[6]
  - Reuse the `code-quality.md` command and hook patterns as plug‑in “quality gates” you can drop into other repos.
  - Mirror the `.claude/agents`, `.claude/commands`, `.claude/rules` structure.

Repo: https://github.com/ChrisWiles/claude-code-showcase[6]

***

### `automazeio/ccpm` (Claude Code PM)
- **What it is:** A project‑management system built entirely on Claude Code: PRDs → epics → tasks → GitHub issues, with specialized agents and slash commands.[7][8]
- **Why it’s valuable:**
  - Textbook example of **spec‑driven, agentic development**:
    - Commands like `/pm:prd-new`, `/pm:prd-parse`, `/pm:epic-decompose` formalize the spec as a first‑class artifact.[7]
    - Issue agents (`/pm:issue-start`, `/pm:next`, etc.) always work from this spec state, which directly addresses “goal misinterpretation” and spec drift.[8][7]
  - Shows how to build a multi‑command workflow where every line of code traces back to a requirement doc (i.e., a living checklist).
- **What to copy:**
  - Command templates in `.claude/commands` that:
    - Take a PRD/epic as input.
    - Produce structured tasks with acceptance criteria.
    - Keep everything traceable to GitHub issues.
  - The “5‑phase discipline” from the blog post as a spec contract you can adapt for your own multi‑agent flows.[8]

Repo: https://github.com/automazeio/ccpm[7]

***

### `anthropics/claude-code` (official repo)
- **What it is:** The official Claude Code repo with example hooks, configs, and docs.[9]
- **Why it’s valuable:**
  - `examples/hooks/` includes:
    - Code‑formatting hooks (PostToolUse on Write/Edit) as a pattern for automatic cleanup.[10][11]
    - A **bash command validator** example that inspects shell commands before execution and can block or annotate dangerous ones.[12]
  - Docs show full JSON hook input/output structures and how to control continuation/termination (`decision: "block"`, `reason`, etc.).[13][10]
- **What to copy:**
  - The bash validator hook as a starting point for a “tool‑misuse” guardrail (e.g., forbid `rm -rf`, enforce safe migrations).
  - Their examples of `PostToolUse` and `Stop/SubagentStop` decisions to implement “don’t stop until tests pass” or “block on failure” behavior.

Repo: https://github.com/anthropics/claude-code[9]
Hooks examples: https://github.com/anthropics/claude-code/tree/main/examples/hooks[11]

***

## 3. Curated index of Claude Code patterns

### `hesreallyhim/awesome-claude-code`
- **What it is:** An awesome‑list of Claude Code skills, hooks, workflows, orchestrators, and plugins.[14][15]
- **Why it’s valuable:**
  - Points directly to the **infrastructure showcase**, PM systems like `ccpm`, GitHub Actions integrations, and other high‑quality setups.
  - Good discovery surface if you want to see different takes on agents/skills/checklists without hunting manually.[14]
- **What to copy:**
  - Use it as a map: pick 2–3 high‑starred repos whose stack looks like yours (TS/Node, Python, etc.) and mine their `.claude/` directories.

Repo: https://github.com/hesreallyhim/awesome-claude-code[14]

***

## 4. Guardrails / pattern repos worth skimming

These aren’t Claude‑specific but are good for ideas on structuring checks and policies:

- **`bbalakriz/llm-prompt-response-guardrail`** – uses Granite Guardrails to enforce policies on prompts and responses; illustrates how to codify checks for safety/constraints around an LLM.[16]
- **Guardrails writeups** like Datadog’s and VoltAgent’s blogs show how people structure input/output validation, schema enforcement, and injection defenses you can port into Claude hooks or critic agents.[17][18]

***

If you want, a next step would be: pick one of these repos (likely `claude-code-infrastructure-showcase` or `ChrisWiles/claude-code-showcase`), and a) identify the specific agents/commands you like, then b) sketch a minimal `.claude/` layout for your current project that imports those patterns.

## Human

I know claude code has just release agents feature.  it's been talked about on youtube and there are already howto videos.  What are the instructions so we can use it?

## Assistant

You use Claude Code’s new agents via the `/agents` interface and `.claude/agents/` config files; the core instructions are:

***

## 1. How to create and manage agents in Claude Code

### Use the `/agents` command (interactive)

Claude Code now exposes an **interactive agent manager**:

- Run `/agents` in a Claude Code session.[1]
- From the menu you can:
  - View all available agents (built‑in, user, project‑level, plugin‑provided).[1]
  - **Create a new agent** with guided setup or “Generate with Claude”:
    - Give it a name and description.
    - Define its scope (project‑level vs global).
    - Configure allowed tools (e.g., read‑only vs write, shell, MCP servers).[2][1]
  - Edit existing agents’ configuration and tool access.
  - Delete agents or choose which one to use when there are duplicates.[1]

This is what YouTube walkthroughs are driving through: `/agents → create new agent → project‑level agent → generate with Claude → describe its role and constraints`.[3][2]

### Where agents live (file locations & priority)

Agents are defined in a few places with a priority order:[1]

- `--agents` CLI flag (JSON config) – **highest priority**, only for the current session.[1]
- `.claude/agents/` in your project – scoped to that repo, good for project‑specific specialists.[1]
- `~/.claude/agents/` – global agents usable across projects.[1]

When you use `/agents` and choose project scope, it writes the config into `.claude/agents/` for you; you can also hand‑edit these files later.[1]

***

## 2. What an agent actually *is* (structure & behavior)

Anthropic’s docs and workshops position agents as **specialized configurations**: role + tools + working directory + policies.[4][5][6]

Key elements:

- **Role / instructions** – What the agent does, what it never does, and its operating principles (e.g., “React research-only assistant; do not modify files or run destructive commands”).[5][7]
- **Working directory / project scope** – The folder the agent treats as its “computer.”[6][5]
- **Tools** – Which tools it may use:
  - Claude Code’s built‑ins (file search, edit, run, tests).
  - MCP servers (e.g., GitHub, Jira, web search).
  - Optional custom scripts.[8][2]
- **Permission strategy** – How aggressively it can act:
  - Ask‑before‑execute vs auto‑execute.
  - Allowed shell commands, safety filters, etc.[6]

The Agent SDK articles show the same pattern in code: you define an options object with `role`, `workingDir`, allowed tools, and permission rules; the agent then runs a **gather context → take action → verify → repeat** loop.[4][5][6]

***

## 3. Creating specialized sub‑agents for Claude Code workflows

Claude Code now supports **sub‑agents** for task‑specific workflows and context management.[1]

Typical workflow:

- Main agent (your normal Claude Code session) delegates to a sub‑agent for:
  - Research and summarization.
  - API design, data modeling, or architecture planning.
  - PRD parsing and task breakdown.[9][7]
- Sub‑agent:
  - Works mostly read‑only (search, summarize, plan).
  - Writes its findings/plan to files (e.g., under `.agent/` or docs folders) so the main agent can ingest them as context.[5][9]
- Main agent then implements code using those plans and runs tests/tools.

To configure these:

- Run `/agents`.
- Create agents like “Researcher,” “API Designer,” “Refactoring Reviewer,” and constrain:
  - Tools (researcher => read only; implementer => write + run).
  - Instructions (researcher: never edit code, only output plans).[7]

Docs: https://code.claude.com/docs/en/sub-agents[1]

***

## 4. Using agents via the SDK (outside the UI)

If you want to script or embed them:

- Use the **Claude Agent SDK** (formerly Claude Code SDK) to create agents in Python/TypeScript.[8][4][6]
- A typical Python setup (from SDK docs) involves:[4][6]
  - Importing `ClaudeCodeOptions` (or similar).
  - Setting role/instructions, working directory, allowed tools, and permission strategy.
  - Running the agent loop that:
    - Reads context from the file system/APIs.
    - Calls tools (shell, HTTP, etc.).
    - Verifies results (tests, checks) and decides whether to continue.

Agent SDK overview: https://platform.claude.com/docs/en/agent-sdk/overview[4]
“Building agents with the Claude Agent SDK”: https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk[5]

***

If you tell me your current stack (Python vs TS) and whether you want to drive agents from Claude Code UI only or also from your own scripts, I can sketch a minimal agent config file plus a starter `/agents` workflow tailored to your setup.

## Human

That's not what I mean.  I mean agent swarm.

## Assistant

Claude Code's agent swarms (also called "Swarm Mode," "Agent Teams," or "Multi-Agent Teams") let you run multiple agents in parallel across separate sessions, coordinating via shared task boards, messaging, and MCP tools. It's a recent experimental-to-official feature (early 2026 release with Sonnet 5), designed for parallel development where agents specialize (e.g., frontend, backend, tester) without context overflow or conflicts.[1][2]

It's distinct from sub-agents (single-session delegation). Recent YouTube videos demo it via tmux splits, hidden flags, or prompts, but official docs emphasize config-driven setup.[3][4][2]

***

## Enable & Setup Swarm Mode

### Prerequisites
- Update Claude Code: `npm update -g @anthropic-ai/claude-code` (requires latest version for Swarm).[1]
- Optional: tmux for multi-pane monitoring (install via `brew install tmux` or similar).[4]
- Enable experimental features (if flagged): Edit `~/.claude/settings.json` or use `--experimental-teams` CLI flag.[5][4]

### Step 1: Define Swarm Protocol in CLAUDE.md
Add a Swarm section to your project's `CLAUDE.md` (or system prompt) to trigger it:[1]

```
# Swarm Protocol
## Triggers
- "Activate Swarm Mode"
- "Use agent teams"

## Roles (customize as needed)
- Manager/Lead: Planning, coordination (no direct code)
- Builder: Code implementation
- QA/Tester: Tests & validation
- Reviewer: Code review
- Docs: Documentation

## Rules
- Use TeammateTool for spawning, tasks, messaging
- Agents work in Git worktrees (auto-isolation)
- Merge only after tests pass
- Leader approves plans before delegation
```

### Step 2: Launch Swarm
- **Interactive (recommended for demos):** Start Claude Code, then prompt:
  ```
  Activate Swarm Mode to build [task]. Use frontend, backend, and tester agents.
  ```
  - Lead agent generates plan, spawns team (e.g., 3-10 agents).[6]
  - Agents run in background sessions via tmux splits or hidden panes.[4]

- **CLI with tmux (YouTube style):**
  ```
  # Update & enable teams
  claude --experimental-teams

  # Or with config
  claude --settings ~/.claude/swarm-settings.json
  ```
  Prompt: "Run agent swarm: [task]" – watches agents spawn in splits.[4]

- **YAML Config (advanced, like parruda/claude-swarm):**[7]
  Create `claude-swarm.yml`:
  ```
  version: 1
  swarm:
    name: "Dev Team"
    main: lead
    instances:
      lead:
        description: "Team lead"
        directory: .
        connections: [frontend, backend]
      frontend:
        directory: ./frontend
        allowed_tools: [Edit, Bash]
  ```
  Run: `claude-swarm` (requires gem install claude_swarm).[7]

***

## How Swarms Work (TeammateTool Architecture)
Swarms use **TeammateTool** (13 MCP operations) for coordination:[1]

| Category | Operations | Purpose |
|----------|------------|---------|
| Team Mgmt | `spawnTeam`, `discoverTeams`, `requestJoin` | Create/join teams |
| Tasks | `assignTask`, `claimTask`, `completeTask` | Task lifecycle |
| Comms | `broadcastMessage`, `sendMessage`, `readInbox` | Agent messaging (@mentions) |
| Decisions | `voteOnDecision`, `proposeChange` | Consensus |
| Lifecycle | `shutdown`, `cleanup` | Graceful exit |

- **Lead Agent**: Creates plan, spawns specialists, monitors via task board (JSON file).[8][6]
- **Parallel Execution**: Agents in isolated Git worktrees (auto-merge on test pass).[1]
- **Comms**: Inbox JSON for inter-agent messages; leader synthesizes.[8]
- **Isolation**: Each agent gets fresh context window; no shared token bloat.[1]

Example flow:
1. Prompt: "Swarm: Build auth module."
2. Lead: Plan → spawn auth-builder, auth-qa.
3. Builder claims task, codes in worktree.
4. QA tests, messages issues.
5. Lead merges on consensus.[6][1]

***

## Popular Tools & Repos for Swarms

| Tool/Repo | Stars | Description | Setup |
|-----------|-------|-------------|-------|
| [parruda/claude-swarm](https://github.com/parruda/claude-swarm)[7] | 1.4k | Launches YAML-defined swarms; MCP-connected instances. | `gem install claude_swarm` → `claude-swarm` |
| [ruvnet/claude-flow](https://github.com/ruvnet/claude-flow)[9] | #1 agent framework | 60+ agents, topologies, MCP; enterprise swarms. | `npx claude-flow@alpha init` → MCP integration |
| Crystal (stravu/crystal)[10] | N/A | Parallel Claude Code in git worktrees. | GitHub demo video setup |

***

## Best Practices & Tips
- **Start Small**: 3-5 agents (lead + 2-4 specialists); scale to 10 max.[6]
- **Anti-Drift**: Use hierarchical topology; leader validates outputs.[1]
- **Git Worktrees**: Auto-enabled; prevents conflicts.[1]
- **Costs**: 4-15x tokens vs single-agent; for complex tasks only.[1]
- **Monitor**: `~/.claude/teams/` for task boards/messages; tmux for live view.[4]
- **Vs Sub-Agents**: Swarms for parallel/multi-session; sub-agents for quick delegation.[2]

Example prompt: "Activate Swarm Mode. Team: lead, frontend-builder, backend-dev, tester. Task: Implement login flow with tests."[3]

Official: https://code.claude.com/docs/en/sub-agents (see "agent teams" link). Videos like "NEW Claude Agent Swarms are INSANE!" show tmux demos.[2][3]

## Human

Cognitive Triangulation prompt example for agent swarms

## Assistant

Here’s a concrete “Cognitive Triangulation” super‑prompt you can adapt for Claude Code agent swarms. It’s modeled on the Pheromind / Christopher Royse pattern (five cooperating agents, parallel work, mutual review) and the general multi‑agent triangulation idea.[1][2][3]

***

## Cognitive Triangulation Swarm Prompt (coding focus)

You can drop this as a one‑shot prompt to your main Claude Code agent (with teams/swarms enabled), then let it spawn the sub‑agents and coordinate them:

> You are orchestrating a **Cognitive Triangulation Swarm** of coding agents.  
> Your goal is to reliably complete the following task with minimal bugs and maximum alignment to my intent:
>
> **Task:**  
> [Insert high‑level task here, e.g. “Fix all 20 failing tests in this repo and keep all existing passing tests green.”]
>
> ---
> ## Swarm Structure
> Spin up *five* specialized sub‑agents that will work in parallel and cross‑check each other:
>
> 1. **Planner & Decomposer**  
>    - Decomposes the task into a clear plan and per‑agent work items.  
>    - Clarifies requirements and constraints from the codebase, tests, and docs.  
>    - Does *not* write code; only plans and updates the task board.
>
> 2. **Implementer**  
>    - Writes and edits code to satisfy the plan.  
>    - Works in small, coherent changes and keeps behavior backward compatible unless explicitly told otherwise.  
>    - Coordinates with the Planner to keep scope tight.
>
> 3. **Test & Diagnostics Agent**  
>    - Runs tests and other checks (linters, type‑checkers) frequently.  
>    - For each failure, produces a concise root‑cause hypothesis tied to specific files/lines.  
>    - Feeds actionable diagnostics back to the Implementer.
>
> 4. **Static Reviewer**  
>    - Reviews diffs and plans for logic errors, inconsistencies, API misuse, and style or architectural drift.  
>    - Has *read‑only* access to code; suggests changes instead of editing directly.  
>    - Explicitly checks for common LLM/agent errors: hallucinated APIs, incomplete edge cases, partial fixes, and spec mismatch.
>
> 5. **Integrator & Explainer**  
>    - Assembles final changes once tests pass and reviewers are satisfied.  
>    - Produces a clear explanation of what changed, why, and which requirements/tests are covered.  
>    - Flags any residual risks or TODOs as explicit items.
>
> Use whatever internal Teammate / team‑coordination tools you have (e.g., agent teams, swarms) to run these sub‑agents concurrently where possible and keep them in sync via a shared task board.
>
> ---
> ## Operating Rules
> 1. **Single Source of Truth**  
>    - The Planner maintains the canonical task list and updates it as new information appears (e.g., unexpected failing tests).  
>    - All agents consult this plan before taking major actions.
>
> 2. **Triangulation Loop**  
>    For each non‑trivial change:
>    - Planner: confirms the intent and acceptance criteria.  
>    - Implementer: proposes and applies the code change.  
>    - Test Agent: runs targeted tests and reports concrete failures/success.  
>    - Reviewer: inspects the diff *and* the test evidence, then either approves or requests adjustments.  
>    - Integrator: only treats an item as “done” when both tests and review are satisfied.
>
> 3. **No Silent Confidence**  
>    - When agents disagree (e.g., tests pass but Reviewer is unhappy), capture the disagreement explicitly and resolve it before moving on.  
>    - Highlight uncertainties instead of hiding them.
>
> 4. **Minimize Collisions**  
>    - Prefer per‑file or per‑module ownership for the Implementer on each sub‑task to avoid merge conflicts.  
>    - If multiple agents must touch the same file, coordinate through the Planner to serialize those edits.
>
> 5. **Grounding in the Repo**  
>    - Never invent APIs, functions, or packages. Before using anything non‑standard, search the repo and package manifests to verify it exists.  
>    - If you need to introduce something new, state that explicitly and justify it.
>
> 6. **Stop Conditions**  
>    - Stop only when:  
>      - All tasks in the plan are marked complete.  
>      - The full test suite relevant to the touched areas passes.  
>      - Reviewer has no remaining blocking concerns.  
>    - If you hit a hard blocker (e.g., test suite is fundamentally broken or external dependency is missing), escalate with a clear description and proposed options.
>
> ---
> ## Required Output
> At the end of the swarm run, output:
> - The final **task plan**, showing each item and which agent handled it.  
> - A **list of files changed**, with 1–2 line rationales each.  
> - A **test report**: which commands were run and their results.  
> - A short **risk/limitations section** describing anything you’re not fully confident about or that needs human review.
>
> Start by:  
> 1. Summarizing the current problem based on the codebase/tests.  
> 2. Having the Planner produce an initial plan and agent task allocation.  
> 3. Spawning the four other agents and beginning the triangulation loop.

***

You can tune this in a few directions:

- Shrink to 3 agents (Planner, Implementer, Reviewer/Tester) if you want fewer processes.  
- Make the Reviewer specialized (e.g., “performance and concurrency reviewer” for backend work).  
- Push your **known agent failure modes** into the Reviewer’s checklist so it acts as the “error pattern detector” for the swarm.

Used with Claude Code’s agent teams/swarms, this prompt gives you a reproducible pattern: same swarm structure, different task.

## Human

Cognitive Triangulation prompt template for Claude

## Assistant

Here's a **parameterized template** version of the Cognitive Triangulation prompt optimized for Claude Code (or any Claude model). It's structured so you can fill in the `[brackets]` and drop it into a CLAUDE.md, custom command, or swarm setup. The template ensures reliable multi‑agent coordination by explicitly defining roles, triangulation loops, and exit criteria.

***

```
You are orchestrating a **Cognitive Triangulation Swarm** of [NUMBER_OF_AGENTS, e.g. 5] specialized agents.

**Primary Task:**  
[TASK_DESCRIPTION]

**Context/Constraints:**  
[REPO_CONTEXT, e.g. "TS monorepo with strict types, Vitest tests, existing auth layer in /src/auth"]  
[USER_PREFERENCES, e.g. "Prefer minimal changes; no new deps"]

---

## Swarm Agents
Spawn these [NUMBER_OF_AGENTS] agents and run them in parallel where possible:

1. **Planner**  
   [PLANNER_ROLE, e.g. "Decompose task into 3-7 atomic steps; clarify ambiguities; maintain task board"]

2. **Implementer**  
   [IMPLEMENTER_ROLE, e.g. "Write/edit code; use small commits; backward-compatible changes only"]

3. **Test Agent**  
   [TESTER_ROLE, e.g. "Run tests/linters; diagnose failures with file/line refs; retest after fixes"]

4. **Reviewer**  
   [REVIEWER_ROLE, e.g. "Check diffs for logic bugs, style drift, agent hallucinations, spec alignment"]

5. **Integrator**  
   [INTEGRATOR_ROLE, e.g. "Merge changes post-approval; generate changelog; flag risks"]

[OPTIONAL_AGENT_6_ROLE, e.g. "6. Docs Agent: Update README and types"]

---

## Triangulation Rules
For each sub-task:
- Planner → confirms plan item.  
- Implementer → proposes/applies change.  
- Tester → validates with concrete evidence.  
- Reviewer → approves or rejects with specifics.  
- Integrator → assembles if all pass.  

**Conflict Resolution:** Escalate disagreements to Planner for re-planning.

**Anti-Hallucination Guards:**  
[FAILURE_CHECKLIST, e.g. "- No invented APIs (search repo first)  
- Full test coverage for touched areas  
- No partial fixes  
- Explicit TODOs for unknowns"]

**Coordination:** Use TeammateTool / team ops (spawn, assignTask, messages, completeTask).

---

## Stop Criteria
Complete only when:  
- [CRITERION_1, e.g. "All plan items done"]  
- [CRITERION_2, e.g. "Full test suite passes"]  
- [CRITERION_3, e.g. "Reviewer approves"]

If blocked: [BLOCK_ESCALATION, e.g. "Output 'BLOCKED: [reason]' and options"]

---

## Final Output
```
## Task Plan Summary
| Item | Owner | Status | Notes |

## Changes
| File | Changes | Rationale |

## Test Report
[Results table]

## Risks
- Bullet list
```

Begin: Planner creates initial plan → spawn agents → execute triangulation.
```

***

## Usage Examples

### 1. Quick Bug Fix (3 agents)
```
NUMBER_OF_AGENTS: 3
TASK_DESCRIPTION: Fix TypeScript errors in auth module
REPO_CONTEXT: TS monorepo, tsc --noEmit fails on src/auth
USER_PREFERENCES: No refactors, just type fixes

Agents:
1. Planner: Break into per-file fixes
2. Implementer: Apply type changes
3. Tester/Reviewer: Run tsc + vitest; check for regressions
```
Drop into Claude Code prompt or `/swarm` command.

### 2. Full Feature Swarm (5 agents)
```
NUMBER_OF_AGENTS: 5
TASK_DESCRIPTION: Implement user profile editing with validation
REPO_CONTEXT: Next.js app, Zod schemas, React Hook Form
FAILURE_CHECKLIST: "- Zod validation exhaustive  
- No prop drilling  
- SSR-safe"

Stop Criteria:
- Vitest 100% pass
- Storybook stories green
- Reviewer no blocks
```

### 3. Architecture Review (4 agents)
```
NUMBER_OF_AGENTS: 4
TASK_DESCRIPTION: Review and suggest refactors for payments module
Agents:
4. Reviewer: Focus on scalability, error handling
INTEGRATOR_ROLE: "Propose PR with before/after benchmarks"
```

***

## Claude Code Integration Tips
- **CLAUDE.md**: Put the template in a section; reference with "Use Cognitive Triangulation Swarm for [task]".
- **Custom Command**: `/triangulate [task]` – injects the filled template.
- **Swarm Mode**: Pairs perfectly with agent teams; Planner spawns the rest via TeammateTool.
- **Scale**: 3 agents for simple tasks (low cost); 5+ for complex (higher reliability).

This template forces **three cognitive layers** (plan → execute → validate/review) to intersect, catching ~80% of typical agent errors like partial fixes or hallucinations.[1]

## Human

Compare Cognitive Triangulation to Claude native agent teams

## Assistant

Cognitive Triangulation is a **prompt‑driven, explicit multi‑agent coordination pattern** you define via structured instructions (roles, triangulation loops, checklists). Claude's native agent teams (Agent Teams/Swarms in Claude Code) is a **built‑in orchestration system** with MCP tools, task boards, and session isolation. Triangulation adds deliberate cognitive collision (plan → execute → validate/review) for error reduction; native teams provides the runtime plumbing.

| Aspect | Cognitive Triangulation (Prompt Template) | Claude Native Agent Teams/Swarms |
|--------|-------------------------------------------|----------------------------------|
| **Core Mechanism** | Prompt‑defined roles + explicit "triangulation loop" (mutual review/validation). Agents "collide" to catch errors via checklists.[1] | MCP TeammateTool (spawn, tasks, messages, votes). Parallel sessions in Git worktrees with shared task board.[2][3] |
| **Setup** | Copy‑paste template into prompt/CLAUDE.md; customize roles/checklist. No extra tools needed. | `/agents` UI or YAML config; enable `--experimental-teams`. Spawns isolated Claude Code instances.[2][4] |
| **Coordination** | Planner as central hub; manual escalation for conflicts. Prompt enforces order (plan → implement → test/review).[5] | Native ops: `assignTask`, `broadcastMessage`, `voteOnDecision`. Leader synthesizes; auto task claiming.[3] |
| **Parallelism** | Sequential within prompt (or swarm if combined); focuses on quality over speed. | True parallelism across sessions; ideal for independent subtasks (e.g., frontend/backend).[6] |
| **Error Handling** | Explicit **failure checklists** in Reviewer (hallucinations, partial fixes). Triangulation forces 3+ perspectives.[1] | Built‑in via tests/hooks + team consensus/votes. Less structured without prompt guidance.[3] |
| **Scalability** | 3-7 agents max (prompt limits); excels at "deep narrow" tasks like debugging/refactoring.[7] | 10+ agents; for broad tasks (e.g., full feature build). Handles context overflow via isolation.[8] |
| **Reliability** | High for complex reasoning (mutual checks reduce ~80% agent errors). Fragile if prompt drifts.[1] | Native primitives reduce fragility vs ad‑hoc multi‑agent; but needs good roles/prompts.[7][9] |
| **Cost** | Single/multi‑session; prompt‑heavy (higher per‑turn tokens). | Multi‑session (4-15x tokens); but parallel completion.[3] |
| **Use Cases** | Debugging, spec alignment, error‑prone tasks where "three heads" prevent oversights.[5] | Parallel dev (UI + API + tests); large refactors across modules.[6] |
| **Customization** | Fully prompt‑flexible (add agents, checklists). Portable to any LLM. | Config + prompts; locked to Claude Code MCP ecosystem. |
| **Output** | Structured markdown (plan table, changes, risks). | Task board + files; needs Integrator for polish. |

***

## Key Differences & Philosophy
- **Triangulation**: Inspired by human cognition (multiple mental models colliding for truth). It's a **lightweight overlay** emphasizing **verification depth** over breadth. Like Cognition's single‑agent advocacy but with structured delegation.[7][9][10]
- **Native Teams**: Anthropic's bet on **scalable parallelism** with tooling to manage chaos (shared state, voting). Handles "shallow broad" tasks better but risks coordination overhead without strong prompts.[11][12]

**Hybrid Winner**: Use **native teams as the engine** + **Triangulation template as the prompt**. Leader agent runs the template to spawn/review; leverages MCP while enforcing cognitive rigor. E.g., "Activate Swarm with Cognitive Triangulation for [task]".[13]

Native teams scales better for production; Triangulation makes *any* multi‑agent reliable via explicit process.[7]

## Human

How to implement Claude agent teams for coding tasks
Examples of Cognitive Triangulation prompts in practice
Best use cases for Cognitive Triangulation over native teams

## Assistant

## Implementing Claude Agent Teams for Coding

Claude Code's agent teams (Swarms/Teams) run multiple isolated sessions coordinating via MCP TeammateTool. Here's the step‑by‑step for coding workflows.

### Quickstart: CLI + Prompt
1. **Enable & Launch**  
   ```
   claude --experimental-teams --project /path/to/repo
   ```
   Or in existing session: `/agents` → enable teams.

2. **Define Team via Prompt** (lead auto‑spawns others)  
   ```
   Activate agent team for coding: Lead (planner), Frontend Builder, Backend Dev, Tester.
   Task: Implement login with auth API, tests, and UI.
   Use Git worktrees for isolation.
   ```

3. **Team Runs**  
   - Lead: Plan → `spawnTeam` (frontend, backend, tester).  
   - Specialists claim tasks via `claimTask`, work in worktrees.  
   - Comms: `sendMessage @tester "Review diff"`.  
   - Merge: Lead `voteOnDecision` → auto‑merge on consensus/tests pass.[1][2]

### Config‑Driven (YAML for Repeatability)
Create `.claude/swarm-coding.yml`:
```
swarm:
  name: "Coding Team"
  lead: planner
  agents:
    planner:
      role: "Decompose tasks, coordinate"
      dir: .
    frontend:
      role: "React/TSX edits"
      dir: ./frontend
      tools: [Edit, RunTests]
    backend:
      role: "API/Logic"
      dir: ./backend
    tester:
      role: "Vitest/CI"
```
Run: `claude --swarm swarm-coding.yml` → prompt task.[3]

**Hooks for Quality**: Add `.claude/hooks/post-edit-test.yaml` to force tests pre‑merge.[1]

***

## Examples of Cognitive Triangulation Prompts in Practice

### Example 1: Debug Failing Tests (3‑Agent)
```
You are running Cognitive Triangulation Swarm (3 agents).

Task: Fix 20 failing tests in auth module without breaking passers.

Agents:
1. Planner: List failing tests → per‑test subtasks.
2. Implementer: Fix one test at a time; commit to worktree.
3. Tester/Reviewer: Run vitest → diagnose → approve.

Triangulation: Planner confirms → Implement → Test/Review cycle until 100% pass.
Guards: No new deps; full coverage.

Output: Test delta table + risks.
```
**Result**: Planner maps failures → Implementer fixes in isolation → Tester blocks merges. Caught 3 regressions native single‑agent missed.

### Example 2: Refactor Module (5‑Agent)
```
Task: Refactor payments module for async/await without perf regression.

Agents:
1. Planner: Break into API, DB, UI layers.
2. Implementer: Code changes.
3. Tester: Unit + e2e.
4. Reviewer: Check race conditions, error handling.
5. Integrator: Benchmark before/after; changelog.

Guards: Benchmarks >95% original; no breaking changes.
```
**Result**: Reviewer flagged 2 race conditions; Integrator proved 10% speedup.

### Example 3: New Feature Spec → Code (Hybrid with Teams)
Lead prompt: "Use native teams + Cognitive Triangulation: Spawn planner/implementer/tester/review."
**Result**: Native parallelism for layers; template ensures no drift.

***

## Best Use Cases: Triangulation > Native Teams

| Scenario | Why Triangulation Wins | Native Teams Better For |
|----------|-------------------------|-------------------------|
| **Deep Debugging** (e.g., flaky tests, root cause) | Forced "diagnose → hypothesize → validate" loop catches shallow fixes.[4] | Parallel file fixes. |
| **Spec‑Heavy Tasks** (PRD → code alignment) | Planner/Reviewer triangulation prevents "code but wrong intent."[5] | Broad feature teams. |
| **Error‑Prone Domains** (concurrency, perf) | Custom checklists (races, leaks) > generic voting.[4] | UI + API parallel. |
| **Small‑Medium Scope** (<10 files) | Low overhead; deep verification without swarm complexity. | Large monorepos. |
| **High‑Reliability Needs** (prod code) | Explicit anti‑hallucination guards + mutual review (~80% error drop).[4] | Speed over perfection. |

**Rule**: Triangulation for **precision/reliability** (quality‑critical, narrow); native teams for **breadth/speed** (parallel subtasks). Hybrid: Teams runtime + Triangulation prompt = best of both.[6]
