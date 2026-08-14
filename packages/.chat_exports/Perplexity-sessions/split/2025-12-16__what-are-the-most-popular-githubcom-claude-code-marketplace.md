---
title: "what are the most popular github.com claude code marketplace plugins hooks repos"
date: "2025-12-16"
mode: "COPILOT"
uuid: "e2cc33cc-25ba-4183-b574-7e3c6658017a"
entry_count: 3
---

## Human

what are the most popular github.com claude code marketplace plugins hooks repos

## Assistant

**Top Claude Code Repositories**

Popular GitHub repositories for Claude Code plugins, hooks, and marketplaces focus on productivity tools, automation, and workflow enhancements. These align with advanced integrations like those in your agentic systems and hook-based validation workflows. Community-curated "awesome" lists and marketplaces lead in adoption due to their comprehensive collections.[1][2][3]

**Marketplaces and Awesome Lists**
- **Dev-GOM/claude-code-marketplace** (high activity): Offers hooks for code review, bug detection, TODO collectors, and multi-language support with clickable reports.[4]
- **quemsah/awesome-claude-plugins**: Curates top 100 repositories including agent-security hooks and aicode-toolkit for secrets scanning.[1]
- **jmanhype/awesome-claude-code** and **hesreallyhim/awesome-claude-code**: Central hubs for plugins, MCP servers (e.g., GitHub MCP), and slash commands.[2][3]
- **ananddtyagi/claude-code-marketplace** (512 stars): Marketplace for plugins with team configurations.[5]

**Hooks and Frameworks**
- **decider/claude-hooks**: Python-based system for code quality validation, package checks, and notifications; easy install with hierarchical configs.[6]
- **brennercruvinel/CCPlugins** (2.4k stars): Framework saving time on senior-engineer prompts, with CLI extensions and commands.[7]
- **kivilaid/plugin-marketplace**: 87 plugins from multiple sources, including Anthropic tools and agents.[8]

**Integration Notes**
Add marketplaces via `/plugin marketplace add owner/repo` for automatic plugin access. For your Claude Code hooks and subagents, start with tdd-guard or decider/claude-hooks from prior research, then explore awesome lists for Python/TypeScript compatibility. Test via `/plugin validate` to match your RCA and multi-agent setups.[9][10][11][6]

## Human

Top Claude Code marketplaces on GitHub by stars
Most widely used Claude Code hooks for CI automation
Best repositories for Claude plugin hook SDKs
most popular claude code agent repos

## Assistant

**Top Claude Code Marketplaces by Stars**

ananddtyagi/claude-code-marketplace leads with 512 stars, offering plugins like Code Review, Refactor, Bug Detective, and Audit agents via simple `/plugin install` commands. hesreallyhim/awesome-claude-code follows as a comprehensive starter template with MCP servers and tools, popular for development environments. Other notable ones include netresearch/claude-code-marketplace for automated skill syncing and DustyWalker/claude-code-marketplace for production-ready agents.[1][2][3][4]

**Popular Hooks for CI Automation**

decider/claude-hooks excels for CI with Python-based PreToolUse/PostToolUse hooks that enforce code quality, package checks, and notifications, integrating seamlessly into pipelines. disler/claude-code-hooks-mastery covers full lifecycle events like UserPromptSubmit for prompt validation and auditing, suitable for automated workflows. timoconnellaus/define-claude-code-hooks provides TypeScript hooks for project-wide or local CI enforcement.[5][6][7]

**Best Plugin Hook SDK Repositories**

beyondcode/claude-hooks-sdk (PHP) offers a fluent API for structured JSON responses in hooks like PreToolUse. mizunashi-mana/claude-code-hook-sdk (TypeScript) delivers type safety, dependency injection, and testing for scalable hook development. These SDKs streamline custom hooks matching your Python/TypeScript workflows.[8][9]

**Most Popular Claude Code Agent Repos**

wshobson/agents tops with 248+ stars for production-ready orchestration across 48 specialists. iannuttall/claude-agents matches at 248 stars as a community favorite. 0xfurai/claude-code-subagents stands out with 100+ agents in uniform format, ideal for your multi-subagent systems. rahulvrane/awesome-claude-agents curates these with 223 stars.[10][11][12]

## Human

isn't there a superclaude?

## Assistant

SuperClaude exists as a popular configuration framework enhancing Claude Code with specialized commands, cognitive personas, MCP integrations, and token optimization for development workflows. The primary repository, SuperClaude-Org/SuperClaude_Framework, installs via cloning to ~/.claude/ for drop-in use, adding 16+ slash commands like /sc-analyze for architecture scoring. It supports your multi-agent setups through smart routing and personas, with marketplace plugins available via `/plugin marketplace add SuperClaude-Org/SuperClaude_Plugin`.[1][2][3][4]

**Key Repositories**
- **SuperClaude-Org/SuperClaude_Framework**: Core framework with commands, personas (e.g., architect, QA), and MCP servers like Context7/Playwright.[1]
- **SuperClaude-Org/SuperClaude_Plugin**: Marketplace plugin for one-command installs, including PM agents and deep research tools.[5][4]
- **gwendall/superclaude**: GitHub-focused variant for commit messages, changelogs, and code reviews via CLI.[6]

**Installation and Usage**
Run `git clone https://github.com/SuperClaude-Org/SuperClaude_Framework ~/.claude/` then restart Claude Code; use `/sc analyze` for codebase review or `/sc architect` for design. Pairs well with hooks like decider/claude-hooks for CI and your subagent orchestration. Videos demonstrate Next.js scaffolding in under 20 minutes.[2][7][8][9]
