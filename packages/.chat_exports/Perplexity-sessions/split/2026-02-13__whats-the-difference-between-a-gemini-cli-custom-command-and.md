---
title: "what's the difference between a gemini cli custom command and skill?"
date: "2026-02-13"
mode: "COPILOT"
uuid: "cc4a2d75-ee5c-42c0-98f3-0f91a3d5d5d1"
entry_count: 4
---

## Human

what's the difference between a gemini cli custom command and skill?

## Assistant

**Custom Commands** are user-defined slash commands (e.g., `/refactor`) configured via `.toml` files, acting as manual shortcuts to trigger specific, reusable prompts for repetitive tasks like code reviews or boilerplate generation.[1][4][7]

**Skills**, in contrast, are self-contained directories (typically with a `SKILL.md` file) based on the Agent Skills standard, providing on-demand, specialized capabilities like procedural workflows or domain expertise (e.g., security auditing).[2][6]

## Key Differences

| Aspect              | Custom Commands                          | Skills                                   |
|---------------------|------------------------------------------|------------------------------------------|
| **Activation**     | Manual trigger via slash command         | Autonomous: AI detects and activates via `activate_skill` tool based on context/description [2][3] |
| **Scope**          | Simple prompt shortcuts, project/global  | Modular directories with instructions, assets; dynamic loading to save tokens [1][2] |
| **Context Handling**| Static, one-off execution               | Persistent during session; better maintenance across interactions/platforms like Claude [1] |
| **Discovery**      | User-invoked only                       | Tiered (workspace `.gemini/skills/`, user `~/.gemini/skills/`, extensions) with progressive loading [2] |
| **Use Case**       | Quick, explicit workflows               | Orchestrators/sub-skills for agentic tasks (e.g., git-commit chaining sub-skills) [1][3] |

Skills offer progressive disclosure—loading only when relevant—making them ideal for complex, AI-driven autonomy in tools like Gemini CLI, while commands suit fast manual invocation.[3][1][2]

## Human

Can custom commands invoke skills like we can in claude code?

## Assistant

**No, custom commands in Gemini CLI cannot directly invoke skills.** Custom commands are static TOML-defined prompts with shell injection (`!{...}`) and argument placeholders (`{{args}}`), but they lack syntax or tooling to call `activate_skill` or reference skills programmatically.[1]

In Claude Code, this is possible via the `SlashCommand` tool, allowing the AI (or custom commands) to dynamically invoke other slash commands or skills like `/skill-name`.[2][3]

## Invocation Patterns

| Feature/Tool       | Gemini CLI Custom Commands | Claude Code Equivalent                  |
|--------------------|----------------------------|-----------------------------------------|
| **Direct Invocation** | User types `/command` only | User or AI via `SlashCommand` tool [3] |
| **AI Autonomous**  | No; skills use `activate_skill` tool [4][5] | Yes, for skills & commands [6][2] |
| **Chaining**       | Manual via orchestrator skills calling sub-skills indirectly [5] | Commands trigger skills/subagents [6] |
| **Prompt Hack**    | Instruct AI post-command to activate skill (indirect) [7] | Built-in tool support |

Users often convert commands to skills for cross-platform (Gemini/Claude) compatibility and better chaining, using commands solely as manual triggers for orchestrator skills.[5]

## Human

What are the limitations of custom commands vs skills

## Assistant

Custom commands in Gemini CLI are limited to static, manual shortcuts, while skills enable dynamic, autonomous extensions with better context and portability.[1][2]

## Activation and Awareness
- Custom commands require explicit user invocation via `/command`; the AI cannot detect or trigger them autonomously.[2][1]
- Skills activate via the `activate_skill` tool when context matches their description, supporting agentic workflows without manual input.[3][1]

## Context and Persistence
- Commands execute one-off with basic argument insertion (`{{args}}`), leading to potential context loss in multi-turn interactions.[1]
- Skills load progressively (workspace/user/extension tiers), maintain session context, and chain sub-skills (e.g., git-commit orchestrating add/message/status).[3][1]

## Portability and Scope
- Commands are Gemini CLI-specific, defined in `.toml` files (project `~/.gemini/commands/` or global).[4]
- Skills (SKILL.md folders) are cross-platform, working unchanged in Claude Code, with progressive disclosure to avoid token bloat.[1]

## Extensibility
| Limitation Category | Custom Commands                          | Skills                                   |
|---------------------|------------------------------------------|------------------------------------------|
| **Chaining**        | Indirect (via orchestrator skill prompt) | Native: Orchestrators invoke sub-skills [1] |
| **Assets/Assets**   | Text/shell only (`!{...}`)               | Instructions, scripts, files; MCP integration [1][4] |
| **Discovery**       | Static list in `/help`                   | Tiered, reloadable (`/skills reload`) [3] |
| **Disable/Override**| Project overrides user                   | Scoped disable/enable per tier [3] |

Many users convert commands to skills for superior autonomy and compatibility, reserving commands for quick manual launches.[1]

## Human

What are examples of effective skills vs custom commands

## Assistant

Effective skills demonstrate autonomous activation and modularity, while custom commands excel as quick manual shortcuts for repetitive prompts.[1][2][3]

## Custom Commands Examples
These are TOML-defined shortcuts invoked via `/command args`, ideal for static tasks with shell integration.
- `/git:fix "Button misaligned"`: Injects issue description into refactor prompt; appends raw args for precise fixes.[4][5]
- `/test:gen "user auth flow"`: Generates unit tests from description, using `{{args}}` placeholder.[2][6]
- `/changelog 1.2.0 "added feature"`: Appends version/details to prompt for entry generation, with shell grep for searches.[4]

## Skills Examples
Skills are SKILL.md folders that activate via `activate_skill` tool on context match, supporting chaining and assets.
- **Tech News Aggregator**: Fetches/summarizes URL news autonomously when asked about updates; includes scripts for RSS parsing.[7]
- **Git Orchestrator**: Workspace skill chaining sub-skills (add, commit message, status check) for full workflows without manual steps.[3]
- **Security Auditor**: Loads on vulnerability queries, using checklists/scripts for scans; portable to Claude Code.[8][1]

## Comparison Table

| Use Case Type      | Custom Commands (Manual)              | Skills (Autonomous)                     |
|--------------------|---------------------------------------|-----------------------------------------|
| **Repetitive Prompts** | `/db:reset` (drops/recreates DB via shell) [6] | N/A—use for dynamic decisions |
| **Complex Workflows** | Limited chaining                     | Codebase migration (multi-step assets) [1] |
| **Domain Expertise** | `/plan "feature X"` (planning template) [9] | Cloud deployment (procedural instructions) [1] |
| **Token Efficiency**| Always loaded in session             | On-demand, tiered loading [1] |

Commands suit explicit, one-shot tasks; skills power agentic chains and cross-tool reuse.[8][3]
