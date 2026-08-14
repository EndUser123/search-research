---
title: "You are primarily a technical editor. As a knowledge systems engineer, you synthesize workflows and preserve unique insi"
date: "2025-12-24"
mode: "COPILOT"
uuid: "0ed01f02-e99f-4bc8-8787-234822c83b51"
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

Agent harnesses extend context engineering to coordinate multiple agents and sessions so long-running coding tasks become more reliable, but they still depend on strong guardrails, handoffs, and human-in-the-loop checkpoints rather than pure “hands-off” vibe coding.[1]

## Core ideas about agent harnesses

- An agent harness connects many agent sessions (or repeated runs of one agent) into a **structured** long-running workflow with checkpoints, handoffs, guardrails, and optional human oversight.[1]
- Harnesses are framed as the evolution of prompt engineering → context engineering → multi-session harnesses that manage reasoning, memory, tools, and subagents across long tasks.[1]
- The key value comes from the *layer around* LLMs (reasoning patterns, memory systems, tool orchestration), not raw model scaling, which is argued to be hitting diminishing returns.[1]

## Architecture and components

- Common pattern: an initializer agent sets up the project (requirements, scaffolding, feature list, repo) and a task/coding agent runs in a loop to make incremental progress with periodic context resets to avoid context rot.[1]
- Harnesses wrap an existing context engine: prompt engineering, retrieval (RAG), short- and long-term memory, file-system and git-based memory, and subagents for isolated tasks (e.g., research).[1]
- Core harness elements:
  - Guardrails: checks at the beginning or end of agents (especially the initializer) to ensure the project/codebase is ready and healthy.[1]
  - Checkpoints: tests and environment checks run between stages to detect “going off the rails” early.[1]
  - Handoffs: offloaded artifacts (progress files, feature lists, codebase state, git log) that the next session reads to quickly rebuild working context.[1]
  - Human-in-the-loop: interrupt points where a human can validate, approve, or correct before the harness continues automatically.[1]

## Context and memory strategies

- Context engineering remains central: provide the right context at the right time while avoiding context rot and overfilling the window.[1]
- Typical priming flow at session start:
  - Read persisted progress files produced by prior sessions.  
  - Inspect git log as a memory source to infer what has been built and changed.  
  - Read portions of the codebase to reconstruct state.[1]
- File system as memory is emphasized across multiple systems (Anthropic harness, LangChain DeepAgents, Manus): codebase + progress files + git log together provide a rich, inspectable memory substrate.[1]
- Memory compaction and retrieval are used to keep context windows small while still letting agents pull needed docs and prior decisions.[1]

## Anthropic long-running harness pattern

- Anthropic’s open-sourced harness defines an appspec (PRD-like spec) that the initializer agent uses to:
  - Generate a large feature-list JSON with >200 features and their validation criteria.  
  - Create an init script, scaffold the project, and initialize a git repo (used as core memory).[1]
- Subsequent sessions use a coding agent running in a loop to:
  - Prime itself by reading files, git log, and prior progress.  
  - Run regression tests and environment checks.  
  - Pick the next high-priority feature, implement it, run tests, and self-validate.  
  - Update the feature list and a dedicated progress file (e.g., `claude_progress.txt`), then commit to git.[1]
- The system loops until all tests pass and all features are implemented, with the feature list acting as the single source of truth for completed/validated work.[1]

## Example outcomes and integrations

- A 24-hour run of the Anthropic harness built a working Claude-like chat application (chat UI, conversations, folders, themes, pinned chats) without human intervention, though this is presented as experimental rather than recommended practice.[1]
- The same harness concept was adapted to use Linear as the task-tracking surface instead of local files: feature list and progress updates become Linear tasks and comments, turning “progress files” into familiar work artifacts.[1]
- Viewers report:
  - Running similar harnesses for 8–35 hours for front-end and back-end work, with agent harnesses becoming their primary way of coding.[1]
  - Evolving harnesses across multiple versions (e.g., A1–A5), with later harnesses partially generated by earlier ones and tracking metrics on prompts, orchestration, and harness performance.[1]
  - Using Anthropic’s Agent SDK, Claude Code, WezTerm, and tmux as the operational environment for long-running harnesses.[1]
  - Running the Linear agent harness with their own Claude Code setup successfully for hours, only intervening to avoid hitting usage limits.[1]
  - Porting the Linear harness pattern to other tools like ClickUp to track agent progress.[1]

## Guardrails, bounded attention, and reliability issues

- Bounded attention: large context windows still hit “dumb zones” when overloaded, so harnesses rely on:
  - Memory compaction and selective handoffs.  
  - Progress files capturing key state and decisions.  
  - Subagents for isolated tasks.[1]
- Current summarization and handoff quality is described as **inconsistent**:
  - Progress files sometimes miss important details (e.g., failed validation and how it was fixed).  
  - Missing resolution steps can cause the same bug or failure pattern to repeat across sessions.[1]
- Predictive context is described as a hard problem: future-critical observations cannot reliably be predicted at capture time, making it difficult to know what must be preserved for later sessions.[1]
- Reliability math: with per-step reliability of 95%, a 20-step multi-agent pipeline has only about 36% end-to-end reliability (\(0.95^{20}\) ≈ 0.36), so purely autonomous long harnesses are unlikely to be trustworthy without more structure.[1]
- To achieve “true” vibe coding (no human oversight) for long tasks, the harness would need near-99.9% reliability over potentially hundreds of steps, which is deemed unrealistic for current agents.[1]

## Human-in-the-loop and autonomy balance

- Harnesses should be as autonomous as possible while exposing **strategic** injection points:
  - Simple UI-level approvals like “check this box to continue” after a feature is implemented or a website is deployed.  
  - Inline human review when tests pass but semantics or UX still need inspection.[1]
- Effective harnesses are described as heavily engineered systems rather than simple “give the agent the repo and let it go” setups.[1]
- With robust human-in-the-loop checkpoints and well-defined self-validation, partial “vibe coding” becomes viable: nearly all coding is delegated, but the system is scaffolded by engineered guardrails and lightweight human approvals.[1]

## External tools, platforms, and related work

- OutSystems Agent Workbench:
  - Low-code agent builder with workflows for short-term memory, system prompts, long-term memory, multi-attention workflows, and custom tools.  
  - Provides observability dashboards, analytics, error tracing, user and environment management, and one-click deployment for enterprise-grade agents.[1]
- LangChain DeepAgents:
  - Provide a harness-style architecture with context management using file-system tools for non-coding and coding tasks.[1]
- Manus:
  - Shares context-engineering strategies where the file system acts as context.  
  - Emphasizes that you cannot predict which observation will be crucial many steps later, reinforcing the predictive-context challenge.[1]
- Commenters reference:
  - Using “Claude’s status line” to monitor context usage; handing off to a new session around 80% context utilization to preempt session degradation.[1]
  - Steve Yegge’s “Beads” concept plus MCP Agent Mail for direct agent-to-agent communication to help harnesses scale to multiple cooperating agents.[1]
  - Google’s “Conductor Extension for Gemini CLI” as a harness-style mechanism for Gemini.[1]
  - Goose’s “Adversarial Cooperation in Code Synthesis” paper for the G3 coding agent, related conceptually to adversarial multi-agent workflows (details of implementation unknown in the thread).[1]

***

## Operational patterns and setups

### Multi-model and multi-agent flows

- Use an initializer + task agent pattern:
  - Initializer agent: ingest PRD/appspec, generate feature list JSON, scaffold project, initialize git, and set core guardrails.  
  - Task/coding agent: run in a loop across many sessions, each time re-priming from progress files, git log, and codebase, then implementing one feature and validating it.[1]
- Run many sessions sequentially with periodic context resets:
  - Each session reads the latest progress artifacts and code to rebuild working context.  
  - Context usage is monitored (e.g., using Claude’s status line), and a new session is started around 80% context usage.[1]
- Multi-version harness evolution:
  - New harness versions (e.g., A3–A5) are generated and refined by older harnesses, using tracked metrics on prompts, orchestration, and harness performance.[1]
- Multi-agent collaboration:
  - Use subagents for isolated tasks like research or environment verification, while a main coding agent focuses on implementation and regression testing.  
  - Explore patterns like Steve Yegge’s Beads plus MCP Agent Mail for direct agent-to-agent messaging to coordinate larger agent swarms.[1]

### Automation patterns

- Long-running coding harness:
  - Automatically cycle: prime → run tests → environment checks → select next feature → implement → run tests → self-validate → update progress artifacts → commit to git → repeat.[1]
  - Only pause automatically when tests fail repeatedly or when human intervention is requested at configured checkpoints.[1]
- Git as a first-class automation primitive:
  - Every completed step ends with a commit, providing a durable, inspectable memory of changes.  
  - Git logs also become a source for priming and regression-analysis in later sessions.[1]
- Integration with project trackers:
  - Mirror feature list and progress in systems like Linear or ClickUp so that each session updates tasks and comments as it progresses through features.  
  - Use tracker updates as both status reporting and a form of offloaded memory.[1]
- Telemetry-driven refinement:
  - Track metrics on prompts, orchestration steps, error rates, session lengths, and harness outcomes.  
  - Use those metrics to automatically propose or implement changes in the next harness version.[1]

### Guardrail artifacts and rules

- Progress files (e.g., `claude_progress.txt` or equivalent project-tracker meta tasks):
  - Must capture: what was implemented, tests run, validation outcomes, failures, and remediation steps.  
  - Serve as primary handoff artifact between sessions and as a debugging trail when harness behavior degrades.[1]
- Feature list JSON:
  - Encodes all planned features with explicit validation criteria, forming the backbone for planning and self-verification.  
  - Must be kept up to date as features are implemented or changed during the run.[1]
- Guardrail rules embedded in harness logic:
  - Always run tests and environment checks before selecting and implementing the next feature.  
  - Block progress if validations fail repeatedly, and either roll back via git or request human input.[1]
  - Trigger new sessions before context usage becomes too high (e.g., around 80% of the window).[1]
- Human-in-the-loop checkpoints:
  - After major milestones (e.g., a batch of features, or a user-visible deployment), require a quick human review/approval.  
  - Provide simple UI controls (e.g., a checkbox or short approval prompt) to minimize friction while maintaining reliability.[1]

***

## Practical recommendations

- Implement an initializer + coding-agent harness:
  - Define a structured appspec/PRD and generate a feature-list JSON plus validation criteria.  
  - Have an initializer agent scaffold the project, initialize git, and create core artifacts (feature list, progress file).[1]
- Use git and file system as primary memory:
  - Treat the codebase, git log, feature list, and progress file as the canonical memory layer.  
  - Ensure every session reads these before doing any new work.[1]
- Add strong guardrails:
  - Require tests and environment checks to pass before moving to the next feature.  
  - Encode explicit rules that block progress when validations fail repeatedly and either roll back or ask for human help.[1]
- Engineer robust handoffs:
  - Standardize progress file structure so it always includes implemented work, failed validations, and how they were fixed.  
  - Make updating the feature list and progress artifacts mandatory at the end of each session.[1]
- Control context and session boundaries:
  - Monitor context usage (e.g., via model status lines) and switch to a fresh session when usage approaches a threshold like 80%.  
  - Keep per-session prompts focused, relying on offloaded artifacts rather than ever-growing context.[1]
- Build strategic human-in-the-loop checkpoints:
  - Insert lightweight approval steps after key milestones (e.g., every N features or before deployment).  
  - Make approvals fast: a quick UI action or short prompt that resumes the harness automatically once given.[1]
- Iterate on the harness itself:
  - Track reliability metrics per step and per run; log where failures occur.  
  - Periodically have an agent propose and implement changes to the harness code, then test these changes under supervision before fully adopting them.[1]
- Use existing platforms where helpful:
  - For enterprise or production use, consider platforms like OutSystems Agent Workbench to get observability, audit trails, and deployment workflows out of the box.  
  - Experiment with frameworks like Anthropic’s harness, LangChain DeepAgents, and Manus context strategies as reference implementations.[1]
