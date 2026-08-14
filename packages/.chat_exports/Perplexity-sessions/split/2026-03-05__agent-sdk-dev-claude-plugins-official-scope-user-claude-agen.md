---
title: "'  agent-sdk-dev @ claude-plugins-official
  Scope: user
  Claude Agent SDK Development Plugin

  Author: Anthropic"
date: "2026-03-05"
mode: "COPILOT"
uuid: "7cdd449d-8cdd-4aeb-be29-b2c84d64814b"
entry_count: 2
---

## Human

"  agent-sdk-dev @ claude-plugins-official
  Scope: user
  Claude Agent SDK Development Plugin

  Author: Anthropic
  Status: Enabled

  Installed components:
  • Commands: new-sdk-app
  • Agents: agent-sdk-verifier-py, agent-sdk-verifier-ts"

In Claude Code, what are the best use cases for this? How do I get maximum value from it?

## Assistant

The agent-sdk-dev plugin equips Claude Code with tools for developing applications using the Claude Agent SDK. It provides a command for scaffolding projects and agents for validation in Python and TypeScript.

## Best Use Cases
- **Project Scaffolding**: Use `/new-sdk-app` to interactively set up new Agent SDK apps, handling boilerplate for Python or TypeScript projects with tools, hooks, and configurations.[1][2]
- **Code Validation**: Invoke `agent-sdk-verifier-py` or `agent-sdk-verifier-ts` to check SDK apps against best practices, catching issues in agent loops, tool definitions, permissions, and MCP integrations early.[2][1]
- **SDK Prototyping**: Build custom agents that mimic Claude Code's capabilities (e.g., file editing, bash execution) for standalone apps or embedding in SaaS products.[3][1]
- **Plugin Development**: Test SDK-based plugins locally before sharing, leveraging verifiers for hooks, skills, and commands.[4][1]

## Maximizing Value
Integrate it into your workflow by starting sessions with `/new-sdk-app` for quick prototypes, then running verifiers iteratively during development. Combine with your multi-terminal setup and git worktrees for parallel Python/TS validation, and use MCP servers (like your Tavily/Serper) in scaffolded apps for enhanced agentic flows.[3][2]

Configure in `.claude/settings.json` for project persistence:

```
{
  "plugins": ["agent-sdk-dev@claude-plugins-official"]
}
```

This aligns with your agentic CLI optimization by accelerating SDK experiments without manual boilerplate.[2]

## Human

How to use new-sdk-app command

## Assistant

The `new-sdk-app` command from the agent-sdk-dev plugin scaffolds new Claude Agent SDK projects interactively in Claude Code. It handles setup for Python or TypeScript, installs dependencies, and runs initial verification.[1][2]

## Usage Steps
Run it directly in a Claude Code session (plugin must be enabled).

1. Type `/new-sdk-app [project-name]` or just `/new-sdk-app` (name optional).[1]
2. Answer interactive prompts:
   - Language: TypeScript or Python.
   - Project name (defaults to provided or "my-sdk-app").
   - Agent type: Coding, business, custom.
   - Starting point: Minimal, basic, or example-based.
   - Package manager: npm/yarn/pnpm (TS) or pip/poetry (Py).[2][1]
3. Claude creates the project folder, files (e.g., `agent.ts/py`, `.env.example`, `.gitignore`), installs SDK, validates syntax/types, and verifies with `agent-sdk-verifier-py/ts`.[1]

## Example Output
After prompts, expect a new directory like `my-project/` with runnable agent code. Test by running `npm run dev` (TS) or `python main.py` (Py).[1]

## Tips for Value
Use in a git worktree for isolation, then verify iteratively with "Verify my Agent SDK application". Integrates seamlessly with your MCP servers and multi-LLM prompts for custom agent prototyping.[2][1]
